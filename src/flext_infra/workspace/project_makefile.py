"""Project Makefile generator for workspace sync.

Fully generates project Makefiles from pyproject.toml metadata and the
base bootstrap template. Custom targets live in ``custom.mk`` alongside
the generated ``Makefile``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_core import p, r
from flext_infra import FlextInfraBaseMkGenerator, FlextInfraUtilitiesDocsScope, c, m, u


class FlextInfraProjectMakefileUpdater:
    """Fully generate project Makefiles from pyproject.toml metadata.

    The generated ``Makefile`` is 100% managed — do not edit it.  Put any
    project-specific Make targets in ``custom.mk`` next to the ``Makefile``;
    it is automatically included via ``-include custom.mk`` at the end.

    Idempotency:
      - SHA-256 comparison skips the write if the generated content is
        identical to the file already on disk.
    """

    def update(self, project_root: Path, *, canonical_root: Path) -> p.Result[bool]:
        """Regenerate project Makefile from pyproject.toml.

        Args:
            project_root: Root directory of the project.
            canonical_root: Workspace canonical root (reserved for future use).

        Returns:
            r with True if Makefile was written, False if unchanged,
            failure with error message on I/O or parse error.

        """
        _ = canonical_root  # reserved for future cross-project dependency resolution
        pyproject = project_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[bool].ok(False)

        meta_result = self._read_pyproject(pyproject)
        if meta_result.failure:
            return r[bool].fail(meta_result.error or "pyproject.toml parse failed")
        meta = meta_result.value

        bootstrap_result = FlextInfraBaseMkGenerator.render_bootstrap_include()
        if bootstrap_result.failure:
            return r[bool].fail(
                bootstrap_result.error or "bootstrap template read failed",
            )
        bootstrap = bootstrap_result.value

        new_content = self._build_makefile(meta, bootstrap)
        makefile_path = project_root / c.Infra.MAKEFILE_FILENAME

        if makefile_path.exists():
            try:
                existing = makefile_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            except OSError as exc:
                return r[bool].fail(f"Makefile read failed: {exc}")

            if u.Cli.sha256_content(existing) == u.Cli.sha256_content(new_content):
                return r[bool].ok(False)

        return u.Cli.atomic_write_text_file(makefile_path, new_content)

    @staticmethod
    def _read_pyproject(pyproject: Path) -> p.Result[m.Infra.ProjectMeta]:
        """Parse pyproject.toml and extract name, python_version, description."""
        project_state = FlextInfraUtilitiesDocsScope.project_state(pyproject.parent)
        data = project_state.payload
        if not data:
            data_result = u.Infra.read_plain(pyproject)
            if data_result.failure:
                return r[m.Infra.ProjectMeta].fail(
                    f"pyproject.toml read failed: {data_result.error}",
                )
            data = data_result.value

        try:
            project = data["project"]
            if not isinstance(project, dict):
                msg = "project table is not a mapping"
                raise KeyError(msg)
            name_raw = project["name"]
            if not isinstance(name_raw, str):
                msg = "project.name is not a string"
                raise KeyError(msg)
            name: str = name_raw
            requires_python_raw = project.get("requires-python", ">=3.13")
            requires_python = (
                requires_python_raw
                if isinstance(requires_python_raw, str)
                else ">=3.13"
            )
            # Extract "3.13" from ">=3.13,<3.14" or ">=3.13"
            version_str = requires_python.lstrip(">= ")
            python_version = version_str.split(",")[0].split("<")[0].strip()
            description_raw = project.get("description", "")
            description: str = (
                description_raw if isinstance(description_raw, str) else ""
            )
        except KeyError as exc:
            return r[m.Infra.ProjectMeta].fail(
                f"pyproject.toml missing required fields: {exc}",
            )

        return r[m.Infra.ProjectMeta].ok(
            m.Infra.ProjectMeta(
                name=name,
                python_version=python_version,
                description=description,
            ),
        )

    @staticmethod
    def _build_makefile(meta: m.Infra.ProjectMeta, bootstrap: str) -> str:
        """Build the fully-generated Makefile content."""
        title = f"# {meta.name}"
        if meta.description:
            title += f" - {meta.description}"
        sep = "# " + "=" * 77
        lines = [
            sep,
            title,
            sep,
            "# @generated by: flext_infra workspace sync",
            "# Run 'make sync' from workspace root to regenerate this file.",
            "# DO NOT EDIT — put custom targets in custom.mk instead.",
            sep,
            "",
            f"PROJECT_NAME := {meta.name}",
            f"PYTHON_VERSION ?= {meta.python_version}",
            f"SRC_DIR ?= {c.Infra.DEFAULT_SRC_DIR}",
            f"TESTS_DIR ?= {c.Infra.DIR_TESTS}",
            bootstrap,
            "",
            "# Project-specific targets (optional, never overwritten by sync)",
            "-include custom.mk",
        ]
        return "\n".join(lines) + "\n"


__all__: list[str] = ["FlextInfraProjectMakefileUpdater"]
