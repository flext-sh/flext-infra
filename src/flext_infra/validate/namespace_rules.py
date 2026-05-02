"""Namespace validation rules (rules 0-3) for flext projects.

AST-helper layer used by ``FlextInfraNamespaceValidator``. The validator
sources AST modules via rope (``pymodule.get_ast()``) per the flext-infra
detector mandate; this module operates on the resulting ``ast.Module``
trees without performing its own source reads.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraNamespaceRules:
    """Implementation of namespace rules 0-3 for AST-based validation."""

    _DIRECT_FACADE_SUFFIX_RULES = (
        ("Constants", c.Infra.CONSTANTS_PY, c.Infra.FAMILY_DIRECTORIES["c"]),
        ("Models", c.Infra.MODELS_PY, c.Infra.FAMILY_DIRECTORIES["m"]),
        ("Protocols", c.Infra.PROTOCOLS_PY, c.Infra.FAMILY_DIRECTORIES["p"]),
        ("Types", c.Infra.TYPINGS_PY, c.Infra.FAMILY_DIRECTORIES["t"]),
        ("Utilities", c.Infra.UTILITIES_PY, c.Infra.FAMILY_DIRECTORIES["u"]),
    )

    @staticmethod
    def _is_private_dir_file(filepath: Path) -> bool:
        """Return True if the file is inside a private (_xxx) directory."""
        return any(
            part.startswith("_") and not part.startswith("__")
            for part in filepath.parts
            if "." not in part
        )

    @staticmethod
    def _is_type_checking_guard(node: ast.stmt) -> bool:
        """Return True if the node is an `if TYPE_CHECKING:` block."""
        return (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        )

    @staticmethod
    def _annotation_contains(annotation: ast.expr | None, name: str) -> bool:
        return name in (ast.unparse(annotation) if annotation else "")

    def target_name(self, target: ast.expr | None) -> str:
        """Return the bare-identifier name when ``target`` is ``ast.Name``."""
        match target:
            case ast.Name(id=name):
                return name
            case _:
                return ""

    def call_name(self, func: ast.expr | None) -> str:
        """Return the trailing attribute/identifier of a call's callable."""
        unparsed = ast.unparse(func) if func else ""
        return unparsed.rsplit(".", maxsplit=1)[-1]

    def _accumulate_violations(
        self,
        rule_prefix: str,
        messages: Iterable[str],
    ) -> t.StrSequence:
        return [
            f"[{rule_prefix}-{i:03d}] {msg}" for i, msg in enumerate(messages, start=1)
        ]

    def check_rule_0(
        self,
        tree: ast.Module,
        filepath: Path,
        prefix: str,
    ) -> t.StrSequence:
        """Rule 0 -- One namespace class per module."""
        outer_classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        class_count = len(outer_classes)
        messages: t.MutableSequenceOf[str] = []
        if class_count != 1:
            messages.append(
                f"{filepath}:{(outer_classes[0].lineno if outer_classes else 1)} — Multiple outer classes found (expected 1, got {class_count})"
                if class_count > 1
                else f"{filepath}:1 — No outer class found (expected 1, got 0)"
            )
        for cls in outer_classes:
            if prefix and not cls.name.startswith(prefix):
                messages.append(
                    f"{filepath}:{cls.lineno} — Class '{cls.name}' does not start with prefix '{prefix}'"
                )
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                continue
            if not self._is_allowed_module_level(node, filepath):
                lineno = getattr(node, "lineno", 0)
                messages.append(
                    f"{filepath}:{lineno} — Disallowed top-level statement: {type(node).__name__}"
                )
        return self._accumulate_violations("NS-000", messages)

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
        messages: t.MutableSequenceOf[str] = []
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            base_strs = {ast.unparse(b) for b in cls.bases}
            if not any("Constants" in b or b == "c" for b in base_strs):
                messages.append(
                    f"{filepath}:{cls.lineno} — Constants class '{cls.name}' must inherit from a Constants base"
                )
            for inner_node in ast.walk(cls):
                if isinstance(inner_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    messages.append(
                        f"{filepath}:{inner_node.lineno} — Method '{inner_node.name}' found in Constants class"
                    )
        return self._accumulate_violations("NS-001", messages)

    def _check_rule_1_non_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        messages: t.MutableSequenceOf[str] = []
        for node in tree.body:
            messages.extend(self._check_loose_final(node, filepath))
            messages.extend(self._check_loose_collection(node, filepath))
        if filepath.parent.name != "_constants":
            for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                messages.extend(self._check_loose_enums(cls, filepath))
        return self._accumulate_violations("NS-001", messages)

    def _check_loose_final(
        self,
        node: ast.stmt,
        filepath: Path,
    ) -> t.StrSequence:
        if not (
            isinstance(node, ast.AnnAssign)
            and self._annotation_contains(node.annotation, "Final")
        ):
            return []
        target_name = self.target_name(node.target)
        if target_name and not target_name.startswith("_"):
            return [
                f"{filepath}:{node.lineno} — Loose Final constant '{target_name}' belongs in constants.py"
            ]
        return []

    def _check_loose_collection(
        self,
        node: ast.stmt,
        filepath: Path,
    ) -> t.StrSequence:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            return []
        func_name = self.call_name(node.value.func)
        if func_name not in c.Infra.COLLECTION_CALLS:
            return []
        target_name = self.target_name(node.targets[0] if node.targets else None)
        if (
            target_name
            and target_name not in c.Infra.DUNDER_ALLOWED
            and target_name not in c.Infra.ALIAS_NAMES
        ):
            return [
                f"{filepath}:{node.lineno} — Loose collection constant '{target_name}' belongs in constants.py"
            ]
        return []

    def _check_loose_enums(
        self,
        cls: ast.ClassDef,
        filepath: Path,
    ) -> t.StrSequence:
        messages: t.MutableSequenceOf[str] = []
        for inner in cls.body:
            if isinstance(inner, ast.ClassDef) and any(
                ast.unparse(b) == base
                for b in inner.bases
                for base in c.Infra.ENUM_BASES
            ):
                messages.append(
                    f"{filepath}:{inner.lineno} — Loose Enum '{inner.name}' belongs in constants.py"
                )
        return messages

    def check_rule_2(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        """Rule 2 -- Types centralization."""
        if filepath.name == c.Infra.TYPINGS_PY:
            return self._check_rule_2_canonical(tree, filepath)
        if filepath.parent.name == c.Infra.FAMILY_DIRECTORIES["t"]:
            return []
        return self._check_rule_2_non_canonical(tree, filepath)

    def _check_rule_2_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        messages: t.MutableSequenceOf[str] = []
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            base_strs = {ast.unparse(b) for b in cls.bases}
            if not any("Types" in b or b == "t" for b in base_strs):
                messages.append(
                    f"{filepath}:{cls.lineno} — Types class '{cls.name}' must inherit from a Types base"
                )
            for inner in cls.body:
                if isinstance(
                    inner, ast.ClassDef
                ) and self._inner_inherits_forbidden_base(inner):
                    messages.append(
                        f"{filepath}:{inner.lineno} — Inner class '{inner.name}' in Types must not inherit from BaseModel/Protocol"
                    )
        return self._accumulate_violations("NS-002", messages)

    def _inner_inherits_forbidden_base(
        self,
        inner: ast.ClassDef,
    ) -> bool:
        forbidden = {"BaseModel", "Protocol"}
        return any(ast.unparse(base) in forbidden for base in inner.bases)

    def _check_rule_2_non_canonical(
        self,
        tree: ast.Module,
        filepath: Path,
    ) -> t.StrSequence:
        messages: t.MutableSequenceOf[str] = []
        for node in tree.body:
            messages.extend(self._check_loose_typevar(node, filepath))
            messages.extend(self._check_loose_typealias_annotation(node, filepath))
            messages.extend(self._check_loose_pep695_typealias(node, filepath))
        return self._accumulate_violations("NS-002", messages)

    def _check_loose_typevar(
        self,
        node: ast.stmt,
        filepath: Path,
    ) -> t.StrSequence:
        if not (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)):
            return []
        func_name = self.call_name(node.value.func)
        if func_name not in c.Infra.TYPEVAR_CALLABLES:
            return []
        target_name = self.target_name(node.targets[0] if node.targets else None)
        return [
            f"{filepath}:{node.lineno} — TypeVar '{target_name}' belongs in typings.py"
        ]

    def _check_loose_typealias_annotation(
        self,
        node: ast.stmt,
        filepath: Path,
    ) -> t.StrSequence:
        if not (
            isinstance(node, ast.AnnAssign)
            and self._annotation_contains(node.annotation, "TypeAlias")
        ):
            return []
        target_name = self.target_name(node.target)
        return [
            f"{filepath}:{node.lineno} — TypeAlias '{target_name}' belongs in typings.py"
        ]

    def _check_loose_pep695_typealias(
        self,
        node: ast.stmt,
        filepath: Path,
    ) -> t.StrSequence:
        if not isinstance(node, ast.TypeAlias):
            return []
        name = getattr(node, c.Infra.DUNDER_NAME, None)
        name_str = getattr(name, "id", str(name)) if name else "unknown"
        return [
            f"{filepath}:{node.lineno} — PEP 695 TypeAlias '{name_str}' belongs in typings.py"
        ]

    def check_rule_3(
        self,
        tree: ast.Module,
        filepath: Path,
        *,
        class_stem: str,
        package_name: str,
    ) -> t.StrSequence:
        """Rule 3 -- Runtime modules use namespaced MRO aliases, not direct local facade imports."""
        if self._is_private_dir_file(filepath):
            return []
        messages: t.MutableSequenceOf[str] = []
        owner_rules = self._owner_direct_facade_rules(class_stem)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != package_name:
                continue
            for alias in node.names:
                if self._allows_direct_facade_import(filepath, alias.name, owner_rules):
                    continue
                if not self._is_local_facade_owner_import(alias.name, owner_rules):
                    continue
                messages.append(
                    f"{filepath}:{node.lineno} — Runtime module must use namespaced MRO aliases (c/m/p/t/u) instead of direct import '{alias.name}'"
                )
        return self._accumulate_violations("NS-003", messages)

    def _allows_direct_facade_import(
        self,
        filepath: Path,
        imported_name: str,
        owner_rules: tuple[tuple[str, str, str], ...],
    ) -> bool:
        for prefix, facade_filename, private_dir in owner_rules:
            if not imported_name.startswith(prefix):
                continue
            if filepath.name == facade_filename:
                return True
            if private_dir in filepath.parts:
                return True
        return False

    def _is_local_facade_owner_import(
        self,
        imported_name: str,
        owner_rules: tuple[tuple[str, str, str], ...],
    ) -> bool:
        return any(
            imported_name.startswith(prefix)
            for prefix, _facade_filename, _private_dir in owner_rules
        )

    def _owner_direct_facade_rules(
        self,
        class_stem: str,
    ) -> tuple[tuple[str, str, str], ...]:
        return tuple(
            (f"{class_stem}{suffix}", facade_filename, private_dir)
            for suffix, facade_filename, private_dir in self._DIRECT_FACADE_SUFFIX_RULES
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
        if self._is_type_checking_guard(node):
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
            # TypeAlias allowed in typings.py and _typings/ sub-modules.
            return (
                filepath.name == c.Infra.TYPINGS_PY
                or filepath.parent.name == c.Infra.FAMILY_DIRECTORIES["t"]
            )
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
            func_name = self.call_name(node.value.func)
            if func_name in c.Infra.TYPEVAR_CALLABLES:
                # TypeVar allowed in typings.py and _typings/ sub-modules.
                return (
                    filepath.name == c.Infra.TYPINGS_PY
                    or filepath.parent.name == c.Infra.FAMILY_DIRECTORIES["t"]
                )
        return False

    def _is_allowed_ann_assign(
        self,
        node: ast.AnnAssign,
        filepath: Path,
    ) -> bool:
        # __all__: list[str] = [...] and other dunders with annotations are always allowed.
        if (
            isinstance(node.target, ast.Name)
            and node.target.id in c.Infra.DUNDER_ALLOWED
        ):
            return True
        if self._annotation_contains(node.annotation, "TypeAlias"):
            # TypeAlias allowed in typings.py and _typings/ sub-modules.
            return (
                filepath.name == c.Infra.TYPINGS_PY
                or filepath.parent.name == c.Infra.FAMILY_DIRECTORIES["t"]
            )
        if (
            isinstance(node.target, ast.Name)
            and node.target.id.startswith("_")
            and self._annotation_contains(node.annotation, "Final")
        ):
            # Private Final constants allowed in constants.py and _constants/ sub-modules.
            return (
                filepath.name == c.Infra.CONSTANTS_PY
                or filepath.parent.name == "_constants"
            )
        return False


__all__: list[str] = ["FlextInfraNamespaceRules"]
