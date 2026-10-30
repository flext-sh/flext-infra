"""Native gate running one repository-declared module through its runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_infra import m, p, u
from flext_infra.gates import FlextInfraGates


class FlextInfraGatesProjectModule(FlextInfraGates):
    """Run repository-declared modules through the canonical native gate runner."""

    @override
    def _get_check_dirs(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> Sequence[str]:
        """A declared module checks its project without invented file arguments.

        Returns:
            The single project directory argument.

        """
        del ctx
        return (str(project_dir),)

    @override
    def _build_check_command(
        self, project_dir: Path, ctx: m.Infra.GateContext, check_dirs: Sequence[str]
    ) -> Sequence[str]:
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
    ) -> tuple[bool, Sequence[p.Infra.Issue]]:
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
            else (self._command_error_issue(result, self.gate_id, str(project_dir)),),
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


__all__: list[str] = ["FlextInfraGatesProjectModule"]
