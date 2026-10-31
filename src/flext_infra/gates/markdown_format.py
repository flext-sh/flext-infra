"""FLEXT markdown formatting gate: ``rumdl fmt``, owned by ``make fmt``.

rumdl is the fleet's markdown linter and formatter (ADR-025). The read-only
side (``rumdl fmt --check``) validates inside ``make check``; the mutating
side (``rumdl fmt``) is reached only through the gate's fix contract from
``make fmt`` — the gate deliberately never appears in
``CANONICAL_FIXABLE_GATE_IDS``, so every tool runs exactly one operation per
verb and no verb repeats another's work. Both sides read the generated
``.rumdl.toml`` the ``markdown`` gate reads: one rule set, one owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import itertools
import time
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m
from flext_infra.gates import FlextInfraMarkdownGateBase

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraGatesMarkdownFormat(FlextInfraMarkdownGateBase):
    """Markdown formatting gate."""

    gate_id: ClassVar[str] = c.Infra.MARKDOWN_FORMAT
    gate_name: ClassVar[str] = "Markdown Format"
    can_fix: ClassVar[bool] = True

    @override
    def check_union(
        self,
        project_dirs: Sequence[Path],
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Keep the generated-configuration gap loud for its own project.

        A project without the generated configuration forms its own union
        group, so the single-project check reports that gap with its path.

        Returns:
            The union execution, or the project's configuration-gap result.

        """
        owner = project_dirs[0]
        if not (owner / c.Infra.MARKDOWN_CONFIG_FILENAME).is_file():
            return self.check(owner, ctx)
        return super().check_union(project_dirs, ctx)

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Run ``rumdl fmt --check`` against the generated rule set.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        config_path = project_dir / c.Infra.MARKDOWN_CONFIG_FILENAME
        if not config_path.is_file():
            # .rumdl.toml is a codegen-managed artifact (policy full):
            # absence is a generation gap reported loud with the exact path,
            # never a silent fall back to the tool's built-in defaults.
            return self._build_single_issue_result(
                project_dir,
                (
                    f"generated {c.Infra.MARKDOWN_CONFIG_FILENAME} is absent: "
                    f"{config_path}; run make gen"
                ),
                ctx,
                time.monotonic(),
            )
        return super().check(project_dir, ctx)

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: Sequence[str],
    ) -> Sequence[str]:
        """Build the read-only ``rumdl fmt --check`` pass.

        Returns:
            The resulting ``Sequence[str]``.

        """
        del ctx
        return self._rumdl_command(project_dir, "fmt", check_dirs, "--check")

    @override
    def _build_fix_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: Sequence[str],
    ) -> Sequence[str]:
        """Build the single mutating pass: ``rumdl fmt``.

        Returns:
            The resulting ``Sequence[str]``.

        """
        del ctx
        return self._rumdl_command(project_dir, "fmt", targets)

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[m.Infra.Issue]]:
        """Parse ``rumdl fmt --check``: one finding per file it would rewrite.

        The check pass prints a unified diff per file it would rewrite; the
        ``--- <file>`` / ``+++ <file>`` header pair names that file. Findings
        the formatter cannot repair belong to the ``markdown`` gate, and the
        mutating pass prints no diff, so neither yields a finding here.

        Returns:
            The resulting ``tuple[bool, Sequence[m.Infra.Issue]]``.

        """
        del ctx
        old_header, new_header = c.Infra.MARKDOWN_FORMAT_DIFF_HEADERS
        lines = result.stdout.splitlines()
        issues: MutableSequence[m.Infra.Issue] = [
            m.Infra.Issue(
                file=current.removeprefix(old_header),
                line=1,
                column=1,
                code=self.gate_id,
                message="file is not rumdl-formatted (repair belongs to `make fmt`)",
            )
            for current, following in itertools.pairwise(lines)
            if current.startswith(old_header)
            and following == new_header + current.removeprefix(old_header)
        ]
        return self._finalize_parse_result(
            result,
            project_dir,
            issues,
            c.Infra.RUMDL,
        )


__all__: list[str] = ["FlextInfraGatesMarkdownFormat"]
