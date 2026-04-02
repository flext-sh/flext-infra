"""Rope+regex transformers for constant operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t
from flext_infra._utilities.codegen_constant_detection import (
    FlextInfraUtilitiesCodegenConstantDetection,
)
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing


class FlextInfraUtilitiesCodegenConstantTransformation:
    """Rope+regex transformers for constant value replacement and normalization."""

    @staticmethod
    def derive_constants_class(
        package_name: str,
        pkg_dir: Path | None = None,
    ) -> str:
        """``flext_dbt_oracle_wms`` -> ``FlextDbtOracleWmsConstants``."""
        if pkg_dir is not None:
            constants_file = pkg_dir / "constants.py"
            if constants_file.is_file():
                try:
                    source = constants_file.read_text(c.Infra.Encoding.DEFAULT)
                except (OSError, UnicodeDecodeError):
                    pass
                else:
                    match = re.search(r"^class\s+(\w+)", source, re.MULTILINE)
                    if match:
                        return match.group(1)
        return (
            "".join(part.capitalize() for part in package_name.split("_")) + "Constants"
        )

    @staticmethod
    def replace_canonical_values(
        file_path: Path,
        parent_class: str,
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        """Replace hardcoded canonical values with parent class references."""
        try:
            source = file_path.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return False, []

        # Build lookup: (name, value_repr) -> canonical_ref
        lookup: dict[tuple[str, str], str] = {}
        for item in definitions:
            ref = FlextInfraUtilitiesCodegenConstantDetection.canonical_reference_for(
                item.name,
                item.value_repr,
            )
            if ref:
                lookup[item.name, item.value_repr] = ref

        if not lookup:
            return False, []

        changes: MutableSequence[str] = []
        new_lines: MutableSequence[str] = []
        modified = False

        for line in source.splitlines(keepends=True):
            match = c.Infra.Detection.FINAL_DECL_RE.match(line.rstrip("\n"))
            if match:
                _indent, name, value = match.group(1), match.group(2), match.group(3)
                canonical_ref = lookup.get((name, value.strip()), "")
                if canonical_ref:
                    # Preserve original annotation portion, replace value only
                    eq_idx = line.index("=")
                    new_value = f"{parent_class}.{canonical_ref}"
                    new_line = f"{line[: eq_idx + 1]} {new_value}\n"
                    new_lines.append(new_line)
                    changes.append(f"replaced {name} -> {canonical_ref}")
                    modified = True
                    continue
            new_lines.append(line)

        if modified:
            file_path.write_text("".join(new_lines), encoding=c.Infra.Encoding.DEFAULT)
        return modified, changes

    @staticmethod
    def remove_unused_constants(
        file_path: Path,
        unused: Sequence[m.Infra.UnusedConstant],
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        """Remove unused constants from a file by line filtering."""
        unused_names = {item.name for item in unused}
        if not unused_names:
            return False, []
        try:
            source = file_path.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return False, []

        changes: MutableSequence[str] = []
        kept: MutableSequence[str] = []
        class_stack: MutableSequence[tuple[str, int]] = []
        removals = 0

        for line in source.splitlines(keepends=True):
            stripped = line.lstrip()
            indent_level = len(line) - len(line.lstrip())

            # Track class nesting
            class_match = re.match(r"class\s+(\w+)", stripped)
            if class_match:
                while class_stack and class_stack[-1][1] >= indent_level:
                    class_stack.pop()
                class_stack.append((class_match.group(1), indent_level))

            # Check if this line is a Final assignment for an unused name
            final_match = c.Infra.Detection.FINAL_DECL_RE.match(line.rstrip("\n"))
            if final_match and final_match.group(2) in unused_names:
                class_path = ".".join(name for name, _ in class_stack)
                changes.append(f"removed {class_path}.{final_match.group(2)}")
                removals += 1
                continue

            kept.append(line)

        if removals > 0:
            file_path.write_text("".join(kept), encoding=c.Infra.Encoding.DEFAULT)
        return removals > 0, changes

    @staticmethod
    def normalize_constant_aliases(
        file_path: Path,
        project_import: str,
        pkg_dir: Path | None = None,
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        """Normalize ``FlextXxxConstants.Y`` -> ``c.Y`` via regex replacement."""
        cls = FlextInfraUtilitiesCodegenConstantTransformation
        parts = project_import.replace("from ", "").split(" import ")
        package_name = parts[0].strip() if parts else ""
        resolved_pkg_dir = pkg_dir
        if resolved_pkg_dir is None and package_name:
            for parent in file_path.parents:
                if parent.name == package_name:
                    resolved_pkg_dir = parent
                    break
        target_class = cls.derive_constants_class(package_name, resolved_pkg_dir)

        try:
            source = file_path.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return False, []

        # Replace FlextXxxConstants.ATTR with c.ATTR
        pattern = re.compile(
            rf"\b{re.escape(target_class)}((?:\.[A-Za-z_]\w*)+)",
        )
        changes: MutableSequence[str] = []
        replacements = 0

        def _replace_ref(match: re.Match[str]) -> str:
            nonlocal replacements
            suffix = match.group(1)
            old_ref = f"{target_class}{suffix}"
            new_ref = f"c{suffix}"
            changes.append(f"{old_ref} -> {new_ref}")
            replacements += 1
            return new_ref

        new_source = pattern.sub(_replace_ref, source)

        if replacements == 0:
            return False, []

        # Remove direct import of the target class
        cleaned_source = FlextInfraUtilitiesCodegenConstantTransformation._clean_import(
            new_source,
            target_class,
        )

        # Ensure ``c`` import exists
        if " import c" not in cleaned_source and ",c" not in cleaned_source:
            insert_line = project_import
            if not insert_line.endswith("\n"):
                insert_line += "\n"
            idx = FlextInfraUtilitiesParsing.find_import_insert_position(
                cleaned_source.splitlines(),
            )
            lines = cleaned_source.splitlines(keepends=True)
            lines.insert(idx, insert_line)
            cleaned_source = "".join(lines)
            changes.append("added c import")

        file_path.write_text(cleaned_source, encoding=c.Infra.Encoding.DEFAULT)
        return True, changes

    @staticmethod
    def _clean_import(source: str, class_name: str) -> str:
        """Remove ``class_name`` from import statements in source."""
        esc = re.escape(class_name)
        strip_re = re.compile(rf",\s*{esc}\b|{esc}\s*,\s*|\b{esc}\b")
        result: MutableSequence[str] = []
        for line in source.splitlines(keepends=True):
            stripped = line.lstrip()
            if not stripped.startswith(("from ", "import ")) or class_name not in line:
                result.append(line)
                continue
            cleaned = strip_re.sub("", line)
            # Skip if import is now empty
            cs = cleaned.strip()
            if re.match(r"^\s*from\s+[\w.]+\s+import\s*\)?\s*$", cs):
                continue
            if re.search(r"import\s*\(\s*\)", cs):
                continue
            result.append(cleaned)
        return "".join(result)


__all__ = ["FlextInfraUtilitiesCodegenConstantTransformation"]
