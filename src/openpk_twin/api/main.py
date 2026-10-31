
"""FastAPI application for OpenPK-Twin."""

from __future__ import annotations

import math

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from openpk_twin import __version__
from openpk_twin.simulation import simulate_virtual_population_iv_bolus


app = FastAPI(
    title="OpenPK-Twin API",
    description=(
        "An open-source API for pharmacokinetic modelling "
        "and virtual patient simulation. Educational and "
        "research use only."
    ),
    version=__version__,
)


class PopulationSimulationRequest(BaseModel):
    """Validated input parameters for population simulation."""

    model_config = ConfigDict(extra="forbid")

    dose_mg: float = Field(gt=0)
    typical_volume_of_distribution_L: float = Field(gt=0)
    typical_clearance_L_per_h: float = Field(gt=0)

    times_h: list[float] = Field(min_length=2, max_length=500)

    n_patients: int = Field(default=1000, ge=1, le=10000, strict=True)

    cv_clearance: float = Field(default=0.30, ge=0, le=2.0)
    cv_volume: float = Field(default=0.20, ge=0, le=2.0)

    seed: int | None = Field(default=42, ge=0, le=4294967295)

    @field_validator(
        "dose_mg",
        "typical_volume_of_distribution_L",
        "typical_clearance_L_per_h",
        "cv_clearance",
        "cv_volume",
    )
    @classmethod
    def validate_finite_values(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("Values must be finite.")
        return value

    @field_validator("times_h")
    @classmethod
    def validate_times(cls, values: list[float]) -> list[float]:
        if not all(math.isfinite(t) for t in values):
            raise ValueError("Sampling times must be finite.")

        if any(t < 0 for t in values):
            raise ValueError("Sampling times cannot be negative.")

        if any(
            current <= previous
            for previous, current in zip(values, values[1:])
        ):
            raise ValueError(
                "Sampling times must be strictly increasing."
            )

        return values

    @model_validator(mode="after")
    def validate_simulation_limits(self):
        if self.n_patients * len(self.times_h) > 1_000_000:
            raise ValueError(
                "Simulation workload exceeds the API limit. "
                "Reduce patient count or sampling points."
            )

        if not math.isfinite(
            self.dose_mg / self.typical_volume_of_distribution_L
        ):
            raise ValueError("Initial concentration is outside numeric limits.")

        if not math.isfinite(
            self.typical_clearance_L_per_h
            / self.typical_volume_of_distribution_L
        ):
            raise ValueError("Elimination rate is outside numeric limits.")

        return self


class PopulationSimulationResponse(BaseModel):
    """Structured output from the population simulation."""

    model: str
    n_patients: int
    seed: int | None

    times_h: list[float]

    median_mg_per_L: list[float]
    percentile_05_mg_per_L: list[float]
    percentile_95_mg_per_L: list[float]

    representative_patient_ids: list[int]
    representative_profiles_mg_per_L: list[list[float]]

    mean_clearance_L_per_h: float
    mean_volume_of_distribution_L: float

    assumptions: list[str]


@app.get("/")
def root():
    """Return basic project information."""

    return {
        "project": "OpenPK-Twin",
        "version": __version__,
        "description": "Pharmacokinetic modelling and virtual patient simulation",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Check whether the API is running."""

    return {
        "status": "ok",
        "version": __version__,
    }


@app.post(
    "/api/v1/population/iv-bolus",
    response_model=PopulationSimulationResponse,
    tags=["Population Pharmacokinetics"],
    summary="Run a virtual patient IV bolus simulation",
)
def run_population_simulation(
    request: PopulationSimulationRequest,
) -> PopulationSimulationResponse:
    """Run a reproducible Monte Carlo population simulation."""

    result = simulate_virtual_population_iv_bolus(
        dose_mg=request.dose_mg,
        typical_volume_of_distribution_L=(
            request.typical_volume_of_distribution_L
        ),
        typical_clearance_L_per_h=request.typical_clearance_L_per_h,
        times_h=request.times_h,
        n_patients=request.n_patients,
        cv_clearance=request.cv_clearance,
        cv_volume=request.cv_volume,
        seed=request.seed,
    )

    concentrations = result["concentrations_mg_per_L"]

    # Return at most 50 representative profiles to limit response size.
    sample_count = min(50, request.n_patients)

    selected_indices = np.linspace(
        0,
        request.n_patients - 1,
        num=sample_count,
        dtype=int,
    )

    return PopulationSimulationResponse(
        model="one-compartment IV bolus",
        n_patients=request.n_patients,
        seed=request.seed,
        times_h=result["times_h"].tolist(),
        median_mg_per_L=result["median_mg_per_L"].tolist(),
        percentile_05_mg_per_L=(
            result["percentile_05_mg_per_L"].tolist()
        ),
        percentile_95_mg_per_L=(
            result["percentile_95_mg_per_L"].tolist()
        ),
        representative_patient_ids=[
            int(index + 1) for index in selected_indices
        ],
        representative_profiles_mg_per_L=(
            concentrations[selected_indices].tolist()
        ),
        mean_clearance_L_per_h=float(
            np.mean(result["clearance_L_per_h"])
        ),
        mean_volume_of_distribution_L=float(
            np.mean(result["volume_of_distribution_L"])
        ),
        assumptions=[
            "Single intravenous bolus administration.",
            "One well-mixed pharmacokinetic compartment.",
            "First-order elimination.",
            "Independent lognormal clearance and volume variability.",
            "Population percentiles describe simulated variability, "
            "not validated clinical prediction intervals.",
        ],
    )
