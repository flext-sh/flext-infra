"""Real-process contract for per-checkout Make validation serialization."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock

import pytest
from filelock import FileLock

from flext_core import r
from flext_infra import c, config, m, p, t, u
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_tests import tm
from tests import u as test_u

_TRANSACTIONAL_VERBS = tuple(
    verb.name for verb in config.Infra.codegen.make.verbs if verb.transactional
)


class TestsFlextInfraMakeSerialization:
    """Prove configured Make verbs share one native checkout lock."""

    _process_start_timeout_seconds = 30

    def test_config_owns_relative_checkout_lock_and_serialized_verbs(self) -> None:
        """The typed SSOT owns path, timeout, and the exact protected verbs."""
        serialization = config.Infra.codegen.make.serialization
        make_config = config.Infra.codegen.make
        declared_verbs = {verb.name for verb in make_config.verbs}
        lock_paths = (serialization.single_flight_lock_path, serialization.lock_path)

        tm.that(len(set(lock_paths)), eq=len(lock_paths))
        tm.that(serialization.timeout_seconds, gt=0)
        tm.that(make_config.serialized_verbs, empty=False)
        tm.that(set(make_config.serialized_verbs).issubset(declared_verbs), where=bool)
        for verb in make_config.verbs:
            if verb.transactional:
                tm.that(verb.serialized, eq=True)
                tm.that(verb.apply_guarded, eq=True)
        for lock_path in lock_paths:
            tm.that(not lock_path.is_absolute(), where=bool)
            tm.that(lock_path in serialization.snapshot_excludes, where=bool)
        for excluded_path in serialization.snapshot_excludes:
            tm.that(not excluded_path.is_absolute(), where=bool)

    def test_single_flight_and_mutation_locks_must_be_distinct(self) -> None:
        """The child transaction lock cannot recursively equal the outer lock."""
        serialization = config.Infra.codegen.make.serialization
        payload = serialization.model_dump(mode="python")
        payload["single_flight_lock_path"] = serialization.lock_path

        with pytest.raises(ValueError, match="lock paths must be distinct"):
            m.Infra.MakeSerializationSpec.model_validate(payload)

    def test_every_serialization_lock_must_be_snapshot_excluded(self) -> None:
        """Lock artifacts never invalidate the operation they protect."""
        serialization = config.Infra.codegen.make.serialization
        payload = serialization.model_dump(mode="python")
        payload["snapshot_excludes"] = tuple(
            path
            for path in serialization.snapshot_excludes
            if path != serialization.single_flight_lock_path
        )

        with pytest.raises(ValueError, match="lock paths must be snapshot-excluded"):
            m.Infra.MakeSerializationSpec.model_validate(payload)

    def test_every_serialization_lock_must_be_repository_relative(self) -> None:
        """Every configured lock remains owned by the selected Make engine."""
        serialization = config.Infra.codegen.make.serialization
        payload = serialization.model_dump(mode="python")
        payload["single_flight_lock_path"] = (
            serialization.single_flight_lock_path.resolve()
        )

        with pytest.raises(ValueError, match="lock paths must be repository-relative"):
            m.Infra.MakeSerializationSpec.model_validate(payload)

    @pytest.mark.parametrize("contender_is_mutation", [False, True])
    def test_complete_operation_single_flight(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        contender_is_mutation: bool,
    ) -> None:
        """The single-flight lock spans each complete one-command operation."""
        make_config = config.Infra.codegen.make
        serialization = make_config.serialization
        mutation_verb = _TRANSACTIONAL_VERBS[0]
        check_verb = next(
            verb for verb in make_config.serialized_verbs if verb != mutation_verb
        )
        contender_verb = mutation_verb if contender_is_mutation else check_verb
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            f".PHONY: _serialized_{mutation_verb} _serialized_{check_verb}\n",
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        mutation_entered = Event()
        mutation_release = Event()
        contender_started = Event()
        contender_entered = Event()
        child_lock_acquired = Event()
        primary_order_lock = Lock()
        primary_count = 0
        event_timeout_seconds = 2
        mutation_lock_path = (tmp_path / serialization.lock_path).resolve()

        def controlled_run_make(
            _service_type: type[FlextInfraMakeSerializationService],
            _checkout: Path,
            command: t.StrSequence,
            *,
            failure_context: str,
        ) -> p.Result[m.Infra.ProcessExit]:
            nonlocal primary_count
            tm.that(failure_context, empty=False)
            if f"_serialized_{mutation_verb}" in command:
                with primary_order_lock:
                    primary_count += 1
                    primary_index = primary_count
                if primary_index == 1:

                    def acquire_child_lock() -> p.Result[bool]:
                        child_lock_acquired.set()
                        return r[bool].ok(True)

                    tm.ok(
                        u.Infra.serialization_lock_execute(
                            (mutation_lock_path,),
                            0,
                            acquire_child_lock,
                            timeout_failure=lambda _path, _timeout: r[bool].fail(
                                "child mutation lock remained held by its parent"
                            ),
                            acquisition_failure=lambda error: r[bool].fail(error),
                        )
                    )
                    mutation_entered.set()
                    tm.that(
                        mutation_release.wait(timeout=event_timeout_seconds), where=bool
                    )
                else:
                    contender_entered.set()
            elif f"_serialized_{check_verb}" in command:
                contender_entered.set()
            return r[m.Infra.ProcessExit].ok(
                m.Infra.ProcessExit(
                    exit_code=int(c.Infra.ScriptExitCode.PASS),
                    raw_exit_code=int(c.Infra.ScriptExitCode.PASS),
                    classification="success",
                )
            )

        monkeypatch.setattr(
            FlextInfraMakeSerializationService,
            "_run_make",
            classmethod(controlled_run_make),
        )
        monkeypatch.setenv(make_config.apply_variable, make_config.apply_value)
        mutation_service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": tmp_path,
            "verb": mutation_verb,
            "makefile": makefile,
        })
        contender_service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": tmp_path,
            "verb": contender_verb,
            "makefile": makefile,
        })

        def execute_contender() -> p.Result[m.Infra.ProcessExit]:
            contender_started.set()
            result: p.Result[m.Infra.ProcessExit] = contender_service.execute()
            return result

        with ThreadPoolExecutor(max_workers=2) as executor:
            mutation_future = executor.submit(mutation_service.execute)
            tm.that(mutation_entered.wait(timeout=event_timeout_seconds), where=bool)
            tm.that(child_lock_acquired.wait(timeout=event_timeout_seconds), where=bool)
            contender_future = executor.submit(execute_contender)
            tm.that(contender_started.wait(timeout=event_timeout_seconds), where=bool)
            try:
                tm.that(contender_entered.wait(timeout=0.5), eq=False)
                mutation_release.set()
            finally:
                mutation_release.set()
            mutation_result = mutation_future.result(timeout=event_timeout_seconds)
            contender_result = contender_future.result(timeout=event_timeout_seconds)

        tm.ok(mutation_result)
        tm.ok(contender_result)
        tm.that(contender_entered.is_set(), where=bool)

    def test_operation_oserror_is_not_classified_as_lock_acquisition(
        self, tmp_path: Path
    ) -> None:
        """Only lock acquisition errors reach the acquisition failure callback."""
        serialization = config.Infra.codegen.make.serialization
        lock_path = tmp_path / serialization.lock_path
        lock_path.parent.mkdir(parents=True)
        acquisition_failures: list[str] = []
        operation_error = "protected operation failed"

        def operation() -> p.Result[bool]:
            raise OSError(operation_error)

        def timeout_failure(
            timed_out_path: Path, timeout_seconds: int
        ) -> p.Result[bool]:
            return r[bool].fail(
                f"{timed_out_path} remained locked for {timeout_seconds}s"
            )

        def acquisition_failure(error: str) -> p.Result[bool]:
            acquisition_failures.append(error)
            return r[bool].fail(error)

        with pytest.raises(OSError, match=operation_error):
            u.Infra.serialization_lock_execute(
                (lock_path,),
                serialization.timeout_seconds,
                operation,
                timeout_failure=timeout_failure,
                acquisition_failure=acquisition_failure,
            )
        tm.that(acquisition_failures, eq=[])

    def test_transactional_verb_requires_apply_guard_and_serialization(self) -> None:
        """A transaction cannot bypass either authorization or single-flight."""
        verb = next(
            item for item in config.Infra.codegen.make.verbs if item.transactional
        )
        payload = verb.model_dump(mode="python")
        payload["serialized"] = False

        with pytest.raises(ValueError, match="must be serialized and APPLY-guarded"):
            m.Infra.MakeVerbSpec.model_validate(payload)

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
        validation_verb = config.Infra.codegen.make.serialized_verbs[0]
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

        executor = ThreadPoolExecutor(max_workers=2)
        try:
            incumbent_future = executor.submit(
                u.Cli.run_raw, [*command, validation_verb], tmp_path
            )
            contender_future = None
            release = tmp_path / ".reports" / "serialization-test" / "incumbent-release"
            try:
                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (
                        tmp_path
                        / ".reports"
                        / "serialization-test"
                        / "incumbent-started"
                    ).exists()
                    and not incumbent_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that(
                    (
                        tmp_path
                        / ".reports"
                        / "serialization-test"
                        / "incumbent-started"
                    ).exists(),
                    where=bool,
                )
                contender_future = executor.submit(
                    u.Cli.run_raw, [*command, validation_verb], tmp_path
                )
                release.write_text("", encoding="utf-8")
                incumbent_process = tm.ok(
                    incumbent_future.result(timeout=self._process_start_timeout_seconds)
                )
                contender_process = tm.ok(
                    contender_future.result(timeout=self._process_start_timeout_seconds)
                )
            finally:
                release.touch()
                incumbent_future.cancel()
                if contender_future is not None:
                    contender_future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        tm.that(incumbent_process.exit_code, eq=0)
        tm.that(contender_process.exit_code, eq=0)
        tm.that(
            not (tmp_path / ".reports" / "serialization-test" / "overlap").exists(),
            where=bool,
        )
        tm.that(
            (tmp_path / config.Infra.codegen.make.serialization.lock_path).is_file(),
            where=bool,
        )

    def test_external_callers_share_the_selected_make_engine_lock(
        self, tmp_path: Path
    ) -> None:
        """Different callers of one selected Make owner cannot overlap."""
        validation_verb = config.Infra.codegen.make.serialized_verbs[0]
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

        executor = ThreadPoolExecutor(max_workers=2)
        try:
            incumbent_future = executor.submit(command, callers[0])
            contender_future = None
            release = state / "release"
            try:
                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (state / "started").exists()
                    and not incumbent_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that((state / "started").exists(), where=bool)
                contender_future = executor.submit(command, callers[1])
                release.write_text("", encoding="utf-8")
                incumbent = tm.ok(
                    incumbent_future.result(timeout=self._process_start_timeout_seconds)
                )
                contender = tm.ok(
                    contender_future.result(timeout=self._process_start_timeout_seconds)
                )
            finally:
                release.touch()
                incumbent_future.cancel()
                if contender_future is not None:
                    contender_future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        tm.that(incumbent.exit_code, eq=0)
        tm.that(contender.exit_code, eq=0)
        tm.that(not (state / "overlap").exists(), where=bool)
        tm.that(
            (engine_root / config.Infra.codegen.make.serialization.lock_path).is_file(),
            where=bool,
        )

    def test_private_failure_reaches_cli_and_outer_make(self, tmp_path: Path) -> None:
        """A private nonzero status is never coerced into public success."""
        validation_verb = config.Infra.codegen.make.serialized_verbs[0]
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

        outer_make = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", validation_verb], cwd=tmp_path
            )
        )

        tm.that(outer_make.exit_code, eq=make_failure_exit_code)
        tm.that(outer_make.stdout + outer_make.stderr, has=f"Error {private_exit_code}")
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
                    config.Infra.codegen.make.serialized_verbs[0],
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
        validation_verb = config.Infra.codegen.make.serialized_verbs[0]
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

    @pytest.mark.parametrize("mutation_verb", _TRANSACTIONAL_VERBS)
    def test_transactional_mutation_runs_one_internal_command_without_what(
        self, tmp_path: Path, mutation_verb: str
    ) -> None:
        """A transaction transports APPLY once and derives its handler internally."""
        make_config = config.Infra.codegen.make
        invocations = tmp_path / "invocations.txt"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@test "$({make_config.apply_variable})" = '
                f'"{make_config.apply_value}"\n'
                f'\t@test -z "$${{{c.Infra.WORKTREE_TRANSACTION_ENV}}}"\n'
                f"\t@printf 'run\\n' >> {invocations}\n"
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
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(invocations.read_text(encoding="utf-8").splitlines(), eq=["run"])
        with FileLock(tmp_path / make_config.serialization.lock_path, timeout=0):
            pass

