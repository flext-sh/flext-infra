"""Migrate projects to unified FLEXT infrastructure."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

import tomlkit
from pydantic import JsonValue

from flext_infra import FlextInfraBaseMkGenerator, c, m, p, r, s, t, u


class FlextInfraProjectMigrator(s[Sequence[m.Infra.MigrationResult]]):
    """Migrate projects to standardized base.mk, Makefile, and pyproject structure."""

    def __init__(
        self,
        *,
        discovery: p.Infra.Discovery | None = None,
        generator: FlextInfraBaseMkGenerator | None = None,
    ) -> None:
        """Initialize migrator with optional custom discovery and generator services."""
        super().__init__()
        self._discovery = discovery
        self._generator = generator or FlextInfraBaseMkGenerator()

    @staticmethod
    def _action_text(action: str, *, dry_run: bool) -> str:
        return f"[DRY-RUN] {action}" if dry_run else action

    @staticmethod
    def _no_change_result(message: str, *, dry_run: bool) -> r[str]:
        """Return a no-op result: dry-run shows message, normal returns empty."""
        if dry_run:
            return r[str].ok(f"[DRY-RUN] {message}")
        return r[str].ok("")

    @staticmethod
    def _append_result(
        result: r[str],
        changes: MutableSequence[str],
        errors: MutableSequence[str],
    ) -> None:
        if result.is_failure:
            errors.append(result.error or "migration action failed")
            return
        val: str = result.value
        if val:
            changes.append(val)

    @staticmethod
    def _has_flext_core_dependency(document: tomlkit.TOMLDocument) -> bool:
        project = u.Infra.get_table(document, c.Infra.PROJECT)
        if project is not None:
            deps = u.Infra.get_item(project, c.Infra.DEPENDENCIES)
            if isinstance(deps, list):
                deps_list: Sequence[JsonValue] = (
                    t.Infra.JSON_SEQ_ADAPTER.validate_python([*deps])
                )
                for dep_raw in deps_list:
                    if str(dep_raw).strip().startswith(c.Infra.Packages.CORE):
                        return True
        tool = u.Infra.get_table(document, c.Infra.TOOL)
        if tool is None:
            return False
        poetry = u.Infra.get_table(tool, c.Infra.POETRY)
        if poetry is None:
            return False
        poetry_deps = u.Infra.get_table(poetry, c.Infra.DEPENDENCIES)
        if poetry_deps is None:
            return False
        return c.Infra.Packages.CORE in poetry_deps

    @staticmethod
    def _workspace_root_project(
        workspace_root: Path,
    ) -> m.Infra.ProjectInfo | None:
        """Detect workspace root as a project if it has Makefile, pyproject.toml, and .git."""
        has_makefile = (workspace_root / c.Infra.Files.MAKEFILE_FILENAME).is_file()
        has_pyproject = (workspace_root / c.Infra.Files.PYPROJECT_FILENAME).is_file()
        has_git = (workspace_root / c.Infra.Git.DIR).exists()
        if not (has_makefile and has_pyproject and has_git):
            return None
        return m.Infra.ProjectInfo(
            name=workspace_root.name,
            path=workspace_root,
            stack="python/workspace",
            has_tests=(workspace_root / c.Infra.Directories.TESTS).is_dir(),
            has_src=(workspace_root / c.Infra.Paths.DEFAULT_SRC_DIR).is_dir(),
        )

    @override
    def execute(self) -> r[Sequence[m.Infra.MigrationResult]]:
        return r[Sequence[m.Infra.MigrationResult]].fail(
            "Use migrate() method directly",
        )

    def migrate(
        self,
        *,
        workspace_root: Path,
        dry_run: bool = False,
    ) -> r[Sequence[m.Infra.MigrationResult]]:
        """Migrate all projects in workspace."""
        root = workspace_root.resolve()
        if not root.is_dir():
            return r[Sequence[m.Infra.MigrationResult]].fail(
                f"workspace root does not exist: {root}",
            )
        if self._discovery is not None:
            discovered = self._discovery.discover_projects(root)
        else:
            discovered = u.Infra.discover_projects(root)
        if discovered.is_failure:
            return r[Sequence[m.Infra.MigrationResult]].fail(
                discovered.error or "project discovery failed",
            )
        discovered_projects: Sequence[m.Infra.ProjectInfo] = discovered.value
        projects = list(discovered_projects)
        workspace_project = self._workspace_root_project(root)
        if workspace_project is not None and all(
            existing.path != workspace_project.path for existing in projects
        ):
            projects.append(workspace_project)
        results: Sequence[m.Infra.MigrationResult] = [
            self._migrate_project(
                project=project,
                dry_run=dry_run,
                workspace_root=root,
            )
            for project in projects
        ]
        return r[Sequence[m.Infra.MigrationResult]].ok(results)

    def _migrate_basemk(
        self,
        project_root: Path,
        *,
        dry_run: bool,
        is_workspace_root: bool = False,
    ) -> r[str]:
        _ = is_workspace_root
        target = project_root / c.Infra.Files.BASE_MK
        generated = self._generator.generate_basemk()
        if generated.is_failure:
            return r[str].fail(generated.error or "base.mk generation failed")
        generated_text: str = generated.value
        current = (
            target.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if target.exists()
            else ""
        )
        if u.Infra.sha256_content(current) == u.Infra.sha256_content(generated_text):
            if dry_run:
                return r[str].ok(
                    self._action_text("base.mk already up-to-date", dry_run=True),
                )
            return r[str].ok("")
        if not dry_run:
            try:
                u.write_file(target, generated_text, encoding=c.Infra.Encoding.DEFAULT)
            except OSError as exc:
                return r[str].fail(f"base.mk update failed: {exc}")
        return r[str].ok(
            self._action_text(
                "base.mk regenerated via BaseMkGenerator",
                dry_run=dry_run,
            ),
        )

    def _migrate_gitignore(self, project_root: Path, *, dry_run: bool) -> r[str]:
        gitignore_path = project_root / c.Infra.Files.GITIGNORE
        try:
            existing_lines = (
                gitignore_path.read_text(encoding=c.Infra.Encoding.DEFAULT).splitlines()
                if gitignore_path.exists()
                else list[str]()
            )
        except OSError as exc:
            return r[str].fail(f".gitignore read failed: {exc}")
        filtered = [
            line
            for line in existing_lines
            if line.strip() not in c.Infra.GITIGNORE_REMOVE_EXACT
        ]
        existing_patterns = {line.strip() for line in filtered if line.strip()}
        missing = [
            pattern
            for pattern in c.Infra.REQUIRED_GITIGNORE_ENTRIES
            if pattern not in existing_patterns
        ]
        if not missing and len(filtered) == len(existing_lines):
            if dry_run:
                return r[str].ok(
                    self._action_text(".gitignore already normalized", dry_run=True),
                )
            return r[str].ok("")
        next_lines = list(filtered)
        if missing:
            if next_lines and next_lines[-1].strip():
                next_lines.append("")
            next_lines.append(
                "# --- workspace-migrate: required ignores (auto-managed) ---",
            )
            next_lines.extend(missing)
        if not dry_run:
            body = "\n".join(next_lines).rstrip("\n") + "\n"
            try:
                u.write_file(gitignore_path, body, encoding=c.Infra.Encoding.DEFAULT)
            except OSError as exc:
                return r[str].fail(f".gitignore update failed: {exc}")
        return r[str].ok(
            self._action_text(
                ".gitignore cleaned from scripts/ and normalized",
                dry_run=dry_run,
            ),
        )

    def _migrate_makefile(self, project_root: Path, *, dry_run: bool) -> r[str]:
        makefile_path = project_root / c.Infra.Files.MAKEFILE_FILENAME
        if not makefile_path.exists():
            return self._no_change_result("Makefile not found", dry_run=dry_run)
        try:
            original = makefile_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except OSError as exc:
            return r[str].fail(f"Makefile read failed: {exc}")
        updated = original
        for before, after in c.Infra.MAKEFILE_REPLACEMENTS:
            updated = updated.replace(before, after)
        updated = self._apply_bootstrap_include(updated)
        if updated == original:
            return self._no_change_result("Makefile already migrated", dry_run=dry_run)
        if not dry_run:
            try:
                u.write_file(makefile_path, updated, encoding=c.Infra.Encoding.DEFAULT)
            except OSError as exc:
                return r[str].fail(f"Makefile update failed: {exc}")
        return r[str].ok(
            self._action_text(
                "Makefile migrated to bootstrap include",
                dry_run=dry_run,
            ),
        )

    def _apply_bootstrap_include(self, content: str) -> str:
        if c.Infra.MAKEFILE_INCLUDE_OLD not in content:
            return content
        bootstrap_result = self._generator.render_bootstrap_include()
        if bootstrap_result.is_failure:
            return content
        return content.replace(
            c.Infra.MAKEFILE_INCLUDE_OLD,
            bootstrap_result.value,
        )

    def _migrate_project(
        self,
        *,
        project: p.Infra.ProjectInfo,
        dry_run: bool,
        workspace_root: Path,
    ) -> m.Infra.MigrationResult:
        is_root = project.path.resolve() == workspace_root.resolve()
        changes: MutableSequence[str] = []
        errors: MutableSequence[str] = []
        self._append_result(
            self._migrate_basemk(
                project.path,
                dry_run=dry_run,
                is_workspace_root=is_root,
            ),
            changes,
            errors,
        )
        self._append_result(
            self._migrate_makefile(project.path, dry_run=dry_run),
            changes,
            errors,
        )
        self._append_result(
            self._migrate_pyproject(
                project.path,
                project_name=project.name,
                dry_run=dry_run,
            ),
            changes,
            errors,
        )
        self._append_result(
            self._migrate_gitignore(project.path, dry_run=dry_run),
            changes,
            errors,
        )
        if not changes and (not errors):
            changes.append("no changes needed")
        return m.Infra.MigrationResult(
            project=project.name,
            changes=changes,
            errors=errors,
        )

    def _migrate_pyproject(
        self,
        project_root: Path,
        *,
        project_name: str,
        dry_run: bool,
    ) -> r[str]:
        pyproject_path = project_root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject_path.exists():
            return self._no_change_result("pyproject.toml not found", dry_run=dry_run)
        if project_name == c.Infra.Packages.CORE:
            return self._no_change_result(
                "pyproject.toml dependency unchanged for flext-core",
                dry_run=dry_run,
            )
        document_result = u.Infra.read_document(pyproject_path)
        if document_result.is_failure:
            return r[str].fail(
                document_result.error or "pyproject parse failed",
            )
        document: tomlkit.TOMLDocument = document_result.value
        if self._has_flext_core_dependency(document):
            return self._no_change_result(
                "pyproject.toml already includes flext-core dependency",
                dry_run=dry_run,
            )
        return self._apply_flext_core_dependency(
            document, pyproject_path, dry_run=dry_run
        )

    def _apply_flext_core_dependency(
        self,
        document: tomlkit.TOMLDocument,
        pyproject_path: Path,
        *,
        dry_run: bool,
    ) -> r[str]:
        """Add flext-core dependency to the pyproject document and write if not dry-run."""
        project_table = u.Infra.ensure_table(document, c.Infra.PROJECT)
        dependencies_raw = u.Infra.get_item(project_table, c.Infra.DEPENDENCIES)
        dependencies: MutableSequence[str] = []
        if isinstance(dependencies_raw, list):
            dependency_items: Sequence[JsonValue] = (
                t.Infra.JSON_SEQ_ADAPTER.validate_python([*dependencies_raw])
            )
            dependencies = [str(dep_raw) for dep_raw in dependency_items]
        dependency_spec = c.Infra.Packages.CORE
        if dependency_spec not in dependencies:
            dependencies.append(dependency_spec)
        project_table[c.Infra.DEPENDENCIES] = dependencies
        if not dry_run:
            write_result = u.Infra.write_document(pyproject_path, document)
            if write_result.is_failure:
                return r[str].fail(
                    write_result.error or "pyproject update failed",
                )
        return r[str].ok(
            self._action_text(
                "pyproject.toml adds flext-core dependency",
                dry_run=dry_run,
            ),
        )


__all__ = ["FlextInfraProjectMigrator"]
