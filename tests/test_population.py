
import numpy as np
import pytest

from openpk_twin.models.one_compartment import simulate_iv_bolus
from openpk_twin.simulation.population import (
    simulate_virtual_population_iv_bolus,
)


def run_population(seed=42, cv_cl=0.30, cv_vd=0.20, n=1000):
    return simulate_virtual_population_iv_bolus(
        dose_mg=100.0,
        typical_volume_of_distribution_L=10.0,
        typical_clearance_L_per_h=1.0,
        times_h=np.linspace(0, 24, 25),
        n_patients=n,
        cv_clearance=cv_cl,
        cv_volume=cv_vd,
        seed=seed,
    )


def test_output_shapes_and_percentiles():
    result = run_population()

    assert result["concentrations_mg_per_L"].shape == (1000, 25)
    assert result["median_mg_per_L"].shape == (25,)
    assert result["percentile_05_mg_per_L"].shape == (25,)
    assert result["percentile_95_mg_per_L"].shape == (25,)

    assert np.all(
        result["percentile_05_mg_per_L"]
        <= result["median_mg_per_L"]
    )

    assert np.all(
        result["median_mg_per_L"]
        <= result["percentile_95_mg_per_L"]
    )


def test_reproducibility_with_same_seed():
    first = run_population(seed=123)
    second = run_population(seed=123)

    for key in first:
        np.testing.assert_array_equal(first[key], second[key])


def test_population_parameter_variability():
    result = run_population(n=2000)

    clearance = result["clearance_L_per_h"]
    volume = result["volume_of_distribution_L"]

    assert np.std(clearance) > 0
    assert np.std(volume) > 0

    assert np.all(clearance > 0)
    assert np.all(volume > 0)


def test_zero_variability_matches_single_patient_model():
    result = run_population(
        cv_cl=0,
        cv_vd=0,
        n=100,
    )

    expected = simulate_iv_bolus(
        dose_mg=100.0,
        volume_of_distribution_L=10.0,
        clearance_L_per_h=1.0,
        times_h=np.linspace(0, 24, 25),
    )

    observed = result["concentrations_mg_per_L"]

    for patient_profile in observed:
        np.testing.assert_allclose(patient_profile, expected)

    assert np.all(result["clearance_L_per_h"] == 1.0)
    assert np.all(result["volume_of_distribution_L"] == 10.0)


def test_individual_concentrations_decrease_over_time():
    result = run_population()

    concentrations = result["concentrations_mg_per_L"]

    assert np.all(concentrations > 0)
    assert np.all(np.diff(concentrations, axis=1) < 0)


def test_population_means_are_reasonably_preserved():
    result = run_population(n=20000)

    assert np.mean(result["clearance_L_per_h"]) == pytest.approx(
        1.0, rel=0.02
    )

    assert np.mean(result["volume_of_distribution_L"]) == pytest.approx(
        10.0, rel=0.02
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"n_patients": 0},
        {"n_patients": -10},
        {"dose_mg": -100},
        {"cv_clearance": -0.1},
        {"cv_volume": -0.2},
        {"typical_clearance_L_per_h": 0},
        {"typical_volume_of_distribution_L": 0},
        {"times_h": [-1, 0, 1]},
        {"times_h": [0, float("nan"), 2]},
        {"times_h": [[0, 1], [2, 3]]},
    ],
)
def test_invalid_population_inputs(overrides):
    parameters = {
        "dose_mg": 100.0,
        "typical_volume_of_distribution_L": 10.0,
        "typical_clearance_L_per_h": 1.0,
        "times_h": [0, 1, 2],
        "n_patients": 100,
        "cv_clearance": 0.30,
        "cv_volume": 0.20,
        "seed": 42,
    }

    parameters.update(overrides)

    with pytest.raises(ValueError):
        simulate_virtual_population_iv_bolus(**parameters)
