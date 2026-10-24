"""Runtime integrity and declared native-module checks in the existing engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, t, u
from flext_infra.gates import FlextInfraGate
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraRuntimeIntegrityGate(FlextInfraGate):
    """Retain each existing runtime owner's native process exactly once."""

    gate_id: ClassVar[str] = c.Infra.RUNTIME_INTEGRITY
    gate_name: ClassVar[str] = "Runtime Integrity"

    def native_execution(
        self,
        name: str,
        command: t.StrSequence,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run one native owner and retain its unmodified causal outcome.

        Returns:
            The native execution result.

        """
        started = time.monotonic()
        native = self._run(command, project_dir)
        passed = u.Cli.process_succeeded(native.outcome)
        issues = (
            ()
            if passed
            else (
                self._command_error_issue(
                    native, tool=name, file=str(project_dir), line=0, column=0
                ),
            )
        )
        component_ctx = ctx.model_copy(update={"reports_dir": ctx.reports_dir / name})
        return self._build_check_gate_execution(
            project_dir,
            passed=passed,
            issues=issues,
            evidence=self._publish_raw_receipt(component_ctx, self._raw_output(native)),
            started=started,
        ).model_copy(
            update={
                "process": m.Cli.ProcessOutcome.model_validate(
                    native.outcome, from_attributes=True
                ),
                "outcome": (
                    c.Infra.ToolOutcome.CLEAN if passed else c.Infra.ToolOutcome.ERROR
                ),
            }
        )

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Execute the four original owners through this check invocation.

        Returns:
            The combined execution of the original owners.

        """
        started = time.monotonic()
        runtime_root = (
            FlextInfraWorkspaceDetector
            .runtime_election(project_dir)
            .unwrap()
            .runtime_root
            if ctx.runtime_root is None
            else ctx.runtime_root
        )
        python = u.Infra.runtime_python(project_dir, runtime_root=runtime_root)
        uv = u.Infra.managed_mise_binary("uv", runtime_root).unwrap()
        infra = (str(python), "-m", "flext_infra")
        commands: tuple[tuple[str, t.StrSequence], ...] = (
            (
                "pip-check",
                (str(uv), "pip", "check", "--python", str(python)),
            ),
            (
                "lock-integrity",
                (
                    *infra,
                    "deps",
                    "verify-locks",
                    "--repository-root",
                    str(project_dir if ctx.runtime_root is None else runtime_root),
                ),
            ),
            (
                "environment-provenance",
                (
                    *infra,
                    "workspace",
                    "verify-environment",
                    "--repository-root",
                    str(runtime_root),
                ),
            ),
            (
                "mise-proof",
                (
                    *infra,
                    "codegen",
                    "mise-proof",
                    "--repository-root",
                    str(runtime_root),
                    "--uv-executable",
                    str(uv),
                ),
            ),
        )
        components: dict[str, m.Infra.GateExecution] = {}
        for name, command in commands:
            execution = self.native_execution(name, command, project_dir, ctx)
            components[name] = execution
            if execution.interrupted or (not execution.result.passed and ctx.fail_fast):
                break
        issues = tuple(
            issue for execution in components.values() for issue in execution.issues
        )
        return self._build_check_gate_execution(
            project_dir,
            passed=len(components) == len(commands)
            and all(execution.result.passed for execution in components.values()),
            issues=issues,
            evidence=self._publish_raw_receipt(
                ctx,
                "\n".join(
                    f"{name}: {execution.raw_receipt}"
                    for name, execution in components.items()
                ),
            ),
            started=started,
        ).model_copy(
            update={
                "components": components,
                "requested_components": tuple(name for name, _ in commands),
                "outcome": (
                    c.Infra.ToolOutcome.CLEAN
                    if len(components) == len(commands)
                    and all(item.result.passed for item in components.values())
                    else c.Infra.ToolOutcome.ERROR
                ),
            }
        )


class FlextInfraProjectModuleGate(FlextInfraGate):
    """Run repository-declared modules through the canonical native gate runner."""

    @override
    def _get_check_dirs(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> t.StrSequence:
        """A declared module checks its project without invented file arguments.

        Returns:
            The single project directory argument.

        """
        del ctx
        return (str(project_dir),)

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: t.StrSequence
    ) -> t.StrSequence:
        """Bind the declared command to the elected physical environment.

        Returns:
            The command bound to the elected interpreter.

        """
        del check_dirs
        return (
            str(u.Infra.runtime_python(project_dir, runtime_root=ctx.runtime_root)),
            "-m",
            *self.check_module_command_prefix,
        )

    @override
    def _parse_check_output(
        self, result: p.Cli.CommandOutput, project_dir: Path, ctx: m.Infra.GateContext
    ) -> t.Pair[bool, t.SequenceOf[p.Infra.Issue]]:
        """Retain the native result without interpreting or suppressing output.

        Returns:
            The execution parsed from the native result.

        """
        del ctx
        passed = u.Cli.process_succeeded(result.outcome)
        return (
            passed,
            ()
            if passed
            else (
                self._command_error_issue(
                    result,
                    tool=self.gate_id,
                    file=str(project_dir),
                    line=0,
                    column=0,
                ),
            ),
        )

    @override
    def _parsed_gate_execution(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        result: p.Cli.CommandOutput,
        started: float,
    ) -> m.Infra.GateExecution:
        """Add the original process to the shared parsed execution.

        Returns:
            The shared parsed execution including the original process.

        """
        return (
            super()
            ._parsed_gate_execution(project_dir, ctx, result, started)
            .model_copy(
                update={
                    "process": m.Cli.ProcessOutcome.model_validate(
                        result.outcome, from_attributes=True
                    )
                }
            )
        )


__all__: list[str] = ["FlextInfraProjectModuleGate", "FlextInfraRuntimeIntegrityGate"]
