"""Cooling option generation and weighted comparison."""

from __future__ import annotations

from math import ceil

from .calculations import (
    DEFAULT_COOLING_UNIT_KW,
    calculate_cooling_load,
    standby_unit_count,
)
from .models import CoolingOption, ProjectInputs, Redundancy


DEFAULT_WEIGHTS = {
    "capex": 0.30,
    "energy": 0.30,
    "resilience": 0.25,
    "technology": 0.15,
}


def _redundancy_score(redundancy: Redundancy) -> float:
    return {
        Redundancy.N: 0.45,
        Redundancy.N_PLUS_1: 0.72,
        Redundancy.N_PLUS_2: 0.82,
        Redundancy.TWO_N: 0.95,
    }[redundancy]


def _technology_score(risk: str) -> float:
    return {"low": 0.90, "medium": 0.70, "high": 0.45}[risk]


def _weighted_score(
    *,
    capex_score: float,
    energy_score: float,
    resilience_score: float,
    technology_risk: str,
    weights: dict[str, float],
) -> float:
    return round(
        capex_score * weights["capex"]
        + energy_score * weights["energy"]
        + resilience_score * weights["resilience"]
        + _technology_score(technology_risk) * weights["technology"],
        4,
    )


def generate_cooling_options(
    inputs: ProjectInputs,
    weights: dict[str, float] | None = None,
) -> list[CoolingOption]:
    """Generate concept cooling options ranked by weighted engineering priorities."""

    active_weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    cooling_load_kw = calculate_cooling_load(inputs).result
    active_units = ceil(cooling_load_kw / DEFAULT_COOLING_UNIT_KW)
    standby_units = standby_unit_count(inputs.redundancy, active_units=active_units)
    policy_installed_kw = (active_units + standby_units) * DEFAULT_COOLING_UNIT_KW

    candidates = [
        {
            "name": "Air-cooled chiller plus CRAH",
            "topology": "Air-cooled chilled-water plant serving perimeter or gallery CRAH units.",
            "phase": "MVP",
            "capacity_factor": 1.0,
            "estimated_pue": max(inputs.design_pue_target, 1.32),
            "water_use_risk": "low",
            "technology_risk": "low",
            "capex_score": 0.78,
            "energy_score": 0.66,
            "rationale": [
                "Simple concept baseline.",
                "Low water dependency.",
                "Good fit for early comparison and modular delivery.",
            ],
        },
        {
            "name": "Indirect evaporative cooling",
            "topology": "Indirect evaporative air handling with mechanical trim cooling.",
            "phase": "Phase 2",
            "capacity_factor": 1.0,
            "estimated_pue": min(inputs.design_pue_target, 1.25),
            "water_use_risk": "medium",
            "technology_risk": "medium",
            "capex_score": 0.70,
            "energy_score": 0.84,
            "rationale": [
                "Potentially stronger energy performance.",
                "Needs climate, water, air quality, and maintenance validation.",
            ],
        },
        {
            "name": "Direct-to-chip liquid cooling hybrid",
            "topology": "Liquid cooling loop for high-density racks with residual air cooling.",
            "phase": "Phase 2",
            "capacity_factor": 1.0,
            "estimated_pue": min(inputs.design_pue_target, 1.20),
            "water_use_risk": "low",
            "technology_risk": "medium",
            "capex_score": 0.58,
            "energy_score": 0.88,
            "rationale": [
                "Best suited to AI and GPU density.",
                "Requires CDU, leak detection, controls, and server compatibility review.",
            ],
        },
        {
            "name": "2N water-cooled chiller plant",
            "topology": "Dual-path chilled-water plant with water-cooled chillers and cooling towers.",
            "phase": "Phase 3",
            "capacity_factor": 2.0,
            "estimated_pue": min(inputs.design_pue_target, 1.28),
            "water_use_risk": "high",
            "technology_risk": "low",
            "capex_score": 0.45,
            "energy_score": 0.76,
            "rationale": [
                "High resilience path for larger mission-critical facilities.",
                "Requires water availability, water treatment, planning, plume, and maintenance review.",
            ],
        },
    ]

    options: list[CoolingOption] = []
    for candidate in candidates:
        if candidate["name"].startswith("Direct-to-chip") and inputs.max_rack_kw < 25:
            candidate = {
                **candidate,
                "technology_risk": "high",
                "rationale": [
                    *candidate["rationale"],
                    "Rack density does not yet force liquid cooling; keep as a future-readiness option.",
                ],
            }

        installed_capacity_kw = policy_installed_kw
        if candidate["capacity_factor"] >= 2.0:
            installed_capacity_kw = max(
                policy_installed_kw,
                active_units * DEFAULT_COOLING_UNIT_KW * candidate["capacity_factor"],
            )
        resilience_score = max(_redundancy_score(inputs.redundancy), 0.90) if candidate["capacity_factor"] >= 2 else _redundancy_score(inputs.redundancy)
        option = CoolingOption(
            name=candidate["name"],
            topology=candidate["topology"],
            recommended_phase=candidate["phase"],
            installed_capacity_kw=round(installed_capacity_kw, 2),
            estimated_pue=round(candidate["estimated_pue"], 3),
            water_use_risk=candidate["water_use_risk"],
            technology_risk=candidate["technology_risk"],
            resilience_score=round(resilience_score, 3),
            energy_score=candidate["energy_score"],
            capex_score=candidate["capex_score"],
            weighted_score=_weighted_score(
                capex_score=candidate["capex_score"],
                energy_score=candidate["energy_score"],
                resilience_score=resilience_score,
                technology_risk=candidate["technology_risk"],
                weights=active_weights,
            ),
            rationale=candidate["rationale"],
        )
        options.append(option)

    return sorted(options, key=lambda item: item.weighted_score, reverse=True)
