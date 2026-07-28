"""Real-process contract for per-checkout Make validation serialization."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from filelock import FileLock, Timeout
from flext_infra import c, config, m, p, u
from flext_tests import tm
from tests import u as test_u

_MUTATION_CASES = tuple(
    (verb, mutation_what, fixed_point_what)
    for verb, fixed_points in config.Infra.codegen.make.serialization.mutation_fixed_points.items()
    for mutation_what, fixed_point_what in fixed_points.items()
)


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
        for verb, fixed_points in serialization.mutation_fixed_points.items():
            tm.that(verb in serialization.verbs, eq=True)
            tm.that(fixed_points, empty=False)
            for mutation_what, fixed_point_what in fixed_points.items():
                tm.that(mutation_what, empty=False)
                tm.that(fixed_point_what, empty=False)
        tm.that(serialization.lock_path in serialization.snapshot_excludes, eq=True)
        for excluded_path in serialization.snapshot_excludes:
            tm.that(excluded_path.is_absolute(), eq=False)

    def test_mutation_mapping_requires_a_fixed_point(self) -> None:
        """Every declared mutating selector has a validation selector."""
        serialization = config.Infra.codegen.make.serialization
        payload = serialization.model_dump(mode="python")
        empty_fixed_points: dict[str, str] = {}
        payload["mutation_fixed_points"] = {serialization.verbs[0]: empty_fixed_points}

        with pytest.raises(
            ValueError, match="make serialization mutation verbs require fixed points"
        ):
            m.Infra.MakeSerializationSpec.model_validate(payload)

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

    def test_fingerprint_represents_a_deleted_tracked_path(
        self, tmp_path: Path
    ) -> None:
        """A tracked deletion is snapshot state, not a fingerprint read failure."""
        tracked = tmp_path / "tracked.txt"
        tracked.write_text("base", encoding="utf-8")
        test_u.Tests.initialize_git_repo(tmp_path)
        exclusions = config.Infra.codegen.make.serialization.snapshot_excludes
        baseline = tm.ok(
            u.Infra.workspace_fingerprint(tmp_path, excluded_paths=exclusions)
        )

        tracked.unlink()
        deleted = tm.ok(
            u.Infra.workspace_fingerprint(tmp_path, excluded_paths=exclusions)
        )

        tm.that(deleted.digest, ne=baseline.digest)
        tm.that(
            u.Infra.workspace_fingerprint_changes(baseline, deleted), eq=(tracked.name,)
        )

    def test_serialized_validations_cannot_overlap_in_one_checkout(
        self, tmp_path: Path
    ) -> None:
        """Two public CLI processes serialize their nested Make executions."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        worker = tmp_path / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "root = Path(sys.argv[1])\n"
                "state = root / '.reports' / 'serialization-test'\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "active = state / 'active'\n"
                "started = state / 'incumbent-started'\n"
                "contender = state / 'contender-entered'\n"
                "overlap = state / 'overlap'\n"
                "if not started.exists():\n"
                "    active.write_text('incumbent', encoding='utf-8')\n"
                "    started.write_text('', encoding='utf-8')\n"
                "    release = state / 'incumbent-release'\n"
                "    deadline = time.monotonic() + 30\n"
                "    while time.monotonic() < deadline and not release.exists():\n"
                "        time.sleep(0.01)\n"
                "    if not release.exists():\n"
                "        raise SystemExit(9)\n"
                "    active.unlink()\n"
                "else:\n"
                "    contender.write_text('', encoding='utf-8')\n"
                "    try:\n"
                "        with active.open('x', encoding='utf-8') as stream:\n"
                "            stream.write('contender')\n"
                "    except FileExistsError:\n"
                "        overlap.write_text('', encoding='utf-8')\n"
                "        raise SystemExit(3)\n"
                "    active.unlink()\n"
            ),
            encoding="utf-8",
        )
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{validation_verb}\n"
                f"_serialized_{validation_verb}:\n"
                f"\t@{sys.executable} {worker} {tmp_path}\n"
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
            "--makefile",
            str(makefile),
            "--verb",
        ]

        with ThreadPoolExecutor(max_workers=2) as executor:
            incumbent_future = executor.submit(
                u.Cli.run_raw, [*command, validation_verb], tmp_path
            )
            deadline = time.monotonic() + self._process_start_timeout_seconds
            while (
                not (
                    tmp_path / ".reports" / "serialization-test" / "incumbent-started"
                ).exists()
                and not incumbent_future.done()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            tm.that(
                (
                    tmp_path / ".reports" / "serialization-test" / "incumbent-started"
                ).exists(),
                eq=True,
            )
            contender_future = executor.submit(
                u.Cli.run_raw, [*command, validation_verb], tmp_path
            )
            (
                tmp_path / ".reports" / "serialization-test" / "incumbent-release"
            ).write_text("", encoding="utf-8")
            incumbent_process = tm.ok(
                incumbent_future.result(timeout=self._process_start_timeout_seconds)
            )
            contender_process = tm.ok(
                contender_future.result(timeout=self._process_start_timeout_seconds)
            )

        tm.that(incumbent_process.exit_code, eq=0)
        tm.that(contender_process.exit_code, eq=0)
        tm.that(
            (tmp_path / ".reports" / "serialization-test" / "overlap").exists(),
            eq=False,
        )
        tm.that(
            (tmp_path / config.Infra.codegen.make.serialization.lock_path).is_file(),
            eq=True,
        )

    def test_external_callers_share_the_selected_make_engine_lock(
        self, tmp_path: Path
    ) -> None:
        """Different callers of one selected Make owner cannot overlap."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        state = engine_root / "state"
        worker = engine_root / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "state = Path(sys.argv[1])\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "active = state / 'active'\n"
                "started = state / 'started'\n"
                "release = state / 'release'\n"
                "overlap = state / 'overlap'\n"
                "if not started.exists():\n"
                "    active.write_text('incumbent', encoding='utf-8')\n"
                "    started.write_text('', encoding='utf-8')\n"
                "    deadline = time.monotonic() + 30\n"
                "    while time.monotonic() < deadline and not release.exists():\n"
                "        time.sleep(0.01)\n"
                "    if not release.exists():\n"
                "        raise SystemExit(9)\n"
                "    active.unlink()\n"
                "else:\n"
                "    try:\n"
                "        with active.open('x', encoding='utf-8') as stream:\n"
                "            stream.write('contender')\n"
                "    except FileExistsError:\n"
                "        overlap.write_text('', encoding='utf-8')\n"
                "        raise SystemExit(3)\n"
                "    active.unlink()\n"
            ),
            encoding="utf-8",
        )
        selected_makefile = engine_root / "canonical.mk"
        selected_makefile.write_text(
            (
                f".PHONY: _serialized_{validation_verb}\n"
                f"_serialized_{validation_verb}:\n"
                f"\t@{sys.executable} {worker} {state}\n"
            ),
            encoding="utf-8",
        )
        callers = (tmp_path / "caller-a", tmp_path / "caller-b")
        for caller in callers:
            caller.mkdir()
            test_u.Tests.initialize_git_repo(caller)

        def command(caller: Path) -> p.Result[p.Cli.CommandOutput]:
            return u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    c.Infra.PACKAGE_IMPORT_NAME,
                    c.Infra.CLI_GROUP_WORKSPACE,
                    "serialize-make",
                    "--workspace",
                    str(caller),
                    "--makefile",
                    str(selected_makefile),
                    "--verb",
                    validation_verb,
                ],
                cwd=caller,
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            incumbent_future = executor.submit(command, callers[0])
            deadline = time.monotonic() + self._process_start_timeout_seconds
            while (
                not (state / "started").exists()
                and not incumbent_future.done()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            tm.that((state / "started").exists(), eq=True)
            contender_future = executor.submit(command, callers[1])
            (state / "release").write_text("", encoding="utf-8")
            incumbent = tm.ok(
                incumbent_future.result(timeout=self._process_start_timeout_seconds)
            )
            contender = tm.ok(
                contender_future.result(timeout=self._process_start_timeout_seconds)
            )

        tm.that(incumbent.exit_code, eq=0)
        tm.that(contender.exit_code, eq=0)
        tm.that((state / "overlap").exists(), eq=False)
        tm.that(
            (engine_root / config.Infra.codegen.make.serialization.lock_path).is_file(),
            eq=True,
        )

    def test_private_failure_reaches_cli_and_outer_make(self, tmp_path: Path) -> None:
        """A private nonzero status is never coerced into public success."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        private_exit_code = 7
        make_failure_exit_code = 2
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        cli_command = (
            f"{sys.executable} -m {c.Infra.PACKAGE_IMPORT_NAME} "
            f"{c.Infra.CLI_GROUP_WORKSPACE} serialize-make "
            f"--workspace {tmp_path} --makefile {makefile} --verb {validation_verb}"
        )
        makefile.write_text(
            (
                f".PHONY: {validation_verb} _serialized_{validation_verb}\n"
                f"{validation_verb}:\n"
                f"\t@{cli_command}\n"
                f"_serialized_{validation_verb}:\n"
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
                    "--makefile",
                    str(makefile),
                    "--verb",
                    validation_verb,
                ],
                cwd=tmp_path,
            )
        )
        outer_make = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", validation_verb], cwd=tmp_path
            )
        )

        tm.that(direct.exit_code, eq=make_failure_exit_code)
        tm.that(direct.stdout + direct.stderr, has=f"Error {private_exit_code}")
        tm.that(outer_make.exit_code, eq=make_failure_exit_code)
        tm.that(outer_make.exit_code, ne=0)

    def test_selected_makefile_is_required_at_the_cli_boundary(
        self, tmp_path: Path
    ) -> None:
        """A caller cannot silently fall back to a different Make owner."""
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
                    config.Infra.codegen.make.serialization.verbs[0],
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, ne=0)
        tm.that(process.stdout + process.stderr, has="makefile")

    def test_writer_ignoring_lock_invalidates_gate_snapshot(
        self, tmp_path: Path
    ) -> None:
        """A concurrent content writer makes a green private target invalid."""
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
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
                f".PHONY: _serialized_{validation_verb}\n"
                f"_serialized_{validation_verb}:\n"
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
                    "--makefile",
                    str(makefile),
                    "--verb",
                    validation_verb,
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, eq=int(c.Infra.ScriptExitCode.INFRA))
        tm.that(
            process.stdout + process.stderr,
            has=[
                f"workspace changed during serialized Make {validation_verb}",
                "concurrent.txt",
            ],
        )

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_declared_mutation_runs_fixed_point_without_rejecting_own_output(
        self,
        tmp_path: Path,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """An authorized generator apply owns its projection and proves stability."""
        make_config = config.Infra.codegen.make
        projection = tmp_path / "generated.txt"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.selector})" = "{mutation_what}" ]; then '
                f"printf 'generated\\n' > {projection}; "
                f'elif [ "$({make_config.selector})" = "{fixed_point_what}" ]; then '
                f'[ "$({make_config.apply_variable})" != '
                f'"{make_config.apply_value}" ] || exit 9; '
                "else exit 8; fi\n"
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
                    "--makefile",
                    str(makefile),
                    "--verb",
                    mutation_verb,
                ],
                cwd=tmp_path,
                env={
                    make_config.apply_variable: make_config.apply_value,
                    make_config.selector: mutation_what,
                },
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(projection.read_text(encoding="utf-8"), eq="generated\n")

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_mutation_lock_covers_fixed_point(
        self,
        tmp_path: Path,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """The checkout lock covers apply, fixed-point validation, and final snapshot."""
        make_config = config.Infra.codegen.make
        worker = tmp_path / "worker.py"
        worker.write_text(
            (
                "from pathlib import Path\n"
                "import sys\n"
                "import time\n"
                "state = Path(sys.argv[1])\n"
                "phase = sys.argv[2]\n"
                "state.mkdir(parents=True, exist_ok=True)\n"
                "events = state / 'events'\n"
                "with events.open('a', encoding='utf-8') as stream:\n"
                "    stream.write(f'{phase}-start\\n')\n"
                "(state / f'{phase}-started').write_text('', encoding='utf-8')\n"
                "release = state / f'{phase}-release'\n"
                "deadline = time.monotonic() + 30\n"
                "while not release.exists() and time.monotonic() < deadline:\n"
                "    time.sleep(0.01)\n"
                "if not release.exists():\n"
                "    raise SystemExit(9)\n"
                "with events.open('a', encoding='utf-8') as stream:\n"
                "    stream.write(f'{phase}-end\\n')\n"
            ),
            encoding="utf-8",
        )
        state = tmp_path / ".reports" / "serialization-fixed-point"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.selector})" = "{mutation_what}" ]; then '
                f"{sys.executable} {worker} {state} mutation; "
                f'elif [ "$({make_config.selector})" = "{fixed_point_what}" ]; then '
                f"{sys.executable} {worker} {state} fixed-point; "
                "else exit 8; "
                "fi\n"
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
            "--makefile",
            str(makefile),
            "--verb",
        ]

        lock_path = tmp_path / make_config.serialization.lock_path
        with ThreadPoolExecutor(max_workers=1) as executor:
            mutation_future = executor.submit(
                u.Cli.run_raw,
                [*command, mutation_verb],
                tmp_path,
                env={
                    make_config.apply_variable: make_config.apply_value,
                    make_config.selector: mutation_what,
                },
            )
            deadline = time.monotonic() + self._process_start_timeout_seconds
            while (
                not (state / "mutation-started").exists()
                and not mutation_future.done()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            tm.that((state / "mutation-started").exists(), eq=True)
            mutation_lock_held = False
            try:
                with FileLock(lock_path, timeout=0):
                    pass
            except Timeout:
                mutation_lock_held = True
            tm.that(mutation_lock_held, eq=True)
            (state / "mutation-release").write_text("", encoding="utf-8")

            deadline = time.monotonic() + self._process_start_timeout_seconds
            while (
                not (state / "fixed-point-started").exists()
                and not mutation_future.done()
                and time.monotonic() < deadline
            ):
                time.sleep(0.01)
            tm.that((state / "fixed-point-started").exists(), eq=True)
            fixed_point_lock_held = False
            try:
                with FileLock(lock_path, timeout=0):
                    pass
            except Timeout:
                fixed_point_lock_held = True
            tm.that(fixed_point_lock_held, eq=True)
            (state / "fixed-point-release").write_text("", encoding="utf-8")
            mutation = tm.ok(
                mutation_future.result(timeout=self._process_start_timeout_seconds)
            )

        tm.that(mutation.exit_code, eq=0, msg=mutation.stdout + mutation.stderr)
        with FileLock(lock_path, timeout=0):
            pass
        tm.that(
            (state / "events").read_text(encoding="utf-8").splitlines(),
            eq=[
                "mutation-start",
                "mutation-end",
                "fixed-point-start",
                "fixed-point-end",
            ],
        )
