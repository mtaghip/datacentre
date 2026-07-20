"""Initial API contract for the future service layer."""

API_ENDPOINTS = [
    {
        "method": "POST",
        "path": "/projects",
        "phase": "MVP",
        "description": "Create a data centre project shell and capture core metadata.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/brief",
        "phase": "MVP",
        "description": "Create or update the structured project brief and assumption register.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/calculations",
        "phase": "MVP",
        "description": "Run deterministic concept calculations and return traceable calculation lines.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/options/cooling",
        "phase": "MVP",
        "description": "Generate cooling architecture options and rank them by weighted criteria.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/reports/basis-of-design",
        "phase": "MVP",
        "description": "Generate a basis-of-design report package with unresolved assumptions.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/cfd/openfoam-cases",
        "phase": "Phase 2",
        "description": "Create a solver case package for OpenFOAM from layout and rack heat-load data.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/bim/ifc-export",
        "phase": "Phase 2",
        "description": "Export concept layout and equipment placement data as IFC.",
    },
    {
        "method": "POST",
        "path": "/projects/{project_id}/review-gates",
        "phase": "MVP",
        "description": "Record human review status and prevent unsupported approval claims.",
    },
]
