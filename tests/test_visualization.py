
import matplotlib

# Use a non-interactive backend for automated testing.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from openpk_twin.simulation import simulate_virtual_population_iv_bolus
from openpk_twin.visualization import plot_population_profile


@pytest.fixture
def population_results():
    """Generate a reproducible virtual population."""

    return simulate_virtual_population_iv_bolus(
        dose_mg=100,
        typical_volume_of_distribution_L=10,
        typical_clearance_L_per_h=1,
        times_h=np.linspace(0, 24, 25),
        n_patients=20,
        seed=42,
    )


def test_population_plot_creation(population_results):
    """Verify that a valid population plot is created."""

    fig, ax = plot_population_profile(population_results)

    assert fig is not None
    assert ax is not None

    assert ax.get_xlabel() == "Time (hours)"
    assert ax.get_ylabel() == "Plasma concentration (mg/L)"

    assert len(ax.lines) == 21
    assert len(ax.collections) == 1

    plt.close(fig)


def test_population_plot_without_individuals(population_results):
    """Verify population-only plotting."""

    fig, ax = plot_population_profile(
        population_results,
        show_individuals=False,
    )

    assert len(ax.lines) == 1
    assert len(ax.collections) == 1

    plt.close(fig)


def test_maximum_individual_curves(population_results):
    """Check that individual curves are limited correctly."""

    fig, ax = plot_population_profile(
        population_results,
        max_individuals=5,
    )

    # Five individual curves plus one median curve.
    assert len(ax.lines) == 6

    plt.close(fig)


def test_custom_title(population_results):
    """Check custom plot titles."""

    fig, ax = plot_population_profile(
        population_results,
        title="OpenPK-Twin Population Analysis",
    )

    assert ax.get_title() == "OpenPK-Twin Population Analysis"

    plt.close(fig)


def test_existing_axes_reused(population_results):
    """Verify integration into an existing Matplotlib figure."""

    fig, ax = plt.subplots()

    returned_fig, returned_ax = plot_population_profile(
        population_results,
        ax=ax,
    )

    assert returned_fig is fig
    assert returned_ax is ax

    plt.close(fig)


def test_invalid_percentile_order(population_results):
    """Reject incorrectly ordered population percentiles."""

    invalid = dict(population_results)

    invalid["percentile_05_mg_per_L"] = (
        population_results["percentile_95_mg_per_L"]
    )

    invalid["percentile_95_mg_per_L"] = (
        population_results["percentile_05_mg_per_L"]
    )

    with pytest.raises(ValueError):
        plot_population_profile(invalid)


def test_invalid_sampling_times(population_results):
    """Reject duplicated or non-increasing sampling times."""

    invalid = dict(population_results)
    invalid["times_h"] = np.array(
        [0, 1, 1] + list(range(3, 25))
    )

    with pytest.raises(ValueError):
        plot_population_profile(invalid)


def test_missing_required_key(population_results):
    """Reject incomplete simulation outputs."""

    invalid = dict(population_results)
    del invalid["median_mg_per_L"]

    with pytest.raises(ValueError):
        plot_population_profile(invalid)


@pytest.mark.parametrize(
    "limit",
    [0, -1, True, 2.5],
)
def test_invalid_individual_limit(population_results, limit):
    """Reject invalid individual curve limits."""

    with pytest.raises(ValueError):
        plot_population_profile(
            population_results,
            max_individuals=limit,
        )
