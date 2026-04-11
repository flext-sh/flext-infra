"""Pyrefly path computation helpers for extra_paths manager."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraUtilitiesDiscovery, c, t, u

if TYPE_CHECKING:
    from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager


class FlextInfraExtraPathsPyrefly:
    """Pyrefly search-path and project-includes computation."""

    def pyrefly_search_paths(
        self: FlextInfraExtraPathsManager,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Compute pyrefly search paths for a project."""
        rules = self.pyrefly_path_rules()
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
        local_dirs = [
            relative_path
            for relative_path in rules.env_dirs
            if (project_dir / relative_path).is_dir()
        ]
        paths: t.Infra.StrSet = {*typings_paths}
        if is_root and rules.include_path_dependencies_in_search_path:
            pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
            doc_result = u.Cli.toml_read_document(pyproject)
            if doc_result.is_success:
                paths.update(
                    self.get_dep_paths(
                        doc_result.value,
                        is_root=True,
                    ),
                )
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
        self: FlextInfraExtraPathsManager,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Build pyrefly project-includes from YAML rules and discovered dirs."""
        rules = self.pyrefly_path_rules()
        env_dirs = set(rules.env_dirs)
        includes: t.Infra.StrSet = set()
        local_dirs = set(FlextInfraUtilitiesDiscovery.discover_python_dirs(project_dir))
        includes.update(
            f"{directory}/**/*.py*" for directory in sorted(local_dirs & env_dirs)
        )
        if not is_root or (not rules.workspace_include_children):
            return sorted(includes)
        child_env_dirs = set(rules.workspace_include_child_env_dirs)
        for child in sorted(project_dir.iterdir()):
            if not child.is_dir():
                continue
            if not (child / c.Infra.Files.PYPROJECT_FILENAME).exists():
                continue
            child_dirs = set(FlextInfraUtilitiesDiscovery.discover_python_dirs(child))
            includes.update(
                f"{child.name}/{directory}/**/*.py*"
                for directory in sorted(child_dirs & child_env_dirs)
            )
        return sorted(includes)


__all__ = ["FlextInfraExtraPathsPyrefly"]
