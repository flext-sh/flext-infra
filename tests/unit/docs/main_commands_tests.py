"""Tests for documentation CLI — FlextInfraDocsCli handlers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeAlias

import pytest
from flext_tests import tm
from tests import t

from flext_core import r
from flext_infra import (
    FlextInfraDocBuilder,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    c,
    m,
)

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
        report = _R(phase="test", scope="test", result="OK")
        monkeypatch.setattr(FlextInfraDocBuilder, "build", _stub_ok([report]))
        result = FlextInfraDocBuilder().execute_command(m.Infra.DocsBuildInput())
        tm.that(result.is_success, eq=True)

    def test_run_build_success_with_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(
            phase="test",
            scope="test",
            result=c.Infra.Status.FAIL,
        )
        monkeypatch.setattr(FlextInfraDocBuilder, "build", _stub_ok([report]))
        result = FlextInfraDocBuilder().execute_command(m.Infra.DocsBuildInput())
        tm.that(result.is_failure, eq=True)

    def test_run_build_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocBuilder, "build", _stub_fail("build error"))
        result = FlextInfraDocBuilder().execute_command(m.Infra.DocsBuildInput())
        tm.that(result.is_failure, eq=True)


class TestRunGenerate:
    def test_run_generate_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocGenerator, "generate", _stub_ok([]))
        result = FlextInfraDocGenerator().execute_command(m.Infra.DocsGenerateInput())
        tm.that(result.is_success, eq=True)

    def test_run_generate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraDocGenerator,
            "generate",
            _stub_fail("generate error"),
        )
        result = FlextInfraDocGenerator().execute_command(m.Infra.DocsGenerateInput())
        tm.that(result.is_failure, eq=True)

    def test_run_generate_with_apply_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_kwargs: t.MutableScalarMapping = {}

        def mock_gen(*_a: t.Scalar, **kw: t.Scalar) -> r[Sequence[_R]]:
            captured_kwargs.update(kw)
            return r[Sequence[_R]].ok([])

        monkeypatch.setattr(FlextInfraDocGenerator, "generate", mock_gen)
        FlextInfraDocGenerator().execute_command(m.Infra.DocsGenerateInput(apply=True))
        assert captured_kwargs.get("apply") is True


class TestRunValidate:
    def test_run_validate_success_no_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(phase="test", scope="test", result="OK")
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _stub_ok([report]))
        result = FlextInfraDocValidator().execute_command(m.Infra.DocsValidateInput())
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
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _stub_ok([report]))
        result = FlextInfraDocValidator().execute_command(m.Infra.DocsValidateInput())
        tm.that(result.is_failure, eq=True)

    def test_run_validate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "validate",
            _stub_fail("validate error"),
        )
        result = FlextInfraDocValidator().execute_command(m.Infra.DocsValidateInput())
        tm.that(result.is_failure, eq=True)

    def test_run_validate_with_check_parameter(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_kwargs: t.MutableScalarMapping = {}

        def mock_val(*_a: t.Scalar, **kw: t.Scalar) -> r[Sequence[_R]]:
            captured_kwargs.update(kw)
            return r[Sequence[_R]].ok([])

        monkeypatch.setattr(FlextInfraDocValidator, "validate", mock_val)
        FlextInfraDocValidator().execute_command(m.Infra.DocsValidateInput(check=True))
        assert captured_kwargs.get("check") == "all"
