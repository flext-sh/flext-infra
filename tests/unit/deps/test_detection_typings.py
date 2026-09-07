"""Test detection typings behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import p, r as tr
from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from flext_tests import tm
from tests import t, u


class _StubToml:
    def __init__(self, values: t.SequenceOf[p.Result[t.JsonMapping]]) -> None:
        self._values: tuple[p.Result[t.JsonMapping], ...] = tuple(values)
        self._idx = 0

    def read_plain(self, path: Path) -> p.Result[t.JsonMapping]:
        _ = path
        value: p.Result[t.JsonMapping] = self._values[self._idx]
        if self._idx < len(self._values) - 1:
            self._idx += 1
        return value


class TestsFlextInfraDepsDetectionTypings:
    """Test flext infra deps detection typings behavior."""

    def test_success(self) -> None:
        """Verify dependency limit loading succeeds."""
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([tr[t.JsonMapping].ok({"key": "value", "num": 42})])
        result = service.load_dependency_limits(Path("/fake/limits.toml"))
        tm.that(result.get("key"), eq="value")
        tm.that(result.get("num"), eq=42)

    def test_failure_fails_loud(self) -> None:
        """Verify a failed limits read escapes instead of returning empty."""
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([tr[t.JsonMapping].fail("not found")])
        with pytest.raises(RuntimeError, match="failed to load dependency limits"):
            service.load_dependency_limits(Path("/fake/limits.toml"))

    def test_unconvertible_values_skipped(self) -> None:
        """Verify unconvertible values skipped."""
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([tr[t.JsonMapping].ok({"good": "val", "bad": ["x"]})])
        result = service.load_dependency_limits(Path("/fake/limits.toml"))
        tm.that(result, has="good")
        tm.that(result, has="bad")

    def test_none_value_preserved(self) -> None:
        """Verify none value preserved."""
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([tr[t.JsonMapping].ok({"key": None})])
        result = service.load_dependency_limits(Path("/fake/limits.toml"))
        tm.that(result, has="key")
        tm.that(result["key"], eq=None)

    def test_run_mypy_stub_hints_empty_output(self, tmp_path: Path) -> None:
        """Verify run mypy stub hints empty output."""
        service = FlextInfraDependencyDetectionService()
        service.runner = u.Tests.command_runner()
        tm.that(tm.ok(service.run_mypy_stub_hints(tmp_path)), eq=([], []))

    def test_parses_hints(self, tmp_path: Path) -> None:
        """Verify parses hints."""
        service = FlextInfraDependencyDetectionService()
        service.runner = u.Tests.command_runner(
            stdout='note: hint: "pip install types-pyyaml"',
            stderr='error: Library stubs not installed for "requests"',
            returncode=1,
        )
        tm.that(
            tm.ok(service.run_mypy_stub_hints(tmp_path)),
            eq=(["types-pyyaml"], ["requests"]),
        )
