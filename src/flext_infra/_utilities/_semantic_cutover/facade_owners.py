"""Derive a facade letter's class from the ``__all__`` that declares it.

The owner of a facade letter is the module that declares it in its own
``__all__`` next to the class it names (``__all__ = ["FlextCliModels", "m"]``).
Resolution follows the last module-scope binding of each name through imports
and plain or annotated aliases, reading editable and installed sources without
importing them. No class name is ever inferred from a package name.
"""

from __future__ import annotations

import ast
from importlib.util import resolve_name
from typing import TYPE_CHECKING

from ..private_import_facades import FlextInfraUtilitiesPrivateImportFacades
from ..rope_analysis import FlextInfraUtilitiesRopeAnalysis

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra import t


class FlextInfraUtilitiesSemanticCutoverFacadeOwners:
    """Resolve facade letters to the class their declaring module names."""

    @classmethod
    def facade_classes(cls, package: str) -> t.StrMapping:
        """Map every letter ``package`` publishes to its declared facade class."""
        modules = FlextInfraUtilitiesPrivateImportFacades.source_modules(
            {}, (f"from {package} import *",)
        )
        indexed = modules.get(package)
        if indexed is None:
            msg = f"facade package is not importable for derivation: {package}"
            raise ValueError(msg)
        classes: dict[str, str] = {}
        for name in FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
            indexed[0]
        ):
            owner = cls._facade_letter_class(modules, package, name)
            if owner is not None:
                classes[name] = owner
        return classes

    @classmethod
    def _facade_declared_owner(
        cls, modules: t.MappingKV[str, t.Pair[str, bool]], module: str, letter: str
    ) -> str:
        """Return the class ``letter`` names, or raise with the missing proof."""
        owner = cls._facade_letter_class(modules, module, letter)
        if owner is None:
            msg = (
                f"{module}.{letter} is not declared with its facade class in the "
                "__all__ of the module that binds it"
            )
            raise ValueError(msg)
        return owner

    @classmethod
    def _facade_letter_class(
        cls, modules: t.MappingKV[str, t.Pair[str, bool]], module: str, letter: str
    ) -> str | None:
        """Return the declared class of a letter that ``module`` publishes."""
        resolved = cls._facade_declared_class(modules, module, letter, frozenset())
        if resolved is None:
            return None
        owner_module, owner = resolved
        if owner == letter:
            return None
        exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
            modules[owner_module][0]
        )
        if letter not in exports or owner not in exports:
            return None
        if cls._facade_declared_class(modules, module, owner, frozenset()) != resolved:
            msg = f"{module} does not publish {owner_module}.{owner} as {owner}"
            raise ValueError(msg)
        return owner

    @classmethod
    def _facade_declared_class(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        module: str,
        name: str,
        visiting: frozenset[str],
    ) -> t.Pair[str, str] | None:
        """Follow the last module-scope binding of ``name`` to its class."""
        identity = f"{module}.{name}"
        if identity in visiting:
            msg = f"cyclic facade binding: {identity}"
            raise ValueError(msg)
        indexed = modules.get(module)
        if indexed is None:
            return None
        source, is_package = indexed
        package = module if is_package else module.rpartition(".")[0]
        target: t.Pair[str, str] | None = None
        declared = False
        for node in cls._facade_ordered_statements(
            ast.parse(source, filename=module).body
        ):
            if isinstance(node, ast.ClassDef) and node.name == name:
                target, declared = None, True
            elif isinstance(node, ast.Assign | ast.AnnAssign) and any(
                isinstance(bound, ast.Name) and bound.id == name
                for bound in (
                    node.targets if isinstance(node, ast.Assign) else (node.target,)
                )
            ):
                target = (
                    (module, node.value.id)
                    if isinstance(node.value, ast.Name)
                    else None
                )
                declared = False
            elif isinstance(node, ast.ImportFrom):
                for imported in node.names:
                    if (imported.asname or imported.name) == name:
                        source_module = (
                            resolve_name(
                                "." * node.level + (node.module or ""), package
                            )
                            if node.level
                            else node.module or ""
                        )
                        target, declared = (source_module, imported.name), False
        if declared:
            return module, name
        # A submodule import binds a module, never a facade class.
        if target is None or ".".join(target) in modules:
            return None
        return cls._facade_declared_class(modules, *target, visiting | {identity})

    @classmethod
    def _facade_ordered_statements(
        cls, body: t.SequenceOf[ast.stmt]
    ) -> Iterator[ast.stmt]:
        """Yield module-scope bindings in execution order, entering conditionals."""
        for node in body:
            if isinstance(node, ast.If):
                yield from cls._facade_ordered_statements(node.body)
                yield from cls._facade_ordered_statements(node.orelse)
            else:
                yield node


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverFacadeOwners"]
