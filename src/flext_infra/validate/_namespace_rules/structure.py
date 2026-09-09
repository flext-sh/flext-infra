"""Module, facade, and size rules for strict FLEXT namespaces."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c

from .base import FlextInfraNamespaceRulesBase

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraNamespaceRulesStructure(FlextInfraNamespaceRulesBase):
    """Enforce one-class modules and explicit facade composition."""

    @classmethod
    def check_structure(
        cls,
        tree: object,
        filepath: Path,
        *,
        class_stem: str,
        package_name: str,
        is_test_file: bool,
    ) -> t.StrSequence:
        """Return structural and logical-size violations for one module."""
        if filepath.name in {"__init__.py", "__version__.py"}:
            return ()
        messages: list[str] = []
        classes = cls.outer_classes(tree)
        expected = f"Tests{class_stem}" if is_test_file else class_stem
        if len(classes) < 1:
            messages.append(
                f"{filepath}:1 — module must declare at least one top-level class; "
                f"found {len(classes)}"
            )
        facade_classes = [
            node
            for node in classes
            if isinstance(getattr(node, "name", ""), str)
            and getattr(node, "name", "").startswith(expected)
        ]
        if not facade_classes:
            messages.append(
                f"{filepath}:1 — module must declare at least one class starting with "
                f"{expected!r} (the facade class)"
            )
        for node in facade_classes:
            name = getattr(node, "name", "")
            if expected and isinstance(name, str) and not name.startswith(expected):
                messages.append(
                    f"{filepath}:{cls.line(node)} — class {name!r} must start with "
                    f"{expected!r}"
                )
        # Secondary support classes at module level are allowed in facade modules;
        # only the facade class must satisfy the naming and nesting rules.
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
            } and not (
                cls._dunder_assignment(node)
                or cls._canonical_facade_alias(
                    node,
                    tree,
                    filepath,
                    class_stem=class_stem,
                    package_name=package_name,
                )
            ):
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
        # The nested namespace is named after the project that owns the facade
        # (`FlextLdifModels` nests `Ldif`), so the expected name is derived from
        # the outer class. Naming `Infra` here made the rule pass only inside
        # this project and reject every other member of the fleet.
        namespace = (
            getattr(outer, "name", "")
            .removesuffix(c.Infra.FAMILY_SUFFIXES.get(layer, ""))
            .removeprefix(c.Infra.PKG_PREFIX_UNDERSCORE.rstrip("_").capitalize())
        )
        nested = tuple(
            node
            for node in (getattr(outer, "body", ()) or ())
            if cls.kind(node) == "ClassDef" and getattr(node, "name", "") == namespace
        )
        messages: list[str] = []
        if layer not in outer_bases:
            messages.append(
                f"{filepath}:{cls.line(outer)} — facade must inherit canonical {layer!r}"
            )
        if len(nested) != 1:
            messages.append(
                f"{filepath}:{cls.line(outer)} — facade must declare one nested "
                f"{namespace} MRO"
            )
        elif len(getattr(nested[0], "bases", ()) or ()) < c.Infra.FACADE_MINIMUM_BASES:
            messages.append(
                f"{filepath}:{cls.line(nested[0])} — {namespace} must explicitly "
                "compose its private family through multiple inheritance"
            )
        return tuple(messages)

    @classmethod
    def _canonical_facade_alias(
        cls,
        node: object,
        tree: object,
        filepath: Path,
        *,
        class_stem: str,
        package_name: str,
    ) -> bool:
        """Recognize the required bottom alias only at its discovered public owner."""
        spec = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS.get(filepath.name)
        if spec is None or filepath.parent != Path(c.Infra.DEFAULT_SRC_DIR).joinpath(
            *package_name.split(".")
        ):
            return False
        alias, suffix = spec
        classes = cls.outer_classes(tree)
        if len(classes) != 1 or getattr(classes[0], "name", "") != (
            class_name := f"{class_stem}{suffix}"
        ):
            return False
        targets = getattr(node, "targets", ())
        value = getattr(node, "value", None)
        if not (
            cls.kind(node) == "Assign"
            and len(targets) == 1
            and cls.kind(targets[0]) == "Name"
            and cls.name_of(targets[0]) == alias
            and cls.kind(value) == "Name"
            and cls.name_of(value) == class_name
            and cls.line(node) > cls.line(classes[0])
        ):
            return False
        return all(
            cls._dunder_assignment(statement)
            for statement in (getattr(tree, "body", ()) or ())
            if cls.line(statement) > cls.line(node)
        )

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
