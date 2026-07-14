"""Cohesive doc-sync + transitive-dependency mixin for FlextInfraExtraPathsManager."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, p, t, u


class FlextInfraExtraPathsSyncMixin:
    """Mixin holding TOML doc-sync plus transitive-dependency path resolution."""

    if TYPE_CHECKING:
        # Provided by the concrete FlextInfraExtraPathsManager / its base; declared
        # for static resolution only so they don't shadow the runtime implementations.
        root: Path
        _workspace_project_dirs: t.MappingKV[str, Path]
        _workspace_project_names: t.Infra.StrSet
        pyright_extra_paths: Callable[..., t.StrSequence]

    def _resolve_transitive_deps(
        self, direct_names: t.StrSequence, *, visited: t.Infra.StrSet | None = None
    ) -> t.StrSequence:
        """Recursively resolve transitive workspace path dependencies."""
        resolved_visited: set[str] = visited if visited is not None else set()
        all_paths: set[str] = set(direct_names)
        for name in direct_names:
            if name in resolved_visited:
                continue
            resolved_visited.add(name)
            dep_dir = self._workspace_project_dirs.get(name)
            if dep_dir is None:
                continue
            # mro-wkii.17.26 (codex): transitive lookup uses the canonical
            # distribution-to-member map, never directory-name assumptions.
            dep_pyproject = dep_dir / c.Infra.PYPROJECT_FILENAME
            if not dep_pyproject.exists():
                continue
            dep_payload = u.Infra.pyproject_payload(dep_pyproject)
            transitive = u.Infra.local_runtime_dependency_names_from_payload(
                dep_payload,
                workspace_project_names=tuple(self._workspace_project_names),
            )
            if not transitive:
                continue
            all_paths.update(transitive)
            all_paths.update(
                self._resolve_transitive_deps(transitive, visited=resolved_visited)
            )
        return sorted(all_paths)

    def sync_doc(
        self, doc: t.Cli.TomlDocument, *, project_dir: Path, is_root: bool
    ) -> t.StrSequence:
        """Apply computed extra paths to an in-memory TOMLDocument."""
        # mro-j47u: compare immutable sequences so equal paths stay idempotent.
        expected = tuple(
            self.pyright_extra_paths(project_dir=project_dir, is_root=is_root)
        )
        tool_table = u.Cli.toml_table_child(doc, c.Infra.TOOL)
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_table_child(tool_table, c.Infra.PYRIGHT)
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_table_child(tool_table, c.Infra.MYPY)
        changes: t.MutableSequenceOf[str] = []
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
        self, payload: t.MutableJsonMapping, *, project_dir: Path, is_root: bool
    ) -> t.StrSequence:
        """Apply computed extra paths to one normalized TOML payload."""
        expected = self.pyright_extra_paths(project_dir=project_dir, is_root=is_root)
        tool_table = u.Cli.toml_mapping_child(payload, c.Infra.TOOL)
        if tool_table is None:
            return list[str]()
        pyright_table = u.Cli.toml_mapping_child(tool_table, c.Infra.PYRIGHT)
        if pyright_table is None:
            return list[str]()
        mypy_table = u.Cli.toml_mapping_child(tool_table, c.Infra.MYPY)
        changes: t.MutableSequenceOf[str] = []
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
        self, pyproject_path: Path, *, dry_run: bool = False, is_root: bool = False
    ) -> p.Result[bool]:
        """Synchronize pyright and mypy paths for one pyproject.toml."""
        if not pyproject_path.exists():
            return r[bool].fail(f"pyproject not found: {pyproject_path}")
        doc_result = u.Cli.toml_read_document(pyproject_path)
        if doc_result.failure:
            return r[bool].fail(doc_result.error or f"failed to read {pyproject_path}")
        changes = self.sync_doc(
            doc_result.value, project_dir=pyproject_path.parent, is_root=is_root
        )
        if changes and (not dry_run):
            write_result = u.Cli.toml_write_document(pyproject_path, doc_result.value)
            if write_result.failure:
                return r[bool].fail(
                    write_result.error or f"failed to write {pyproject_path}"
                )
        return r[bool].ok(bool(changes))

    def sync_extra_paths(
        self, *, dry_run: bool = False, project_dirs: t.SequenceOf[Path] | None = None
    ) -> p.Result[int]:
        """Synchronize extraPaths and mypy_path across projects."""
        if project_dirs:
            for project_dir in project_dirs:
                pyproject = project_dir / c.Infra.PYPROJECT_FILENAME
                sync_result = self.sync_one(
                    pyproject, dry_run=dry_run, is_root=project_dir == self.root
                )
                if sync_result.failure:
                    return r[int].fail(
                        sync_result.error or f"sync failed for {pyproject}"
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


__all__: list[str] = ["FlextInfraExtraPathsSyncMixin"]
