"""Deptry dependency-declaration gate over the project's import surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override
from uuid import uuid4

from flext_infra import c, config, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraDepsGate(FlextInfraGate):
    """Fail every import the project's declared dependencies never declare.

    Why (aihub-l42it.11): undeclared runtime imports surface today only deep
    inside the generation pipeline's rope pass, minutes into a failing run;
    this gate states the same fact in seconds at check time, so a racing
    consolidation can never land an orphan import unnoticed.
    """

    gate_id: ClassVar[str] = c.Infra.DEPS
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = False

    @override
    def selected_for(self, project_dir: Path) -> bool:
        """Select projects that declare dependencies (a pyproject exists).

        Returns:
            The resulting ``bool``.
        """
        return (project_dir / c.PYPROJECT_FILENAME).is_file()

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run deptry over the checkout and fail on any declared-surface gap.

        Native execution and report failures remain ERROR receipts, not findings.

        Args:
            project_dir: The root directory of the project to check.
            ctx: The gate context containing configuration and report directories.

        Returns:
            The complete scan receipt with every dependency issue.

        Raises:
            FileExistsError: If the report directory cannot be created.
        """
        started = time.monotonic()
        raw_output = ""
        native_error = ""
        issues: t.VariadicTuple[m.Infra.Issue] = ()
        outcome = c.Infra.ToolOutcome.ERROR
        try:
            settings = u.Cli.atomic_read_binary_file_state(
                project_dir / c.PYPROJECT_FILENAME,
                required=True,
            ).unwrap()
            source = project_dir / c.Infra.DEFAULT_SRC_DIR
            if not source.is_dir():
                msg = f"deptry production source is missing: {source}"
                raise FileNotFoundError(msg)
            # An exclusive run path cannot inherit a previous command's report.
            report_dir = ctx.reports_dir.absolute() / (
                f"{project_dir.name}-{self.gate_id}-{uuid4().hex}"
            )
            planned = u.Cli.atomic_plan_directory_chain(report_dir).unwrap()
            if not planned.directories:
                raise FileExistsError(report_dir)
            u.Cli.atomic_create_directory_chain_guarded(
                planned,
                permission_mode=config.Infra.codegen.modes.directory_private,
            ).unwrap()
            out_file = report_dir / "deptry.json"
            command = self._python_console_script_command(
                c.Infra.DEPTRY,
                str(c.Infra.DEFAULT_SRC_DIR),
                "--config",
                str(settings.path),
                "--json-output",
                str(out_file),
                "--no-ansi",
            )
            raw_output = f"command={command!r} cwd={project_dir} report={out_file}"
            native = u.Cli.run_raw(
                command,
                cwd=project_dir,
                timeout=c.Infra.TIMEOUT_MEDIUM,
            ).unwrap()
            raw_output += (
                f"\nreturn-code={native.outcome.raw_return_code}\n"
                + self._raw_output(native)
            )
            if not u.Cli.process_succeeded(native.outcome):
                native_error = self._raw_output(native)
            if (
                native.outcome.timed_out
                or native.outcome.forwarded_signal is not None
                or native.outcome.raw_return_code not in {0, 1}
            ):
                issues = (
                    self._command_error_issue(
                        native,
                        tool=c.Infra.DEPTRY,
                        file=str(project_dir),
                        line=0,
                        column=0,
                    ),
                )
            else:
                state = u.Cli.atomic_read_binary_file_state(
                    out_file,
                    required=True,
                ).unwrap()
                content = self._report_content(state.content, out_file)
                report = m.Infra.DeptryNativeReport.model_validate_json(
                    content,
                    strict=True,
                )
                u.Cli.atomic_verify_binary_file_states((settings, state)).unwrap()
                raw_output += f"\nreport-sha256={u.Cli.sha256_bytes(content)}"
                issues = tuple(
                    m.Infra.Issue(
                        file=item.location.file,
                        line=(
                            item.location.line if item.location.line is not None else 0
                        ),
                        column=(
                            item.location.column
                            if item.location.column is not None
                            else 0
                        ),
                        code=f"{self.gate_id}-{item.error.code}",
                        message=item.error.message,
                        severity=c.Infra.GateSeverity.ERROR.value,
                    )
                    for item in report.root
                )
                self._require_exit_report_agreement(
                    native.outcome.raw_return_code,
                    len(issues),
                )
                outcome = u.Infra.tool_outcome(
                    native.outcome,
                    findings=len(issues),
                    findings_exit_codes=(1,),
                )
        except (OSError, ValueError, RuntimeError) as exc:
            issues = (
                *issues,
                m.Infra.Issue(
                    file=str(project_dir),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message="\n".join(
                        detail
                        for detail in (native_error, f"{type(exc).__name__}: {exc}")
                        if detail
                    ),
                    severity=c.Infra.GateSeverity.ERROR.value,
                ),
            )
            raw_output += "\n" + issues[-1].message
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=outcome is c.Infra.ToolOutcome.CLEAN,
                outcome=outcome,
                issues=issues,
                raw_output=raw_output,
                started=started,
            ),
        )

    @staticmethod
    def _report_content(content: bytes | None, out_file: Path) -> bytes:
        """Return the native report bytes, or raise when deptry wrote none.

        Args:
            content: The captured report bytes, None without a native report.
            out_file: The report path named by the failure message.

        Returns:
            The native report bytes.

        Raises:
            ValueError: If deptry did not produce its native report.

        """
        if content is None:
            msg = f"deptry did not produce its native report: {out_file}"
            raise ValueError(msg)
        return content

    @staticmethod
    def _require_exit_report_agreement(return_code: int, findings: int) -> None:
        """Raise when deptry's exit status contradicts its native report.

        Args:
            return_code: The native deptry process return code.
            findings: The number of issues the native report declares.

        Raises:
            ValueError: If the exit status contradicts the native report.

        """
        if return_code != int(bool(findings)):
            msg = "deptry exit status contradicts its native report"
            raise ValueError(msg)


__all__: list[str] = ["FlextInfraDepsGate"]
