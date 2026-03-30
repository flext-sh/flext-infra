"""Tests for documentation CLI — main() entry point routing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Callable, MutableMapping, Sequence

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
)
from flext_infra.cli import main
from tests import m, t


def _ok_empty(*a: t.Scalar, **kw: t.Scalar) -> r[Sequence[m.Infra.DocsPhaseReport]]:
    return r[Sequence[m.Infra.DocsPhaseReport]].ok([])


def _ok_audit(*a: t.Scalar, **kw: t.Scalar) -> r[Sequence[m.Infra.DocsPhaseReport]]:
    return r[Sequence[m.Infra.DocsPhaseReport]].ok([])


class TestMainRouting:
    def test_main_with_audit_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "audit", "--workspace", "."])
        monkeypatch.setattr(FlextInfraDocAuditor, "audit", _ok_audit)
        tm.that(main(), eq=0)

    def test_main_with_fix_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "fix", "--workspace", "."])
        monkeypatch.setattr(FlextInfraDocFixer, "fix", _ok_empty)
        tm.that(main(), eq=0)

    def test_main_with_build_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "build", "--workspace", "."])
        monkeypatch.setattr(FlextInfraDocBuilder, "build", _ok_empty)
        tm.that(main(), eq=0)

    def test_main_with_generate_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "docs", "generate", "--workspace", "."],
        )
        monkeypatch.setattr(FlextInfraDocGenerator, "generate", _ok_empty)
        tm.that(main(), eq=0)

    def test_main_with_validate_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "docs", "validate", "--workspace", "."],
        )
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _ok_empty)
        tm.that(main(), eq=0)

    def test_main_with_no_command_prints_help(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["prog"])
        tm.that(main(), eq=1)

    def test_main_with_help_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "--help"])
        tm.that(main(), eq=0)

    def test_main_with_audit_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "audit", "--help"])
        tm.that(main(), eq=0)

    def test_main_with_fix_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "fix", "--help"])
        tm.that(main(), eq=0)

    def test_main_with_build_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "build", "--help"])
        tm.that(main(), eq=0)

    def test_main_with_generate_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "generate", "--help"])
        tm.that(main(), eq=0)

    def test_main_with_validate_help(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "validate", "--help"])
        tm.that(main(), eq=0)


def _capture_audit(
    store: MutableMapping[str, t.Scalar],
) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(*a: t.Scalar, **kw: t.Scalar) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        store.update(kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok([])

    return _fn


def _capture_simple(
    store: MutableMapping[str, t.Scalar],
) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(*a: t.Scalar, **kw: t.Scalar) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        store.update(kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok([])

    return _fn


class TestMainWithFlags:
    def test_audit_custom_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "docs", "audit", "--workspace", "/custom/path"],
        )
        monkeypatch.setattr(FlextInfraDocAuditor, "audit", _capture_audit(kw))
        main()
        tm.that(str(kw.get("workspace_root", "")).endswith("custom/path"), eq=True)

    def test_audit_project_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "docs", "audit", "--project", "test-proj"],
        )
        monkeypatch.setattr(FlextInfraDocAuditor, "audit", _capture_audit(kw))
        main()
        tm.that(kw.get("project"), eq="test-proj")

    def test_audit_strict_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "audit", "--strict"])
        monkeypatch.setattr(FlextInfraDocAuditor, "audit", _capture_audit(kw))
        main()
        tm.that(kw.get("strict"), eq=True)

    def test_fix_apply_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "fix", "--apply"])
        monkeypatch.setattr(FlextInfraDocFixer, "fix", _capture_simple(kw))
        main()
        tm.that(kw.get("apply"), eq=True)

    def test_generate_apply_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "generate", "--apply"])
        monkeypatch.setattr(FlextInfraDocGenerator, "generate", _capture_simple(kw))
        main()
        tm.that(kw.get("apply"), eq=True)

    def test_validate_apply_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "validate", "--apply"])
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _capture_simple(kw))
        main()
        tm.that(kw.get("apply"), eq=True)

    def test_audit_check_parameter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "audit", "--check"])
        monkeypatch.setattr(FlextInfraDocAuditor, "audit", _capture_audit(kw))
        main()
        tm.that(kw.get("check"), eq="all")

    def test_validate_check_parameter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "validate", "--check"])
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _capture_simple(kw))
        main()
        tm.that(kw.get("check"), eq="all")

    def test_validate_check_before_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        kw: MutableMapping[str, t.Scalar] = {}
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "validate", "--check"])
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _capture_simple(kw))
        tm.that(main(), eq=0)
        tm.that(kw.get("check"), eq="all")

    def test_build_rejects_apply_before_subcommand(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "docs", "build", "--apply"])
        tm.that(main(), eq=2)
