
"""Two-compartment pharmacokinetic model for IV bolus administration."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def simulate_two_compartment_iv_bolus(
    dose_mg: float,
    central_volume_L: float,
    peripheral_volume_L: float,
    clearance_L_per_h: float,
    intercompartmental_clearance_L_per_h: float,
    times_h: ArrayLike,
) -> NDArray[np.float64]:
    """
    Simulate central plasma concentration after a single IV bolus.

    Assumptions:
    - Instantaneous IV bolus into the central compartment.
    - Linear distribution between two well-mixed compartments.
    - First-order elimination from the central compartment.

    Returns
    -------
    numpy.ndarray
        Central compartment concentrations in mg/L.
    """

    parameters = {
        "Dose": dose_mg,
        "Central volume": central_volume_L,
        "Peripheral volume": peripheral_volume_L,
        "Clearance": clearance_L_per_h,
        "Intercompartmental clearance": intercompartmental_clearance_L_per_h,
    }

    for name, value in parameters.items():
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and greater than zero.")

    times = np.asarray(times_h, dtype=float)

    if (
        times.size == 0
        or not np.all(np.isfinite(times))
        or np.any(times < 0)
    ):
        raise ValueError(
            "Sampling times must be finite, non-negative and non-empty."
        )

    # Calculate pharmacokinetic microconstants (1/hour).
    k10 = clearance_L_per_h / central_volume_L
    k12 = intercompartmental_clearance_L_per_h / central_volume_L
    k21 = intercompartmental_clearance_L_per_h / peripheral_volume_L

    # Calculate hybrid macroconstants (alpha and beta).
    rate_sum = k10 + k12 + k21

    discriminant = rate_sum**2 - 4.0 * k10 * k21
    sqrt_discriminant = np.sqrt(discriminant)

    alpha = 0.5 * (rate_sum + sqrt_discriminant)
    beta = (k10 * k21) / alpha

    # Calculate biexponential coefficients.
    coefficient_a = (alpha - k21) / (alpha - beta)
    coefficient_b = (k21 - beta) / (alpha - beta)

    initial_concentration = dose_mg / central_volume_L

    concentrations = initial_concentration * (
        coefficient_a * np.exp(-alpha * times)
        + coefficient_b * np.exp(-beta * times)
    )

    return np.asarray(concentrations, dtype=np.float64)
