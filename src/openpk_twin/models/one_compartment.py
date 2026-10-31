
"""One-compartment pharmacokinetic model for IV bolus administration."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def calculate_elimination_rate_constant(
    clearance_L_per_h: float,
    volume_of_distribution_L: float,
) -> float:
    """Calculate elimination rate constant (1/hour)."""

    if not np.isfinite(clearance_L_per_h) or clearance_L_per_h <= 0:
        raise ValueError("Clearance must be greater than zero.")

    if not np.isfinite(volume_of_distribution_L) or volume_of_distribution_L <= 0:
        raise ValueError("Volume of distribution must be greater than zero.")

    return clearance_L_per_h / volume_of_distribution_L


def simulate_iv_bolus(
    dose_mg: float,
    volume_of_distribution_L: float,
    clearance_L_per_h: float,
    times_h: ArrayLike,
) -> NDArray[np.float64]:
    """
    Simulate plasma concentrations following a single IV bolus dose.

    Assumptions:
    - Instantaneous intravenous administration
    - Single well-mixed compartment
    - First-order elimination

    Returns concentrations in mg/L.
    """

    if not np.isfinite(dose_mg) or dose_mg <= 0:
        raise ValueError("Dose must be greater than zero.")

    elimination_rate = calculate_elimination_rate_constant(
        clearance_L_per_h,
        volume_of_distribution_L,
    )

    times = np.asarray(times_h, dtype=float)

    if times.size == 0 or not np.all(np.isfinite(times)) or np.any(times < 0):
        raise ValueError("Times must be finite, non-negative and non-empty.")

    initial_concentration = dose_mg / volume_of_distribution_L

    concentrations = initial_concentration * np.exp(
        -elimination_rate * times
    )

    return np.asarray(concentrations, dtype=np.float64)
