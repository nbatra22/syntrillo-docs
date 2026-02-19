"""
Synthetic blood pressure data for testing.

ALL data in this module is entirely computer-generated.
It contains NO real patient information and NO Protected Health Information (PHI).
Do not substitute real patient data here under any circumstances.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ── Synthetic identity constants ──────────────────────────────────────────────
# These identifiers are obviously fake UUIDs / IDs used only in test code.

SYNTHETIC_INTERNAL_KEY = "00000000-0000-0000-0000-000000000001"
SYNTHETIC_HEALTHIE_USER_ID = "SYNTHETIC-TEST-0001"
SYNTHETIC_PSEUDONYMS = {
    "healthie_user_id": SYNTHETIC_HEALTHIE_USER_ID,
    "syntrillo_internal_key": SYNTHETIC_INTERNAL_KEY,
    "first_name": "Synthetic",
    "last_name": "Patient",
}


# ── DataFrame factory ─────────────────────────────────────────────────────────

def make_bp_dataframe(
    num_readings: int = 80,
    start_date: datetime = None,
    duration_weeks: float = 8.0,
    sbp_mean: float = 135.0,
    sbp_std: float = 10.0,
    dbp_mean: float = 85.0,
    dbp_std: float = 7.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic blood pressure DataFrame suitable for testing.

    Readings are evenly distributed across the specified period.
    The numpy seed makes each call fully reproducible.

    ALL data is entirely synthetic. Contains no PHI.

    Args:
        num_readings:   Total number of readings to generate.
        start_date:     First reading date. Defaults to 2025-01-01.
        duration_weeks: Total span of the dataset in weeks.
        sbp_mean:       Mean systolic blood pressure (mmHg).
        sbp_std:        Systolic standard deviation (mmHg).
        dbp_mean:       Mean diastolic blood pressure (mmHg).
        dbp_std:        Diastolic standard deviation (mmHg).
        seed:           RNG seed for reproducibility.
    """
    if start_date is None:
        start_date = datetime(2025, 1, 1)

    rng = np.random.default_rng(seed)
    total_hours = duration_weeks * 7 * 24
    offsets = np.linspace(0, total_hours, num=num_readings)

    timestamps = [
        start_date + timedelta(hours=float(h))
        for h in offsets
    ]

    sbp = rng.normal(sbp_mean, sbp_std, num_readings).round(1)
    dbp = rng.normal(dbp_mean, dbp_std, num_readings).round(1)

    return pd.DataFrame({
        "timestamp_local": pd.to_datetime(timestamps),
        "systolic": sbp,
        "diastolic": dbp,
    })


def make_bp_dataframe_with_extremes(seed: int = 99) -> pd.DataFrame:
    """
    Synthetic DataFrame that includes readings designed to trigger the
    extremes filter (SBP < 90, SBP > 170, DBP > 110).

    ALL data is entirely synthetic. Contains no PHI.
    """
    base = make_bp_dataframe(num_readings=40, seed=seed)

    # Inject three known-extreme rows
    extremes = pd.DataFrame({
        "timestamp_local": pd.to_datetime([
            "2025-01-05 08:00:00",
            "2025-01-10 14:30:00",
            "2025-01-15 21:00:00",
        ]),
        "systolic": [85.0, 175.0, 130.0],   # SBP < 90, SBP > 170, normal
        "diastolic": [70.0, 95.0, 115.0],   # normal, normal, DBP > 110
    })

    return pd.concat([base, extremes], ignore_index=True).sort_values(
        "timestamp_local"
    ).reset_index(drop=True)


def make_bp_dataframe_short(seed: int = 7) -> pd.DataFrame:
    """
    Synthetic DataFrame spanning < 4 weeks — not enough to produce
    Baseline or Prior timeframes (only Current/Latest will appear).

    ALL data is entirely synthetic. Contains no PHI.
    """
    return make_bp_dataframe(
        num_readings=20,
        duration_weeks=2.5,
        seed=seed,
    )


def make_bp_dataframe_improving(seed: int = 11) -> pd.DataFrame:
    """
    Synthetic DataFrame where SBP is higher in the first two weeks
    (Baseline) and lower in the final two weeks (Current), producing
    an 'improving' progress direction for Avg SBP.

    ALL data is entirely synthetic. Contains no PHI.
    """
    rng = np.random.default_rng(seed)
    start = datetime(2025, 1, 1)
    total_readings = 60
    total_hours = 8 * 7 * 24
    offsets = np.linspace(0, total_hours, num=total_readings)

    # SBP decreases linearly from ~155 to ~125 over the period
    sbp = np.linspace(155, 125, total_readings) + rng.normal(0, 3, total_readings)
    dbp = np.linspace(90, 78, total_readings) + rng.normal(0, 3, total_readings)

    timestamps = [start + timedelta(hours=float(h)) for h in offsets]

    return pd.DataFrame({
        "timestamp_local": pd.to_datetime(timestamps),
        "systolic": sbp.round(1),
        "diastolic": dbp.round(1),
    })
