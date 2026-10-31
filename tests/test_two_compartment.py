
import numpy as np
import pytest

from openpk_twin.models.two_compartment import (
    simulate_two_compartment_iv_bolus,
)


def test_initial_concentration():
    """Initial concentration should equal Dose / central volume."""

    result = simulate_two_compartment_iv_bolus(
        dose_mg=100,
        central_volume_L=10,
        peripheral_volume_L=20,
        clearance_L_per_h=1,
        intercompartmental_clearance_L_per_h=2,
        times_h=[0],
    )

    assert result[0] == pytest.approx(10.0)


def test_reference_concentration_profile():
    """Check the model against independently calculated values."""

    times = [0, 1, 4, 8, 12]

    expected = [
        10.0,
        7.4875939233,
        3.6709191786,
        2.1038521171,
        1.6216950790,
    ]

    observed = simulate_two_compartment_iv_bolus(
        dose_mg=100,
        central_volume_L=10,
        peripheral_volume_L=20,
        clearance_L_per_h=1,
        intercompartmental_clearance_L_per_h=2,
        times_h=times,
    )

    np.testing.assert_allclose(
        observed,
        expected,
        rtol=1e-8,
    )


def test_concentration_decreases_over_time():
    """Verify positive parameters produce a declining profile."""

    times = np.linspace(0, 24, 100)

    concentrations = simulate_two_compartment_iv_bolus(
        dose_mg=100,
        central_volume_L=10,
        peripheral_volume_L=20,
        clearance_L_per_h=1,
        intercompartmental_clearance_L_per_h=2,
        times_h=times,
    )

    assert np.all(np.diff(concentrations) < 0)


@pytest.mark.parametrize(
    "dose, vc, vp, cl, q, times",
    [
        (0, 10, 20, 1, 2, [0]),
        (100, 0, 20, 1, 2, [0]),
        (100, 10, 0, 1, 2, [0]),
        (100, 10, 20, 0, 2, [0]),
        (100, 10, 20, 1, 0, [0]),
        (100, 10, 20, 1, 2, [-1]),
        (100, 10, 20, 1, 2, []),
        (100, 10, 20, 1, 2, [float("nan")]),
    ],
)
def test_invalid_inputs(dose, vc, vp, cl, q, times):
    """Invalid parameters must raise ValueError."""

    with pytest.raises(ValueError):
        simulate_two_compartment_iv_bolus(
            dose_mg=dose,
            central_volume_L=vc,
            peripheral_volume_L=vp,
            clearance_L_per_h=cl,
            intercompartmental_clearance_L_per_h=q,
            times_h=times,
        )
