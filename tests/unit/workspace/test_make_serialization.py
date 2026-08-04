"""Real-process contract for per-checkout Make validation serialization."""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock

import pytest
from filelock import FileLock, Timeout

from flext_core import r
from flext_infra import c, config, m, p, t, u
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_tests import tm
from tests import u as test_u

# Derived from the handler SSOT: a serialized mutation runs the verb's
# apply selector, then re-checks itself with the read-only default.
_MUTATION_CASES = tuple(
    (verb.name, verb.apply_what, verb.default_what)
    for verb in config.Infra.codegen.make.verbs
    if verb.name in config.Infra.codegen.make.serialization.mutation_verbs
)


class TestsFlextInfraMakeSerialization:
    """Prove configured Make verbs share one native checkout lock."""

    _process_start_timeout_seconds = 30

    def test_config_owns_relative_checkout_lock_and_serialized_verbs(self) -> None:
        """The typed SSOT owns path, timeout, and the exact protected verbs."""
        serialization = config.Infra.codegen.make.serialization
        declared_verbs = {verb.name for verb in config.Infra.codegen.make.verbs}
        lock_paths = (serialization.single_flight_lock_path, serialization.lock_path)

        tm.that(len(set(lock_paths)), eq=len(lock_paths))
        tm.that(serialization.timeout_seconds, gt=0)
        tm.that(serialization.verbs, empty=False)
        tm.that(set(serialization.verbs).issubset(declared_verbs), where=bool)
        # Every serialized mutation verb is itself serialized and apply-guarded,
        # so its apply and read-only selectors both come from the handler SSOT.
        for verb_name, mutation_what, fixed_point_what in _MUTATION_CASES:
            tm.that(verb_name in serialization.verbs, where=bool)
            tm.that(mutation_what, empty=False)
            tm.that(fixed_point_what, empty=False)
        for lock_path in lock_paths:
            tm.that(not lock_path.is_absolute(), where=bool)
            tm.that(lock_path in serialization.snapshot_excludes, where=bool)
        for excluded_path in serialization.snapshot_excludes:
            tm.that(not excluded_path.is_absolute(), where=bool)

    def test_accepts_apply_allows_apply_token_without_mutation_verbs(self) -> None:
        """Test accepts_apply so WHAT=cache-clear APPLY=Y is legal and non-mutating."""
        make = config.Infra.codegen.make
        test_verb = next(verb for verb in make.verbs if verb.name == "test")
        tm.that(test_verb.accepts_apply, eq=True)
        tm.that(test_verb.apply_guarded, eq=False)
        tm.that("test" in make.serialization.mutation_verbs, eq=False)
        service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": Path.cwd(),
            "verb": "test",
            "makefile": Path.cwd() / c.Infra.MAKEFILE_FILENAME,
            "selector_value": "cache-clear",
            "apply_token": make.apply_value,
        })
        tm.that(service.selector_value, eq="cache-clear")
        tm.that(service.apply_token, eq=make.apply_value)

    def test_mutation_verbs_equal_apply_guarded_public_verbs(self) -> None:
        """Config SSOT must keep mutation_verbs == apply_guarded verb names.

        A drift here fails closed on every flext_infra import (including ai-hub
        CLI when PYTHONPATH points at this checkout).
        """
        make = config.Infra.codegen.make
        mutation = set(make.serialization.mutation_verbs)
        guarded = {verb.name for verb in make.verbs if verb.apply_guarded}
        tm.that(mutation, eq=guarded)
        tm.that(mutation.issubset(set(make.serialization.verbs)), where=bool)

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

    @pytest.mark.parametrize(
        "contender_is_mutation", [False, True], ids=("check", "mutation")
    )
    def test_complete_operation_single_flight(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        contender_is_mutation: bool,
    ) -> None:
        """Checks and mutations wait through both mutation phases."""
        make_config = config.Infra.codegen.make
        serialization = make_config.serialization
        mutation_verb, mutation_what, fixed_point_what = _MUTATION_CASES[0]
        check_verb = next(verb for verb in serialization.verbs if verb != mutation_verb)
        contender_verb = mutation_verb if contender_is_mutation else check_verb
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            f".PHONY: _serialized_{mutation_verb} _serialized_{check_verb}\n",
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        mutation_entered = Event()
        mutation_release = Event()
        fixed_point_entered = Event()
        fixed_point_release = Event()
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
            run_context: str,
        ) -> p.Result[m.Infra.ProcessExit]:
            nonlocal primary_count
            tm.that(run_context, empty=False)
            tm.that(run_context, has="serialized Make")
            if " failed" in run_context or run_context.endswith("failed"):
                message = f"run_context must stay neutral: {run_context}"
                raise AssertionError(message)
            apply_marker = f"{make_config.apply_variable}={make_config.apply_value}"
            is_apply = apply_marker in command
            is_mutation_target = f"_serialized_{mutation_verb}" in command
            is_fixed_point = (
                is_mutation_target
                and f"{make_config.selector}={fixed_point_what}" in command
                and not is_apply
            )
            if is_mutation_target and is_apply:
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
            elif is_fixed_point:
                fixed_point_entered.set()
                tm.that(
                    fixed_point_release.wait(timeout=event_timeout_seconds), where=bool
                )
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
        mutation_service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": tmp_path,
            "verb": mutation_verb,
            "makefile": makefile,
            "selector_value": mutation_what,
            "apply_token": make_config.apply_value,
        })
        contender_payload: dict[str, object] = {
            "workspace_root": tmp_path,
            "verb": contender_verb,
            "makefile": makefile,
        }
        if contender_is_mutation:
            contender_payload["selector_value"] = mutation_what
            contender_payload["apply_token"] = make_config.apply_value
        contender_service = FlextInfraMakeSerializationService.model_validate(
            contender_payload
        )

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
                tm.that(
                    fixed_point_entered.wait(timeout=event_timeout_seconds), where=bool
                )
                tm.that(contender_entered.wait(timeout=0.5), eq=False)
            finally:
                mutation_release.set()
                fixed_point_release.set()
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

    def test_mutation_verbs_must_be_serialized(self) -> None:
        """A mutating verb outside the serialized set is rejected."""
        serialization = config.Infra.codegen.make.serialization
        payload = serialization.model_dump(mode="python")
        unserialized = next(
            verb.name
            for verb in config.Infra.codegen.make.verbs
            if verb.name not in serialization.verbs
        )
        payload["mutation_verbs"] = [*serialization.mutation_verbs, unserialized]

        with pytest.raises(
            ValueError, match="make serialization mutation verbs are not serialized"
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
        tm.that(
            fixed_point_what,
            eq=next(
                verb.default_what
                for verb in make_config.verbs
                if verb.name == mutation_verb
            ),
        )
        projection = tmp_path / "generated.txt"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.apply_variable})" = '
                f'"{make_config.apply_value}" ]; then '
                f"printf 'generated\\n' > {projection}; "
                f"else "
                f'[ "$({make_config.apply_variable})" != '
                f'"{make_config.apply_value}" ] || exit 9; '
                "fi\n"
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
                    "--selector-value",
                    mutation_what,
                    "--apply-token",
                    make_config.apply_value,
                ],
                cwd=tmp_path,
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(projection.read_text(encoding="utf-8"), eq="generated\n")

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_transaction_owned_mutation_avoids_nested_lock_and_locks_fixed_point(
        self,
        tmp_path: Path,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """The child owns apply serialization before Make locks the fixed point."""
        make_config = config.Infra.codegen.make
        tm.that(
            fixed_point_what,
            eq=next(
                verb.default_what
                for verb in make_config.verbs
                if verb.name == mutation_verb
            ),
        )
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
                f'\t@if [ "$({make_config.apply_variable})" = '
                f'"{make_config.apply_value}" ]; then '
                f"{sys.executable} {worker} {state} mutation; "
                f"else "
                f"{sys.executable} {worker} {state} fixed-point; "
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
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            state.mkdir(parents=True, exist_ok=True)
            mutation_future = executor.submit(
                u.Cli.run_raw,
                [
                    *command,
                    mutation_verb,
                    "--selector-value",
                    mutation_what,
                    "--apply-token",
                    make_config.apply_value,
                ],
                tmp_path,
            )
            try:
                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (state / "mutation-started").exists()
                    and not mutation_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that((state / "mutation-started").exists(), where=bool)
                mutation_lock_available = False
                try:
                    with FileLock(lock_path, timeout=0):
                        mutation_lock_available = True
                except Timeout:
                    mutation_lock_available = False
                tm.that(mutation_lock_available, where=bool)
                (state / "mutation-release").write_text("", encoding="utf-8")

                deadline = time.monotonic() + self._process_start_timeout_seconds
                while (
                    not (state / "fixed-point-started").exists()
                    and not mutation_future.done()
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                tm.that((state / "fixed-point-started").exists(), where=bool)
                fixed_point_lock_held = False
                try:
                    with FileLock(lock_path, timeout=0):
                        pass
                except Timeout:
                    fixed_point_lock_held = True
                tm.that(fixed_point_lock_held, where=bool)
                (state / "fixed-point-release").write_text("", encoding="utf-8")
                mutation = tm.ok(
                    mutation_future.result(timeout=self._process_start_timeout_seconds)
                )
            finally:
                (state / "mutation-release").touch()
                (state / "fixed-point-release").touch()
                mutation_future.cancel()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

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

    @pytest.mark.parametrize(
        ("mutation_verb", "mutation_what", "fixed_point_what"), _MUTATION_CASES
    )
    def test_transaction_to_fixed_point_lock_gap_fails_closed_on_drift(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        mutation_verb: str,
        mutation_what: str,
        fixed_point_what: str,
    ) -> None:
        """Reject drift after transaction apply and before fixed-point lock entry."""
        make_config = config.Infra.codegen.make
        projection = tmp_path / "projection.txt"
        makefile = tmp_path / c.Infra.MAKEFILE_FILENAME
        makefile.write_text(
            (
                f".PHONY: _serialized_{mutation_verb}\n"
                f"_serialized_{mutation_verb}:\n"
                f'\t@if [ "$({make_config.selector})" = "{mutation_what}" ]; then '
                f"printf 'generated\\n' > {projection}; "
                f'elif [ "$({make_config.selector})" = "{fixed_point_what}" ]; then '
                ":; else exit 8; fi\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        lock_path = tmp_path / make_config.serialization.lock_path
        post_transaction_captured = Event()
        original_fingerprint = u.Infra.workspace_fingerprint
        fingerprint_calls = 0

        def observed_fingerprint(
            checkout: Path, *, excluded_paths: t.SequenceOf[Path] = ()
        ) -> p.Result[m.Infra.WorkspaceFingerprint]:
            nonlocal fingerprint_calls
            result = original_fingerprint(checkout, excluded_paths=excluded_paths)
            fingerprint_calls += 1
            if fingerprint_calls == 1:
                post_transaction_captured.set()
            return result

        monkeypatch.setattr(u.Infra, "workspace_fingerprint", observed_fingerprint)
        service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": tmp_path,
            "verb": mutation_verb,
            "makefile": makefile,
            "selector_value": mutation_what,
            "apply_token": make_config.apply_value,
        })

        incumbent_lock = FileLock(
            lock_path, timeout=0, fallback_to_soft=False, preserve_lock_file=True
        )
        incumbent_lock.acquire()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                execution_future = executor.submit(service.execute)
                try:
                    tm.that(post_transaction_captured.wait(timeout=8), where=bool)
                    (tmp_path / "concurrent.txt").write_text(
                        "drift\n", encoding="utf-8"
                    )
                    incumbent_lock.release()
                    result = execution_future.result(timeout=8)
                finally:
                    incumbent_lock.release()
                    execution_future.cancel()
        finally:
            incumbent_lock.release()

        tm.fail(
            result,
            has="workspace changed between transaction apply and fixed-point lock",
        )
