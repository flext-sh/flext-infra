"""Portable per-checkout serialization for state-sensitive Make validation."""

from __future__ import annotations

from typing import Annotated, override

from filelock import FileLock, Timeout
from flext_core import r

from flext_infra import c, config, m, p, u
from flext_infra.base import s


class FlextInfraMakeSerializationService(s[m.Infra.ProcessExit]):
    """Run one configured private Make target under a native process lock."""

    verb: Annotated[
        str, m.Field(description="Configured public Make verb to serialize")
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

    @override
    def execute(self) -> p.Result[m.Infra.ProcessExit]:
        """Acquire the checkout lock, then stream the private Make dispatch."""
        serialization = config.Infra.codegen.make.serialization
        if self.verb not in serialization.verbs:
            allowed = ", ".join(serialization.verbs)
            return r[m.Infra.ProcessExit].fail(
                f"Make verb '{self.verb}' is not serialized (allowed: {allowed})"
            )

        checkout = self.root.resolve()
        lock_path = (checkout / serialization.lock_path).resolve()
        try:
            lock_path.relative_to(checkout)
        except ValueError:
            return r[m.Infra.ProcessExit].fail(
                f"Make serialization lock escapes checkout: {lock_path}"
            )

        try:
            with FileLock(
                lock_path,
                timeout=serialization.timeout_seconds,
                fallback_to_soft=False,
                preserve_lock_file=True,
            ):
                before_result = u.Infra.workspace_fingerprint(
                    checkout, excluded_paths=serialization.snapshot_excludes
                )
                if before_result.failure:
                    return self._process_failure(
                        int(c.Infra.ScriptExitCode.INFRA),
                        before_result.error
                        or "failed to fingerprint workspace before serialized Make",
                    )
                execution_result = u.Cli.run_raw(
                    [c.Infra.MAKE, "--no-print-directory", f"_serialized_{self.verb}"],
                    cwd=checkout,
                    capture=False,
                )
                after_result = u.Infra.workspace_fingerprint(
                    checkout, excluded_paths=serialization.snapshot_excludes
                )
        except Timeout:
            return self._process_failure(
                c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                (
                    "Timed out waiting for Make validation lock "
                    f"'{lock_path}' after {serialization.timeout_seconds}s"
                ),
            )
        except OSError as exc:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"Make validation lock acquisition failed: {exc}",
            )

        if after_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                after_result.error
                or "failed to fingerprint workspace after serialized Make",
            )
        before = before_result.value
        after = after_result.value
        if before.digest != after.digest:
            changed_paths = u.Infra.workspace_fingerprint_changes(before, after)
            rendered_paths = ", ".join(changed_paths) or "HEAD/index"
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                (
                    f"workspace changed during serialized Make {self.verb}: "
                    f"{rendered_paths}"
                ),
            )
        if execution_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                execution_result.error or f"serialized Make {self.verb} failed",
            )
        execution = execution_result.value
        if execution.exit_code != 0:
            outcome = m.Infra.ProcessExit(
                exit_code=u.Infra.normalize_process_exit_code(execution.exit_code),
                raw_exit_code=execution.exit_code,
                classification=u.Infra.classify_process_exit(execution.exit_code),
            )
            return r[m.Infra.ProcessExit].fail(
                (
                    f"serialized Make {self.verb} failed "
                    f"({outcome.classification}, exit={outcome.exit_code})"
                ),
                error_code=c.Infra.PROCESS_EXIT_ERROR_CODE,
                error_data=outcome,
            )
        return r[m.Infra.ProcessExit].ok(
            m.Infra.ProcessExit(
                exit_code=int(c.Infra.ScriptExitCode.PASS),
                raw_exit_code=int(c.Infra.ScriptExitCode.PASS),
                classification="success",
            )
        )


__all__: list[str] = ["FlextInfraMakeSerializationService"]
