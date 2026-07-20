import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datacentre_mvp.calculations import (  # noqa: E402
    build_calculation_pack,
    calculate_airflow,
    estimate_rack_count,
    size_cooling_system,
)
from datacentre_mvp.cli import run  # noqa: E402
from datacentre_mvp.models import ProjectInputs, Redundancy  # noqa: E402
from datacentre_mvp.options import generate_cooling_options  # noqa: E402


class CalculationTests(unittest.TestCase):
    def sample_inputs(self, **overrides):
        payload = {
            "project_name": "Unit test hall",
            "site_location": "London, UK",
            "target_it_kw": 2000,
            "average_rack_kw": 10,
            "max_rack_kw": 35,
            "rack_count": None,
            "redundancy": Redundancy.N_PLUS_1,
            "design_pue_target": 1.35,
        }
        payload.update(overrides)
        return ProjectInputs(**payload)

    def test_rack_count_rounds_up_when_not_provided(self):
        inputs = self.sample_inputs(target_it_kw=2050, average_rack_kw=12)

        result = estimate_rack_count(inputs)

        self.assertEqual(result.result, 171)
        self.assertEqual(result.unit, "racks")

    def test_n_plus_one_adds_one_standby_cooling_unit(self):
        inputs = self.sample_inputs(target_it_kw=2000, redundancy=Redundancy.N_PLUS_1)

        lines = {line.label: line for line in size_cooling_system(inputs, unit_capacity_kw=500)}

        self.assertEqual(lines["active_cooling_units"].result, 5)
        self.assertEqual(lines["standby_cooling_units"].result, 1)
        self.assertEqual(lines["installed_cooling_capacity"].result, 3000)

    def test_two_n_standby_matches_active_units(self):
        inputs = self.sample_inputs(target_it_kw=2000, redundancy=Redundancy.TWO_N)

        lines = {line.label: line for line in size_cooling_system(inputs, unit_capacity_kw=500)}

        self.assertEqual(lines["active_cooling_units"].result, 5)
        self.assertEqual(lines["standby_cooling_units"].result, 5)
        self.assertEqual(lines["installed_cooling_capacity"].result, 5000)

    def test_airflow_responds_to_safety_factor(self):
        base = self.sample_inputs(airflow_safety_factor=1.0)
        higher = self.sample_inputs(airflow_safety_factor=1.2)

        self.assertGreater(calculate_airflow(higher).result, calculate_airflow(base).result)

    def test_calculation_pack_contains_review_flag_and_warnings(self):
        inputs = self.sample_inputs(max_rack_kw=35)

        pack = build_calculation_pack(inputs)

        self.assertTrue(pack["human_review_required"])
        self.assertTrue(any("High rack density" in warning for warning in pack["warnings"]))
        self.assertGreater(len(pack["calculations"]), 5)

    def test_cooling_options_are_ranked(self):
        inputs = self.sample_inputs()

        options = generate_cooling_options(inputs)

        scores = [option.weighted_score for option in options]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_cli_run_accepts_sample_json(self):
        sample_path = ROOT / "examples" / "sample_project.json"
        payload = json.loads(sample_path.read_text(encoding="utf-8"))

        output = run(payload)

        self.assertIn("calculation_pack", output)
        self.assertIn("cooling_options", output)


if __name__ == "__main__":
    unittest.main()
