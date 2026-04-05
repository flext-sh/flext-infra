"""Pyrefly path computation helpers for extra_paths manager."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, p, t, u


class FlextInfraExtraPathsPyrefly:
    """Pyrefly search-path and project-includes computation."""

    def _resolver(self) -> p.Infra.ExtraPathsResolver:
        """Validate the owning object against the shared resolver contract."""
        if not isinstance(self, p.Infra.ExtraPathsResolver):
            msg = "FlextInfraExtraPathsPyrefly requires an ExtraPathsResolver owner"
            raise TypeError(msg)
        return self

    @staticmethod
    def _existing_relative_paths(
        project_dir: Path,
        configured_paths: t.StrSequence,
    ) -> t.StrSequence:
        existing: t.StrSequence = [
            relative_path
            for relative_path in configured_paths
            if (project_dir / relative_path).is_dir()
        ]
        return existing

    @staticmethod
    def _source_root(
        project_dir: Path,
        *,
        source_dir: str,
        project_root: str,
    ) -> str:
        if (project_dir / source_dir).is_dir():
            return source_dir
        return project_root

    def pyrefly_search_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Compute pyrefly search paths for a project."""
        resolver = self._resolver()
        rules = resolver.pyrefly_path_rules()
        source_root = self._source_root(
            project_dir,
            source_dir=rules.source_dir,
            project_root=rules.project_root,
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = self._existing_relative_paths(
            project_dir,
            configured_typings,
        )
        paths: t.Infra.StrSet = {source_root, *typings_paths}
        if is_root:
            local_dirs = self._existing_relative_paths(
                project_dir,
                rules.env_dirs,
            )
            paths.update(local_dirs)
            if rules.workspace_include_children:
                child_env_dirs = set(rules.workspace_include_child_env_dirs)
                for child in sorted(project_dir.iterdir()):
                    if not child.is_dir():
                        continue
                    if not (child / c.Infra.Files.PYPROJECT_FILENAME).exists():
                        continue
                    paths.add(child.name)
                    for env_dir in sorted(child_env_dirs):
                        child_env = child / env_dir
                        if child_env.is_dir():
                            paths.add(f"{child.name}/{env_dir}")
            return sorted(paths)
        if rules.include_path_dependencies_in_search_path:
            project_pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
            doc_result = u.Infra.read_document(project_pyproject)
            if doc_result.is_success:
                dep_paths = resolver.get_dep_paths(doc_result.value, is_root=False)
                paths.update(dep_paths)
        shared_paths = self._existing_relative_paths(
            project_dir,
            rules.project_shared_search_paths,
        )
        paths.update(shared_paths)
        paths.add(rules.project_root)
        return sorted(paths)

    def pyrefly_project_includes(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Build pyrefly project-includes from YAML rules and discovered dirs."""
        rules = self._resolver().pyrefly_path_rules()
        env_dirs = set(rules.env_dirs)
        includes: t.Infra.StrSet = set()
        local_dirs = set(u.Infra.discover_python_dirs(project_dir))
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
            child_dirs = set(u.Infra.discover_python_dirs(child))
            includes.update(
                f"{child.name}/{directory}/**/*.py*"
                for directory in sorted(child_dirs & child_env_dirs)
            )
        return sorted(includes)


__all__ = ["FlextInfraExtraPathsPyrefly"]
