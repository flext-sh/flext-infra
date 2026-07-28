"""Real-process contract for per-checkout Make validation serialization."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flext_infra import c, config, u
from flext_tests import tm
from tests import u as test_u


class TestsFlextInfraMakeSerialization:
    """Prove configured Make verbs share one native checkout lock."""

    _process_start_timeout_seconds = 30

    def test_config_owns_relative_checkout_lock_and_serialized_verbs(self) -> None:
        """The typed SSOT owns path, timeout, and the exact protected verbs."""
        serialization = config.Infra.codegen.make.serialization
        declared_verbs = {verb.name for verb in config.Infra.codegen.make.verbs}

        tm.that(serialization.lock_path.is_absolute(), eq=False)
        tm.that(serialization.timeout_seconds, gt=0)
        tm.that(serialization.verbs, empty=False)
        tm.that(set(serialization.verbs).issubset(declared_verbs), eq=True)
        tm.that("setup" in serialization.verbs, eq=False)
        tm.that(serialization.lock_path in serialization.snapshot_excludes, eq=True)
        for excluded_path in serialization.snapshot_excludes:
            tm.that(excluded_path.is_absolute(), eq=False)

    def test_process_exit_classifies_timeout_and_signal(self) -> None:
        """Process outcomes retain standard timeout and signal semantics."""
        timeout_exit = u.Infra.normalize_process_exit_code(
            c.Infra.PROCESS_TIMEOUT_EXIT_CODE
        )
        signal_exit = u.Infra.normalize_process_exit_code(-9)

        tm.that(timeout_exit, eq=c.Infra.PROCESS_TIMEOUT_EXIT_CODE)
        tm.that(u.Infra.classify_process_exit(timeout_exit), eq="timeout")
        tm.that(signal_exit, eq=c.Infra.PROCESS_SIGNAL_EXIT_OFFSET + 9)
        tm.that(u.Infra.classify_process_exit(-9), eq="signal=9")

    def test_fingerprint_distinguishes_index_from_worktree_content(
        self, tmp_path: Path
    ) -> None:
        """A staged change remains visible when working content matches HEAD."""
        tracked = tmp_path / "tracked.txt"
        tracked.write_text("base", encoding="utf-8")
        test_u.Tests.initialize_git_repo(tmp_path)
        exclusions = config.Infra.codegen.make.serialization.snapshot_excludes
        baseline = tm.ok(
            u.Infra.workspace_fingerprint(tmp_path, excluded_paths=exclusions)
        )

        tracked.write_text("staged", encoding="utf-8")
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", tracked.name], cwd=tmp_path))
        staged = tm.ok(
            u.Infra.workspace_fingerprint(tmp_path, excluded_paths=exclusions)
        )
        tracked.write_text("base", encoding="utf-8")
        mixed = tm.ok(
            u.Infra.workspace_fingerprint(tmp_path, excluded_paths=exclusions)
        )

        tm.that(staged.digest, ne=baseline.digest)
        tm.that(mixed.digest, ne=baseline.digest)
        tm.that(mixed.digest, ne=staged.digest)
        tm.that(
            u.Infra.workspace_fingerprint_changes(baseline, mixed), eq=(tracked.name,)
        )

    def test_check_and_test_cannot_overlap_in_one_checkout(
        self, tmp_path: Path
    ) -> None:
        """Two public CLI processes serialize their nested Make executions."""
        worker = tmp_path / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "root = Path(sys.argv[1])\n"
                "label = sys.argv[2]\n"
                "state = root / '.reports' / 'serialization-test'\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "active = state / 'active'\n"
                "started = state / 'check-started'\n"
                "contender = state / 'test-entered'\n"
                "overlap = state / 'overlap'\n"
                "if label == 'check':\n"
                "    active.write_text(label, encoding='utf-8')\n"
                "    started.write_text(label, encoding='utf-8')\n"
                "    deadline = time.monotonic() + 0.5\n"
                "    while time.monotonic() < deadline and not contender.exists():\n"
                "        time.sleep(0.01)\n"
                "    active.unlink()\n"
                "else:\n"
                "    contender.write_text(label, encoding='utf-8')\n"
                "    try:\n"
                "        with active.open('x', encoding='utf-8') as stream:\n"
                "            stream.write(label)\n"
                "    except FileExistsError:\n"
                "        overlap.write_text(label, encoding='utf-8')\n"
                "        raise SystemExit(3)\n"
                "    active.unlink()\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                ".PHONY: _serialized_check _serialized_test\n"
                "_serialized_check:\n"
                f"\t@{sys.executable} {worker} {tmp_path} check\n"
                "_serialized_test:\n"
                f"\t@{sys.executable} {worker} {tmp_path} test\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        command = [
            sys.executable,
            "-m",
            c.Infra.PACKAGE_IMPORT_NAME,
            c.Infra.CLI_GROUP_WORKSPACE,
            "serialize-make",
            "--workspace",
            str(tmp_path),
            "--verb",
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            check_future = executor.submit(u.Cli.run_raw, [*command, "check"], tmp_path)
            deadline = time.monotonic() + self._process_start_timeout_seconds
            while (
                not (
                    tmp_path / ".reports" / "serialization-test" / "check-started"
                ).exists()
                and not check_future.done()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            tm.that(
                (
                    tmp_path / ".reports" / "serialization-test" / "check-started"
                ).exists(),
                eq=True,
            )
            test_future = executor.submit(u.Cli.run_raw, [*command, "test"], tmp_path)
            check_process = tm.ok(
                check_future.result(timeout=self._process_start_timeout_seconds)
            )
            test_process = tm.ok(
                test_future.result(timeout=self._process_start_timeout_seconds)
            )

        tm.that(check_process.exit_code, eq=0)
        tm.that(test_process.exit_code, eq=0)
        tm.that(
            (tmp_path / ".reports" / "serialization-test" / "overlap").exists(),
            eq=False,
        )
        tm.that(
            (tmp_path / config.Infra.codegen.make.serialization.lock_path).is_file(),
            eq=True,
        )

    def test_private_failure_reaches_cli_and_outer_make(self, tmp_path: Path) -> None:
        """A private nonzero status is never coerced into public success."""
        private_exit_code = 7
        make_failure_exit_code = 2
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        cli_command = (
            f"{sys.executable} -m {c.Infra.PACKAGE_IMPORT_NAME} "
            f"{c.Infra.CLI_GROUP_WORKSPACE} serialize-make "
            f"--workspace {tmp_path} --verb test"
        )
        makefile.write_text(
            (
                ".PHONY: test _serialized_test\n"
                "test:\n"
                f"\t@{cli_command}\n"
                "_serialized_test:\n"
                f"\t@exit {private_exit_code}\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)

        direct = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(tmp_path),
                    "--verb",
                    "test",
                ],
                cwd=tmp_path,
            )
        )
        outer_make = tm.ok(
            u.Cli.run_raw([c.Infra.MAKE, "--no-print-directory", "test"], cwd=tmp_path)
        )

        tm.that(direct.exit_code, eq=make_failure_exit_code)
        tm.that(direct.stdout + direct.stderr, has=f"Error {private_exit_code}")
        tm.that(outer_make.exit_code, eq=make_failure_exit_code)
        tm.that(outer_make.exit_code, ne=0)

    def test_writer_ignoring_lock_invalidates_gate_snapshot(
        self, tmp_path: Path
    ) -> None:
        """A concurrent content writer makes a green private target invalid."""
        writer = tmp_path / "writer.py"
        writer.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "time.sleep(0.1)\n"
                "Path(sys.argv[1]).write_text('changed', encoding='utf-8')\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                ".PHONY: _serialized_check\n"
                "_serialized_check:\n"
                f"\t@{sys.executable} {writer} {tmp_path / 'concurrent.txt'} & "
                "sleep 0.4\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)

        process = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(tmp_path),
                    "--verb",
                    "check",
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, eq=int(c.Infra.ScriptExitCode.INFRA))
        tm.that(
            process.stdout + process.stderr,
            has=["workspace changed during serialized Make check", "concurrent.txt"],
        )
