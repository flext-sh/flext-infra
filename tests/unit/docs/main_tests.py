"""Tests for documentation CLI — _handle_audit and _handle_fix handlers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocFixer,
)
from tests import m, t


def _ok(
    val: Sequence[m.Infra.DocsPhaseReport],
) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(
        _self: t.Scalar,
        *_a: t.Scalar,
        **_kw: t.Scalar,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        _ = (_self, *_a, _kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok(val)

    return _fn


def _fail_report(err: str) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(
        _self: t.Scalar,
        *_a: t.Scalar,
        **_kw: t.Scalar,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        _ = (_self, *_a, _kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].fail(err)

    return _fn


def _ok_list(
    val: Sequence[m.Infra.DocsPhaseReport],
) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(
        _self: t.Scalar,
        *_a: t.Scalar,
        **_kw: t.Scalar,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        _ = (_self, *_a, _kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok(val)

    return _fn


def _fail_list(err: str) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(
        _self: t.Scalar,
        *_a: t.Scalar,
        **_kw: t.Scalar,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        _ = (_self, *_a, _kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].fail(err)

    return _fn


def _capturing(
    captured: t.MutableScalarMapping,
) -> Callable[..., r[Sequence[m.Infra.DocsPhaseReport]]]:
    def _fn(
        _self: t.Scalar,
        *_a: t.Scalar,
        **kw: t.Scalar,
    ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
        _ = (_self, *_a, kw)
        captured.update(kw)
        return r[Sequence[m.Infra.DocsPhaseReport]].ok([])

    return _fn


class TestRunAudit:
    @pytest.mark.parametrize(
        ("passed", "expected_success"),
        [(True, True), (False, False)],
    )
    def test_run_audit_report_exit_code(
        self,
        monkeypatch: pytest.MonkeyPatch,
        passed: bool,
        expected_success: bool,
    ) -> None:
        m.Infra.DocsPhaseReport(
            phase="audit",
            scope="root",
            items=[],
            checks=["links"],
            strict=True,
            passed=passed,
        )
        result = FlextInfraDocAuditor.execute_command(
            FlextInfraDocAuditor(strict_mode=True),
        )
        tm.that(result.is_success, eq=expected_success)

    def test_run_audit_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        result = FlextInfraDocAuditor.execute_command(
            FlextInfraDocAuditor(strict_mode=True),
        )
        tm.that(result.is_failure, eq=True)

    @pytest.mark.parametrize(
        ("check", "strict", "field", "expected"),
        [
            (True, False, "check", "all"),
            (False, True, "strict", True),
        ],
    )
    def test_run_audit_forwards_arguments(
        self,
        monkeypatch: pytest.MonkeyPatch,
        check: bool,
        strict: bool,
        field: str,
        expected: t.Scalar,
    ) -> None:
        captured_kwargs: t.MutableScalarMapping = {}
        FlextInfraDocAuditor.execute_command(
            FlextInfraDocAuditor(check=check, strict_mode=strict),
        )
        captured_kwargs.get("params")


class TestRunFix:
    def test_run_fix_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        result = FlextInfraDocFixer.execute_command(FlextInfraDocFixer())
        tm.that(result.is_success, eq=True)

    def test_run_fix_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        result = FlextInfraDocFixer.execute_command(FlextInfraDocFixer())
        tm.that(result.is_failure, eq=True)

    @pytest.mark.parametrize(("apply", "expected"), [(True, True), (False, False)])
    def test_run_fix_forwards_apply_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
        apply: bool,
        expected: bool,
    ) -> None:
        captured_kwargs: t.MutableScalarMapping = {}

        def mock_fix(
            _self: t.Scalar,
            *_a: t.Scalar,
            **kw: t.Scalar,
        ) -> r[Sequence[m.Infra.DocsPhaseReport]]:
            _ = (_self, *_a, kw)
            captured_kwargs.update(kw)
            return r[Sequence[m.Infra.DocsPhaseReport]].ok([])

        FlextInfraDocFixer.execute_command(FlextInfraDocFixer(apply=apply))
        assert captured_kwargs.get("apply") == expected
