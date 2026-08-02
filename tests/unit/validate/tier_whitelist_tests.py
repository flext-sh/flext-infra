"""Tests for FlextInfraValidateTierWhitelist.

Guard 5: Abstraction-boundary + tier-whitelist enforcer. Flags runtime
imports of flext-core-abstracted third-party libraries (pydantic,
structlog, returns, orjson, pyyaml, dependency_injector) anywhere
outside their metadata-declared owning project. Uses rope's semantic import resolution so
``if TYPE_CHECKING:`` imports are exempt.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.gates.tier_whitelist import FlextInfraTierWhitelistGate
from flext_infra.validate.tier_whitelist import FlextInfraValidateTierWhitelist
from flext_tests import tf, tm
from tests import m

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


@pytest.fixture
def v() -> FlextInfraValidateTierWhitelist:
    """Shared validator instance."""
    return FlextInfraValidateTierWhitelist()


def _seed_pkg(root: Path, name: str = "pkg") -> Path:
    pkg = root / "src" / name
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    return pkg


class TestTierWhitelistAbstractionBoundary:
    """Abstraction-boundary rule: no bare pydantic/structlog/... outside flext-core."""

    def test_empty_workspace_passes(
        self, tmp_path: Path, v: FlextInfraValidateTierWhitelist
    ) -> None:
        report: m.Infra.ValidationReport = tm.ok(v.build_report(tmp_path))
        tm.that(report, is_=m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)

    def test_clean_imports_pass(
        self, tmp_path: Path, v: FlextInfraValidateTierWhitelist
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf(base_dir=pkg).create(
            "from flext_core import m, c\nX = m.BaseModel\n", "good.py"
        )
        report: m.Infra.ValidationReport = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=True)

    @pytest.mark.parametrize(
        ("source", "filename", "expected_substring"),
        [
            ("from pydantic import BaseModel\n", "bad.py", "pydantic"),
            ("import structlog\n", "bad_structlog.py", "structlog"),
            ("from returns.result import Result\n", "bad_returns.py", "returns"),
        ],
    )
    def test_bare_abstracted_import_flagged(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
        source: str,
        filename: str,
        expected_substring: str,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf(base_dir=pkg).create(source, filename)
        report: m.Infra.ValidationReport = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=False)
        tm.that(" | ".join(report.violations), has=expected_substring)

    def test_flext_core_src_is_allowlisted(
        self, tmp_path: Path, v: FlextInfraValidateTierWhitelist
    ) -> None:
        project_root = tmp_path / "arbitrary-worktree-name"
        (project_root / "pyproject.toml").parent.mkdir(parents=True)
        (project_root / "pyproject.toml").write_text(
            "[project]\nname = 'flext-core'\nversion = '0.0.0'\n",
            encoding="utf-8",
        )
        src = _seed_pkg(project_root, "flext_core")
        tf(base_dir=src).create(
            "from pydantic import BaseModel\nX = BaseModel\n", "abstractions.py"
        )
        report: m.Infra.ValidationReport = tm.ok(v.build_report(project_root))
        tm.that(report.passed, eq=True)


class TestTierWhitelistSummary:
    """Summary content."""

    def test_failing_summary_reports_count(
        self, tmp_path: Path, v: FlextInfraValidateTierWhitelist
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf(base_dir=pkg).create("from pydantic import BaseModel\n", "a.py")
        tf(base_dir=pkg).create("import structlog\n", "b.py")
        report: m.Infra.ValidationReport = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="2")

    def test_execute_and_gate_preserve_every_violation(self, tmp_path: Path) -> None:
        pkg = _seed_pkg(tmp_path)
        tf(base_dir=pkg).create("from pydantic import BaseModel\n", "a.py")
        tf(base_dir=pkg).create("import structlog\n", "b.py")
        validator = FlextInfraValidateTierWhitelist(workspace_root=tmp_path)

        result = validator.execute()
        tm.that(result.failure, eq=True)
        error = tm.not_none(result.error)
        tm.that(error, has="a.py")
        tm.that(error, has="b.py")

        execution = FlextInfraTierWhitelistGate(tmp_path).check(
            tmp_path,
            m.Infra.GateContext(workspace=tmp_path, reports_dir=tmp_path / "reports"),
        )
        tm.that(execution.result.passed, eq=False)
        tm.that(len(execution.issues), eq=2)
        tm.that("\n".join(issue.message for issue in execution.issues), has="a.py")
        tm.that("\n".join(issue.message for issue in execution.issues), has="b.py")

    def test_passing_summary_mentions_boundary(
        self, tmp_path: Path, v: FlextInfraValidateTierWhitelist
    ) -> None:
        _seed_pkg(tmp_path)
        report: m.Infra.ValidationReport = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="boundary")


__all__: t.StrSequence = []
