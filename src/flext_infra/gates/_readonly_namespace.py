"""Conservative source authentication for readonly namespace declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
from pathlib import Path

from flext_infra import m


class FlextInfraReadonlyNamespace:
    """Authenticate declarations without importing project code or settings.

    Unsupported type expressions and ambiguous bindings are errors, not a
    structural-subtyping guess. Ruff remains the naming-binding authority.
    """

    def __init__(self, paths: tuple[Path, ...]) -> None:
        self.modules: dict[str, tuple[Path, ast.Module]] = {}
        for path in paths:
            if path.suffix not in {".py", ".pyi"}:
                continue
            parts = [] if path.stem == "__init__" else [path.stem]
            parent = path.parent
            while (parent / "__init__.py").is_file() or (
                parent / "__init__.pyi"
            ).is_file():
                parts.insert(0, parent.name)
                parent = parent.parent
            module = ".".join(parts)
            if not module or module in self.modules:
                msg = f"Ambiguous readonly namespace module: {path}"
                raise ValueError(msg)
            self.modules[module] = (
                path,
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path)),
            )

    @staticmethod
    def _spelling(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{FlextInfraReadonlyNamespace._spelling(node.value)}.{node.attr}"
        msg = "Unsupported readonly namespace symbol expression"
        raise ValueError(msg)

    @staticmethod
    def _bindings(tree: ast.AST, name: str) -> list[ast.AST]:
        """Include imports and stores, not just function declarations."""
        return [
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name
            )
            or (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and node.id == name
            )
            or (isinstance(node, ast.arg) and node.arg == name)
            or (
                isinstance(node, ast.alias)
                and (
                    node.name == "*" or (node.asname or node.name.split(".")[0]) == name
                )
            )
            or (isinstance(node, ast.ExceptHandler) and node.name == name)
            or (isinstance(node, ast.MatchAs) and node.name == name)
            or (isinstance(node, ast.MatchStar) and node.name == name)
            or (isinstance(node, ast.MatchMapping) and node.rest == name)
        ]

    @classmethod
    def _typing_symbol(cls, tree: ast.Module, name: str) -> bool:
        imports = [
            alias
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module in {"typing", "typing_extensions"}
            and not node.level
            for alias in node.names
            if alias.name == name and alias.asname is None
        ]
        return bool(imports) and cls._bindings(tree, name) == imports

    @classmethod
    def _declaration(
        cls, tree: ast.Module | ast.ClassDef, qualname: str
    ) -> ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.AnnAssign:
        head, separator, tail = qualname.partition(".")
        candidates = [
            node
            for node in tree.body
            if (
                isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == head
            )
            or (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == head
            )
        ]
        if len(candidates) != 1 or len(cls._bindings(tree, head)) != 1:
            msg = f"Missing, rebound, or ambiguous readonly declaration: {qualname}"
            raise ValueError(msg)
        node = candidates[0]
        if separator:
            if not isinstance(node, ast.ClassDef):
                msg = f"Readonly namespace owner is not a class: {qualname}"
                raise ValueError(msg)
            return cls._declaration(node, tail)
        return node

    def _owner(
        self, identity: str
    ) -> tuple[ast.Module, str, ast.ClassDef | ast.AnnAssign]:
        candidates = [
            module for module in self.modules if identity.startswith(f"{module}.")
        ]
        if not candidates:
            msg = f"Unavailable or ambiguous readonly type owner: {identity}"
            raise ValueError(msg)
        module = max(candidates, key=len)
        tree = self.modules[module][1]
        node = self._declaration(tree, identity.removeprefix(f"{module}."))
        if not isinstance(node, (ast.ClassDef, ast.AnnAssign)):
            msg = f"Readonly producer or return owner is not a typed declaration: {identity}"
            raise ValueError(msg)
        return tree, module, node

    @classmethod
    def _getter(cls, tree: ast.Module, node: ast.AST) -> ast.FunctionDef:
        if not isinstance(node, ast.FunctionDef):
            msg = "Readonly namespace must be a synchronous instance getter"
            raise ValueError(msg)
        args = node.args
        positional = [*args.posonlyargs, *args.args]
        if (
            len(positional) != 1
            or positional[0].arg != "self"
            or args.defaults
            or args.kw_defaults
            or args.kwonlyargs
            or args.vararg
            or args.kwarg
            or node.type_params
            or len(node.decorator_list) != 1
            or not isinstance(node.decorator_list[0], ast.Name)
            or node.decorator_list[0].id != "property"
            or cls._bindings(tree, "property")
            or node.returns is None
        ):
            msg = "Readonly namespace requires an unshadowed builtin property without extra arguments"
            raise ValueError(msg)
        return node

    @classmethod
    def _protocol(cls, tree: ast.Module, node: ast.AST) -> ast.ClassDef:
        if (
            not isinstance(node, ast.ClassDef)
            or node.keywords
            or node.type_params
            or not cls._typing_symbol(tree, "Protocol")
            or not any(
                isinstance(base, ast.Name) and base.id == "Protocol"
                for base in node.bases
            )
        ):
            msg = "Readonly namespace owner must be a real explicitly declared Protocol"
            raise ValueError(msg)
        for decorator in node.decorator_list:
            if (
                not isinstance(decorator, ast.Name)
                or decorator.id != "runtime_checkable"
                or not cls._typing_symbol(tree, "runtime_checkable")
            ):
                msg = "Readonly Protocol has an unauthenticated class decorator"
                raise ValueError(msg)
        return node

    @classmethod
    def _field_type(cls, tree: ast.Module, annotation: ast.expr) -> str:
        if isinstance(annotation, ast.Subscript):
            if (
                not isinstance(annotation.value, ast.Name)
                or annotation.value.id != "Annotated"
                or not cls._typing_symbol(tree, "Annotated")
                or not isinstance(annotation.slice, ast.Tuple)
                or not annotation.slice.elts
            ):
                msg = "Readonly return compatibility has an unsupported type expression"
                raise ValueError(msg)
            annotation = annotation.slice.elts[0]
        if (
            not isinstance(annotation, ast.Name)
            or not isinstance(vars(builtins).get(annotation.id), type)
            or annotation.id in {"object", "type"}
            or cls._bindings(tree, annotation.id)
        ):
            msg = "Readonly return compatibility requires an unambiguous concrete builtin field type"
            raise ValueError(msg)
        return annotation.id

    def authenticate(
        self, root: Path, occurrence: m.Infra.RuffReadonlyNamespaceOccurrence
    ) -> tuple[str, int, int]:
        """Return the one native N802 identity supported by source evidence."""
        path = (root / occurrence.path).resolve()
        candidates = [
            (module, tree)
            for module, (source, tree) in self.modules.items()
            if source == path
        ]
        if len(candidates) != 1:
            msg = f"Registered readonly getter is not in the native manifest: {path}"
            raise ValueError(msg)
        module, tree = candidates[0]
        parent_name, _, name = occurrence.qualname.rpartition(".")
        parent = self._protocol(tree, self._declaration(tree, parent_name))
        getter = self._getter(tree, self._declaration(parent, name))
        if getter.returns is None or (
            f"{module}.{self._spelling(getter.returns)}" != occurrence.return_type_owner
        ):
            msg = "Readonly getter return annotation does not identify the registered owner"
            raise ValueError(msg)
        return_tree, _, contract = self._owner(occurrence.return_type_owner)
        contract = self._protocol(return_tree, contract)
        if any(
            not isinstance(base, ast.Name) or base.id != "Protocol"
            for base in contract.bases
        ) or any(
            isinstance(node, (ast.AsyncFunctionDef, ast.AnnAssign))
            for node in contract.body
        ):
            msg = "Readonly return contract has unsupported inherited or non-property members"
            raise ValueError(msg)
        producer_tree, producer_module, producer = self._owner(
            occurrence.producer_qualname
        )
        if (
            not isinstance(producer, ast.AnnAssign)
            or producer.value is None
            or isinstance(producer.value, ast.Constant)
            or self.modules[producer_module][0].suffix != ".py"
        ):
            msg = "Readonly namespace requires a real valued typed producer field"
            raise ValueError(msg)
        producer_parent = occurrence.producer_qualname.rsplit(".", 1)[0]
        _, _, concrete = self._owner(
            f"{producer_parent}.{self._spelling(producer.annotation)}"
        )
        if (
            not isinstance(concrete, ast.ClassDef)
            or concrete.decorator_list
            or concrete.keywords
            or any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                for node in concrete.body
            )
        ):
            msg = "Readonly producer field must identify a concrete source class"
            raise ValueError(msg)
        requirements = [
            node for node in contract.body if isinstance(node, ast.FunctionDef)
        ]
        if not requirements:
            msg = "Readonly return contract has no authenticated readonly members"
            raise ValueError(msg)
        for requirement in requirements:
            member = self._getter(
                return_tree, self._declaration(contract, requirement.name)
            )
            field = self._declaration(concrete, requirement.name)
            if (
                member.returns is None
                or not isinstance(field, ast.AnnAssign)
                or self._field_type(return_tree, member.returns)
                != self._field_type(producer_tree, field.annotation)
            ):
                msg = f"Readonly producer is incompatible with return member: {requirement.name}"
                raise ValueError(msg)
        for _, source_tree in self.modules.values():
            for node in ast.walk(source_tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.ctx, (ast.Store, ast.Del))
                    and node.attr == name
                    and source_tree is tree
                ) or (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"setattr", "delattr", "exec"}
                    and source_tree in {tree, return_tree, producer_tree}
                ):
                    msg = "Readonly namespace has a dynamic or attribute rebinding"
                    raise ValueError(msg)
        return str(path), getter.lineno, getter.col_offset + len("def ") + 1


__all__ = ["FlextInfraReadonlyNamespace"]
