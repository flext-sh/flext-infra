"""Project Makefile generator for workspace sync.

Fully generates project Makefiles from pyproject.toml metadata and the
base bootstrap template.  Custom targets live in ``custom.mk`` alongside
the generated ``Makefile``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import tempfile
import tomllib
from pathlib import Path
from typing import NamedTuple

from flext_infra import FlextInfraBaseMkGenerator, r

_ENCODING = "utf-8"

# Legacy sentinel used by the previous sentinel-based approach.
# Present only during migration; the new generated Makefile has no sentinel.
_LEGACY_SENTINEL: str = "# --- FLEXT:custom-targets ---"


class _ProjectMeta(NamedTuple):
    """Extracted project metadata from pyproject.toml."""

    name: str
    python_version: str
    description: str


class FlextInfraProjectMakefileUpdater:
    """Fully generate project Makefiles from pyproject.toml metadata.

    The generated ``Makefile`` is 100% managed — do not edit it.  Put any
    project-specific Make targets in ``custom.mk`` next to the ``Makefile``;
    it is automatically included via ``-include custom.mk`` at the end.

    Migration (legacy sentinel-based Makefiles):
      - If the existing ``Makefile`` contains the legacy sentinel
        ``# --- FLEXT:custom-targets ---``, the inline custom section is
        extracted and written to ``custom.mk`` (only if ``custom.mk`` does
        not yet exist and the custom section is non-empty).

    Idempotency:
      - SHA-256 comparison skips the write if the generated content is
        identical to the file already on disk.
    """

    def update(self, project_root: Path, *, canonical_root: Path) -> r[bool]:
        """Regenerate project Makefile from pyproject.toml.

        Args:
            project_root: Root directory of the project.
            canonical_root: Workspace canonical root (reserved for future use).

        Returns:
            r with True if Makefile was written, False if unchanged,
            failure with error message on I/O or parse error.

        """
        _ = canonical_root  # reserved for future cross-project dependency resolution
        pyproject = project_root / "pyproject.toml"
        if not pyproject.exists():
            return r[bool].ok(False)

        meta_result = self._read_pyproject(pyproject)
        if meta_result.is_failure:
            return r[bool].fail(meta_result.error or "pyproject.toml parse failed")
        meta = meta_result.value

        bootstrap_result = FlextInfraBaseMkGenerator.render_bootstrap_include()
        if bootstrap_result.is_failure:
            return r[bool].fail(
                bootstrap_result.error or "bootstrap template read failed",
            )
        bootstrap = bootstrap_result.value

        new_content = self._build_makefile(meta, bootstrap)
        makefile_path = project_root / "Makefile"

        # Migration: move any legacy inline custom section to custom.mk
        if makefile_path.exists():
            try:
                existing = makefile_path.read_text(encoding=_ENCODING)
            except OSError as exc:
                return r[bool].fail(f"Makefile read failed: {exc}")

            migrate_result = self._migrate_custom_section(
                existing, project_root / "custom.mk"
            )
            if migrate_result.is_failure:
                return r[bool].fail(
                    migrate_result.error or "custom.mk migration failed"
                )

            existing_hash = hashlib.sha256(existing.encode(_ENCODING)).hexdigest()
            new_hash = hashlib.sha256(new_content.encode(_ENCODING)).hexdigest()
            if existing_hash == new_hash:
                return r[bool].ok(False)

        return self._atomic_write(makefile_path, new_content)

    @staticmethod
    def _read_pyproject(pyproject: Path) -> r[_ProjectMeta]:
        """Parse pyproject.toml and extract name, python_version, description."""
        try:
            with pyproject.open("rb") as fh:
                data = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            return r[_ProjectMeta].fail(f"pyproject.toml read failed: {exc}")

        try:
            project = data["project"]
            name: str = project["name"]
            requires_python: str = project.get("requires-python", ">=3.13")
            # Extract "3.13" from ">=3.13,<3.14" or ">=3.13"
            version_str = requires_python.lstrip(">= ")
            python_version = version_str.split(",")[0].split("<")[0].strip()
            description: str = project.get("description", "")
        except (KeyError, AttributeError) as exc:
            return r[_ProjectMeta].fail(
                f"pyproject.toml missing required fields: {exc}",
            )

        return r[_ProjectMeta].ok(
            _ProjectMeta(
                name=name,
                python_version=python_version,
                description=description,
            ),
        )

    @staticmethod
    def _build_makefile(meta: _ProjectMeta, bootstrap: str) -> str:
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
            "SRC_DIR ?= src",
            "TESTS_DIR ?= tests",
            bootstrap,
            "",
            "# Project-specific targets (optional, never overwritten by sync)",
            "-include custom.mk",
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _migrate_custom_section(existing_content: str, custom_mk_path: Path) -> r[bool]:
        """Migrate inline custom section to custom.mk (one-time, non-destructive).

        Only writes ``custom.mk`` if:
        - The existing Makefile contains the legacy sentinel.
        - The extracted custom section is non-empty (after stripping).
        - ``custom.mk`` does not already exist.

        Returns True if migration was performed, False if skipped.
        """
        sentinel_line = "\n" + _LEGACY_SENTINEL + "\n"
        if sentinel_line not in existing_content:
            return r[bool].ok(False)

        if custom_mk_path.exists():
            return r[bool].ok(False)

        # Use last sentinel occurrence (handles files with multiple sentinels)
        idx = existing_content.rindex(sentinel_line)
        custom_raw = existing_content[idx + len(sentinel_line) :]

        # Strip trivial content (empty lines, standalone comments from the old header)
        custom_lines = [
            ln
            for ln in custom_raw.splitlines()
            if ln.strip() and not ln.strip().startswith("# ===")
        ]
        if not custom_lines:
            return r[bool].ok(False)

        custom_content = "\n".join(custom_lines) + "\n"
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=str(custom_mk_path.parent),
                delete=False,
                encoding=_ENCODING,
                suffix=".tmp",
            ) as tmp:
                _ = tmp.write(custom_content)
                tmp_path = Path(tmp.name)
            _ = tmp_path.replace(custom_mk_path)
        except OSError as exc:
            return r[bool].fail(f"custom.mk write failed: {exc}")
        return r[bool].ok(True)

    @staticmethod
    def _atomic_write(target: Path, content: str) -> r[bool]:
        """Write content to target via atomic temp-file rename."""
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=str(target.parent),
                delete=False,
                encoding=_ENCODING,
                suffix=".tmp",
            ) as tmp:
                _ = tmp.write(content)
                tmp_path = Path(tmp.name)
            _ = tmp_path.replace(target)
        except OSError as exc:
            return r[bool].fail(f"atomic write failed: {exc}")
        return r[bool].ok(True)


__all__ = ["FlextInfraProjectMakefileUpdater"]
