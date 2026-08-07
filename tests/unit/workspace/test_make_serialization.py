"""Real-process contract for per-checkout Make validation serialization."""

from __future__ import annotations

import sys
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Lock
from types import TracebackType

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


@dataclass(frozen=True, slots=True)
class _LockBarrier:
    """Handle to one parked serialization run held inside its lock window."""

    release: Event
    future: Future[p.Result[m.Infra.ProcessExit]]
    timeout_seconds: float

    def release_incumbent(self) -> None:
        """Let the parked run finish."""
        self.release.set()

    def result(self) -> p.Result[m.Infra.ProcessExit]:
        """Return the parked run's typed outcome."""
        return self.future.result(timeout=self.timeout_seconds)


class _IncumbentLockWindow:
    """Hold one serialization run inside its locked window for a contender.

    Exemplar for cross-thread contract tests: the incumbent parks at the
    public ``run_raw`` seam, which the service reaches only after acquiring
    every lock. Entry and release are ``Event`` handshakes, so a contender
    observes the locked window deterministically instead of racing a sleep.
    """

    def __init__(
        self, service: FlextInfraMakeSerializationService, timeout_seconds: float
    ) -> None:
        """Store the parked service and the handshake budget."""
        self._service = service
        self._timeout_seconds = timeout_seconds
        self._entered = Event()
        self._release = Event()
        self._monkey = pytest.MonkeyPatch()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future: Future[p.Result[m.Infra.ProcessExit]] | None = None

    def __enter__(self) -> _LockBarrier:
        """Start the run and return once its locks are provably held."""
        original_run_raw = u.Cli.run_raw

        def holding_run_raw(
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            self._entered.set()
            self._release.wait(timeout=self._timeout_seconds)
            return original_run_raw(
                cmd, cwd, timeout, env, remove_env_keys, input_data, capture=capture
            )

        self._monkey.setattr(u.Cli, "run_raw", holding_run_raw)
        self._future = self._executor.submit(self._service.execute)
        tm.that(self._entered.wait(timeout=self._timeout_seconds), where=bool)
        return _LockBarrier(
            release=self._release,
            future=self._future,
            timeout_seconds=self._timeout_seconds,
        )

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        """Release the parked run and restore the patched seam."""
        self._release.set()
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._monkey.undo()


class TestsFlextInfraMakeSerialization:
    """Prove configured Make verbs share one native checkout lock."""

    _process_start_timeout_seconds = 30
    _barrier_timeout_seconds = 10

    @staticmethod
    def _trivial_makefile(
        root: Path, verb: str, name: str = c.Infra.MAKEFILE_FILENAME
    ) -> Path:
        """Write a Make owner whose serialized target is a shell no-op."""
        makefile = root / name
        makefile.write_text(
            f".PHONY: _serialized_{verb}\n_serialized_{verb}:\n\t@:\n", encoding="utf-8"
        )
        return makefile

    @staticmethod
    def _service(
        checkout: Path, verb: str, makefile: Path
    ) -> FlextInfraMakeSerializationService:
        """Build the public serialization service for one checkout."""
        service: FlextInfraMakeSerializationService = (
            FlextInfraMakeSerializationService.model_validate({
                "workspace_root": checkout,
                "verb": verb,
                "makefile": makefile,
            })
        )
        return service

    def _incumbent_holding_lock(
        self, service: FlextInfraMakeSerializationService
    ) -> _IncumbentLockWindow:
        """Return a window in which ``service`` provably holds its locks.

        The incumbent parks inside the public ``run_raw`` seam -- after every
        lock is held and before any work completes -- so a contender observes
        the real locked window. Entry and release are ``Event`` handshakes,
        never sleeps, so the test is deterministic under any scheduler.
        """
        return _IncumbentLockWindow(
            service=service, timeout_seconds=self._barrier_timeout_seconds
        )

    @staticmethod
    def _lock_is_held(lock_path: Path) -> bool:
        """Return whether another owner currently holds ``lock_path``."""
        try:
            with FileLock(lock_path, timeout=0):
                return False
        except Timeout:
            return True

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
        """Given one checkout, when a run holds the lock, no other run may enter.

        Exemplar: mutual exclusion is a property of the service, so the test
        drives ``execute`` in-process and synchronizes on ``Event`` barriers.
        No subprocess, no filesystem sentinel, no sleep -- the contender
        proves the window is closed while the incumbent is provably inside it.
        """
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        makefile = self._trivial_makefile(tmp_path, validation_verb)
        test_u.Tests.initialize_git_repo(tmp_path)
        lock_path = tmp_path / config.Infra.codegen.make.serialization.lock_path
        service = self._service(tmp_path, validation_verb, makefile)

        with self._incumbent_holding_lock(service) as barrier:
            contender_blocked = self._lock_is_held(lock_path)
            barrier.release_incumbent()
            incumbent = tm.ok(barrier.result())

        tm.that(contender_blocked, eq=True)
        tm.that(incumbent.exit_code, eq=0)
        tm.that(lock_path.is_file(), where=bool)

    def test_external_callers_share_the_selected_make_engine_lock(
        self, tmp_path: Path
    ) -> None:
        """Given two callers of one Make owner, the engine root owns the lock.

        Exemplar: lock ownership follows the selected Make owner, never the
        caller's cwd. Asserting real exclusion on the engine lock plus the
        absence of any caller-local lock is the complete contract.
        """
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        engine_root = tmp_path / "engine"
        engine_root.mkdir()
        makefile = self._trivial_makefile(engine_root, validation_verb, "canonical.mk")
        callers = (tmp_path / "caller-a", tmp_path / "caller-b")
        for caller in callers:
            caller.mkdir()
            test_u.Tests.initialize_git_repo(caller)
        lock_relative = config.Infra.codegen.make.serialization.lock_path
        engine_lock = engine_root / lock_relative
        service = self._service(callers[0], validation_verb, makefile)

        with self._incumbent_holding_lock(service) as barrier:
            contender_blocked = self._lock_is_held(engine_lock)
            barrier.release_incumbent()
            incumbent = tm.ok(barrier.result())

        tm.that(contender_blocked, eq=True)
        tm.that(incumbent.exit_code, eq=0)
        tm.that(engine_lock.is_file(), where=bool)
        for caller in callers:
            tm.that((caller / lock_relative).exists(), eq=False)

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
        """Given a writer that ignores the lock, the gate rejects its own run.

        Exemplar: the behavior is "content changed while the gate ran", so the
        test writes that file at the one instant the gate is mid-run -- from
        the public ``run_raw`` seam -- instead of racing a background process
        against a fixed ``sleep``. The drift is therefore guaranteed, not
        probable, and the assertion stays on the reported failure.
        """
        validation_verb = config.Infra.codegen.make.serialization.verbs[0]
        makefile = self._trivial_makefile(tmp_path, validation_verb)
        test_u.Tests.initialize_git_repo(tmp_path)
        drift = tmp_path / "concurrent.txt"
        original_run_raw = u.Cli.run_raw

        def writing_run_raw(
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            outcome = original_run_raw(
                cmd, cwd, timeout, env, remove_env_keys, input_data, capture=capture
            )
            if any(argument.startswith("_serialized_") for argument in cmd):
                drift.write_text("changed", encoding="utf-8")
            return outcome

        monkey = pytest.MonkeyPatch()
        try:
            monkey.setattr(u.Cli, "run_raw", writing_run_raw)
            service = self._service(tmp_path, validation_verb, makefile)
            outcome = service.execute()
        finally:
            monkey.undo()

        tm.fail(
            outcome,
            has=[
                f"workspace changed during serialized Make {validation_verb}",
                drift.name,
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
        """Given an authorized apply, its own projection never counts as drift.

        Exemplar: the observable outcome is the generator's projection plus a
        successful typed result. Driving the service in-process keeps the
        assertion on behavior while a one-line shell recipe stands in for the
        real generator.
        """
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
                f"printf 'generated\\n' > {projection}; fi\n"
            ),
            encoding="utf-8",
        )
        test_u.Tests.initialize_git_repo(tmp_path)
        service = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": tmp_path,
            "verb": mutation_verb,
            "makefile": makefile,
            "selector_value": mutation_what,
            "apply_token": make_config.apply_value,
        })

        outcome = tm.ok(service.execute())

        tm.that(outcome.exit_code, eq=0)
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
        """Given a mutation, apply runs unlocked and the fixed point runs locked.

        Exemplar: the phase order and lock state are recorded by observing the
        service's own dispatch instead of writing sentinels from a spawned
        worker. Each observation captures the selector Make received and
        whether the mutation lock was held at that instant, so the assertion
        is the actual contract: apply is transaction-owned, the fixed-point
        re-check is lock-owned.
        """
        make_config = config.Infra.codegen.make
        tm.that(
            fixed_point_what,
            eq=next(
                verb.default_what
                for verb in make_config.verbs
                if verb.name == mutation_verb
            ),
        )
        makefile = self._trivial_makefile(tmp_path, mutation_verb)
        test_u.Tests.initialize_git_repo(tmp_path)
        lock_path = tmp_path / make_config.serialization.lock_path
        observed: list[tuple[str, bool]] = []
        observed_guard = Lock()
        original_run_raw = u.Cli.run_raw

        def observing_run_raw(
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            selector = next(
                (
                    argument.split("=", 1)[1]
                    for argument in cmd
                    if argument.startswith(f"{make_config.selector}=")
                ),
                "",
            )
            with observed_guard:
                observed.append((selector, self._lock_is_held(lock_path)))
            return original_run_raw(
                cmd, cwd, timeout, env, remove_env_keys, input_data, capture=capture
            )

        monkey = pytest.MonkeyPatch()
        try:
            monkey.setattr(u.Cli, "run_raw", observing_run_raw)
            service = FlextInfraMakeSerializationService.model_validate({
                "workspace_root": tmp_path,
                "verb": mutation_verb,
                "makefile": makefile,
                "selector_value": mutation_what,
                "apply_token": make_config.apply_value,
            })
            outcome = tm.ok(service.execute())
        finally:
            monkey.undo()

        tm.that(outcome.exit_code, eq=0)
        tm.that(
            [selector for selector, _ in observed], eq=[mutation_what, fixed_point_what]
        )
        tm.that(observed[0][1], eq=False)
        tm.that(observed[1][1], eq=True)
        tm.that(self._lock_is_held(lock_path), eq=False)

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
