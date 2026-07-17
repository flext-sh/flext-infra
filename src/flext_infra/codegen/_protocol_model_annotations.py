"""Render concrete model annotations as structural protocol annotations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import abc
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import (
    Annotated,
    ClassVar,
    ForwardRef,
    Literal,
    TypeAliasType,
    get_args,
    get_origin,
)

from flext_infra import c, m, p, t


class FlextInfraCodegenProtocolModelAnnotations:
    """Map validated runtime model types to public protocol-facade types."""

    _ORIGINS: ClassVar[t.MappingKV[type, str]] = {
        list: "list",
        tuple: "tuple",
        dict: "dict",
        set: "set",
        frozenset: "frozenset",
        type: "type",
        abc.Sequence: "Sequence",
        abc.Mapping: "Mapping",
        abc.MutableSequence: "MutableSequence",
        abc.MutableMapping: "MutableMapping",
        abc.Set: "AbstractSet",
        abc.MutableSet: "MutableSet",
        abc.Iterable: "Iterable",
        abc.Iterator: "Iterator",
        abc.Callable: "Callable",
    }
    _MODEL_REF = c.Infra.compile(r"FlextInfra(?:Config)?Models\w*\.([A-Z]\w*)")
    _ANNOTATED_PREFIX = "Annotated["
    _BANNED = frozenset({"Any", "object", "typing.Any"})

    @classmethod
    def render(cls, annotation: t.TypeHintSpecifier | None) -> str:
        """Render one field/property type without exposing a concrete model."""
        if isinstance(annotation, ForwardRef):
            return cls._render_forward(annotation.__forward_arg__)
        if isinstance(annotation, str):
            return cls._render_forward(annotation)
        if annotation is None or annotation is type(None):
            return "None"
        if isinstance(annotation, TypeAliasType):
            return cls.render(annotation.__value__)
        origin = get_origin(annotation)
        arguments = get_args(annotation)
        if origin is Annotated:
            return cls.render(arguments[0])
        if origin in {UnionType, type(int | str)}:
            return " | ".join(cls.render(argument) for argument in arguments)
        if origin is Literal:
            return f"Literal[{', '.join(repr(argument) for argument in arguments)}]"
        if origin is abc.Callable:
            parameters, return_type = arguments
            if parameters is Ellipsis:
                rendered_parameters = "..."
            elif isinstance(parameters, list):
                rendered_parameters = ", ".join(
                    cls.render(parameter) for parameter in parameters
                )
            else:
                msg = f"unsupported Callable parameters: {parameters!r}"
                raise TypeError(msg)
            return f"Callable[[{rendered_parameters}], {cls.render(return_type)}]"
        if origin is not None:
            rendered_origin = cls._ORIGINS.get(origin)
            if rendered_origin is None:
                rendered_origin = cls._facade_name(origin)
            if rendered_origin is None:
                msg = f"unsupported protocol annotation origin: {origin!r}"
                raise TypeError(msg)
            rendered_arguments = ", ".join(
                "..." if argument is Ellipsis else cls.render(argument)
                for argument in arguments
            )
            return (
                f"{rendered_origin}[{rendered_arguments}]"
                if rendered_arguments
                else rendered_origin
            )
        if isinstance(annotation, type):
            if issubclass(annotation, m.BaseModel):
                if annotation.__module__.startswith("flext_infra._models"):
                    return f"p.Infra.{annotation.__name__}"
                facade_name = cls._facade_name(annotation)
                if facade_name is not None:
                    return facade_name
            if issubclass(annotation, Enum) and hasattr(c.Infra, annotation.__name__):
                return f"c.Infra.{annotation.__name__}"
            if annotation.__module__ == "builtins":
                return cls._validate(annotation.__name__)
            if annotation is Path:
                return "Path"
            if annotation.__module__ == "datetime":
                return annotation.__name__
            if annotation.__module__ == "uuid":
                return annotation.__name__
            facade_name = cls._facade_name(annotation)
            if facade_name is not None:
                return facade_name
        facade_name = cls._facade_name(annotation)
        if facade_name is not None:
            return facade_name
        msg = f"unsupported protocol annotation: {annotation!r}"
        raise TypeError(msg)

    @classmethod
    def _facade_name(cls, value: t.TypeHintSpecifier) -> str | None:
        """Return the existing public facade path for an identical runtime type."""
        for prefix, facade in (
            ("p.Infra", p.Infra),
            ("p.Cli", p.Cli),
            ("p", p),
            ("c.Infra", c.Infra),
            ("t.Infra", t.Infra),
            ("t", t),
        ):
            for name in dir(facade):
                if getattr(facade, name) is value:
                    return f"{prefix}.{name}"
        return None

    @classmethod
    def _render_forward(cls, annotation: str) -> str:
        """Normalize a postponed source annotation without evaluating Field data."""
        rendered = annotation.strip()
        if rendered.startswith(cls._ANNOTATED_PREFIX):
            rendered = cls._first_annotated_argument(rendered)
        rendered = cls._MODEL_REF.sub(r"p.Infra.\1", rendered)
        rendered = rendered.replace("m.Infra.", "p.Infra.")
        return cls._validate(rendered)

    @classmethod
    def _first_annotated_argument(cls, annotation: str) -> str:
        """Extract the first top-level argument from ``Annotated[...]``."""
        content = annotation[len(cls._ANNOTATED_PREFIX) : -1]
        depth = 0
        for index, character in enumerate(content):
            if character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
            elif character == "," and depth == 0:
                return content[:index].strip()
        msg = f"malformed Annotated protocol field: {annotation}"
        raise ValueError(msg)

    @classmethod
    def _validate(cls, rendered: str) -> str:
        """Reject escape-hatch types from generated public contracts."""
        tokens = frozenset(
            c.Infra.compile(r"[A-Za-z_][A-Za-z0-9_.]*").findall(rendered)
        )
        banned = tokens.intersection(cls._BANNED)
        if banned:
            msg = f"forbidden generated protocol annotation: {sorted(banned)}"
            raise TypeError(msg)
        return rendered


__all__: list[str] = ["FlextInfraCodegenProtocolModelAnnotations"]
