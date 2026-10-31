"""FLEXT markdown quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m
from flext_infra.gates import FlextInfraMarkdownGateBase

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraGatesMarkdown(FlextInfraMarkdownGateBase):
    """Markdown quality gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN
    gate_name: ClassVar[str] = "Markdown"
    # Fixable findings are repaired by the native linter. The findings that
    # remain after repair come back under rumdl's declared findings status:
    # the repair verb completes and reports them, and the read-only gate
    # enforces them.
    can_fix: ClassVar[bool] = True

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: Sequence[str],
    ) -> Sequence[str]:
        """Lint the collected Markdown files read-only, through their lint view.

        rumdl has no configuration that excludes a region of a file, so the
        check reads every target from ``--stdin-batch`` (see
        ``_execute_check_command``) under its own path, with declared foreign
        projected blocks masked.

        Returns:
            The rumdl check invocation.

        """
        del ctx, check_dirs
        return self._rumdl_command(project_dir, "check", (), "--stdin-batch")

    @override
    def _execute_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: Sequence[str],
        started: float,
    ) -> m.Infra.GateExecution:
        """Run the read-only lint over every target's projected-block view.

        The check command reads its targets from stdin, so the invocation
        carries the rumdl ``--stdin-batch`` payload of every target.

        Returns:
            The parsed lint execution.

        """
        result = self._run(
            self._build_check_command(project_dir, ctx, targets),
            project_dir,
            ctx,
            input_data=self.projected_block_stdin_batch(project_dir, targets),
        )
        return self._parsed_gate_execution(project_dir, ctx, result, started)

    @override
    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: Sequence[str],
    ) -> Sequence[str]:
        """Repair fixable findings and return the linter's residual verdict.

        Returns:
            The resulting ``Sequence[str]``.

        """
        del ctx
        return self._rumdl_command(project_dir, "check", targets, "--fix")

    @override
    def _projected_command(self, project_dir: Path, target: str) -> Sequence[str]:
        """Repair one projected file's lint view read from stdin.

        Returns:
            The rumdl ``check --fix --stdin`` invocation named after ``target``.

        """
        return self._rumdl_command(
            project_dir, "check", (), "--fix", "--stdin", "--stdin-filename", target
        )

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        """Parse rumdl output, discarding lines marking already-applied fixes.

        Returns:
            The resulting ``tuple[bool, Sequence[m.Infra.Issue]]``.

        """
        del ctx
        issues: MutableSequence[m.Infra.Issue] = []
        for line in (result.stdout + "\n" + result.stderr).splitlines():
            match = c.Infra.MARKDOWN_RE.match(line.strip())
            if not match:
                continue
            if match.group("msg").strip().endswith(c.Infra.MARKDOWN_FIXED_SUFFIX):
                continue
            issues.append(
                m.Infra.Issue(
                    file=match.group("file"),
                    line=int(match.group("line")),
                    column=int(match.group("col") or 1),
                    code=match.group("code"),
                    message=match.group("msg"),
                ),
            )
        return self._finalize_parse_result(result, project_dir, issues, c.Infra.RUMDL)


__all__: list[str] = ["FlextInfraGatesMarkdown"]
