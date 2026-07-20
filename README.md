# Datacentre

AI-assisted concept design tooling for data centre engineering.

This repository starts the MVP as an auditable calculation core rather than a black-box AI agent. The current package focuses on:

- project brief inputs
- IT load and rack planning
- cooling load and airflow estimates
- redundancy sizing for `N`, `N+1`, `N+2`, and `2N`
- preliminary CAPEX, OPEX, and PUE estimates
- cooling option comparison
- explicit assumptions and human-review flags

The product direction is broader: design, simulate, optimise, and document a data centre from concept to operation through one intelligent engineering platform.

## Quick Start

```powershell
python -m unittest discover -s tests
$env:PYTHONPATH='src'
python -m datacentre_mvp.cli examples/sample_project.json
```

## Repository Structure

```text
docs/
  startup-design.md       Product, engineering, commercial, and roadmap blueprint
src/datacentre_mvp/
  models.py               Input and result dataclasses
  calculations.py         Deterministic engineering calculation functions
  options.py              Cooling option generation and scoring
  api_contract.py         Initial API surface definition
  cli.py                  JSON-in, JSON-out calculation runner
tests/
  test_calculations.py    Regression tests for the MVP calculation core
```

## Engineering Guardrail

Outputs from this MVP are conceptual. They are intended to support option development and early-stage engineering conversations. They are not construction-ready and require review and approval by qualified mechanical, electrical, structural, fire, and mission-critical engineers before use in design deliverables.
