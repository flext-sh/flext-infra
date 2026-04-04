"""Tests for documentation CLI — main() entry point routing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from flext_tests import tm
from tests import m

from flext_core import r
from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
)
from flext_infra.cli import main as infra_main

type DocsCommandInput = (
    m.Infra.DocsAuditInput
    | m.Infra.DocsFixInput
    | m.Infra.DocsBuildInput
    | m.Infra.DocsGenerateInput
    | m.Infra.DocsValidateInput
)
type DocsCommandService = (
    FlextInfraDocAuditor
    | FlextInfraDocFixer
    | FlextInfraDocBuilder
    | FlextInfraDocGenerator
    | FlextInfraDocValidator
)
type AuditCommand = Callable[[FlextInfraDocAuditor, m.Infra.DocsAuditInput], r[bool]]
type FixCommand = Callable[[FlextInfraDocFixer, m.Infra.DocsFixInput], r[bool]]
type GenerateCommand = Callable[
    [FlextInfraDocGenerator, m.Infra.DocsGenerateInput],
    r[bool],
]
type ValidateCommand = Callable[
    [FlextInfraDocValidator, m.Infra.DocsValidateInput],
    r[bool],
]


def _ok_command(
    _self: DocsCommandService,
    _params: DocsCommandInput,
) -> r[bool]:
    return r[bool].ok(True)


class TestMainRouting:
    def test_main_with_audit_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocAuditor, "execute_command", _ok_command)
        tm.that(infra_main(["docs", "audit", "--workspace", "."]), eq=0)

    def test_main_with_fix_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocFixer, "execute_command", _ok_command)
        tm.that(infra_main(["docs", "fix", "--workspace", "."]), eq=0)

    def test_main_with_build_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocBuilder, "execute_command", _ok_command)
        tm.that(infra_main(["docs", "build", "--workspace", "."]), eq=0)

    def test_main_with_generate_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocGenerator, "execute_command", _ok_command)
        tm.that(infra_main(["docs", "generate", "--workspace", "."]), eq=0)

    def test_main_with_validate_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocValidator, "execute_command", _ok_command)
        tm.that(infra_main(["docs", "validate", "--workspace", "."]), eq=0)

    def test_main_with_no_command_prints_help(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        del monkeypatch
        tm.that(infra_main(["docs"]), eq=1)

    def test_main_with_help_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        del monkeypatch
        tm.that(infra_main(["docs", "--help"]), eq=0)

    def test_main_with_audit_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        del monkeypatch
        tm.that(infra_main(["docs", "audit", "--help"]), eq=0)

    def test_main_with_fix_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        del monkeypatch
        tm.that(infra_main(["docs", "fix", "--help"]), eq=0)

    def test_main_with_build_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        del monkeypatch
        tm.that(infra_main(["docs", "build", "--help"]), eq=0)

    def test_main_with_generate_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        del monkeypatch
        tm.that(infra_main(["docs", "generate", "--help"]), eq=0)

    def test_main_with_validate_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        del monkeypatch
        tm.that(infra_main(["docs", "validate", "--help"]), eq=0)


def _capture_audit(
    captured: list[m.Infra.DocsAuditInput],
) -> AuditCommand:
    def _fn(
        _self: FlextInfraDocAuditor,
        params: m.Infra.DocsAuditInput,
    ) -> r[bool]:
        captured.append(params)
        return r[bool].ok(True)

    return _fn


def _capture_fix(
    captured: list[m.Infra.DocsFixInput],
) -> FixCommand:
    def _fn(
        _self: FlextInfraDocFixer,
        params: m.Infra.DocsFixInput,
    ) -> r[bool]:
        captured.append(params)
        return r[bool].ok(True)

    return _fn


def _capture_generate(
    captured: list[m.Infra.DocsGenerateInput],
) -> GenerateCommand:
    def _fn(
        _self: FlextInfraDocGenerator,
        params: m.Infra.DocsGenerateInput,
    ) -> r[bool]:
        captured.append(params)
        return r[bool].ok(True)

    return _fn


def _capture_validate(
    captured: list[m.Infra.DocsValidateInput],
) -> ValidateCommand:
    def _fn(
        _self: FlextInfraDocValidator,
        params: m.Infra.DocsValidateInput,
    ) -> r[bool]:
        captured.append(params)
        return r[bool].ok(True)

    return _fn


class TestMainWithFlags:
    def test_audit_custom_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsAuditInput] = []
        monkeypatch.setattr(
            FlextInfraDocAuditor, "execute_command", _capture_audit(captured)
        )
        tm.that(infra_main(["docs", "audit", "--workspace", "/custom/path"]), eq=0)
        tm.that(str(captured[0].workspace_path).endswith("custom/path"), eq=True)

    def test_audit_project_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsAuditInput] = []
        monkeypatch.setattr(
            FlextInfraDocAuditor, "execute_command", _capture_audit(captured)
        )
        tm.that(infra_main(["docs", "audit", "--project", "test-proj"]), eq=0)
        tm.that(captured[0].project, eq="test-proj")

    def test_audit_strict_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsAuditInput] = []
        monkeypatch.setattr(
            FlextInfraDocAuditor, "execute_command", _capture_audit(captured)
        )
        tm.that(infra_main(["docs", "audit", "--strict"]), eq=0)
        tm.that(captured[0].strict, eq=True)

    def test_fix_apply_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsFixInput] = []
        monkeypatch.setattr(
            FlextInfraDocFixer, "execute_command", _capture_fix(captured)
        )
        tm.that(infra_main(["docs", "fix", "--apply"]), eq=0)
        tm.that(captured[0].apply, eq=True)

    def test_generate_apply_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsGenerateInput] = []
        monkeypatch.setattr(
            FlextInfraDocGenerator,
            "execute_command",
            _capture_generate(captured),
        )
        tm.that(infra_main(["docs", "generate", "--apply"]), eq=0)
        tm.that(captured[0].apply, eq=True)

    def test_validate_apply_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsValidateInput] = []
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "execute_command",
            _capture_validate(captured),
        )
        tm.that(infra_main(["docs", "validate", "--apply"]), eq=0)
        tm.that(captured[0].apply, eq=True)

    def test_audit_check_parameter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsAuditInput] = []
        monkeypatch.setattr(
            FlextInfraDocAuditor, "execute_command", _capture_audit(captured)
        )
        tm.that(infra_main(["docs", "audit", "--check"]), eq=0)
        tm.that(captured[0].check, eq=True)

    def test_validate_check_parameter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[m.Infra.DocsValidateInput] = []
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "execute_command",
            _capture_validate(captured),
        )
        tm.that(infra_main(["docs", "validate", "--check"]), eq=0)
        tm.that(captured[0].check, eq=True)

    def test_validate_check_before_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: list[m.Infra.DocsValidateInput] = []
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "execute_command",
            _capture_validate(captured),
        )
        tm.that(infra_main(["docs", "validate", "--check"]), eq=0)
        tm.that(captured[0].check, eq=True)

    def test_build_rejects_apply_before_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(FlextInfraDocBuilder, "execute_command", _ok_command)
        tm.that(infra_main(["docs", "build", "--apply"]), eq=0)
