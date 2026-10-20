"""Canonical Pyrefly target selection utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, config

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraUtilitiesPyrefly:
    """Own target selection shared by quality gates and refactor automation."""

    @staticmethod
    def pyrefly_target_args(
        project_dir: Path,
        discovered_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """Check every selected owned target with configured artifact exclusions.

        Pyrefly ignores the configured ``project-excludes`` whenever files are
        passed on the command line and reads them only from
        ``--project-excludes``. Explicit targets therefore carry the project's
        configured excludes, so a generated or vendored tree inside a target
        directory stays excluded exactly as in project-checking mode.

        Returns:
            The resulting ``t.StrSequence``.

        """
        parsed = u.Cli.toml_read_document(project_dir / c.PYPROJECT_FILENAME)
        document = parsed.value if parsed.success else None
        tool = (
            None if document is None else u.Cli.toml_table_child(document, c.Infra.TOOL)
        )
        pyrefly = (
            None if tool is None else u.Cli.toml_table_child(tool, c.Infra.PYREFLY)
        )
        excludes = (
            ()
            if pyrefly is None
            else u.Cli.toml_as_string_list(
                u.Cli.toml_item_child(pyrefly, c.Infra.PROJECT_EXCLUDES),
            )
        )
        return (
            *discovered_dirs,
            *(
                argument
                for glob in excludes
                for argument in (c.Infra.PYREFLY_PROJECT_EXCLUDES_FLAG, glob)
            ),
        )

    @staticmethod
    def pyrefly_project_excludes(declared_globs: t.StrSequence) -> t.StrSequence:
        """Compose Pyrefly exclusions with the shared analysis artifact catalog.

        Every analyzer consumes the same declared file and directory patterns,
        including foreign generated sources and ephemeral tool output.

        Returns:
            The sorted, deduplicated ``project-excludes`` values.

        """
        return sorted({*declared_globs, *config.Infra.codegen.analyzer_exclude_globs})


__all__: list[str] = ["FlextInfraUtilitiesPyrefly"]
