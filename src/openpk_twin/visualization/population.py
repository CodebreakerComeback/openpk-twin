
"""Population pharmacokinetic visualization utilities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from numpy.typing import ArrayLike


def plot_population_profile(
    population_results: Mapping[str, ArrayLike],
    *,
    show_individuals: bool = True,
    max_individuals: int = 100,
    ax: Any = None,
    title: str = "Population Pharmacokinetic Profile",
) -> tuple[Any, Any]:
    """
    Plot individual and population concentration-time profiles.

    Parameters
    ----------
    population_results:
        Output dictionary from the OpenPK-Twin virtual patient engine.

    show_individuals:
        Whether to display individual virtual patient profiles.

    max_individuals:
        Maximum number of individual profiles to display.

    ax:
        Optional Matplotlib axes for integration into another figure.

    title:
        Figure title.

    Returns
    -------
    tuple
        Matplotlib figure and axes objects.

    Notes
    -----
    The shaded 5th–95th percentile interval represents the
    distribution of simulated concentrations at each time point.
    It is not a confidence interval for a population parameter.
    """

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Matplotlib is required for visualization. "
            "Install it using: pip install openpk-twin[viz]"
        ) from exc

    required_keys = [
        "times_h",
        "concentrations_mg_per_L",
        "median_mg_per_L",
        "percentile_05_mg_per_L",
        "percentile_95_mg_per_L",
    ]

    missing = [
        key for key in required_keys
        if key not in population_results
    ]

    if missing:
        raise ValueError(
            f"Missing population result keys: {missing}"
        )

    times = np.asarray(
        population_results["times_h"], dtype=float
    )

    concentrations = np.asarray(
        population_results["concentrations_mg_per_L"],
        dtype=float,
    )

    median = np.asarray(
        population_results["median_mg_per_L"],
        dtype=float,
    )

    lower = np.asarray(
        population_results["percentile_05_mg_per_L"],
        dtype=float,
    )

    upper = np.asarray(
        population_results["percentile_95_mg_per_L"],
        dtype=float,
    )

    if (
        times.ndim != 1
        or times.size < 2
        or not np.all(np.isfinite(times))
        or np.any(times < 0)
        or np.any(np.diff(times) <= 0)
    ):
        raise ValueError(
            "Times must be finite, non-negative and strictly increasing."
        )

    if concentrations.ndim != 2:
        raise ValueError(
            "Individual concentrations must be a 2D array."
        )

    if concentrations.shape[0] < 1 or concentrations.shape[1] != times.size:
        raise ValueError(
            "Concentration matrix must contain patients and match the time points."
        )

    for name, values in {
        "Concentrations": concentrations,
        "Median": median,
        "5th percentile": lower,
        "95th percentile": upper,
    }.items():
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            raise ValueError(
                f"{name} values must be finite and non-negative."
            )

    if any(
        values.shape != times.shape
        for values in (median, lower, upper)
    ):
        raise ValueError(
            "Population percentile arrays must match the time array."
        )

    if not np.all(lower <= median) or not np.all(median <= upper):
        raise ValueError(
            "Population percentile ordering is invalid."
        )

    if (
        isinstance(max_individuals, bool)
        or not isinstance(max_individuals, (int, np.integer))
        or max_individuals < 1
    ):
        raise ValueError(
            "max_individuals must be a positive integer."
        )

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure

    if show_individuals:
        n_patients = concentrations.shape[0]

        if n_patients > max_individuals:
            indices = np.linspace(
                0,
                n_patients - 1,
                num=max_individuals,
                dtype=int,
            )
        else:
            indices = np.arange(n_patients)

        for index in indices:
            ax.plot(
                times,
                concentrations[index],
                linewidth=0.7,
                alpha=0.12,
            )

    ax.fill_between(
        times,
        lower,
        upper,
        alpha=0.22,
        label="5th–95th percentile",
    )

    ax.plot(
        times,
        median,
        linewidth=2.2,
        label="Median population profile",
    )

    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Plasma concentration (mg/L)")
    ax.set_title(title)

    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()

    return fig, ax
