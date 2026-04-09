"""Tests for documentation command handlers exposed through the canonical API."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeAlias

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import (
    FlextInfraDocBuilder,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
)
from tests import c, m, t

_R: TypeAlias = m.Infra.DocsPhaseReport


def _stub_ok(val: Sequence[_R]) -> Callable[..., r[Sequence[_R]]]:
    return lambda *_a, **_kw: r[Sequence[_R]].ok(val)


def _stub_fail(err: str) -> Callable[..., r[Sequence[_R]]]:
    return lambda *_a, **_kw: r[Sequence[_R]].fail(err)


class TestRunBuild:
    def test_run_build_success_no_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _R(phase="test", scope="test", result="OK")
        result = FlextInfraDocBuilder.execute_command(FlextInfraDocBuilder())
        tm.that(result.is_success, eq=True)

    def test_run_build_success_with_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _R(
            phase="test",
            scope="test",
            result=c.Infra.Status.FAIL,
        )
        result = FlextInfraDocBuilder.execute_command(FlextInfraDocBuilder())
        tm.that(result.is_failure, eq=True)

    def test_run_build_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        result = FlextInfraDocBuilder.execute_command(FlextInfraDocBuilder())
        tm.that(result.is_failure, eq=True)


class TestRunGenerate:
    def test_run_generate_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        result = FlextInfraDocGenerator.execute_command(FlextInfraDocGenerator())
        tm.that(result.is_success, eq=True)

    def test_run_generate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraDocGenerator,
            "generate",
            _stub_fail("generate error"),
        )
        result = FlextInfraDocGenerator.execute_command(FlextInfraDocGenerator())
        tm.that(result.is_failure, eq=True)

    def test_run_generate_with_apply_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_kwargs: t.MutableScalarMapping = {}

        def mock_gen(*_a: t.Scalar, **kw: t.Scalar) -> r[Sequence[_R]]:
            captured_kwargs.update(kw)
            return r[Sequence[_R]].ok([])

        FlextInfraDocGenerator.execute_command(
            FlextInfraDocGenerator(apply=True),
        )
        assert captured_kwargs.get("apply") is True


class TestRunValidate:
    def test_run_validate_success_no_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(phase="test", scope="test", result="OK")
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "validate_workspace",
            _stub_ok([report]),
        )
        result = FlextInfraDocValidator.execute_command(FlextInfraDocValidator())
        tm.that(result.is_success, eq=True)

    def test_run_validate_success_with_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(
            phase="test",
            scope="test",
            result=c.Infra.Status.FAIL,
        )
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "validate_workspace",
            _stub_ok([report]),
        )
        result = FlextInfraDocValidator.execute_command(FlextInfraDocValidator())
        tm.that(result.is_failure, eq=True)

    def test_run_validate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "validate_workspace",
            _stub_fail("validate error"),
        )
        result = FlextInfraDocValidator.execute_command(FlextInfraDocValidator())
        tm.that(result.is_failure, eq=True)

    def test_run_validate_with_check_parameter(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        result = FlextInfraDocValidator.execute_command(
            FlextInfraDocValidator(check=True)
        )
        tm.that(result.is_success, eq=True)
