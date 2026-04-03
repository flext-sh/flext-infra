"""Rope+regex-based detection of constant declarations and usages.

Replaces the former CST-based visitor approach with regex scanning for
``Final`` declarations and ``c.*`` / ``FlextXxxConstants.*`` usage patterns.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesCodegenGovernance,
    FlextInfraUtilitiesDiscovery,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCodegenConstantDetection:
    """Regex-based detection of constant declarations and usages."""

    _MIN_QUOTED_LITERAL_LEN = 2

    # ------------------------------------------------------------------
    # Project inference
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_project_name(py_file: Path, root_path: Path) -> str:
        """Extract project name from file path (src/PROJECT_NAME/...)."""
        try:
            parts = py_file.relative_to(root_path).parts
            if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
                src_idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
                if src_idx + 1 < len(parts):
                    return parts[src_idx + 1].replace("_", "-")
            return "unknown"
        except ValueError:
            return "unknown"

    @staticmethod
    def canonical_reference_for(name: str, value_repr: str) -> str:
        """Return canonical constant reference for a name/value pair."""
        gov = FlextInfraUtilitiesCodegenGovernance
        min_quoted = FlextInfraUtilitiesCodegenConstantDetection._MIN_QUOTED_LITERAL_LEN

        def _name_matches(canonical_ref: str) -> bool:
            if not canonical_ref:
                return False
            return name in gov.get_semantic_names(canonical_ref)

        # Try integer literal
        if re.fullmatch(r"-?\d+", value_repr) is not None:
            candidate = gov.get_canonical_int_values().get(int(value_repr), "")
            return candidate if _name_matches(candidate) else ""

        # Try string literal
        if (
            len(value_repr) >= min_quoted
            and value_repr[0] == value_repr[-1]
            and value_repr[0] in {'"', "'"}
        ):
            candidate = gov.get_canonical_str_values().get(value_repr[1:-1], "")
            return candidate if _name_matches(candidate) else ""

        return ""

    # ------------------------------------------------------------------
    # Declaration extraction (regex-based, replaces CST DeclarationVisitor)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_definitions_from_source(
        source: str,
        *,
        project: str,
        file_path: str,
    ) -> Sequence[m.Infra.ConstantDefinition]:
        """Scan source text for ``NAME: Final[...] = VALUE`` declarations."""
        definitions: MutableSequence[m.Infra.ConstantDefinition] = []
        class_stack: MutableSequence[tuple[str, int]] = []
        lines = source.splitlines()

        for line_num, line in enumerate(lines, 1):
            stripped = line.lstrip()
            indent_level = len(line) - len(stripped)

            # Track class nesting via indentation
            if stripped.startswith("class ") and stripped.endswith(":"):
                class_name_match = re.match(r"class\s+(\w+)", stripped)
                if class_name_match:
                    # Pop deeper or same-level classes
                    while class_stack and class_stack[-1][1] >= indent_level:
                        class_stack.pop()
                    class_stack.append((class_name_match.group(1), indent_level))

            # Pop classes if we're back at a shallower indent
            while class_stack and indent_level <= class_stack[-1][1]:
                class_stack.pop()

            match = re.match(
                r"^(?P<indent>\s*)(?P<name>[A-Z_][A-Z0-9_]*)"
                r"\s*:\s*(?P<ann>Final\[.*?\])\s*=\s*(?P<value>.+?)\s*(?:#.*)?$",
                line,
            )
            if not match:
                continue

            definitions.append(
                m.Infra.ConstantDefinition(
                    name=match.group("name"),
                    value_repr=match.group("value").strip(),
                    type_annotation=match.group("ann"),
                    file_path=file_path,
                    class_path=".".join(name for name, _ in class_stack),
                    project=project,
                    line=line_num,
                ),
            )
        return definitions

    @staticmethod
    def extract_constant_definitions(
        file_path: Path,
        project: str,
    ) -> Sequence[m.Infra.ConstantDefinition]:
        """Extract Final constant definitions from a Python file."""
        try:
            source = file_path.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return []
        return FlextInfraUtilitiesCodegenConstantDetection._extract_definitions_from_source(
            source,
            project=project,
            file_path=str(file_path),
        )

    @staticmethod
    def extract_all_constant_definitions(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[m.Infra.ConstantDefinition]]:
        """Extract all constant definitions from all Python files."""
        if exclude_packages is None:
            exclude_packages = frozenset()
        all_defs: MutableMapping[str, MutableSequence[m.Infra.ConstantDefinition]] = {}
        for py_file in root_path.rglob(c.Infra.Extensions.PYTHON_GLOB):
            if any(excl in py_file.parts for excl in exclude_packages):
                continue
            project_name = (
                FlextInfraUtilitiesCodegenConstantDetection._infer_project_name(
                    py_file,
                    root_path,
                )
            )
            defs = FlextInfraUtilitiesCodegenConstantDetection.extract_constant_definitions(
                py_file,
                project_name,
            )
            if defs:
                if project_name not in all_defs:
                    all_defs[project_name] = list[m.Infra.ConstantDefinition]()
                all_defs[project_name].extend(defs)
        return all_defs

    # ------------------------------------------------------------------
    # Usage scanning (regex-based, replaces CST UsageVisitor)
    # ------------------------------------------------------------------

    @staticmethod
    def scan_all_constant_usages(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[t.Infra.StrIntPair]]:
        """Scan all constant usages across workspace."""
        if exclude_packages is None:
            exclude_packages = frozenset()
        usage_map: MutableMapping[str, MutableSequence[t.Infra.StrIntPair]] = {}
        for py_file in root_path.rglob(c.Infra.Extensions.PYTHON_GLOB):
            if any(excl in py_file.parts for excl in exclude_packages):
                continue
            project_name = (
                FlextInfraUtilitiesCodegenConstantDetection._infer_project_name(
                    py_file,
                    root_path,
                )
            )
            _, _, all_refs = (
                FlextInfraUtilitiesCodegenConstantDetection.scan_constant_usages(
                    py_file,
                    project_name,
                    collect_all_refs=True,
                )
            )
            for constant_name, line_num in all_refs:
                if constant_name not in usage_map:
                    usage_map[constant_name] = list[tuple[str, int]]()
                usage_map[constant_name].append((str(py_file), line_num))
        return usage_map

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

    @staticmethod
    def detect_unused_constants(
        definitions: Sequence[m.Infra.ConstantDefinition],
        all_used_names: t.Infra.StrSet,
    ) -> Sequence[m.Infra.UnusedConstant]:
        return [
            m.Infra.UnusedConstant(
                name=definition.name,
                file_path=definition.file_path,
                class_path=definition.class_path,
                project=definition.project,
                line=definition.line,
            )
            for definition in definitions
            if definition.name not in all_used_names
            and not re.match(r"Flext\w*Constants\.", definition.value_repr)
        ]

    @staticmethod
    def resolve_parent_package(pkg_dir: Path) -> str:
        """Find the parent package by scanning constants.py imports via regex."""
        return FlextInfraUtilitiesDiscovery.resolve_parent_constants(
            pkg_dir,
            return_module=True,
        )


__all__ = ["FlextInfraUtilitiesCodegenConstantDetection"]
