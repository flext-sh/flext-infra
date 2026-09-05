"""Module, facade, and size rules for strict FLEXT namespaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_infra import c
from flext_infra.validate._namespace_rules.base import FlextInfraNamespaceRulesBase

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraNamespaceRulesStructure(FlextInfraNamespaceRulesBase):
    """Enforce one-class modules and explicit facade composition."""

    _MINIMUM_INFRA_BASES: ClassVar[int] = 2

    @classmethod
    def check_structure(
        cls, tree: object, filepath: Path, *, class_stem: str, is_test_file: bool
    ) -> t.StrSequence:
        """Return structural and logical-size violations for one module."""
        if filepath.name in {"__init__.py", "__version__.py"}:
            return ()
        messages: list[str] = []
        classes = cls.outer_classes(tree)
        expected = f"Tests{class_stem}" if is_test_file else class_stem
        if len(classes) != 1:
            messages.append(
                f"{filepath}:1 — module must declare exactly one top-level class; "
                f"found {len(classes)}"
            )
        for node in classes:
            name = getattr(node, "name", "")
            if expected and isinstance(name, str) and not name.startswith(expected):
                messages.append(
                    f"{filepath}:{cls.line(node)} — class {name!r} must start with "
                    f"{expected!r}"
                )
        for node in getattr(tree, "body", ()) or ():
            kind = cls.kind(node)
            if kind in {"FunctionDef", "AsyncFunctionDef"}:
                messages.append(
                    f"{filepath}:{cls.line(node)} — top-level function is forbidden; "
                    "nest behavior in the module class"
                )
            if kind in {
                "Assign",
                "AnnAssign",
                "TypeAlias",
            } and not cls._dunder_assignment(node):
                messages.append(
                    f"{filepath}:{cls.line(node)} — module alias/data declaration is "
                    "forbidden; use the canonical facade class"
                )
            if kind == "Expr" and not cls._module_docstring(node):
                messages.append(
                    f"{filepath}:{cls.line(node)} — import-time expression is forbidden"
                )
        logical = sum(
            1
            for node in cls.walk(tree)
            if cls.kind(node) in c.Infra.NAMESPACE_LOGICAL_STATEMENT_KINDS
        )
        if logical > c.Infra.NAMESPACE_MAX_LOGICAL_LOC:
            messages.append(
                f"{filepath}:1 — {logical} logical statements exceed the "
                f"{c.Infra.NAMESPACE_MAX_LOGICAL_LOC} limit"
            )
        messages.extend(cls._facade_shape(tree, filepath))
        return cls.violations("NS-STRUCT", messages)

    @classmethod
    def _facade_shape(cls, tree: object, filepath: Path) -> t.StrSequence:
        """Require an explicit outer+Infra MRO on canonical family facades."""
        layer = c.Infra.NAMESPACE_LAYER_BY_FILE.get(filepath.name)
        if layer not in {"c", "t", "p", "m", "u"}:
            return ()
        classes = cls.outer_classes(tree)
        if len(classes) != 1:
            return ()
        outer = classes[0]
        outer_bases = tuple(
            cls.name_of(base) for base in (getattr(outer, "bases", ()) or ())
        )
        nested = tuple(
            node
            for node in (getattr(outer, "body", ()) or ())
            if cls.kind(node) == "ClassDef" and getattr(node, "name", "") == "Infra"
        )
        messages: list[str] = []
        if layer not in outer_bases:
            messages.append(
                f"{filepath}:{cls.line(outer)} — facade must inherit canonical {layer!r}"
            )
        if len(nested) != 1:
            messages.append(
                f"{filepath}:{cls.line(outer)} — facade must declare one nested Infra MRO"
            )
        elif len(getattr(nested[0], "bases", ()) or ()) < cls._MINIMUM_INFRA_BASES:
            messages.append(
                f"{filepath}:{cls.line(nested[0])} — Infra must explicitly compose its "
                "private family through multiple inheritance"
            )
        return tuple(messages)

    @classmethod
    def _dunder_assignment(cls, node: object) -> bool:
        """Allow only the export manifest at module level."""
        targets = (
            getattr(node, "targets", ())
            if cls.kind(node) == "Assign"
            else (getattr(node, "target", None),)
        )
        return any(cls.name_of(target) == "__all__" for target in targets)

    @classmethod
    def _module_docstring(cls, node: object) -> bool:
        """Return whether an expression is a module docstring."""
        value = getattr(node, "value", None)
        return cls.kind(value) == "Constant" and isinstance(
            getattr(value, "value", None), str
        )


__all__: list[str] = ["FlextInfraNamespaceRulesStructure"]
