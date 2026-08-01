"""Portable per-checkout serialization for state-sensitive Make validation."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

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
    selector_value: Annotated[
        str | None,
        m.Field(
            description="Explicit caller selector; absent resolves from the registry"
        ),
    ] = None
    apply_token: Annotated[
        str | None,
        m.Field(description="Caller mutation token validated against typed config"),
    ] = None

    def _serialized_command(
        self,
        makefile: Path,
        make_config: m.Infra.MakeSpec,
        *,
        selected_what: str,
        apply_value: str,
    ) -> t.StrSequence:
        """Build the nested command with validated public Make variables."""
        return (
            c.Infra.MAKE,
            "--no-print-directory",
            "-f",
            str(makefile),
            f"_serialized_{self.verb}",
            *((f"{make_config.selector}={selected_what}",) if selected_what else ()),
            *((f"{make_config.apply_variable}={apply_value}",) if apply_value else ()),
        )

    def _make_variables(self, make_config: m.Infra.MakeSpec) -> p.Result[t.StrMapping]:
        """Resolve one caller request from the canonical verb matrix."""
        verb_spec = next(
            (item for item in make_config.verbs if item.name == self.verb), None
        )
        if verb_spec is None:
            return r[t.StrMapping].fail(f"unknown Make verb: {self.verb}")
        applying = self.apply_token not in {None, "", make_config.apply_absent_value}
        if applying and self.apply_token != make_config.apply_value:
            return r[t.StrMapping].fail(
                f"{make_config.apply_variable} must be "
                f"{make_config.apply_value} when set"
            )
        selected_what = self.selector_value or verb_spec.default_what
        if selected_what not in verb_spec.handlers:
            allowed = ", ".join(verb_spec.handlers)
            return r[t.StrMapping].fail(
                f"unsupported {self.verb} {make_config.selector}={selected_what} "
                f"(allowed: {allowed})"
            )
        handler = verb_spec.handlers[selected_what]
        if applying and not handler.mutating:
            return r[t.StrMapping].fail(
                f"Make verb '{self.verb}' {make_config.selector}={selected_what} "
                f"is read-only and does not accept {make_config.apply_variable}"
            )
        return r[t.StrMapping].ok({
            make_config.selector: selected_what,
            make_config.apply_variable: self.apply_token or "",
        })

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
        serialization: m.Infra.MakeSerializationSpec,
        make_config: m.Infra.MakeSpec,
        make_variables: t.StrMapping,
        *,
        makefile: Path,
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
        primary = self._run_make(
            checkout,
            self._serialized_command(
                makefile,
                make_config,
                selected_what=make_variables.get(make_config.selector, ""),
                apply_value=make_variables.get(make_config.apply_variable, ""),
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
        if changed_paths is not None:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"workspace changed during serialized Make {self.verb}: "
                f"{changed_paths}",
            )
        return primary

    def _execute_mutation_once(
        self,
        checkout: Path,
        make_config: m.Infra.MakeSpec,
        make_variables: t.StrMapping,
        *,
        makefile: Path,
    ) -> p.Result[m.Infra.ProcessExit]:
        """Run one mutation; the enclosing single-flight lock owns serialization."""
        return self._run_make(
            checkout,
            self._serialized_command(
                makefile,
                make_config,
                selected_what=make_variables.get(make_config.selector, ""),
                apply_value=make_variables.get(make_config.apply_variable, ""),
            ),
            failure_context=f"serialized Make {self.verb} failed",
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
        """Single-flight the complete operation while retaining mutation locks."""
        serialization = config.Infra.codegen.make.serialization
        make_config = config.Infra.codegen.make
        if self.verb not in make_config.serialized_verbs:
            allowed = ", ".join(make_config.serialized_verbs)
            return r[m.Infra.ProcessExit].fail(
                f"Make verb '{self.verb}' is not serialized (allowed: {allowed})"
            )
        make_variables_result = self._make_variables(make_config)
        if make_variables_result.failure:
            return r[m.Infra.ProcessExit].fail(
                make_variables_result.error or "invalid GNU Make variables"
            )
        make_variables = make_variables_result.value
        verb_spec = next(item for item in make_config.verbs if item.name == self.verb)
        selected_what = make_variables[make_config.selector]
        is_mutation = (
            verb_spec.handlers[selected_what].mutating
            and make_variables.get(make_config.apply_variable)
            == make_config.apply_value
        )

        checkout = self.root.resolve()
        selected_makefile = self.makefile.resolve()
        if not selected_makefile.is_file():
            return r[m.Infra.ProcessExit].fail(
                f"Selected Make owner does not exist: {selected_makefile}"
            )
        engine_root = selected_makefile.parent
        mutation_lock_path = (engine_root / serialization.lock_path).resolve()
        single_flight_lock_path = (
            engine_root / serialization.single_flight_lock_path
        ).resolve()
        for lock_path in (single_flight_lock_path, mutation_lock_path):
            try:
                lock_path.relative_to(engine_root)
            except ValueError:
                return r[m.Infra.ProcessExit].fail(
                    f"Make serialization lock escapes selected Make owner: {lock_path}"
                )

        def complete_operation() -> p.Result[m.Infra.ProcessExit]:
            if is_mutation:
                return self._execute_mutation_once(
                    checkout, make_config, make_variables, makefile=selected_makefile
                )
            return u.Infra.serialization_lock_execute(
                (mutation_lock_path,),
                serialization.timeout_seconds,
                lambda: self._execute_locked(
                    checkout,
                    serialization,
                    make_config,
                    make_variables,
                    makefile=selected_makefile,
                ),
                timeout_failure=self._lock_timeout_failure,
                acquisition_failure=self._lock_acquisition_failure,
            )

        return u.Infra.serialization_lock_execute(
            (single_flight_lock_path,),
            serialization.timeout_seconds,
            complete_operation,
            timeout_failure=self._lock_timeout_failure,
            acquisition_failure=self._lock_acquisition_failure,
        )


__all__: list[str] = ["FlextInfraMakeSerializationService"]
