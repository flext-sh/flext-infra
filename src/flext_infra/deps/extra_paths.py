"""Synchronize pyright, mypy, and pyrefly paths from workspace dependencies.

Handlers are called by the canonical CLI via FlextInfraCliDeps.register_deps.
"""

from __future__ import annotations

from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import override

from tomlkit.toml_document import TOMLDocument

from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraExtraPathsManager(FlextInfraProjectSelectionServiceBase[bool]):
    """Manager for synchronizing type-checker search paths from dependencies."""

    _tool_config: m.Infra.ToolConfigDocument = u.PrivateAttr()
    _workspace_project_names: t.Infra.StrSet = u.PrivateAttr(default_factory=set)

    @override
    def model_post_init(self, __context: object, /) -> None:
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

    def _resolve_transitive_deps(
        self,
        direct_names: t.StrSequence,
        *,
        visited: t.Infra.StrSet | None = None,
    ) -> t.StrSequence:
        """Recursively resolve transitive workspace path dependencies."""
        resolved_visited: set[str] = visited if visited is not None else set()
        all_paths: set[str] = set(direct_names)
        for name in direct_names:
            if name in resolved_visited:
                continue
            resolved_visited.add(name)
            dep_pyproject = self.root / name / c.Infra.PYPROJECT_FILENAME
            if not dep_pyproject.exists():
                continue
            dep_payload = u.Infra.pyproject_payload(
                dep_pyproject,
            )
            transitive = u.Infra.local_dependency_names_from_payload(
                dep_payload,
                workspace_project_names=tuple(self._workspace_project_names),
            )
            if not transitive:
                continue
            all_paths.update(transitive)
            all_paths.update(
                self._resolve_transitive_deps(
                    transitive,
                    visited=resolved_visited,
                )
            )
        return sorted(all_paths)

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
        resolved: MutableSequence[str] = []
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

    def sync_doc(
        self,
        doc: TOMLDocument,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Apply computed extra paths to an in-memory TOMLDocument."""
        expected = self.pyright_extra_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        tool_table = u.Cli.toml_table_child(doc, c.Infra.TOOL)
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_table_child(tool_table, c.Infra.PYRIGHT)
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_table_child(tool_table, c.Infra.MYPY)
        changes: MutableSequence[str] = []
        pyright_extra_paths = u.Cli.toml_item_child(pyright_table, "extraPaths")
        current_pyright = u.Cli.toml_as_string_list(
            pyright_extra_paths if pyright_extra_paths is not None else []
        )
        if current_pyright != expected:
            pyright_table["extraPaths"] = expected
            changes.append("synchronized pyright extraPaths")
        if mypy_table is not None:
            mypy_path_item = u.Cli.toml_item_child(mypy_table, "mypy_path")
            current_mypy = u.Cli.toml_as_string_list(
                mypy_path_item if mypy_path_item is not None else []
            )
            if current_mypy != expected:
                mypy_table["mypy_path"] = expected
                tool_table[c.Infra.MYPY] = mypy_table
                changes.append("synchronized mypy mypy_path")
        if changes:
            tool_table[c.Infra.PYRIGHT] = pyright_table
            doc["tool"] = tool_table
        return changes

    def sync_payload(
        self,
        payload: MutableMapping[str, t.JsonValue],
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        """Apply computed extra paths to one normalized TOML payload."""
        expected = self.pyright_extra_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        tool_table = u.Cli.toml_mapping_child(payload, c.Infra.TOOL)
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_mapping_child(tool_table, c.Infra.PYRIGHT)
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_mapping_child(tool_table, c.Infra.MYPY)
        changes: MutableSequence[str] = []
        if u.Cli.toml_mapping_sync_string_list(
            u.Cli.toml_mapping_ensure_path(payload, (c.Infra.TOOL, c.Infra.PYRIGHT)),
            "extraPaths",
            expected,
        ):
            changes.append("synchronized pyright extraPaths")
        if mypy_table is not None and u.Cli.toml_mapping_sync_string_list(
            u.Cli.toml_mapping_ensure_path(payload, (c.Infra.TOOL, c.Infra.MYPY)),
            "mypy_path",
            expected,
        ):
            changes.append("synchronized mypy mypy_path")
        return changes

    def sync_one(
        self,
        pyproject_path: Path,
        *,
        dry_run: bool = False,
        is_root: bool = False,
    ) -> p.Result[bool]:
        """Synchronize pyright and mypy paths for one pyproject.toml."""
        if not pyproject_path.exists():
            return r[bool].fail(f"pyproject not found: {pyproject_path}")
        doc_result = u.Cli.toml_read_document(pyproject_path)
        if doc_result.failure:
            return r[bool].fail(doc_result.error or f"failed to read {pyproject_path}")
        changes = self.sync_doc(
            doc_result.value,
            project_dir=pyproject_path.parent,
            is_root=is_root,
        )
        if changes and (not dry_run):
            write_result = u.Cli.toml_write_document(pyproject_path, doc_result.value)
            if write_result.failure:
                return r[bool].fail(
                    write_result.error or f"failed to write {pyproject_path}",
                )
        return r[bool].ok(bool(changes))

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
        local_dirs = [
            directory
            for directory in u.Infra.discover_python_dirs(project_dir)
            if not is_root
            or not (project_dir / directory / c.Infra.PYPROJECT_FILENAME).is_file()
        ]
        paths: t.Infra.StrSet = {*typings_paths}
        if rules.include_path_dependencies_in_search_path:
            pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
            if pyproject.exists():
                payload = u.Infra.pyproject_payload(
                    pyproject,
                )
                paths.update(self._dep_paths(payload, is_root=is_root))
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

    def sync_extra_paths(
        self,
        *,
        dry_run: bool = False,
        project_dirs: Sequence[Path] | None = None,
    ) -> p.Result[int]:
        """Synchronize extraPaths and mypy_path across projects."""
        if project_dirs:
            for project_dir in project_dirs:
                pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
                sync_result = self.sync_one(
                    pyproject,
                    dry_run=dry_run,
                    is_root=project_dir == self.root,
                )
                if sync_result.failure:
                    return r[int].fail(
                        sync_result.error or f"sync failed for {pyproject}",
                    )
                if sync_result.value and (not dry_run):
                    u.Cli.info(f"Updated {pyproject}")
            return r[int].ok(0)
        pyproject = self.root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[int].fail(f"Missing {pyproject}")
        sync_result = self.sync_one(pyproject, dry_run=dry_run, is_root=True)
        if sync_result.failure:
            return r[int].fail(sync_result.error or f"sync failed for {pyproject}")
        if sync_result.value and (not dry_run):
            u.Cli.info("Updated extraPaths and mypy_path from path dependencies.")
        return r[int].ok(0)


__all__: list[str] = ["FlextInfraExtraPathsManager"]
