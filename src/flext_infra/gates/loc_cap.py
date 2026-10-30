"""FLEXT module-cap SUPREME LAW (§3.1) quality gate.

Enforces the per-module logical-LOC ceiling using scc's code-line count.
Per-class / per-method / per-function caps require AST and are out of scope
for this tool-driven gate (scc reports at file granularity only).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, config, m, u
from flext_infra.gates import FlextInfraGates

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraLocCapGate(FlextInfraGates):
    """Flag any module whose scc `Code` LOC exceeds the config-owned ceiling."""

    gate_id: ClassVar[str] = "loc-cap"
    gate_name: ClassVar[str] = "MODULE-LOC SUPREME LAW"
    can_fix: ClassVar[bool] = False

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: Sequence[str],
    ) -> Sequence[str]:
        """Run scc over the project's Python directories, emitting per-file JSON.

        Returns:
            The resulting ``Sequence[str]``.

        """
        _ = project_dir, ctx
        return [
            c.Infra.SCC_BINARY,
            "--format",
            "json",
            "--by-file",
            *check_dirs,
        ]

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        """Parse scc JSON into one Issue per over-cap module.

        Returns:
            The resulting ``tuple[bool, Sequence[m.Infra.Issue]]``.

        """
        del project_dir, ctx
        if not u.Cli.process_succeeded(result.outcome):
            return (
                False,
                (
                    m.Infra.Issue(
                        file="<scc>",
                        line=0,
                        column=0,
                        code="LOC_CAP_EXEC",
                        message=result.stderr or "scc execution failed",
                        severity="ERROR",
                    ),
                ),
            )
        issues = self._files_over_cap(
            result.stdout,
            config.Infra.codegen.loc_cap.max_lines,
        )
        return len(issues) == 0, issues

    @staticmethod
    def _issue_for_over_cap(path: str, code: int, cap: int) -> m.Infra.Issue:
        """Build the ``LOC_CAP`` issue for one module past the SUPREME LAW cap.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=path,
            line=code,
            column=0,
            code="LOC_CAP",
            message=f"{code} code LOC exceeds {cap}-line SUPREME LAW",
            severity="ERROR",
        )

    @classmethod
    def _files_over_cap(
        cls,
        scc_json: str,
        cap: int,
    ) -> tuple[m.Infra.Issue, ...]:
        """Extract over-cap modules from an `scc --format json --by-file` payload.

        Generated and authored modules share the same configured ceiling.
        Parsing failures propagate.

        Returns:
            The resulting ``tuple[m.Infra.Issue, ...],``.

        """
        report = m.Infra.SccReport.model_validate_json(scc_json, strict=True)
        return tuple(
            cls._issue_for_over_cap(file.location, file.code, cap)
            for language in report.root
            if language.name == c.Infra.SCC_PYTHON_LANG
            for file in language.files
            if file.code > cap
        )


__all__: list[str] = ["FlextInfraGatesLocCap"]
