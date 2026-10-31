
"""Automated reproducibility tests for OpenPK-Twin."""

import numpy as np
import pytest

from openpk_twin.simulation import (
    simulate_virtual_population_iv_bolus,
    simulate_virtual_population_two_compartment_iv_bolus,
)


TIMES = np.linspace(0, 24, 25)


def run_one_compartment(seed=42):
    return simulate_virtual_population_iv_bolus(
        dose_mg=100.0,
        typical_volume_of_distribution_L=10.0,
        typical_clearance_L_per_h=1.0,
        times_h=TIMES,
        n_patients=1000,
        cv_clearance=0.30,
        cv_volume=0.20,
        seed=seed,
    )


def run_two_compartment(seed=42):
    return simulate_virtual_population_two_compartment_iv_bolus(
        dose_mg=100.0,
        typical_central_volume_L=10.0,
        typical_peripheral_volume_L=20.0,
        typical_clearance_L_per_h=1.0,
        intercompartmental_clearance_L_per_h=2.0,
        times_h=TIMES,
        n_patients=1000,
        cv_clearance=0.30,
        cv_central_volume=0.20,
        cv_peripheral_volume=0.20,
        seed=seed,
    )


@pytest.mark.parametrize(
    "simulation",
    [run_one_compartment, run_two_compartment],
    ids=["one-compartment", "two-compartment"],
)
def test_same_seed_produces_identical_results(simulation):
    """Identical inputs and seeds must produce identical outputs."""

    first = simulation(seed=42)
    second = simulation(seed=42)

    assert first.keys() == second.keys()

    for key in first:
        np.testing.assert_array_equal(
            first[key],
            second[key],
            err_msg=f"Reproducibility failed for {key}",
        )


@pytest.mark.parametrize(
    "simulation",
    [run_one_compartment, run_two_compartment],
    ids=["one-compartment", "two-compartment"],
)
def test_different_seeds_change_population(simulation):
    """Different seeds should generate different virtual populations."""

    first = simulation(seed=42)
    second = simulation(seed=43)

    assert not np.array_equal(
        first["concentrations_mg_per_L"],
        second["concentrations_mg_per_L"],
    )


@pytest.mark.parametrize(
    "simulation",
    [run_one_compartment, run_two_compartment],
    ids=["one-compartment", "two-compartment"],
)
def test_population_percentiles_match_individual_profiles(simulation):
    """Verify percentile summaries against individual simulations."""

    result = simulation(seed=42)

    concentrations = result["concentrations_mg_per_L"]

    expected_05 = np.percentile(concentrations, 5, axis=0)
    expected_50 = np.percentile(concentrations, 50, axis=0)
    expected_95 = np.percentile(concentrations, 95, axis=0)

    np.testing.assert_allclose(
        result["percentile_05_mg_per_L"], expected_05
    )

    np.testing.assert_allclose(
        result["median_mg_per_L"], expected_50
    )

    np.testing.assert_allclose(
        result["percentile_95_mg_per_L"], expected_95
    )

    assert np.all(np.isfinite(concentrations))
