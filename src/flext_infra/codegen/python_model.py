"""Static Python model shared by one generation run.

Griffe parses each source once, read through the run's source view; every
fact (``__all__``, members, imports, class bases, alias targets) is derived
from that single parse. Nothing is imported or executed.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Annotated

import griffe

from flext_infra import c, m, p, t, u


class FlextInfraCodegenPythonModel(m.ArbitraryTypesModel):
    """Parse-once static model over the run's source view."""

    source_project: Annotated[
        p.Infra.RopeProject,
        m.Field(description="Source view every module is read through"),
    ]
    module_files: Annotated[
        t.MappingKV[str, Path],
        m.Field(description="Indexed module names elected before installed ones"),
    ]
    _modules: t.MutableMappingKV[Path, griffe.Module] = m.PrivateAttr(
        default_factory=dict[Path, griffe.Module],
    )
    _sources: t.MutableMappingKV[str, str] = m.PrivateAttr(
        default_factory=dict[str, str],
    )
    _ancestors: t.MutableMappingKV[str, frozenset[str]] = m.PrivateAttr(
        default_factory=dict[str, frozenset[str]],
    )

    def module_at(self, path: Path, name: str) -> griffe.Module:
        """Return the one parse of ``path`` under its dotted module name.

        Returns:
            The parsed module.

        """
        module = self._modules.get(path)
        if module is None:
            source = self.source_project.source_text(path)
            *packages, leaf = name.split(".")
            # Relative imports resolve against the enclosing packages, so the
            # module is visited inside its package chain.
            folder = path.parent if path.name != c.Infra.INIT_PY else path.parent.parent
            folders = [folder, *folder.parents][: len(packages)][::-1]
            parent: griffe.Module | None = None
            for package, package_dir in zip(packages, folders, strict=True):
                parent = griffe.Module(
                    package, filepath=package_dir / c.Infra.INIT_PY, parent=parent
                )
            module = griffe.visit(leaf, path, source, parent=parent)
            self._modules[path] = module
            self._sources[module.path] = source
        return module

    def module(self, name: str) -> griffe.Module | None:
        """Return the parsed module a dotted name resolves to, when it has a source.

        Returns:
            The parsed module, or ``None`` for a name without a Python source.

        """
        path = self.locate(name)
        return None if path is None else self.module_at(path, name)

    def locate(self, name: str) -> Path | None:
        """Resolve a dotted module name: indexed sources, then installed packages.

        Returns:
            The module's source file, or ``None`` when no source declares it.

        """
        indexed = self.module_files.get(name)
        if indexed is not None:
            return indexed
        head, *rest = name.split(".")
        folder = self.package_dir(head)
        if folder is None:
            return None
        folder = folder.joinpath(*rest)
        return next(
            (
                candidate
                for candidate in (
                    folder / c.Infra.INIT_PY,
                    folder.with_suffix(c.Infra.EXT_PYTHON),
                )
                if self.source_project.source_query(candidate, "isfile")
            ),
            None,
        )

    @staticmethod
    def package_dir(name: str) -> Path | None:
        """Return the installed package directory of a dotted package name.

        Returns:
            The package directory, or ``None`` for a plain module or unknown name.

        """
        return (
            u.Infra.declared_package_dir(name)
            if all(part.isidentifier() for part in name.split("."))
            else None
        )

    @staticmethod
    def exports(module: griffe.Module) -> t.StrSequence | None:
        """Return the explicit ``__all__`` strings, ``None`` when undeclared.

        Returns:
            The declared names, empty when the declaration is not literal.

        """
        declared = module.exports
        if declared is not None:
            names = tuple(name for name in declared if isinstance(name, str))
            return tuple(dict.fromkeys(names)) if len(names) == len(declared) else ()
        # Without a module declaration, a single root class may own ``__all__``.
        roots = [
            member
            for member in module.members.values()
            if isinstance(member, griffe.Class)
        ]
        owner = roots[0].members.get("__all__") if len(roots) == 1 else None
        if not isinstance(owner, griffe.Attribute):
            return None
        value = owner.value
        if not isinstance(value, griffe.ExprTuple | griffe.ExprList | griffe.ExprSet):
            return ()
        literals = tuple(
            ast.literal_eval(element) if isinstance(element, str) else None
            for element in value.elements
        )
        strings = tuple(name for name in literals if isinstance(name, str))
        return tuple(dict.fromkeys(strings)) if len(strings) == len(literals) else ()

    @staticmethod
    def implicit_exports(module: griffe.Module) -> t.StrSequence:
        """Return the classes and assignments a module binds itself.

        Returns:
            The implicit export names in declaration order.

        """
        return tuple(
            name
            for name, member in module.members.items()
            if isinstance(member, griffe.Class | griffe.Attribute)
        )

    @staticmethod
    def import_target(module: griffe.Module, name: str) -> str:
        """Return the dotted target a name is imported from.

        Returns:
            The import target, or ``""`` when the module binds ``name`` itself.

        """
        member = module.members.get(name)
        return member.target_path if isinstance(member, griffe.Alias) else ""

    @staticmethod
    def defines(module: griffe.Module, name: str) -> bool:
        """Return whether a module binds ``name`` itself (not through an import).

        Returns:
            Whether the module defines ``name``.

        """
        member = module.members.get(name)
        return member is not None and not isinstance(member, griffe.Alias)

    @staticmethod
    def class_bases(module: griffe.Module) -> t.MappingKV[str, t.StrSequence]:
        """Return each top-level class with its base expressions as written.

        Returns:
            The base expressions keyed by class name.

        """
        return {
            name: tuple(str(base) for base in member.bases)
            for name, member in module.members.items()
            if isinstance(member, griffe.Class)
        }

    @staticmethod
    def value_root(module: griffe.Module, name: str) -> str:
        """Return the root name of an attribute bound to a name or attribute chain.

        Returns:
            The root name, or ``""`` for any other binding.

        """
        member = module.members.get(name)
        if not isinstance(member, griffe.Attribute):
            return ""
        value = member.value
        if isinstance(value, griffe.ExprAttribute):
            value = value.values[0]
        return value.name if isinstance(value, griffe.ExprName) else ""

    @staticmethod
    def class_alias(module: griffe.Module, name: str) -> str:
        """Return the local class a module-level name is bound to (``c = Cls``).

        Returns:
            The class name, or ``""`` when ``name`` is not a bare class binding.

        """
        member = module.members.get(name)
        if not isinstance(member, griffe.Attribute) or not isinstance(
            member.value, griffe.ExprName
        ):
            return ""
        target = member.value.name
        return target if isinstance(module.members.get(target), griffe.Class) else ""

    def static_class_alias(self, module: griffe.Module, name: str) -> str:
        """Return the class a name statically re-binds, proven on the module tree.

        The alias is one plain module-level ``name = Cls`` after the single
        ``class Cls`` declaration, and neither name is stored anywhere else.

        Returns:
            The class name, or ``""`` when the binding is not a static alias.

        """
        original = self.class_alias(module, name)
        if not original:
            return ""
        tree = ast.parse(self._sources[module.path])
        aliases = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
            and isinstance(node.value, ast.Name)
            and node.value.id == original
        ]
        stores = [
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        ]
        declarations = [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == original
        ]
        proven = (
            len(aliases) == 1
            and stores.count(name) == 1
            and original not in stores
            and len(declarations) == 1
            and declarations[0].lineno < aliases[0].lineno
        )
        return original if proven else ""

    @classmethod
    def letters(cls, module: griffe.Module) -> frozenset[str]:
        """Return exported lower-case names bound to a class or imported name.

        Returns:
            The facade letters the module declares.

        """
        owners = frozenset(module.imports) | frozenset(cls.class_bases(module))
        return frozenset(
            name
            for name in cls.exports(module) or ()
            if name.islower()
            and not name.startswith("_")
            and cls.value_root(module, name) in owners
        )

    @classmethod
    def facade_owner(cls, module: griffe.Module) -> t.StrPair | None:
        """Return the published ``(alias, class)`` facade pair of one module.

        Returns:
            The sole exported alias bound to an exported local class, or ``None``.

        Raises:
            ValueError: If the module publishes more than one facade pair.

        """
        exports = cls.exports(module) or ()
        owners = {
            (name, target)
            for name in exports
            if name.islower()
            and not name.startswith("_")
            and (target := cls.class_alias(module, name))
            and target in exports
        }
        if len(owners) > 1:
            msg = f"ambiguous facade declaration in {module.filepath}: {sorted(owners)}"
            raise ValueError(msg)
        return next(iter(owners), None)

    def resolve(self, dotted: str) -> str:
        """Follow import bindings from a dotted name to its defining module.

        Returns:
            The canonical ``module.name`` path, or ``dotted`` when unresolvable.

        """
        seen: set[str] = set()
        while dotted not in seen:
            seen.add(dotted)
            module_name, _, name = dotted.rpartition(".")
            module = self.module(module_name) if module_name else None
            target = "" if module is None else self.import_target(module, name)
            if not target:
                return dotted
            dotted = target
        return dotted

    def ancestors(self, dotted: str) -> frozenset[str]:
        """Return the canonical paths of every class a class inherits from.

        Local bases resolve to their module; bases bound to no import or local
        class stay unresolved and are omitted.

        Returns:
            The transitive base class paths of ``dotted``.

        """
        cached = self._ancestors.get(dotted)
        if cached is not None:
            return cached
        self._ancestors[dotted] = frozenset()
        module_name, _, name = dotted.rpartition(".")
        module = self.module(module_name) if module_name else None
        if module is None:
            return frozenset()
        found: set[str] = set()
        for base in self.class_bases(module).get(name, ()):
            head, _, tail = base.partition(".")
            target = module.imports.get(head) or (
                f"{module_name}.{head}" if head in module.members else ""
            )
            if target:
                resolved = self.resolve(f"{target}.{tail}" if tail else target)
                found.update((resolved, *self.ancestors(resolved)))
        self._ancestors[dotted] = frozenset(found)
        return self._ancestors[dotted]


__all__: list[str] = ["FlextInfraCodegenPythonModel"]
