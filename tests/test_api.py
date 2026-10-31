
import pytest
from fastapi.testclient import TestClient

from openpk_twin.api.main import app


client = TestClient(app)


def valid_payload():
    """Return a valid population simulation request."""

    return {
        "dose_mg": 100,
        "typical_volume_of_distribution_L": 10,
        "typical_clearance_L_per_h": 1,
        "times_h": [0, 1, 2, 4, 8, 12, 24],
        "n_patients": 100,
        "cv_clearance": 0.30,
        "cv_volume": 0.20,
        "seed": 42,
    }


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "OpenPK-Twin"
    assert response.json()["documentation"] == "/docs"


def test_population_simulation_endpoint():
    response = client.post(
        "/api/v1/population/iv-bolus",
        json=valid_payload(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["model"] == "one-compartment IV bolus"
    assert data["n_patients"] == 100
    assert len(data["times_h"]) == 7

    assert len(data["median_mg_per_L"]) == 7
    assert len(data["percentile_05_mg_per_L"]) == 7
    assert len(data["percentile_95_mg_per_L"]) == 7

    assert len(data["representative_profiles_mg_per_L"]) == 50

    assert data["median_mg_per_L"][0] > 0


def test_population_percentile_order():
    response = client.post(
        "/api/v1/population/iv-bolus",
        json=valid_payload(),
    )

    data = response.json()

    lower = data["percentile_05_mg_per_L"]
    median = data["median_mg_per_L"]
    upper = data["percentile_95_mg_per_L"]

    assert all(
        l <= m <= u
        for l, m, u in zip(lower, median, upper)
    )


def test_reproducible_api_simulation():
    payload = valid_payload()

    first = client.post(
        "/api/v1/population/iv-bolus",
        json=payload,
    )

    second = client.post(
        "/api/v1/population/iv-bolus",
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert (
        first.json()["median_mg_per_L"]
        == second.json()["median_mg_per_L"]
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"dose_mg": 0},
        {"dose_mg": -100},
        {"typical_clearance_L_per_h": 0},
        {"typical_volume_of_distribution_L": 0},
        {"n_patients": 0},
        {"n_patients": 10001},
        {"cv_clearance": 2.1},
        {"times_h": [0, 2, 1]},
        {"times_h": [-1, 0, 1]},
        {"times_h": [0, 1, 1]},
        {"extra_parameter": 123},
    ],
)
def test_invalid_requests_are_rejected(changes):
    payload = valid_payload()
    payload.update(changes)

    response = client.post(
        "/api/v1/population/iv-bolus",
        json=payload,
    )

    assert response.status_code == 422


def test_simulation_workload_limit():
    payload = valid_payload()

    payload["n_patients"] = 3000
    payload["times_h"] = list(range(500))

    response = client.post(
        "/api/v1/population/iv-bolus",
        json=payload,
    )

    assert response.status_code == 422
