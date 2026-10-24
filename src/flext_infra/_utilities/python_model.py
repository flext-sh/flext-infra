"""Static Python model utilities for ``u.Infra`` (the sole Griffe owner).

Griffe parses each source once, read through the run's source view; every
fact (``__all__``, members, imports, class bases, alias targets) is derived
from that single parse. Nothing is imported or executed.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

import griffe

from flext_infra import c, m, p, t
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery


class FlextInfraUtilitiesPythonModel:
    """Parse-once static model queries over one run's source view."""

    @staticmethod
    def python_model_run(
        source_project: p.Infra.RopeProject,
        module_files: t.MappingKV[str, Path],
    ) -> m.Infra.PythonModelRun:
        """Open one static model run with empty parse caches.

        Returns:
            The run every query of this model reads and caches through.

        """
        return m.Infra.PythonModelRun(
            source_project=source_project,
            module_files=module_files,
            modules={},
            sources={},
            ancestors={},
        )

    @staticmethod
    def python_model_module_at(
        run: m.Infra.PythonModelRun, path: Path, name: str
    ) -> t.Infra.PythonModule:
        """Return the one parse of ``path`` under its dotted module name.

        Relative imports resolve against the enclosing packages, so the module
        is visited inside its package chain.

        Returns:
            The parsed module.

        """
        module = run.modules.get(path)
        if module is None:
            source = run.source_project.source_text(path)
            *packages, leaf = name.split(".")
            folder = path.parent if path.name != c.Infra.INIT_PY else path.parent.parent
            folders = [folder, *folder.parents][: len(packages)][::-1]
            parent: t.Infra.PythonModule | None = None
            for package, package_dir in zip(packages, folders, strict=True):
                parent = griffe.Module(
                    package, filepath=package_dir / c.Infra.INIT_PY, parent=parent
                )
            module = griffe.visit(leaf, path, source, parent=parent)
            run.modules[path] = module
            run.sources[module.path] = source
        return module

    @classmethod
    def python_model_module(
        cls, run: m.Infra.PythonModelRun, name: str
    ) -> t.Infra.PythonModule | None:
        """Return the parsed module a dotted name resolves to, when it has a source.

        Returns:
            The parsed module, or ``None`` for a name without a Python source.

        """
        path = cls.python_model_locate(run, name)
        return None if path is None else cls.python_model_module_at(run, path, name)

    @classmethod
    def python_model_locate(cls, run: m.Infra.PythonModelRun, name: str) -> Path | None:
        """Resolve a dotted module name: indexed sources, then installed packages.

        Returns:
            The module's source file, or ``None`` when no source declares it.

        """
        indexed = run.module_files.get(name)
        if indexed is not None:
            return indexed
        head, *rest = name.split(".")
        folder = cls.python_model_package_dir(head)
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
                if run.source_project.source_query(candidate, "isfile")
            ),
            None,
        )

    @staticmethod
    def python_model_package_dir(name: str) -> Path | None:
        """Return the installed package directory of a dotted package name.

        Returns:
            The package directory, or ``None`` for a plain module or unknown name.

        """
        return (
            FlextInfraUtilitiesDiscovery.declared_package_dir(name)
            if all(part.isidentifier() for part in name.split("."))
            else None
        )

    @staticmethod
    def python_model_exports(module: t.Infra.PythonModule) -> t.StrSequence | None:
        """Return the explicit ``__all__`` strings Griffe computed, ``None`` if absent.

        A single root class owning ``__all__`` declares the module's exports
        when the module itself declares none (Griffe ``Object.exports``).

        Returns:
            The declared names, empty when an entry is not a string literal.

        """
        classes = [owner for owner in module.classes.values() if not owner.is_alias]
        declared = (
            module.exports
            if module.exports is not None or len(classes) != 1
            else classes[0].exports
        )
        if declared is None:
            return None
        names = tuple(name for name in declared if isinstance(name, str))
        return tuple(dict.fromkeys(names)) if len(names) == len(declared) else ()

    @staticmethod
    def python_model_implicit_exports(module: t.Infra.PythonModule) -> t.StrSequence:
        """Return the classes and assignments a module binds itself.

        Returns:
            The implicit export names in declaration order.

        """
        return tuple(
            name
            for name, member in module.members.items()
            if not member.is_alias and (member.is_class or member.is_attribute)
        )

    @staticmethod
    def python_model_members(module: t.Infra.PythonModule) -> frozenset[str]:
        """Return every name a module binds, defined or imported.

        Returns:
            The module's bound names.

        """
        return frozenset(module.members)

    @staticmethod
    def python_model_imports(module: t.Infra.PythonModule) -> t.StrMapping:
        """Return every imported name with its dotted import target.

        Returns:
            The import targets keyed by local name.

        """
        return module.imports

    @staticmethod
    def python_model_import_target(module: t.Infra.PythonModule, name: str) -> str:
        """Return the dotted target a name is imported from.

        Returns:
            The import target, or ``""`` when the module binds ``name`` itself.

        """
        member = module.members.get(name)
        return (
            module.imports.get(name, "")
            if member is not None and member.is_alias
            else ""
        )

    @staticmethod
    def python_model_defines(module: t.Infra.PythonModule, name: str) -> bool:
        """Return whether a module binds ``name`` itself (not through an import).

        Returns:
            Whether the module defines ``name``.

        """
        member = module.members.get(name)
        return member is not None and not member.is_alias

    @staticmethod
    def python_model_class_bases(
        module: t.Infra.PythonModule,
    ) -> t.MappingKV[str, t.StrSequence]:
        """Return each top-level class with its base expressions as written.

        Returns:
            The base expressions keyed by class name.

        """
        return {
            name: tuple(str(base) for base in owner.bases)
            for name, owner in module.classes.items()
            if not owner.is_alias
        }

    @staticmethod
    def python_model_value_root(module: t.Infra.PythonModule, name: str) -> str:
        """Return the root name of an attribute bound to a name or attribute chain.

        Returns:
            The root name, or ``""`` for any other binding.

        """
        attribute = module.attributes.get(name)
        value = (
            str(attribute.value)
            if attribute is not None
            and not attribute.is_alias
            and attribute.value is not None
            else ""
        )
        parts = value.split(".")
        return parts[0] if all(part.isidentifier() for part in parts) else ""

    @staticmethod
    def python_model_class_alias(module: t.Infra.PythonModule, name: str) -> str:
        """Return the local class a module-level name is bound to (``c = Cls``).

        Returns:
            The class name, or ``""`` when ``name`` is not a bare class binding.

        """
        attribute = module.attributes.get(name)
        target = (
            str(attribute.value)
            if attribute is not None
            and not attribute.is_alias
            and attribute.value is not None
            else ""
        )
        owner = module.classes.get(target)
        return target if owner is not None and not owner.is_alias else ""

    @classmethod
    def python_model_static_class_alias(
        cls, run: m.Infra.PythonModelRun, module: t.Infra.PythonModule, name: str
    ) -> str:
        """Return the class a name statically re-binds, proven on the module tree.

        The alias is one plain module-level ``name = Cls`` after the single
        ``class Cls`` declaration, and neither name is stored anywhere else.

        Returns:
            The class name, or ``""`` when the binding is not a static alias.

        """
        original = cls.python_model_class_alias(module, name)
        if not original:
            return ""
        tree = ast.parse(run.sources[module.path])
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
    def python_model_letters(cls, module: t.Infra.PythonModule) -> frozenset[str]:
        """Return exported lower-case names bound to a class or imported name.

        Returns:
            The facade letters the module declares.

        """
        owners = frozenset(module.imports) | frozenset(
            cls.python_model_class_bases(module)
        )
        return frozenset(
            name
            for name in cls.python_model_exports(module) or ()
            if name.islower()
            and not name.startswith("_")
            and cls.python_model_value_root(module, name) in owners
        )

    @classmethod
    def python_model_facade_owner(
        cls, module: t.Infra.PythonModule
    ) -> t.StrPair | None:
        """Return the published ``(alias, class)`` facade pair of one module.

        Returns:
            The sole exported alias bound to an exported local class, or ``None``.

        Raises:
            ValueError: If the module publishes more than one facade pair.

        """
        exports = cls.python_model_exports(module) or ()
        owners = {
            (name, target)
            for name in exports
            if name.islower()
            and not name.startswith("_")
            and (target := cls.python_model_class_alias(module, name))
            and target in exports
        }
        if len(owners) > 1:
            msg = f"ambiguous facade declaration in {module.filepath}: {sorted(owners)}"
            raise ValueError(msg)
        return next(iter(owners), None)

    @classmethod
    def python_model_resolve(cls, run: m.Infra.PythonModelRun, dotted: str) -> str:
        """Follow import bindings from a dotted name to its defining module.

        Returns:
            The canonical ``module.name`` path, or ``dotted`` when unresolvable.

        """
        seen: set[str] = set()
        while dotted not in seen:
            seen.add(dotted)
            module_name, _, name = dotted.rpartition(".")
            module = cls.python_model_module(run, module_name) if module_name else None
            target = (
                "" if module is None else cls.python_model_import_target(module, name)
            )
            if not target:
                return dotted
            dotted = target
        return dotted

    @classmethod
    def python_model_ancestors(
        cls, run: m.Infra.PythonModelRun, dotted: str
    ) -> frozenset[str]:
        """Return the canonical paths of every class a class inherits from.

        Local bases resolve to their module; bases bound to no import or local
        class stay unresolved and are omitted.

        Returns:
            The transitive base class paths of ``dotted``.

        """
        cached = run.ancestors.get(dotted)
        if cached is not None:
            return cached
        run.ancestors[dotted] = frozenset()
        module_name, _, name = dotted.rpartition(".")
        module = cls.python_model_module(run, module_name) if module_name else None
        if module is None:
            return frozenset()
        found: set[str] = set()
        for base in cls.python_model_class_bases(module).get(name, ()):
            head, _, tail = base.partition(".")
            target = module.imports.get(head) or (
                f"{module_name}.{head}" if head in module.members else ""
            )
            if target:
                resolved = cls.python_model_resolve(
                    run, f"{target}.{tail}" if tail else target
                )
                found.update((resolved, *cls.python_model_ancestors(run, resolved)))
        run.ancestors[dotted] = frozenset(found)
        return run.ancestors[dotted]


__all__: list[str] = ["FlextInfraUtilitiesPythonModel"]
