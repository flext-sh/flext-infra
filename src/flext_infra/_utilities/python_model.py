"""Static Python model utilities for ``u.Infra`` over the run's one parse.

The run's source project parses each source exactly once and keeps that
syntax tree in memory, invalidating it only when the resource changes. Every
fact (``__all__``, members, imports, class bases, assigned values) is derived
from that tree once per parse, with the static semantics the facade and
lazy-init planners rely on. Nothing is imported or executed.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, MutableMapping
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery


class FlextInfraUtilitiesPythonModel:
    """Parse-once static model queries over one run's source view."""

    @staticmethod
    def python_model_run(
        source_project: p.Infra.RopeProject,
        module_files: t.MappingKV[str, Path],
        *,
        module_facts: MutableMapping[
            t.Infra.RopeNativeParsedModule, m.Infra.PythonModuleFacts
        ]
        | None = None,
    ) -> m.Infra.PythonModelRun:
        """Open one static model run with empty fact caches.

        Returns:
            The run every query of this model reads and caches through.

        """
        return m.Infra.PythonModelRun(
            source_project=source_project,
            module_files=module_files,
            modules=module_facts if module_facts is not None else {},
            ancestors={},
            project_notices={},
        )

    @classmethod
    def python_model_module_at(
        cls, run: m.Infra.PythonModelRun, path: Path, name: str
    ) -> m.Infra.PythonModuleFacts:
        """Return the facts of ``path`` under its dotted module name.

        The source project owns the one parse; its invalidation replaces the
        parsed module, so the facts cache never serves a stale tree.

        Returns:
            The module facts.

        Raises:
            TypeError: If the parsed module carries no module syntax tree.

        """
        project = run.source_project
        parsed = project.get_pymodule(
            FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path)
        )
        facts = run.modules.get(parsed)
        if facts is None:
            tree = parsed.get_ast()
            if not isinstance(tree, ast.Module):
                msg = f"parsed source carries no module syntax tree: {path}"
                raise TypeError(msg)
            facts = cls._python_model_facts(path, name, tree)
            run.modules[parsed] = facts
        return facts

    @classmethod
    def _python_model_facts(
        cls, path: Path, name: str, tree: ast.Module
    ) -> m.Infra.PythonModuleFacts:
        """Derive one module's top-level facts from its syntax tree.

        Returns:
            The members, imports, exports, classes and assigned values.

        """
        draft = m.Infra.PythonModuleFactsDraft(
            path=path,
            name=name,
            is_init=path.name == c.Infra.INIT_PY,
            members={},
            imports={},
            classes={},
            class_exports={},
            values={},
        )
        for node, parent in cls._python_model_statements(tree):
            match node:
                case ast.Import():
                    cls._python_model_on_import(draft, node)
                case ast.ImportFrom():
                    cls._python_model_on_import_from(draft, node)
                case ast.ClassDef():
                    cls._python_model_bind(draft, node.name, "class")
                    draft.classes[node.name] = tuple(map(ast.unparse, node.bases))
                    draft.class_exports[node.name] = cls._python_model_class_exports(
                        node
                    )
                case ast.FunctionDef() | ast.AsyncFunctionDef():
                    cls._python_model_bind(draft, node.name, "function")
                case ast.Assign() | ast.AnnAssign():
                    cls._python_model_on_assign(draft, node, parent)
                case ast.AugAssign():
                    cls._python_model_on_augment(draft, node)
                case _:
                    pass
        return m.Infra.PythonModuleFacts(
            path=path,
            declaration_only=all(
                (
                    isinstance(node, ast.ImportFrom)
                    and node.level == 0
                    and node.module == "__future__"
                )
                or (
                    isinstance(node, ast.Expr)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                )
                for node in tree.body
            ),
            members=draft.members,
            imports=draft.imports,
            exports=cls._python_model_literal(draft.exports),
            classes=draft.classes,
            class_exports=draft.class_exports,
            values=draft.values,
        )

    @staticmethod
    def _python_model_bind(
        draft: m.Infra.PythonModuleFactsDraft,
        member: str,
        kind: t.Infra.PythonMemberKind,
    ) -> None:
        """Bind one top-level name, dropping facts of its previous binding."""
        draft.members[member] = kind
        draft.classes.pop(member, None)
        draft.class_exports.pop(member, None)
        draft.values.pop(member, None)

    @classmethod
    def _python_model_on_import(
        cls, draft: m.Infra.PythonModuleFactsDraft, node: ast.Import
    ) -> None:
        """Bind each ``import`` name to its top package or its full alias path."""
        for alias in node.names:
            target = alias.name if alias.asname else alias.name.split(".")[0]
            local = alias.asname or target.split(".")[0]
            draft.imports[local] = target
            cls._python_model_bind(draft, local, "alias")

    @classmethod
    def _python_model_on_import_from(
        cls, draft: m.Infra.PythonModuleFactsDraft, node: ast.ImportFrom
    ) -> None:
        """Bind each ``from`` import, skipping a package's own submodule import.

        ``from . import b`` inside ``a/__init__.py`` names ``a.b`` itself, and
        an import of a name onto itself creates no binding.
        """
        for alias in node.names:
            if (
                node.level == 1
                and not node.module
                and not alias.asname
                and draft.is_init
            ):
                continue
            target = cls._python_model_absolute(
                node, alias, draft.name, is_init=draft.is_init
            )
            if alias.name == "*":
                local = target.replace(".", "/")
                target = target.replace(".*", "")
            else:
                local = alias.asname or alias.name
                draft.imports[local] = target
            if target != f"{draft.name}.{local}":
                cls._python_model_bind(draft, local, "alias")

    @classmethod
    def _python_model_on_assign(
        cls,
        draft: m.Infra.PythonModuleFactsDraft,
        node: ast.Assign | ast.AnnAssign,
        parent: ast.AST,
    ) -> None:
        """Bind each assigned name; a conditional rebinding keeps the first."""
        for name in cls._python_model_assigned(node):
            if name in draft.members and isinstance(
                parent, (ast.If, ast.ExceptHandler)
            ):
                continue
            cls._python_model_bind(draft, name, "attribute")
            if node.value is not None:
                draft.values[name] = ast.unparse(node.value)
            if name == "__all__":
                draft.exports = cls._python_model_all(node.value)

    @classmethod
    def _python_model_on_augment(
        cls, draft: m.Infra.PythonModuleFactsDraft, node: ast.AugAssign
    ) -> None:
        """Extend a declared ``__all__`` by an ``__all__ += ...`` statement."""
        if (
            draft.exports is not None
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
            and isinstance(node.op, ast.Add)
        ):
            draft.exports.extend(cls._python_model_all(node.value))

    @classmethod
    def _python_model_statements(
        cls, node: ast.AST
    ) -> Iterator[tuple[ast.stmt, ast.AST]]:
        """Yield every statement of one scope with its direct parent node.

        Compound statements and exception handlers are entered; function and
        class bodies are separate scopes and are not.

        Yields:
            ``(statement, parent)`` pairs in source order.

        """
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                yield child, node
                if not isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    yield from cls._python_model_statements(child)
            elif isinstance(child, (ast.excepthandler, ast.match_case)):
                yield from cls._python_model_statements(child)

    @staticmethod
    def _python_model_assigned(node: ast.Assign | ast.AnnAssign) -> t.StrSequence:
        """Return the plain names one assignment binds.

        An unpacking or subscript target binds no static name, so the whole
        assignment binds none; attribute targets bind no module name.

        Returns:
            The bound names in target order.

        """
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not all(isinstance(target, (ast.Name, ast.Attribute)) for target in targets):
            return ()
        return tuple(target.id for target in targets if isinstance(target, ast.Name))

    @classmethod
    def _python_model_class_exports(cls, node: ast.ClassDef) -> t.StrSequence | None:
        """Return the class-level ``__all__`` a class body declares.

        Returns:
            The literal names, empty when not all literal, ``None`` when absent.

        """
        bound: set[str] = set()
        exports: list[str | None] | None = None
        for statement, parent in cls._python_model_statements(node):
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                for target_name in cls._python_model_assigned(statement):
                    if target_name in bound and isinstance(
                        parent, (ast.If, ast.ExceptHandler)
                    ):
                        continue
                    bound.add(target_name)
                    if target_name == "__all__":
                        exports = cls._python_model_all(statement.value)
            elif isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                bound.add(statement.name)
        return cls._python_model_literal(exports)

    @classmethod
    def _python_model_all(cls, value: ast.expr | None) -> list[str | None]:
        """Return the entries one ``__all__`` value declares.

        String literals are names; any other resolvable entry is ``None``; an
        unsupported expression declares nothing.

        Returns:
            The declared entries in order.

        """
        entries = cls._python_model_entries(value) if value is not None else []
        return entries if entries is not None else []

    @classmethod
    def _python_model_entries(cls, value: ast.expr) -> list[str | None] | None:
        """Flatten one ``__all__`` expression into its entries.

        Returns:
            The entries, or ``None`` for an unsupported expression.

        """
        if isinstance(value, ast.Constant):
            return [value.value if isinstance(value.value, str) else None]
        if isinstance(value, (ast.Name, ast.Attribute)):
            return [None]
        if isinstance(value, ast.Starred):
            return cls._python_model_entries(value.value)
        parts: t.SequenceOf[ast.expr]
        if isinstance(value, ast.BinOp):
            parts = (value.left, value.right)
        elif isinstance(value, (ast.List, ast.Set, ast.Tuple)):
            parts = value.elts
        else:
            return None
        entries: list[str | None] = []
        for part in parts:
            found = cls._python_model_entries(part)
            if found is None:
                return None
            entries.extend(found)
        return entries

    @staticmethod
    def _python_model_literal(
        entries: t.SequenceOf[str | None] | None,
    ) -> t.StrSequence | None:
        """Normalize declared entries: all literal, or empty when any is not.

        Returns:
            The literal names, empty when an entry is not literal, or ``None``.

        """
        if entries is None:
            return None
        names = tuple(entry for entry in entries if entry is not None)
        return names if len(names) == len(entries) else ()

    @staticmethod
    def _python_model_absolute(
        node: ast.ImportFrom, alias: ast.alias, name: str, *, is_init: bool
    ) -> str:
        """Resolve one ``from`` import to its absolute dotted target.

        Returns:
            The absolute dotted path of the imported name.

        """
        parts = name.split(".")
        level = (
            node.level - 1
            if is_init and (node.level > 0 or len(parts) > 1)
            else node.level
        )
        kept = len(parts) - min(max(level, 0), len(parts) - 1)
        base = ".".join(parts[:kept]) + "." if node.level > 0 else ""
        module = f"{node.module}." if node.module else ""
        return f"{base}{module}{alias.name}"

    @classmethod
    def python_model_module(
        cls, run: m.Infra.PythonModelRun, name: str
    ) -> m.Infra.PythonModuleFacts | None:
        """Return the facts of the module a dotted name resolves to.

        Returns:
            The module facts, or ``None`` for a name without a Python source.

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
    def python_model_exports(
        module: m.Infra.PythonModuleFacts,
    ) -> t.StrSequence | None:
        """Return the explicit ``__all__`` names, ``None`` if absent.

        A single root class owning ``__all__`` declares the module's exports
        when the module itself declares none.

        Returns:
            The declared names, empty when an entry is not a string literal.

        """
        classes = tuple(module.classes)
        declared = (
            module.exports
            if module.exports is not None or len(classes) != 1
            else module.class_exports[classes[0]]
        )
        return None if declared is None else tuple(dict.fromkeys(declared))

    @staticmethod
    def python_model_implicit_exports(
        module: m.Infra.PythonModuleFacts,
    ) -> t.StrSequence:
        """Return the classes and assignments a module binds itself.

        Returns:
            The implicit export names in declaration order.

        """
        return tuple(
            name
            for name, kind in module.members.items()
            if kind in {"class", "attribute"}
        )

    @staticmethod
    def python_model_members(module: m.Infra.PythonModuleFacts) -> frozenset[str]:
        """Return every name a module binds, defined or imported.

        Returns:
            The module's bound names.

        """
        return frozenset(module.members)

    @staticmethod
    def python_model_imports(module: m.Infra.PythonModuleFacts) -> t.StrMapping:
        """Return every imported name with its dotted import target.

        Returns:
            The import targets keyed by local name.

        """
        return module.imports

    @staticmethod
    def python_model_import_target(module: m.Infra.PythonModuleFacts, name: str) -> str:
        """Return the dotted target a name is imported from.

        Returns:
            The import target, or ``""`` when the module binds ``name`` itself.

        """
        return (
            module.imports.get(name, "") if module.members.get(name) == "alias" else ""
        )

    @staticmethod
    def python_model_defines(module: m.Infra.PythonModuleFacts, name: str) -> bool:
        """Return whether a module binds ``name`` itself (not through an import).

        Returns:
            Whether the module defines ``name``.

        """
        return module.members.get(name) not in {None, "alias"}

    @staticmethod
    def python_model_class_bases(
        module: m.Infra.PythonModuleFacts,
    ) -> t.MappingKV[str, t.StrSequence]:
        """Return each top-level class with its base expressions as written.

        Returns:
            The base expressions keyed by class name.

        """
        return module.classes

    @staticmethod
    def python_model_value_root(module: m.Infra.PythonModuleFacts, name: str) -> str:
        """Return the root name of an attribute bound to a name or attribute chain.

        Returns:
            The root name, or ``""`` for any other binding.

        """
        parts = module.values.get(name, "").split(".")
        return parts[0] if all(part.isidentifier() for part in parts) else ""

    @staticmethod
    def python_model_class_alias(module: m.Infra.PythonModuleFacts, name: str) -> str:
        """Return the local class a module-level name is bound to (``c = Cls``).

        Returns:
            The class name, or ``""`` when ``name`` is not a bare class binding.

        """
        target = module.values.get(name, "")
        return target if target in module.classes else ""

    @classmethod
    def python_model_letters(cls, module: m.Infra.PythonModuleFacts) -> frozenset[str]:
        """Return exported lower-case names bound to a class or imported name.

        Returns:
            The facade letters the module declares.

        """
        owners = frozenset(module.imports) | frozenset(module.classes)
        return frozenset(
            name
            for name in cls.python_model_exports(module) or ()
            if name.islower()
            and not name.startswith("_")
            and cls.python_model_value_root(module, name) in owners
        )

    @classmethod
    def python_model_facade_owner(
        cls, module: m.Infra.PythonModuleFacts
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
            msg = f"ambiguous facade declaration in {module.path}: {sorted(owners)}"
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
        for base in module.classes.get(name, ()):
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
