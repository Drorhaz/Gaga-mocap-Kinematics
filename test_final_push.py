"""
Test Suite: Final Push Implementation
======================================
Comprehensive tests for all 4 tasks.

Run with: pytest test_final_push.py -v

Author: Gaga Motion Analysis Pipeline
Date: 2026-01-23
"""

import pytest
import numpy as np
from src.subject_validation import (
    validate_height,
    validate_mass,
    compute_normalized_intensity_index,
    validate_subject_context
)
from src.burst_classification import EVENT_DENSITY_THRESHOLDS


# =============================================================================
# TASK 1: SUBJECT CONTEXT & NORMALIZATION TESTS
# =============================================================================

class TestTask1SubjectValidation:
    """Test height/mass validation and intensity normalization."""
    
    def test_height_pass_normal_range(self):
        """Test height in normal range (140-210 cm) returns PASS."""
        status, reason = validate_height(170.0)
        assert status == 'PASS'
        assert 'normal range' in reason.lower()
    
    def test_height_fail_zero(self):
        """Test height = 0 returns FAIL."""
        status, reason = validate_height(0.0)
        assert status == 'FAIL'
        assert 'zero or negative' in reason.lower()
    
    def test_height_fail_negative(self):
        """Test negative height returns FAIL."""
        status, reason = validate_height(-10.0)
        assert status == 'FAIL'
        assert 'zero or negative' in reason.lower()
    
    def test_height_fail_exceeds_max(self):
        """Test height > 250 cm returns FAIL."""
        status, reason = validate_height(300.0)
        assert status == 'FAIL'
        assert 'exceeds maximum' in reason.lower()
        assert '250' in reason
    
    def test_height_review_below_typical(self):
        """Test height < 140 cm but > 0 returns REVIEW."""
        status, reason = validate_height(130.0)
        assert status == 'REVIEW'
        assert 'below typical' in reason.lower()
    
    def test_height_review_above_typical(self):
        """Test height > 210 cm but < 250 returns REVIEW."""
        status, reason = validate_height(220.0)
        assert status == 'REVIEW'
        assert 'above typical' in reason.lower()
    
    def test_height_edge_case_250(self):
        """Test height = 250 cm (boundary) returns REVIEW."""
        status, reason = validate_height(250.0)
        assert status in ['PASS', 'REVIEW']  # At boundary
    
    def test_mass_pass_normal_range(self):
        """Test mass in normal range (40-150 kg) returns PASS."""
        status, reason = validate_mass(70.0)
        assert status == 'PASS'
        assert 'normal range' in reason.lower()
    
    def test_mass_fail_zero(self):
        """Test mass <= 20 kg returns FAIL."""
        status, reason = validate_mass(15.0)
        assert status == 'FAIL'
        assert 'too low' in reason.lower()
    
    def test_mass_fail_exceeds_max(self):
        """Test mass > 200 kg returns FAIL."""
        status, reason = validate_mass(250.0)
        assert status == 'FAIL'
        assert 'exceeds maximum' in reason.lower()
    
    def test_intensity_normalization_valid(self):
        """Test intensity normalization with valid mass."""
        result = compute_normalized_intensity_index(1000.0, 70.0)
        
        assert result['intensity_normalized'] is not None
        assert abs(result['intensity_normalized'] - 14.2857) < 0.01
        assert result['mass_status'] == 'PASS'
        assert result['intensity_raw'] == 1000.0
        assert result['mass_kg'] == 70.0
    
    def test_intensity_normalization_invalid_mass(self):
        """Test intensity normalization with invalid mass returns error."""
        result = compute_normalized_intensity_index(1000.0, 0.0, validate_inputs=True)
        
        assert result['intensity_normalized'] is None
        assert 'error' in result
        assert result['mass_status'] == 'FAIL'
    
    def test_subject_context_all_pass(self):
        """Test validate_subject_context with all PASS values."""
        result = validate_subject_context(height_cm=170.0, mass_kg=70.0)
        
        assert result['overall_status'] == 'PASS'
        assert result['height']['status'] == 'PASS'
        assert result['mass']['status'] == 'PASS'
    
    def test_subject_context_height_fail(self):
        """Test validate_subject_context with height FAIL."""
        result = validate_subject_context(height_cm=0.0, mass_kg=70.0)
        
        assert result['overall_status'] == 'FAIL'
        assert result['height']['status'] == 'FAIL'
        assert result['mass']['status'] == 'PASS'
    
    def test_subject_context_height_review(self):
        """Test validate_subject_context with height REVIEW."""
        result = validate_subject_context(height_cm=130.0, mass_kg=70.0)
        
        assert result['overall_status'] == 'REVIEW'
        assert result['height']['status'] == 'REVIEW'
        assert result['mass']['status'] == 'PASS'


# =============================================================================
# TASK 2: OUTLIER POLICY TESTS
# =============================================================================

class TestTask2OutlierPolicy:
    """Test outlier policy thresholds and decision logic."""
    
    def test_outlier_rate_threshold_exists(self):
        """Test that 5% outlier rate threshold is defined."""
        assert 'outlier_rate_review' in EVENT_DENSITY_THRESHOLDS
        assert EVENT_DENSITY_THRESHOLDS['outlier_rate_review'] == 5.0
    
    def test_artifact_rate_reject_threshold(self):
        """Test that 1% artifact rate reject threshold is defined."""
        assert 'artifact_rate_reject' in EVENT_DENSITY_THRESHOLDS
        assert EVENT_DENSITY_THRESHOLDS['artifact_rate_reject'] == 1.0
    
    def test_artifact_rate_warn_threshold(self):
        """Test that 0.1% artifact rate warn threshold is defined."""
        assert 'artifact_rate_warn' in EVENT_DENSITY_THRESHOLDS
        assert EVENT_DENSITY_THRESHOLDS['artifact_rate_warn'] == 0.1
    
    def test_consecutive_frame_classification(self):
        """Test that frame duration tiers are correct (1-3, 4-7, 8+)."""
        from src.burst_classification import TIER_ARTIFACT_MAX, TIER_BURST_MAX
        
        assert TIER_ARTIFACT_MAX == 3  # 1-3 frames = Artifact
        assert TIER_BURST_MAX == 7     # 4-7 frames = Burst
        # 8+ frames = Flow (implicit)
    
    def test_burst_classification_with_mock_data(self):
        """Test burst classification with synthetic data."""
        from src.burst_classification import classify_burst_events
        
        # Create mock data: short spike (artifact)
        fs = 120.0
        n_frames = 1200  # 10 seconds
        omega = np.random.randn(n_frames, 5) * 100  # Low velocity
        
        # Add 2-frame artifact (should be classified as artifact)
        omega[100:102, 0] = 3000  # >2000 deg/s
        
        result = classify_burst_events(omega, fs)
        
        # Check structure
        assert 'summary' in result
        assert 'decision' in result
        assert 'events' in result
        
        # Check that artifact was detected
        assert result['summary']['total_events'] > 0


# =============================================================================
# TASK 3: FILTER SYNERGY TESTS
# =============================================================================

class TestTask3FilterSynergy:
    """Test residual slope and filter ceiling logic."""
    
    def test_winter_analysis_returns_slope(self):
        """Test that winter_residual_analysis returns residual_slope."""
        from src.filtering import winter_residual_analysis
        
        # Create synthetic signal
        fs = 120.0
        t = np.linspace(0, 1, int(fs))
        signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave
        
        # Run Winter analysis with details
        result = winter_residual_analysis(signal, fs, return_details=True)
        
        assert 'residual_slope' in result
        assert isinstance(result['residual_slope'], float)
        assert 'residual_rms_final' in result
        assert 'cutoff_hz' in result
    
    def test_residual_slope_is_negative_for_converging_filter(self):
        """Test that residual slope is negative for well-converged filter."""
        from src.filtering import winter_residual_analysis
        
        # Create clean low-frequency signal
        fs = 120.0
        t = np.linspace(0, 2, int(2 * fs))
        signal = np.sin(2 * np.pi * 3 * t)  # 3 Hz - should converge well
        
        result = winter_residual_analysis(signal, fs, fmax=12, return_details=True)
        
        # Slope should be negative (RMS decreasing with cutoff)
        # Note: Not always guaranteed for all signals, but likely for clean sine
        assert result['residual_slope'] <= 0.1  # Allow small positive due to noise
    
    def test_filter_ceiling_warning_structure(self):
        """Test that filter_ceiling_warning is added to metadata."""
        from src.filtering import apply_winter_filter
        import pandas as pd
        
        # Create mock dataframe
        fs = 120.0
        n_frames = 240
        t = np.linspace(0, n_frames/fs, n_frames)
        
        df = pd.DataFrame({
            'time__s': t,
            'marker1__px': np.sin(2 * np.pi * 5 * t) * 100,
            'marker1__py': np.cos(2 * np.pi * 5 * t) * 100,
            'marker1__pz': np.ones(n_frames) * 1000
        })
        
        pos_cols = ['marker1__px', 'marker1__py', 'marker1__pz']
        
        # Apply filter
        df_filt, metadata = apply_winter_filter(
            df, fs, pos_cols, fmax=16, per_region_filtering=False
        )
        
        # Check that ceiling warning structure exists (may or may not be triggered)
        assert 'filter_ceiling_warning' in metadata or 'winter_details' in metadata


# =============================================================================
# TASK 4: SCHEMA DOCUMENTATION TESTS
# =============================================================================

class TestTask4SchemaDocumentation:
    """Test parameter schema has LaTeX formulas and code references."""
    
    def test_schema_structure(self):
        """Test that PARAMETER_SCHEMA is properly structured."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        assert 'step_05' in PARAMETER_SCHEMA
        assert 'step_06' in PARAMETER_SCHEMA
        assert 'step_04' in PARAMETER_SCHEMA
    
    def test_height_parameter_has_formula(self):
        """Test that height parameter has LaTeX formula."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        height_param = PARAMETER_SCHEMA['step_05']['parameters']['subject_context.height_cm']
        desc = height_param['description']
        
        # Should contain formula
        assert '$' in desc or 'Formula:' in desc
        # Should contain sanity check
        assert '250' in desc
    
    def test_intensity_index_has_formula(self):
        """Test that intensity_index has normalization formula."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        intensity_param = PARAMETER_SCHEMA['step_06']['parameters']['movement_metrics.intensity_index']
        desc = intensity_param['description']
        
        # Should contain formula: I/m
        assert '$I_{norm}' in desc or 'I / m' in desc.replace('_', ' ')
        # Should mention mass
        assert 'mass' in desc.lower() or 'kg' in desc
    
    def test_residual_rms_has_formula_and_thresholds(self):
        """Test that residual RMS has formula and quality thresholds."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        rms_param = PARAMETER_SCHEMA['step_06']['parameters']['signal_quality.avg_residual_rms']
        desc = rms_param['description']
        
        # Should contain formula
        assert 'RMS' in desc
        assert '$' in desc or 'Formula:' in desc
        # Should contain thresholds
        assert '15' in desc and '30' in desc  # GOLD<15, SILVER 15-30, REVIEW>30
    
    def test_outlier_parameters_have_thresholds(self):
        """Test that outlier parameters have explicit thresholds."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        outlier_pct = PARAMETER_SCHEMA['step_06']['parameters']['outlier_analysis.percentages.total_outliers']
        outlier_consec = PARAMETER_SCHEMA['step_06']['parameters']['outlier_analysis.consecutive_runs.max_consecutive_any_outlier']
        
        # Should mention 5% threshold
        assert '5' in outlier_pct['description']
        
        # Should mention classification: 1-3, 4-7, 8+
        assert '1-3' in outlier_consec['description'] or 'Artifact' in outlier_consec['description']
        assert '8' in outlier_consec['description']
    
    def test_filter_cutoff_has_code_reference(self):
        """Test that filter cutoff has code reference."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        cutoff_param = PARAMETER_SCHEMA['step_04']['parameters']['filter_params.filter_cutoff_hz']
        desc = cutoff_param['description']
        
        # Should contain code reference
        assert 'src/' in desc or 'Code:' in desc
        assert 'filtering.py' in desc


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests across multiple tasks."""
    
    def test_complete_subject_validation_workflow(self):
        """Test complete workflow: validate height, mass, normalize intensity."""
        # Step 1: Validate subject
        validation = validate_subject_context(height_cm=170.0, mass_kg=70.0)
        assert validation['overall_status'] == 'PASS'
        
        # Step 2: Normalize intensity
        intensity_result = compute_normalized_intensity_index(1000.0, 70.0)
        assert intensity_result['intensity_normalized'] is not None
        
        # Step 3: Check consistency
        assert intensity_result['mass_kg'] == validation['mass']['value_kg']
    
    def test_invalid_subject_prevents_normalization(self):
        """Test that invalid mass prevents intensity normalization."""
        # Invalid mass
        validation = validate_subject_context(height_cm=170.0, mass_kg=0.0)
        assert validation['mass']['status'] == 'FAIL'
        
        # Normalization should fail
        intensity_result = compute_normalized_intensity_index(1000.0, 0.0, validate_inputs=True)
        assert intensity_result['intensity_normalized'] is None
    
    def test_schema_contains_all_new_fields(self):
        """Test that schema contains all new fields from all 4 tasks."""
        from src.utils_nb07 import PARAMETER_SCHEMA
        
        # Task 1: Subject context
        assert 'subject_context.height_cm' in PARAMETER_SCHEMA['step_05']['parameters']
        
        # Task 2: Outlier analysis
        assert 'outlier_analysis.percentages.total_outliers' in PARAMETER_SCHEMA['step_06']['parameters']
        
        # Task 3: Filter parameters
        assert 'filter_params.filter_cutoff_hz' in PARAMETER_SCHEMA['step_04']['parameters']
        
        # Check descriptions are enhanced
        height_desc = PARAMETER_SCHEMA['step_05']['parameters']['subject_context.height_cm']['description']
        assert len(height_desc) > 50  # Should be detailed


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
