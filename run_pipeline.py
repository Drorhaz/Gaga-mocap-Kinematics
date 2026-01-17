#!/usr/bin/env python3
"""
Automated Motion Capture Pipeline Runner
Processes multiple CSV files through the complete pipeline.

Usage:
    python run_pipeline.py --csv-list csv_files.txt
    python run_pipeline.py --auto-discover
    python run_pipeline.py --single "data/734/T1/file.csv"
"""

import os
import sys
import yaml
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse


class PipelineRunner:
    """Orchestrates the complete motion capture processing pipeline."""
    
    def __init__(self, project_root: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.config_file = self.project_root / "config" / "config_v1.yaml"
        self.notebooks_dir = self.project_root / "notebooks"
        self.dry_run = dry_run
        
        # Pipeline sequence (notebook numbers)
        self.pipeline_sequence = ['01', '02', '03', '04', '05', '06']
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging to file and console."""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"pipeline_run_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Pipeline Runner initialized. Log: {log_file}")
    
    def discover_csv_files(self, pattern: str = "**/*.csv") -> List[Path]:
        """Auto-discover CSV files in data directory."""
        data_dir = self.project_root / "data"
        csv_files = list(data_dir.glob(pattern))
        
        # Exclude files with 'test' or 'backup' in name
        csv_files = [f for f in csv_files 
                     if 'test' not in f.name.lower() 
                     and 'backup' not in f.name.lower()]
        
        self.logger.info(f"Discovered {len(csv_files)} CSV files")
        return sorted(csv_files)
    
    def update_config(self, csv_path: Path) -> bool:
        """Update config.yaml with new CSV path."""
        try:
            # Calculate relative path from data dir
            data_dir = self.project_root / "data"
            relative_path = csv_path.relative_to(data_dir)
            
            # Read current config
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update CSV path (use forward slashes for cross-platform)
            config['current_csv'] = str(relative_path).replace('\\', '/')
            
            # Write back
            if not self.dry_run:
                with open(self.config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
            
            self.logger.info(f"✅ Config updated: current_csv = {config['current_csv']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update config: {e}")
            return False
    
    def run_notebook(self, notebook_num: str, timeout: int = 600) -> Dict:
        """
        Execute a single notebook using papermill.
        
        Args:
            notebook_num: Notebook number (e.g., '01', '02')
            timeout: Max execution time in seconds
            
        Returns:
            Dict with status, error, execution_time
        """
        notebook_name = f"{notebook_num}_*.ipynb"
        notebooks = list(self.notebooks_dir.glob(notebook_name))
        
        if not notebooks:
            return {
                'status': 'error',
                'error': f'Notebook {notebook_num} not found',
                'execution_time': 0
            }
        
        notebook_path = notebooks[0]
        output_path = notebook_path.parent / f"{notebook_path.stem}_output.ipynb"
        
        self.logger.info(f"▶️  Running: {notebook_path.name}")
        
        if self.dry_run:
            self.logger.info("   [DRY RUN - Skipped]")
            return {'status': 'skipped', 'error': None, 'execution_time': 0}
        
        start_time = datetime.now()
        
        try:
            # Use papermill to execute notebook
            import papermill as pm
            
            pm.execute_notebook(
                input_path=str(notebook_path),
                output_path=str(output_path),
                kernel_name='python3',
                timeout=timeout,
                progress_bar=False
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"✅ Completed in {execution_time:.1f}s")
            
            # Cleanup output notebook (optional)
            output_path.unlink(missing_ok=True)
            
            return {
                'status': 'success',
                'error': None,
                'execution_time': execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self.logger.error(f"❌ Failed after {execution_time:.1f}s: {error_msg}")
            
            return {
                'status': 'failed',
                'error': error_msg,
                'execution_time': execution_time
            }
    
    def process_single_csv(self, csv_path: Path) -> Dict:
        """
        Process a single CSV file through the entire pipeline.
        
        Returns:
            Dict with run summary
        """
        self.logger.info("="*70)
        self.logger.info(f"📁 Processing: {csv_path.name}")
        self.logger.info("="*70)
        
        run_summary = {
            'csv_file': str(csv_path),
            'run_id': csv_path.stem,
            'start_time': datetime.now().isoformat(),
            'notebooks': {},
            'status': 'started'
        }
        
        # Step 1: Update config
        if not self.update_config(csv_path):
            run_summary['status'] = 'failed'
            run_summary['error'] = 'Config update failed'
            return run_summary
        
        # Step 2: Run pipeline notebooks
        total_time = 0
        all_success = True
        
        for notebook_num in self.pipeline_sequence:
            result = self.run_notebook(notebook_num, timeout=600)
            run_summary['notebooks'][notebook_num] = result
            total_time += result['execution_time']
            
            if result['status'] == 'failed':
                all_success = False
                self.logger.warning(f"⚠️  Stopping pipeline due to failure in notebook {notebook_num}")
                break
        
        # Step 3: Verify outputs
        if all_success:
            derivatives_exist = self.verify_outputs(csv_path.stem)
            run_summary['outputs_verified'] = derivatives_exist
            
            if derivatives_exist:
                run_summary['status'] = 'success'
                self.logger.info(f"🎉 Successfully processed {csv_path.name}")
            else:
                run_summary['status'] = 'partial'
                self.logger.warning(f"⚠️  Pipeline completed but missing some outputs")
        else:
            run_summary['status'] = 'failed'
        
        run_summary['end_time'] = datetime.now().isoformat()
        run_summary['total_execution_time'] = total_time
        
        return run_summary
    
    def verify_outputs(self, run_id: str) -> bool:
        """Verify that all expected output files were created."""
        derivatives_dir = self.project_root / "derivatives"
        
        expected_files = [
            f"step_01_parse/{run_id}__parsed_run.parquet",
            f"step_02_preprocess/{run_id}__preprocessed.parquet",
            f"step_03_resample/{run_id}__resampled.parquet",
            f"step_04_filtering/{run_id}__filtered.parquet",
            f"step_06_kinematics/{run_id}__kinematics.parquet",
            f"step_06_kinematics/{run_id}__kinematics_summary.json",
        ]
        
        all_exist = True
        for file_path in expected_files:
            full_path = derivatives_dir / file_path
            if not full_path.exists():
                self.logger.warning(f"Missing: {file_path}")
                all_exist = False
        
        return all_exist
    
    def run_master_report(self) -> bool:
        """Execute notebook 07 to generate master quality report."""
        self.logger.info("="*70)
        self.logger.info("📊 Generating Master Quality Report (Notebook 07)")
        self.logger.info("="*70)
        
        result = self.run_notebook('07', timeout=300)
        
        if result['status'] == 'success':
            self.logger.info("✅ Master report generated successfully")
            
            # Find the generated Excel file
            reports_dir = self.project_root / "reports"
            excel_files = list(reports_dir.glob("Master_Audit_Log_*.xlsx"))
            if excel_files:
                latest = max(excel_files, key=lambda p: p.stat().st_mtime)
                self.logger.info(f"📄 Report: {latest}")
            
            return True
        else:
            self.logger.error("❌ Master report generation failed")
            return False
    
    def process_batch(self, csv_files: List[Path], 
                      stop_on_error: bool = False) -> Dict:
        """
        Process multiple CSV files.
        
        Args:
            csv_files: List of CSV file paths
            stop_on_error: If True, stop entire batch on first error
            
        Returns:
            Dict with batch summary
        """
        batch_summary = {
            'total_files': len(csv_files),
            'start_time': datetime.now().isoformat(),
            'runs': [],
            'success_count': 0,
            'failed_count': 0
        }
        
        self.logger.info(f"🚀 Starting batch processing of {len(csv_files)} files")
        
        for i, csv_path in enumerate(csv_files, 1):
            self.logger.info(f"\n[{i}/{len(csv_files)}] Processing {csv_path.name}")
            
            run_result = self.process_single_csv(csv_path)
            batch_summary['runs'].append(run_result)
            
            if run_result['status'] == 'success':
                batch_summary['success_count'] += 1
            else:
                batch_summary['failed_count'] += 1
                
                if stop_on_error:
                    self.logger.error("🛑 Stopping batch due to error (stop_on_error=True)")
                    break
        
        batch_summary['end_time'] = datetime.now().isoformat()
        
        # Generate master report
        if batch_summary['success_count'] > 0:
            self.run_master_report()
        
        # Save batch summary
        self.save_batch_summary(batch_summary)
        
        return batch_summary
    
    def save_batch_summary(self, summary: Dict):
        """Save batch processing summary to JSON."""
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = reports_dir / f"batch_summary_{timestamp}.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"📝 Batch summary saved: {summary_file}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Automated Motion Capture Pipeline Runner'
    )
    
    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Path to project root directory'
    )
    
    parser.add_argument(
        '--csv-list',
        type=str,
        help='Text file with list of CSV paths (one per line)'
    )
    
    parser.add_argument(
        '--auto-discover',
        action='store_true',
        help='Automatically discover all CSV files in data/'
    )
    
    parser.add_argument(
        '--single',
        type=str,
        help='Process a single CSV file'
    )
    
    parser.add_argument(
        '--json',
        type=str,
        help='JSON file with batch configuration (see batch_configs/ folder)'
    )
    
    parser.add_argument(
        '--stop-on-error',
        action='store_true',
        help='Stop batch processing on first error'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate run without executing notebooks'
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = PipelineRunner(args.project_root, dry_run=args.dry_run)
    
    # Get CSV file list
    csv_files = []
    
    if args.single:
        csv_files = [Path(args.single)]
    elif args.csv_list:
        with open(args.csv_list, 'r') as f:
            csv_files = [Path(line.strip()) for line in f if line.strip()]
    elif args.json:
        # Load from JSON batch configuration
        with open(args.json, 'r') as f:
            batch_config = json.load(f)
        
        # Convert relative paths to full paths (relative to data/ directory)
        data_dir = runner.project_root / "data"
        csv_files = [data_dir / csv_path for csv_path in batch_config['csv_files']]
        
        print(f"📋 Loaded batch config: {batch_config.get('batch_name', 'Unnamed')}")
        print(f"📄 Description: {batch_config.get('description', 'N/A')}")
    elif args.auto_discover:
        csv_files = runner.discover_csv_files()
    else:
        parser.print_help()
        sys.exit(1)
    
    if not csv_files:
        print("❌ No CSV files found to process")
        sys.exit(1)
    
    # Run pipeline
    print(f"\n🚀 Processing {len(csv_files)} file(s)...")
    batch_result = runner.process_batch(csv_files, stop_on_error=args.stop_on_error)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 BATCH PROCESSING COMPLETE")
    print("="*70)
    print(f"✅ Success: {batch_result['success_count']}")
    print(f"❌ Failed:  {batch_result['failed_count']}")
    print(f"📁 Total:   {batch_result['total_files']}")
    print("="*70)


if __name__ == '__main__':
    main()
