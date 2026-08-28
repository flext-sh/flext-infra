"""Reject dead governance skill paths and conflicting authority sequences."""

from __future__ import annotations

import json
import re
from pathlib import Path

import flext_infra

ROOT = Path(flext_infra.__file__).resolve().parents[2]


def test_standalone_governance_never_climbs_to_parent_authority() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "standalone authority" in agents
    assert "Never climb to a parent checkout" in agents
    assert re.search(r"(?<![\w-])(bd|gt)(?![\w-])", agents) is None


def test_markdownlint_does_not_suppress_strict_rules() -> None:
    config = json.loads((ROOT / ".markdownlint.json").read_text(encoding="utf-8"))
    assert config.get("MD012") is not False
    assert config.get("MD050") is not False
    assert config.get("MD064") is not False
    assert config.get("MD075") is not False
    assert config["MD013"]["line_length"] <= 500
