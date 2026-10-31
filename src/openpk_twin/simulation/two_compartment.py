
"""Monte Carlo two-compartment virtual patient simulation."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _draw_lognormal(
    typical_value: float,
    cv: float,
    size: int,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Generate lognormal values preserving the arithmetic mean."""

    sigma = np.sqrt(np.log1p(cv**2))

    return typical_value * rng.lognormal(
        mean=-0.5 * sigma**2,
        sigma=sigma,
        size=size,
    )


def simulate_virtual_population_two_compartment_iv_bolus(
    dose_mg: float,
    typical_central_volume_L: float,
    typical_peripheral_volume_L: float,
    typical_clearance_L_per_h: float,
    intercompartmental_clearance_L_per_h: float,
    times_h: ArrayLike,
    n_patients: int = 1000,
    cv_clearance: float = 0.30,
    cv_central_volume: float = 0.20,
    cv_peripheral_volume: float = 0.20,
    seed: int | None = None,
) -> dict[str, NDArray[np.float64]]:
    """
    Simulate a virtual population using a two-compartment IV bolus model.

    Variability in clearance and compartment volumes is represented
    using independent lognormal distributions.

    Intercompartmental clearance is fixed across patients.

    Returns individual PK parameters, concentration profiles,
    median concentration and 5th/95th percentiles.
    """

    positive_parameters = {
        "Dose": dose_mg,
        "Central volume": typical_central_volume_L,
        "Peripheral volume": typical_peripheral_volume_L,
        "Clearance": typical_clearance_L_per_h,
        "Intercompartmental clearance":
            intercompartmental_clearance_L_per_h,
    }

    for name, value in positive_parameters.items():
        if not np.isfinite(value) or value <= 0:
            raise ValueError(
                f"{name} must be finite and greater than zero."
            )

    if (
        isinstance(n_patients, bool)
        or not isinstance(n_patients, (int, np.integer))
        or n_patients < 1
    ):
        raise ValueError(
            "Number of patients must be a positive integer."
        )

    cv_values = {
        "Clearance CV": cv_clearance,
        "Central volume CV": cv_central_volume,
        "Peripheral volume CV": cv_peripheral_volume,
    }

    for name, cv in cv_values.items():
        if not np.isfinite(cv) or cv < 0:
            raise ValueError(
                f"{name} must be finite and non-negative."
            )

    if seed is not None and (
        isinstance(seed, bool)
        or not isinstance(seed, (int, np.integer))
        or seed < 0
    ):
        raise ValueError("Seed must be a non-negative integer or None.")

    times = np.asarray(times_h, dtype=float)

    if (
        times.ndim != 1
        or times.size == 0
        or not np.all(np.isfinite(times))
        or np.any(times < 0)
        or np.any(np.diff(times) <= 0)
    ):
        raise ValueError(
            "Times must be finite, non-negative and strictly increasing."
        )

    rng = np.random.default_rng(seed)

    # Generate individual virtual patient parameters.
    clearance = _draw_lognormal(
        typical_clearance_L_per_h,
        cv_clearance,
        n_patients,
        rng,
    )

    central_volume = _draw_lognormal(
        typical_central_volume_L,
        cv_central_volume,
        n_patients,
        rng,
    )

    peripheral_volume = _draw_lognormal(
        typical_peripheral_volume_L,
        cv_peripheral_volume,
        n_patients,
        rng,
    )

    # Calculate individual microconstants.
    k10 = clearance / central_volume

    k12 = (
        intercompartmental_clearance_L_per_h
        / central_volume
    )

    k21 = (
        intercompartmental_clearance_L_per_h
        / peripheral_volume
    )

    # Calculate biexponential hybrid rate constants.
    rate_sum = k10 + k12 + k21

    discriminant = rate_sum**2 - 4.0 * k10 * k21

    sqrt_discriminant = np.sqrt(discriminant)

    alpha = 0.5 * (rate_sum + sqrt_discriminant)

    beta = (k10 * k21) / alpha

    coefficient_a = (alpha - k21) / (alpha - beta)

    coefficient_b = (k21 - beta) / (alpha - beta)

    # Vectorised central compartment concentration.
    initial_concentration = dose_mg / central_volume

    concentrations = initial_concentration[:, None] * (
        coefficient_a[:, None]
        * np.exp(-alpha[:, None] * times[None, :])
        +
        coefficient_b[:, None]
        * np.exp(-beta[:, None] * times[None, :])
    )

    return {
        "times_h": times,
        "clearance_L_per_h": clearance,
        "central_volume_L": central_volume,
        "peripheral_volume_L": peripheral_volume,
        "concentrations_mg_per_L": concentrations,
        "median_mg_per_L": np.percentile(
            concentrations, 50, axis=0
        ),
        "percentile_05_mg_per_L": np.percentile(
            concentrations, 5, axis=0
        ),
        "percentile_95_mg_per_L": np.percentile(
            concentrations, 95, axis=0
        ),
    }
