"""Tests for documentation CLI — _run_build, _run_generate, _run_validate handlers."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence

import pytest
from flext_core import r, t
from flext_tests import tm

from flext_infra import (
    FlextInfraDocBuilder,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
    u,
)
from flext_infra.docs.__main__ import _run_build, _run_generate, _run_validate

from ...models import m

_R = m.Infra.DocsPhaseReport


def _cli_args(
    extra_defaults: Mapping[str, t.Scalar | None],
    **overrides: t.Scalar,
) -> u.Infra.CliArgs:
    defaults: Mapping[str, t.Scalar | None] = {
        "workspace": ".",
        "project": None,
        "projects": None,
        "check": False,
        "apply": False,
        **extra_defaults,
    }
    defaults.update(overrides)
    return u.Infra.resolve(argparse.Namespace(**defaults))


def _build_args(**overrides: t.Scalar) -> u.Infra.CliArgs:
    return _cli_args({}, **overrides)


def _gen_args(**overrides: t.Scalar) -> u.Infra.CliArgs:
    return _cli_args({"apply": False}, **overrides)


def _val_args(**overrides: t.Scalar) -> u.Infra.CliArgs:
    return _cli_args({"check": True, "apply": False}, **overrides)


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
        tm.that(_run_build(_build_args()), eq=0)

    def test_run_build_success_with_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(phase="test", scope="test", result="FAIL")
        monkeypatch.setattr(FlextInfraDocBuilder, "build", _stub_ok([report]))
        tm.that(_run_build(_build_args()), eq=1)

    def test_run_build_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocBuilder, "build", _stub_fail("build error"))
        tm.that(_run_build(_build_args()), eq=1)


class TestRunGenerate:
    def test_run_generate_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(FlextInfraDocGenerator, "generate", _stub_ok([]))
        tm.that(_run_generate(_gen_args()), eq=0)

    def test_run_generate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraDocGenerator,
            "generate",
            _stub_fail("generate error"),
        )
        tm.that(_run_generate(_gen_args()), eq=1)

    def test_run_generate_with_apply_flag(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_kwargs: Mapping[str, t.Scalar] = {}

        def mock_gen(*_a: t.Scalar, **kw: t.Scalar) -> r[Sequence[_R]]:
            captured_kwargs.update(kw)
            return r[Sequence[_R]].ok([])

        monkeypatch.setattr(FlextInfraDocGenerator, "generate", mock_gen)
        _run_generate(_gen_args(apply=True))
        assert captured_kwargs.get("apply") is True


class TestRunValidate:
    def test_run_validate_success_no_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(phase="test", scope="test", result="OK")
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _stub_ok([report]))
        tm.that(_run_validate(_val_args()), eq=0)

    def test_run_validate_success_with_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        report = _R(phase="test", scope="test", result="FAIL")
        monkeypatch.setattr(FlextInfraDocValidator, "validate", _stub_ok([report]))
        tm.that(_run_validate(_val_args()), eq=1)

    def test_run_validate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            FlextInfraDocValidator,
            "validate",
            _stub_fail("validate error"),
        )
        tm.that(_run_validate(_val_args()), eq=1)

    def test_run_validate_with_check_parameter(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_kwargs: Mapping[str, t.Scalar] = {}

        def mock_val(*_a: t.Scalar, **kw: t.Scalar) -> r[Sequence[_R]]:
            captured_kwargs.update(kw)
            return r[Sequence[_R]].ok([])

        monkeypatch.setattr(FlextInfraDocValidator, "validate", mock_val)
        _run_validate(_val_args(), check=True)
        assert captured_kwargs.get("check") == "all"
