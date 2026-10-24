"""Conservative source authentication for readonly namespace declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
from pathlib import Path
from typing import TYPE_CHECKING, is_protocol

from flext_infra import c, p, u

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraReadonlyNamespace:
    """Authenticate declarations without importing project code or settings.

    Unsupported type expressions and ambiguous bindings are errors, not a
    structural-subtyping guess. Ruff remains the naming-binding authority.
    """

    def __init__(self, paths: tuple[Path, ...]) -> None:
        """Capture exact native inputs without importing consumer modules.

        Raises:
            ValueError: If a selected source is unavailable.

        """
        self.modules: t.MutableMappingKV[str, tuple[Path, ast.Module]] = {}
        self.ambiguous_modules: set[str] = set()
        self.snapshots: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        for path in paths:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            self.snapshots[path] = state
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
                self.ambiguous_modules.add(module)
                continue
            if state.content is None:
                msg = f"Unavailable readonly namespace source: {path}"
                raise ValueError(msg)
            self.modules[module] = (path, ast.parse(state.content, filename=str(path)))

    def require_unchanged_sources(self) -> None:
        """Reject source races between semantic authentication and native probing.

        Raises:
            ValueError: If a source's exact content or physical identity changed.

        """
        for path, snapshot in self.snapshots.items():
            current = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if current != snapshot:
                msg = f"Readonly namespace source changed during authentication: {path}"
                raise ValueError(msg)

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
        """Include imports and stores, not just function declarations.

        Returns:
            Every potentially competing binding of the spelling.

        """
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
            or (
                isinstance(node, ast.Attribute)
                and isinstance(node.ctx, (ast.Store, ast.Del))
                and node.attr == name
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
            for node in tree.body
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
            if node.decorator_list or node.keywords:
                msg = f"Readonly namespace enclosing class is transformed: {qualname}"
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
        if module in self.ambiguous_modules:
            msg = f"Ambiguous readonly namespace owner module: {module}"
            raise ValueError(msg)
        tree = self.modules[module][1]
        node = self._declaration(tree, identity.removeprefix(f"{module}."))
        if not isinstance(node, (ast.ClassDef, ast.AnnAssign)):
            msg = (
                "Readonly producer or return owner is not a typed declaration: "
                f"{identity}"
            )
            raise TypeError(msg)
        return tree, module, node

    @classmethod
    def _getter(cls, tree: ast.Module, node: ast.AST) -> ast.FunctionDef:
        if not isinstance(node, ast.FunctionDef):
            msg = "Readonly namespace must be a synchronous instance getter"
            raise TypeError(msg)
        args = node.args
        positional = [*args.posonlyargs, *args.args]
        extras = any((
            bool(args.defaults),
            bool(args.kw_defaults),
            bool(args.kwonlyargs),
            args.vararg is not None,
            args.kwarg is not None,
            bool(node.type_params),
        ))
        if len(positional) != 1 or positional[0].arg != "self" or extras:
            msg = (
                "Readonly namespace requires one instance receiver "
                "without extra arguments"
            )
            raise ValueError(msg)
        if (
            len(node.decorator_list) != 1
            or not isinstance(node.decorator_list[0], ast.Name)
            or node.decorator_list[0].id != "property"
            or cls._bindings(tree, "property")
            or node.returns is None
        ):
            msg = (
                "Readonly namespace requires an unshadowed builtin property "
                "and a return annotation"
            )
            raise ValueError(msg)
        for statement in node.body:
            if isinstance(statement, ast.Pass):
                continue
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and (
                    statement.value.value is Ellipsis
                    or isinstance(statement.value.value, str)
                )
            ):
                continue
            msg = "Readonly Protocol getter has an unsupported concrete implementation"
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
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Protocol":
                continue
            if (
                cls._spelling(base) != "p.Cli.Settings"
                or not cls._imported_symbol(tree, "p", "flext_cli.p")
                or not is_protocol(p.Cli.Settings)
            ):
                msg = "Readonly Protocol has unavailable inherited-base metadata"
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
                or not annotation.slice.elts[1:]
            ):
                msg = "Readonly return compatibility has an unsupported type expression"
                raise ValueError(msg)
            annotation = annotation.slice.elts[0]
        if (
            not isinstance(annotation, ast.Name)
            or not isinstance(vars(builtins).get(annotation.id), type)
            or annotation.id
            in {"object", "type", c.Action.LIST, "dict", "set", "frozenset", "tuple"}
            or cls._bindings(tree, annotation.id)
        ):
            msg = (
                "Readonly return compatibility requires an unambiguous "
                "concrete builtin field type"
            )
            raise ValueError(msg)
        return annotation.id

    def authenticate(
        self, root: Path, occurrence: m.Infra.RuffReadonlyNamespaceOccurrence
    ) -> tuple[str, int, int]:
        """Return the one native N802 identity supported by source evidence.

        Returns:
            Exact native filename, row, and name column for the getter.

        Raises:
            ValueError: If identity, ownership, rebinding, or compatibility fails.

        """
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
        if module in self.ambiguous_modules:
            msg = f"Ambiguous readonly namespace getter module: {module}"
            raise ValueError(msg)
        parent_name, _, name = occurrence.qualname.rpartition(".")
        parent = self._protocol(tree, self._declaration(tree, parent_name))
        getter = self._getter(tree, self._declaration(parent, name))
        if getter.returns is None or (
            f"{module}.{self._spelling(getter.returns)}" != occurrence.return_type_owner
        ):
            msg = (
                "Readonly getter return annotation does not identify "
                "the registered owner"
            )
            raise ValueError(msg)
        return_tree, contract = self._return_contract(occurrence.return_type_owner)
        producer_tree, concrete = self._concrete_producer(occurrence.producer_qualname)
        self._require_compatibility(return_tree, contract, producer_tree, concrete)
        self._reject_rebindings(name, (tree, return_tree, producer_tree))
        return str(path), getter.lineno, getter.col_offset + len("def ") + 1

    def _return_contract(self, identity: str) -> tuple[ast.Module, ast.ClassDef]:
        tree, _, node = self._owner(identity)
        contract = self._protocol(tree, node)
        if any(
            not isinstance(base, ast.Name) or base.id != "Protocol"
            for base in contract.bases
        ) or any(
            isinstance(node, (ast.AsyncFunctionDef, ast.AnnAssign))
            for node in contract.body
        ):
            msg = (
                "Readonly return contract has unsupported inherited "
                "or non-property members"
            )
            raise ValueError(msg)
        return tree, contract

    def _concrete_producer(self, identity: str) -> tuple[ast.Module, ast.ClassDef]:
        producer_tree, producer_module, producer = self._owner(identity)
        if (
            not isinstance(producer, ast.AnnAssign)
            or producer.value is None
            or isinstance(producer.value, ast.Constant)
            or self.modules[producer_module][0].suffix != ".py"
        ):
            msg = "Readonly namespace requires a real valued typed producer field"
            raise ValueError(msg)
        producer_parent = identity.rsplit(".", 1)[0]
        _, _, producer_class = self._owner(producer_parent)
        if not isinstance(producer_class, ast.ClassDef) or not self._pydantic_model(
            producer_tree, producer_class
        ):
            msg = "Readonly producer must be a source-authenticated Pydantic model"
            raise ValueError(msg)
        _, _, concrete = self._owner(
            f"{producer_parent}.{self._spelling(producer.annotation)}"
        )
        if (
            not isinstance(concrete, ast.ClassDef)
            or concrete.decorator_list
            or concrete.keywords
            or not self._pydantic_model(producer_tree, concrete)
            or any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                for node in concrete.body
            )
        ):
            msg = "Readonly producer field must identify a concrete source class"
            raise ValueError(msg)
        self._producer_factory(producer_tree, producer)
        return producer_tree, concrete

    @classmethod
    def _imported_symbol(cls, tree: ast.Module, spelling: str, owner: str) -> bool:
        module, _, symbol = owner.rpartition(".")
        imports = [
            alias
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == module
            and not node.level
            for alias in node.names
            if alias.name == symbol and alias.asname is None
        ]
        return bool(imports) and cls._bindings(tree, spelling) == imports

    @classmethod
    def _pydantic_model(cls, tree: ast.Module, node: ast.ClassDef) -> bool:
        return (
            not node.decorator_list
            and not node.keywords
            and bool(node.bases)
            and all(cls._pydantic_base(tree, base) for base in node.bases)
        )

    @classmethod
    def _pydantic_base(cls, tree: ast.Module, base: ast.expr) -> bool:
        name = cls._spelling(base)
        direct = any(
            name == owner.rsplit(".", 1)[1] and cls._imported_symbol(tree, name, owner)
            for owner in (
                "pydantic.BaseModel",
                "pydantic_settings.BaseSettings",
                "flext_core.FlextSettings",
                "flext_cli.FlextCliSettings",
            )
        )
        facade = name == "m.BaseModel" and any(
            cls._imported_symbol(tree, "m", f"{module}.m")
            for module in ("flext_core", "flext_cli")
        )
        return direct or facade

    @classmethod
    def _producer_factory(cls, tree: ast.Module, field: ast.AnnAssign) -> None:
        value = field.value
        if not isinstance(value, ast.Call):
            msg = (
                "Readonly producer requires an authenticated constructor "
                "or field factory"
            )
            raise TypeError(msg)
        factory = cls._spelling(value.func)
        annotation = cls._spelling(field.annotation)
        if factory == annotation and not value.args and not value.keywords:
            return
        field_owner = factory == "Field" and cls._imported_symbol(
            tree, "Field", "pydantic.Field"
        )
        facade_field = factory == "m.Field" and any(
            cls._imported_symbol(tree, "m", f"{module}.m")
            for module in ("flext_core", "flext_cli")
        )
        factories = [
            keyword.value
            for keyword in value.keywords
            if keyword.arg == "default_factory"
        ]
        if (
            not (field_owner or facade_field)
            or value.args
            or any(keyword.arg in {None, "default"} for keyword in value.keywords)
            or len(factories) != 1
            or cls._spelling(factories[0]) != annotation
        ):
            msg = "Readonly producer field factory does not construct its declared type"
            raise ValueError(msg)

    def _require_compatibility(
        self,
        return_tree: ast.Module,
        contract: ast.ClassDef,
        producer_tree: ast.Module,
        concrete: ast.ClassDef,
    ) -> None:
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
                msg = (
                    "Readonly producer is incompatible with return member: "
                    f"{requirement.name}"
                )
                raise ValueError(msg)

    @staticmethod
    def _reject_rebindings(name: str, trees: tuple[ast.Module, ...]) -> None:
        for source_tree in trees:
            for node in ast.walk(source_tree):
                attribute_write = (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.ctx, (ast.Store, ast.Del))
                    and node.attr == name
                )
                dynamic_write = (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id
                    in {
                        "setattr",
                        "delattr",
                        "exec",
                        "eval",
                        "globals",
                        "locals",
                        "vars",
                    }
                )
                subscript_write = isinstance(node, ast.Subscript) and isinstance(
                    node.ctx, (ast.Store, ast.Del)
                )
                if attribute_write or dynamic_write or subscript_write:
                    msg = "Readonly namespace has a dynamic or attribute rebinding"
                    raise ValueError(msg)


__all__ = ["FlextInfraReadonlyNamespace"]
