"""Engine file collection and nested-class propagation utilities.

Centralizes file filtering, project/workspace file collection, and
rope-based nested class propagation helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRope,
    c,
    t,
)

if TYPE_CHECKING:
    from flext_infra import FlextInfraRefactorRuleLoader


class FlextInfraUtilitiesRefactorEngine:
    """Engine file collection and nested-class propagation helpers."""

    @staticmethod
    def apply_nested_class_propagation(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        mappings: t.StrMapping,
        changes: MutableSequence[str],
    ) -> str:
        """Apply nested class propagation and persist only when content changes."""
        source = FlextInfraUtilitiesRope.read_source(resource)
        updated = source
        for old_name, new_name in mappings.items():
            updated = re.sub(rf"\b{re.escape(old_name)}\b", new_name, updated)
        if updated != source:
            changes.append(
                f"Applied nested class propagation ({len(mappings)} renames)"
            )
            FlextInfraUtilitiesRope.write_source(
                rope_project,
                resource,
                updated,
                description="nested class propagation",
            )
        return updated

    # ── Engine file collection ─────────────────────────────────────────

    @staticmethod
    def filter_engine_files(
        candidates: Sequence[Path],
        *,
        base_path: Path,
        pattern: str,
        ignore_patterns: set[str],
        allowed_extensions: set[str],
    ) -> Sequence[Path]:
        """Filter candidate files by pattern, extensions, and ignore rules."""

        def _accept(f: Path) -> bool:
            rel = str(f.relative_to(base_path))
            if not (fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f.name, pattern)):
                return False
            if allowed_extensions and f.suffix not in allowed_extensions:
                return False
            if f.name in ignore_patterns:
                return False
            rp = f.relative_to(base_path)
            return not any(part in ignore_patterns for part in rp.parts) and not any(
                fnmatch.fnmatch(str(rp), ip) for ip in ignore_patterns
            )

        return [f for f in candidates if _accept(f)]

    @staticmethod
    def collect_engine_project_files(
        rule_loader: FlextInfraRefactorRuleLoader,
        config: t.Infra.InfraValue,
        project: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> MutableSequence[Path] | None:
        """Iterate and filter Python files under a project.

        Returns None on error.
        """
        loader = rule_loader
        scan_dirs = frozenset(loader.extract_project_scan_dirs(config))
        ir = FlextInfraUtilitiesIteration.iter_python_files(
            workspace_root=project,
            project_roots=[project],
            include_tests=c.Infra.Directories.TESTS in scan_dirs,
            include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
            include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
            src_dirs=scan_dirs or None,
        )
        if ir.is_failure:
            FlextInfraUtilitiesRefactorCli.refactor_error(
                ir.error or f"File iteration failed for {project}",
            )
            return None
        ign, ext = loader.extract_engine_file_filters(config)
        return list(
            FlextInfraUtilitiesRefactorEngine.filter_engine_files(
                ir.value,
                base_path=project,
                pattern=pattern,
                ignore_patterns={str(i) for i in ign},
                allowed_extensions={str(i) for i in ext},
            )
        )

    @staticmethod
    def collect_engine_workspace_files(
        rule_loader: FlextInfraRefactorRuleLoader,
        config: t.Infra.InfraValue,
        workspace_root: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> Sequence[Path]:
        """Collect all candidate files under workspace projects."""
        loader = rule_loader
        root = workspace_root.resolve()
        scan_dirs = frozenset(loader.extract_project_scan_dirs(config))
        projects = FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        ign, ext = loader.extract_engine_file_filters(config)
        ignore_patterns = {str(i) for i in ign}
        allowed_extensions = {str(i) for i in ext}
        all_files: MutableSequence[Path] = []
        for proj in projects:
            ir = FlextInfraUtilitiesIteration.iter_python_files(
                workspace_root=root,
                project_roots=[proj],
                include_tests=c.Infra.Directories.TESTS in scan_dirs,
                include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
                include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
                src_dirs=scan_dirs or None,
            )
            if ir.is_failure:
                FlextInfraUtilitiesRefactorCli.refactor_error(
                    ir.error or f"File iteration failed for {proj}",
                )
                continue
            all_files.extend(
                FlextInfraUtilitiesRefactorEngine.filter_engine_files(
                    ir.value,
                    base_path=proj,
                    pattern=pattern,
                    ignore_patterns=ignore_patterns,
                    allowed_extensions=allowed_extensions,
                )
            )
        return all_files


__all__ = ["FlextInfraUtilitiesRefactorEngine"]
