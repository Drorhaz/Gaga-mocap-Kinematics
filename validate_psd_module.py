"""
Simple validation script for PSD filter validation module.
Tests basic functionality without requiring pytest.
"""

import sys
import os
sys.path.insert(0, 'src')

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

from filter_validation import (
    compute_psd_welch,
    compute_power_in_band,
    analyze_filter_psd_preservation,
    validate_filter_quality,
    check_filter_cutoff_validity,
    validate_winter_filter_multi_signal
)

def test_psd_computation():
    """Test PSD computation on sine wave."""
    print("\n=== Test 1: PSD Computation ===")
    fs = 120.0
    duration = 10.0
    freq_target = 5.0
    
    t = np.arange(0, duration, 1/fs)
    signal = np.sin(2 * np.pi * freq_target * t)
    
    freqs, psd = compute_psd_welch(signal, fs)
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]
    
    print(f"  Target frequency: {freq_target} Hz")
    print(f"  Detected peak: {peak_freq:.2f} Hz")
    print(f"  Error: {abs(peak_freq - freq_target):.2f} Hz")
    
    if abs(peak_freq - freq_target) < 0.5:
        print("[PASS] PSD correctly identifies frequency")
        return True
    else:
        print("[FAIL] PSD frequency detection inaccurate")
        return False

def test_filter_preservation():
    """Test filter preservation analysis."""
    print("\n=== Test 2: Filter Preservation Analysis ===")
    fs = 120.0
    duration = 10.0
    t = np.arange(0, duration, 1/fs)
    
    # Signal: 5 Hz dance + 25 Hz noise
    signal_raw = (np.sin(2*np.pi*5*t) + 
                 0.3 * np.sin(2*np.pi*25*t))
    
    # Filter at 10 Hz
    b, a = butter(2, 10.0/(fs/2), btype='low')
    signal_filt = filtfilt(b, a, signal_raw)
    
    metrics = analyze_filter_psd_preservation(
        signal_raw, signal_filt, fs, cutoff_hz=10.0
    )
    
    print(f"  Dance preservation: {metrics['dance_preservation_pct']:.1f}%")
    print(f"  Noise attenuation: {metrics['noise_attenuation_db']:.1f} dB")
    print(f"  SNR improvement: {metrics['snr_improvement_db']:.1f} dB")
    
    if metrics['dance_preservation_pct'] > 85 and metrics['noise_attenuation_db'] > 5:
        print("[PASS] Filter preserves dance, attenuates noise")
        return True
    else:
        print("[FAIL] Filter performance suboptimal")
        return False

def test_quality_assessment():
    """Test filter quality assessment."""
    print("\n=== Test 3: Quality Assessment ===")
    
    metrics_good = {
        'dance_preservation_pct': 97.0,
        'noise_attenuation_db': 25.0,
        'snr_improvement_db': 8.0
    }
    
    quality = validate_filter_quality(metrics_good)
    
    print(f"  Dance status: {quality['dance_preservation_status']}")
    print(f"  Noise status: {quality['noise_attenuation_status']}")
    print(f"  Overall: {quality['overall_filter_quality']}")
    
    if quality['overall_filter_quality'] == 'PASS':
        print("[PASS] Quality assessment working")
        return True
    else:
        print("[FAIL] Quality assessment incorrect")
        return False

def test_cutoff_validity():
    """Test cutoff validity checking."""
    print("\n=== Test 4: Cutoff Validity Checking ===")
    
    # Valid cutoff
    result = check_filter_cutoff_validity(6.0, 120.0, 12.0)
    print(f"  6 Hz cutoff: {result['validity_status']}")
    
    # Winter failure
    result_fail = check_filter_cutoff_validity(12.0, 120.0, 12.0)
    print(f"  12 Hz cutoff (fmax): {result_fail['validity_status']}")
    
    if result['validity_status'] == 'VALID' and result_fail['validity_status'] == 'FAIL_WINTER_FMAX':
        print("[PASS] Cutoff validity detection working")
        return True
    else:
        print("[FAIL] Cutoff validity detection incorrect")
        return False

def test_multi_signal():
    """Test multi-signal validation."""
    print("\n=== Test 5: Multi-Signal Validation ===")
    
    fs = 120.0
    duration = 5.0
    n_samples = int(fs * duration)
    
    t = np.arange(n_samples) / fs
    # Use fixed seed for reproducibility
    np.random.seed(42)
    df_raw = pd.DataFrame({
        'col1__px': np.sin(2*np.pi*5*t) + 0.05*np.random.randn(n_samples),
        'col2__py': np.sin(2*np.pi*6*t) + 0.05*np.random.randn(n_samples),
        'col3__pz': np.sin(2*np.pi*4*t) + 0.05*np.random.randn(n_samples)
    })
    
    # Apply filter
    b, a = butter(2, 8.0/(fs/2), btype='low')
    df_filt = df_raw.copy()
    for col in df_raw.columns:
        df_filt[col] = filtfilt(b, a, df_raw[col].values)
    
    # Validate
    result = validate_winter_filter_multi_signal(
        df_raw, df_filt, list(df_raw.columns), fs, cutoff_hz=8.0, n_samples=3
    )
    
    print(f"  Signals analyzed: {result['n_signals_analyzed']}")
    print(f"  Mean dance preservation: {result['dance_preservation_mean']:.1f}%")
    print(f"  Overall quality: {result['overall_filter_quality']}")
    
    # Check if validation completed successfully (preservation >70% is reasonable for 8Hz cutoff)
    if result['n_signals_analyzed'] == 3 and result['dance_preservation_mean'] > 70.0:
        print("[PASS] Multi-signal validation working")
        return True
    else:
        print("[FAIL] Multi-signal validation issues")
        return False

def main():
    """Run all validation tests."""
    print("="*60)
    print("PSD Filter Validation Module - Validation Tests")
    print("="*60)
    
    results = []
    results.append(test_psd_computation())
    results.append(test_filter_preservation())
    results.append(test_quality_assessment())
    results.append(test_cutoff_validity())
    results.append(test_multi_signal())
    
    print("\n" + "="*60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("="*60)
    
    if all(results):
        print("\n[SUCCESS] ALL TESTS PASSED - Module validation successful!")
        return 0
    else:
        print("\n[WARN] SOME TESTS FAILED - Check implementation")
        return 1

if __name__ == '__main__':
    sys.exit(main())
