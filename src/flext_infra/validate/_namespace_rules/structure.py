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
    def _is_functional_module(cls, tree: object) -> bool:
        """Return whether a module only re-exports symbols or runs an entry.

        Why (cosmos-3flk9): the operational ``r/e/x/h/d/s`` re-export modules
        and the ``python -m`` entrypoint stub carry no class by law. The shape
        is derived from the AST — imports, the export manifest, the ``__main__``
        guard and one exit call — so the exemption follows what the module IS,
        never a hardcoded list of file names.
        """
        statements = tuple(getattr(tree, "body", ()) or ())
        if cls.outer_classes(tree):
            return False
        entry_calls: list[str] = []
        for statement in statements:
            kind = cls.kind(statement)
            if kind in {"Import", "ImportFrom"}:
                continue
            if cls._module_docstring(statement):
                continue
            if kind == "Assign" and cls._dunder_assignment(statement):
                continue
            if kind == "Raise":
                continue
            if kind == "If":
                guard_calls = [
                    node
                    for node in cls.walk(statement)
                    if cls.kind(node) == "FunctionDef"
                ]
                entry_calls.extend(cls.name_of(node) for node in guard_calls)
                continue
            if kind == "Expr" and cls.kind(
                getattr(statement, "value", None)
            ) == "Call":
                called = cls.dotted_name(
                    getattr(getattr(statement, "value", None), "func", None)
                )
                entry_calls.append(called.rsplit(".", 1)[-1])
                continue
            # A non-dunder assignment, a type alias or any other statement is
            # loose data: the module is a data module and stays fully graded.
            return False
        # A guard must terminate the process through the package entrypoint
        # (``raise SystemExit(main())`` / ``main()``); without it the module
        # is not an entrypoint and stays under the class rules.
        return bool(entry_calls) and all(
            name.endswith("main") for name in entry_calls
        )

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
        if cls._is_functional_module(tree):
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
            if kind in {"FunctionDef", "AsyncFunctionDef"} and not (
                filepath.name == "cli.py" and cls.name_of(node) == "main"
            ):
                messages.append(
                    f"{filepath}:{cls.line(node)} — top-level function is forbidden; "
                    "nest behavior in the module class"
                )
            if kind in {"Assign", "AnnAssign"} and not (
                cls._dunder_assignment(node)
                or cls._canonical_facade_alias(
                    node,
                    tree,
                    filepath,
                    class_stem=class_stem,
                    package_name=package_name,
                )
                or (
                    filepath.name == "api.py"
                    and cls.kind(node) == "AnnAssign"
                    and (
                        cls.name_of(
                            facade_value := getattr(node, "value", None)
                        )
                        == class_stem
                        or (
                            cls.kind(facade_value) == "Call"
                            and cls.dotted_name(getattr(facade_value, "func", None))
                            == f"{class_stem}.fetch_global"
                        )
                    )
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
        """Recognize the required bottom alias only at its discovered public owner.

        Canonical facade singletons come in two codegen-emitted forms:
        a plain ``alias = Class`` (e.g. ``s = FlextApiServiceBase``) and the
        typed global-fetcher ``alias: Class = Class.fetch_global()`` (e.g.
        ``api = FlextApi.fetch_global()``). Both are permitted only on the
        canonical facade files registered in NAMESPACE_FAMILY_EXPECTED_ALIAS
        (constants/typings/protocols/models/utilities) and on the platform
        service-facade files in NAMESPACE_PLATFORM_FACADE_SINGLETONS
        (api.py, base.py, config.py, settings.py). Anything else remains a
        banned module alias.
        """
        spec = c.Infra.NAMESPACE_FAMILY_EXPECTED_ALIAS.get(filepath.name)
        if spec is None:
            spec = c.Infra.NAMESPACE_PLATFORM_FACADE_SINGLETONS.get(filepath.name)
        if spec is None or filepath.parent != Path(c.Infra.DEFAULT_SRC_DIR).joinpath(
            *package_name.split(".")
        ):
            return False
        alias, suffix = spec
        classes = cls.outer_classes(tree)
        # Secondary support classes at module level are allowed (see the loop
        # in check_structure); only the facade class itself must exist with the
        # canonical stem+suffix name.
        facade_class_name = f"{class_stem}{suffix}"
        facade_classes = [
            node
            for node in classes
            if getattr(node, "name", "") == facade_class_name
        ]
        if not facade_classes:
            return False
        facade = facade_classes[0]
        targets = getattr(node, "targets", ()) or (getattr(node, "target", None),)
        value = getattr(node, "value", None)
        value_is_class = (
            cls.kind(value) == "Name" and cls.name_of(value) == facade_class_name
        )
        value_is_global_singleton = (
            cls.kind(value) == "Call"
            and cls.dotted_name(getattr(value, "func", None))
            == f"{facade_class_name}.fetch_global"
        )
        if not (
            cls.kind(node) in {"Assign", "AnnAssign"}
            and len(targets) == 1
            and cls.kind(targets[0]) == "Name"
            and cls.name_of(targets[0]) == alias
            and (value_is_class or value_is_global_singleton)
            and cls.line(node) > cls.line(facade)
        ):
            return False
        return all(
            cls._dunder_assignment(statement) or cls._module_docstring(statement)
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
