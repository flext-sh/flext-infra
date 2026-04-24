"""Namespace validation rules (rules 0-2) for flext projects.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import (
    MutableSequence,
)
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraNamespaceRules:
    """Implementation of namespace rules 0-3 for AST-based validation."""

    _DIRECT_FACADE_IMPORT_RULES = (
        ("FlextInfraConstants", c.Infra.CONSTANTS_PY, "_constants"),
        ("FlextInfraModels", c.Infra.MODELS_PY, "_models"),
        ("FlextInfraProtocols", c.Infra.PROTOCOLS_PY, "_protocols"),
        ("FlextInfraTypes", c.Infra.TYPINGS_PY, "_typings"),
        ("FlextInfraUtilities", c.Infra.UTILITIES_PY, "_utilities"),
    )

    @staticmethod
    def _annotation_contains(
        annotation: ast.expr | None,
        name: str,
    ) -> bool:
        """Check whether an annotation AST node references a given name."""
        if annotation is None:
            return False
        if isinstance(annotation, ast.Name) and annotation.id == name:
            return True
        if isinstance(annotation, ast.Attribute) and annotation.attr == name:
            return True
        if isinstance(annotation, ast.Subscript):
            return FlextInfraNamespaceRules._annotation_contains(
                annotation.value,
                name,
            )
        return False

    @staticmethod
    def _base_contains(base: ast.expr, name: str) -> bool:
        """Check whether a class base AST node references a given name."""
        if isinstance(base, ast.Name) and base.id == name:
            return True
        return isinstance(base, ast.Attribute) and base.attr == name

    @staticmethod
    def _get_assign_target_name(node: ast.Assign) -> str:
        if node.targets and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id
        return ""

    @staticmethod
    def _get_call_name(func: ast.expr) -> str:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return ""

    @staticmethod
    def _get_target_name(target: ast.expr) -> str:
        if isinstance(target, ast.Name):
            return target.id
        return ""

    def check_rule_0(
        self,
        tree: ast.Module,
        filepath: Path,
        prefix: str,
    ) -> t.StrSequence:
        """Rule 0 -- One namespace class per module."""
        violations: MutableSequence[str] = []
        seq = 0
        outer_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        class_count = len(outer_classes)
        if class_count != 1:
            seq += 1
            violations.append(
                f"[NS-000-{seq:03d}] {filepath}:{(outer_classes[0].lineno if outer_classes else 1)} — Multiple outer classes found (expected 1, got {class_count})"
                if class_count > 1
                else f"[NS-000-{seq:03d}] {filepath}:1 — No outer class found (expected 1, got 0)",
            )
        for cls in outer_classes:
            if prefix and (not cls.name.startswith(prefix)):
                seq += 1
                violations.append(
                    f"[NS-000-{seq:03d}] {filepath}:{cls.lineno} — Class '{cls.name}' does not start with prefix '{prefix}'",
                )
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                continue
            if not self._is_allowed_module_level(node, filepath):
                seq += 1
                lineno = getattr(node, "lineno", 0)
                violations.append(
                    f"[NS-000-{seq:03d}] {filepath}:{lineno} — Disallowed top-level statement: {type(node).__name__}",
                )
        return violations

    def check_rule_1(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        """Rule 1 -- Constants centralization."""
        if filepath.name == c.Infra.CONSTANTS_PY:
            return self._check_rule_1_canonical(tree, filepath)
        return self._check_rule_1_non_canonical(tree, filepath)

    def _check_rule_1_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        violations: MutableSequence[str] = []
        seq = 0
        outer_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        for cls in outer_classes:
            if not any(self._base_contains(b, "Constants") for b in cls.bases):
                seq += 1
                violations.append(
                    f"[NS-001-{seq:03d}] {filepath}:{cls.lineno} — Constants class '{cls.name}' must inherit from a Constants base",
                )
            for inner_node in ast.walk(cls):
                if isinstance(inner_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    seq += 1
                    violations.append(
                        f"[NS-001-{seq:03d}] {filepath}:{inner_node.lineno} — Method '{inner_node.name}' found in Constants class",
                    )
        return violations

    def _check_rule_1_non_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        violations: MutableSequence[str] = []
        seq = 0
        for node in tree.body:
            seq, violations = self._check_loose_final(node, filepath, seq, violations)
            seq, violations = self._check_loose_collection(
                node,
                filepath,
                seq,
                violations,
            )
        outer_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        for cls in outer_classes:
            seq, violations = self._check_loose_enums(cls, filepath, seq, violations)
        return violations

    def _check_loose_final(
        self,
        node: ast.stmt,
        filepath: Path,
        seq: int,
        violations: MutableSequence[str],
    ) -> tuple[int, MutableSequence[str]]:
        if not (
            isinstance(node, ast.AnnAssign)
            and self._annotation_contains(node.annotation, "Final")
        ):
            return seq, violations
        target_name = self._get_target_name(node.target)
        if target_name and not target_name.startswith("_"):
            seq += 1
            violations.append(
                f"[NS-001-{seq:03d}] {filepath}:{node.lineno} — Loose Final constant '{target_name}' belongs in constants.py",
            )
        return seq, violations

    def _check_loose_collection(
        self,
        node: ast.stmt,
        filepath: Path,
        seq: int,
        violations: MutableSequence[str],
    ) -> tuple[int, MutableSequence[str]]:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            return seq, violations
        func_name = self._get_call_name(node.value.func)
        if func_name not in c.Infra.COLLECTION_CALLS:
            return seq, violations
        target_name = self._get_assign_target_name(node)
        if (
            target_name
            and target_name not in c.Infra.DUNDER_ALLOWED
            and target_name not in c.Infra.ALIAS_NAMES
        ):
            seq += 1
            violations.append(
                f"[NS-001-{seq:03d}] {filepath}:{node.lineno} — Loose collection constant '{target_name}' belongs in constants.py",
            )
        return seq, violations

    def _check_loose_enums(
        self,
        cls: ast.ClassDef,
        filepath: Path,
        seq: int,
        violations: MutableSequence[str],
    ) -> tuple[int, MutableSequence[str]]:
        for inner in cls.body:
            if isinstance(inner, ast.ClassDef) and any(
                self._base_contains(b, base)
                for b in inner.bases
                for base in c.Infra.ENUM_BASES
            ):
                seq += 1
                violations.append(
                    f"[NS-001-{seq:03d}] {filepath}:{inner.lineno} — Loose Enum '{inner.name}' belongs in constants.py",
                )
        return seq, violations

    def check_rule_2(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        """Rule 2 -- Types centralization."""
        if filepath.name == c.Infra.TYPINGS_PY:
            return self._check_rule_2_canonical(tree, filepath)
        return self._check_rule_2_non_canonical(tree, filepath)

    def _check_rule_2_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        violations: MutableSequence[str] = []
        seq = 0
        outer_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        for cls in outer_classes:
            if not any(self._base_contains(b, "Types") for b in cls.bases):
                seq += 1
                violations.append(
                    f"[NS-002-{seq:03d}] {filepath}:{cls.lineno} — Types class '{cls.name}' must inherit from a Types base",
                )
            for inner in cls.body:
                if isinstance(
                    inner,
                    ast.ClassDef,
                ) and self._inner_inherits_forbidden_base(inner):
                    seq += 1
                    violations.append(
                        f"[NS-002-{seq:03d}] {filepath}:{inner.lineno} — Inner class '{inner.name}' in Types must not inherit from BaseModel/Protocol",
                    )
        return violations

    def _inner_inherits_forbidden_base(
        self,
        inner: ast.ClassDef,
    ) -> bool:
        return any(
            self._base_contains(base, "BaseModel")
            or self._base_contains(base, "Protocol")
            for base in inner.bases
        )

    def _check_rule_2_non_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        violations: MutableSequence[str] = []
        seq = 0
        for node in tree.body:
            seq, violations = self._check_loose_typevar(
                node,
                filepath,
                seq,
                violations,
            )
            seq, violations = self._check_loose_typealias_annotation(
                node,
                filepath,
                seq,
                violations,
            )
            seq, violations = self._check_loose_pep695_typealias(
                node,
                filepath,
                seq,
                violations,
            )
        return violations

    def _check_loose_typevar(
        self,
        node: ast.stmt,
        filepath: Path,
        seq: int,
        violations: MutableSequence[str],
    ) -> tuple[int, MutableSequence[str]]:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            return seq, violations
        func_name = self._get_call_name(node.value.func)
        if func_name not in c.Infra.TYPEVAR_CALLABLES:
            return seq, violations
        target_name = self._get_assign_target_name(node)
        seq += 1
        violations.append(
            f"[NS-002-{seq:03d}] {filepath}:{node.lineno} — TypeVar '{target_name}' belongs in typings.py",
        )
        return seq, violations

    def _check_loose_typealias_annotation(
        self,
        node: ast.stmt,
        filepath: Path,
        seq: int,
        violations: MutableSequence[str],
    ) -> tuple[int, MutableSequence[str]]:
        if not (
            isinstance(node, ast.AnnAssign)
            and self._annotation_contains(node.annotation, "TypeAlias")
        ):
            return seq, violations
        target_name = self._get_target_name(node.target)
        seq += 1
        violations.append(
            f"[NS-002-{seq:03d}] {filepath}:{node.lineno} — TypeAlias '{target_name}' belongs in typings.py",
        )
        return seq, violations

    def _check_loose_pep695_typealias(
        self,
        node: ast.stmt,
        filepath: Path,
        seq: int,
        violations: MutableSequence[str],
    ) -> tuple[int, MutableSequence[str]]:
        if not isinstance(node, ast.TypeAlias):
            return seq, violations
        name = getattr(node, c.Infra.DUNDER_NAME, None)
        name_str = getattr(name, "id", str(name)) if name else "unknown"
        seq += 1
        violations.append(
            f"[NS-002-{seq:03d}] {filepath}:{node.lineno} — PEP 695 TypeAlias '{name_str}' belongs in typings.py",
        )
        return seq, violations

    def check_rule_3(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        """Rule 3 -- Runtime modules use namespaced MRO aliases, not direct local facade imports."""
        violations: MutableSequence[str] = []
        seq = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != f"{c.Infra.PKG_PREFIX_UNDERSCORE}infra":
                continue
            for alias in node.names:
                if self._allows_direct_facade_import(filepath, alias.name):
                    continue
                if not self._is_local_facade_owner_import(alias.name):
                    continue
                seq += 1
                violations.append(
                    f"[NS-003-{seq:03d}] {filepath}:{node.lineno} — Runtime module must use namespaced MRO aliases (c/m/p/t/u) instead of direct import '{alias.name}'",
                )
        return violations

    def _allows_direct_facade_import(self, filepath: Path, imported_name: str) -> bool:
        for prefix, facade_filename, private_dir in self._DIRECT_FACADE_IMPORT_RULES:
            if not imported_name.startswith(prefix):
                continue
            if filepath.name == facade_filename:
                return True
            return private_dir in filepath.parts
        return False

    def _is_local_facade_owner_import(self, imported_name: str) -> bool:
        return any(
            imported_name.startswith(prefix)
            for prefix, _facade_filename, _private_dir in self._DIRECT_FACADE_IMPORT_RULES
        )

    # -- Module-level statement allowlist ---

    def _is_allowed_module_level(
        self,
        node: ast.stmt,
        filepath: Path,
    ) -> bool:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return True
        if self._is_module_docstring(node):
            return True
        if isinstance(node, (ast.Assign, ast.TypeAlias, ast.AnnAssign)):
            return self._is_allowed_assignment(node, filepath)
        return False

    def _is_allowed_assignment(
        self,
        node: ast.Assign | ast.TypeAlias | ast.AnnAssign,
        filepath: Path,
    ) -> bool:
        if isinstance(node, ast.Assign):
            return self._is_allowed_assign(node, filepath)
        if isinstance(node, ast.TypeAlias):
            return bool(filepath.name == c.Infra.TYPINGS_PY)
        return self._is_allowed_ann_assign(node, filepath)

    @staticmethod
    def _is_module_docstring(node: ast.stmt) -> bool:
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )

    def _is_allowed_assign(
        self,
        node: ast.Assign,
        filepath: Path,
    ) -> bool:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in c.Infra.DUNDER_ALLOWED:
                return True
        if len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in c.Infra.ALIAS_NAMES:
                return True
        if isinstance(node.value, ast.Call):
            func_name = self._get_call_name(node.value.func)
            if func_name in c.Infra.TYPEVAR_CALLABLES:
                return bool(filepath.name == c.Infra.TYPINGS_PY)
        return False

    def _is_allowed_ann_assign(
        self,
        node: ast.AnnAssign,
        filepath: Path,
    ) -> bool:
        if self._annotation_contains(node.annotation, "TypeAlias"):
            return bool(filepath.name == c.Infra.TYPINGS_PY)
        if (
            isinstance(node.target, ast.Name)
            and node.target.id.startswith("_")
            and self._annotation_contains(node.annotation, "Final")
        ):
            return bool(filepath.name == c.Infra.CONSTANTS_PY)
        return False


__all__: list[str] = ["FlextInfraNamespaceRules"]
