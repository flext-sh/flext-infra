"""In-process contract for per-checkout Make validation serialization.

Unit scope: typed SSOT validation, lock-callback classification, fingerprint
semantics, and single-flight ordering — all observable without leaving this
process. The cross-process guarantee (two real CLI processes sharing one
native lock) lives in
``tests/integration/make_serialization_processes_tests.py``.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock

import pytest

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


@pytest.mark.xdist_group("make-single-flight")
class TestsFlextInfraMakeSerialization:
    """Prove the serialization service honors its typed configuration."""

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
