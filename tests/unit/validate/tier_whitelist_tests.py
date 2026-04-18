"""Tests for FlextInfraValidateTierWhitelist.

Guard 5: Abstraction-boundary + tier-whitelist enforcer. Flags runtime
imports of flext-core-abstracted third-party libraries (pydantic,
structlog, returns, orjson, pyyaml, dependency_injector) anywhere
outside ``flext-core/src/``. Uses rope's semantic import resolution so
``if TYPE_CHECKING:`` imports are exempt.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tf, tm

from flext_infra import FlextInfraValidateTierWhitelist
from tests import m, t


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
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        report = tm.ok(v.build_report(tmp_path))
        assert isinstance(report, m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)

    def test_clean_imports_pass(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in(
            "from flext_core import m, c\nX = m.BaseModel\n",
            "good.py",
            pkg,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=True)

    def test_bare_pydantic_import_flagged(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in(
            "from pydantic import BaseModel\n",
            "bad.py",
            pkg,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=False)
        joined = " | ".join(report.violations)
        tm.that(joined, has="bad.py")
        tm.that(joined, has="pydantic")

    def test_bare_structlog_import_flagged(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in(
            "import structlog\n",
            "bad_structlog.py",
            pkg,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=False)
        joined = " | ".join(report.violations)
        tm.that(joined, has="structlog")

    def test_bare_returns_import_flagged(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in(
            "from returns.result import Result\n",
            "bad_returns.py",
            pkg,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=False)
        joined = " | ".join(report.violations)
        tm.that(joined, has="returns")

    def test_type_checking_pydantic_import_is_exempt(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in(
            (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from pydantic import BaseModel\n"
            ),
            "typed_only.py",
            pkg,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=True)

    def test_flext_core_src_is_allowlisted(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        # Emulate a flext-core layout — bare pydantic is legal here.
        src = tmp_path / "flext-core" / "src" / "flext_core"
        src.mkdir(parents=True, exist_ok=True)
        (src / "__init__.py").write_text("", encoding="utf-8")
        tf.create_in(
            "from pydantic import BaseModel\nX = BaseModel\n",
            "abstractions.py",
            src,
        )
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.passed, eq=True)


class TestTierWhitelistSummary:
    """Summary content."""

    def test_failing_summary_reports_count(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        pkg = _seed_pkg(tmp_path)
        tf.create_in("from pydantic import BaseModel\n", "a.py", pkg)
        tf.create_in("import structlog\n", "b.py", pkg)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="2")

    def test_passing_summary_mentions_boundary(
        self,
        tmp_path: Path,
        v: FlextInfraValidateTierWhitelist,
    ) -> None:
        _seed_pkg(tmp_path)
        report = tm.ok(v.build_report(tmp_path))
        tm.that(report.summary, has="boundary")


__all__: t.StrSequence = []
