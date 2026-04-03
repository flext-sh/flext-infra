"""Constant transformation utilities for codegen inline-canonical replacement.

Provides derive, detect, replace, and normalize methods used by the
constants CLI command to find and replace hardcoded values with canonical
constant references.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesDiscovery,
    c,
    m,
)


class FlextInfraUtilitiesCodegenConstantTransformation:
    """Derive, detect, replace, and normalize constant references in source."""

    @staticmethod
    def derive_constants_class(pkg_name: str, pkg_dir: Path) -> str:
        """Derive the constants class name for a package.

        First checks constants.py for an existing class definition.
        Falls back to PascalCase conversion of the package name + "Constants".

        Args:
            pkg_name: Underscore-separated package name (e.g., "flext_infra").
            pkg_dir: Path to the package directory.

        Returns:
            Constants class name (e.g., "FlextInfraConstants").

        """
        # Try to find existing parent class from constants.py imports
        parent = FlextInfraUtilitiesDiscovery.resolve_parent_constants(
            pkg_dir,
            return_module=False,
        )
        if parent:
            return parent
        # Derive from package name: flext_infra -> FlextInfraConstants
        parts = pkg_name.split("_")
        pascal = "".join(part.capitalize() for part in parts)
        return f"{pascal}Constants"

    @staticmethod
    def detect_hardcoded_canonicals(
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> Sequence[m.Infra.ConstantDefinition]:
        """Detect constant definitions whose values match canonical references.

        Filters definitions to only those where the value_repr has a known
        canonical constant reference (e.g., a hardcoded "utf-8" that should be
        ``c.Infra.Encoding.DEFAULT``).

        Args:
            definitions: Extracted constant definitions from a source file.

        Returns:
            Subset of definitions that have canonical replacements available.

        """
        result: MutableSequence[m.Infra.ConstantDefinition] = []
        for defn in definitions:
            ref = FlextInfraUtilitiesCodegenConstantDetection.canonical_reference_for(
                defn.name,
                defn.value_repr,
            )
            if ref:
                result.append(defn)
        return result

    @staticmethod
    def replace_canonical_values(
        py_file: Path,
        parent_class: str,
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> tuple[bool, Sequence[str]]:
        """Replace hardcoded constant values with canonical references in a file.

        Reads the source, finds definitions whose values have canonical refs,
        and replaces the value literals with the canonical constant path.

        Args:
            py_file: Python source file to modify.
            parent_class: Constants class name (e.g., "FlextInfraConstants").
            definitions: Extracted constant definitions from the file.

        Returns:
            Tuple of (was_modified, list_of_change_descriptions).

        """
        try:
            source = py_file.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return False, []

        changes: MutableSequence[str] = []
        lines = source.splitlines(keepends=True)
        modified = False

        for defn in definitions:
            ref = FlextInfraUtilitiesCodegenConstantDetection.canonical_reference_for(
                defn.name,
                defn.value_repr,
            )
            if not ref:
                continue
            line_idx = defn.line - 1
            if line_idx < 0 or line_idx >= len(lines):
                continue
            old_line = lines[line_idx]
            # Replace the value_repr with the canonical reference
            escaped_value = re.escape(defn.value_repr)
            new_line = re.sub(
                rf"=\s*{escaped_value}(\s*(?:#.*)?)$",
                f"= {ref}\\1",
                old_line,
            )
            if new_line != old_line:
                lines[line_idx] = new_line
                modified = True
                changes.append(
                    f"L{defn.line}: {defn.name} = {defn.value_repr} -> {ref}",
                )

        if modified:
            py_file.write_text("".join(lines), encoding=c.Infra.Encoding.DEFAULT)
        return modified, changes

    @staticmethod
    def normalize_constant_aliases(
        py_file: Path,
        project_import: str,
        pkg_dir: Path,
    ) -> tuple[str, Sequence[str]]:
        """Normalize constant alias patterns in source to use canonical form.

        Ensures that FlextXxxConstants references are replaced with the
        canonical ``c.Xxx.*`` alias form, and adds the required import if
        missing.

        Args:
            py_file: Python source file to modify.
            project_import: Import statement for the constants class
                (e.g., "from flext_infra import FlextInfraConstants").
            pkg_dir: Package directory for context.

        Returns:
            Tuple of (modified_source, list_of_change_descriptions).

        """
        try:
            source = py_file.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return "", []

        changes: MutableSequence[str] = []
        # Extract the class name from the import statement
        import_match = re.search(r"import\s+(\w+Constants)\b", project_import)
        if not import_match:
            return source, []

        class_name = import_match.group(1)
        # Replace direct FlextXxxConstants.ATTR references with c.Xxx.ATTR
        direct_re = re.compile(rf"\b{re.escape(class_name)}((?:\.[A-Za-z_]\w*)+)")
        new_source = source
        replacements_made = False

        for match in direct_re.finditer(source):
            full_match = match.group(0)
            attr_chain = match.group(1)
            # Build the c.Xxx alias: FlextInfraConstants -> c.Infra
            # Extract the project part from class name
            prefix = class_name.replace("Constants", "")
            # Remove Flext prefix
            prefix = prefix.removeprefix("Flext")
            canonical = f"c.{prefix}{attr_chain}" if prefix else f"c{attr_chain}"
            if full_match != canonical:
                new_source = new_source.replace(full_match, canonical, 1)
                changes.append(f"{full_match} -> {canonical}")
                replacements_made = True

        if replacements_made:
            py_file.write_text(new_source, encoding=c.Infra.Encoding.DEFAULT)

        return new_source, changes


__all__ = ["FlextInfraUtilitiesCodegenConstantTransformation"]
