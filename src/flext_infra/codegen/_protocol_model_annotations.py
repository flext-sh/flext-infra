"""Render native annotations through the project's declared public facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
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

from flext_infra import p, t
from flext_infra._utilities._semantic_cutover.declaration_relocation import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)


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

    @staticmethod
    def _identity(value: p.Infra.RopePyObject) -> str:
        module = value.get_module()
        scope = value.get_scope()
        names = [value.get_name()]
        while scope is not None and scope.parent is not None:
            scope = scope.parent
            if scope.get_kind() == "Class":
                names.append(scope.pyobject.get_name())
        return f"{module.get_name() if module is not None else ''}.{'.'.join(reversed(names))}"

    def source(self, annotation: str, scope: p.Infra.RopeScope) -> str:
        """Rewrite bound type identities without changing literal payloads."""
        owner = FlextInfraUtilitiesSemanticDeclarationRelocation
        for name, declaration in self.declarations.items():
            annotation = owner.quoted_identity_source(
                self.workspace.rope_project,
                scope,
                annotation,
                declaration,
                f"_public.p.{name}",
            )
        return annotation

    def render(
        self,
        annotation: t.TypeHintSpecifier | None,
        scope: p.Infra.RopeScope,
    ) -> str:
        """Render native annotation forms; unsupported forms fail unchanged."""
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
            return f"collections.abc.Callable[{arguments_text}, {self.render(result, scope)}]"
        if origin is not None:
            rendered = ", ".join(
                "..." if argument is Ellipsis else self.render(argument, scope)
                for argument in arguments
            )
            return f"{self.render(origin, scope)}[{rendered}]"
        if not isinstance(annotation, type):
            msg = f"unsupported protocol annotation: {annotation!r}"
            raise TypeError(msg)
        identity = f"{annotation.__module__}.{annotation.__qualname__}"
        if identity in self.names:
            return f"_public.p.{self.names[identity]}"
        for letter, facade in self.facades.items():
            if letter == "m":
                continue
            namespaces = [("", facade)]
            while namespaces:
                prefix, namespace = namespaces.pop()
                for name, member in vars(namespace).items():
                    if member is annotation:
                        return f"_public.{letter}.{prefix}{name}"
                    if (
                        isinstance(member, type)
                        and member.__module__.startswith(
                            f"{self.project.package_name}."
                        )
                        and not hasattr(member, "model_fields")
                        and not name.startswith("_")
                    ):
                        namespaces.append((f"{prefix}{name}.", member))
        if identity in {"builtins.object", "typing.Any"}:
            msg = f"forbidden generated protocol annotation: {identity}"
            raise TypeError(msg)
        if annotation.__module__ == "builtins":
            return annotation.__qualname__
        self.imports[annotation.__module__] = f"import {annotation.__module__}"
        return identity


__all__: list[str] = ["FlextInfraCodegenProtocolModelAnnotations"]
