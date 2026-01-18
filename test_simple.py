#!/usr/bin/env python3
"""Simple test for artifact detection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from artifacts import detect_velocity_artifacts
import numpy as np

def test_spike():
    """Test that velocity spike is detected."""
    velocity = np.array([[0.1, 0.1, 0.1], [0.1, 5.0, 0.1], [0.1, 0.1, 0.1]])
    mask = detect_velocity_artifacts(velocity, mad_multiplier=6.0)
    
    # Should detect spike in Y axis only
    assert not mask[0, 0]  # No spike in first frame
    assert not mask[0, 1]  # No spike in X
    assert mask[0, 2]  # Spike in Y
    print("✅ Spike detection test passed")

if __name__ == "__main__":
    test_spike()
    print("All tests passed!")
