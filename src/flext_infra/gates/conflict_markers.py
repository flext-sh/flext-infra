"""Read-only Git conflict-marker gate over tracked and unpublished files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, t, u
from flext_infra.gates import FlextInfraGate


class FlextInfraConflictMarkersGate(FlextInfraGate):
    """Detect unresolved merge controls without following source symlinks."""

    gate_id: ClassVar[str] = c.Infra.CONFLICT_MARKERS
    gate_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO[gate_id][0]
    can_fix: ClassVar[bool] = False

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Check the owned Git inventory or a sealed candidate's physical tree.

        Returns:
            The complete scan receipt with every unresolved control line.

        Raises:
            ValueError: If the selected inventory has no source files.

        """
        if ctx.runtime_root is None:
            paths = u.Infra.git_tracked_scope_paths(project_dir)
            if paths is not None:
                changed = u.Infra.git_changed_paths(
                    m.Infra.GitRepoRequest(repo_root=project_dir)
                ).unwrap()
                paths = tuple(sorted({*paths, *changed}))
        else:
            manifest = u.Cli.atomic_inventory_physical_tree(project_dir).unwrap()
            paths = tuple(
                entry.path for entry in manifest.entries if entry.kind != "directory"
            )
        if paths is None or not paths:
            message = (
                f"conflict-marker gate requires a nonempty source inventory: {project_dir}"
            )
            raise ValueError(message)
        return self._check_paths(paths, project_dir)

    @override
    def check_files(
        self,
        files: t.SequenceOf[Path],
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Check the supplied owned files through the same scanner.

        Returns:
            The scan receipt for the selected files.

        """
        return (
            self._check_paths(files, project_dir)
            if files
            else self.check(project_dir, ctx)
        )

    def _check_paths(
        self,
        paths: t.SequenceOf[Path],
        project_dir: Path,
    ) -> m.Infra.GateExecution:
        """Read literal file bytes and classify controls through the shared owner.

        Returns:
            The completed verdict with source-path and line-number evidence.

        Raises:
            FileNotFoundError: If a required source snapshot contains no bytes.
            ValueError: If a selected source lies outside this project.

        """
        started = time.monotonic()
        issues: list[m.Infra.Issue] = []
        root = project_dir.resolve()
        for path in paths:
            source = path if path.is_absolute() else project_dir / path
            owned = source.parent.resolve() / source.name
            if not owned.is_relative_to(root):
                message = f"conflict-marker source is outside the project: {path}"
                raise ValueError(message)
            if owned.is_symlink():
                content = str(owned.readlink()).encode()
            else:
                content = (
                    u.Cli
                    .atomic_read_binary_file_state(owned, required=True)
                    .unwrap()
                    .content
                )
                if content is None:
                    raise FileNotFoundError(owned)
            for number, line in enumerate(content.splitlines(), start=1):
                if (control := u.Infra.merge_conflict_control(line)) is not None:
                    issues.append(
                        m.Infra.Issue(
                            file=str(owned),
                            line=number,
                            column=1,
                            code=f"{self.gate_id}-{control}",
                            message=f"Unresolved Git merge control: {control}",
                            severity=c.Infra.GateSeverity.ERROR.value,
                        ),
                    )
        raw = f"checked={len(paths)} findings={len(issues)}"
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=tuple(issues),
            raw_output="\n".join((raw, *(issue.formatted for issue in issues))),
            started=started,
        )


__all__: list[str] = ["FlextInfraConflictMarkersGate"]
