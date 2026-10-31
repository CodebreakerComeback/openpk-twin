
"""Monte Carlo virtual patient simulation for IV bolus pharmacokinetics."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _lognormal_sigma(cv: float) -> float:
    """Convert coefficient of variation into lognormal SD."""
    return float(np.sqrt(np.log1p(cv**2)))


def simulate_virtual_population_iv_bolus(
    dose_mg: float,
    typical_volume_of_distribution_L: float,
    typical_clearance_L_per_h: float,
    times_h: ArrayLike,
    n_patients: int = 1000,
    cv_clearance: float = 0.30,
    cv_volume: float = 0.20,
    seed: int | None = None,
) -> dict[str, NDArray[np.float64]]:
    """
    Simulate a virtual patient population using a one-compartment
    IV bolus pharmacokinetic model.

    Inter-individual variability in clearance and volume of
    distribution is modelled using independent lognormal distributions.

    CV values are fractions (e.g. 0.30 means 30%).

    Returns individual PK parameters, concentration profiles,
    median concentrations and 5th/95th population percentiles.
    """

    positive_parameters = {
        "Dose": dose_mg,
        "Typical volume of distribution":
            typical_volume_of_distribution_L,
        "Typical clearance": typical_clearance_L_per_h,
    }

    for name, value in positive_parameters.items():
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive.")

    if (
        isinstance(n_patients, bool)
        or not isinstance(n_patients, (int, np.integer))
        or n_patients < 1
    ):
        raise ValueError("Number of patients must be a positive integer.")

    for name, cv in {
        "Clearance CV": cv_clearance,
        "Volume CV": cv_volume,
    }.items():
        if not np.isfinite(cv) or cv < 0:
            raise ValueError(f"{name} must be finite and non-negative.")

    times = np.asarray(times_h, dtype=float)

    if (
        times.ndim != 1
        or times.size == 0
        or not np.all(np.isfinite(times))
        or np.any(times < 0)
    ):
        raise ValueError(
            "Sampling times must be a non-empty, finite, "
            "one-dimensional array of non-negative values."
        )

    rng = np.random.default_rng(seed)

    # Convert variability into lognormal distribution parameters.
    sigma_cl = _lognormal_sigma(cv_clearance)
    sigma_vd = _lognormal_sigma(cv_volume)

    # Generate reproducible individual patient parameters.
    # The -0.5 * sigma**2 correction preserves the arithmetic mean.
    clearance = typical_clearance_L_per_h * rng.lognormal(
        mean=-0.5 * sigma_cl**2,
        sigma=sigma_cl,
        size=n_patients,
    )

    volume = typical_volume_of_distribution_L * rng.lognormal(
        mean=-0.5 * sigma_vd**2,
        sigma=sigma_vd,
        size=n_patients,
    )

    # Individual elimination rate constants.
    elimination_rate = clearance / volume

    # Vectorised one-compartment IV bolus simulation.
    concentrations = (
        dose_mg / volume[:, np.newaxis]
    ) * np.exp(
        -elimination_rate[:, np.newaxis] * times[np.newaxis, :]
    )

    return {
        "times_h": times,
        "clearance_L_per_h": clearance,
        "volume_of_distribution_L": volume,
        "concentrations_mg_per_L": concentrations,
        "median_mg_per_L": np.percentile(concentrations, 50, axis=0),
        "percentile_05_mg_per_L": np.percentile(concentrations, 5, axis=0),
        "percentile_95_mg_per_L": np.percentile(concentrations, 95, axis=0),
    }
