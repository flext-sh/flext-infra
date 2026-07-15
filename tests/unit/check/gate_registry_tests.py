"""Tests for gate registration of the new durissimas gates.

`loc-cap`, `boundary`, and `canonical-alias` must be in the SSOT-derived
ALLOWED_GATES and resolve through the registry.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, m, p, r, u
from flext_infra.check.workspace_check_gates import FlextInfraGateRegistry
from flext_infra.gates.canonical_alias import FlextInfraCanonicalAliasGate
from tests import t


class TestGateRegistry:
    def test_new_gates_in_allowed(self) -> None:
        tm.that("loc-cap" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that("boundary" in c.Infra.ALLOWED_GATES, eq=True)
        tm.that("canonical-alias" in c.Infra.ALLOWED_GATES, eq=True)

    def test_registry_resolves_loc_cap(self) -> None:
        tm.that(FlextInfraGateRegistry.default().get("loc-cap") is not None, eq=True)

    def test_registry_resolves_boundary(self) -> None:
        tm.that(FlextInfraGateRegistry.default().get("boundary") is not None, eq=True)

    def test_registry_resolves_canonical_alias(self) -> None:
        tm.that(
            FlextInfraGateRegistry.default().get("canonical-alias") is not None, eq=True
        )

    def test_canonical_alias_fix_fails_on_read_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project_dir = tmp_path / "demo"
        package_dir = project_dir / "src" / "demo"
        package_dir.mkdir(parents=True)
        source_file = package_dir / "service.py"
        source_file.write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "VALUE = c.MAX_SIZE\n",
            encoding="utf-8",
        )

        def _fail_read(path: Path) -> p.Result[str]:
            return r[str].fail(f"read failed: {path.name}")

        monkeypatch.setattr(u.Cli, "files_read_text", _fail_read)
        gate = FlextInfraCanonicalAliasGate(tmp_path)
        result = gate.fix(
            project_dir,
            m.Infra.GateContext(
                workspace=tmp_path, reports_dir=tmp_path / "reports", apply_fixes=True
            ),
        )

        tm.that(result.result.passed, eq=False)
        tm.that(result.raw_output, has="read failed: service.py")


__all__: t.StrSequence = []
