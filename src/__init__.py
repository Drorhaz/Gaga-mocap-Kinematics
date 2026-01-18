"""
Motion capture preprocessing modules.
"""

from .artifacts import (
    detect_velocity_artifacts,
    expand_artifact_mask,
    compute_true_velocity,
    apply_artifact_truncation
)

from .time_alignment import (
    generate_perfect_time_grid,
    ensure_hemispheric_alignment,
    precise_temporal_resampling,
    resample_positions,
    resample_quaternions,
    verify_resampling_quality
)
