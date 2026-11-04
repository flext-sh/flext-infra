"""FLEXT pyrefly quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, p, u
from flext_infra.gates import FlextInfraGates

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraGatesPyrefly(FlextInfraGates):
    """Pyrefly quality gate."""

    gate_id: ClassVar[str] = c.Infra.PYREFLY
    gate_name: ClassVar[str] = "Pyrefly"
    can_fix: ClassVar[bool] = False
    checker_info_prefixes: ClassVar[Sequence[str]] = ("INFO",)
    requires_python_targets: ClassVar[bool] = True

    # Native JSON report replaced before every run: ``{project}-pyrefly.json``.
    check_report_filename: ClassVar[str] = "pyrefly.json"
    check_remove_env_keys: ClassVar[Sequence[str]] = (
        *FlextInfraGates.check_remove_env_keys,
        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH,
    )

    def __init__(
        self,
        repository_root: Path,
        *,
        source_roots: Sequence[Path] = (),
        runner: p.Cli.CommandRunner = u.Cli,
    ) -> None:
        """Bind staged import roots while retaining normal project execution."""
        super().__init__(repository_root, runner=runner)
        self._source_roots = source_roots

    def _native_report_path(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> Path:
        """Resolve the JSON report this gate replaces before every run.

        Returns:
            The resulting ``Path``.

        Raises:
            RuntimeError: If ``check_report_filename`` is empty.

        """
        report_path = self._check_report_path(project_dir, ctx)
        if report_path is None:
            msg = "FlextInfraGatesPyrefly.check_report_filename is empty"
            raise RuntimeError(msg)
        return report_path

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> Sequence[str]:
        """Check only local Python roots to avoid scanning dependency trees.

        Returns:
            The resulting ``Sequence[str]``.

        """
        del ctx
        return self._python_targets(project_dir)

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        check_dirs: Sequence[str],
    ) -> Sequence[str]:
        """Run Pyrefly against the project config, writing its JSON report file.

        Returns:
            The Pyrefly invocation bound to the declared native runtime.

        """
        json_file = self._native_report_path(project_dir, ctx)
        target_args = u.Infra.pyrefly_target_args(
            project_dir,
            tuple(check_dirs),
            selected_files=ctx.selected_files,
        )
        return self._python_module_command(
            c.Infra.PYREFLY,
            c.Infra.CHECK,
            *target_args,
            *(() if self._source_roots else ("--config", c.PYPROJECT_FILENAME)),
            *(
                argument
                for source in self._source_roots
                for argument in ("--search-path", str(source))
            ),
            "--python-interpreter-path",
            str(u.Infra.runtime_python(project_dir, runtime_root=ctx.runtime_root)),
            "--output-format",
            c.Infra.OUTPUT_JSON,
            "--min-severity",
            "warn",
            "-o",
            str(json_file),
            "--summary=none",
        )

    @override
    def _evidence_output(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
        result: p.Cli.CommandOutput,
    ) -> str:
        """Publish the tool streams plus the native JSON report this gate owns.

        The JSON-mode invocation writes nothing to stdout or stderr, so the
        raw receipt carries the report the tool itself produced.

        Returns:
            The resulting ``str``.

        """
        parts = [self._raw_output(result)]
        report_path = self._native_report_path(project_dir, ctx)
        if report_path.exists():
            parts.append(report_path.read_text(encoding="utf-8"))
        return "\n".join(part for part in parts if part)

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> tuple[bool, Sequence[p.Infra.Issue]]:
        """Read Pyrefly's freshly written JSON report file into findings.

        Returns:
            The run's verdict and its diagnostics or stderr failures.

        """
        json_file = self._native_report_path(project_dir, ctx)
        if not u.Cli.process_succeeded(result.outcome) and not json_file.exists():
            return False, (
                self._command_error_issue(result, c.Infra.PYREFLY, str(json_file)),
            )
        validated: p.Result[p.Infra.PyreflyReport] = u.validate_value(
            m.Infra.PyreflyReport,
            json_file.read_text(encoding="utf-8"),
            from_json=True,
            strict=True,
        )
        if validated.failure:
            return False, (
                self._malformed_report_issue(
                    str(validated.error),
                    tool=c.Infra.PYREFLY,
                    file=str(json_file),
                ),
            )
        issues = self._checker_issues(
            result,
            project_dir,
            tuple(
                m.Infra.Issue(
                    file=diag.path,
                    line=diag.line,
                    column=diag.column,
                    code=diag.name,
                    message=diag.description,
                    severity=diag.severity,
                    locations=(),
                    related_locations=(),
                )
                for diag in validated.value.errors
            ),
        )
        return (
            u.Cli.process_succeeded(result.outcome)
            and not any(
                issue.severity.lower() in {"error", "warning", "warn"}
                for issue in issues
            ),
            issues,
        )


__all__: list[str] = ["FlextInfraGatesPyrefly"]
