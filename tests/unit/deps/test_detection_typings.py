from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_tests import tm

from flext_infra import FlextInfraDependencyDetectionService
from tests import m, p, r as tr, t


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


class _StubRunner(p.Cli.CommandRunner):
    def __init__(self, result: tr[m.Cli.CommandOutput]) -> None:
        self._result = result
        self.last_kwargs: Mapping[str, str | int | Path | t.StrMapping] = {}

    @override
    def run_raw(
        self,
        cmd: t.StrSequence,
        cwd: t.Cli.PathLike | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
        input_data: bytes | None = None,
    ) -> tr[m.Cli.CommandOutput]:
        del cmd, input_data
        self.last_kwargs = {
            "cwd": cwd or Path.cwd(),
            "timeout": timeout or 0,
            "env": env or {},
        }
        return self._result

    @override
    def run(
        self,
        cmd: t.StrSequence,
        cwd: t.Cli.PathLike | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> tr[m.Cli.CommandOutput]:
        del cmd, cwd, timeout, env
        if self._result.failure:
            return self._result
        output = self._result.value
        if output.exit_code != 0:
            return tr[m.Cli.CommandOutput].fail(
                output.stderr or output.stdout or "Command failed",
            )
        return self._result

    @override
    def capture(
        self,
        cmd: t.StrSequence,
        cwd: t.Cli.PathLike | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> tr[str]:
        return self.run(cmd, cwd=cwd, timeout=timeout, env=env).map(
            lambda output: output.stdout.strip(),
        )

    @override
    def run_checked(
        self,
        cmd: t.StrSequence,
        cwd: t.Cli.PathLike | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> tr[bool]:
        return self.run(cmd, cwd=cwd, timeout=timeout, env=env).map(
            lambda _output: True,
        )

    @override
    def run_to_file(
        self,
        cmd: t.StrSequence,
        output_file: t.Cli.PathLike,
        cwd: t.Cli.PathLike | None = None,
        timeout: int | None = None,
        env: t.StrMapping | None = None,
    ) -> tr[int]:
        result = self.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
        if result.failure:
            return tr[int].fail(result.error or "Command failed")
        output_path = (
            output_file if isinstance(output_file, Path) else Path(output_file)
        )
        output_path.write_text(
            f"{result.value.stdout}{result.value.stderr}",
            encoding="utf-8",
        )
        return tr[int].ok(result.value.exit_code)


class TestLoadDependencyLimits:
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


class TestRunMypyStubHints:
    def test_mypy_not_found(self, tmp_path: Path) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        tm.that(tm.ok(service.run_mypy_stub_hints(tmp_path, venv_bin)), eq=([], []))

    def test_runner_failure(
        self,
        tmp_path: Path,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "mypy").write_text("", encoding="utf-8")
        service.runner = _StubRunner(tr[m.Cli.CommandOutput].fail("mypy crash"))
        tm.fail(service.run_mypy_stub_hints(tmp_path, venv_bin))

    def test_parses_hints(
        self,
        tmp_path: Path,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "mypy").write_text("", encoding="utf-8")
        out = m.Cli.CommandOutput(
            exit_code=0,
            stdout='note: hint: "pip install types-pyyaml"',
            stderr='error: Library stubs not installed for "requests"',
        )
        service.runner = _StubRunner(tr[m.Cli.CommandOutput].ok(out))
        tm.ok(service.run_mypy_stub_hints(tmp_path, venv_bin))

    def test_run_mypy_stub_hints_with_timeout(
        self,
        tmp_path: Path,
    ) -> None:
        service = FlextInfraDependencyDetectionService()
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "mypy").write_text("", encoding="utf-8")
        out = m.Cli.CommandOutput(exit_code=0, stdout="", stderr="")
        runner = _StubRunner(tr[m.Cli.CommandOutput].ok(out))
        service.runner = runner
        tm.ok(service.run_mypy_stub_hints(tmp_path, venv_bin, timeout=600))
        tm.that(runner.last_kwargs["timeout"], eq=600)
