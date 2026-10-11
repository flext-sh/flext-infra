"""Semantic facade-base cutover: extend the parent by its declared class name.

A facade module that imports its parent's short letter, subclasses it, and then
rebinds the same letter to the subclass binds that letter twice. Type checkers
then read the letter as a variable, so every ``m.X`` annotation reached through
the facade resolves to Unknown. An annotated rebind (``m: type[X] = X``) has the
same effect. This phase extends the class the parent declares for the letter in
its own ``__all__`` and keeps the letter a plain alias of the facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import (
    Assignment,
    MetadataWrapper,
    QualifiedNameProvider,
    QualifiedNameSource,
    ScopeProvider,
)

from flext_infra import c, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverFacadeBaseCst,
    FlextInfraUtilitiesSemanticCutoverFacadeOwners,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverFacadeBases(
    FlextInfraUtilitiesSemanticCutoverFacadeBaseCst,
    FlextInfraUtilitiesSemanticCutoverFacadeOwners,
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Rewire a facade that extends its parent's letter to the declared class."""

    class _BehaviorReferences(cst.CSTTransformer):
        """Rebind only proven imported member identities, preserving shadowing."""

        METADATA_DEPENDENCIES = (QualifiedNameProvider, ScopeProvider)

        def __init__(
            self,
            resolve: Callable[[str], t.Triple[str, str, str] | None],
            context: CodemodContext,
        ) -> None:
            self.owner_for_reference = resolve
            self.context = context

        @override
        def leave_Attribute(
            self,
            original_node: cst.Attribute,
            updated_node: cst.Attribute,
        ) -> cst.BaseExpression:
            names = self.get_metadata(QualifiedNameProvider, original_node, None)
            if names is None:
                return updated_node
            targets = {
                target
                for name in names
                if name.source is QualifiedNameSource.IMPORT
                and (target := self.owner_for_reference(name.name)) is not None
            }
            if not targets:
                return updated_node
            if len(targets) != 1 or any(
                name.source is not QualifiedNameSource.IMPORT for name in names
            ):
                msg = "behavior reference has ambiguous imported identity"
                raise ValueError(msg)
            module, receiver, member = targets.pop()
            module_import = "." in receiver
            bound_name = receiver.split(".")[0]
            imported_identity = module if module_import else f"{module}.{receiver}"
            scope = self.get_metadata(ScopeProvider, original_node, None)
            if scope is None:
                message = "behavior reference has no lexical scope"
                raise ValueError(message)
            for assignment in scope[bound_name]:
                qualified = assignment.get_qualified_names_for(bound_name)
                own_class = (
                    module == self.context.full_module_name
                    and isinstance(assignment, Assignment)
                    and isinstance(assignment.node, cst.ClassDef)
                    and assignment.node.name.value == receiver
                )
                if not own_class and any(
                    name.name != imported_identity for name in qualified
                ):
                    msg = f"relocated behavior receiver is shadowed: {receiver}"
                    raise ValueError(msg)
            if module != self.context.full_module_name:
                AddImportsVisitor.add_needed_import(
                    self.context, module, None if module_import else receiver
                )
            return cst.Attribute(cst.parse_expression(receiver), cst.Name(member))

    @classmethod
    def _behavior_lineage(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        module: str,
        receiver: str,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Follow the imported facade's declared classes and base bindings.

        Returns:
            The declared module and class identities in C3 order.
        """
        resolved = cls._facade_declared_class(modules, module, receiver, frozenset())
        if resolved is None:
            return ()
        cache: MutableMapping[t.Pair[str, str], t.VariadicTuple[t.Pair[str, str]]] = {}

        def linearize(
            identity: t.Pair[str, str],
            visiting: frozenset[t.Pair[str, str]],
        ) -> t.VariadicTuple[t.Pair[str, str]]:
            if identity in visiting:
                msg = f"cyclic facade inheritance identity: {identity}"
                raise ValueError(msg)
            if identity in cache:
                return cache[identity]
            owner_module, owner_name = identity
            declaration = next(
                node
                for node in ast.parse(modules[owner_module][0]).body
                if isinstance(node, ast.ClassDef) and node.name == owner_name
            )
            bases: list[t.Pair[str, str]] = []
            for base in declaration.bases:
                expression = base.value if isinstance(base, ast.Subscript) else base
                if not isinstance(expression, ast.Name):
                    msg = (
                        f"unsupported facade inheritance identity: "
                        f"{owner_module}.{owner_name}"
                    )
                    raise TypeError(msg)
                inherited = cls._facade_declared_class(
                    modules, owner_module, expression.id, frozenset()
                )
                if inherited is not None:
                    bases.append(inherited)
            cache[identity] = (
                identity,
                *FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                    (
                        *(linearize(base, visiting | {identity}) for base in bases),
                        tuple(bases),
                    ),
                    message=f"inconsistent facade inheritance identity: {identity}",
                ),
            )
            return cache[identity]

        return linearize(resolved, frozenset())

    @classmethod
    def _behavior_modules(
        cls,
        sources: t.MappingKV[Path, str],
    ) -> t.MappingKV[str, t.Pair[str, bool]]:
        """Discover referenced providers and their declared ancestry.

        Returns:
            The complete provider source inventory.
        """
        statements = tuple(
            statement
            for source in sources.values()
            for statement in cls._behavior_imports(source)
        )
        modules = FlextInfraUtilitiesPrivateImportFacades.source_modules(
            sources, statements
        )
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        typing_directory = families["t"].directory
        # Provider discovery expands the inventory, never the owners eligible
        # for a reference. Its declared inheritance lineage elects those owners.
        while True:
            inherited_statements = tuple(
                statement
                for module, (source, _package) in modules.items()
                if typing_directory in module.split(".") or module.endswith(".typings")
                for statement in cls._behavior_base_imports(source)
            )
            expanded = FlextInfraUtilitiesPrivateImportFacades.source_modules(
                sources, (*statements, *inherited_statements)
            )
            if expanded.keys() == modules.keys():
                break
            statements = (*statements, *inherited_statements)
            modules = expanded
        return modules

    @staticmethod
    def _behavior_imports(source: str) -> t.StrTuple:
        """Select imports participating in facade or method references.

        Returns:
            The declared import statements.
        """
        tree = ast.parse(source)
        called = {
            call.func.value.id
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
        }
        return tuple(
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and not node.level
            and any(
                alias.name in {"t", "u"} or (alias.asname or alias.name) in called
                for alias in node.names
            )
        )

    @staticmethod
    def _behavior_base_imports(source: str) -> t.StrTuple:
        """Read imported class bases from one provider declaration.

        Returns:
            The imports that supply declared base names.
        """
        tree = ast.parse(source)
        names = {
            base.id
            for declaration in tree.body
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
            if isinstance(base, ast.Name)
        }
        return tuple(
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and any((alias.asname or alias.name) in names for alias in node.names)
        )

    @staticmethod
    def _behavior_requires_facade(
        member: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> bool:
        """Identify methods that read their receiver or need instance dispatch.

        Returns:
            Whether direct lower-owner invocation would change dispatch.
        """
        decorators = {
            decorator.id
            for decorator in member.decorator_list
            if isinstance(decorator, ast.Name)
        }
        parameters = (*member.args.posonlyargs, *member.args.args)
        return "staticmethod" not in decorators and (
            "classmethod" not in decorators
            or not parameters
            or any(
                isinstance(reference, ast.Name) and reference.id == parameters[0].arg
                for statement in member.body
                for reference in ast.walk(statement)
            )
        )

    @classmethod
    def _behavior_owner_inventory(
        cls, modules: t.MappingKV[str, t.Pair[str, bool]]
    ) -> m.Infra.SemanticBehaviorOwners:
        """Elect exported public utility owners once for a relocation pass.

        Returns:
            The immutable owner inventory.
        """
        utility_directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            "u"
        ].directory
        owners: MutableMapping[t.Pair[str, str], list[t.Pair[str, str]]] = {}
        contextual: set[t.Quad[str, str, str, str]] = set()
        for module, (source, _package) in modules.items():
            parts = module.split(".")
            if utility_directory not in parts:
                continue
            tree = ast.parse(source)
            exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(source)
            for declaration in tree.body:
                if (
                    not isinstance(declaration, ast.ClassDef)
                    or declaration.name not in exports
                ):
                    continue
                for member in declaration.body:
                    if not isinstance(
                        member, ast.FunctionDef | ast.AsyncFunctionDef
                    ) or member.name.startswith("_"):
                        continue
                    owners.setdefault((parts[0], member.name), []).append((
                        module,
                        declaration.name,
                    ))
                    if cls._behavior_requires_facade(member):
                        contextual.add((
                            parts[0],
                            module,
                            declaration.name,
                            member.name,
                        ))
        return m.Infra.SemanticBehaviorOwners(
            modules=modules,
            owners={key: tuple(values) for key, values in owners.items()},
            contextual=frozenset(contextual),
        )

    @classmethod
    def _behavior_import_lineage(
        cls,
        imported: t.Pair[str, str],
        inventory: m.Infra.SemanticBehaviorOwners,
        typing_directory: str,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Elect the imported typing facade's declared ancestry.

        Returns:
            Eligible declared identities, preserving retired-module provenance.
        """
        module, receiver = imported
        package = module.split(".")[0]
        declared = cls._facade_declared_class(
            inventory.modules, module, receiver, frozenset()
        )
        facade = cls._facade_declared_class(
            inventory.modules, package, "t", frozenset()
        )
        retired = (
            typing_directory in module.split(".")
            and module not in inventory.modules
            and facade is not None
        )
        return (
            cls._behavior_lineage(
                inventory.modules,
                package if retired else module,
                "t" if retired else receiver,
            )
            if retired or (declared is not None and declared == facade)
            else ()
        )

    @classmethod
    def _plan_behavior_consumers(
        cls,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Rewire behavior consumers through their declared owner inventory.

        Returns:
            The authenticated semantic migration edits.
        """
        inventory = cls._behavior_owner_inventory(cls._behavior_modules(sources))
        typing_directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            "t"
        ].directory

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            tree = ast.parse(source)
            identities = {
                (node.module, alias.name)
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module and not node.level
                for alias in node.names
            }
            if not identities:
                return source, ()
            state = m.Infra.SemanticBehaviorResolution(
                path=path,
                inventory=inventory,
                typing_directory=typing_directory,
                identities=frozenset(identities),
                lineages={},
                obsolete=set(),
            )
            indices = tuple(
                index
                for index, part in enumerate(path.parts)
                if part == c.Infra.DEFAULT_SRC_DIR
            )
            module_name = (
                ".".join((*path.parts[indices[-1] + 1 : -1], path.stem))
                if indices
                else None
            )
            context = CodemodContext(full_module_name=module_name)
            updated = MetadataWrapper(cst.parse_module(source)).visit(
                cls._BehaviorReferences(
                    lambda qualified: cls._resolve_behavior_reference(state, qualified),
                    context,
                )
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.module is None:
                    continue
                for alias in node.names:
                    if (node.module, alias.name) in state.obsolete:
                        RemoveImportsVisitor.remove_unused_import(
                            context, node.module, alias.name, alias.asname
                        )
            updated = updated.visit(AddImportsVisitor(context))
            updated = updated.visit(RemoveImportsVisitor(context))
            return updated.code, (
                "rebound relocated behavior to declared utility owners",
            )

        return cls._semantic_edits(cls._editable_sources(sources), rewrite)

    @classmethod
    def _resolve_behavior_reference(
        cls,
        state: m.Infra.SemanticBehaviorResolution,
        qualified: str,
    ) -> t.Triple[str, str, str] | None:
        """Resolve one qualified call using its consumer-owned operation state.

        Returns:
            The canonical module, receiver, and member, or no relocation.

        Raises:
            ValueError: If the owner is ambiguous or requires facade dispatch.
        """
        imported = next(
            (
                identity
                for identity in state.identities
                if qualified.startswith(".".join(identity) + ".")
                and qualified.removeprefix(".".join(identity) + ".").count(".") == 0
            ),
            None,
        )
        if imported is None:
            return None
        package = imported[0].split(".")[0]
        member = qualified.rpartition(".")[2]
        if imported not in state.lineages:
            state.lineages[imported] = cls._behavior_import_lineage(
                imported, state.inventory, state.typing_directory
            )
        lineage = state.lineages[imported]
        if any(
            isinstance(declaration, ast.ClassDef)
            and declaration.name == class_name
            and any(
                isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
                and method.name == member
                for method in declaration.body
            )
            for owner_module, class_name in lineage
            for declaration in ast.parse(state.inventory.modules[owner_module][0]).body
        ):
            return None
        candidates: t.SequenceOf[t.Pair[str, str]] = ()
        for owner_module, _class in lineage:
            candidates = state.inventory.owners.get(
                (owner_module.split(".")[0], member), ()
            )
            if candidates:
                break
        if not candidates:
            return None
        if len(candidates) != 1:
            message = f"ambiguous relocated behavior owner: {qualified}"
            raise ValueError(message)
        owner_module, owner_class = candidates[0]
        owner_package = owner_module.split(".")[0]
        internal = (
            owner_package in state.path.parts
            and c.Infra.DEFAULT_SRC_DIR in state.path.parts
        )
        if (
            internal
            and (owner_package, owner_module, owner_class, member)
            in state.inventory.contextual
        ):
            message = f"lower behavior owner requires facade dispatch: {qualified}"
            raise ValueError(message)
        state.obsolete.add(imported)
        return (
            owner_module if internal else package,
            owner_class if internal else f"{package}.u",
            member,
        )

    @classmethod
    def _plan_facade_bases(
        cls,
        root: Path,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModScanFinding],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan the class-name base for every facade the detector selected.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        selected = frozenset((root / finding.file).resolve() for finding in findings)
        items = tuple(
            item for item in cls._editable_sources(sources) if item[0] in selected
        )
        shapes = {
            path: found
            for path, source in items
            if (
                found := cls._facade_shapes(path, ast.parse(source, filename=str(path)))
            )
        }
        if not shapes:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        modules = FlextInfraUtilitiesPrivateImportFacades.source_modules(
            sources,
            tuple(
                f"from {shape[0]} import {shape[1]}"
                for found in shapes.values()
                for shape in found
            ),
        )

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            # A facade may compose several parents by their letters (``class
            # X(c, api_c)``); each base is rewired in turn against the source
            # the previous one produced, so every import, base and eager read
            # lands in one edit.
            rewritten = source
            changes: list[str] = []
            for shape in shapes[path]:
                tree = ast.parse(rewritten, filename=str(path))
                owner = cls._facade_declared_owner(modules, shape[0], shape[1])
                bound = cls._facade_bound_imports(tree, shape[0])
                if owner in cls._facade_module_bindings(tree) - bound:
                    msg = f"{owner} is already bound locally in {path}"
                    raise ValueError(msg)
                explicit = (
                    cls._explicit_parent_reads(rewritten, tree, shape[1], owner)
                    if shape[1] == shape[2]
                    else rewritten
                )
                rewritten = cls._rewrite_facade_base_source(
                    explicit,
                    shape=shape,
                    owner=owner,
                    owner_bound=owner in bound,
                )
                changes.append(f"extended {shape[0]}.{owner} in {shape[3]}")
            if cls._facade_shapes(path, ast.parse(rewritten)):
                msg = f"facade base cutover left residue in {path}"
                raise ValueError(msg)
            return rewritten, tuple(changes)

        return cls._semantic_edits(
            tuple(item for item in items if item[0] in shapes),
            rewrite,
        )

    @staticmethod
    def _facade_shapes(
        path: Path,
        tree: ast.Module,
    ) -> t.VariadicTuple[t.Quad[str, str, str, str]]:
        """Return every ``(module, letter, local, facade)`` rebound letter base.

        One facade may extend several parents by their letters; the shapes
        are ordered by parent module so the rewrite is deterministic.

        Returns:
            Every ``(module, letter, local, facade)`` rebound letter base.

        Raises:
            ValueError: If relative facade base import is not a declared owner in.

        """
        imports: MutableMapping[str, t.Triple[str, str, int]] = {}
        rebinds: MutableMapping[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for imported in node.names:
                    imports[imported.asname or imported.name] = (
                        node.module or "",
                        imported.name,
                        node.level,
                    )
            elif (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Name)
            ):
                rebinds[node.targets[0].id] = node.value.id
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and isinstance(node.value, ast.Name)
            ):
                rebinds[node.target.id] = node.value.id
        shapes = {
            (module, imported, base.id, node.name, level)
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            for base in node.bases
            if isinstance(base, ast.Name) and base.id in imports
            for module, imported, level in (imports[base.id],)
            if rebinds.get(imported) == node.name
        }
        if any(level for *_rest, level in shapes):
            msg = f"relative facade base import is not a declared owner in {path}"
            raise ValueError(msg)
        return tuple(
            (module, imported, local, facade)
            for module, imported, local, facade, _level in sorted(shapes)
        )

    @staticmethod
    def _explicit_parent_reads(
        source: str,
        tree: ast.Module,
        letter: str,
        owner: str,
    ) -> str:
        """Spell the parent class wherever the letter is read before its rebind.

        Until the rebind executes, every eager read of the letter (class
        bases, class bodies, decorators, defaults) evaluates the imported
        parent, so writing the parent class there keeps runtime identical.
        Function and lambda bodies run after the rebind and keep the letter.

        Returns:
            The resulting ``str``.

        """
        rebind_line = max(
            node.lineno
            for node in tree.body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == letter
                for target in (
                    node.targets if isinstance(node, ast.Assign) else (node.target,)
                )
            )
        )
        reads: list[t.Pair[int, int]] = []
        pending: list[ast.AST] = list(tree.body)
        while pending:
            node = pending.pop()
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                pending.extend(node.decorator_list)
                pending.extend(node.args.defaults)
                pending.extend(
                    default for default in node.args.kw_defaults if default is not None
                )
                continue
            if isinstance(node, ast.Lambda):
                continue
            if (
                isinstance(node, ast.Name)
                and node.id == letter
                and isinstance(node.ctx, ast.Load)
                and node.lineno < rebind_line
            ):
                reads.append((node.lineno, node.col_offset))
            pending.extend(ast.iter_child_nodes(node))
        lines = source.splitlines(keepends=True)
        for lineno, column in sorted(reads, reverse=True):
            encoded = lines[lineno - 1].encode()
            lines[lineno - 1] = (
                encoded[:column] + owner.encode() + encoded[column + len(letter) :]
            ).decode()
        return "".join(lines)

    @staticmethod
    def _facade_bound_imports(tree: ast.Module, module: str) -> frozenset[str]:
        """Return names a module already imports unaliased from ``module``.

        Returns:
            Names a module already imports unaliased from ``module``.

        """
        return frozenset(
            imported.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and not node.level
            and node.module == module
            for imported in node.names
            if imported.asname is None
        )

    @staticmethod
    def _facade_module_bindings(tree: ast.Module) -> frozenset[str]:
        """Return every module-scope binding name.

        Returns:
            Every module-scope binding name.

        """
        names: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.ImportFrom | ast.Import):
                names.update(
                    imported.asname or imported.name.split(".")[0]
                    for imported in node.names
                )
        return frozenset(names)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverFacadeBases"]
