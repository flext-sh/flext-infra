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
)
from pathlib import Path

from flext_cli.utilities import u
from flext_infra import (
    c,
    m,
    t,
)
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra.iteration import FlextInfraUtilitiesIteration


class FlextInfraUtilitiesRefactorEngine:
    """Engine file collection and nested-class propagation helpers."""

    @staticmethod
    def _resolve_engine_config(
        settings: t.MappingKV[str, t.Infra.InfraValue],
    ) -> m.Infra.EngineConfig:
        """Resolve the typed refactor engine config through the shared CLI DSL."""
        return m.Infra.EngineConfig.model_validate(
            u.Cli.rules_resolve_scope(
                dict(settings),
                scope_key=c.Infra.RK_REFACTOR_ENGINE,
                allowed_keys=c.Infra.ENGINE_CONFIG_KEYS,
            )
        )

    @staticmethod
    def filter_engine_files(
        files: t.SequenceOf[Path],
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
            rel = str(f.relative_to(base_path))
            if any(fnmatch.fnmatch(rel, ip) for ip in ign):
                continue
            yield f

    @staticmethod
    def collect_engine_project_files(
        settings: t.MappingKV[str, t.Infra.InfraValue],
        project: Path,
        *,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> t.MutableSequenceOf[Path] | None:
        """Iterate and filter Python files under a project.

        Returns None on error.
        """
        engine_config = FlextInfraUtilitiesRefactorEngine._resolve_engine_config(
            settings,
        )
        scan_dirs = frozenset(engine_config.project_scan_dirs)
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
        ign = engine_config.ignore_patterns
        ext = engine_config.file_extensions
        return list(
            FlextInfraUtilitiesRefactorEngine.filter_engine_files(
                ir.value,
                base_path=project,
                pattern=pattern,
                ignore_patterns=set(ign),
                allowed_extensions=set(ext),
            )
        )

    @staticmethod
    def collect_engine_workspace_files(
        settings: t.MappingKV[str, t.Infra.InfraValue],
        workspace_root: Path,
        *,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
    ) -> t.SequenceOf[Path]:
        """Collect all candidate files under workspace projects."""
        root = workspace_root.resolve()
        engine_config = FlextInfraUtilitiesRefactorEngine._resolve_engine_config(
            settings,
        )
        scan_dirs = frozenset(engine_config.project_scan_dirs)
        projects = FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        ign = engine_config.ignore_patterns
        ext = engine_config.file_extensions
        ignore_patterns = set(ign)
        allowed_extensions = set(ext)
        all_files: t.MutableSequenceOf[Path] = []
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

    @staticmethod
    def discover_engine_projects(
        settings: t.MappingKV[str, t.Infra.InfraValue],
        workspace_root: Path,
    ) -> t.SequenceOf[Path]:
        """Discover workspace projects using the typed engine config."""
        root = workspace_root.resolve()
        engine_config = FlextInfraUtilitiesRefactorEngine._resolve_engine_config(
            settings,
        )
        scan_dirs = frozenset(engine_config.project_scan_dirs)
        return FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )


__all__: list[str] = ["FlextInfraUtilitiesRefactorEngine"]
