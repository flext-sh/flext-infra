"""Runtime integrity check in the existing gate engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraGatesRuntimeIntegrityGate(FlextInfra):
    """Retain each existing runtime owner's native process exactly once."""

    gate_id: ClassVar[str] = c.Infra.RUNTIME_INTEGRITY
    gate_name: ClassVar[str] = "Runtime Integrity"

    def native_execution(
        self,
        name: str,
        command: Sequence[str],
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run one native owner and retain its unmodified causal outcome.

        Returns:
            The native execution result.

        """
        started = time.monotonic()
        native = self._run(command, project_dir, ctx)
        passed = u.Cli.process_succeeded(native.outcome)
        issues = (
            ()
            if passed
            else (self._command_error_issue(native, name, str(project_dir)),)
        )
        component_ctx = ctx.model_copy(update={"reports_dir": ctx.reports_dir / name})
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=passed,
                issues=tuple(issues),
                raw_output=self._raw_output(native),
                started=started,
            ),
            component_ctx,
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

    def _waved_execution(
        self,
        name: str,
        command: Sequence[str],
        project_dir: Path,
        ctx: m.Infra.GateContext,
        signal_wave: p.Cli.SignalWave,
    ) -> m.Infra.GateExecution:
        """Run one native owner as a task of the gate's concurrent wave.

        Returns:
            The native execution result.

        """
        return self.native_execution(
            name,
            command,
            project_dir,
            ctx.model_copy(update={"signal_wave": signal_wave}),
        )

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Execute the original owners through this check invocation.

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
        commands: tuple[tuple[str, Sequence[str]], ...] = (
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
        if ctx.fail_fast:
            for name, command in commands:
                execution = self.native_execution(name, command, project_dir, ctx)
                components[name] = execution
                if execution.interrupted or not execution.result.passed:
                    break
        else:
            # The read-only owners share no mutable state: one concurrent
            # wave, so the gate costs its slowest owner instead of their sum.
            executions = u.Cli.run_in_signal_wave(
                tuple(
                    partial(self._waved_execution, name, command, project_dir, ctx)
                    for name, command in commands
                ),
                max_workers=len(commands),
                signal_wave=ctx.signal_wave,
            )
            components.update(
                (name, execution)
                for (name, _command), execution in zip(
                    commands, executions, strict=True
                )
            )
        issues = tuple(
            issue for execution in components.values() for issue in execution.issues
        )
        return self._build_gate_execution(
            m.Infra.GateExecutionParams(
                project_dir=project_dir,
                verdict=len(components) == len(commands)
                and all(execution.result.passed for execution in components.values()),
                issues=tuple(issues),
                raw_output="\n".join(
                    f"{name}: {execution.raw_receipt}"
                    for name, execution in components.items()
                ),
                started=started,
            ),
            ctx,
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


__all__: list[str] = ["FlextInfraGatesRuntimeIntegrity"]
