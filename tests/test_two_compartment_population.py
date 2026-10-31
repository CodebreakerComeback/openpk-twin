
import numpy as np
import pytest

from openpk_twin.models.two_compartment import (
    simulate_two_compartment_iv_bolus,
)

from openpk_twin.simulation import (
    simulate_virtual_population_two_compartment_iv_bolus,
)


def run_population(seed=42, cv_cl=0.30, cv_vc=0.20, cv_vp=0.20, n=1000):
    return simulate_virtual_population_two_compartment_iv_bolus(
        dose_mg=100.0,
        typical_central_volume_L=10.0,
        typical_peripheral_volume_L=20.0,
        typical_clearance_L_per_h=1.0,
        intercompartmental_clearance_L_per_h=2.0,
        times_h=np.linspace(0, 24, 25),
        n_patients=n,
        cv_clearance=cv_cl,
        cv_central_volume=cv_vc,
        cv_peripheral_volume=cv_vp,
        seed=seed,
    )


def test_population_output_shapes():
    result = run_population()

    assert result["concentrations_mg_per_L"].shape == (1000, 25)
    assert result["median_mg_per_L"].shape == (25,)
    assert result["percentile_05_mg_per_L"].shape == (25,)
    assert result["percentile_95_mg_per_L"].shape == (25,)


def test_initial_concentration():
    result = run_population()

    expected = 100.0 / 10.0

    np.testing.assert_allclose(
        result["concentrations_mg_per_L"][:, 0],
        expected,
    )


def test_zero_variability_matches_deterministic_model():
    """Population profiles must match the deterministic model."""

    times = np.linspace(0, 24, 25)

    result = run_population(
        cv_cl=0,
        cv_vc=0,
        cv_vp=0,
        n=100,
    )

    expected = simulate_two_compartment_iv_bolus(
        dose_mg=100.0,
        central_volume_L=10.0,
        peripheral_volume_L=20.0,
        clearance_L_per_h=1.0,
        intercompartmental_clearance_L_per_h=2.0,
        times_h=times,
    )

    for profile in result["concentrations_mg_per_L"]:
        np.testing.assert_allclose(
            profile,
            expected,
            rtol=1e-10,
        )


def test_reproducibility():
    first = run_population(seed=123)
    second = run_population(seed=123)

    for key in first:
        np.testing.assert_array_equal(
            first[key],
            second[key],
        )


def test_population_variability():
    result = run_population(n=2000)

    assert np.std(result["clearance_L_per_h"]) > 0
    assert np.std(result["central_volume_L"]) > 0
    assert np.std(result["peripheral_volume_L"]) > 0


def test_percentile_ordering():
    result = run_population()

    assert np.all(
        result["percentile_05_mg_per_L"]
        <= result["median_mg_per_L"]
    )

    assert np.all(
        result["median_mg_per_L"]
        <= result["percentile_95_mg_per_L"]
    )


def test_concentrations_are_positive_and_decreasing():
    result = run_population()

    concentrations = result["concentrations_mg_per_L"]

    assert np.all(concentrations > 0)
    assert np.all(np.diff(concentrations, axis=1) < 0)


def test_parameter_means_are_preserved():
    result = run_population(n=20000)

    assert np.mean(result["clearance_L_per_h"]) == pytest.approx(
        1.0, rel=0.02
    )

    assert np.mean(result["central_volume_L"]) == pytest.approx(
        10.0, rel=0.02
    )

    assert np.mean(result["peripheral_volume_L"]) == pytest.approx(
        20.0, rel=0.02
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"dose_mg": 0},
        {"central_volume_L": 0},
        {"peripheral_volume_L": 0},
        {"clearance_L_per_h": 0},
        {"intercompartmental_clearance_L_per_h": 0},
        {"n_patients": 0},
        {"cv_clearance": -0.1},
        {"cv_central_volume": -0.1},
        {"cv_peripheral_volume": -0.1},
        {"times_h": [-1, 0, 1]},
        {"times_h": [0, 2, 1]},
        {"times_h": [0, float("nan"), 2]},
        {"seed": -1},
    ],
)
def test_invalid_inputs(changes):
    parameters = {
        "dose_mg": 100.0,
        "typical_central_volume_L": 10.0,
        "typical_peripheral_volume_L": 20.0,
        "typical_clearance_L_per_h": 1.0,
        "intercompartmental_clearance_L_per_h": 2.0,
        "times_h": [0, 1, 2, 4, 8],
        "n_patients": 100,
        "cv_clearance": 0.30,
        "cv_central_volume": 0.20,
        "cv_peripheral_volume": 0.20,
        "seed": 42,
    }

    parameters.update(changes)

    with pytest.raises(ValueError):
        simulate_virtual_population_two_compartment_iv_bolus(
            **parameters
        )
