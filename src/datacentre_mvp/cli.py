"""Command-line runner for the MVP calculation core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .calculations import build_calculation_pack
from .models import ProjectInputs
from .options import generate_cooling_options


def run(payload: dict[str, Any]) -> dict[str, Any]:
    inputs = ProjectInputs.from_mapping(payload)
    return {
        "calculation_pack": build_calculation_pack(inputs),
        "cooling_options": [option.to_dict() for option in generate_cooling_options(inputs)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Datacentre MVP concept calculations.")
    parser.add_argument("project_json", type=Path, help="Path to a project input JSON file.")
    args = parser.parse_args()

    payload = json.loads(args.project_json.read_text(encoding="utf-8"))
    print(json.dumps(run(payload), indent=2))


if __name__ == "__main__":
    main()
