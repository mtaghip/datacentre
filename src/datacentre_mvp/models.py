"""Data models for the auditable MVP calculation core."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Redundancy(StrEnum):
    """Supported concept-stage redundancy targets."""

    N = "N"
    N_PLUS_1 = "N+1"
    N_PLUS_2 = "N+2"
    TWO_N = "2N"


class ReviewStatus(StrEnum):
    """Engineering maturity labels for generated outputs."""

    INDICATIVE = "indicative"
    CONCEPTUAL = "conceptual"
    PRELIMINARY = "preliminary"
    REVIEWED = "reviewed"
    APPROVED = "approved"


@dataclass(frozen=True)
class ProjectInputs:
    """Minimum useful input set for concept-stage calculations."""

    project_name: str
    site_location: str
    target_it_kw: float
    average_rack_kw: float
    max_rack_kw: float
    rack_count: int | None = None
    redundancy: Redundancy = Redundancy.N_PLUS_1
    design_pue_target: float = 1.35
    electricity_cost_per_kwh: float = 0.15
    cooling_delta_t_c: float = 12.0
    chilled_water_delta_t_c: float = 6.0
    airflow_safety_factor: float = 1.10
    white_space_allowance_m2_per_rack: float = 3.2
    support_space_factor: float = 0.65
    capex_cost_per_kw_usd: float = 10_000.0
    annual_hours: int = 8760

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ProjectInputs":
        payload = dict(data)
        if "redundancy" in payload:
            payload["redundancy"] = Redundancy(payload["redundancy"])
        return cls(**payload)

    def __post_init__(self) -> None:
        positive_fields = {
            "target_it_kw": self.target_it_kw,
            "average_rack_kw": self.average_rack_kw,
            "max_rack_kw": self.max_rack_kw,
            "design_pue_target": self.design_pue_target,
            "electricity_cost_per_kwh": self.electricity_cost_per_kwh,
            "cooling_delta_t_c": self.cooling_delta_t_c,
            "chilled_water_delta_t_c": self.chilled_water_delta_t_c,
            "airflow_safety_factor": self.airflow_safety_factor,
            "white_space_allowance_m2_per_rack": self.white_space_allowance_m2_per_rack,
            "support_space_factor": self.support_space_factor,
            "capex_cost_per_kw_usd": self.capex_cost_per_kw_usd,
        }
        for name, value in positive_fields.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.rack_count is not None and self.rack_count <= 0:
            raise ValueError("rack_count must be positive when provided")
        if self.design_pue_target < 1.0:
            raise ValueError("design_pue_target cannot be below 1.0")
        if self.max_rack_kw < self.average_rack_kw:
            raise ValueError("max_rack_kw must be greater than or equal to average_rack_kw")


@dataclass(frozen=True)
class CalculationLine:
    """Traceable single calculation result."""

    label: str
    inputs: dict[str, Any]
    formula: str
    result: float
    unit: str
    assumptions: list[str]
    confidence: str = "medium"
    human_review_required: bool = True
    status: ReviewStatus = ReviewStatus.CONCEPTUAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoolingOption:
    """Concept cooling architecture candidate."""

    name: str
    topology: str
    recommended_phase: str
    installed_capacity_kw: float
    estimated_pue: float
    water_use_risk: str
    technology_risk: str
    resilience_score: float
    energy_score: float
    capex_score: float
    weighted_score: float
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
