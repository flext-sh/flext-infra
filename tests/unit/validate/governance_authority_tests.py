"""Reject dead governance skill paths and conflicting authority sequences."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _workspace_root() -> Path:
    """Resolve the flext superproject when present; else skip workspace tests."""
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(PROJECT_ROOT),
            "rev-parse",
            "--show-superproject-working-tree",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    superproject = completed.stdout.strip()
    if superproject:
        return Path(superproject)
    pytest.skip(
        "flext workspace governance files require a flext superproject; "
        "standalone flext-infra make-work worktrees have none"
    )


def test_prompt_skills_resolve_to_existing_paths() -> None:
    root = _workspace_root()
    prompts = root / ".github" / "prompts"
    law_link = "../../.agents/skills/flext-law/SKILL.md"
    for prompt in prompts.glob("*.prompt.md"):
        text = prompt.read_text(encoding="utf-8")
        assert "flext-inviolable-rules" not in text
        assert "quality-gates" not in text
        if "flext-aggressive-scale-refactor" in prompt.name or "flext-strict-jsonvalue" in prompt.name:
            assert law_link in text
            target = (prompt.parent / law_link).resolve()
            assert target.exists(), f"{prompt.name} dead skill path: {law_link}"


def test_governance_authority_sequence_matches_agents() -> None:
    root = _workspace_root()
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    governance = (root / "docs" / "GOVERNANCE.md").read_text(encoding="utf-8")
    assert "Beads never override higher law" in agents
    assert "never overrides higher law" in governance
    assert "quality-gates skill" not in governance
    assert "`make-check` skill" in governance


def test_docs_validation_required_skills_exist_with_adr() -> None:
    root = _workspace_root()
    config = json.loads(
        (root / "docs" / "architecture" / "architecture_config.json").read_text(
            encoding="utf-8"
        )
    )
    required = config["docs_validation"]["required_skills"]
    skills_root = root / ".agents" / "skills"
    for name in required:
        skill = skills_root / name / "SKILL.md"
        assert skill.is_file(), name
        assert "adr" in skill.read_text(encoding="utf-8").lower(), name


def test_july_handoff_plans_are_marked_historical() -> None:
    root = _workspace_root()
    plans = (
        root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-29-flext-beads-governance-reorganization-handoff.md",
        root
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-07-29-flext-governance-beads-execution-continuation.md",
    )
    for plan in plans:
        text = plan.read_text(encoding="utf-8")
        assert "HISTORICAL / SUPERSEDED" in text


def test_markdownlint_does_not_suppress_strict_rules() -> None:
    root = _workspace_root()
    config = json.loads((root / ".markdownlint.json").read_text(encoding="utf-8"))
    assert config.get("MD012") is not False
    assert config.get("MD050") is not False
    assert config.get("MD064") is not False
    assert config.get("MD075") is not False
    assert config["MD013"]["line_length"] <= 500
