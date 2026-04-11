"""Path dependency resolution for extra paths manager."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesTomlParse,
    c,
    t,
)


class FlextInfraExtraPathsResolutionMixin:
    """Path dependency extraction and transitive resolution methods."""

    root: Path
    _workspace_project_names: t.Infra.StrSet

    @staticmethod
    def _normalize_pep621_path_dependency(path_part: str) -> str | None:
        """Return a normalized local path dependency or ``None`` for non-path refs."""
        normalized = path_part.strip()
        if not normalized:
            return None
        if normalized.startswith(("git+", "git@", "http://", "https://", "ssh://")):
            return None
        if "://" in normalized and not normalized.startswith("file://"):
            return None
        if normalized.startswith("file://"):
            normalized = normalized.removeprefix("file://").strip()
        elif normalized.startswith("file:"):
            normalized = normalized.removeprefix("file:").strip()
        elif not normalized.startswith(("./", "../", "/")):
            return None
        if normalized.startswith("./"):
            normalized = normalized[2:].strip()
        return normalized or None

    def _path_dependency_entries(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract local dependency paths declared across supported TOML sections."""
        paths: set[str] = set()
        project_table = u.Cli.toml_get_table(doc, c.Infra.PROJECT)
        if project_table is not None:
            for item in u.Cli.toml_as_string_list(
                u.Cli.toml_get_item(project_table, c.Infra.DEPENDENCIES)
            ):
                if " @ " not in item:
                    continue
                _name, path_part = item.split(" @ ", 1)
                normalized_path = self._normalize_pep621_path_dependency(path_part)
                if normalized_path is not None:
                    paths.add(normalized_path)
        tool_table = u.Cli.toml_get_table(doc, c.Infra.TOOL)
        if tool_table is None:
            return sorted(paths)
        poetry_table = u.Cli.toml_get_table(tool_table, c.Infra.POETRY)
        if poetry_table is not None:
            deps_table = u.Cli.toml_get_table(poetry_table, c.Infra.DEPENDENCIES)
            if deps_table is not None:
                for dep_key in deps_table:
                    dep_table = u.Cli.toml_get_table(deps_table, dep_key)
                    if dep_table is None:
                        continue
                    dep_path = u.Cli.toml_unwrap_item(
                        u.Cli.toml_get_item(dep_table, c.Infra.PATH),
                    )
                    if isinstance(dep_path, str) and dep_path:
                        normalized_path = dep_path.strip().removeprefix("./").strip()
                        if normalized_path:
                            paths.add(normalized_path)
        uv_table = u.Cli.toml_get_table(tool_table, "uv")
        sources_table = (
            u.Cli.toml_get_table(uv_table, "sources") if uv_table is not None else None
        )
        if sources_table is None:
            return sorted(paths)
        project_deps: t.StrSequence = (
            u.Cli.toml_as_string_list(
                u.Cli.toml_get_item(project_table, c.Infra.DEPENDENCIES)
            )
            if project_table is not None
            else []
        )
        project_dep_names: t.Infra.StrSet = set()
        for dep_entry in project_deps:
            dep_name = FlextInfraUtilitiesTomlParse.dep_name(dep_entry)
            if dep_name:
                project_dep_names.add(dep_name)
        for source_key in sources_table:
            dep_name = str(source_key)
            if project_dep_names and dep_name not in project_dep_names:
                continue
            source_table = u.Cli.toml_get_table(sources_table, dep_name)
            if source_table is None:
                continue
            workspace_val = u.Cli.toml_unwrap_item(
                u.Cli.toml_get_item(source_table, "workspace"),
            )
            if workspace_val is True:
                paths.add(dep_name)
                continue
            source_path = u.Cli.toml_unwrap_item(
                u.Cli.toml_get_item(source_table, c.Infra.PATH),
            )
            if isinstance(source_path, str):
                normalized_path = source_path.strip().removeprefix("./")
                if normalized_path:
                    paths.add(normalized_path)
        return sorted(paths)

    def _dependency_entries(self, doc: t.Cli.TomlDocument) -> t.StrSequence:
        declared_names = FlextInfraUtilitiesTomlParse.declared_dependency_names(doc)
        return sorted(
            {
                *self._path_dependency_entries(doc),
                *(
                    name
                    for name in declared_names
                    if name in self._workspace_project_names
                ),
            },
        )

    def _resolve_transitive_deps(
        self,
        direct_paths: t.StrSequence,
        *,
        visited: t.Infra.StrSet | None = None,
    ) -> t.StrSequence:
        """Recursively resolve transitive path dependencies.

        For each direct dep, reads its pyproject.toml and collects its
        path deps too, with cycle detection.
        """
        resolved_visited: set[str] = visited if visited is not None else set()
        all_paths: set[str] = set(direct_paths)
        for path_value in direct_paths:
            name = FlextInfraUtilitiesTomlParse.dep_name(path_value)
            if not name:
                continue
            if name in resolved_visited:
                continue
            resolved_visited.add(name)
            dep_pyproject = self.root / name / c.Infra.Files.PYPROJECT_FILENAME
            if not dep_pyproject.exists():
                continue
            dep_doc_result = u.Cli.toml_read_document(dep_pyproject)
            if dep_doc_result.is_failure:
                continue
            dep_doc: t.Cli.TomlDocument = dep_doc_result.value
            transitive = self._dependency_entries(dep_doc)
            if transitive:
                all_paths.update(transitive)
                deeper = self._resolve_transitive_deps(
                    transitive,
                    visited=resolved_visited,
                )
                all_paths.update(deeper)
        return sorted(all_paths)

    def get_dep_paths(
        self,
        doc: t.Cli.TomlDocument,
        *,
        is_root: bool = False,
    ) -> t.StrSequence:
        """Resolve path dependencies to all Python directory paths dynamically.

        Scans each dependency for directories containing Python files
        (not just src/) and includes all of them in extraPaths.
        Resolves transitive dependencies automatically.
        """
        dep_skip = c.Infra.Excluded.COMMON_EXCLUDED_DIRS | frozenset({
            c.Infra.Directories.TESTS
        })
        project_table = u.Cli.toml_get_table(doc, c.Infra.PROJECT)
        current_project_name = (
            u.Cli.toml_unwrap_item(u.Cli.toml_get_item(project_table, c.Infra.NAME))
            if project_table is not None
            else None
        )
        raw_paths = self._resolve_transitive_deps(self._dependency_entries(doc))
        resolved: MutableSequence[str] = []
        for path_value in raw_paths:
            if not path_value:
                continue
            name = FlextInfraUtilitiesTomlParse.dep_name(path_value)
            if not name:
                continue
            if isinstance(current_project_name, str) and name == current_project_name:
                continue
            prefix = f"{name}" if is_root else f"../{name}"
            dep_dir = self.root / name
            if dep_dir.is_dir():
                py_dirs = FlextInfraUtilitiesDiscovery.discover_python_dirs(
                    dep_dir, skip_dirs=dep_skip
                )
                for dir_name in py_dirs:
                    resolved.append(f"{prefix}/{dir_name}")
            else:
                resolved.append(f"{prefix}/src")
        return resolved


__all__ = ["FlextInfraExtraPathsResolutionMixin"]
