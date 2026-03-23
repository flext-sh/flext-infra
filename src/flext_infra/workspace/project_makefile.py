"""Project Makefile updater for workspace sync.

Generates and updates the generated section of project Makefiles from
pyproject.toml metadata, preserving custom targets intact.

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

# Variable name prefixes that belong to the generated section.
# Any variable declared before the ifneq bootstrap block that matches
# one of these prefixes is superseded by the new generated header.
_GENERATED_VAR_PREFIXES: tuple[str, ...] = (
    "PROJECT_NAME ",
    "PYTHON_VERSION ",
    "SRC_DIR ",
    "TESTS_DIR ",
)


class _ProjectMeta(NamedTuple):
    """Extracted project metadata from pyproject.toml."""

    name: str
    python_version: str
    description: str


class FlextInfraProjectMakefileUpdater:
    """Update the generated section of project Makefiles from pyproject.toml.

    Splits Makefiles at the FLEXT sentinel, regenerates the header and
    bootstrap block from current pyproject.toml metadata, and preserves
    all custom targets.  SHA-256 idempotency skips unchanged files.

    Sentinel line: ``# --- FLEXT:custom-targets ---``

    First-run behaviour (no sentinel present):
      - Finds the ``ifneq ("$(wildcard ../base.mk)"`` bootstrap block.
      - Preserves any non-standard variable declarations before that block.
      - Replaces everything up to and including the closing ``endif``.
      - Appends the sentinel and the preserved custom section.

    Subsequent runs:
      - Splits on the sentinel and replaces only the generated part.
    """

    SENTINEL: str = "# --- FLEXT:custom-targets ---"

    def update(self, project_root: Path, *, canonical_root: Path) -> r[bool]:
        """Update project Makefile generated section from pyproject.toml.

        Args:
            project_root: Root directory of the project.
            canonical_root: Workspace canonical root (used for context).

        Returns:
            r with True if Makefile was updated, False if unchanged,
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

        generated = self._build_generated_section(meta, bootstrap)

        makefile_path = project_root / "Makefile"
        custom_result = self._extract_custom_section(makefile_path)
        if custom_result.is_failure:
            return r[bool].fail(
                custom_result.error or "custom section extraction failed",
            )
        custom = custom_result.value

        new_content = generated + "\n" + self.SENTINEL + "\n" + custom
        content_hash = hashlib.sha256(new_content.encode(_ENCODING)).hexdigest()

        if makefile_path.exists():
            try:
                existing_text = makefile_path.read_text(encoding=_ENCODING)
            except OSError as exc:
                return r[bool].fail(f"Makefile read failed: {exc}")
            existing_hash = hashlib.sha256(
                existing_text.encode(_ENCODING),
            ).hexdigest()
            if content_hash == existing_hash:
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
    def _build_generated_section(meta: _ProjectMeta, bootstrap: str) -> str:
        """Build the generated Makefile header from metadata and bootstrap block."""
        title = f"# {meta.name}"
        if meta.description:
            title += f" - {meta.description}"
        sep = "# " + "=" * 77
        lines = [
            sep,
            title,
            sep,
            "# @generated by: flext_infra workspace sync",
            "# Run 'make sync' from workspace root to update this section.",
            "# Edit below # --- FLEXT:custom-targets --- only.",
            sep,
            "",
            f"PROJECT_NAME := {meta.name}",
            f"PYTHON_VERSION ?= {meta.python_version}",
            "SRC_DIR ?= src",
            "TESTS_DIR ?= tests",
            bootstrap,
        ]
        return "\n".join(lines)

    def _extract_custom_section(self, makefile_path: Path) -> r[str]:
        """Extract the custom (user-managed) section from an existing Makefile.

        On first run (no sentinel):
          - Finds the bootstrap ``ifneq`` block.
          - Preserves non-standard pre-bootstrap variable declarations.
          - Custom section = preserved vars + everything after the closing ``endif``.

        On subsequent runs (sentinel present):
          - Splits on sentinel and returns everything after it.

        """
        if not makefile_path.exists():
            return r[str].ok("")

        try:
            content = makefile_path.read_text(encoding=_ENCODING)
        except OSError as exc:
            return r[str].fail(f"Makefile read failed: {exc}")

        # --- Subsequent runs: sentinel present as a standalone line ---
        # Match only when the sentinel occupies its own line to avoid
        # splitting on the reference to it inside the generated header comment.
        sentinel_line = "\n" + self.SENTINEL + "\n"
        if sentinel_line in content:
            idx = content.index(sentinel_line)
            return r[str].ok(content[idx + len(sentinel_line) :])

        # --- First run: locate the bootstrap block boundary ---
        lines = content.splitlines()
        search_limit = min(100, len(lines))

        bootstrap_start = -1
        for i, line in enumerate(lines[:search_limit]):
            if line.startswith('ifneq ("$(wildcard ../base.mk)"'):
                bootstrap_start = i
                break

        start = max(0, bootstrap_start)
        last_endif_idx = -1
        for i in range(start, search_limit):
            if lines[i].strip() == "endif":
                last_endif_idx = i

        if last_endif_idx == -1:
            # No bootstrap block found — preserve entire file as custom
            return r[str].ok(content)

        # Collect extra pre-bootstrap vars that are NOT in the generated header
        extra_pre: list[str] = []
        if bootstrap_start > 0:
            for line in lines[:bootstrap_start]:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if any(stripped.startswith(p) for p in _GENERATED_VAR_PREFIXES):
                    continue
                extra_pre.append(line)

        # Custom = extra pre-bootstrap vars + everything after `endif`
        after_endif = lines[last_endif_idx + 1 :]
        combined: list[str] = extra_pre + after_endif

        # Strip leading empty lines
        while combined and not combined[0].strip():
            combined.pop(0)

        custom = "\n".join(combined)
        if custom and not custom.endswith("\n"):
            custom += "\n"
        return r[str].ok(custom)

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
