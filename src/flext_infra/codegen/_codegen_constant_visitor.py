"""Centralized CST visitor library for constants governance detection.

ALL detection CST logic lives here. Census and metrics call these entry-point
functions — they NEVER import libcst directly.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c, m

# ---------------------------------------------------------------------------
# Shared CST helpers (used by visitors and importable by transformer)
# ---------------------------------------------------------------------------


def attribute_chain(expr: cst.BaseExpression) -> list[str]:
    """Flatten a dotted attribute access into a list of names."""
    if isinstance(expr, cst.Name):
        return [expr.value]
    if isinstance(expr, cst.Attribute):
        return [*attribute_chain(expr.value), expr.attr.value]
    return []


def root_name(expr: cst.BaseExpression) -> str:
    """Return the leftmost name in a dotted attribute chain."""
    parts = attribute_chain(expr)
    return parts[0] if parts else ""


def _int_literal(value_repr: str) -> int | None:
    """Parse integer literal from source repr, or None."""
    if re.fullmatch(r"-?\d+", value_repr) is None:
        return None
    return int(value_repr)


def _str_literal(value_repr: str) -> str | None:
    """Parse string literal from source repr, or None."""
    if len(value_repr) < 2:
        return None
    if value_repr[0] != value_repr[-1]:
        return None
    if value_repr[0] not in {'"', "'"}:
        return None
    return value_repr[1:-1]


def _semantic_name_matches(name: str, canonical_ref: str) -> bool:
    """Return True when the constant name semantically matches the canonical ref."""
    if canonical_ref == "Network.DEFAULT_TIMEOUT":
        return name in c.Infra.Dedup.TIMEOUT_NAMES
    if canonical_ref == "DEFAULT_MAX_RETRY_ATTEMPTS":
        return name in c.Infra.Dedup.RETRY_NAMES
    if canonical_ref == "DEFAULT_BATCH_SIZE":
        return name in c.Infra.Dedup.BATCH_NAMES
    if canonical_ref == "Network.LOCALHOST":
        return name in c.Infra.Dedup.HOST_NAMES
    if canonical_ref == "Utilities.DEFAULT_ENCODING":
        return name in c.Infra.Dedup.ENCODING_NAMES
    return False


def canonical_reference_for(name: str, value_repr: str) -> str:
    """Return the canonical parent MRO reference for a hardcoded value, or ''."""
    int_value = _int_literal(value_repr)
    if int_value is not None:
        candidate = c.Infra.Dedup.CANONICAL_INT_VALUES.get(int_value, "")
        return candidate if _semantic_name_matches(name, candidate) else ""

    str_value = _str_literal(value_repr)
    if str_value is not None:
        candidate = c.Infra.Dedup.CANONICAL_STR_VALUES.get(str_value, "")
        return candidate if _semantic_name_matches(name, candidate) else ""

    return ""


class _CodeRenderContext:
    """Lightweight helper to extract source text and line numbers from CST nodes."""

    def __init__(self, source: str) -> None:
        self._render_module = cst.parse_module("")
        self._source = source
        self._search_offset = 0

    def node_code(self, node: cst.CSTNode) -> str:
        """Return the source code text of *node*."""
        return self._render_module.code_for_node(node)

    def line_for_node(self, node: cst.CSTNode) -> int:
        """Approximate the 1-based line number of *node* within the file."""
        snippet = self.node_code(node)
        if not snippet:
            return 1
        index = self._source.find(snippet, self._search_offset)
        if index < 0:
            index = self._source.find(snippet)
        if index < 0:
            return 1
        self._search_offset = index + len(snippet)
        return self._source.count("\n", 0, index) + 1


# ---------------------------------------------------------------------------
# Visitor 1: Constant declarations (Final/ClassVar in nested classes)
# ---------------------------------------------------------------------------


class ConstantDeclarationVisitor(cst.CSTVisitor):
    """Walk nested classes, extract Final/ClassVar annotated declarations."""

    def __init__(self, *, project: str, file_path: str) -> None:
        super().__init__()
        self._project = project
        self._file_path = file_path
        self._render = _CodeRenderContext(Path(file_path).read_text("utf-8"))
        self._class_stack: list[str] = []
        self.definitions: list[m.Infra.ConstantDefinition] = []

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._class_stack.append(node.name.value)

    @override
    def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
        del original_node
        if self._class_stack:
            self._class_stack.pop()

    @override
    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if not isinstance(node.target, cst.Name) or node.value is None:
            return
        type_annotation = self._render.node_code(node.annotation.annotation)
        if "Final" not in type_annotation and "ClassVar" not in type_annotation:
            return
        self.definitions.append(
            m.Infra.ConstantDefinition(
                name=node.target.value,
                value_repr=self._render.node_code(node.value),
                type_annotation=type_annotation,
                file_path=self._file_path,
                class_path=".".join(self._class_stack),
                project=self._project,
                line=self._render.line_for_node(node),
            ),
        )


# ---------------------------------------------------------------------------
# Visitor 2: Constant usages (c.X.Y and FlextXConstants.Y.Z)
# ---------------------------------------------------------------------------


class ConstantUsageVisitor(cst.CSTVisitor):
    """Detect c.* accesses and direct FlextXConstants.Y.Z references."""

    def __init__(self, *, project: str, file_path: str) -> None:
        super().__init__()
        self._project = project
        self._file_path = file_path
        self._render = _CodeRenderContext(Path(file_path).read_text("utf-8"))
        self.used_constants: set[str] = set()
        self.direct_refs: list[m.Infra.DirectConstantRef] = []

    @override
    def visit_Attribute(self, node: cst.Attribute) -> None:
        # Track c.X.Y usage -> constant name
        if isinstance(node.value, cst.Attribute) and root_name(node.value) == "c":
            self.used_constants.add(node.attr.value)

        # Detect FlextXConstants.Y.Z direct references
        chain = attribute_chain(node)
        if len(chain) < 3:
            return
        if not re.fullmatch(c.Infra.Dedup.CONSTANTS_CLASS_PATTERN, chain[0]):
            return

        self.direct_refs.append(
            m.Infra.DirectConstantRef(
                full_ref=".".join(chain),
                alias_ref=".".join(["c", *chain[1:]]),
                file_path=self._file_path,
                project=self._project,
                line=self._render.line_for_node(node),
            ),
        )


# ---------------------------------------------------------------------------
# Public entry-point functions (the ONLY public API)
# ---------------------------------------------------------------------------


def extract_constant_definitions(
    file_path: Path,
    project: str,
) -> list[m.Infra.ConstantDefinition]:
    """Parse constants.py with libcst, extract all Final/ClassVar declarations."""
    try:
        source = file_path.read_text("utf-8")
        tree = cst.parse_module(source)
    except (cst.ParserSyntaxError, UnicodeDecodeError):
        return []
    visitor = ConstantDeclarationVisitor(project=project, file_path=str(file_path))
    tree.visit(visitor)
    return visitor.definitions


def scan_constant_usages(
    file_path: Path,
    project: str,
) -> tuple[set[str], list[m.Infra.DirectConstantRef]]:
    """Parse a Python file with libcst, find c.* usages and direct refs."""
    try:
        source = file_path.read_text("utf-8")
        tree = cst.parse_module(source)
    except (cst.ParserSyntaxError, UnicodeDecodeError):
        return set(), []
    visitor = ConstantUsageVisitor(project=project, file_path=str(file_path))
    tree.visit(visitor)
    return visitor.used_constants, visitor.direct_refs


def detect_hardcoded_canonicals(
    definitions: list[m.Infra.ConstantDefinition],
) -> list[m.Infra.ConstantDefinition]:
    """Filter definitions to those with hardcoded values matching canonicals + semantic names."""
    return [
        definition
        for definition in definitions
        if canonical_reference_for(definition.name, definition.value_repr)
    ]


def detect_unused_constants(
    definitions: list[m.Infra.ConstantDefinition],
    all_used_names: set[str],
) -> list[m.Infra.UnusedConstant]:
    """Cross-reference declarations vs usages, return unused constants."""
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
    ]


__all__ = [
    "ConstantDeclarationVisitor",
    "ConstantUsageVisitor",
    "attribute_chain",
    "canonical_reference_for",
    "detect_hardcoded_canonicals",
    "detect_unused_constants",
    "extract_constant_definitions",
    "root_name",
    "scan_constant_usages",
]
