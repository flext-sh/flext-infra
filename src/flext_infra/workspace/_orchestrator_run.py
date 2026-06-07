"""Per-project make execution + go-gate normalization — extracted concern."""

from __future__ import annotations

import time
from pathlib import Path

from flext_infra import c, m, p, r, t, u


class FlextInfraOrchestratorRunMixin:
    """Run a make verb for one project and normalize check-gates for Go projects.

    Composed into FlextInfraOrchestratorService via inheritance; the loop mixin
    resolves ``_run_project`` through ``self`` MRO.
    """

    def _run_project(
        self,
        project: str,
        verb: str,
        _index: int,
        *,
        make_args: t.StrSequence,
    ) -> p.Result[m.Cli.CommandOutput]:
        """Execute make verb for a single project.

        Args:
            project: Project directory name.
            verb: Make verb to execute.
            _index: 1-based project index.
            make_args: Additional make arguments.

        Returns:
            CommandOutput with log path in stdout, exit code, and timing.

        """
        log_path = u.Cli.resolve_report_path(
            Path.cwd(),
            c.Infra.RK_WORKSPACE,
            verb,
            f"{project}.log",
        )
        _ = u.Cli.ensure_dir(log_path.parent)
        started = time.monotonic()
        normalized_make_args = self._normalize_make_args_for_project(
            project=project,
            verb=verb,
            make_args=make_args,
        )
        proc_result = u.Cli.run_to_file(
            [c.Infra.MAKE, "-C", project, verb, *normalized_make_args],
            log_path,
            env={"NO_COLOR": "1"},
        )
        return_code: int = proc_result.unwrap() if proc_result.success else 1
        stderr = "" if proc_result.success else proc_result.error or ""
        elapsed = time.monotonic() - started
        if return_code == 0:
            u.Cli.info(
                f"  ✓ {project} completed in {int(elapsed)}s  ({log_path})",
            )
        else:
            error_count, error_lines = u.Infra.extract_errors(log_path)
            u.Cli.project_failure(
                m.Infra.ProjectFailureInfo(
                    project=project,
                    elapsed=elapsed,
                    log_path=log_path,
                    error_count=error_count,
                    errors=list(error_lines),
                )
            )
            if error_lines:
                stderr = "\n".join(error_lines)
        return r[m.Cli.CommandOutput].ok(
            m.Cli.CommandOutput(
                stdout=str(log_path),
                stderr=stderr,
                exit_code=return_code,
                duration=round(elapsed, 2),
            ),
        )

    def _normalize_make_args_for_project(
        self,
        *,
        project: str,
        verb: str,
        make_args: t.StrSequence,
    ) -> t.StrSequence:
        """Normalize make args for project."""
        if (verb != c.Infra.VERB_CHECK) or (not self._is_go_project(project)):
            return make_args
        normalized_args: t.MutableSequenceOf[str] = []
        for make_arg in make_args:
            if make_arg.startswith("CHECK_GATES="):
                _, _, gates_value = make_arg.partition("=")
                normalized_gates = self._normalize_check_gates_for_go(gates_value)
                normalized_args.append(f"CHECK_GATES={normalized_gates}")
                continue
            normalized_args.append(make_arg)
        return normalized_args

    def _is_go_project(self, project: str) -> bool:
        """Is go project."""
        go_mod: str = c.Infra.GO_MOD
        return (Path(project) / go_mod).exists()

    def _normalize_check_gates_for_go(self, gates_value: str) -> str:
        """Normalize check gates for go."""
        raw_gates = [gate.strip() for gate in gates_value.split(",") if gate.strip()]
        if not raw_gates:
            return gates_value
        normalized_gates: t.MutableSequenceOf[str] = []
        go_supported = {
            c.Infra.LINT,
            c.Infra.FORMAT,
            c.Infra.SECURITY,
            c.Infra.MARKDOWN,
            c.Infra.GO,
            c.Infra.TYPE_ALIAS,
        }
        python_type_gates = {
            c.Infra.PYREFLY,
            c.Infra.MYPY,
            c.Infra.PYRIGHT,
        }
        for gate in raw_gates:
            mapped_gate = c.Infra.TYPE_ALIAS if gate in python_type_gates else gate
            if mapped_gate not in go_supported and mapped_gate not in python_type_gates:
                normalized_gates.append(mapped_gate)
                continue
            if mapped_gate in go_supported and mapped_gate not in normalized_gates:
                normalized_gates.append(mapped_gate)
        if not normalized_gates:
            normalized_gates.append(c.Infra.TYPE_ALIAS)
        return ",".join(normalized_gates)


__all__: list[str] = ["FlextInfraOrchestratorRunMixin"]
