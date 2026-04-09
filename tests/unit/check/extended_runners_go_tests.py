"""Tests for workspace checker runner — go vet and go fmt.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraGate, FlextInfraGoGate
from tests import u


class TestRunGo:
    def test_run_go_no_go_mod(self, tmp_path: Path) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1")
        result = u.Infra.Tests.run_gate_check(FlextInfraGoGate, tmp_path, proj_dir)
        tm.that(result.result.passed, eq=True)
        tm.that(len(result.issues), eq=0)

    def test_run_go_with_vet_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test")
        vet = u.Infra.Tests.stub_run(stdout="main.go:10:5: error message", returncode=1)
        fmt = u.Infra.Tests.stub_run()
        u.Infra.Tests.patch_gate_run_sequence(monkeypatch, FlextInfraGate, [vet, fmt])
        result = u.Infra.Tests.run_gate_check(FlextInfraGoGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)

    def test_run_go_with_format_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test")
        (proj_dir / "main.go").write_text("package main")
        vet = u.Infra.Tests.stub_run()
        fmt = u.Infra.Tests.stub_run(stdout="main.go", returncode=1)
        u.Infra.Tests.patch_gate_run_sequence(monkeypatch, FlextInfraGate, [vet, fmt])
        result = u.Infra.Tests.run_gate_check(FlextInfraGoGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=1)

    def test_run_go_skips_empty_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        proj_dir = u.Infra.Tests.mk_project(tmp_path, "p1")
        (proj_dir / "go.mod").write_text("module test\n")
        (proj_dir / "main.go").write_text("package main\n")
        vet = u.Infra.Tests.stub_run()
        fmt = u.Infra.Tests.stub_run(
            stdout="src/file.go\n\nsrc/other.go\n", returncode=1
        )
        u.Infra.Tests.patch_gate_run_sequence(monkeypatch, FlextInfraGate, [vet, fmt])
        result = u.Infra.Tests.run_gate_check(FlextInfraGoGate, tmp_path, proj_dir)
        tm.that(not result.result.passed, eq=True)
        tm.that(len(result.issues), eq=2)
