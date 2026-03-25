"""Rope Project lifecycle and refactor utilities — zero disk artifacts.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.base.project import Project as RopeProject
from rope.base.resources import File as RopeFile
from rope.refactor.rename import Rename

from flext_infra import c, t


class FlextInfraUtilitiesRope:
    """Rope Project lifecycle and refactor helpers — exposed via u.Infra.*."""

    @staticmethod
    def init_rope_project(
        workspace_root: Path,
        *,
        project_prefix: str = c.Infra.ROPE_PROJECT_PREFIX,
        src_dir: str = c.Infra.ROPE_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> RopeProject:
        """Create a rope Project over workspace_root with no disk artifacts.

        ropefolder=None prevents .ropeproject creation.
        Orchestrator controls project_prefix, src_dir, and ignored_resources.
        """
        source_folders = sorted(
            str(p / src_dir)
            for p in workspace_root.iterdir()
            if p.name.startswith(project_prefix) and (p / src_dir).is_dir()
        )
        return RopeProject(
            str(workspace_root),
            ropefolder=None,  # type: ignore[arg-type]  # rope stubs incomplete
            save_objectdb=False,
            ignored_resources=list(ignored_resources),
            source_folders=source_folders,
        )

    @staticmethod
    def get_file_resource(
        rope_project: RopeProject,
        module_name: str,
    ) -> RopeFile | None:
        """Return rope File for a dotted module name, or None if not found."""
        rel = module_name.replace(".", "/") + ".py"
        try:
            resource = rope_project.get_resource(rel)
            return resource if isinstance(resource, RopeFile) else None
        except ResourceNotFoundError:
            return None

    @staticmethod
    def find_definition_offset(source: str, symbol: str) -> int | None:
        """Return offset of symbol's definition in source, or None.

        Uses word-boundary matching to avoid false positives on prefix names
        (e.g. 'Foo' must not match 'FooBar').
        """
        pattern = re.compile(
            rf"(?:class|def)\s+({re.escape(symbol)})\b|^({re.escape(symbol)})\s*=",
            re.MULTILINE,
        )
        m = pattern.search(source)
        if m is None:
            return None
        # group(1) for class/def, group(2) for assignment
        return m.start(1) if m.group(1) is not None else m.start(2)

    @staticmethod
    def rename_symbol_workspace(
        rope_project: RopeProject,
        resource: RopeFile,
        offset: int,
        new_name: str,
        *,
        apply: bool,
    ) -> Sequence[str]:
        """Rename symbol at offset across the whole project.

        Returns list of file paths changed. Orchestrator decides whether to apply.
        """
        changed_files: t.Infra.MutableStrIndex = {}
        try:
            changes = Rename(rope_project, resource, offset).get_changes(new_name)
        except RefactoringError:
            return []
        for change in changes.changes:
            changed_files[change.resource.path] = 1
        if apply:
            rope_project.do(changes)
        return list(changed_files)

    @staticmethod
    def run_rope_pre_hooks(path: Path, *, dry_run: bool) -> list[str]:
        """Pre-hook stub — orchestrator wires transformers here."""
        del path, dry_run
        return []

    @staticmethod
    def run_rope_post_hooks(path: Path, *, dry_run: bool) -> list[str]:
        """Post-hook stub — cleanup pass after LibCST rules."""
        del path, dry_run
        return []


__all__ = ["FlextInfraUtilitiesRope"]
