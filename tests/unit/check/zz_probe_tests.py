"""Temporary probe: import-side effects of the gate registry."""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, u
from flext_infra.check import FlextInfraGateRegistry
from tests import tm


def test_b_validate_overlay_model(tmp_path: Path) -> None:
    """Validate the overlay model with the registry imported."""
    registry = FlextInfraGateRegistry.default()
    print("REGISTRY:", type(registry))
    validated = u.validate_value(
        m.Infra.JscpdProjectOverlay,
        {"ignore": ["**/first.py"]},
    )
    print(
        "PROBE-B:",
        validated.success,
        validated.value if validated.success else validated.error,
    )
    tm.ok(validated.success)
