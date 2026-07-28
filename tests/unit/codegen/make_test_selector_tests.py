"""Behavior contract for focused pytest selection through generated Make."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import u
from tests import u as test_u


class TestsMakeTestSelector:
    """The generated `test` recipe honours the documented argument knob."""

    def test_explicit_target_replaces_the_default_suite(self, tmp_path: Path) -> None:
        """A focused target is the pytest target, not an appendix to tests/."""
        makefile = tm.ok(u.Cli.files_read_text(Path("Makefile")))
        (tmp_path / "Makefile").write_text(makefile, encoding="utf-8")
        test_u.Tests.write_executable(
            tmp_path / ".venv" / "bin" / "python", "#!/bin/sh\nexit 0\n"
        )
        invocation_log = tmp_path / "uv-args.log"
        uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(
            uv, f'#!/bin/sh\nprintf "%s\\n" "$@" > "{invocation_log}"\n'
        )
        selected = "tests/unit/selected_test.py"

        executed = tm.ok(
            u.Cli.run_raw(
                [
                    "make",
                    "--no-print-directory",
                    "test",
                    f"PYTEST_ARGS={selected}",
                    f"UV={uv}",
                ],
                cwd=tmp_path,
            )
        )

        tm.that(executed.exit_code, eq=0)
        arguments = invocation_log.read_text(encoding="utf-8")
        tm.that(arguments, has=selected)
        tm.that(str(tmp_path / "tests") in arguments, eq=False)
