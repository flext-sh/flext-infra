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
    MetadataWrapper,
    QualifiedNameProvider,
    QualifiedNameSource,
    ScopeProvider,
)

from flext_infra import c, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesPrivateImportFacades,
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
            self.resolve = resolve
            self.context = context

        @override
        def leave_Attribute(
            self,
            original_node: cst.Attribute,
            updated_node: cst.Attribute,
        ) -> cst.BaseExpression:
            names = self.get_metadata(QualifiedNameProvider, original_node, ())
            targets = {
                target
                for name in names
                if name.source is QualifiedNameSource.IMPORT
                and (target := self.resolve(name.name)) is not None
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
            scope = self.get_metadata(ScopeProvider, original_node)
            for assignment in scope[bound_name]:
                qualified = assignment.get_qualified_names_for(bound_name)
                own_class = (
                    module == self.context.full_module_name
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

        Args:
            modules: A mapping of module names to their source code and a boolean flag.
            module: The name of the module containing the facade.
            receiver: The name of the class being resolved.

        Returns:
            A tuple of pairs representing the lineage of the behavior, where each pair contains the module and class name.

        Raises:
            TypeError: If an unsupported facade inheritance identity is encountered.
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
                    msg = f"unsupported facade inheritance identity: {owner_module}.{owner_name}"
                    raise TypeError(msg)
                inherited = cls._facade_declared_class(
                    modules, owner_module, expression.id, frozenset()
                )
                if inherited is not None:
                    bases.append(inherited)
            sequences = [list(linearize(base, visiting | {identity})) for base in bases]
            sequences.append(list(bases))
            lineage = [identity]
            while any(sequences):
                chosen = next(
                    (
                        sequence[0]
                        for sequence in sequences
                        if sequence
                        and not any(sequence[0] in tail[1:] for tail in sequences)
                    ),
                    None,
                )
                if chosen is None:
                    msg = f"inconsistent facade inheritance identity: {identity}"
                    raise ValueError(msg)
                lineage.append(chosen)
                for sequence in sequences:
                    if sequence and sequence[0] == chosen:
                        sequence.pop(0)
            cache[identity] = tuple(lineage)
            return cache[identity]

        return linearize(resolved, frozenset())

    @classmethod
    def _plan_behavior_consumers(
        cls,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Resolve removed typing behavior to its unique declared utility owner.

        Internal consumers depend on the lower owner, never the utility facade
        that composes them. External consumers keep the public facade contract.
        No retired class or method-name registry participates in discovery.

        Args:
            sources: A mapping from file paths to their source code content.

        Returns:
            A result containing a variadic tuple of semantic migration edits.
        """
        statements = tuple(
            ast.unparse(node)
            for source in sources.values()
            for tree in (ast.parse(source),)
            for called in (
                {
                    call.func.value.id
                    for call in ast.walk(tree)
                    if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                },
            )
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and not node.level
            and any(
                alias.name in {"t", "u"} or (alias.asname or alias.name) in called
                for alias in node.names
            )
        )
        modules = FlextInfraUtilitiesPrivateImportFacades.source_modules(
            sources, statements
        )
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        utility_directory = families["u"].directory
        typing_directory = families["t"].directory
        # Provider discovery expands the inventory, never the owners eligible
        # for a reference. Its declared inheritance lineage elects those owners.
        while True:
            inherited_statements = tuple(
                ast.unparse(node)
                for module, (source, _package) in modules.items()
                if typing_directory in module.split(".") or module.endswith(".typings")
                for tree in (ast.parse(source),)
                for names in (
                    {
                        base.id
                        for declaration in tree.body
                        if isinstance(declaration, ast.ClassDef)
                        for base in declaration.bases
                        if isinstance(base, ast.Name)
                    },
                )
                for node in tree.body
                if isinstance(node, ast.ImportFrom)
                and any((alias.asname or alias.name) in names for alias in node.names)
            )
            expanded = FlextInfraUtilitiesPrivateImportFacades.source_modules(
                sources, (*statements, *inherited_statements)
            )
            if expanded.keys() == modules.keys():
                break
            statements = (*statements, *inherited_statements)
            modules = expanded
        owners: MutableMapping[t.Pair[str, str], list[t.Pair[str, str]]] = {}
        contextual: set[t.Quad[str, str, str, str]] = set()
        for module, (source, _package) in modules.items():
            parts = module.split(".")
            if utility_directory not in parts and typing_directory not in parts:
                continue
            tree = ast.parse(source)
            exports = {
                name
                for node in tree.body
                if isinstance(node, ast.Assign | ast.AnnAssign)
                and node.value is not None
                and any(
                    isinstance(target, ast.Name) and target.id == "__all__"
                    for target in (
                        node.targets if isinstance(node, ast.Assign) else (node.target,)
                    )
                )
                for name in ast.literal_eval(node.value)
            }
            for declaration in tree.body:
                if not isinstance(declaration, ast.ClassDef):
                    continue
                for member in declaration.body:
                    if not isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef):
                        continue
                    if (
                        utility_directory in parts
                        and declaration.name in exports
                        and not member.name.startswith("_")
                    ):
                        owners.setdefault((parts[0], member.name), []).append((
                            module,
                            declaration.name,
                        ))
                        decorators = {
                            decorator.id
                            for decorator in member.decorator_list
                            if isinstance(decorator, ast.Name)
                        }
                        parameters = (*member.args.posonlyargs, *member.args.args)
                        if "staticmethod" not in decorators and (
                            "classmethod" not in decorators
                            or not parameters
                            or any(
                                isinstance(reference, ast.Name)
                                and reference.id == parameters[0].arg
                                for statement in member.body
                                for reference in ast.walk(statement)
                            )
                        ):
                            contextual.add((
                                parts[0],
                                module,
                                declaration.name,
                                member.name,
                            ))

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            tree = ast.parse(source)
            identities = {
                (node.module, alias.name)
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module and not node.level
                for alias in node.names
            }
            obsolete: set[t.Pair[str, str]] = set()
            lineages: MutableMapping[
                t.Pair[str, str], t.VariadicTuple[t.Pair[str, str]]
            ] = {}

            def resolve(qualified: str) -> t.Triple[str, str, str] | None:
                imported = next(
                    (
                        identity
                        for identity in identities
                        if qualified.startswith(".".join(identity) + ".")
                        and qualified.removeprefix(".".join(identity) + ".").count(".")
                        == 0
                    ),
                    None,
                )
                if imported is None:
                    return None
                module, receiver = imported
                package = module.split(".")[0]
                member = qualified.rpartition(".")[2]
                if imported not in lineages:
                    declared = cls._facade_declared_class(
                        modules, module, receiver, frozenset()
                    )
                    facade = cls._facade_declared_class(
                        modules, package, "t", frozenset()
                    )
                    retired = (
                        typing_directory in module.split(".")
                        and module not in modules
                        and facade is not None
                    )
                    lineages[imported] = (
                        cls._behavior_lineage(
                            modules,
                            package if retired else module,
                            "t" if retired else receiver,
                        )
                        if retired or (declared is not None and declared == facade)
                        else ()
                    )
                lineage = lineages[imported]
                if any(
                    isinstance(declaration, ast.ClassDef)
                    and declaration.name == class_name
                    and any(
                        isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef)
                        and method.name == member
                        for method in declaration.body
                    )
                    for owner_module, class_name in lineage
                    for declaration in ast.parse(modules[owner_module][0]).body
                ):
                    return None
                candidates: t.SequenceOf[t.Pair[str, str]] = ()
                for owner_module, _class in lineage:
                    candidates = owners.get((owner_module.split(".")[0], member), ())
                    if candidates:
                        break
                if not candidates:
                    return None
                if len(candidates) != 1:
                    msg = f"ambiguous relocated behavior owner: {qualified}"
                    raise ValueError(msg)
                owner_module, owner_class = candidates[0]
                owner_package = owner_module.split(".")[0]
                internal = (
                    owner_package in path.parts
                    and c.Infra.DEFAULT_SRC_DIR in path.parts
                )
                if (
                    internal
                    and (owner_package, owner_module, owner_class, member) in contextual
                ):
                    msg = f"lower behavior owner requires facade dispatch: {qualified}"
                    raise ValueError(msg)
                obsolete.add(imported)
                return (
                    owner_module if internal else package,
                    owner_class if internal else f"{package}.u",
                    member,
                )

            if not identities:
                return source, ()
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
                cls._BehaviorReferences(resolve, context)
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom) or node.module is None:
                    continue
                for alias in node.names:
                    if (node.module, alias.name) in obsolete:
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
