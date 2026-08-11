"""Tests that conforming pyproject.toml never widens the lint surface.

``codegen conform`` regenerates the ``[MANAGED]`` pyproject sections from the
tooling SSOT. When a per-file-ignore that the workspace genuinely relies on is
absent from that SSOT, the rendered tree silently *adds* lint errors, the
transaction guard reports ``breakage=yes`` and refuses to apply -- so a missing
SSOT entry blocks every other generated artifact from landing.

Concretely: ``scripts/cmd`` intentionally uses hyphenated command filenames
(``loc-cap.py``), which is a CLI naming convention, not a Python import path.
The ignore for that directory must live in the SSOT so the generator reproduces
it instead of dropping it.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

from flext_infra import config
from flext_tests import tm


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(__file__).resolve().parents[2]


def _live_per_file_ignores() -> frozenset[str]:
    """Return the per-file-ignore globs the governed pyproject declares."""
    payload = tomllib.loads(
        (_workspace_root() / "pyproject.toml").read_text(encoding="utf-8")
    )
    ruff = payload["tool"]["ruff"]["lint"]
    return frozenset(ruff["per-file-ignores"])


def _ssot_per_file_ignores() -> frozenset[str]:
    """Return every per-file-ignore glob the generator can reproduce.

    Two sources feed the rendered pyproject, and conform merges both:
    ``Infra.tooling`` is the FLEET policy every generated project inherits,
    while a ``ManagedArtifacts.Ruff`` block in the project's own
    ``config/*.yaml`` adds exemptions that belong to that repository alone.
    A path that exists in one repository is declared project-locally so the
    fleet policy does not write a dead exemption into every project.
    """
    ruff = config.Infra.tooling.tools.ruff
    fleet = frozenset(ruff.lint.per_file_ignores)

    project: set[str] = set()
    for path in sorted((_workspace_root() / "config").glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        managed = payload.get("ManagedArtifacts") or {}
        project.update(managed.get("Ruff", {}).get("per_file_ignores", {}))
    return fleet | frozenset(project)


class TestsFlextInfraPyprojectConformPreservesLintScope:
    def test_ssot_preserves_pytest_assertion_semantics(self) -> None:
        """Keep generated and external pytest suites valid without migration."""
        rules = config.Infra.tooling.tools.ruff.lint.per_file_ignores["**/tests/**"]

        tm.that(rules, has="assert")

    def test_ssot_declares_every_governed_per_file_ignore(self) -> None:
        """No governed lint exemption is missing from the tooling SSOT."""
        missing = _live_per_file_ignores() - _ssot_per_file_ignores()

        tm.that(missing, eq=frozenset())
