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

from flext_infra import c, m, t
from flext_infra._utilities.codegen_governance import (
    FlextInfraUtilitiesCodegenGovernance,
)
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery


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

    # ------------------------------------------------------------------
    # Literal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def int_literal(value_repr: str) -> int | None:
        if re.fullmatch(r"-?\d+", value_repr) is None:
            return None
        return int(value_repr)

    @staticmethod
    def str_literal(value_repr: str) -> str | None:
        if (
            len(value_repr)
            < FlextInfraUtilitiesCodegenConstantDetection._MIN_QUOTED_LITERAL_LEN
        ):
            return None
        if value_repr[0] != value_repr[-1]:
            return None
        if value_repr[0] not in {'"', "'"}:
            return None
        return value_repr[1:-1]

    @staticmethod
    def semantic_name_matches(name: str, canonical_ref: str) -> bool:
        if not canonical_ref:
            return False
        return name in FlextInfraUtilitiesCodegenGovernance.get_semantic_names(
            canonical_ref,
        )

    @staticmethod
    def canonical_reference_for(name: str, value_repr: str) -> str:
        det = FlextInfraUtilitiesCodegenConstantDetection
        int_value = det.int_literal(value_repr)
        if int_value is not None:
            candidate = (
                FlextInfraUtilitiesCodegenGovernance.get_canonical_int_values().get(
                    int_value, ""
                )
            )
            return candidate if det.semantic_name_matches(name, candidate) else ""
        str_value = det.str_literal(value_repr)
        if str_value is not None:
            candidate = (
                FlextInfraUtilitiesCodegenGovernance.get_canonical_str_values().get(
                    str_value, ""
                )
            )
            return candidate if det.semantic_name_matches(name, candidate) else ""
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
        for py_file in root_path.rglob("*.py"):
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
    def scan_constant_usages(
        file_path: Path,
        project: str,
        *,
        target_class: str = "",
        collect_all_refs: bool = False,
    ) -> t.Infra.Triple[
        t.Infra.StrSet,
        Sequence[m.Infra.DirectConstantRef],
        Sequence[t.Infra.StrIntPair],
    ]:
        """Scan constant usages in a file via regex."""
        try:
            source = file_path.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return set(), [], []

        if not target_class and not collect_all_refs:
            pkg_name = file_path.parent.name
            while pkg_name.startswith("_") and file_path.parent.parent.name != "src":
                pkg_name = file_path.parent.parent.name
            target_class = (
                "".join(part.capitalize() for part in pkg_name.split("_")) + "Constants"
            )

        constants_class_pattern = (
            FlextInfraUtilitiesCodegenGovernance.get_constants_class_pattern()
        )
        used_constants: t.Infra.StrSet = set()
        direct_refs: MutableSequence[m.Infra.DirectConstantRef] = []
        all_constant_refs: MutableSequence[t.Infra.StrIntPair] = []

        for line_num, line in enumerate(source.splitlines(), 1):
            # Track c.ATTR usage
            for hit in re.finditer(r"\bc\.([A-Za-z_]\w*)", line):
                attr_name = hit.group(1)
                used_constants.add(attr_name)
                if collect_all_refs:
                    all_constant_refs.append((attr_name, line_num))

            # Track FlextXxxConstants.ATTR direct refs
            for hit in re.finditer(r"\b(Flext\w*Constants(?:\.[A-Za-z_]\w*)+)", line):
                chain = hit.group(1).split(".")
                if not re.fullmatch(constants_class_pattern, chain[0]):
                    continue
                if target_class and chain[0] != target_class and not collect_all_refs:
                    continue
                direct_refs.append(
                    m.Infra.DirectConstantRef(
                        full_ref=".".join(chain),
                        alias_ref=".".join(["c", *chain[1:]]),
                        file_path=str(file_path),
                        project=project,
                        line=line_num,
                    ),
                )
                if collect_all_refs:
                    all_constant_refs.append((chain[-1], line_num))

        return used_constants, direct_refs, all_constant_refs

    @staticmethod
    def scan_all_constant_usages(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[t.Infra.StrIntPair]]:
        """Scan all constant usages across workspace."""
        if exclude_packages is None:
            exclude_packages = frozenset()
        usage_map: MutableMapping[str, MutableSequence[t.Infra.StrIntPair]] = {}
        for py_file in root_path.rglob("*.py"):
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
    def detect_hardcoded_canonicals(
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> Sequence[m.Infra.ConstantDefinition]:
        return [
            definition
            for definition in definitions
            if FlextInfraUtilitiesCodegenConstantDetection.canonical_reference_for(
                definition.name,
                definition.value_repr,
            )
        ]

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
