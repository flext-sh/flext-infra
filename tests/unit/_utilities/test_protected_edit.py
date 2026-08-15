from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from flext_core import r
from flext_tests import tm
from tests import c, m, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraUtilitiesProtectedEdit:
    def test_preview_source_writes_restores_original_sources_after_preview(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.preview_source_writes(
            {py_file: updated_source}, workspace=tmp_path, gates=("lint",)
        )

        tm.that(result, eq=(True, []))
        tm.that(py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT), eq=original_source)

    def test_protected_source_write_skips_pytest_for_non_test_file(
        self, tmp_path: Path
    ) -> None:
        py_file = tmp_path / "sample.py"
        original_source = "def value() -> int:\n    return 1\n"
        updated_source = "def value() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source=updated_source, gates=("lint",)
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    def test_protected_source_write_treats_no_tests_collected_as_success(
        self, tmp_path: Path
    ) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        py_file = tests_dir / "test_placeholder.py"
        original_source = "def helper() -> int:\n    return 1\n"
        updated_source = "def helper() -> int:\n    return 2\n"
        py_file.write_text(original_source, encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_write(
            py_file,
            request=m.Infra.ProtectedSourceWriteRequest(
                workspace=tmp_path, updated_source=updated_source, gates=("lint",)
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            py_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n"),
            eq=updated_source.rstrip("\n"),
        )

    def test_protected_source_writes_applies_request_options(
        self, tmp_path: Path
    ) -> None:
        left_file = tmp_path / "left.py"
        right_file = tmp_path / "right.py"
        left_file.write_text("VALUE = 1\n", encoding=c.Cli.ENCODING_DEFAULT)
        right_file.write_text("VALUE = 10\n", encoding=c.Cli.ENCODING_DEFAULT)

        result = u.Infra.protected_source_writes(
            {left_file: "VALUE = 2\n", right_file: "VALUE = 20\n"},
            request=m.Infra.ProtectedSourceWritesRequest(
                workspace=tmp_path, gates=("lint",), skip_pytest=True
            ),
        )

        tm.that(result, eq=(True, []))
        tm.that(
            (
                left_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n")
                == "VALUE = 2"
            ),
            eq=True,
        )
        tm.that(
            (
                right_file.read_text(encoding=c.Cli.ENCODING_DEFAULT).rstrip("\n")
                == "VALUE = 20"
            ),
            eq=True,
        )

    def test_every_lint_gate_runs_concurrently(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No lint gate is serialized ahead of the others.

        mro-38p39: a lint snapshot runs one subprocess per gate. Running any of
        them before the pool makes the snapshot cost that gate's full wall clock
        plus the slowest of the rest, instead of just the slowest. Measured on
        the two slowest tests in the suite: 8 snapshots x 4 gates, 0.297s per
        gate, with ruff serialized ahead of a 3-worker pool.

        The gates are independent -- each builds its own command and returns a
        value, touching no shared state -- so the snapshot wall clock must be the
        slowest single gate, never their sum. This asserts the observable
        subprocess timeline, not the internal structure.
        """
        py_file = tmp_path / "sample.py"
        py_file.write_text("VALUE = 1\n", encoding=c.Cli.ENCODING_DEFAULT)
        gates = ("ruff", "pyrefly")
        started: list[float] = []
        finished: list[float] = []

        def _slow_run(*_args: object, **_kwargs: object) -> object:
            started.append(time.monotonic())
            time.sleep(0.4)
            finished.append(time.monotonic())
            return r.ok(u.Tests.create_command_output())

        monkeypatch.setattr(u.Cli, "run_raw", _slow_run)
        _ = u.Infra.lint_snapshot(py_file, tmp_path, gates=gates)

        tm.that(len(started), eq=len(gates))
        # Concurrent: the last gate starts before the first one finishes.
        tm.that(max(started) < min(finished), eq=True)
