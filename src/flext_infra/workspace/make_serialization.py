"""Portable per-checkout serialization for state-sensitive Make validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, override

from filelock import FileLock, Timeout
from flext_core import r

from flext_infra import c, config, m, p, t, u
from flext_infra.base import s


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
        cls, checkout: Path, command: t.StrSequence, *, failure_context: str
    ) -> p.Result[m.Infra.ProcessExit]:
        """Run one private Make phase and retain its process semantics."""
        result = u.Cli.run_raw(list(command), cwd=checkout, capture=False)
        if result.failure:
            return cls._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), result.error or failure_context
            )
        output = result.value
        if output.exit_code != 0:
            outcome = m.Infra.ProcessExit(
                exit_code=u.Infra.normalize_process_exit_code(output.exit_code),
                raw_exit_code=output.exit_code,
                classification=u.Infra.classify_process_exit(output.exit_code),
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

    def _execute_locked(
        self,
        checkout: Path,
        make_config: m.Infra.MakeSpec,
        serialization: m.Infra.MakeSerializationSpec,
        *,
        fixed_point_what: str | None,
        makefile: Path,
    ) -> p.Result[m.Infra.ProcessExit]:
        """Run the primary phase and optional fixed point under one lock."""
        before_result = self._capture_fingerprint(
            checkout, serialization, phase="before serialized Make"
        )
        if before_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                before_result.error
                or "failed to fingerprint workspace before serialized Make",
            )
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
        after_result = self._capture_fingerprint(
            checkout, serialization, phase="after serialized Make"
        )
        if after_result.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                after_result.error
                or "failed to fingerprint workspace after serialized Make",
            )
        after = after_result.value
        changed_paths = self._changed_paths(before_result.value, after)
        if changed_paths is not None and fixed_point_what is None:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"workspace changed during serialized Make {self.verb}: "
                f"{changed_paths}",
            )
        if primary.failure:
            return primary
        if fixed_point_what is None:
            return primary

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
        changed_paths = self._changed_paths(after, fixed_after_result.value)
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

        try:
            with FileLock(
                lock_path,
                timeout=serialization.timeout_seconds,
                fallback_to_soft=False,
                preserve_lock_file=True,
            ):
                return self._execute_locked(
                    checkout,
                    make_config,
                    serialization,
                    fixed_point_what=fixed_point_what,
                    makefile=selected_makefile,
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


__all__: list[str] = ["FlextInfraMakeSerializationService"]
