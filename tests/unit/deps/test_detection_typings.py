from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import patch

from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService, r as tr
from tests.typings import t


class _StubToml:
    def __init__(self, values: Sequence[tr[t.Infra.ContainerDict]]) -> None:
        self._values = values
        self._idx = 0

    def read_plain(self, path: Path) -> tr[t.Infra.ContainerDict]:
        _ = path
        value = self._values[self._idx]
        if self._idx < len(self._values) - 1:
            self._idx += 1
        return value


class TestsFlextInfraDepsDetectionTypings:
    def test_success(self) -> None:
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([
            tr[t.Infra.ContainerDict].ok({"key": "value", "num": 42})
        ])
        result = service.load_dependency_limits(Path("/fake/limits.toml"))
        assert result.get("key") == "value"
        assert result.get("num") == 42

    def test_failure_returns_empty(self) -> None:
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([tr[t.Infra.ContainerDict].fail("not found")])
        tm.that(service.load_dependency_limits(Path("/fake/limits.toml")), empty=True)

    def test_unconvertible_values_skipped(self) -> None:
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([
            tr[t.Infra.ContainerDict].ok({"good": "val", "bad": ["x"]})
        ])
        result = service.load_dependency_limits(Path("/fake/limits.toml"))
        assert "good" in result
        assert "bad" in result

    def test_none_value_preserved(self) -> None:
        service = FlextInfraDependencyDetectionService()
        service.toml = _StubToml([tr[t.Infra.ContainerDict].ok({"key": None})])
        result = service.load_dependency_limits(Path("/fake/limits.toml"))
        assert "key" in result
        tm.that(result["key"], eq=None)

    def test_run_mypy_stub_hints_empty_output(self, tmp_path: Path) -> None:
        service = FlextInfraDependencyDetectionService()
        with patch("mypy.api.run", return_value=("", "", 0)):
            tm.that(tm.ok(service.run_mypy_stub_hints(tmp_path)), eq=([], []))

    def test_parses_hints(
        self,
        tmp_path: Path,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        with patch(
            "mypy.api.run",
            return_value=(
                'note: hint: "pip install types-pyyaml"',
                'error: Library stubs not installed for "requests"',
                1,
            ),
        ):
            tm.that(
                tm.ok(service.run_mypy_stub_hints(tmp_path)),
                eq=(["types-pyyaml"], ["requests"]),
            )
