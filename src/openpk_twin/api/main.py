
"""FastAPI application for OpenPK-Twin."""

from __future__ import annotations

import math

import numpy as np
from fastapi import FastAPI
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from openpk_twin import __version__
from openpk_twin.simulation import (
    simulate_virtual_population_iv_bolus,
    simulate_virtual_population_two_compartment_iv_bolus,
)


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="OpenPK-Twin API",
    description=(
        "Open-source pharmacokinetic modelling and virtual "
        "patient simulation. Educational and research use only."
    ),
    version=__version__,
)


# ---------------------------------------------------------
# COMMON REQUEST VALIDATION
# ---------------------------------------------------------

class PopulationBaseRequest(BaseModel):
    """Shared validation for population simulations."""

    model_config = ConfigDict(extra="forbid")

    times_h: list[float] = Field(min_length=2, max_length=500)

    n_patients: int = Field(
        default=1000,
        ge=1,
        le=10000,
        strict=True,
    )

    seed: int | None = Field(
        default=42,
        ge=0,
        le=4294967295,
    )

    @field_validator("times_h")
    @classmethod
    def validate_times(cls, values):
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
    def validate_workload(self):
        if self.n_patients * len(self.times_h) > 1_000_000:
            raise ValueError(
                "Simulation workload exceeds the API limit."
            )

        return self


# ---------------------------------------------------------
# ONE-COMPARTMENT REQUEST
# ---------------------------------------------------------

class PopulationSimulationRequest(PopulationBaseRequest):
    """One-compartment IV bolus simulation input."""

    dose_mg: float = Field(gt=0)
    typical_volume_of_distribution_L: float = Field(gt=0)
    typical_clearance_L_per_h: float = Field(gt=0)

    cv_clearance: float = Field(default=0.30, ge=0, le=2.0)
    cv_volume: float = Field(default=0.20, ge=0, le=2.0)

    @field_validator(
        "dose_mg",
        "typical_volume_of_distribution_L",
        "typical_clearance_L_per_h",
        "cv_clearance",
        "cv_volume",
    )
    @classmethod
    def validate_finite_values(cls, value):
        if not math.isfinite(value):
            raise ValueError("Values must be finite.")
        return value

    @model_validator(mode="after")
    def validate_parameter_ratios(self):
        ratios = [
            self.dose_mg / self.typical_volume_of_distribution_L,
            self.typical_clearance_L_per_h
            / self.typical_volume_of_distribution_L,
        ]

        if not all(math.isfinite(x) for x in ratios):
            raise ValueError("Parameter ratios exceed numeric limits.")

        return self


# ---------------------------------------------------------
# TWO-COMPARTMENT REQUEST
# ---------------------------------------------------------

class TwoCompartmentPopulationSimulationRequest(
    PopulationBaseRequest
):
    """Two-compartment IV bolus simulation input."""

    dose_mg: float = Field(gt=0)

    typical_central_volume_L: float = Field(gt=0)
    typical_peripheral_volume_L: float = Field(gt=0)

    typical_clearance_L_per_h: float = Field(gt=0)

    intercompartmental_clearance_L_per_h: float = Field(gt=0)

    cv_clearance: float = Field(default=0.30, ge=0, le=2.0)
    cv_central_volume: float = Field(default=0.20, ge=0, le=2.0)
    cv_peripheral_volume: float = Field(default=0.20, ge=0, le=2.0)

    @field_validator(
        "dose_mg",
        "typical_central_volume_L",
        "typical_peripheral_volume_L",
        "typical_clearance_L_per_h",
        "intercompartmental_clearance_L_per_h",
        "cv_clearance",
        "cv_central_volume",
        "cv_peripheral_volume",
    )
    @classmethod
    def validate_finite_values(cls, value):
        if not math.isfinite(value):
            raise ValueError("Values must be finite.")
        return value

    @model_validator(mode="after")
    def validate_parameter_ratios(self):
        ratios = [
            self.dose_mg / self.typical_central_volume_L,
            self.typical_clearance_L_per_h
            / self.typical_central_volume_L,
            self.intercompartmental_clearance_L_per_h
            / self.typical_central_volume_L,
            self.intercompartmental_clearance_L_per_h
            / self.typical_peripheral_volume_L,
        ]

        if not all(math.isfinite(x) for x in ratios):
            raise ValueError("Parameter ratios exceed numeric limits.")

        return self


# ---------------------------------------------------------
# COMMON RESPONSE
# ---------------------------------------------------------

class PopulationSimulationResponse(BaseModel):
    """Structured simulation response."""

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

    mean_central_volume_L: float | None = None
    mean_peripheral_volume_L: float | None = None

    assumptions: list[str]


# ---------------------------------------------------------
# RESPONSE BUILDER
# ---------------------------------------------------------

def build_population_response(
    result,
    request,
    model_name,
    volume_mean,
    assumptions,
    central_volume_mean=None,
    peripheral_volume_mean=None,
):
    """Convert scientific simulation output into API response."""

    concentrations = result["concentrations_mg_per_L"]

    sample_count = min(50, request.n_patients)

    selected_indices = np.linspace(
        0,
        request.n_patients - 1,
        num=sample_count,
        dtype=int,
    )

    return PopulationSimulationResponse(
        model=model_name,
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
            int(i + 1) for i in selected_indices
        ],

        representative_profiles_mg_per_L=(
            concentrations[selected_indices].tolist()
        ),

        mean_clearance_L_per_h=float(
            np.mean(result["clearance_L_per_h"])
        ),

        mean_volume_of_distribution_L=float(volume_mean),

        mean_central_volume_L=central_volume_mean,

        mean_peripheral_volume_L=peripheral_volume_mean,

        assumptions=assumptions,
    )


# ---------------------------------------------------------
# GENERAL ENDPOINTS
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "project": "OpenPK-Twin",
        "version": __version__,
        "description": (
            "Pharmacokinetic modelling and virtual patient simulation"
        ),
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": __version__,
    }


# ---------------------------------------------------------
# ONE-COMPARTMENT SIMULATION ENDPOINT
# ---------------------------------------------------------

@app.post(
    "/api/v1/population/iv-bolus",
    response_model=PopulationSimulationResponse,
    tags=["Population Pharmacokinetics"],
)
def run_population_simulation(
    request: PopulationSimulationRequest,
):
    """Run a one-compartment virtual patient simulation."""

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

    return build_population_response(
        result=result,
        request=request,
        model_name="one-compartment IV bolus",
        volume_mean=float(
            np.mean(result["volume_of_distribution_L"])
        ),
        assumptions=[
            "Single intravenous bolus administration.",
            "One well-mixed compartment.",
            "First-order elimination.",
            "Independent lognormal clearance and volume variability.",
            "Population percentiles describe simulated variability, "
            "not validated clinical prediction intervals.",
        ],
    )


# ---------------------------------------------------------
# TWO-COMPARTMENT SIMULATION ENDPOINT
# ---------------------------------------------------------

@app.post(
    "/api/v1/population/two-compartment/iv-bolus",
    response_model=PopulationSimulationResponse,
    tags=["Population Pharmacokinetics"],
)
def run_two_compartment_population_simulation(
    request: TwoCompartmentPopulationSimulationRequest,
):
    """Run a two-compartment virtual patient simulation."""

    result = simulate_virtual_population_two_compartment_iv_bolus(
        dose_mg=request.dose_mg,
        typical_central_volume_L=request.typical_central_volume_L,
        typical_peripheral_volume_L=(
            request.typical_peripheral_volume_L
        ),
        typical_clearance_L_per_h=request.typical_clearance_L_per_h,
        intercompartmental_clearance_L_per_h=(
            request.intercompartmental_clearance_L_per_h
        ),
        times_h=request.times_h,
        n_patients=request.n_patients,
        cv_clearance=request.cv_clearance,
        cv_central_volume=request.cv_central_volume,
        cv_peripheral_volume=request.cv_peripheral_volume,
        seed=request.seed,
    )

    central_mean = float(
        np.mean(result["central_volume_L"])
    )

    peripheral_mean = float(
        np.mean(result["peripheral_volume_L"])
    )

    return build_population_response(
        result=result,
        request=request,
        model_name="two-compartment IV bolus",
        volume_mean=central_mean + peripheral_mean,
        central_volume_mean=central_mean,
        peripheral_volume_mean=peripheral_mean,
        assumptions=[
            "Single IV bolus into the central compartment.",
            "Two well-mixed compartments.",
            "First-order distribution and elimination.",
            "Elimination occurs from the central compartment.",
            "Independent lognormal clearance and volume variability.",
            "Intercompartmental clearance is fixed.",
            "Population percentiles describe simulated variability, "
            "not validated clinical prediction intervals.",
        ],
    )
