"""Synchronize pyright, mypy, and pyrefly paths from workspace dependencies.

Handlers are called by the canonical CLI via FlextInfraCliDeps.register_deps.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

from flext_infra import (
    c,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.deps._extra_paths_sources import FlextInfraExtraPathsSourceMixin
from flext_infra.deps._extra_paths_sync import FlextInfraExtraPathsSyncMixin


class FlextInfraExtraPathsManager(
    FlextInfraExtraPathsSourceMixin,
    FlextInfraExtraPathsSyncMixin,
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Manager for synchronizing type-checker search paths from dependencies."""

    _tool_config: m.Infra.ToolConfigDocument = u.PrivateAttr()
    _workspace_project_names: t.Infra.StrSet = u.PrivateAttr(default_factory=set)

    @override
    def model_post_init(self, __context: dict[str, p.AttributeProbe], /) -> None:
        """Initialize tool configuration and workspace metadata after validation."""
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.failure:
            msg = tool_config_result.error or "failed to load deps tool settings"
            raise ValueError(msg)
        self._tool_config = tool_config_result.value
        self._workspace_project_names = set(
            u.Infra.workspace_member_names(self.workspace_root)
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Synchronize extra paths for the configured project slice."""
        result = self.sync_extra_paths(
            dry_run=self.effective_dry_run,
            project_dirs=self.project_dirs,
        )
        if result.failure:
            return r[bool].fail(result.error or "extra-path synchronization failed")
        return r[bool].ok(True)

    def _dep_paths(
        self,
        payload: t.Infra.ContainerDict,
        *,
        is_root: bool = False,
    ) -> t.StrSequence:
        """Resolve dependency source roots to relative search paths."""
        dep_skip = c.Infra.COMMON_EXCLUDED_DIRS | frozenset({c.Infra.DIR_TESTS})
        project_table = payload.get(c.Infra.PROJECT)
        current_project_name = (
            project_table.get(c.NAME) if isinstance(project_table, Mapping) else None
        )
        resolved: t.MutableSequenceOf[str] = []
        for name in self._resolve_transitive_deps(
            u.Infra.local_dependency_names_from_payload(
                payload,
                workspace_project_names=tuple(self._workspace_project_names),
            )
        ):
            if isinstance(current_project_name, str) and name == current_project_name:
                continue
            prefix = name if is_root else f"../{name}"
            dep_dir = self.root / name
            if not dep_dir.is_dir():
                resolved.append(f"{prefix}/src")
                continue
            for dir_name in u.Infra.discover_python_dirs(dep_dir, skip_dirs=dep_skip):
                resolved.append(f"{prefix}/{dir_name}")
        return resolved

    @override
    def pyright_extra_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Compute pyright extra paths for a project."""
        rules = self._tool_config.tools.pyright.path_rules
        source_root = (
            rules.source_dir
            if (project_dir / rules.source_dir).is_dir()
            else rules.project_root
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = [
            relative_path
            for relative_path in configured_typings
            if (project_dir / relative_path).is_dir()
        ]
        return sorted({rules.project_root, source_root, *typings_paths})

    def pyrefly_search_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Compute pyrefly search paths for a project."""
        rules = self._tool_config.tools.pyrefly.path_rules
        source_root = (
            rules.source_dir
            if (project_dir / rules.source_dir).is_dir()
            else rules.project_root
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = [
            relative_path
            for relative_path in configured_typings
            if (project_dir / relative_path).is_dir()
        ]
        shared_paths = [
            relative_path
            for relative_path in rules.project_shared_search_paths
            if (project_dir / relative_path).is_dir()
        ]
        local_dirs = [
            directory
            for directory in u.Infra.discover_python_dirs(project_dir)
            if not is_root
            or not (project_dir / directory / c.Infra.PYPROJECT_FILENAME).is_file()
        ]
        paths: t.Infra.StrSet = {*typings_paths, *shared_paths}
        if rules.include_path_dependencies_in_search_path:
            pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
            if pyproject.exists():
                payload = u.Infra.pyproject_payload(
                    pyproject,
                )
                paths.update(self._dep_paths(payload, is_root=is_root))
                paths.update(self._uv_source_paths(payload, project_dir=project_dir))
        if (project_dir / source_root).is_dir():
            paths.add(source_root)
        if (
            any(directory != source_root for directory in local_dirs)
            or any(project_dir.glob("*.py"))
            or any(project_dir.glob("*.pyi"))
        ):
            paths.add(rules.project_root)
        if (not paths) and (project_dir / rules.project_root).is_dir():
            paths.add(rules.project_root)
        return sorted(paths)

    def pyrefly_project_includes(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Build pyrefly project-includes from auto-discovered top-level Python dirs."""
        pyright_includes = self._pyright_include_globs(project_dir)
        if pyright_includes:
            return pyright_includes
        rules = self._tool_config.tools.pyrefly.path_rules
        includes: t.Infra.StrSet = set()
        local_dirs = [
            directory
            for directory in u.Infra.discover_python_dirs(project_dir)
            if not is_root
            or not (project_dir / directory / c.Infra.PYPROJECT_FILENAME).is_file()
        ]
        includes.update(f"{directory}/**/*.py*" for directory in local_dirs)
        if not is_root or (not rules.workspace_include_children):
            return sorted(includes)
        for child in sorted(project_dir.iterdir()):
            if not child.is_dir() or not (child / c.Infra.PYPROJECT_FILENAME).exists():
                continue
            child_dirs = u.Infra.discover_python_dirs(child)
            includes.update(
                f"{child.name}/{directory}/**/*.py*" for directory in child_dirs
            )
        return sorted(includes)

    @staticmethod
    def _pyright_include_globs(project_dir: Path) -> t.StrSequence:
        """Return pyrefly-compatible globs derived from [tool.pyright].include."""
        pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
        if not pyproject.exists():
            return ()
        payload = u.Infra.pyproject_payload(pyproject)
        tool_table = payload.get(c.Infra.TOOL)
        if not isinstance(tool_table, Mapping):
            return ()
        pyright_table = tool_table.get(c.Infra.PYRIGHT)
        if not isinstance(pyright_table, Mapping):
            return ()
        include_items = pyright_table.get(c.Infra.INCLUDE)
        if not isinstance(include_items, list):
            return ()
        includes: t.Infra.StrSet = set()
        for item in include_items:
            if not isinstance(item, str):
                continue
            normalized = item.strip().rstrip("/")
            if not normalized:
                continue
            if "*" in normalized or normalized.endswith((".py", ".pyi")):
                includes.add(normalized)
            else:
                includes.add(f"{normalized}/**/*.py*")
        return tuple(sorted(includes))


__all__: list[str] = ["FlextInfraExtraPathsManager"]
