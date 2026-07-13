"""Synchronize pyright, mypy, and pyrefly paths from workspace dependencies.

Handlers are called by the canonical CLI via FlextInfraCliDeps.register_deps.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, override

from flext_infra import c, config, p, r, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.deps._extra_paths_sources import FlextInfraExtraPathsSourceMixin
from flext_infra.deps._extra_paths_sync import FlextInfraExtraPathsSyncMixin

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraExtraPathsManager(
    FlextInfraExtraPathsSourceMixin,
    FlextInfraExtraPathsSyncMixin,
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Manager for synchronizing type-checker search paths from dependencies."""

    _workspace_project_names: t.Infra.StrSet = u.PrivateAttr(default_factory=set)

    @override
    def model_post_init(self, __context: t.MappingKV[str, p.AttributeProbe], /) -> None:
        """Initialize workspace metadata after validation."""
        self._workspace_project_names = set(
            u.Infra.workspace_member_names(self.workspace_root)
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Synchronize extra paths for the configured project slice."""
        result = self.sync_extra_paths(
            dry_run=self.effective_dry_run, project_dirs=self.project_dirs
        )
        if result.failure:
            return r[bool].fail(result.error or "extra-path synchronization failed")
        return r[bool].ok(True)

    def _dep_paths(
        self, payload: t.Infra.ContainerDict, *, project_dir: Path
    ) -> t.StrSequence:
        """Resolve only productive dependency import roots to relative paths."""
        project_table = payload.get(c.Infra.PROJECT)
        current_project_name = (
            project_table.get(c.NAME) if isinstance(project_table, Mapping) else None
        )
        resolved: t.Infra.StrSet = set()
        for name in self._resolve_transitive_deps(
            u.Infra.local_dependency_names_from_payload(
                payload, workspace_project_names=tuple(self._workspace_project_names)
            )
        ):
            if isinstance(current_project_name, str) and name == current_project_name:
                continue
            dep_dir = self.root / name
            # mro-j47u (codex): dependency lookup is an import-root contract;
            # legacy/examples/scripts are never promoted by directory discovery.
            for source_root in self._uv_source_search_roots(dep_dir):
                resolved.add(
                    self._project_relative_path(
                        project_dir=project_dir, target_dir=source_root
                    )
                )
        return tuple(sorted(resolved))

    @override
    def pyright_extra_paths(self, *, project_dir: Path, is_root: bool) -> t.StrSequence:
        """Compute pyright extra paths for a project."""
        rules = config.Infra.tooling.tools.pyright.path_rules
        source_root = rules.source_dir
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
        self, *, project_dir: Path, is_root: bool
    ) -> t.StrSequence:
        """Compute pyrefly search paths for a project."""
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        source_root = rules.source_dir
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
        paths: t.Infra.StrSet = {*typings_paths, *shared_paths}
        if rules.include_path_dependencies_in_search_path:
            pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
            if pyproject.exists():
                payload = u.Infra.pyproject_payload(pyproject)
                paths.update(self._dep_paths(payload, project_dir=project_dir))
                paths.update(self._uv_source_paths(payload, project_dir=project_dir))
        paths.add(source_root)
        return sorted(paths)

    def pyrefly_project_includes(
        self, *, project_dir: Path, is_root: bool
    ) -> t.StrSequence:
        """Build Pyrefly includes from configured productive directories."""
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        # mro-j47u (codex): never reread an on-disk Pyright table while its
        # in-memory payload is being conformed; include only real production roots.
        includes: t.Infra.StrSet = set(
            self.pyrefly_include_globs(
                tuple(
                    directory
                    for directory in rules.env_dirs
                    if (project_dir / directory).is_dir()
                )
            )
        )
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
    def pyrefly_include_globs(env_dirs: t.StrSequence) -> t.StrSequence:
        """Render Pyrefly include globs for already validated Python roots."""
        return tuple(f"{directory}/**/*.py*" for directory in env_dirs)


__all__: list[str] = ["FlextInfraExtraPathsManager"]
