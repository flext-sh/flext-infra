"""Render native annotations through the project's declared public facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from inspect import getmembers_static
from sys import stdlib_module_names
from types import UnionType
from typing import (
    Annotated,
    ForwardRef,
    Literal,
    TypeAliasType,
    Union,
    get_args,
    get_origin,
)

from flext_infra import c, p, t, u


class FlextInfraCodegenProtocolModelAnnotations:
    """Reuse native specialization and identity-bound source annotation rewrites."""

    def __init__(
        self,
        project: p.Infra.ProjectSpec,
        workspace: p.Infra.RopeWorkspaceDsl,
        facades: t.MappingKV[str, p.ModuleOwned],
        declarations: t.MappingKV[str, p.Infra.RopePyName],
    ) -> None:
        self.project = project
        self.workspace = workspace
        self.facades = facades
        self.declarations = declarations
        self.imports: dict[str, str] = {}
        self.names = {
            self._identity(declaration.get_object()): name
            for name, declaration in declarations.items()
        }
        self.public_names: dict[int, str] = {}
        for letter, facade in facades.items():
            if letter == "m":
                continue
            pending = [("", facade)]
            visited: set[int] = set()
            while pending:
                prefix, namespace = pending.pop()
                if id(namespace) in visited:
                    continue
                visited.add(id(namespace))
                for name, member in getmembers_static(namespace):
                    if name.startswith("_") or not isinstance(member, type):
                        continue
                    self.public_names.setdefault(
                        id(member), f"_public.{letter}.{prefix}{name}"
                    )
                    if not hasattr(member, "model_fields"):
                        pending.append((f"{prefix}{name}.", member))

    @staticmethod
    def _identity(value: p.Infra.RopePyObject) -> str:
        module = value.get_module()
        if module is None:
            msg = f"model declaration has no native module: {value.get_name()}"
            raise ValueError(msg)
        scope = value.get_scope()
        names = [value.get_name()]
        while scope is not None and scope.parent is not None:
            scope = scope.parent
            if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
                names.append(scope.pyobject.get_name())
        return f"{module.get_name()}.{'.'.join(reversed(names))}"

    def source(self, annotation: str, scope: p.Infra.RopeScope) -> str:
        """Rewrite bound type identities without changing literal payloads.

        Returns:
            The resulting ``str``.

        """
        roots: list[str] = []

        def replacement(lexical: p.Infra.RopeScope, expression: str) -> str | None:
            changed = self._source_reference(lexical, expression)
            roots.append((expression if changed is None else changed).partition(".")[0])
            return changed

        rendered = u.Infra.rewrite_type_source(
            annotation, self.workspace.rope_project, scope, replacement
        )
        self.record_imports(rendered, scope, roots)
        return rendered

    def _source_reference(
        self, scope: p.Infra.RopeScope, expression: str
    ) -> str | None:
        """Select the declared replacement through its Rope binding.

        Returns:
            The resulting ``str | None``.

        """
        binding = u.Infra.expression_name(scope, expression)
        for name, declaration in self.declarations.items():
            if u.Infra.same_name(declaration, binding):
                return f"_public.p.{name}"
        return None

    def record_imports(
        self,
        source: str,
        scope: p.Infra.RopeScope,
        required: t.SequenceOf[str] = (),
    ) -> None:
        """Reuse native import records for the names retained in a signature.

        Raises:
            ValueError: If protocol annotation has no declaring module.

        """
        module = scope.pyobject.get_module()
        if module is None:
            msg = "protocol annotation has no declaring module"
            raise ValueError(msg)
        roots = {
            *required,
            *(
                source[begin:end].partition(".")[0]
                for begin, end in u.Infra.reference_regions(source)
            ),
        }
        for information in u.Infra.native_import_infos(
            self.workspace.rope_project, module
        ):
            aliases = tuple(
                (name, alias)
                for name, alias in information.names_and_aliases
                if (alias or name.partition(".")[0]) in roots
            )
            if not aliases:
                continue
            imported = (
                u.Infra.from_import(information.module_name, information.level, aliases)
                if isinstance(information, p.Infra.RopeFromImport)
                else u.Infra.normal_import(aliases)
            )
            statement = imported.get_import_statement()
            self.imports[statement] = statement

    def render(
        self,
        annotation: t.TypeFormSpecifier | None,
        scope: p.Infra.RopeScope,
    ) -> str:
        """Render native annotation forms; unsupported forms fail unchanged.

        Returns:
            The resulting ``str``.

        Raises:
            TypeError: If unsupported protocol annotation; or if forbidden generated
                protocol annotation; or if annotation has no declared public facade.

        """
        if annotation is None or annotation is type(None):
            return "None"
        if isinstance(annotation, ForwardRef | str):
            return self.source(
                annotation.__forward_arg__
                if isinstance(annotation, ForwardRef)
                else annotation,
                scope,
            )
        if isinstance(annotation, TypeAliasType):
            return self.render(annotation.__value__, scope)
        origin = get_origin(annotation)
        arguments = get_args(annotation)
        if isinstance(origin, TypeAliasType):
            bindings = dict(zip(origin.__type_params__, arguments, strict=True))
            value = origin.__value__
            for parameter, argument in bindings.items():
                if value is parameter:
                    return self.render(argument, scope)
            parameters = getattr(value, "__parameters__", ())
            if parameters:
                value = value[tuple(bindings[parameter] for parameter in parameters)]
            return self.render(value, scope)
        if origin is Annotated:
            return self.render(arguments[0], scope)
        if origin in {UnionType, Union}:
            return " | ".join(self.render(argument, scope) for argument in arguments)
        if origin is Literal:
            self.imports["typing"] = "import typing"
            return (
                f"typing.Literal[{', '.join(repr(argument) for argument in arguments)}]"
            )
        if origin is Callable:
            parameters, result = arguments
            arguments_text = (
                "..."
                if parameters is Ellipsis
                else f"[{', '.join(self.render(parameter, scope) for parameter in parameters)}]"
            )
            self.imports["collections.abc"] = "import collections.abc"
            return (
                f"collections.abc.Callable[{arguments_text}, "
                f"{self.render(result, scope)}]"
            )
        if origin is not None:
            if origin is tuple and not arguments:
                return "tuple[()]"
            rendered = ", ".join(
                "..." if argument is Ellipsis else self.render(argument, scope)
                for argument in arguments
            )
            return f"{self.render(origin, scope)}[{rendered}]"
        if not isinstance(annotation, type):
            msg = f"unsupported protocol annotation: {annotation!r}"
            raise TypeError(msg)
        identity = f"{annotation.__module__}.{annotation.__qualname__}"
        if identity in {"builtins.object", "typing.Any"}:
            msg = f"forbidden generated protocol annotation: {identity}"
            raise TypeError(msg)
        if annotation.__module__ == "builtins":
            return annotation.__qualname__
        if identity in self.names:
            return f"_public.p.{self.names[identity]}"
        if id(annotation) in self.public_names:
            return self.public_names[id(annotation)]
        if annotation.__module__.partition(".")[0] not in stdlib_module_names:
            msg = f"annotation has no declared public facade: {identity}"
            raise TypeError(msg)
        self.imports[annotation.__module__] = f"import {annotation.__module__}"
        return identity


__all__: list[str] = ["FlextInfraCodegenProtocolModelAnnotations"]
