"""Portable per-checkout serialization for state-sensitive Make validation."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Annotated, override

from flext_core import r

from flext_infra import c, config, m, p, t, u
from flext_infra.base import s
from flext_infra.workspace.serialization_lock import FlextInfraSerializationLockOwner


class FlextInfraMakeSerializationService(s[m.Infra.ProcessExit]):
    """Run one configured private Make target under a native process lock."""

    verb: Annotated[
        str, m.Field(description="Configured public Make verb to serialize")
    ]
    makefile: Annotated[
        Path,
        m.Field(
            description=(
                "Selected Make owner used for nested dispatch and lock ownership"
            )
        ),
    ]

    @classmethod
    def _process_failure(
        cls, raw_exit_code: int, message: str
    ) -> p.Result[m.Infra.ProcessExit]:
        """Return one typed failure whose CLI boundary preserves process status."""
        outcome = m.Infra.ProcessExit(
            exit_code=u.Infra.normalize_process_exit_code(raw_exit_code),
            raw_exit_code=raw_exit_code,
            classification=u.Infra.classify_process_exit(raw_exit_code),
        )
        return r[m.Infra.ProcessExit].fail(
            message, error_code=c.Infra.PROCESS_EXIT_ERROR_CODE, error_data=outcome
        )

    @staticmethod
    def _success_exit() -> m.Infra.ProcessExit:
        """Build the canonical successful process outcome."""
        return m.Infra.ProcessExit(
            exit_code=int(c.Infra.ScriptExitCode.PASS),
            raw_exit_code=int(c.Infra.ScriptExitCode.PASS),
            classification="success",
        )

    @classmethod
    def _run_make(
        cls,
        checkout: Path,
        command: t.StrSequence,
        *,
        failure_context: str,
        deadline: p.Cli.ProcessDeadline | None = None,
    ) -> p.Result[m.Infra.ProcessExit]:
        """Run one private Make phase and retain its process semantics."""
        log_path: Path | None = None
        if deadline is None:
            raw_result = u.Cli.run_raw(list(command), cwd=checkout, capture=False)
            if raw_result.failure:
                return cls._process_failure(
                    int(c.Infra.ScriptExitCode.INFRA),
                    raw_result.error or failure_context,
                )
            raw_exit_code = raw_result.value.exit_code
        else:
            log_path = u.Cli.resolve_report_path(
                checkout,
                c.Infra.RK_WORKSPACE,
                "test",
                "serialized-make.log",
            )
            result = u.Cli.run_to_file(
                command,
                log_path,
                cwd=checkout,
                env={c.Infra.TEST_DEADLINE_OWNER_ENV: "1"},
                live=True,
                deadline=deadline,
            )
            if result.failure:
                exit_code = (
                    deadline.timeout_exit_code
                    if time.monotonic()
                    >= (
                        deadline.expires_at_monotonic
                        - deadline.termination_grace_seconds
                    )
                    else int(c.Infra.ScriptExitCode.INFRA)
                )
                return cls._process_failure(
                    exit_code, result.error or failure_context
                )
            raw_exit_code = result.value
            if raw_exit_code != 0:
                child_exit = u.Infra.extract_make_child_exit_code(log_path)
                if child_exit is not None:
                    raw_exit_code = child_exit
        if raw_exit_code != 0:
            outcome = m.Infra.ProcessExit(
                exit_code=u.Infra.normalize_process_exit_code(raw_exit_code),
                raw_exit_code=raw_exit_code,
                classification=u.Infra.classify_process_exit(raw_exit_code),
            )
            return r[m.Infra.ProcessExit].fail(
                (
                    f"{failure_context} "
                    f"({outcome.classification}, exit={outcome.exit_code})"
                ),
                error_code=c.Infra.PROCESS_EXIT_ERROR_CODE,
                error_data=outcome,
            )
        return r[m.Infra.ProcessExit].ok(cls._success_exit())

    @staticmethod
    def _capture_fingerprint(
        checkout: Path, serialization: m.Infra.MakeSerializationSpec, *, phase: str
    ) -> p.Result[m.Infra.WorkspaceFingerprint]:
        """Capture one checkout snapshot with phase-specific diagnostics."""
        result = u.Infra.workspace_fingerprint(
            checkout, excluded_paths=serialization.snapshot_excludes
        )
        if result.failure:
            return r[m.Infra.WorkspaceFingerprint].fail(
                result.error or f"failed to fingerprint workspace {phase}"
            )
        return result

    @staticmethod
    def _changed_paths(
        before: m.Infra.WorkspaceFingerprint, after: m.Infra.WorkspaceFingerprint
    ) -> str | None:
        """Render changed paths when two snapshots differ."""
        if before.digest == after.digest:
            return None
        paths = u.Infra.workspace_fingerprint_changes(before, after)
        return ", ".join(paths) or "HEAD/index"

    @classmethod
    def _deadline_failure_if_exhausted(
        cls, deadline: p.Cli.ProcessDeadline | None, *, phase: str
    ) -> p.Result[m.Infra.ProcessExit] | None:
        """Fail before another phase when the shared absolute budget is gone."""
        if deadline is None or time.monotonic() < deadline.expires_at_monotonic:
            return None
        return cls._process_failure(
            deadline.timeout_exit_code,
            f"test deadline exhausted {phase}",
        )

    def _execute_locked(
        self,
        checkout: Path,
        serialization: m.Infra.MakeSerializationSpec,
        *,
        makefile: Path,
        deadline: p.Cli.ProcessDeadline | None = None,
    ) -> p.Result[m.Infra.ProcessExit]:
        """Run one read-only validation and reject any checkout mutation."""
        before_result = self._capture_fingerprint(
            checkout, serialization, phase="before serialized Make"
        )
        if before_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                before_result.error
                or "failed to fingerprint workspace before serialized Make",
            )
        if expired := self._deadline_failure_if_exhausted(
            deadline, phase="during the pre-run fingerprint"
        ):
            return expired
        primary = self._run_make(
            checkout,
            (
                c.Infra.MAKE,
                "--no-print-directory",
                "-f",
                str(makefile),
                f"_serialized_{self.verb}",
            ),
            failure_context=f"serialized Make {self.verb} failed",
            deadline=deadline,
        )
        if primary.failure:
            return primary
        if expired := self._deadline_failure_if_exhausted(
            deadline, phase="before the post-run fingerprint"
        ):
            return expired
        after_result = self._capture_fingerprint(
            checkout, serialization, phase="after serialized Make"
        )
        if after_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                after_result.error
                or "failed to fingerprint workspace after serialized Make",
            )
        if expired := self._deadline_failure_if_exhausted(
            deadline, phase="during the post-run fingerprint"
        ):
            return expired
        after = after_result.value
        changed_paths = self._changed_paths(before_result.value, after)
        if changed_paths is not None:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"workspace changed during serialized Make {self.verb}: "
                f"{changed_paths}",
            )
        if (
            deadline is not None
            and time.monotonic() >= deadline.expires_at_monotonic
        ):
            return self._process_failure(
                deadline.timeout_exit_code,
                f"serialized Make {self.verb} exhausted its absolute deadline",
            )
        return primary

    @staticmethod
    def _test_deadline() -> m.Cli.ProcessDeadline:
        """Create the one absolute wall shared by the complete test lifecycle."""
        policy = config.Infra.tooling.tools.pytest
        return m.Cli.ProcessDeadline(
            expires_at_monotonic=time.monotonic() + policy.run_timeout_seconds,
            termination_grace_seconds=policy.termination_grace_seconds,
            timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
        )

    @classmethod
    def _remaining_lock_timeout(
        cls,
        deadline: p.Cli.ProcessDeadline | None,
        configured_timeout_seconds: int,
    ) -> p.Result[int]:
        """Reserve termination grace while bounding lock acquisition."""
        if deadline is None:
            return r[int].ok(configured_timeout_seconds)
        remaining = (
            deadline.expires_at_monotonic
            - time.monotonic()
            - deadline.termination_grace_seconds
        )
        if remaining <= 0:
            return r[int].fail("test deadline exhausted before lock acquisition")
        return r[int].ok(
            min(configured_timeout_seconds, max(0, int(remaining)))
        )

    def _execute_transaction_owned_mutation(
        self,
        checkout: Path,
        make_config: m.Infra.MakeSpec,
        serialization: m.Infra.MakeSerializationSpec,
        *,
        fixed_point_what: str,
        makefile: Path,
        lock_path: Path,
    ) -> p.Result[m.Infra.ProcessExit]:
        """Let the child transaction own apply locks, then lock the fixed point."""
        primary = self._run_make(
            checkout,
            (
                c.Infra.MAKE,
                "--no-print-directory",
                "-f",
                str(makefile),
                f"_serialized_{self.verb}",
            ),
            failure_context=f"serialized Make {self.verb} failed",
        )
        if primary.failure:
            return primary
        post_transaction_result = self._capture_fingerprint(
            checkout, serialization, phase="after transaction-owned mutation"
        )
        if post_transaction_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                post_transaction_result.error
                or "failed to fingerprint workspace after transaction-owned mutation",
            )
        post_transaction = post_transaction_result.value

        def locked_fixed_point() -> p.Result[m.Infra.ProcessExit]:
            locked_start_result = self._capture_fingerprint(
                checkout, serialization, phase="before locked fixed-point check"
            )
            if locked_start_result.failure:
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.INFRA),
                    locked_start_result.error
                    or "failed to fingerprint workspace before fixed-point check",
                )
            locked_start = locked_start_result.value
            changed_paths = self._changed_paths(post_transaction, locked_start)
            if changed_paths is not None:
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.INFRA),
                    "workspace changed between transaction apply and fixed-point "
                    f"lock: {changed_paths}",
                )
            fixed_point = self._run_make(
                checkout,
                (
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "-f",
                    str(makefile),
                    f"_serialized_{self.verb}",
                    f"{make_config.selector}={fixed_point_what}",
                    f"{make_config.apply_variable}=",
                ),
                failure_context=(
                    f"serialized Make {self.verb} fixed-point "
                    f"{make_config.selector}={fixed_point_what} failed"
                ),
            )
            if fixed_point.failure:
                return fixed_point
            fixed_after_result = self._capture_fingerprint(
                checkout, serialization, phase="after fixed-point check"
            )
            if fixed_after_result.failure:
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.INFRA),
                    fixed_after_result.error
                    or "failed to fingerprint workspace after fixed-point check",
                )
            changed_paths = self._changed_paths(locked_start, fixed_after_result.value)
            if changed_paths is not None:
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.INFRA),
                    (
                        f"serialized Make {self.verb} fixed-point "
                        f"{make_config.selector}={fixed_point_what} changed workspace: "
                        f"{changed_paths}"
                    ),
                )
            return primary

        return FlextInfraSerializationLockOwner.execute(
            (lock_path,),
            serialization.timeout_seconds,
            locked_fixed_point,
            timeout_failure=self._lock_timeout_failure,
            acquisition_failure=self._lock_acquisition_failure,
        )

    @classmethod
    def _lock_timeout_failure(
        cls, lock_path: Path, timeout_seconds: int
    ) -> p.Result[m.Infra.ProcessExit]:
        """Preserve portable timeout process semantics at the CLI boundary."""
        return cls._process_failure(
            c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
            (
                "Timed out waiting for Make validation lock "
                f"'{lock_path}' after {timeout_seconds}s"
            ),
        )

    @classmethod
    def _lock_acquisition_failure(cls, error: str) -> p.Result[m.Infra.ProcessExit]:
        """Preserve infrastructure process semantics for native lock failures."""
        return cls._process_failure(
            int(c.Infra.ScriptExitCode.INFRA),
            f"Make validation lock acquisition failed: {error}",
        )

    @override
    def execute(self) -> p.Result[m.Infra.ProcessExit]:
        """Acquire the checkout lock, then stream the private Make dispatch."""
        serialization = config.Infra.codegen.make.serialization
        make_config = config.Infra.codegen.make
        if self.verb not in serialization.verbs:
            allowed = ", ".join(serialization.verbs)
            return r[m.Infra.ProcessExit].fail(
                f"Make verb '{self.verb}' is not serialized (allowed: {allowed})"
            )
        selected_what = os.environ.get(make_config.selector, "").strip()
        fixed_point_what = serialization.mutation_fixed_points.get(self.verb, {}).get(
            selected_what
        )
        if (
            fixed_point_what is not None
            and os.environ.get(make_config.apply_variable) != make_config.apply_value
        ):
            return r[m.Infra.ProcessExit].fail(
                f"Serialized mutation {self.verb} "
                f"{make_config.selector}={selected_what} requires "
                f"{make_config.apply_variable}={make_config.apply_value}"
            )

        checkout = self.root.resolve()
        deadline = self._test_deadline() if self.verb == "test" else None
        lock_timeout = self._remaining_lock_timeout(
            deadline, serialization.timeout_seconds
        )
        if lock_timeout.failure:
            return self._process_failure(
                c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                lock_timeout.error or "test deadline exhausted before lock acquisition",
            )
        selected_makefile = self.makefile.resolve()
        if not selected_makefile.is_file():
            return r[m.Infra.ProcessExit].fail(
                f"Selected Make owner does not exist: {selected_makefile}"
            )
        engine_root = selected_makefile.parent
        lock_path = (engine_root / serialization.lock_path).resolve()
        try:
            lock_path.relative_to(engine_root)
        except ValueError:
            return r[m.Infra.ProcessExit].fail(
                f"Make serialization lock escapes selected Make owner: {lock_path}"
            )

        if fixed_point_what is not None:
            return self._execute_transaction_owned_mutation(
                checkout,
                make_config,
                serialization,
                fixed_point_what=fixed_point_what,
                makefile=selected_makefile,
                lock_path=lock_path,
            )
        return FlextInfraSerializationLockOwner.execute(
            (lock_path,),
            lock_timeout.value,
            lambda: self._execute_locked(
                checkout,
                serialization,
                makefile=selected_makefile,
                deadline=deadline,
            ),
            timeout_failure=self._lock_timeout_failure,
            acquisition_failure=self._lock_acquisition_failure,
        )


__all__: list[str] = ["FlextInfraMakeSerializationService"]
