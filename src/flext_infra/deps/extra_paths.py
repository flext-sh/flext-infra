"""Synchronize pyright and mypy extraPaths from path dependencies."""

from __future__ import annotations

import sys
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
from tomlkit.items import Item, Table
from tomlkit.toml_document import TOMLDocument

from flext_infra import FlextInfraDependencyPathSync, c, m, r, t, u


class FlextInfraExtraPathsManager:
    """Manager for synchronizing pyright and mypy extraPaths from path dependencies."""

    ROOT = u.Infra.resolve_workspace_root(__file__)
    _STRING_LIST_ADAPTER: TypeAdapter[t.StrSequence] = TypeAdapter(t.StrSequence)

    def __init__(self, workspace_root: Path | None = None) -> None:
        """Initialize the extra paths manager with path resolver and TOML service."""
        super().__init__()
        self.root = workspace_root or self.ROOT
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.is_failure:
            msg = tool_config_result.error or "failed to load deps tool config"
            raise ValueError(msg)
        self._tool_config: m.Infra.ToolConfigDocument = tool_config_result.value

    @staticmethod
    def _table_get(container: TOMLDocument | Table, key: str) -> Item | None:
        if key not in container:
            return None
        raw_item = container[key]
        if isinstance(raw_item, Item):
            return raw_item
        return None

    @staticmethod
    def _as_table(value: Item | None) -> Table | None:
        if not isinstance(value, Table):
            return None
        return value

    @staticmethod
    def _as_string_list(value: Item | None) -> t.StrSequence:
        """Normalize sequence-like values to a list of strings."""
        if value is None or isinstance(value, str):
            return []
        if not isinstance(value, list):
            return []
        try:
            return FlextInfraExtraPathsManager._STRING_LIST_ADAPTER.validate_python(
                [*value],
            )
        except ValidationError:
            return []

    def path_dep_paths_pep621(self, doc: TOMLDocument) -> t.StrSequence:
        """Extract path dependency paths from PEP 621 project.dependencies."""
        project_table = self._as_table(self._table_get(doc, c.Infra.Toml.PROJECT))
        if project_table is None:
            return []
        deps_list = self._table_get(project_table, c.Infra.Toml.DEPENDENCIES)
        deps_items = self._as_string_list(deps_list)
        paths: MutableSequence[str] = []
        for item in deps_items:
            if " @ " not in item:
                continue
            _name, path_part = item.split(" @ ", 1)
            path_part = path_part.strip()
            if path_part.startswith("file:"):
                path_part = path_part[5:].strip()
            if path_part.startswith("./"):
                path_part = path_part[2:].strip()
            if path_part:
                paths.append(path_part)
        return sorted(set(paths))

    def path_dep_paths_poetry(self, doc: TOMLDocument) -> t.StrSequence:
        """Extract path dependency paths from Poetry tool.poetry.dependencies."""
        tool_table = self._as_table(self._table_get(doc, c.Infra.Toml.TOOL))
        if tool_table is None:
            return []
        poetry_table = self._as_table(self._table_get(tool_table, c.Infra.Toml.POETRY))
        if poetry_table is None:
            return []
        deps_table = self._as_table(
            self._table_get(poetry_table, c.Infra.Toml.DEPENDENCIES),
        )
        if deps_table is None:
            return []
        paths: MutableSequence[str] = []
        for dep_key in deps_table:
            dep_table = self._as_table(self._table_get(deps_table, dep_key))
            if dep_table is None:
                continue
            dep_path = self._table_get(dep_table, c.Infra.Toml.PATH)
            if isinstance(dep_path, str) and dep_path:
                dep_path = dep_path.strip()
                if dep_path.startswith("./"):
                    dep_path = dep_path[2:].strip()
                if dep_path:
                    paths.append(dep_path)
        return sorted(set(paths))

    def path_dep_paths(self, doc: TOMLDocument) -> t.StrSequence:
        """Combine PEP 621 and Poetry path dependencies."""
        return sorted(
            {*self.path_dep_paths_pep621(doc), *self.path_dep_paths_poetry(doc)},
        )

    def _resolve_transitive_deps(
        self,
        direct_paths: t.StrSequence,
        *,
        visited: set[str] | None = None,
    ) -> t.StrSequence:
        """Recursively resolve transitive path dependencies.

        For each direct dep, reads its pyproject.toml and collects its
        path deps too, with cycle detection.
        """
        if visited is None:
            visited = set()
        all_paths: set[str] = set(direct_paths)
        for path_value in direct_paths:
            name = FlextInfraDependencyPathSync.extract_dep_name(path_value)
            if name in visited:
                continue
            visited.add(name)
            dep_pyproject = self.root / name / c.Infra.Files.PYPROJECT_FILENAME
            if not dep_pyproject.exists():
                continue
            dep_doc_result = u.Infra.read_document(dep_pyproject)
            if dep_doc_result.is_failure:
                continue
            dep_doc: TOMLDocument = dep_doc_result.value
            transitive = self.path_dep_paths(dep_doc)
            if transitive:
                all_paths.update(transitive)
                deeper = self._resolve_transitive_deps(
                    transitive,
                    visited=visited,
                )
                all_paths.update(deeper)
        return sorted(all_paths)

    def get_dep_paths(
        self,
        doc: TOMLDocument,
        *,
        is_root: bool = False,
    ) -> t.StrSequence:
        """Resolve path dependencies to all Python directory paths dynamically.

        Scans each dependency for directories containing Python files
        (not just src/) and includes all of them in extraPaths.
        Resolves transitive dependencies automatically.
        """
        raw_paths = self._resolve_transitive_deps(self.path_dep_paths(doc))
        resolved: MutableSequence[str] = []
        for path_value in raw_paths:
            if not path_value:
                continue
            name = FlextInfraDependencyPathSync.extract_dep_name(path_value)
            prefix = f"{name}" if is_root else f"../{name}"

            # Dynamically discover all directories with Python files
            dep_dir = self.root / name
            if dep_dir.is_dir():
                for subdir in sorted(dep_dir.iterdir()):
                    if not subdir.is_dir():
                        continue
                    if subdir.name.startswith(".") or subdir.name in {
                        "__pycache__",
                        "node_modules",
                        "vendor",
                        "build",
                        "dist",
                        ".venv",
                        "tests",
                    }:
                        continue
                    # Check if this directory contains Python files
                    has_py = any(subdir.rglob("*.py"))
                    if has_py:
                        resolved.append(f"{prefix}/{subdir.name}")
            else:
                # Fallback: just add src/ if directory doesn't exist
                resolved.append(f"{prefix}/src")
        return resolved

    @staticmethod
    def _discover_local_python_dirs(project_dir: Path) -> t.StrSequence:
        """Dynamically discover directories with Python files in a project.

        Delegates to the SSOT discovery in u.Infra.
        """
        return u.Infra.discover_python_dirs(project_dir)

    @staticmethod
    def _existing_relative_paths(
        project_dir: Path,
        configured_paths: t.StrSequence,
    ) -> t.StrSequence:
        existing: MutableSequence[str] = []
        for relative_path in configured_paths:
            if (project_dir / relative_path).is_dir():
                existing.append(relative_path)
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

    def _pyright_path_rules(self) -> m.Infra.PyrightConfig.PathRulesConfig:
        return self._tool_config.tools.pyright.path_rules

    def _pyrefly_path_rules(self) -> m.Infra.PyreflyConfig.PathRulesConfig:
        return self._tool_config.tools.pyrefly.path_rules

    def pyright_extra_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        rules = self._pyright_path_rules()
        source_root = self._source_root(
            project_dir,
            source_dir=rules.source_dir,
            project_root=rules.project_root,
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = self._existing_relative_paths(project_dir, configured_typings)
        return sorted({rules.project_root, source_root, *typings_paths})

    def mypy_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        rules = self._pyright_path_rules()
        source_root = self._source_root(
            project_dir,
            source_dir=rules.source_dir,
            project_root=rules.project_root,
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = self._existing_relative_paths(project_dir, configured_typings)
        return sorted({rules.project_root, source_root, *typings_paths})

    def pyrefly_search_paths(
        self,
        *,
        project_dir: Path,
        is_root: bool,
    ) -> t.StrSequence:
        rules = self._pyrefly_path_rules()
        source_root = self._source_root(
            project_dir,
            source_dir=rules.source_dir,
            project_root=rules.project_root,
        )
        configured_typings = (
            rules.root_typings_paths if is_root else rules.project_typings_paths
        )
        typings_paths = self._existing_relative_paths(project_dir, configured_typings)
        paths: set[str] = {rules.project_root, source_root, *typings_paths}
        if is_root:
            for child in sorted(project_dir.iterdir()):
                if not child.is_dir():
                    continue
                if not (child / c.Infra.Files.PYPROJECT_FILENAME).exists():
                    continue
                paths.add(child.name)
                child_source = child / rules.source_dir
                if child_source.is_dir():
                    paths.add(f"{child.name}/{rules.source_dir}")
        return sorted(paths)

    def sync_one(
        self,
        pyproject_path: Path,
        *,
        dry_run: bool = False,
        is_root: bool = False,
    ) -> r[bool]:
        """Synchronize pyright and mypy paths for single pyproject.toml."""
        if not pyproject_path.exists():
            return r[bool].fail(f"pyproject not found: {pyproject_path}")
        doc_result = u.Infra.read_document(pyproject_path)
        if doc_result.is_failure:
            return r[bool].fail(doc_result.error or f"failed to read {pyproject_path}")
        doc: TOMLDocument = doc_result.value
        project_dir = pyproject_path.parent
        pyright_extra = self.pyright_extra_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        mypy_path = self.mypy_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        tool_table = self._as_table(self._table_get(doc, c.Infra.Toml.TOOL))
        if tool_table is None:
            return r[bool].fail(f"no [tool] section in {pyproject_path}")
        pyright_table = self._as_table(
            self._table_get(tool_table, c.Infra.Toml.PYRIGHT),
        )
        if pyright_table is None:
            return r[bool].fail(f"no [tool.pyright] section in {pyproject_path}")
        mypy_table = self._as_table(self._table_get(tool_table, c.Infra.Toml.MYPY))
        self._as_table(
            self._table_get(tool_table, c.Infra.Toml.PYREFLY),
        )
        changed = False
        current_pyright = self._as_string_list(
            self._table_get(pyright_table, "extraPaths"),
        )
        if current_pyright != pyright_extra:
            pyright_table["extraPaths"] = pyright_extra
            changed = True
        if mypy_table is not None:
            current_mypy = self._as_string_list(
                self._table_get(mypy_table, "mypy_path"),
            )
            if current_mypy != mypy_path:
                mypy_table["mypy_path"] = mypy_path
                tool_table[c.Infra.Toml.MYPY] = mypy_table
                changed = True
        # NOTE: pyrefly search-path is handled by FlextInfraEnsurePyreflyConfigPhase (SSOT).
        if changed:
            tool_table[c.Infra.Toml.PYRIGHT] = pyright_table
            doc[c.Infra.Toml.TOOL] = tool_table
        if changed and (not dry_run):
            write_result = u.Infra.write_document(pyproject_path, doc)
            if write_result.is_failure:
                return r[bool].fail(
                    write_result.error or f"failed to write {pyproject_path}",
                )
        return r[bool].ok(changed)

    def sync_doc(
        self,
        doc: TOMLDocument,
        *,
        project_dir: Path,
        is_root: bool = False,
    ) -> t.StrSequence:
        """Synchronize extra paths on an in-memory TOMLDocument.

        Used by FlextInfraEnsureExtraPathsPhase to modify the doc in-place
        without reading/writing to disk (avoiding overwrite by modernizer).

        Returns:
            List of change descriptions.

        """
        changes: MutableSequence[str] = []
        pyright_extra = self.pyright_extra_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        mypy_path = self.mypy_paths(
            project_dir=project_dir,
            is_root=is_root,
        )
        tool_table = self._as_table(self._table_get(doc, c.Infra.Toml.TOOL))
        if tool_table is None:
            return changes
        pyright_table = self._as_table(
            self._table_get(tool_table, c.Infra.Toml.PYRIGHT),
        )
        if pyright_table is None:
            return changes
        mypy_table = self._as_table(self._table_get(tool_table, c.Infra.Toml.MYPY))
        self._as_table(
            self._table_get(tool_table, c.Infra.Toml.PYREFLY),
        )
        current_pyright = self._as_string_list(
            self._table_get(pyright_table, "extraPaths"),
        )
        if current_pyright != pyright_extra:
            pyright_table["extraPaths"] = pyright_extra
            changes.append("synchronized pyright extraPaths")
        if mypy_table is not None:
            current_mypy = self._as_string_list(
                self._table_get(mypy_table, "mypy_path"),
            )
            if current_mypy != mypy_path:
                mypy_table["mypy_path"] = mypy_path
                tool_table[c.Infra.Toml.MYPY] = mypy_table
                changes.append("synchronized mypy mypy_path")
        # NOTE: pyrefly search-path is handled by FlextInfraEnsurePyreflyConfigPhase (SSOT).
        if changes:
            tool_table[c.Infra.Toml.PYRIGHT] = pyright_table
            doc[c.Infra.Toml.TOOL] = tool_table
        return changes

    def sync_extra_paths(
        self,
        *,
        dry_run: bool = False,
        project_dirs: Sequence[Path] | None = None,
    ) -> r[int]:
        """Synchronize extraPaths and mypy_path across projects."""
        if project_dirs:
            for project_dir in project_dirs:
                pyproject = project_dir / c.Infra.Files.PYPROJECT_FILENAME
                sync_result = self.sync_one(
                    pyproject,
                    dry_run=dry_run,
                    is_root=project_dir == self.root,
                )
                if sync_result.is_failure:
                    return r[int].fail(
                        sync_result.error or f"sync failed for {pyproject}",
                    )
                if sync_result.value and (not dry_run):
                    u.Infra.info(f"Updated {pyproject}")
            return r[int].ok(0)
        pyproject = self.root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[int].fail(f"Missing {pyproject}")
        sync_result = self.sync_one(pyproject, dry_run=dry_run, is_root=True)
        if sync_result.is_failure:
            return r[int].fail(sync_result.error or f"sync failed for {pyproject}")
        if sync_result.value and (not dry_run):
            u.Infra.info("Updated extraPaths and mypy_path from path dependencies.")
        return r[int].ok(0)

    @staticmethod
    def _resolve_project_dirs(cli: u.Infra.CliArgs) -> Sequence[Path] | None:
        return cli.project_dirs()

    @staticmethod
    def main(argv: t.StrSequence | None = None) -> int:
        """Execute extra paths synchronization from command line."""
        parser = u.Infra.create_parser(
            "flext-infra deps extra-paths",
            "Synchronize pyright and mypy extraPaths from path dependencies",
            include_apply=True,
            include_project=True,
        )
        args = parser.parse_args(argv)
        cli = u.Infra.resolve(args)
        manager = FlextInfraExtraPathsManager(workspace_root=cli.workspace)
        project_dirs = FlextInfraExtraPathsManager._resolve_project_dirs(cli)
        result = manager.sync_extra_paths(
            dry_run=cli.dry_run,
            project_dirs=project_dirs,
        )
        if result.is_success:
            return result.value
        u.Infra.error(result.error or "sync failed")
        return 1


main = FlextInfraExtraPathsManager.main


if __name__ == "__main__":
    sys.exit(FlextInfraExtraPathsManager.main())


__all__ = [
    "FlextInfraExtraPathsManager",
]
