"""Typing, Pydantic, and dependency-injection namespace rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c
from flext_infra.validate._namespace_rules.base import FlextInfraNamespaceRulesBase

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraNamespaceRulesContracts(FlextInfraNamespaceRulesBase):
    """Reject untyped boundaries, legacy Pydantic, and concrete wiring."""

    @classmethod
    def check_contracts(cls, tree: object, filepath: Path) -> t.StrSequence:
        """Return contract and clean-architecture violations."""
        messages: list[str] = []
        for node in cls.walk(tree):
            kind = cls.kind(node)
            if kind in {"FunctionDef", "AsyncFunctionDef"}:
                messages.extend(cls._function_contract(node, filepath))
            if kind in {"AnnAssign", "arg", "FunctionDef", "AsyncFunctionDef"}:
                messages.extend(cls._annotation_contract(node, filepath))
            if kind == "Call":
                messages.extend(cls._call_contract(node, filepath))
        messages.extend(cls._composition_root(tree, filepath))
        return cls.violations("NS-CONTRACT", messages)

    @classmethod
    def _function_contract(cls, node: object, filepath: Path) -> t.StrSequence:
        """Require typed public input/output boundaries."""
        name = getattr(node, "name", "")
        if not isinstance(name, str) or (name.startswith("_") and name != "__init__"):
            return ()
        messages: list[str] = []
        arguments = getattr(node, "args", None)
        positional = (
            *(getattr(arguments, "posonlyargs", ()) or ()),
            *(getattr(arguments, "args", ()) or ()),
            *(getattr(arguments, "kwonlyargs", ()) or ()),
        )
        for argument in positional:
            argument_name = getattr(argument, "arg", "")
            if argument_name in {"self", "cls"}:
                continue
            if getattr(argument, "annotation", None) is None:
                messages.append(
                    f"{filepath}:{cls.line(argument)} — public input {argument_name!r} "
                    "must use a typed model contract"
                )
        if getattr(node, "returns", None) is None:
            messages.append(
                f"{filepath}:{cls.line(node)} — public operation {name!r} must declare "
                "a typed output"
            )
        if name != "__init__" or "services" not in filepath.parts:
            return tuple(messages)
        for argument in positional:
            annotation = getattr(argument, "annotation", None)
            annotation_name = cls.name_of(annotation)
            dotted = cls.dotted_name(annotation)
            if annotation_name.startswith("Flext") and not dotted.startswith("p."):
                messages.append(
                    f"{filepath}:{cls.line(argument)} — service dependency "
                    f"{annotation_name!r} must be injected through p"
                )
        return tuple(messages)

    @classmethod
    def _annotation_contract(cls, node: object, filepath: Path) -> t.StrSequence:
        """Reject broad and legacy annotation vocabulary."""
        annotations: list[object] = []
        if cls.kind(node) == "AnnAssign" or cls.kind(node) == "arg":
            annotations.append(getattr(node, "annotation", None))
        else:
            annotations.append(getattr(node, "returns", None))
        messages: list[str] = []
        for annotation in annotations:
            if annotation is None:
                continue
            names = {
                cls.name_of(candidate)
                for candidate in cls.walk(annotation)
                if cls.name_of(candidate)
            }
            banned = sorted(names & c.Infra.NAMESPACE_BANNED_ANNOTATIONS)
            if banned:
                messages.append(
                    f"{filepath}:{cls.line(node)} — banned annotation(s): "
                    + ", ".join(banned)
                )
        return tuple(messages)

    @classmethod
    def _call_contract(cls, node: object, filepath: Path) -> t.StrSequence:
        """Reject legacy Pydantic calls and service-locator access."""
        callable_node = getattr(node, "func", None)
        name = cls.name_of(callable_node)
        messages: list[str] = []
        if name in c.Infra.NAMESPACE_PYDANTIC_V1_MEMBERS:
            messages.append(
                f"{filepath}:{cls.line(node)} — legacy Pydantic member {name!r}; "
                "use Pydantic v2"
            )
        if name in c.Infra.NAMESPACE_SERVICE_LOCATOR_NAMES:
            messages.append(
                f"{filepath}:{cls.line(node)} — service locator {name!r} is forbidden; "
                "inject p contracts"
            )
        return tuple(messages)

    @classmethod
    def _composition_root(cls, tree: object, filepath: Path) -> t.StrSequence:
        """Permit effectful construction only inside the public API class."""
        if filepath.name == "api.py":
            return ()
        messages: list[str] = []
        for node in getattr(tree, "body", ()) or ():
            if cls.kind(node) not in {"Assign", "AnnAssign"}:
                continue
            value = getattr(node, "value", None)
            if cls.kind(value) == "Call":
                messages.append(
                    f"{filepath}:{cls.line(node)} — import-time wiring is forbidden; "
                    "compose dependencies in api.py"
                )
        return tuple(messages)


__all__: list[str] = ["FlextInfraNamespaceRulesContracts"]
