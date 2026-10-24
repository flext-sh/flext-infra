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
from functools import lru_cache, partial
from pathlib import Path
from typing import TYPE_CHECKING, override

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, RemoveImportsVisitor
from libcst.metadata import (
    Assignment,
    GlobalScope,
    MetadataWrapper,
    QualifiedNameProvider,
    QualifiedNameSource,
    Scope,
    ScopeProvider,
)

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticCutoverFacadeBaseCst,
    FlextInfraUtilitiesSemanticCutoverFacadeOwners,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping


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
            original_node: t.Infra.Cst.Attribute,
            updated_node: t.Infra.Cst.Attribute,
        ) -> t.Infra.Cst.BaseExpression:
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
            scope = self.get_metadata(ScopeProvider, original_node)
            if not isinstance(scope, Scope):
                msg = "behavior reference has no lexical scope"
                raise TypeError(msg)
            target = self._scoped_target(original_node, scope, target)
            module, receiver, member = target
            module_import = "." in receiver
            bound_name = receiver.split(".")[0]
            imported_identity = module if module_import else f"{module}.{receiver}"
            assignments = scope[bound_name]
            for assignment in assignments:
                qualified = assignment.get_qualified_names_for(bound_name)
                own_class = (
                    module == self.context.full_module_name
                    and isinstance(assignment, Assignment)
                    and isinstance(assignment.node, c.Infra.Cst.ClassDef)
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

        @staticmethod
        def _scoped_target(
            node: t.Infra.Cst.Attribute,
            scope: Scope,
            target: t.Triple[str, str, str],
        ) -> t.Triple[str, str, str]:
            """Qualify missing utility imports originating in local scopes.

            Returns:
                A distinct public module receiver, or the existing target.

            """
            module, receiver, member = target
            if (
                receiver != c.Infra.FacadeFamily.U
                or not isinstance(node.value, c.Infra.Cst.Name)
                or scope[receiver]
            ):
                return target
            assignments = scope[node.value.value]
            if assignments and all(
                not isinstance(assignment.scope, GlobalScope)
                for assignment in assignments
            ):
                return module, f"{module}.{receiver}", member
            return target

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
        *,
        project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Follow the imported facade's declared classes and base bindings.

        Returns:
            A tuple of pairs representing the lineage of the behavior, where each
            pair contains the module and class name.

        A ``ValueError`` fails on a cyclic or inconsistent facade inheritance
        identity, and a ``TypeError`` propagates from unsupported facade
        inheritance identities through ``_behavior_base_identity``.

        """
        resolved = cls._facade_declared_class(
            modules, module, receiver, frozenset(), project=project
        )
        if resolved is None:
            return ()
        return cls._class_identity_lineage(modules, resolved, project=project)

    @classmethod
    def _class_identity_lineage(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        identity: t.Pair[str, str],
        *,
        project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Linearize one declared class identity through its proven bases.

        Returns:
            The C3 lineage of module and class name pairs, starting at it.

        A ``ValueError`` fails on a cyclic, undeclared, or inconsistent facade
        inheritance identity, and a ``TypeError`` propagates from unsupported
        facade inheritance identities through ``_behavior_base_identity``.

        """
        cache: MutableMapping[t.Pair[str, str], t.VariadicTuple[t.Pair[str, str]]] = {}

        def linearize(
            current: t.Pair[str, str],
            visiting: frozenset[t.Pair[str, str]],
        ) -> t.VariadicTuple[t.Pair[str, str]]:
            if current in visiting:
                msg = f"cyclic facade inheritance identity: {current}"
                raise ValueError(msg)
            if current in cache:
                return cache[current]
            owner_module, owner_name = current
            declaration = cls._declared_class_node(modules[owner_module][0], owner_name)
            if declaration is None:
                msg = f"facade inheritance identity has no declaration: {current}"
                raise ValueError(msg)
            bases: list[t.Pair[str, str]] = []
            for base in declaration.bases:
                expression = base.value if isinstance(base, ast.Subscript) else base
                inherited = cls._behavior_base_identity(
                    modules, owner_module, expression, project=project
                )
                if inherited is not None:
                    bases.append(inherited)
            cache[current] = (
                current,
                *FlextInfraUtilitiesRopeSourceBasesRuntime.merge_class_lineages(
                    (
                        *(linearize(base, visiting | {current}) for base in bases),
                        tuple(bases),
                    ),
                    message=f"inconsistent facade inheritance identity: {current}",
                ),
            )
            return cache[current]

        return linearize(identity, frozenset())

    @classmethod
    def _behavior_base_identity(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        module: str,
        expression: ast.expr,
        *,
        project: p.Infra.RopeProject,
    ) -> t.Pair[str, str] | None:
        """Resolve a base's declared class, including imported-module attributes.

        Returns:
            The declared base identity, or no source-backed class.

        Raises:
            TypeError: If a base is not a supported proven binding.

        """
        if isinstance(expression, ast.Name):
            return cls._facade_declared_class(
                modules, module, expression.id, frozenset(), project=project
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
                    modules,
                    ".".join(target),
                    expression.attr,
                    frozenset(),
                    project=project,
                )
        if isinstance(expression, ast.Attribute):
            owner = (
                cls._facade_declared_class(
                    modules, module, expression.value.id, frozenset(), project=project
                )
                if isinstance(expression.value, ast.Name)
                else cls._behavior_base_identity(
                    modules, module, expression.value, project=project
                )
            )
            if owner is not None:
                # A class attribute resolves through the owner's own C3 lineage:
                # the nested class may be declared on an inherited base.
                for lineage_module, lineage_name in cls._class_identity_lineage(
                    modules, owner, project=project
                ):
                    nested = f"{lineage_name}.{expression.attr}"
                    if (
                        cls._declared_class_node(modules[lineage_module][0], nested)
                        is not None
                    ):
                        return lineage_module, nested
        msg = (
            "unsupported facade inheritance identity: "
            f"{module}.{ast.unparse(expression)}"
        )
        raise TypeError(msg)

    @staticmethod
    def _declared_class_node(source: str, qualified: str) -> ast.ClassDef | None:
        """Find a module class, or a class nested in one, by its dotted name.

        Returns:
            The declaration reached through each enclosing class body, if any.

        """
        body: t.SequenceOf[ast.stmt] = ast.parse(source).body
        declaration: ast.ClassDef | None = None
        for name in qualified.split("."):
            declaration = next(
                (
                    node
                    for node in body
                    if isinstance(node, ast.ClassDef) and node.name == name
                ),
                None,
            )
            if declaration is None:
                return None
            body = declaration.body
        return declaration

    @classmethod
    def behavior_source_modules(
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
            FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                c.Infra.MODELS_PY
            ).directory,
        ))
        # Provider discovery expands the inventory, never the owners eligible
        # for a reference. Its declared inheritance lineage elects those owners.
        base_imports: MutableMapping[str, t.StrTuple] = {}
        while True:
            inherited_statements = tuple(
                statement
                for module, (source, _package) in modules.items()
                if directories.intersection(module.split("."))
                or module.endswith((".typings", ".models", ".utilities"))
                for statement in (
                    base_imports[source]
                    if source in base_imports
                    else base_imports.setdefault(
                        source, cls._behavior_base_imports(source)
                    )
                )
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
            root.id
            for declaration in tree.body
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
            for root in ast.walk(base)
            if isinstance(root, ast.Name)
        }
        return tuple(
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and any((alias.asname or alias.name) in names for alias in node.names)
        )

    @classmethod
    def behavior_utility_owners(
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
                    if cls._behavior_member_binding(declaration, member.name) is member:
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
        *,
        project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Elect only a declared typing facade or its retired private binding.

        Returns:
            The elected typing lineage, or empty for an unrelated receiver.

        """
        package = module.split(".", 1)[0]
        declared = cls._facade_declared_class(
            modules, module, receiver, frozenset(), project=project
        )
        facade = cls._facade_declared_class(
            modules, package, c.Infra.FacadeFamily.T, frozenset(), project=project
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
                project=project,
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

        Raises:
            ValueError: If a lineage identity has no class declaration.

        """
        for owner_module, class_name in lineage:
            declaration = cls._declared_class_node(modules[owner_module][0], class_name)
            if declaration is None:
                msg = (
                    "facade inheritance identity has no declaration: "
                    f"{owner_module}.{class_name}"
                )
                raise ValueError(msg)
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

    @staticmethod
    def _behavior_import_roles(
        project: Path,
        path: Path,
        source: str,
    ) -> t.Pair[frozenset[t.Pair[str, str]], frozenset[t.Pair[str, str]]]:
        """Elect self utility and external declaration imports by their real layer.

        Returns:
            Exact imported identities for each permitted behavior rewrite.

        """
        namespace = FlextInfraUtilitiesImportLaw.import_namespace(project, path)
        if namespace is None:
            return frozenset(), frozenset()
        imports = frozenset(
            (node.module, alias.name)
            for node in ast.parse(source, filename=str(path)).body
            if isinstance(node, ast.ImportFrom) and node.module and not node.level
            for alias in node.names
            if alias.name == c.Infra.FacadeFamily.U
        )
        if any(
            isinstance(node, ast.Import)
            and any(alias.name == namespace[0].name for alias in node.names)
            for node in ast.parse(source, filename=str(path)).body
        ):
            imports |= {(namespace[0].name, c.Infra.FacadeFamily.U)}
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        layer = FlextInfraUtilitiesImportLaw.module_import_layer(namespace[1])
        if layer in {
            order.index(c.Infra.FacadeFamily.U),
            order.index(c.Infra.FacadeFamily.M),
        }:
            return (
                frozenset(
                    identity for identity in imports if identity[0] == namespace[0].name
                ),
                frozenset(
                    identity
                    for identity in imports
                    if layer == order.index(c.Infra.FacadeFamily.M)
                    and identity[0] != namespace[0].name
                ),
            )
        if layer <= order.index(c.Infra.FacadeFamily.M):
            return (
                frozenset(),
                frozenset(
                    identity for identity in imports if identity[0] != namespace[0].name
                ),
            )
        return frozenset(), frozenset()

    @classmethod
    def _plan_behavior_consumers(
        cls,
        sources: t.MappingKV[Path, str],
        *,
        native_project: p.Infra.RopeProject,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Resolve removed typing behavior to its unique declared utility owner.

        Internal consumers depend on the lower owner, never the utility facade
        that composes them. External consumers keep the public facade contract.
        Their manifest owners are resolved inside the authenticated graph, not
        restricted to the producer repository selected for publication.
        No retired class or method-name registry participates in discovery.

        Returns:
            Immutable consumer edits, or failures for unresolved identities.

        Raises:
            ValueError: If a consumer has no declared project owner.

        """
        typing_directory = (
            FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                c.Infra.TYPINGS_PY
            ).directory
        )
        owners: MutableMapping[Path, MutableMapping[Path, str]] = {}
        for path, source in sources.items():
            owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                Path(source_project.root.real_path),
                path,
                source_project=source_project,
            )
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
        for project_root, owner_sources in owners.items():
            modules = cls.behavior_source_modules(
                {**production, **owner_sources}, typing_directory
            )
            ownership = cls.behavior_utility_owners(
                modules,
                FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                    c.Infra.UTILITIES_PY
                ).directory,
            )

            def rewrite(
                path: Path,
                source: str,
                project_root: Path = project_root,
                modules: t.MappingKV[str, t.Pair[str, bool]] = modules,
                ownership: t.Pair[
                    t.MappingKV[t.Pair[str, str], t.SequenceOf[t.Pair[str, str]]],
                    frozenset[t.Quad[str, str, str, str]],
                ] = ownership,
            ) -> t.Infra.TransformResult:
                utility_imports, declaration_imports = cls._behavior_import_roles(
                    project_root, path, source
                )
                return cls.rewrite_behavior_consumer(
                    m.Infra.SemanticBehaviorRewriteRequest(
                        path=path,
                        source=source,
                        modules=modules,
                        ownership=ownership,
                        utility_imports=utility_imports,
                        declaration_imports=declaration_imports,
                    ),
                    native_project=native_project,
                    source_project=source_project,
                )

            planned = cls._semantic_edits(cls._editable_sources(owner_sources), rewrite)
            if planned.failure:
                return planned
            edits.extend(planned.value)
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(edits))

    @classmethod
    def _behavior_reference_target(
        cls,
        qualified: str,
        request: m.Infra.SemanticBehaviorRewriteRequest,
        lineage: t.SequenceOf[t.Pair[str, str]],
        *,
        project: p.Infra.RopeProject,
    ) -> t.Triple[str, str, str] | None:
        """Elect a unique relocated method owner in inherited precedence order.

        Returns:
            The module, receiver and member, or no target when none is declared.

        Raises:
            ValueError: If ownership is ambiguous or requires internal facade dispatch.

        """
        member = qualified.rpartition(".")[2]
        path, modules = request.path, request.modules
        owners, contextual = request.ownership
        if not any(
            owners.get((owner_module.partition(".")[0], member))
            for owner_module, _class in lineage
        ):
            return None
        public_lineage = cls._behavior_lineage(
            modules,
            qualified.partition(".")[0],
            c.Infra.FacadeFamily.U,
            project=project,
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
        project: p.Infra.RopeProject,
    ) -> bool:
        """Prove lexical import equivalence through the effective method owner.

        Returns:
            Whether both receivers reach the identical utility declaration.

        """
        module, receiver, member = target
        expected = cls._behavior_effective_declaration(
            modules,
            cls._behavior_lineage(modules, module, receiver, project=project),
            member,
        )
        existing, _, existing_receiver = binding.rpartition(".")
        effective = cls._behavior_effective_declaration(
            modules,
            cls._behavior_lineage(
                modules, existing, existing_receiver, project=project
            ),
            member,
        )
        return expected is not None and effective == expected

    @classmethod
    def rewrite_behavior_consumer(
        cls,
        request: m.Infra.SemanticBehaviorRewriteRequest,
        *,
        native_project: p.Infra.RopeProject,
        source_project: p.Infra.RopeProject,
    ) -> t.Infra.TransformResult:
        """Rebind proven imported behavior and compose its semantic import edits.

        Returns:
            The rewritten source and its changes, without publishing effects.

        """
        path = request.path
        source = request.source
        modules = request.modules
        ownership = request.ownership
        utility_imports = request.utility_imports
        declaration_imports = request.declaration_imports
        elected_imports = utility_imports | declaration_imports
        tree = ast.parse(source)
        identities = {
            (node.module, alias.name)
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module and not node.level
            for alias in node.names
        }
        identities.update(elected_imports)
        model_source = cls._is_model_behavior_source(path, source_project)
        obsolete: set[t.Pair[str, str]] = set()
        lineages: MutableMapping[
            t.Pair[str, str], t.VariadicTuple[t.Pair[str, str]]
        ] = {
            identity: lineage
            for identity in identities
            if (
                lineage := (
                    cls._behavior_lineage(modules, *identity, project=native_project)
                    if identity in elected_imports
                    else cls._typing_consumer_lineage(
                        modules, identity, project=native_project
                    )
                )
            )
        }

        # Owner facts are immutable for this request; lexical checks still run
        # for every reference. A new source/candidate creates a fresh resolver.
        @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
        def resolve(qualified: str) -> t.Triple[str, str, str] | None:
            own_import = next(
                (
                    identity
                    for identity in utility_imports
                    if qualified.startswith(".".join(identity) + ".")
                ),
                None,
            )
            if model_source and own_import is not None:
                target = cls._model_behavior_target(native_project, qualified)
                cls._record_obsolete_target(obsolete, own_import, target)
                return target
            imported = next(
                (
                    identity
                    for identity in lineages
                    if qualified.startswith(".".join(identity) + ".")
                    and qualified.removeprefix(".".join(identity) + ".").count(".") == 0
                ),
                None,
            )
            if imported is None:
                return None
            lineage = lineages[imported]
            if imported not in elected_imports and cls._behavior_member_declared(
                modules, lineage, qualified.rpartition(".")[2], ownership[0]
            ):
                return None
            if imported in elected_imports:
                member = qualified.rpartition(".")[2]
                effective = cls._behavior_effective_declaration(
                    modules, lineage, member
                )
                lower = cls._lower_behavior_targets(
                    request, effective, member, identities, project=native_project
                )
                cls._require_unambiguous_lower(lower, qualified)
                if lower:
                    obsolete.add(imported)
                    return lower[0]
                if imported in declaration_imports:
                    return None
            target = cls._behavior_reference_target(
                qualified, request, lineage, project=native_project
            )
            if target is None and imported in utility_imports:
                msg = f"self-facade callable owner is unresolved: {qualified}"
                raise ValueError(msg)
            cls._record_obsolete_target(obsolete, imported, target)
            return target

        if not lineages and not (model_source and utility_imports):
            return cls._behavior_consumer_outcome(
                request, source, (), project=native_project
            )
        return cls._rewrite_behavior_references(
            request, tree, resolve, obsolete, project=native_project
        )

    @classmethod
    def _rewrite_behavior_references(
        cls,
        request: m.Infra.SemanticBehaviorRewriteRequest,
        tree: ast.Module,
        resolve: Callable[[str], t.Triple[str, str, str] | None],
        obsolete: set[t.Pair[str, str]],
        *,
        project: p.Infra.RopeProject,
    ) -> t.Infra.TransformResult:
        """Rewrite resolved receivers and clean only the resulting obsolete imports.

        Returns:
            The checked concrete source and its actual behavior migration changes.

        """
        module_name = cls._source_module_name(request.path)
        context = CodemodContext(full_module_name=module_name)
        updated = MetadataWrapper(cst.parse_module(request.source)).visit(
            cls._BehaviorReferences(
                resolve,
                partial(
                    cls._equivalent_behavior_receiver,
                    modules=request.modules,
                    project=project,
                ),
                context,
            )
        )
        if not obsolete:
            return cls._behavior_consumer_outcome(
                request, request.source, (), project=project
            )
        cls._remove_obsolete_behavior_imports(context, tree, obsolete)
        updated = AddImportsVisitor(context).transform_module(updated)
        updated = RemoveImportsVisitor(context).transform_module(updated)
        return cls._behavior_consumer_outcome(
            request,
            updated.code,
            ("rebound relocated behavior to declared utility owners",),
            project=project,
        )

    @staticmethod
    def _is_model_behavior_source(
        path: Path, source_project: p.Infra.RopeProject
    ) -> bool:
        """Determine the consumer layer from its authenticated native project owner.

        Returns:
            Whether the source is declared in the configured model import layer.

        """
        project_root = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            Path(source_project.root.real_path), path, source_project=source_project
        )
        located = (
            FlextInfraUtilitiesImportLaw.import_namespace(project_root, path)
            if project_root is not None
            else None
        )
        return located is not None and (
            FlextInfraUtilitiesImportLaw.module_import_layer(located[1])
            == tuple(config.Infra.tooling.lazy_init.import_layer_order).index("m")
        )

    @classmethod
    def _typing_consumer_lineage(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        identity: t.Pair[str, str],
        *,
        project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Resolve a typing consumer against its declared family directory.

        Returns:
            The native behavior ancestry belonging to the typing identity.

        """
        directory = FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
            c.Infra.TYPINGS_PY
        ).directory
        return cls._typing_behavior_lineage(
            modules, *identity, directory, project=project
        )

    @staticmethod
    def _model_behavior_target(
        native_project: p.Infra.RopeProject | None, qualified: str
    ) -> t.Triple[str, str, str] | None:
        """Require native model ownership before resolving a utility declaration.

        Returns:
            The proven utility declaration target, or no eligible native method.

        Raises:
            ValueError: If the model cutover has no authenticated Rope project.

        """
        if native_project is None:
            msg = "model utility cutover requires its authenticated Rope project"
            raise ValueError(msg)
        return FlextInfraUtilitiesImportLaw.model_utility_target(
            native_project, qualified
        )

    @classmethod
    def _lower_behavior_targets(
        cls,
        request: m.Infra.SemanticBehaviorRewriteRequest,
        effective: t.Pair[str, str] | None,
        member: str,
        identities: set[t.Pair[str, str]],
        *,
        project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[t.Triple[str, str, str]]:
        """Elect lower model owners only for context-free static declarations.

        Returns:
            Matching model receivers reaching the same effective declaration.

        """
        declaration = cls._effective_declaration_node(request.modules, effective)
        context_free = cls._context_free_static_member(declaration, member)
        return tuple(
            (module, receiver, member)
            for module, receiver in identities
            if receiver == c.Infra.FacadeFamily.M
            and context_free
            and cls._behavior_effective_declaration(
                request.modules,
                cls._behavior_lineage(
                    request.modules, module, receiver, project=project
                ),
                member,
            )
            == effective
        )

    @classmethod
    def _behavior_consumer_outcome(
        cls,
        request: m.Infra.SemanticBehaviorRewriteRequest,
        source: str,
        changes: t.StrSequence,
        *,
        project: p.Infra.RopeProject,
    ) -> t.Infra.TransformResult:
        """Require residual self imports to be proven composition-only references.

        Returns:
            The candidate and its actual behavior edits.

        Raises:
            ValueError: If a self-facade import retains an unproved reference.

        """
        remaining = tuple(
            (node.module, alias.name, alias.asname or alias.name)
            for node in ast.parse(source, filename=str(request.path)).body
            if isinstance(node, ast.ImportFrom) and node.module is not None
            for alias in node.names
            if (node.module, alias.name) in request.utility_imports
        )
        if not remaining:
            return source, changes
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = runtime.build_string_module(
            project,
            source,
            resource=project.get_resource(
                request.path.relative_to(Path(project.root.real_path)).as_posix()
            ),
        )
        if not all(
            cls._behavior_composition_references(module, identity, project=project)
            for identity in remaining
        ):
            msg = (
                "self-facade reference has no declared callable binding: "
                f"{request.path}"
            )
            raise ValueError(msg)
        return source, changes

    @staticmethod
    def _behavior_composition_references(
        module: p.Infra.RopeSourceModule,
        identity: t.Triple[str, str, str],
        *,
        project: p.Infra.RopeProject,
    ) -> bool:
        """Prove every remaining receiver use is a direct native superclass.

        Returns:
            Whether the imported class is used exclusively for composition.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        imported_module, imported_name, local = identity
        qualified = f"{imported_module}.{imported_name}"
        binding = runtime.qualified_name(project, qualified)
        receiver = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(receiver) or not (
            runtime.same_name(
                binding,
                runtime.resolve_symbol(
                    module.get_scope(), ast.Name(id=local, ctx=ast.Load())
                ),
            )
        ):
            return False
        references = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_regions(
            module, f"${{{local}}}", arguments={local: f"name={qualified},exact"}
        )
        bases: set[t.Pair[int, int]] = set()
        pending = list(module.get_scope().get_scopes())
        while pending:
            scope = pending.pop()
            pending.extend(scope.get_scopes())
            owner = scope.pyobject
            if (
                scope.get_kind() != c.Infra.RopeScopeKind.CLASS
                or not FlextInfraUtilitiesRopeRuntimeTypes.py_class(owner)
                or receiver not in owner.get_superclasses()
            ):
                continue
            declaration = owner.get_ast()
            if not isinstance(declaration, ast.ClassDef):
                continue
            for base in declaration.bases:
                if not isinstance(base, ast.Name):
                    continue
                start = runtime.source_offset(module.source_code, base)
                lexical = runtime.scope_at(
                    module, start, declaration_line=declaration.lineno
                )
                if runtime.same_name(binding, runtime.resolve_symbol(lexical, base)):
                    bases.add((start, start + len(base.id)))
        return bool(references) and set(references) <= bases

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

    @staticmethod
    def _require_unambiguous_lower(
        lower: t.SequenceOf[t.Triple[str, str, str]],
        qualified: str,
    ) -> None:
        """Fail when more than one lower receiver declares the member.

        Args:
            lower: The lower receivers declaring the effective member.
            qualified: The qualified reference being resolved.

        Raises:
            ValueError: If more than one lower receiver declares the member.

        """
        if len(lower) > 1:
            msg = f"ambiguous lower declaration receiver: {qualified}"
            raise ValueError(msg)

    @staticmethod
    def _record_obsolete_target(
        obsolete: set[t.Pair[str, str]],
        imported: t.Pair[str, str],
        target: t.Triple[str, str, str] | None,
    ) -> None:
        """Mark an elected import obsolete once its reference target resolves.

        Args:
            obsolete: The elected imports proven obsolete.
            imported: The imported module/name identity.
            target: The resolved reference target, when present.

        """
        if target is not None:
            obsolete.add(imported)

    @classmethod
    def _effective_declaration_node(
        cls,
        modules: t.MappingKV[str, t.Pair[str, bool]],
        effective: t.Pair[str, str] | None,
    ) -> ast.ClassDef | None:
        """Return the declared class node of an effective declaration.

        Returns:
            The declared class node, or ``None`` when there is no effective
            declaration.

        Raises:
            ValueError: If the effective identity has no class declaration.

        """
        if effective is None:
            return None
        declaration = cls._declared_class_node(modules[effective[0]][0], effective[1])
        if declaration is None:
            msg = (
                "facade inheritance identity has no declaration: "
                f"{effective[0]}.{effective[1]}"
            )
            raise ValueError(msg)
        return declaration

    @classmethod
    def _context_free_static_member(
        cls,
        declaration: ast.ClassDef | None,
        member: str,
    ) -> bool:
        """Return whether a class member is a context-free static method.

        Returns:
            Whether the bound member is declared as a ``@staticmethod``.

        """
        binding = (
            cls._behavior_member_binding(declaration, member)
            if declaration is not None
            else None
        )
        return isinstance(binding, ast.FunctionDef | ast.AsyncFunctionDef) and any(
            isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
            for decorator in binding.decorator_list
        )

    @staticmethod
    def _source_module_name(path: Path) -> str | None:
        """Return the importable module name for a source under ``src``.

        Returns:
            The dotted module name, or ``None`` when the path is outside ``src``.

        """
        indices = tuple(
            index
            for index, part in enumerate(path.parts)
            if part == c.Infra.DEFAULT_SRC_DIR
        )
        if not indices:
            return None
        return ".".join((*path.parts[indices[-1] + 1 : -1], path.stem))

    @classmethod
    def _plan_facade_bases(
        cls,
        root: Path,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModOccurrence],
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
                owner = cls._facade_declared_owner(
                    modules, shape[0], shape[1], project=project
                )
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

        with FlextInfraUtilitiesRopeCore.open_import_project(root) as project:
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
