"""Engine file collection and nested-class propagation utilities.

Centralizes file filtering, project/workspace file collection, and
rope-based nested class propagation helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
from collections.abc import (
    Iterator,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import (
    FlextInfraUtilitiesIteration,
    c,
    t,
)

if TYPE_CHECKING:
    from flext_infra import FlextInfraUtilitiesRefactorRuleLoader


class FlextInfraUtilitiesRefactorEngine:
    """Engine file collection and nested-class propagation helpers."""

    @staticmethod
    def filter_engine_files(
        files: Sequence[Path],
        *,
        base_path: Path,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
        ignore_patterns: set[str] | None = None,
        allowed_extensions: set[str] | None = None,
    ) -> Iterator[Path]:
        """Filter candidate files by glob pattern, ignore list, and extension."""
        ign = ignore_patterns or set()
        ext = allowed_extensions or {c.Infra.EXT_PYTHON}
        for f in files:
            if not fnmatch.fnmatch(f.name, pattern):
                continue
            if f.suffix not in ext:
                continue
            try:
                rel = str(f.relative_to(base_path))
            except ValueError:
                rel = str(f)
            if any(fnmatch.fnmatch(rel, ip) for ip in ign):
                continue
            yield f

    @staticmethod
    def collect_engine_project_files(
        rule_loader: FlextInfraUtilitiesRefactorRuleLoader,
        settings: t.Infra.InfraValue,
        project: Path,
        *,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> MutableSequence[Path] | None:
        """Iterate and filter Python files under a project.

        Returns None on error.
        """
        loader = rule_loader
        scan_dirs = frozenset(loader.extract_project_scan_dirs(settings))
        ir = FlextInfraUtilitiesIteration.iter_python_files(
            workspace_root=project,
            project_roots=[project],
            include_tests=c.Infra.DIR_TESTS in scan_dirs,
            include_examples=c.Infra.DIR_EXAMPLES in scan_dirs,
            include_scripts=c.Infra.DIR_SCRIPTS in scan_dirs,
            src_dirs=scan_dirs or None,
        )
        if ir.failure:
            u.Cli.error(ir.error or f"File iteration failed for {project}")
            return None
        ign, ext = loader.extract_engine_file_filters(settings)
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
        rule_loader: FlextInfraUtilitiesRefactorRuleLoader,
        settings: t.Infra.InfraValue,
        workspace_root: Path,
        *,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> Sequence[Path]:
        """Collect all candidate files under workspace projects."""
        loader = rule_loader
        root = workspace_root.resolve()
        scan_dirs = frozenset(loader.extract_project_scan_dirs(settings))
        projects = FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        ign, ext = loader.extract_engine_file_filters(settings)
        ignore_patterns = {str(i) for i in ign}
        allowed_extensions = {str(i) for i in ext}
        all_files: MutableSequence[Path] = []
        for proj in projects:
            ir = FlextInfraUtilitiesIteration.iter_python_files(
                workspace_root=root,
                project_roots=[proj],
                include_tests=c.Infra.DIR_TESTS in scan_dirs,
                include_examples=c.Infra.DIR_EXAMPLES in scan_dirs,
                include_scripts=c.Infra.DIR_SCRIPTS in scan_dirs,
                src_dirs=scan_dirs or None,
            )
            if ir.failure:
                u.Cli.error(ir.error or f"File iteration failed for {proj}")
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


__all__: list[str] = ["FlextInfraUtilitiesRefactorEngine"]
