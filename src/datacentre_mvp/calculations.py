"""Deterministic concept-stage calculations for the Datacentre MVP."""

from __future__ import annotations

from math import ceil
from typing import Any

from .models import CalculationLine, ProjectInputs, Redundancy

ENGINE_VERSION = "0.1.0"

AIR_DENSITY_KG_M3 = 1.2
AIR_SPECIFIC_HEAT_J_KG_K = 1005
WATER_DENSITY_KG_M3 = 1000
WATER_SPECIFIC_HEAT_J_KG_K = 4186
DEFAULT_COOLING_UNIT_KW = 500
COOLING_LOAD_ALLOWANCE = 1.10
PLANT_SPACE_M2_PER_KW = 0.07


def estimate_rack_count(inputs: ProjectInputs) -> CalculationLine:
    rack_count = inputs.rack_count or ceil(inputs.target_it_kw / inputs.average_rack_kw)
    assumptions = [
        "Rack count is concept-stage only.",
        "If rack count is not supplied, target IT load is divided by average rack density.",
    ]
    return CalculationLine(
        label="rack_count",
        inputs={
            "target_it_kw": inputs.target_it_kw,
            "average_rack_kw": inputs.average_rack_kw,
            "provided_rack_count": inputs.rack_count,
        },
        formula="provided rack_count else ceil(target_it_kw / average_rack_kw)",
        result=float(rack_count),
        unit="racks",
        assumptions=assumptions,
    )


def calculate_it_load(inputs: ProjectInputs) -> CalculationLine:
    return CalculationLine(
        label="it_load",
        inputs={"target_it_kw": inputs.target_it_kw},
        formula="target_it_kw",
        result=inputs.target_it_kw,
        unit="kW",
        assumptions=["IT load is treated as the full critical load at concept stage."],
        confidence="high",
    )


def calculate_space_plan(inputs: ProjectInputs) -> list[CalculationLine]:
    racks = estimate_rack_count(inputs).result
    white_space_m2 = racks * inputs.white_space_allowance_m2_per_rack
    support_space_m2 = white_space_m2 * inputs.support_space_factor
    plant_space_m2 = inputs.target_it_kw * PLANT_SPACE_M2_PER_KW
    total_area_m2 = white_space_m2 + support_space_m2 + plant_space_m2

    common_assumptions = [
        "Areas are for concept comparison only.",
        "Plant and support allowances vary significantly by site, phasing, and equipment selection.",
    ]
    return [
        CalculationLine(
            label="white_space_area",
            inputs={
                "rack_count": racks,
                "white_space_allowance_m2_per_rack": inputs.white_space_allowance_m2_per_rack,
            },
            formula="rack_count * white_space_allowance_m2_per_rack",
            result=round(white_space_m2, 2),
            unit="m2",
            assumptions=common_assumptions,
        ),
        CalculationLine(
            label="support_space_area",
            inputs={
                "white_space_area_m2": white_space_m2,
                "support_space_factor": inputs.support_space_factor,
            },
            formula="white_space_area_m2 * support_space_factor",
            result=round(support_space_m2, 2),
            unit="m2",
            assumptions=common_assumptions,
        ),
        CalculationLine(
            label="mechanical_plant_area",
            inputs={
                "target_it_kw": inputs.target_it_kw,
                "plant_space_m2_per_kw": PLANT_SPACE_M2_PER_KW,
            },
            formula="target_it_kw * plant_space_m2_per_kw",
            result=round(plant_space_m2, 2),
            unit="m2",
            assumptions=common_assumptions,
        ),
        CalculationLine(
            label="total_concept_area",
            inputs={
                "white_space_area_m2": white_space_m2,
                "support_space_area_m2": support_space_m2,
                "mechanical_plant_area_m2": plant_space_m2,
            },
            formula="white_space_area_m2 + support_space_area_m2 + mechanical_plant_area_m2",
            result=round(total_area_m2, 2),
            unit="m2",
            assumptions=common_assumptions,
        ),
    ]


def calculate_cooling_load(inputs: ProjectInputs) -> CalculationLine:
    cooling_kw = inputs.target_it_kw * COOLING_LOAD_ALLOWANCE
    return CalculationLine(
        label="cooling_load",
        inputs={
            "target_it_kw": inputs.target_it_kw,
            "cooling_load_allowance": COOLING_LOAD_ALLOWANCE,
        },
        formula="target_it_kw * cooling_load_allowance",
        result=round(cooling_kw, 2),
        unit="kW",
        assumptions=[
            "All IT power is assumed to become heat.",
            "A 10 percent concept allowance is applied for early-stage uncertainty.",
        ],
    )


def standby_unit_count(redundancy: Redundancy, active_units: int) -> int:
    if redundancy == Redundancy.N:
        return 0
    if redundancy == Redundancy.N_PLUS_1:
        return 1
    if redundancy == Redundancy.N_PLUS_2:
        return 2
    if redundancy == Redundancy.TWO_N:
        return active_units
    raise ValueError(f"Unsupported redundancy: {redundancy}")


def size_cooling_system(
    inputs: ProjectInputs,
    unit_capacity_kw: float = DEFAULT_COOLING_UNIT_KW,
) -> list[CalculationLine]:
    if unit_capacity_kw <= 0:
        raise ValueError("unit_capacity_kw must be positive")

    cooling_load_kw = calculate_cooling_load(inputs).result
    active_units = ceil(cooling_load_kw / unit_capacity_kw)
    standby_units = standby_unit_count(inputs.redundancy, active_units)
    installed_capacity_kw = (active_units + standby_units) * unit_capacity_kw

    assumptions = [
        "Unit capacity is a configurable concept-stage module size.",
        "Installed capacity includes active and standby modules.",
        "Detailed selection must consider part-load efficiency, fault domains, maintainability, and manufacturer data.",
    ]
    return [
        CalculationLine(
            label="active_cooling_units",
            inputs={
                "cooling_load_kw": cooling_load_kw,
                "unit_capacity_kw": unit_capacity_kw,
            },
            formula="ceil(cooling_load_kw / unit_capacity_kw)",
            result=float(active_units),
            unit="units",
            assumptions=assumptions,
        ),
        CalculationLine(
            label="standby_cooling_units",
            inputs={
                "redundancy": inputs.redundancy.value,
                "active_cooling_units": active_units,
            },
            formula="redundancy policy standby count",
            result=float(standby_units),
            unit="units",
            assumptions=assumptions,
        ),
        CalculationLine(
            label="installed_cooling_capacity",
            inputs={
                "active_cooling_units": active_units,
                "standby_cooling_units": standby_units,
                "unit_capacity_kw": unit_capacity_kw,
            },
            formula="(active_cooling_units + standby_cooling_units) * unit_capacity_kw",
            result=round(installed_capacity_kw, 2),
            unit="kW",
            assumptions=assumptions,
        ),
    ]


def calculate_airflow(inputs: ProjectInputs) -> CalculationLine:
    heat_w = inputs.target_it_kw * 1000
    airflow_m3_s = heat_w / (
        AIR_DENSITY_KG_M3 * AIR_SPECIFIC_HEAT_J_KG_K * inputs.cooling_delta_t_c
    )
    airflow_m3_s *= inputs.airflow_safety_factor
    return CalculationLine(
        label="supply_airflow",
        inputs={
            "target_it_kw": inputs.target_it_kw,
            "air_density_kg_m3": AIR_DENSITY_KG_M3,
            "air_specific_heat_j_kg_k": AIR_SPECIFIC_HEAT_J_KG_K,
            "cooling_delta_t_c": inputs.cooling_delta_t_c,
            "airflow_safety_factor": inputs.airflow_safety_factor,
        },
        formula="(target_it_kw * 1000) / (rho_air * cp_air * delta_t) * safety_factor",
        result=round(airflow_m3_s, 2),
        unit="m3/s",
        assumptions=[
            "Airflow estimate assumes sensible IT heat removal by air.",
            "Liquid cooling or rear-door heat exchangers require separate treatment.",
        ],
    )


def calculate_chilled_water_flow(inputs: ProjectInputs) -> CalculationLine:
    cooling_load_w = calculate_cooling_load(inputs).result * 1000
    flow_m3_s = cooling_load_w / (
        WATER_DENSITY_KG_M3
        * WATER_SPECIFIC_HEAT_J_KG_K
        * inputs.chilled_water_delta_t_c
    )
    return CalculationLine(
        label="chilled_water_flow",
        inputs={
            "cooling_load_kw": cooling_load_w / 1000,
            "water_density_kg_m3": WATER_DENSITY_KG_M3,
            "water_specific_heat_j_kg_k": WATER_SPECIFIC_HEAT_J_KG_K,
            "chilled_water_delta_t_c": inputs.chilled_water_delta_t_c,
        },
        formula="(cooling_load_kw * 1000) / (rho_water * cp_water * delta_t)",
        result=round(flow_m3_s, 4),
        unit="m3/s",
        assumptions=[
            "Flow is based on chilled-water sensible heat transfer only.",
            "Pump head, pipe sizing, glycol content, and redundancy are excluded from the MVP calculation.",
        ],
    )


def calculate_facility_energy(inputs: ProjectInputs) -> list[CalculationLine]:
    facility_kw = inputs.target_it_kw * inputs.design_pue_target
    annual_kwh = facility_kw * inputs.annual_hours
    annual_opex = annual_kwh * inputs.electricity_cost_per_kwh

    assumptions = [
        "PUE is an input target, not a validated operating result.",
        "Energy cost excludes demand charges, taxes, escalation, and curtailment.",
    ]
    return [
        CalculationLine(
            label="facility_power",
            inputs={
                "target_it_kw": inputs.target_it_kw,
                "design_pue_target": inputs.design_pue_target,
            },
            formula="target_it_kw * design_pue_target",
            result=round(facility_kw, 2),
            unit="kW",
            assumptions=assumptions,
        ),
        CalculationLine(
            label="annual_energy",
            inputs={
                "facility_power_kw": facility_kw,
                "annual_hours": inputs.annual_hours,
            },
            formula="facility_power_kw * annual_hours",
            result=round(annual_kwh, 2),
            unit="kWh/year",
            assumptions=assumptions,
        ),
        CalculationLine(
            label="annual_energy_cost",
            inputs={
                "annual_energy_kwh": annual_kwh,
                "electricity_cost_per_kwh": inputs.electricity_cost_per_kwh,
            },
            formula="annual_energy_kwh * electricity_cost_per_kwh",
            result=round(annual_opex, 2),
            unit="currency/year",
            assumptions=assumptions,
        ),
    ]


def calculate_capex(inputs: ProjectInputs) -> CalculationLine:
    capex = inputs.target_it_kw * inputs.capex_cost_per_kw_usd
    return CalculationLine(
        label="concept_capex",
        inputs={
            "target_it_kw": inputs.target_it_kw,
            "capex_cost_per_kw_usd": inputs.capex_cost_per_kw_usd,
        },
        formula="target_it_kw * capex_cost_per_kw_usd",
        result=round(capex, 2),
        unit="USD",
        assumptions=[
            "Cost is a high-level benchmark only.",
            "Estimate excludes site-specific abnormal costs, utility upgrades, financing, taxes, and escalation.",
        ],
        confidence="low",
    )


def build_calculation_pack(inputs: ProjectInputs) -> dict[str, Any]:
    lines: list[CalculationLine] = [
        calculate_it_load(inputs),
        estimate_rack_count(inputs),
        calculate_cooling_load(inputs),
        *size_cooling_system(inputs),
        calculate_airflow(inputs),
        calculate_chilled_water_flow(inputs),
        *calculate_space_plan(inputs),
        *calculate_facility_energy(inputs),
        calculate_capex(inputs),
    ]

    warnings = []
    if inputs.max_rack_kw >= 30:
        warnings.append(
            "High rack density detected. Assess direct-to-chip, rear-door heat exchanger, or immersion cooling options."
        )
    if inputs.redundancy == Redundancy.N:
        warnings.append("N redundancy has limited maintainability and resilience for mission-critical use.")
    if inputs.design_pue_target < 1.15:
        warnings.append("Very low PUE target requires climate, load profile, and cooling topology validation.")

    return {
        "engine_version": ENGINE_VERSION,
        "project": {
            "name": inputs.project_name,
            "site_location": inputs.site_location,
            "redundancy": inputs.redundancy.value,
        },
        "status": "conceptual",
        "human_review_required": True,
        "warnings": warnings,
        "calculations": [line.to_dict() for line in lines],
    }
