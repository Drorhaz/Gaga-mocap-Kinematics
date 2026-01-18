#!/usr/bin/env python3
"""Debug test for artifact detection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from artifacts import detect_velocity_artifacts
import numpy as np
from scipy.stats import median_abs_deviation

def test_spike():
    """Test that velocity spike is detected."""
    velocity = np.array([[0.1, 0.1, 0.1], [0.1, 5.0, 0.1], [0.1, 0.1, 0.1]])
    
    # Manual MAD calculation
    abs_diffs = np.abs(np.diff(velocity, axis=0))
    print(f"Velocity diffs shape: {abs_diffs.shape}")
    print(f"Velocity diffs (Y axis): {abs_diffs[1]}")
    
    mad = median_abs_deviation(abs_diffs, scale='normal')
    print(f"MAD per axis: {mad}")
    print(f"MAD (Y axis): {mad[1]}")
    
    threshold = 6.0 * mad
    print(f"Threshold per axis: {threshold}")
    print(f"Threshold (Y axis): {threshold[1]}")
    
    mask = detect_velocity_artifacts(velocity, mad_multiplier=6.0)
    print(f"Final mask[0,2]: {mask[0,2]}")
    
    # Should detect spike in Y axis only
    assert mask[0, 2]  # Spike in Y
    print("✅ Spike detection test passed")

if __name__ == "__main__":
    test_spike()
