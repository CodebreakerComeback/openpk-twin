
import numpy as np
import pytest

from openpk_twin.models.one_compartment import (
    calculate_elimination_rate_constant,
    simulate_iv_bolus,
)


def test_elimination_rate_constant():
    """Verify k = CL / Vd."""

    result = calculate_elimination_rate_constant(
        clearance_L_per_h=1.0,
        volume_of_distribution_L=10.0,
    )

    assert result == pytest.approx(0.1)


def test_initial_plasma_concentration():
    """Verify C0 = Dose / Vd."""

    result = simulate_iv_bolus(
        dose_mg=100.0,
        volume_of_distribution_L=10.0,
        clearance_L_per_h=1.0,
        times_h=[0.0],
    )

    assert result[0] == pytest.approx(10.0)


def test_concentration_time_profile():
    """Verify the analytical one-compartment equation."""

    times = np.array([0.0, 10.0, 20.0])

    expected = 10.0 * np.exp(-0.1 * times)

    observed = simulate_iv_bolus(
        dose_mg=100.0,
        volume_of_distribution_L=10.0,
        clearance_L_per_h=1.0,
        times_h=times,
    )

    np.testing.assert_allclose(observed, expected)


@pytest.mark.parametrize(
    "dose, vd, clearance, times",
    [
        (0.0, 10.0, 1.0, [0.0]),
        (-10.0, 10.0, 1.0, [0.0]),
        (100.0, 0.0, 1.0, [0.0]),
        (100.0, 10.0, 0.0, [0.0]),
        (100.0, 10.0, 1.0, [-1.0]),
        (100.0, 10.0, 1.0, []),
    ],
)
def test_invalid_inputs_raise_errors(dose, vd, clearance, times):
    """Ensure invalid inputs are rejected."""

    with pytest.raises(ValueError):
        simulate_iv_bolus(
            dose_mg=dose,
            volume_of_distribution_L=vd,
            clearance_L_per_h=clearance,
            times_h=times,
        )
