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
from functools import partial
from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import (
    Assignment,
    MetadataWrapper,
    QualifiedNameProvider,
    QualifiedNameSource,
    Scope,
    ScopeProvider,
)

from flext_infra import c, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesProjectDiscovery,
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
            resolve_reference: Callable[[str], t.Triple[str, str, str] | None],
            equivalent_receiver: Callable[[str, t.Triple[str, str, str]], bool],
            context: CodemodContext,
        ) -> None:
            self.resolve_reference = resolve_reference
            self.equivalent_receiver = equivalent_receiver
            self.context = context
            self.destinations: t.MutableMappingKV[str, str] = {}

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
                self.resolve_reference(name.name)
                if name.source is QualifiedNameSource.IMPORT
                else None
                for name in names
            }
            if not targets or targets == {None}:
                return updated_node
            if len(targets) != 1 or (target := targets.pop()) is None:
                msg = "behavior reference has ambiguous imported identity"
                raise ValueError(msg)
            module, receiver, member = target
            module_import = "." in receiver
            bound_name = receiver.split(".")[0]
            imported_identity = module if module_import else f"{module}.{receiver}"
            scope = self.get_metadata(ScopeProvider, original_node)
            if not isinstance(scope, Scope):
                msg = "behavior reference has no lexical scope"
                raise TypeError(msg)
            assignments = scope[bound_name]
            for assignment in assignments:
                qualified = assignment.get_qualified_names_for(bound_name)
                own_class = (
                    module == self.context.full_module_name
                    and isinstance(assignment, Assignment)
                    and isinstance(assignment.node, cst.ClassDef)
                    and assignment.node.name.value == receiver
                )
                if not own_class and (
                    not qualified
                    or any(
                        name.source is not QualifiedNameSource.IMPORT
                        or (
                            name.name != imported_identity
                            and not self.equivalent_receiver(name.name, target)
                        )
                        for name in qualified
                    )
                ):
                    msg = f"relocated behavior receiver is shadowed: {receiver}"
                    raise ValueError(msg)
            if module != self.context.full_module_name and not assignments:
                self._reserve_destination(bound_name, imported_identity)
                AddImportsVisitor.add_needed_import(
                    self.context, module, None if module_import else receiver
                )
            return cst.Attribute(cst.parse_expression(receiver), cst.Name(member))

        def _reserve_destination(self, bound_name: str, identity: str) -> None:
            """Reserve module-global imports across all lexical consumer scopes.

            Raises:
                ValueError: If pending imports would bind different owners to one name.

            """
            if (
                bound_name in self.destinations
                and self.destinations[bound_name] != identity
            ):
                msg = f"conflicting relocated behavior import destination: {bound_name}"
                raise ValueError(msg)
            self.destinations[bound_name] = identity

    @classmethod
    def _behavior_lineage(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        module: str,
        receiver: str,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Follow the imported facade's declared classes and base bindings.

        Returns:
            Pairs of module and class names representing the behavior lineage.
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
                inherited = cls._behavior_base_identity(
                    modules, owner_module, expression
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
    def _behavior_base_identity(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        module: str,
        expression: ast.expr,
    ) -> t.Pair[str, str] | None:
        """Resolve a base's declared class, including imported-module attributes.

        Returns:
            The declared base identity, or no source-backed class.

        Raises:
            TypeError: If a base is not a supported proven binding.

        """
        if isinstance(expression, ast.Name):
            return cls._facade_declared_class(
                modules, module, expression.id, frozenset()
            )
        if isinstance(expression, ast.Attribute) and isinstance(
            expression.value, ast.Name
        ):
            source, is_package = modules[module]
            package = module if is_package else module.rpartition(".")[0]
            target, _declared = cls._facade_binding_state(
                source, module, expression.value.id, package
            )
            if target is not None and ".".join(target) in modules:
                return cls._facade_declared_class(
                    modules, ".".join(target), expression.attr, frozenset()
                )
        msg = (
            "unsupported facade inheritance identity: "
            f"{module}.{ast.unparse(expression)}"
        )
        raise TypeError(msg)

    @classmethod
    def _behavior_source_modules(
        cls,
        sources: t.MappingKV[Path, str],
        typing_directory: str,
    ) -> t.MappingKV[str, t.Pair[str, bool]]:
        """Index contextual packages and expand referenced facade inheritance.

        Returns:
            Live source modules needed for behavior ownership resolution.

        Raises:
            ValueError: If contextual packages declare the same module identity.

        """
        statements = tuple(
            statement
            for source in sources.values()
            for statement in cls._behavior_imports(source)
        )
        contextual: MutableMapping[str, t.Pair[str, bool]] = {}
        for path, source in sources.items():
            if c.Infra.DEFAULT_SRC_DIR in path.parts:
                continue
            package = path.parent
            while package / c.Infra.INIT_PY in sources:
                package = package.parent
            if package == path.parent:
                continue
            parts = path.relative_to(package).parts
            module = ".".join(
                parts[:-1] if path.name == c.Infra.INIT_PY else (*parts[:-1], path.stem)
            )
            if module in contextual:
                msg = f"ambiguous contextual behavior module identity: {module}"
                raise ValueError(msg)
            contextual[module] = (source, path.name == c.Infra.INIT_PY)
        contextual_packages = {module.partition(".")[0] for module in contextual}
        statements = tuple(
            statement
            for statement in statements
            if not any(
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.partition(".")[0] in contextual_packages
                for node in ast.walk(ast.parse(statement))
            )
        )
        modules = FlextInfraUtilitiesPrivateImportFacades.source_modules(
            sources, statements
        )
        modules.update(contextual)
        directories = frozenset((
            typing_directory,
            FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                c.Infra.UTILITIES_PY
            ).directory,
        ))
        # Provider discovery expands the inventory, never the owners eligible
        # for a reference. Its declared inheritance lineage elects those owners.
        while True:
            inherited_statements = tuple(
                statement
                for module, (source, _package) in modules.items()
                if directories.intersection(module.split("."))
                or module.endswith((".typings", ".utilities"))
                for statement in cls._behavior_base_imports(source)
            )
            expanded = FlextInfraUtilitiesPrivateImportFacades.source_modules(
                sources, (*statements, *inherited_statements)
            )
            expanded.update(contextual)
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
        receiver_names = frozenset((
            c.Infra.FacadeFamily.T,
            c.Infra.FacadeFamily.U,
        ))
        return tuple(
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and not node.level
            and any(
                alias.name in receiver_names or (alias.asname or alias.name) in called
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

    @classmethod
    def _behavior_utility_owners(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        utility_directory: str,
    ) -> t.Pair[
        t.MappingKV[t.Pair[str, str], t.SequenceOf[t.Pair[str, str]]],
        frozenset[t.Quad[str, str, str, str]],
    ]:
        """Index exported utility methods and their contextual dispatch needs.

        Returns:
            Discovered method owners and methods requiring facade dispatch.

        """
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
                    if (
                        utility_directory in parts
                        and declaration.name in exports
                        and not member.name.startswith("_")
                        and cls._behavior_member_binding(declaration, member.name)
                        is member
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
        return owners, frozenset(contextual)

    @classmethod
    def _typing_behavior_lineage(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        module: str,
        receiver: str,
        typing_directory: str,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Elect only a declared typing facade or its retired private binding.

        Returns:
            The elected typing lineage, or empty for an unrelated receiver.

        """
        package = module.split(".", 1)[0]
        declared = cls._facade_declared_class(modules, module, receiver, frozenset())
        facade = cls._facade_declared_class(
            modules, package, c.Infra.FacadeFamily.T, frozenset()
        )
        retired = (
            typing_directory in module.split(".")
            and module not in modules
            and facade is not None
        )
        if retired or (declared is not None and declared == facade):
            return cls._behavior_lineage(
                modules,
                package if retired else module,
                c.Infra.FacadeFamily.T if retired else receiver,
            )
        return ()

    @classmethod
    def _behavior_member_declared(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        lineage: t.SequenceOf[t.Pair[str, str]],
        member: str,
        owners: t.MappingKV[t.Pair[str, str], t.SequenceOf[t.Pair[str, str]]],
    ) -> bool:
        """Keep typing-owned bindings, never utility behavior inherited through t.

        Returns:
            Whether the effective binding remains outside the utility owners.

        """
        effective = cls._behavior_effective_declaration(modules, lineage, member)
        return effective is not None and effective not in owners.get(
            (effective[0].partition(".")[0], member), ()
        )

    @classmethod
    def _behavior_effective_declaration(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        lineage: t.SequenceOf[t.Pair[str, str]],
        member: str,
    ) -> t.Pair[str, str] | None:
        """Locate the first C3 class that binds a member, including non-method masks.

        Returns:
            The effective declaring class identity, or no declaration.

        """
        for owner_module, class_name in lineage:
            declaration = next(
                node
                for node in ast.parse(modules[owner_module][0]).body
                if isinstance(node, ast.ClassDef) and node.name == class_name
            )
            if cls._behavior_member_binding(declaration, member) is not None:
                return owner_module, class_name
        return None

    @classmethod
    def _behavior_member_binding(
        cls,
        declaration: ast.ClassDef,
        member: str,
    ) -> ast.stmt | None:
        """Follow class execution order without treating bare annotations as masks.

        Returns:
            The last statement that binds the member, or no class binding.

        """
        for node in reversed(declaration.body):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                if node.name == member:
                    return node
            elif (
                isinstance(node, ast.Assign | ast.AnnAssign)
                and node.value is not None
                and cls._assigns_name(node, member)
            ):
                return node
        return None

    @classmethod
    def _plan_behavior_consumers(
        cls,
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Resolve removed typing behavior to its unique declared utility owner.

        Internal consumers depend on the lower owner, never the utility facade
        that composes them. External consumers keep the public facade contract.
        No retired class or method-name registry participates in discovery.

        Returns:
            Immutable consumer edits, or failures for unresolved identities.

        """
        typing_directory = (
            FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                c.Infra.TYPINGS_PY
            ).directory
        )
        owners: MutableMapping[Path, MutableMapping[Path, str]] = {}
        for path, source in sources.items():
            owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(root, path)
            if owner is None:
                msg = f"behavior consumer project owner is unresolved: {path}"
                raise ValueError(msg)
            owners.setdefault(owner, {})[path] = source
        production = {
            path: source
            for path, source in sources.items()
            if c.Infra.DEFAULT_SRC_DIR in path.parts
        }
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for owner_sources in owners.values():
            modules = cls._behavior_source_modules(
                {**production, **owner_sources}, typing_directory
            )
            ownership = cls._behavior_utility_owners(
                modules,
                FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                    c.Infra.UTILITIES_PY
                ).directory,
            )
            planned = cls._semantic_edits(
                cls._editable_sources(owner_sources),
                partial(
                    cls._rewrite_behavior_consumer,
                    modules=modules,
                    typing_directory=typing_directory,
                    ownership=ownership,
                ),
            )
            if planned.failure:
                return planned
            edits.extend(planned.value)
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(edits))

    @classmethod
    def _behavior_reference_target(
        cls,
        qualified: str,
        path: Path,
        lineage: t.SequenceOf[t.Pair[str, str]],
        modules: t.MappingKV[str, t.Pair[str, bool]],
        ownership: t.Pair[
            t.MappingKV[t.Pair[str, str], t.SequenceOf[t.Pair[str, str]]],
            frozenset[t.Quad[str, str, str, str]],
        ],
    ) -> t.Triple[str, str, str] | None:
        """Elect a unique relocated method owner in inherited precedence order.

        Returns:
            The module, receiver and member, or no target when none is declared.

        Raises:
            ValueError: If ownership is ambiguous or requires internal facade dispatch.

        """
        member = qualified.rpartition(".")[2]
        owners, contextual = ownership
        if not any(
            owners.get((owner_module.partition(".")[0], member))
            for owner_module, _class in lineage
        ):
            return None
        public_lineage = cls._behavior_lineage(
            modules, qualified.partition(".")[0], c.Infra.FacadeFamily.U
        )
        effective = cls._behavior_effective_declaration(modules, public_lineage, member)
        if effective is None or effective not in owners.get(
            (effective[0].partition(".")[0], member), ()
        ):
            msg = (
                "relocated behavior is not reachable through public utilities: "
                f"{qualified}"
            )
            raise ValueError(msg)
        owner_module, owner_class = effective
        owner_package = owner_module.split(".", 1)[0]
        internal = owner_package in path.parts and c.Infra.DEFAULT_SRC_DIR in path.parts
        if (
            internal
            and (owner_package, owner_module, owner_class, member) in contextual
        ):
            msg = f"lower behavior owner requires facade dispatch: {qualified}"
            raise ValueError(msg)
        return (
            owner_module if internal else qualified.partition(".")[0],
            owner_class if internal else c.Infra.FacadeFamily.U,
            member,
        )

    @classmethod
    def _equivalent_behavior_receiver(
        cls,
        binding: str,
        target: t.Triple[str, str, str],
        *,
        modules: t.MappingKV[str, t.Pair[str, bool]],
    ) -> bool:
        """Prove lexical import equivalence through the effective method owner.

        Returns:
            Whether both receivers reach the identical utility declaration.
        """
        module, receiver, member = target
        if receiver != c.Infra.FacadeFamily.U:
            return False
        expected = cls._behavior_effective_declaration(
            modules, cls._behavior_lineage(modules, module, receiver), member
        )
        existing, _, existing_receiver = binding.rpartition(".")
        effective = cls._behavior_effective_declaration(
            modules, cls._behavior_lineage(modules, existing, existing_receiver), member
        )
        return expected is not None and effective == expected

    @classmethod
    def _rewrite_behavior_consumer(
        cls,
        path: Path,
        source: str,
        *,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        typing_directory: str,
        ownership: t.Pair[
            t.MappingKV[t.Pair[str, str], t.SequenceOf[t.Pair[str, str]]],
            frozenset[t.Quad[str, str, str, str]],
        ],
    ) -> t.Infra.TransformResult:
        """Rebind proven imported behavior and compose its semantic import edits.

        Returns:
            The rewritten source and its changes, without publishing effects.

        """
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
                    and qualified.removeprefix(".".join(identity) + ".").count(".") == 0
                ),
                None,
            )
            if imported is None:
                return None
            module, receiver = imported
            if imported not in lineages:
                lineages[imported] = cls._typing_behavior_lineage(
                    modules, module, receiver, typing_directory
                )
            lineage = lineages[imported]
            if cls._behavior_member_declared(
                modules, lineage, qualified.rpartition(".")[2], ownership[0]
            ):
                return None
            target = cls._behavior_reference_target(
                qualified, path, lineage, modules, ownership
            )
            if target is not None:
                obsolete.add(imported)
            return target

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
            cls._BehaviorReferences(
                resolve,
                partial(cls._equivalent_behavior_receiver, modules=modules),
                context,
            )
        )
        cls._remove_obsolete_behavior_imports(context, tree, obsolete)
        updated = AddImportsVisitor(context).transform_module(updated)
        updated = RemoveImportsVisitor(context).transform_module(updated)
        return updated.code, ("rebound relocated behavior to declared utility owners",)

    @staticmethod
    def _remove_obsolete_behavior_imports(
        context: CodemodContext,
        tree: ast.Module,
        obsolete: set[t.Pair[str, str]],
    ) -> None:
        """Schedule removal only for imports whose proven behavior was rebound."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            for alias in node.names:
                if (node.module, alias.name) in obsolete:
                    RemoveImportsVisitor.remove_unused_import(
                        context, node.module, alias.name, alias.asname
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
                local_rebound = any(
                    isinstance(node, ast.Assign | ast.AnnAssign)
                    and cls._assigns_name(node, shape[2])
                    and isinstance(node.value, ast.Name)
                    and node.value.id == shape[3]
                    for node in tree.body
                )
                owner = cls._facade_declared_owner(modules, shape[0], shape[1])
                bound = cls._facade_bound_imports(tree, shape[0])
                if owner in cls._facade_module_bindings(tree) - bound:
                    msg = f"{owner} is already bound locally in {path}"
                    raise ValueError(msg)
                explicit = (
                    cls._explicit_parent_reads(rewritten, tree, shape[2], owner)
                    if local_rebound
                    else rewritten
                )
                rewritten = cls._rewrite_facade_base_source(
                    explicit,
                    shape=shape,
                    owner=owner,
                    owner_bound=owner in bound,
                    local_rebound=local_rebound,
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
            if rebinds.get(imported) == node.name or rebinds.get(base.id) == node.name
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
