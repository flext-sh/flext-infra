"""Per-project pyproject.toml flext-core dependency migration — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra.constants import c
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraProjectMigratorPyprojectMixin:
    """Ensure a project's pyproject.toml declares the flext-core dependency.

    Composed into FlextInfraProjectMigrator via inheritance; borrows the
    ``_no_change_result``/``_action_text`` helpers from the artifacts mixin via
    MRO.
    """

    if TYPE_CHECKING:

        @staticmethod
        def _no_change_result(message: str, *, dry_run: bool) -> p.Result[str]: ...
        @staticmethod
        def _action_text(action: str, *, dry_run: bool) -> str: ...

    def _migrate_pyproject(
        self,
        project_root: Path,
        *,
        project_name: str,
        dry_run: bool,
    ) -> p.Result[str]:
        """Migrate pyproject."""
        pyproject_path = project_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject_path.exists():
            return self._no_change_result("pyproject.toml not found", dry_run=dry_run)
        if project_name == c.Infra.PKG_CORE:
            return self._no_change_result(
                "pyproject.toml dependency unchanged for flext-core",
                dry_run=dry_run,
            )
        document_result = u.Cli.toml_read_document(pyproject_path)
        if document_result.failure:
            return r[str].fail(
                document_result.error or "pyproject parse failed",
            )
        document: t.Cli.TomlDocument = document_result.value
        if c.Infra.PKG_CORE in u.Infra.declared_dependency_names(document):
            return self._no_change_result(
                "pyproject.toml already includes flext-core dependency",
                dry_run=dry_run,
            )
        return self._apply_flext_core_dependency(
            document, pyproject_path, dry_run=dry_run
        )

    def _apply_flext_core_dependency(
        self,
        document: t.Cli.TomlDocument,
        pyproject_path: Path,
        *,
        dry_run: bool,
    ) -> p.Result[str]:
        """Add flext-core dependency to the pyproject document and write if not dry-run."""
        project_table = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        dependencies_item = u.Cli.toml_item_child(project_table, c.Infra.DEPENDENCIES)
        dependencies = list(
            u.Cli.toml_as_string_list(
                dependencies_item if dependencies_item is not None else [],
            ),
        )
        dependency_spec = c.Infra.PKG_CORE
        if dependency_spec not in dependencies:
            dependencies.append(dependency_spec)
        project_table[c.Infra.DEPENDENCIES] = dependencies
        if not dry_run:
            write_result = u.Cli.toml_write_document(pyproject_path, document)
            if write_result.failure:
                return r[str].fail(
                    write_result.error or "pyproject update failed",
                )
        return r[str].ok(
            self._action_text(
                "pyproject.toml adds flext-core dependency",
                dry_run=dry_run,
            ),
        )


__all__: list[str] = ["FlextInfraProjectMigratorPyprojectMixin"]
