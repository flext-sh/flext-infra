"""Facade component calls use their identity-proven composed public receiver.

Every facade letter, and every namespace class nested in it, composes family
component classes by MRO. A consumer that calls a method through the component
class instead of its composed facade namespace bypasses the facade alphabet.
The generated rules derive both receiver identities from native composition;
constructors and entity references retain their declared owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Generator, Mapping, Sequence
from functools import cache, partial
from importlib.metadata import packages_distributions
from pathlib import Path

import rope.base.exceptions
from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import (
    FlextInfraUtilitiesCodemodNative,
    FlextInfraUtilitiesCodemodNativePackage,
)
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesFacadeComponents:
    """Derive component-to-namespace references and render their relocation."""

    @staticmethod
    def _same_facade_target(
        occupied: p.Infra.RopePyObject, provider: p.Infra.RopeSourceClass
    ) -> bool:
        """Whether an occupied binding names the same class the planning holds.

        Rope yields distinct PyClass instances for one logical class when the
        provider was resolved through a different project instance (snapshot
        overlay vs live module scan); object identity would then reject a
        binding that is in fact the class the facade already imports. Two
        bindings name the same target when both are classes of the same
        qualified origin (module + name); a genuine collision — a different
        class reusing the short name — keeps the occupation verdict.

        Returns:
            Whether both objects denote the same underlying class.

        """
        if occupied is provider:
            return True
        if not FlextInfraUtilitiesRopeRuntime.abstract_class(occupied):
            return False
        occupied_module = occupied.get_module()
        return (
            occupied_module is not None
            and occupied_module.get_name() == provider.get_module().get_name()
            and occupied.get_name() == provider.get_name()
        )

    @staticmethod
    def generate_module_skeleton(
        *,
        context: m.Infra.ModuleSkeletonRenderContext,
    ) -> p.Result[str]:
        """Fill the existing module template with its validated native inventory.

        Returns:
            Rendered source or the template owner's original typed failure.

        """
        template = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATE_MODULE_SKELETON
        )
        return u.Cli.template_render(template, context)

    @staticmethod
    def facade_component_declarations(
        project: p.Infra.RopeProject,
        directory: Path,
    ) -> tuple[tuple[Path, p.Infra.RopeSourceClass], ...]:
        """Read exported local declarations from the indexed immediate modules.

        Returns:
            Source-owned classes, without reconstructing a syntax inventory.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        declarations: list[tuple[Path, p.Infra.RopeSourceClass]] = []
        for path in sorted(project.source_children(directory)):
            if path.name == c.Infra.INIT_PY or path.suffix != c.Infra.EXT_PYTHON:
                continue
            if not project.source_query(path, "isfile"):
                continue
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                project.get_pymodule(runtime.file_resource_at(project, path))
            )
            exported = (
                FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                    module
                )
            )
            for scope in module.get_scope().get_scopes():
                owner = scope.pyobject
                if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(owner):
                    continue
                binding = module.get_attributes().get(owner.get_name())
                if (
                    owner.get_name() in exported
                    and binding is not None
                    and binding.get_object() is owner
                    and owner.get_module() is module
                ):
                    declarations.append((path, owner))
        return tuple(declarations)

    @classmethod
    def facade_domain_declarations(
        cls,
        project: p.Infra.RopeProject,
        directory: Path,
        declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
    ) -> tuple[tuple[Path, p.Infra.RopeSourceClass], ...]:
        """Read the elected owner of every private domain below a family directory.

        A private domain package (``_name/``) reaches its family facade only
        through the owner ``family_subfacade_owners`` elects. An owner already
        among the immediate declarations is that same declaration and is not
        repeated; an owner kept inside its domain package is admitted here.
        ``declarations`` are the family directory's own, already read once.

        Returns:
            Each domain owner kept inside its domain package, in path order.

        Raises:
            TypeError: If an elected domain owner is not a native source class.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        owners: list[tuple[Path, p.Infra.RopeSourceClass]] = []
        domains = tuple(
            domain
            for domain in sorted(project.source_children(directory))
            if domain.name.startswith("_")
            and project.source_query(domain / c.Infra.INIT_PY, "isfile")
        )
        elected = cls._family_subfacade_owner_map(
            project, domains, {directory: declarations}
        )
        for domain in domains:
            for path, name in elected[domain]:
                if path.parent == directory:
                    continue
                module = types.require_source_module(
                    project.get_pymodule(runtime.file_resource_at(project, path))
                )
                owner = module.get_attributes()[name].get_object()
                if not types.py_class(owner):
                    message = (
                        f"Elected domain owner is not a source class: {path}:{name}"
                    )
                    raise TypeError(message)
                owners.append((path, owner))
        return tuple(owners)

    @classmethod
    def family_subfacade_owners(
        cls,
        project: p.Infra.RopeProject,
        directory: Path,
    ) -> list[tuple[Path, str]]:
        """Elect actual compositions by native base and publication identity.

        Returns:
            Maximal native owners at the canonical sibling precedence.

        """
        return cls.family_subfacade_owner_map(project, (directory,))[directory]

    @classmethod
    def family_subfacade_owner_map(
        cls,
        project: p.Infra.RopeProject,
        directories: Sequence[Path],
    ) -> dict[Path, list[tuple[Path, str]]]:
        """Elect every domain owner in one pass over its shared family declarations.

        The family directory's declarations, their member kinds and their
        composed member suppliers are the same facts for every sibling domain;
        one resolver over the family and every requested domain reads them
        once and each domain election consumes the same observations.

        Returns:
            Each requested domain with its maximal native owners.

        """
        return cls._family_subfacade_owner_map(
            project,
            directories,
            {
                parent: cls.facade_component_declarations(project, parent)
                for parent in {directory.parent for directory in directories}
            },
        )

    @classmethod
    def _family_subfacade_owner_map(
        cls,
        project: p.Infra.RopeProject,
        directories: Sequence[Path],
        family_declarations: Mapping[
            Path, Sequence[tuple[Path, p.Infra.RopeSourceClass]]
        ],
    ) -> dict[Path, list[tuple[Path, str]]]:
        """Elect domain owners against already-read family declarations.

        Returns:
            Each requested domain with its maximal native owners.

        """
        elected: dict[Path, list[tuple[Path, str]]] = {}
        for parent in sorted({directory.parent for directory in directories}):
            domains = sorted(
                directory for directory in directories if directory.parent == parent
            )
            shared = family_declarations[parent]
            owned = {
                domain: cls.facade_component_declarations(project, domain)
                for domain in domains
            }
            bases_runtime = FlextInfraUtilitiesRopeSourceBasesRuntime
            resolver_factory = bases_runtime.source_member_resolver_factory(
                project,
                sources={
                    FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                        owner.get_module(), source_project=project
                    ): (path, owner.get_module().source_code)
                    for path, owner in (
                        *shared,
                        *(item for items in owned.values() for item in items),
                    )
                },
            )
            observations = (
                cache(
                    partial(
                        FlextInfraUtilitiesFacadeMembers.class_kind,
                        resolver_factory=resolver_factory,
                        source_project=project,
                    )
                ),
                cache(
                    partial(
                        cls._composed_owner_suppliers,
                        resolver_factory=resolver_factory,
                        project=project,
                    )
                ),
            )
            for domain in domains:
                elected[domain] = cls._domain_subfacade_owners(
                    domain, (*shared, *owned[domain]), observations
                )
        return elected

    @classmethod
    def _composed_owner_suppliers(
        cls,
        owner: p.Infra.RopeSourceClass,
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        project: p.Infra.RopeProject,
    ) -> tuple[p.Infra.RopePyObject, ...]:
        """Read the member suppliers of an owner that composes family classes.

        Returns:
            The composed member suppliers, or none for a non-composing owner.

        """
        if not cls.facade_composes_class(owner, source_project=project):
            return ()
        return tuple(
            cls._composed_member_suppliers(
                owner,
                owner.get_module().get_source_binding_index(),
                resolver_factory=resolver_factory,
                project=project,
            )
        )

    @classmethod
    def _domain_subfacade_owners(
        cls,
        directory: Path,
        declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
        observations: tuple[
            Callable[[p.Infra.RopePyObject], c.Infra.FacadeMemberKind],
            Callable[[p.Infra.RopeSourceClass], tuple[p.Infra.RopePyObject, ...]],
        ],
    ) -> list[tuple[Path, str]]:
        """Elect one domain's owners from the shared family observations.

        Returns:
            Maximal native owners at the canonical sibling precedence.

        """
        kind, composed_suppliers = observations
        types = FlextInfraUtilitiesRopeRuntimeTypes
        canonical = directory.parent / f"{directory.name.lstrip('_')}.py"
        elected: list[tuple[Path, p.Infra.RopeSourceClass]] = []
        composed: dict[p.Infra.RopeSourceClass, frozenset[p.Infra.RopePyObject]] = {}
        for path, owner in declarations:
            if kind(owner) is not c.Infra.FacadeMemberKind.TYPE:
                continue
            if path.parent != directory.parent and any(
                types.py_function(scope.pyobject)
                for scope in owner.get_scope().get_scopes()
            ):
                continue
            suppliers = tuple(owner.get_superclasses())
            member_suppliers: tuple[p.Infra.RopePyObject, ...] = ()
            if not any(
                types.py_class(supplier)
                and (resource := supplier.get_module().get_resource()) is not None
                and Path(resource.real_path).parent == directory
                for supplier in suppliers
            ):
                member_suppliers = composed_suppliers(owner)
                suppliers = (*suppliers, *member_suppliers)
            if path == canonical:
                suppliers = (*suppliers, *cls._component_callable_suppliers(owner))
            origins = {
                Path(resource.real_path).parent
                for supplier in suppliers
                if types.py_class(supplier)
                and supplier is not owner
                and (resource := supplier.get_module().get_resource()) is not None
                and kind(supplier) is c.Infra.FacadeMemberKind.TYPE
            }
            if directory in origins and (
                path == canonical
                or len({origin for origin in origins if origin.name.startswith("_")})
                == 1
            ):
                elected.append((path, owner))
                composed[owner] = frozenset(
                    ancestor
                    for supplier in (owner, *member_suppliers)
                    if types.py_class(supplier)
                    for ancestor in supplier.get_mro()
                )
        if not elected:
            return []
        priority = max(
            (path == canonical, path.parent == directory) for path, _ in elected
        )
        return [
            (path, owner.get_name())
            for path, owner in elected
            if (path == canonical, path.parent == directory) == priority
            and not any(
                other is not owner
                and owner in composed[other]
                and other not in composed[owner]
                for other_path, other in elected
                if (other_path == canonical, other_path.parent == directory) == priority
            )
        ]

    @staticmethod
    def _composed_member_suppliers(
        owner: p.Infra.RopeSourceClass,
        index: p.Infra.RopeSourceBindingIndex,
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        project: p.Infra.RopeProject,
    ) -> list[p.Infra.RopePyObject]:
        """Collect class members and nested type bases a composed owner supplies.

        Returns:
            Class-valued assignment targets and nested type-namespace bases.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        member_suppliers: list[p.Infra.RopePyObject] = []
        pending = [owner]
        while pending:
            holder = pending.pop()
            member_suppliers.extend(
                binding.value_binding.get_object()
                for declaration in index.assignment_layouts(holder.get_scope())
                if declaration.targets
                and declaration.targets[0][0] != c.Infra.MODEL_CONFIG_ATTRIBUTE
                for binding in index.assignment_layouts(
                    holder.get_scope(),
                    name=declaration.targets[0][0],
                    resolve_values=True,
                )
                if binding.region == declaration.region
                and binding.value_binding is not None
                and types.py_class(binding.value_binding.get_object())
            )
            for scope in holder.get_scope().get_scopes():
                nested = scope.pyobject
                if (
                    types.py_class(nested)
                    and FlextInfraUtilitiesFacadeMembers.class_kind(
                        nested,
                        resolver_factory=resolver_factory,
                        source_project=project,
                    )
                    is c.Infra.FacadeMemberKind.TYPE
                ):
                    member_suppliers.extend(nested.get_superclasses())
                    pending.append(nested)
        return member_suppliers

    @staticmethod
    def _component_callable_suppliers(
        owner: p.Infra.RopeSourceClass,
    ) -> Generator[p.Infra.RopeSourceClass]:
        """Observe direct method delegation through the existing native index.

        Yields:
            Actual class receivers called in this owner's own method bodies.

        Raises:
            TypeError: If the native word regions are unavailable.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        module = owner.get_module()
        words = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Callable supplier election requires native word regions"
            raise TypeError(message)
        methods = {
            scope.pyobject
            for scope in owner.get_scope().get_scopes()
            if types.py_function(scope.pyobject)
        }
        for fragment in module.get_source_binding_index().fragments:
            context = fragment.context
            if (
                context.role != "function-body"
                or context.structural_scope.pyobject not in methods
            ):
                continue
            if words.get_primary_range(fragment.end - 1) != (
                fragment.start,
                fragment.end,
            ):
                continue
            prefix, _member, offset = words.get_splitted_primary_before(fragment.end)
            if not prefix or not words.is_a_function_being_called(offset):
                continue
            receiver = runtime.expression_name(context.environment, prefix)
            called = runtime.expression_name(
                context.environment, module.source_code[fragment.start : fragment.end]
            )
            if (
                receiver is not None
                and types.py_class(supplier := receiver.get_object())
                and called is not None
                and types.py_function(called.get_object())
            ):
                yield supplier

    @classmethod
    def render_type_facade(
        cls,
        pkg_dir: Path,
        facade_path: Path,
        sources: Mapping[Path, str],
        *,
        project: p.Infra.RopeProject,
    ) -> p.Result[str]:
        """Project the type family through the same native declaration operation.

        Returns:
            Source preserving the full declared type owner's body and identity.

        """
        planned = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path), (), sources, source_project=project
        )
        with project.source_view(
            declared_files=planned, additional_source_folders=None
        ):
            return cls.facade_component_source(
                project,
                facade_path,
                pkg_dir
                / FlextInfraUtilitiesCodegenNamespace.facade_families()["t"].directory,
                family=c.Infra.FacadeFamily.T,
            )

    @classmethod
    def render_utility_facade(
        cls,
        pkg_dir: Path,
        *,
        family: str | c.Infra.FacadeFamily = c.Infra.FacadeFamily.U,
        project: p.Infra.RopeProject | None = None,
        sources: Mapping[Path, str] | None = None,
    ) -> p.Result[str] | None:
        """Project one declared family against its sole authenticated native view.

        Returns:
            Source, or absence when this package has no family declarations.

        """
        if project is None or sources is not None:
            with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
                Path(project.root.real_path) if project is not None else pkg_dir.parent,
                planned_sources=sources,
                source_project=project,
            ) as (captured, _contents):
                return cls.render_utility_facade(
                    pkg_dir, family=family, project=captured
                )
        selected = c.Infra.FacadeFamily(family)
        directory = (
            pkg_dir
            / FlextInfraUtilitiesCodegenNamespace.facade_families()[selected].directory
        )
        if not project.source_query(directory, "isdir"):
            return None
        elected = FlextInfraUtilitiesCodegenNamespace.facade_module_path(
            pkg_dir, selected, project=project
        )
        if elected is None:
            if not cls.facade_component_declarations(project, directory):
                return None
            message = f"Family declarations have no public facade: {directory}"
            return r[str].fail(message)
        if elected.failure:
            return r[str].from_failure(elected)
        return cls.facade_component_source(
            project, elected.value, directory, family=selected
        )

    @classmethod
    def facade_component_source(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        directory: Path,
        *,
        family: c.Infra.FacadeFamily,
        owner_name: str | None = None,
    ) -> p.Result[str]:
        """Compose declared native providers while retaining authored source bodies.

        Native layouts supply every span and lexical environment. Import operations
        and the change collector remain Rope's owners; no source is parsed here.

        Returns:
            The complete unchanged-body source candidate, never a published effect.

        """
        settled = cls._facade_settled_initializers(project, (path, directory))
        if settled.failure:
            return r[str].from_failure(settled)
        resource = FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path)
        planned = cls._facade_component_plan(
            project, path, directory, family=family, owner_name=owner_name
        )
        if planned.failure:
            return r[str].from_failure(planned)
        module, owner, namespace, layout = planned.value[:4]
        composition = (planned.value[4], planned.value[5], planned.value[7])
        step = cls._facade_indent_step(project)
        source = cls._facade_sorted_imports(
            project,
            path,
            resource,
            cls._facade_body_opening(resource, module, namespace, layout, step)
            if composition[1]
            else module.source_code,
            planned.value[6],
        )
        declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path), (), {path: source}, source_project=project
        )
        with project.source_view(
            declared_files=declared, additional_source_folders=None
        ):
            projected = cls._facade_projected_class(
                project, path, resource, owner=owner, namespace=namespace
            )
            if projected.failure:
                return r[str].from_failure(projected)
            rendered = cls._facade_rendered_class(
                projected.value, source, composition, step
            )
        return rendered.flat_map(
            lambda text: cls._facade_rendered_order(
                project, (path, directory), owner, (text, owner_name is not None)
            )
        )

    @staticmethod
    def _facade_settled_initializers(
        project: p.Infra.RopeProject, location: tuple[Path, Path]
    ) -> p.Result[bool]:
        """Refuse a facade whose package or family initializer holds a conflict.

        Returns:
            True, or the first initializer carrying a Git merge-control line.

        """
        path, directory = location
        for initializer in dict.fromkeys((
            path.parent / c.Infra.INIT_PY,
            directory / c.Infra.INIT_PY,
        )):
            if not project.source_query(initializer, "isfile"):
                continue
            marker = FlextInfraUtilitiesBase.first_merge_conflict_marker(
                project.source_text(initializer)
            )
            if marker is not None:
                return r[bool].fail(
                    "Unresolved merge conflict in facade initializer: "
                    f"{initializer}: {marker}"
                )
        return r[bool].ok(value=True)

    @classmethod
    def _facade_rendered_order(
        cls,
        project: p.Infra.RopeProject,
        location: tuple[Path, Path],
        owner: p.Infra.RopeSourceClass,
        rendering: tuple[str, bool],
    ) -> p.Result[str]:
        """Linearize every class of the rendered facade before it is planned.

        The rendered text is proved by the same base owner as the authored
        source (``_facade_class_bases``) over the same candidate view, so a
        composition whose planned C3 order is inconsistent (one provider
        reached through two facade paths) fails here, before any plan can
        publish it.

        A recomposed domain owner (``rendering[1]``) also proves every
        enclosing declaration's ancestry (``_facade_consumer_orders``).

        Returns:
            The rendered text, or the owner's linearization failure.

        """
        path, directory = location
        text, recomposed = rendering
        declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path), (), {path: text}, source_project=project
        )
        with project.source_view(
            declared_files=declared, additional_source_folders=None
        ):
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                project.get_pymodule(
                    FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(
                        project, path
                    )
                )
            )
            rendered = module.get_attributes()[owner.get_name()].get_object()
            if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(rendered):
                return r[str].fail(
                    f"Rendered facade lost its owner class: {path}:{owner.get_name()}"
                )
            ordered = cls._facade_class_bases(
                project,
                (path, directory, module, rendered),
                {
                    FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                        module, source_project=project
                    ): (path, text)
                },
            )
            if ordered.success and recomposed:
                ordered = cls._facade_consumer_orders(project, (path, text), rendered)
        return ordered.map(lambda _orders: text)

    @classmethod
    def _facade_consumer_orders(
        cls,
        project: p.Infra.RopeProject,
        rendered: tuple[Path, str],
        owner: p.Infra.RopeSourceClass,
    ) -> p.Result[tuple[t.StrTuple, ...]]:
        """Prove the recomposed owner keeps every enclosing declaration's C3.

        A recomposed owner gains providers that existing classes of the
        enclosing packages (below the top-level package) may already list
        explicitly, in an order the old
        ancestry permitted. Linearizing every declaration of the owner's
        enclosing packages over the candidate proves the existing ancestry
        still holds; a contradiction refuses the recomposition and names the
        owner, before any plan can publish it.

        Returns:
            The C3 order of every enclosing declaration, or the contradiction.

        """
        path, text = rendered
        discovery = FlextInfraUtilitiesProjectDiscovery
        enclosing: list[Path] = []
        current = path.parent
        while project.source_query(current.parent / c.Infra.INIT_PY, "isfile"):
            enclosing.append(current)
            current = current.parent
        references = tuple(
            (
                m.Infra.SourceClassReference(
                    target=module_name,
                    attributes=(declaration.get_name(),),
                    qualified_base=f"{module_name}.{declaration.get_name()}",
                ),
            )
            for directory in enclosing
            for _origin, declaration in cls.facade_component_declarations(
                project, directory
            )
            if declaration.get_name() != owner.get_name()
            for module_name in (
                discovery.module_name_for_provider(
                    declaration.get_module(), source_project=project
                ),
            )
        )
        ordered = r[tuple[t.StrTuple, ...]].create_from_callable(
            partial(
                FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_orders,
                project,
                {
                    discovery.module_name_for_provider(
                        owner.get_module(), source_project=project
                    ): (path, text)
                },
                references,
            )
        )
        if ordered.failure:
            return r[tuple[t.StrTuple, ...]].fail(
                f"Recomposed owner {owner.get_name()} contradicts an existing "
                f"ancestry: {ordered.error}",
                exception=ordered.exception,
            )
        return ordered

    @classmethod
    def _facade_component_plan(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        directory: Path,
        *,
        family: c.Infra.FacadeFamily,
        owner_name: str | None,
    ) -> p.Result[
        tuple[
            p.Infra.RopeSourceModule,
            p.Infra.RopeSourceClass,
            p.Infra.RopeSourceClass,
            p.Infra.RopeSourceClassLayout,
            list[tuple[str, p.Infra.RopePyObject]],
            dict[str, str],
            list[t.Infra.RopeFromImport],
            frozenset[str],
        ]
    ]:
        """Plan the facade composition against the module's own native epoch.

        Returns:
            The module, owner, namespace layout, retained bases, nominal
            publications, added imports and alias names, or the first failure.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
            project.get_pymodule(runtime.file_resource_at(project, path))
        )
        resolved = cls._facade_namespace_owner(
            project, path, directory, module, owner_name=owner_name
        )
        if resolved.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    dict[str, str],
                    list[t.Infra.RopeFromImport],
                    frozenset[str],
                ]
            ].from_failure(resolved)
        owner, namespace = resolved.value[0], resolved.value[1]
        index = module.get_source_binding_index()
        framed = cls._facade_namespace_bases(module, index, namespace, path)
        if framed.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    dict[str, str],
                    list[t.Infra.RopeFromImport],
                    frozenset[str],
                ]
            ].from_failure(framed)
        layout, bases = framed.value
        aliases, alias_names = cls._facade_namespace_aliases(index, namespace)
        providers = cls._facade_admitted_providers(
            project, resolved.value, family=family, aliases=aliases, bases=bases
        )
        if providers.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    dict[str, str],
                    list[t.Infra.RopeFromImport],
                    frozenset[str],
                ]
            ].from_failure(providers)
        composed = cls._facade_retained_providers(
            module,
            path,
            providers.value[0],
            (
                bases,
                cls._facade_root_precedence(project, directory, family)
                if owner_name is not None
                else (),
            ),
        )
        if composed.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    dict[str, str],
                    list[t.Infra.RopeFromImport],
                    frozenset[str],
                ]
            ].from_failure(composed)
        # A recomposed utility domain owner is itself a utility provider, whose
        # storage admits only ClassVar/Final members
        # (``utility_namespace_declaration``); a ``TypeAlias`` publication there
        # would make its own family root refuse it.
        published = cls._facade_nominal_publications(
            module,
            path,
            namespace,
            ()
            if family is c.Infra.FacadeFamily.U and owner_name is not None
            else providers.value[1],
            (aliases, composed.value[0]),
        )
        if published.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    dict[str, str],
                    list[t.Infra.RopeFromImport],
                    frozenset[str],
                ]
            ].from_failure(published)
        return r[
            tuple[
                p.Infra.RopeSourceModule,
                p.Infra.RopeSourceClass,
                p.Infra.RopeSourceClass,
                p.Infra.RopeSourceClassLayout,
                list[tuple[str, p.Infra.RopePyObject]],
                dict[str, str],
                list[t.Infra.RopeFromImport],
                frozenset[str],
            ]
        ].ok((
            module,
            owner,
            namespace,
            layout,
            composed.value[0],
            published.value,
            cls._facade_planned_imports(
                cls._facade_declaring_packages(project, resolved.value[2]),
                (*composed.value[1], *published.value),
                type_alias=bool(published.value or alias_names),
            ),
            alias_names,
        ))

    @classmethod
    def _facade_namespace_owner(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        directory: Path,
        module: p.Infra.RopeSourceModule,
        *,
        owner_name: str | None,
    ) -> p.Result[
        tuple[
            p.Infra.RopeSourceClass,
            p.Infra.RopeSourceClass,
            tuple[tuple[Path, p.Infra.RopeSourceClass], ...],
            t.Infra.RopeSourceMemberResolverFactory,
        ]
    ]:
        """Elect the published facade owner and its sole inherited namespace.

        Returns:
            The owner, namespace, family declarations and their member resolver.

        """
        published = FlextInfraUtilitiesRopeAnalysisImportState.published_facade_owner(
            project,
            FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path),
        )
        name = (
            owner_name
            if owner_name is not None
            else (published[1] if published is not None else None)
        )
        if name is None or name not in module.get_attributes():
            message = f"Facade has no native published class: {path}"
            return r[
                tuple[
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    tuple[tuple[Path, p.Infra.RopeSourceClass], ...],
                    t.Infra.RopeSourceMemberResolverFactory,
                ]
            ].fail(message)
        owner = module.get_attributes()[name].get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(owner):
            message = f"Facade publication is not a source class: {path}:{name}"
            return r[
                tuple[
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    tuple[tuple[Path, p.Infra.RopeSourceClass], ...],
                    t.Infra.RopeSourceMemberResolverFactory,
                ]
            ].fail(message)
        result_type = r[
            tuple[
                p.Infra.RopeSourceClass,
                p.Infra.RopeSourceClass,
                tuple[tuple[Path, p.Infra.RopeSourceClass], ...],
                t.Infra.RopeSourceMemberResolverFactory,
            ]
        ]
        immediate = cls.facade_component_declarations(project, directory)
        declarations = (
            *immediate,
            *cls.facade_domain_declarations(project, directory, immediate),
        )
        competing = cls._facade_competing_declarations(project, declarations)
        if competing:
            return result_type.fail(
                f"Ambiguous source class binding: {', '.join(competing)}"
            )
        sources = {
            FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                declaration.get_module(), source_project=project
            ): (origin, declaration.get_module().source_code)
            for origin, declaration in ((path, owner), *declarations)
        }
        proven = cls._facade_class_bases(
            project,
            (path, directory, module, owner),
            sources,
        )
        if proven.failure:
            return result_type.from_failure(proven)
        resolver_factory = (
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver_factory(
                project, sources=sources
            )
        )
        namespaces = cls._facade_inherited_namespaces(
            owner, directory, resolver_factory=resolver_factory, project=project
        )
        if len(namespaces) > 1:
            message = f"Competing inherited facade namespaces: {path}"
            return result_type.fail(message)
        return result_type.ok((
            owner,
            namespaces[0] if namespaces else owner,
            declarations,
            resolver_factory,
        ))

    @staticmethod
    def _facade_competing_declarations(
        project: p.Infra.RopeProject,
        declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
    ) -> tuple[str, ...]:
        """Name every declared publisher that shares a public class name.

        Two distinct declarations cannot both bind one facade import name; the
        planning would otherwise compose or publish whichever came last.

        Returns:
            Every ``module:Class`` identity of a shared name, in sorted order.

        """
        identities: dict[str, list[str]] = {}
        for _origin, declaration in declarations:
            module_name = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                declaration.get_module(), source_project=project
            )
            identities.setdefault(declaration.get_name(), []).append(
                f"{module_name}:{declaration.get_name()}"
            )
        return tuple(
            sorted(
                identity
                for named in identities.values()
                if len(named) > 1
                for identity in named
            )
        )

    @classmethod
    def _facade_class_bases(
        cls,
        project: p.Infra.RopeProject,
        facade: tuple[Path, Path, p.Infra.RopeSourceModule, p.Infra.RopeSourceClass],
        sources: Mapping[str, tuple[Path, str]],
    ) -> p.Result[tuple[t.StrTuple, ...]]:
        """Prove every facade class base before any source is rendered.

        A base whose import names no source binding is admitted only when its
        provider is this family's generated barrel (the facade is re-rendered
        from the family declarations in the same generation: a declared name is
        republished, a name no family module declares is a retired domain) or
        when it is an upstream module outside the project. Every other class
        is linearized by the source-bases owner, which rejects unresolved,
        module, ambiguous and inconsistent bases.

        Returns:
            The source C3 order of every proven class, or the first base the
            facade cannot compose.

        """
        path, directory, module, owner = facade
        result_type = r[tuple[t.StrTuple, ...]]
        barrel = directory / c.Infra.INIT_PY
        generated = project.source_query(barrel, "isfile") and project.source_text(
            barrel
        ).startswith(c.Infra.AUTOGEN_HEADER)
        admitted = (
            frozenset({directory.resolve(), barrel.resolve()})
            if generated
            else frozenset(),
            Path(project.root.real_path).resolve(),
        )
        proven: list[tuple[m.Infra.SourceClassReference]] = []
        for reference, holder in cls._facade_class_references(
            FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                module, source_project=project
            ),
            owner,
        ):
            deferred = cls._facade_class_deferred(
                project, (path, module, holder), admitted
            )
            if deferred.failure:
                return result_type.from_failure(deferred)
            if not deferred.value:
                proven.append((reference,))
        return result_type.create_from_callable(
            partial(
                FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_orders,
                project,
                sources,
                tuple(proven),
            )
        )

    @staticmethod
    def _facade_class_deferred(
        project: p.Infra.RopeProject,
        facade: tuple[Path, p.Infra.RopeSourceModule, p.Infra.RopeSourceClass],
        admitted: tuple[frozenset[Path], Path],
    ) -> p.Result[bool]:
        """Classify one facade class by the provenance of its unresolved bases.

        ``admitted`` holds the generated family barrel identities (empty when
        the barrel is authored) and the project root.

        Returns:
            Whether a base awaits its generated barrel republication, or the
            first base whose import names no admissible owner.

        """
        path, module, holder = facade
        family, root = admitted
        types = FlextInfraUtilitiesRopeRuntimeTypes
        deferred = False
        layout = module.get_source_binding_index().class_layout(holder.get_scope())
        for (start, end), binding in layout.base_bindings:
            expression = module.source_code[start:end]
            if binding is None:
                return r[bool].fail(f"Unresolved facade base: {path}:{expression}")
            if not types.imported_name(binding):
                continue
            if binding.get_definition_location()[0] is not None:
                continue
            provider = r[Path].create_from_callable(
                partial(
                    FlextInfraUtilitiesRopeRuntimeModules.imported_module_path,
                    project,
                    binding,
                )
            )
            if provider.failure:
                return r[bool].fail(
                    f"Unresolved facade base: {path}:{expression}: {provider.error}",
                    exception=provider.exception,
                )
            if provider.value in family:
                deferred = True
            elif provider.value.is_relative_to(root):
                return r[bool].fail(f"Unresolved facade base: {path}:{expression}")
        return r[bool].ok(value=deferred)

    @staticmethod
    def _facade_class_references(
        module_name: str,
        owner: p.Infra.RopeSourceClass,
    ) -> Generator[tuple[m.Infra.SourceClassReference, p.Infra.RopeSourceClass]]:
        """Address the facade owner and every nested class by its declared path.

        Yields:
            One source class reference per declared facade class, with the class.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        pending: list[tuple[tuple[str, ...], p.Infra.RopeSourceClass]] = [
            ((owner.get_name(),), owner)
        ]
        while pending:
            attributes, holder = pending.pop()
            yield (
                m.Infra.SourceClassReference(
                    target=module_name,
                    attributes=attributes,
                    qualified_base=".".join((module_name, *attributes)),
                ),
                holder,
            )
            pending.extend(
                ((*attributes, scope.pyobject.get_name()), scope.pyobject)
                for scope in holder.get_scope().get_scopes()
                if types.py_class(scope.pyobject)
            )

    @staticmethod
    def _facade_inherited_namespaces(
        owner: p.Infra.RopeSourceClass,
        directory: Path,
        *,
        resolver_factory: t.Infra.RopeSourceMemberResolverFactory,
        project: p.Infra.RopeProject,
    ) -> tuple[p.Infra.RopeSourceClass, ...]:
        """Select nested type namespaces inherited from the owner or the family.

        Returns:
            Every nested type class bound by an abstract parent attribute or a
            family-directory base, in declaration order.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        nested = tuple(
            scope.pyobject
            for scope in owner.get_scope().get_scopes()
            if types.py_class(scope.pyobject)
        )
        return tuple(
            child
            for child in nested
            if FlextInfraUtilitiesFacadeMembers.class_kind(
                child, resolver_factory=resolver_factory, source_project=project
            )
            is c.Infra.FacadeMemberKind.TYPE
            and (
                any(
                    child.get_name() in parent.get_attributes()
                    and types.abstract_class(
                        parent.get_attributes()[child.get_name()].get_object()
                    )
                    for parent in owner.get_superclasses()
                )
                or any(
                    types.py_class(base)
                    and (base_resource := base.get_module().get_resource()) is not None
                    and Path(base_resource.real_path).is_relative_to(directory)
                    for base in child.get_superclasses()
                )
            )
        )

    @staticmethod
    def _facade_namespace_bases(
        module: p.Infra.RopeSourceModule,
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
        path: Path,
    ) -> p.Result[
        tuple[
            p.Infra.RopeSourceClassLayout,
            list[tuple[str, p.Infra.RopePyObject]],
        ]
    ]:
        """Resolve every authored namespace base and binding through Rope.

        Returns:
            The namespace class layout with its base expressions and identities,
            or the first base or namespace binding the facade cannot publish.

        """
        layout = index.class_layout(namespace.get_scope())
        source = module.source_code
        bases: list[tuple[str, p.Infra.RopePyObject]] = []
        for (start, end), binding in layout.base_bindings:
            if binding is None:
                message = f"Unresolved facade base: {path}:{source[start:end]}"
                return r[
                    tuple[
                        p.Infra.RopeSourceClassLayout,
                        list[tuple[str, p.Infra.RopePyObject]],
                    ]
                ].fail(message)
            bases.append((source[start:end], binding.get_object()))
        return FlextInfraUtilitiesFacadeComponents._facade_namespace_bindings(
            module, index, namespace, path
        ).map(lambda _bound: (layout, bases))

    @staticmethod
    def _facade_resolved_assignments(
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
    ) -> tuple[p.Infra.RopeSourceAssignmentLayout, ...]:
        """Resolve every namespace assignment except the authored model metadata.

        Returns:
            Each direct assignment with its native value and root bindings.

        """
        return tuple(
            assignment
            for declaration in index.assignment_layouts(namespace.get_scope())
            if declaration.targets
            and declaration.targets[0][0] != c.Infra.MODEL_CONFIG_ATTRIBUTE
            for assignment in index.assignment_layouts(
                namespace.get_scope(),
                name=declaration.targets[0][0],
                resolve_values=True,
            )
            if assignment.region == declaration.region
        )

    @classmethod
    def _facade_namespace_bindings(
        cls,
        module: p.Infra.RopeSourceModule,
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
        path: Path,
    ) -> p.Result[bool]:
        """Prove every namespace binding is single, resolved and class-valued.

        A name bound twice is ambiguous; a bare dotted-name value that does not
        resolve names its missing binding; an attribute read off a class that is
        not itself a class (``Owner.value``) is no class publication. Authored
        model metadata (``model_config``) stays outside this proof.

        Returns:
            True, or the first binding the facade cannot publish.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        source = module.source_code
        identity = f"{path}:{namespace.get_name()}"
        targets: dict[str, int] = {}
        for assignment in cls._facade_resolved_assignments(index, namespace):
            if assignment.kind == "AugAssign":
                continue
            for target, _region in assignment.targets:
                targets[target] = targets.get(target, 0) + 1
                if targets[target] > 1:
                    return r[bool].fail(
                        f"Ambiguous source class binding: {identity}.{target}"
                    )
            if assignment.kind != "Assign" or assignment.value is None:
                continue
            first, last = assignment.value
            value = source[first:last]
            if not all(part.isidentifier() for part in value.split(".")):
                continue
            names = ", ".join(target for target, _region in assignment.targets)
            if assignment.root_binding is None or assignment.value_binding is None:
                return r[bool].fail(
                    f"Unresolved facade binding: {identity}.{names} = {value}"
                )
            if (
                "." in value
                and value.rsplit(".", 1)[1] != c.Infra.MODEL_CONFIG_ATTRIBUTE
                and types.abstract_class(assignment.root_binding.get_object())
                and not types.abstract_class(assignment.value_binding.get_object())
            ):
                return r[bool].fail(f"Non-class binding: {identity}.{names} = {value}")
        return r[bool].ok(value=True)

    @classmethod
    def _facade_namespace_aliases(
        cls,
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
    ) -> tuple[dict[str, p.Infra.RopePyObject], frozenset[str]]:
        """Read the namespace's resolved assignments once for both alias views.

        Returns:
            Every bound target identity and the single-target class alias names.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        assignments = cls._facade_resolved_assignments(index, namespace)
        aliases = {
            target_name: assignment.value_binding.get_object()
            for assignment in assignments
            if assignment.value_binding is not None
            for target_name, _region in assignment.targets
        }
        # Only a bare ``Name = Owner`` binding is projected to the PEP 613
        # alias; an authored annotation or a native ``type`` statement is the
        # declared contract and is retained verbatim.
        alias_names = frozenset(
            assignment.targets[0][0]
            for assignment in assignments
            if assignment.kind == "Assign"
            and assignment.value_binding is not None
            and types.abstract_class(assignment.value_binding.get_object())
            and assignment.value is not None
            and len(assignment.targets) == 1
            and not assignment.type_parameters
        )
        return aliases, alias_names

    @classmethod
    def _facade_admitted_providers(
        cls,
        project: p.Infra.RopeProject,
        elected: tuple[
            p.Infra.RopeSourceClass,
            p.Infra.RopeSourceClass,
            tuple[tuple[Path, p.Infra.RopeSourceClass], ...],
            t.Infra.RopeSourceMemberResolverFactory,
        ],
        *,
        family: c.Infra.FacadeFamily,
        aliases: Mapping[str, p.Infra.RopePyObject],
        bases: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> p.Result[
        tuple[
            list[tuple[Path, p.Infra.RopeSourceClass]],
            list[p.Infra.RopeSourceClass],
        ]
    ]:
        """Partition the elected family declarations into composed and nominal.

        Returns:
            Admitted composition providers and nominal publications, or the
            first utility provider without a resolved namespace storage role.

        """
        _owner, namespace, declarations, resolver_factory = elected
        payload = FlextInfraUtilitiesDeclarationPayload
        admitted: list[tuple[Path, p.Infra.RopeSourceClass]] = []
        nominal: list[p.Infra.RopeSourceClass] = []
        for provider_path, provider in declarations:
            # A declaration that already descends from the namespace extends
            # it; composing it back would make the namespace its own ancestor.
            if provider is namespace or namespace in provider.get_mro()[1:]:
                continue
            if (
                FlextInfraUtilitiesFacadeMembers.class_kind(
                    provider, resolver_factory=resolver_factory, source_project=project
                )
                is not c.Infra.FacadeMemberKind.TYPE
            ):
                nominal.append(provider)
                continue
            # A provider a namespace alias already publishes is never also
            # composed: the alias is its publication (``Base = Owner``).
            if family is not c.Infra.FacadeFamily.U and provider in aliases.values():
                continue
            if family is c.Infra.FacadeFamily.U:
                if cls._utility_provider_nominal(provider, bases):
                    nominal.append(provider)
                    continue
                if not payload.utility_namespace_declaration(project, provider):
                    message = (
                        "Utility provider has an unresolved namespace storage role: "
                        f"{provider_path}:{provider.get_name()}"
                    )
                    return r[
                        tuple[
                            list[tuple[Path, p.Infra.RopeSourceClass]],
                            list[p.Infra.RopeSourceClass],
                        ]
                    ].fail(message)
            admitted.append((provider_path, provider))
        return r[
            tuple[
                list[tuple[Path, p.Infra.RopeSourceClass]],
                list[p.Infra.RopeSourceClass],
            ]
        ].ok((admitted, nominal))

    @staticmethod
    def _utility_provider_nominal(
        provider: p.Infra.RopeSourceClass,
        bases: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> bool:
        """Whether a utility provider publishes nominally instead of composing.

        Returns:
            True for instance behavior, inherited instance callables absent from
            the facade bases, or a provider without meaningful class callables.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        methods = tuple(
            scope.pyobject
            for scope in provider.get_scope().get_scopes()
            if types.py_function(scope.pyobject)
        )
        if any(
            method.get_kind() not in {"classmethod", "staticmethod"}
            for method in methods
        ):
            return True
        inherited_instance = any(
            types.py_function(value := attribute.get_object())
            and value.get_kind() not in {"classmethod", "staticmethod"}
            and not any(
                (existing := base.get_attributes().get(name)) is not None
                and existing.get_object() is value
                for _expression, base in bases
            )
            for name, attribute in provider.get_attributes().items()
        )
        meaningful = bool(methods) or (
            bool(provider.get_superclasses())
            and any(
                types.py_function(attribute.get_object())
                for attribute in provider.get_attributes().values()
            )
        )
        return inherited_instance or not meaningful

    @classmethod
    def _facade_retained_providers(
        cls,
        module: p.Infra.RopeSourceModule,
        path: Path,
        admitted: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
        framing: tuple[Sequence[tuple[str, p.Infra.RopePyObject]], tuple[str, ...]],
    ) -> p.Result[tuple[list[tuple[str, p.Infra.RopePyObject]], tuple[str, ...]]]:
        """Retain uncovered bases and append each maximal admitted provider.

        ``framing`` holds the authored bases and, for a recomposed domain owner,
        the base precedence its family root facade already declares: bases that
        facade names keep its order ahead of the rest, so the stale root stays
        linearizable until it is re-rendered in the same pass.

        Returns:
            The retained base expressions and the provider bindings to import, or
            the first module binding occupied by a different class.

        """
        maximal = tuple(
            (provider_path, provider)
            for provider_path, provider in admitted
            if not any(
                other is not provider and provider in other.get_mro()[1:]
                for _, other in admitted
            )
        )
        bases, precedence = framing
        retained = [
            (expression, base)
            for expression, base in bases
            if not any(base in provider.get_mro()[1:] for _, provider in maximal)
        ]
        bindings: list[str] = []
        for _provider_path, provider in maximal:
            if any(base is provider for _expression, base in retained):
                continue
            binding = provider.get_name()
            occupied = module.get_scope().get_names().get(binding)
            if occupied is not None and not cls._same_facade_target(
                occupied.get_object(), provider
            ):
                message = f"Occupied facade provider binding: {path}:{binding}"
                return r[
                    tuple[list[tuple[str, p.Infra.RopePyObject]], tuple[str, ...]]
                ].fail(message)
            bindings.append(binding)
            retained.append((binding, provider))
        retained.sort(
            key=lambda item: (
                precedence.index(item[1].get_name())
                if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(item[1])
                and item[1].get_name() in precedence
                else len(precedence)
            )
        )
        return r[tuple[list[tuple[str, p.Infra.RopePyObject]], tuple[str, ...]]].ok((
            retained,
            tuple(bindings),
        ))

    @classmethod
    def _facade_root_precedence(
        cls,
        project: p.Infra.RopeProject,
        directory: Path,
        family: c.Infra.FacadeFamily,
    ) -> tuple[str, ...]:
        """Read the base precedence the family root facade already declares.

        Returns:
            Every base class name of the root facade's classes, in declared
            order, or none when the domain has no published family root.

        """
        family_directory = FlextInfraUtilitiesCodegenNamespace.facade_families()[
            family
        ].directory
        package = next(
            (
                ancestor
                for ancestor in directory.parents
                if directory.is_relative_to(ancestor / family_directory)
                and ancestor / family_directory != directory
            ),
            None,
        )
        elected = (
            None
            if package is None
            else FlextInfraUtilitiesCodegenNamespace.facade_module_path(
                package, family, project=project
            )
        )
        if elected is None or elected.failure:
            return ()
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
            project.get_pymodule(
                FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(
                    project, elected.value
                )
            )
        )
        types = FlextInfraUtilitiesRopeRuntimeTypes
        index = module.get_source_binding_index()
        names: dict[str, None] = {}
        pending = [
            scope
            for scope in module.get_scope().get_scopes()
            if types.py_class(scope.pyobject)
        ]
        while pending:
            scope = pending.pop(0)
            for _region, binding in index.class_layout(scope).base_bindings:
                if binding is not None and types.abstract_class(binding.get_object()):
                    names.setdefault(binding.get_object().get_name())
            pending.extend(
                child for child in scope.get_scopes() if types.py_class(child.pyobject)
            )
        return tuple(names)

    @classmethod
    def _facade_nominal_publications(
        cls,
        module: p.Infra.RopeSourceModule,
        path: Path,
        namespace: p.Infra.RopeSourceClass,
        nominal: Sequence[p.Infra.RopeSourceClass],
        bound: tuple[
            Mapping[str, p.Infra.RopePyObject],
            Sequence[tuple[str, p.Infra.RopePyObject]],
        ],
    ) -> p.Result[dict[str, str]]:
        """Publish nominal providers that no alias or retained base already binds.

        A provider the namespace already composes as a base is published by
        that base; a second ``Name: TypeAlias = Name`` would only repeat it.

        Returns:
            The nominal publication names in declaration order, or the first
            namespace definition or module import occupying that name.

        """
        aliases, retained = bound
        publications: dict[str, str] = {}
        for provider in nominal:
            if provider in aliases.values() or any(
                base is provider for _expression, base in retained
            ):
                continue
            published_name = provider.get_name()
            if published_name in namespace.get_scope().get_defined_names():
                return r[dict[str, str]].fail(
                    f"Occupied nominal facade publication: {path}:{published_name}"
                )
            imported = module.get_scope().get_names().get(published_name)
            if imported is not None and not cls._same_facade_target(
                imported.get_object(), provider
            ):
                return r[dict[str, str]].fail(
                    f"Occupied nominal facade import: {path}:{published_name}"
                )
            publications[published_name] = published_name
        return r[dict[str, str]].ok(publications)

    @staticmethod
    def _facade_declaring_packages(
        project: p.Infra.RopeProject,
        declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
    ) -> dict[str, str]:
        """Map every family declaration to the import package that declares it.

        Returns:
            Each declaration name with its declaring package.

        """
        return {
            declaration.get_name(): (
                FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
                    origin.parent,
                    project_root=Path(project.root.real_path),
                    source_project=project,
                )
            )
            for origin, declaration in declarations
        }

    @staticmethod
    def _facade_planned_imports(
        packages: Mapping[str, str],
        bindings: Sequence[str],
        *,
        type_alias: bool,
    ) -> list[t.Infra.RopeFromImport]:
        """Build the imports this planning adds on top of the module's own epoch.

        The rewritten text replay adds only this delta, never the module's
        original statements (a cross-epoch replay glues the class header).
        Each binding imports from the package that declares it: the family
        package for an immediate declaration, its domain package otherwise.

        Returns:
            One declaring-package import per binding, then ``TypeAlias`` if
            needed.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        added_imports = [
            runtime.from_import(packages[binding], 0, ((binding, None),))
            for binding in bindings
        ]
        if type_alias:
            added_imports.append(
                runtime.from_import("typing", 0, (("TypeAlias", None),))
            )
        return added_imports

    @staticmethod
    def _facade_indent_step(project: p.Infra.RopeProject) -> int:
        """Read the project's native indentation width.

        Returns:
            The strictly validated ``get_indent`` width.

        """
        return u.type_adapter(int).validate_python(
            FlextInfraUtilitiesRopeRuntimeModules.runtime_callable(
                "rope.refactor.sourceutils", "get_indent"
            )(project),
            strict=True,
        )

    @staticmethod
    def _facade_body_opening(
        resource: p.Infra.RopeFile,
        module: p.Infra.RopeSourceModule,
        namespace: p.Infra.RopeSourceClass,
        layout: p.Infra.RopeSourceClassLayout,
        step: int,
    ) -> str:
        """Open an inline namespace body before nominal publications are rendered.

        Returns:
            The module source, with an inline body moved to its own line.

        """
        source = module.source_code
        body_line = module.lines.get_line_number(layout.body[0])
        body_prefix = source[module.lines.get_line_start(body_line) : layout.body[0]]
        if not body_prefix.strip():
            return source
        class_line = namespace.get_scope().get_start()
        indentation = source[module.lines.get_line_start(class_line) : layout.region[0]]
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            (
                m.Infra.SourceRewrite(
                    start=layout.body[0],
                    end=layout.body[0],
                    text="\n" + indentation + " " * step,
                ),
            ),
        ).new_contents

    @staticmethod
    def _facade_sorted_imports(
        project: p.Infra.RopeProject,
        path: Path,
        resource: p.Infra.RopeFile,
        source: str,
        added_imports: Sequence[t.Infra.RopeFromImport],
    ) -> str:
        """Replay only the planned import delta through Rope's import owner.

        Returns:
            The source with the added imports deduplicated and sorted natively.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        planned = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path), (), {path: source}, source_project=project
        )
        with project.source_view(
            declared_files=planned, additional_source_folders=None
        ):
            current = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                project.get_pymodule(resource)
            )
            native_imports = runtime.module_imports_for_pymodule(project, current)
            for import_info in added_imports:
                native_imports.add_import(import_info)
            native_imports.remove_duplicates()
            native_imports.sort_imports()
            return native_imports.get_changed_source()

    @classmethod
    def _facade_projected_class(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        resource: p.Infra.RopeFile,
        *,
        owner: p.Infra.RopeSourceClass,
        namespace: p.Infra.RopeSourceClass,
    ) -> p.Result[tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass]]:
        """Re-resolve the owner and namespace inside the active projected view.

        Returns:
            The projected module and its namespace class, or the lost declaration.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        current = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
            project.get_pymodule(resource)
        )
        attributes = current.get_attributes()
        if owner.get_name() not in attributes:
            # Owner must be re-electable inside the declared candidate view.
            # The former disk fallback parsed another epoch of the same path
            # and fed its offsets to slices of the composed text — the
            # interleaved-corruption class. Losing the owner here rejects the
            # cohort for re-planning instead.
            return r[tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass]].fail(
                f"Projected facade lost its native declaration: {path}"
                f" (owner {owner.get_name()!r} absent from the candidate view;"
                f" view exports {sorted(attributes)[:6]})"
            )
        actual = attributes[owner.get_name()].get_object()
        if not types.py_class(actual):
            return r[tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass]].fail(
                f"Projected facade lost its native declaration: {path}"
                f" (owner {owner.get_name()!r} is"
                f" {type(actual).__name__}, not a class)"
            )
        if namespace is not owner:
            actual = actual.get_attributes()[namespace.get_name()].get_object()
            if not types.py_class(actual):
                return r[tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass]].fail(
                    f"Projected namespace lost its native declaration: {path}"
                )
        return r[tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass]].ok((
            current,
            actual,
        ))

    @classmethod
    def _facade_rendered_class(
        cls,
        projected: tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass],
        source: str,
        composition: tuple[
            Sequence[tuple[str, p.Infra.RopePyObject]],
            dict[str, str],
            frozenset[str],
        ],
        step: int,
    ) -> p.Result[str]:
        """Fill the module skeleton from the projected namespace layout.

        Returns:
            Rendered source or the template owner's original typed failure.

        """
        current, actual = projected
        retained, publications, alias_names = composition
        scope = actual.get_scope()
        # Epoch guard: the layout, lines and every offset below are read from
        # `current`'s frozen parse; the slices below index `source`. Different
        # texts here produced interleaved corruption (epoch mismatch of the
        # same path) — fail the cohort instead of rendering it.
        if current.source_code != source:
            resource = current.get_module().get_resource()
            return r[str].fail(
                "facade layout epoch mismatch: layout text and composed text"
                f" differ for {resource.path if resource else '<virtual>'}"
            )
        layout = current.get_source_binding_index().class_layout(scope)
        end = current.lines.get_line_end(
            current.lines.get_line_number(layout.region[1])
        )
        body_source = cls._facade_body_source(
            (current, actual), source, (layout, end), (alias_names, step)
        )
        class_line = scope.get_start()
        desired_bases = tuple(expression for expression, _base in retained)
        unchanged_header = desired_bases == tuple(
            source[first:last] for first, last in layout.bases
        )
        context = m.Infra.ModuleSkeletonRenderContext(
            class_name=actual.get_name(),
            base_class=None,
            base_module=None,
            module_prefix=source[: layout.region[0]],
            module_suffix=source[end:],
            class_bases=desired_bases,
            class_keywords=tuple(source[first:last] for first, last in layout.keywords),
            type_parameters_source=source[
                layout.name_region[1] : layout.bases_insertion_offset
            ],
            header_source=source[layout.region[0] : layout.header_end]
            if unchanged_header
            else None,
            header_comments=()
            if unchanged_header
            else cls._facade_header_comments(source, layout, desired_bases),
            class_indent=source[
                current.lines.get_line_start(class_line) : layout.region[0]
            ],
            indentation=" " * step,
            body_source=body_source,
            publications=publications,
            managed_header=None
            if source.startswith(c.Infra.AUTOGEN_HEADER)
            else c.Infra.AUTOGEN_HEADER,
        )
        return cls.generate_module_skeleton(context=context)

    @classmethod
    def _facade_body_source(
        cls,
        projected: tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass],
        source: str,
        frame: tuple[p.Infra.RopeSourceClassLayout, int],
        rendering: tuple[frozenset[str], int],
    ) -> tuple[str | tuple[str, str], ...]:
        """Split the namespace body, retiring obsolete generated bindings.

        A managed body whose every statement retired keeps a ``pass`` so the
        namespace stays a valid class body.

        Returns:
            Verbatim body text interleaved with ``(alias, value source)`` pairs.

        """
        current, actual = projected
        layout, end = frame
        alias_names, step = rendering
        scope = actual.get_scope()
        index = current.get_source_binding_index()
        retired = (
            cls._facade_retired_bindings(index, actual, source)
            if source.startswith(c.Infra.AUTOGEN_HEADER)
            else frozenset()
        )
        body_source = cls._facade_alias_body_parts(
            index, scope, source, (layout.header_end, end), (alias_names, retired)
        )
        if (
            retired
            and not "".join(
                part for part in body_source if isinstance(part, str)
            ).strip()
        ):
            class_indent = source[
                current.lines.get_line_start(scope.get_start()) : layout.region[0]
            ]
            return (f"\n{class_indent}{' ' * step}pass",)
        return body_source

    @classmethod
    def _facade_retired_bindings(
        cls,
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
        source: str,
    ) -> frozenset[tuple[int, int]]:
        """Find generated bindings their inherited owner no longer publishes.

        Only a managed (generated) facade body is projection: a binding that
        reads a member off an inherited owner (``Name = Owner.Member``) under
        a name the owner does not publish as that same class is obsolete
        residue of an earlier generation. An authored body stays verbatim.

        Returns:
            The statement regions of every obsolete generated binding.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        inherited = {
            ancestor
            for base in namespace.get_superclasses()
            if types.abstract_class(base)
            for ancestor in base.get_mro()
        }
        retired: set[tuple[int, int]] = set()
        for assignment in cls._facade_resolved_assignments(index, namespace):
            if (
                assignment.root_binding is None
                or assignment.value_binding is None
                or not cls._facade_attribute_binding(assignment, source)
            ):
                continue
            owner = assignment.root_binding.get_object()
            if owner not in inherited:
                continue
            published = owner.get_attributes().get(assignment.targets[0][0])
            if (
                published is None
                or published.get_object() is not assignment.value_binding.get_object()
            ):
                retired.add(assignment.region)
        return frozenset(retired)

    @staticmethod
    def _facade_attribute_binding(
        assignment: p.Infra.RopeSourceAssignmentLayout, source: str
    ) -> bool:
        """Whether one assignment binds a single name to an attribute read.

        Returns:
            Whether the statement is ``Name = Owner.Member`` (annotated or not).

        """
        return (
            assignment.kind in {"Assign", "AnnAssign"}
            and assignment.value is not None
            and len(assignment.targets) == 1
            and "." in source[assignment.value[0] : assignment.value[1]]
        )

    @staticmethod
    def _facade_alias_body_parts(
        index: p.Infra.RopeSourceBindingIndex,
        scope: p.Infra.RopeScope,
        source: str,
        span: tuple[int, int],
        bindings: tuple[frozenset[str], frozenset[tuple[int, int]]],
    ) -> tuple[str | tuple[str, str], ...]:
        """Split the authored body span around every class alias assignment value.

        A retired generated binding leaves the body with its whole line.

        Returns:
            Verbatim body text interleaved with ``(alias, value source)`` pairs.

        """
        alias_names, retired = bindings
        cursor, end = span
        parts: list[str | tuple[str, str]] = []
        for declaration in index.assignment_layouts(scope):
            if declaration.region in retired:
                line_start = source.rfind("\n", 0, declaration.region[0]) + 1
                line_end = source.find("\n", declaration.region[1])
                parts.append(source[cursor:line_start])
                cursor = len(source) if line_end < 0 else line_end + 1
                continue
            if (
                len(declaration.targets) != 1
                or declaration.targets[0][0] not in alias_names
                or declaration.value is None
            ):
                continue
            parts.append(source[cursor : declaration.region[0]])
            first, last = declaration.value
            parts.append((declaration.targets[0][0], source[first:last]))
            cursor = declaration.region[1]
        parts.append(source[cursor:end])
        return tuple(parts)

    @staticmethod
    def _facade_header_comments(
        source: str,
        layout: p.Infra.RopeSourceClassLayout,
        desired_bases: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Keep header comments outside every base or keyword that survives.

        Returns:
            Comments from the rewritten argument list, or none without arguments.

        """
        if layout.arguments_region is None:
            return ()
        beginning, ending = layout.arguments_region
        arguments = source[beginning:ending]
        preserved = (
            *(
                (first, last)
                for first, last in layout.bases
                if source[first:last] in desired_bases
            ),
            *layout.keywords,
        )
        ignored = FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(arguments)
        return tuple(
            arguments[first:last]
            for first, last, _metadata in ignored
            if arguments[first] == "#"
            and not any(
                start <= beginning + first and beginning + last <= stop
                for start, stop in preserved
            )
        )

    @classmethod
    def facade_component_retirements(
        cls,
        project: p.Infra.RopeProject,
        paths: Sequence[Path],
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Retire composed callable aliases after their real consumer closure.

        A published alias that remains consumed or changes callable identity
        escapes as the ``ValueError`` its validating owner raises.

        Returns:
            Exact native assignment edits with their original physical witnesses.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        publications: dict[
            tuple[p.Infra.RopeClassObject, str], p.Infra.RopeClassObject
        ] = {}
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for path in paths:
            # A module the candidate retires (a moved owner's old path) holds no
            # published alias left to retire.
            if not project.source_query(path, "isfile"):
                continue
            try:
                module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                    project.get_pymodule(runtime.file_resource_at(project, path))
                )
            except rope.base.exceptions.ModuleSyntaxError:
                # Conteúdo candidate inválido no overlay (staging do
                # quoted-move): falha por arquivo — o rerun replaneja este
                # path quando o staging assentar.
                continue
            if not module.source_code.startswith(c.Infra.AUTOGEN_HEADER):
                continue
            retired = tuple(cls._composed_alias_retirements(project, path, module))
            publications.update((key, target) for key, target, _rewrite in retired)
            if retired:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=module.source_code,
                        updated_source=FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                            runtime.file_resource_at(project, path),
                            module.source_code,
                            [rewrite for _key, _target, rewrite in retired],
                        ).new_contents,
                    )
                )
        cls.assert_provider_publications_closed(project, publications)
        declared = {plan.path: plan for plan in declared_files}
        return tuple(
            FlextInfraUtilitiesCodegenFilePlan.source_file_plan_from_edit(
                Path(project.root.real_path),
                edit,
                source_project=project,
                declared_files=declared,
            )
            for edit in edits
        )

    @classmethod
    def _composed_alias_retirements(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        module: p.Infra.RopeSourceModule,
    ) -> Generator[
        tuple[
            tuple[p.Infra.RopeClassObject, str],
            p.Infra.RopeClassObject,
            m.Infra.SourceRewrite,
        ]
    ]:
        """Walk every class scope for assignments aliasing a composed ancestor.

        Yields:
            The publication key, its composed target and the assignment removal.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        index = module.get_source_binding_index()
        for owner_scope in module.get_scope().get_scopes():
            for scope in (owner_scope, *owner_scope.get_scopes()):
                owner = scope.pyobject
                if not types.py_class(owner):
                    continue
                ancestry = owner.get_mro()
                for declaration in index.assignment_layouts(scope):
                    if not declaration.targets:
                        continue
                    (assignment,) = tuple(
                        assignment
                        for assignment in index.assignment_layouts(
                            scope,
                            name=declaration.targets[0][0],
                            resolve_values=True,
                        )
                        if assignment.region == declaration.region
                    )
                    target = cls._composed_alias_target(
                        project, path, owner, ancestry, assignment
                    )
                    if target is None:
                        continue
                    yield (
                        (owner, assignment.targets[0][0]),
                        target,
                        m.Infra.SourceRewrite(
                            start=assignment.region[0],
                            end=assignment.region[1],
                            text="",
                        ),
                    )

    @staticmethod
    def _composed_alias_target(
        project: p.Infra.RopeProject,
        path: Path,
        owner: p.Infra.RopeSourceClass,
        ancestry: Sequence[p.Infra.RopePyObject],
        assignment: p.Infra.RopeSourceAssignmentLayout,
    ) -> p.Infra.RopeSourceClass | None:
        """Prove one single-target assignment aliases a composed behavior provider.

        Returns:
            The aliased ancestor provider, or none for any other assignment.

        Raises:
            ValueError: A published alias changes callable identity.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        binding = assignment.value_binding
        if binding is None or len(assignment.targets) != 1:
            return None
        target = binding.get_object()
        if not types.py_class(target) or target not in ancestry[1:]:
            return None
        if not FlextInfraUtilitiesDeclarationPayload.utility_behavior_provider(
            project, target
        ):
            return None
        for name, member in target.get_attributes().items():
            if name.startswith("_") or not types.py_function(member.get_object()):
                continue
            effective = owner.get_attributes().get(name)
            if effective is None or effective.get_object() is not member.get_object():
                message = f"Composed callable identity differs: {path}:{name}"
                raise ValueError(message)
        return target

    @classmethod
    def facade_composes_class(
        cls,
        owner: p.Infra.RopeSourceClass,
        *,
        source_project: p.Infra.RopeProject,
    ) -> bool:
        """Authenticate a holder through its published family's native ancestry.

        The family catalog locates the publisher, never elects a class name.
        Ordinary type publications outside that exact ancestry remain types.

        Returns:
            Whether an existing public namespace composes this native class.

        """
        resource = owner.get_module().get_resource()
        if resource is None:
            return False
        root = Path(source_project.root.real_path)
        for directory in Path(resource.real_path).parents:
            if not directory.is_relative_to(root):
                break
            for (
                family
            ) in FlextInfraUtilitiesCodegenNamespace.facade_families().values():
                if directory.name != family.directory:
                    continue
                publisher = source_project.get_pymodule(
                    source_project.get_folder(
                        directory.parent.relative_to(root).as_posix()
                    )
                )
                package = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    publisher, source_project=source_project
                )
                if any(
                    owner is holder or owner in cls._component_ancestors(holder)
                    for holder, _target in cls._facade_namespace_holders(
                        package, (family.letter,), source_project=source_project
                    )
                ):
                    return True
        return False

    @classmethod
    def plan_component_consumers(
        cls,
        root: Path,
        *,
        source_project: p.Infra.RopeProject,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Close native callable receiver rewrites over the composed candidate.

        The existing claims and lexical-call proof elect every replacement.
        Original physical witnesses and previous move declarations remain owned
        by the shared semantic-edit planner; no source is published here.

        Returns:
            Consumer plans with their original CAS and ownership witnesses.

        """
        claims = cls._component_claims(root, source_project=source_project)
        if not claims:
            return ()
        declared = {plan.path: plan for plan in declared_files}
        plans: list[m.Infra.CodegenFilePlan] = []
        module_syntax_error = FlextInfraUtilitiesRopeRuntime.exception_type(
            "rope.base.exceptions", "ModuleSyntaxError"
        )
        for resource in source_project.get_python_files():
            path = Path(resource.real_path)
            try:
                module = cls._consumer_module(source_project, path)
                calls = cls._component_calls(module, claims)
            except module_syntax_error:
                # A projected consumer with invalid syntax (a render bug owned
                # by its own stage) cannot be a valid consumer candidate; the
                # syntax defect surfaces at its owner's validation, not here.
                continue
            if not calls:
                continue
            source = module.source_code
            rewrites = tuple(rewrite for rewrite, _original, _destination in calls)
            updated = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                resource,
                source,
                rewrites,
            ).new_contents
            if updated != source:
                plans.append(
                    FlextInfraUtilitiesCodegenFilePlan.source_file_plan_from_edit(
                        root,
                        m.Infra.SemanticMigrationEdit(
                            file_path=path,
                            original_source=source,
                            updated_source=updated,
                        ),
                        source_project=source_project,
                        declared_files=declared,
                    )
                )
        return tuple(plans)

    @classmethod
    def assert_provider_publications_closed(
        cls,
        source_project: p.Infra.RopeProject,
        publications: Mapping[
            tuple[p.Infra.RopeClassObject, str], p.Infra.RopeClassObject
        ],
    ) -> None:
        """Reject surviving references before a composed provider loses its alias.

        This observes all native contexts, including the load of a publication
        inside an assignment, deletion or augmented-assignment mutation target.
        It never rewrites those targets or elects another mutation owner.

        Raises:
            ValueError: A candidate still consumes a retiring provider publication.
            TypeError: A native consumer does not provide a module declaration.

        """
        if not publications:
            return
        names = {name for _owner, name in publications}
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for resource in source_project.get_python_files():
            module = cls._consumer_module(source_project, Path(resource.real_path))
            words = runtime.runtime_callable("rope.base.worder", "Worder")(
                module.source_code
            )
            if not isinstance(words, p.Infra.RopeWorder):
                message = "Publication closure requires native word regions"
                raise TypeError(message)
            for name in names:
                finder = (
                    FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
                        source_project, name
                    )
                )
                for occurrence in finder.find_occurrences(pymodule=module):
                    _begin, end = occurrence.get_primary_range()
                    prefix, attribute, offset = words.get_splitted_primary_before(end)
                    if not prefix or attribute != name:
                        continue
                    context = module.get_source_binding_index().context_at(offset)
                    receiver = runtime.expression_name(context.environment, prefix)
                    if (
                        receiver is None
                        or not FlextInfraUtilitiesRopeRuntimeTypes.py_class(
                            owner := receiver.get_object()
                        )
                    ):
                        continue
                    if any(
                        (ancestor, name) in publications for ancestor in owner.get_mro()
                    ):
                        message = (
                            "provider publication has a surviving consumer: "
                            f"{resource.real_path}:{occurrence.lineno}:{name}"
                        )
                        raise ValueError(message)

    @classmethod
    def facade_component_references(
        cls, project: Path, *, source_project: p.Infra.RopeProject
    ) -> Mapping[tuple[str, str], frozenset[str]]:
        """Map each facade namespace to the component references it composes.

        A facade letter, or a namespace class nested in it, composes family
        component classes by MRO (``class Infra(FlextInfraConstantsPytest)``).
        Each public method a lineage component declares yields the exact
        ``Component.member`` text under ``letter`` or ``letter.Namespace``
        when the namespace binds the identical object; a reference two
        namespaces would both claim is ambiguous and never relocates.

        Returns:
            Component references keyed by the composing root package and the
            ``letter[.Namespace]`` target.

        """
        claims: dict[str, set[tuple[str, str]]] = {}
        for (base, member), targets in cls._component_claims(
            project, source_project=source_project
        ).items():
            reference = f"{base.get_name()}.{member}"
            claims.setdefault(reference, set()).update(
                (root, target) for root, target, _holder in targets
            )
        references: dict[tuple[str, str], set[str]] = {}
        for reference, targets in claims.items():
            if len(targets) == 1:
                references.setdefault(next(iter(targets)), set()).add(reference)
        return {key: frozenset(found) for key, found in sorted(references.items())}

    @staticmethod
    def _facade_namespace_holders(
        root: str, letters: Sequence[str], *, source_project: p.Infra.RopeProject
    ) -> Sequence[tuple[p.Infra.RopeClassObject, str]]:
        """List each facade letter and its recursively nested public namespaces.

        Returns:
            Each holder class with its ``letter[.Namespace]`` reference text.

        Raises:
            ValueError: A facade namespace has no native class scope.

        """
        holders: list[tuple[p.Infra.RopeClassObject, str]] = []
        for letter, facade in FlextInfraUtilitiesFacadeMembers.facade_source_classes(
            root, letters, source_project=source_project
        ).items():
            pending = [(facade, letter)]
            while pending:
                holder, target = pending.pop()
                holders.append((holder, target))
                if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(holder):
                    message = f"facade namespace has no native scope: {root}.{target}"
                    raise ValueError(message)
                for nested in holder.get_scope().get_scopes():
                    if nested.get_kind() != "Class":
                        continue
                    value = FlextInfraUtilitiesRopeRuntimeTypes.require_class_object(
                        nested.pyobject, f"{root}.{target}"
                    )
                    if not value.get_name().startswith("_"):
                        pending.append((value, f"{target}.{value.get_name()}"))
        return tuple(holders)

    @staticmethod
    def _component_ancestors(
        holder: p.Infra.RopeClassObject,
    ) -> tuple[p.Infra.RopeClassObject, ...]:
        """Require every ancestor in the holder's native method resolution order.

        Every native entry passes through the strict class guard. An unresolved
        declared base retains its admission failure instead of partial ancestry.

        Returns:
            Every native ancestor once, in method resolution order.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeTypes
        ancestors = holder.get_mro()[1:]
        return tuple(
            runtime.require_class_object(ancestor, holder.get_name())
            for ancestor in ancestors
            if not runtime.unresolved_witness(ancestor)
        )

    @classmethod
    def _composed_methods(
        cls,
        root: str,
        letters: Sequence[str],
        holder: p.Infra.RopeClassObject,
        *,
        source_project: p.Infra.RopeProject,
    ) -> Sequence[tuple[p.Infra.RopeClassObject, str]]:
        """Keep component receivers only when their effective method is identical.

        Returns:
            The resulting ``Sequence[tuple[p.Infra.RopeClassObject, str]]``.

        """
        members = FlextInfraUtilitiesFacadeMembers
        facades = tuple(
            members.facade_source_classes(
                root, letters, source_project=source_project
            ).values()
        )
        holder_members = members.facade_source_members(
            holder, source_project=source_project
        )
        composed: list[tuple[p.Infra.RopeClassObject, str]] = []
        for base in cls._component_ancestors(holder):
            module = base.get_module()
            if module is None or base in facades:
                continue
            name = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                module, source_project=source_project
            )
            if name != root and not name.startswith(f"{root}."):
                continue
            declarations = members.facade_member_declarations(base)
            composed.extend(
                (base, member)
                for member, binding in members.facade_source_members(
                    base, source_project=source_project
                ).items()
                if members.declared_by_package(
                    base,
                    member,
                    root,
                    source_project=source_project,
                    declarations=declarations,
                )
                and FlextInfraUtilitiesRopeRuntimeTypes.py_function(
                    binding.get_object()
                )
                and member in holder_members
                and holder_members[member].get_object() is binding.get_object()
            )
        return tuple(composed)

    @classmethod
    def _component_claims(
        cls, project: Path, *, source_project: p.Infra.RopeProject
    ) -> Mapping[
        tuple[p.Infra.RopeClassObject, str],
        Sequence[tuple[str, str, p.Infra.RopeClassObject]],
    ]:
        """Retain native receiver identities while discovering public composition.

        Returns:
            The resulting ``Mapping[tuple[p.Infra.RopeClassObject, str],
                Sequence[tuple[str, str, p.Infra.RopeClassObject]]]``.

        """
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(project)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        claims: dict[
            tuple[p.Infra.RopeClassObject, str],
            list[tuple[str, str, p.Infra.RopeClassObject]],
        ] = {}
        for root in FlextInfraUtilitiesFacadeMembers.facade_member_lineage(
            package, letters, source_project=source_project
        ):
            for holder, target in cls._facade_namespace_holders(
                root, letters, source_project=source_project
            ):
                for identity in cls._composed_methods(
                    root, letters, holder, source_project=source_project
                ):
                    claims.setdefault(identity, []).append((root, target, holder))
        return claims

    @staticmethod
    def _component_facade(value: p.Infra.RopeClassObject) -> bool:
        """Recognize a sibling facade backed by its native private child domain.

        Returns:
            The resulting ``bool``.

        """
        module = value.get_module()
        resource = None if module is None else module.get_resource()
        return (
            resource is not None
            and not resource.is_folder()
            and resource.parent.has_child(f"_{Path(resource.real_path).stem}")
        )

    @classmethod
    def _component_calls(
        cls,
        module: p.Infra.RopePyModule,
        claims: Mapping[
            tuple[p.Infra.RopeClassObject, str],
            Sequence[tuple[str, str, p.Infra.RopeClassObject]],
        ],
    ) -> Sequence[tuple[m.Infra.SourceRewrite, str, str]]:
        """Prove both the imported component and its lexical facade receiver.

        Callbacks consume the same native callable as call expressions. Both join
        the cohort only in load context. Writes, deletions, augmented assignments
        and class-base declarations never change their mutation or declaration owner.

        The lexical proof runs first: only a read of ``Receiver.method`` whose
        receiver is a dotted name reaches native resolution, and the receiver,
        never the occurrence, is resolved. ``_component_destination`` then
        proves the receiver is the claimed component class and that its
        ``method`` is the claimed callable, which is exactly the identity the
        hierarchy occurrence filter proved, without inferring every unrelated
        textual occurrence of the same method name.

        Returns:
            Native source changes, original references and public destinations.

        Raises:
            TypeError: If component consumer has no native module tree.

        """
        words = FlextInfraUtilitiesRopeRuntimeModules.runtime_callable(
            "rope.base.worder", "Worder"
        )(module.source_code)
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Component references require native word regions"
            raise TypeError(message)
        index = module.get_source_binding_index()
        references: dict[tuple[int, int], tuple[m.Infra.SourceRewrite, str, str]] = {}
        for method in cls._component_candidate_methods(module.source_code, claims):
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
                module.pycore.project, method
            )
            for occurrence in finder.find_occurrences(pymodule=module):
                first, last = occurrence.get_primary_range()
                prefix, name, offset = words.get_splitted_primary_before(last)
                context = index.context_at(offset)
                if (
                    not prefix
                    or name != method
                    or context.access != "read"
                    or context.role == "class-base"
                    or not cls._component_receiver_candidate(
                        context.environment, prefix
                    )
                ):
                    continue
                destination = cls._component_destination(
                    module, prefix, method, offset, claims
                )
                if destination is not None:
                    references[first, last] = (
                        m.Infra.SourceRewrite(start=first, end=last, text=destination),
                        module.source_code[first:last],
                        destination,
                    )
        return tuple(value for _region, value in sorted(references.items()))

    @staticmethod
    def _component_candidate_methods(
        source: str,
        claims: Mapping[
            tuple[p.Infra.RopeClassObject, str],
            Sequence[tuple[str, str, p.Infra.RopeClassObject]],
        ],
    ) -> tuple[str, ...]:
        """Select the claimed methods whose component this module names.

        A lexical receiver names its component class in the module itself:
        through the import, the declaration or the bare alias the receiver
        proof accepts. A module that never spells a component's name holds no
        receiver of it, so its methods need no occurrence search there.

        Returns:
            The sorted methods of every component the source names.

        """
        methods: dict[str, set[str]] = {}
        for component, method in claims:
            methods.setdefault(component.get_name(), set()).add(method)
        return tuple(
            sorted({
                method
                for name, owned in methods.items()
                if name in source
                for method in owned
            })
        )

    @staticmethod
    def _component_receiver_candidate(scope: p.Infra.RopeScope, reference: str) -> bool:
        """Whether a dotted receiver can lexically name a component class.

        The receiver is a dotted name, never a call, subscript or literal. A
        component call reads its receiver through an import, a declaration,
        a parameter or a bare class alias. A root assigned from any other value
        (a call result, a literal) is no class reference; resolving it would
        only infer that value's object graph.

        Returns:
            Whether the receiver root is a lexical class reference candidate.

        """
        if not all(part.isidentifier() for part in reference.split(".")):
            return False
        root = reference.partition(".")[0]
        lexical = FlextInfraUtilitiesRopeRuntimeModules.lexical_scope(scope, root)
        if lexical is None:
            return False
        binding = lexical.get_names().get(root)
        if not isinstance(binding, p.Infra.RopeAssignedName):
            return True
        return all(
            isinstance(assignment.ast_node, c.Infra.AST_NAME_REFERENCE_TYPES)
            for assignment in binding.assignments
        )

    @classmethod
    def _component_destination(
        cls,
        module: p.Infra.RopePyModule,
        reference: str,
        method: str,
        offset: int,
        claims: Mapping[
            tuple[p.Infra.RopeClassObject, str],
            Sequence[tuple[str, str, p.Infra.RopeClassObject]],
        ],
    ) -> str | None:
        """Elect an already bound facade for one native component call.

        Same-name class publications retain their declaration-time RHS identity;
        a stale self-reference in the class scope cannot elect another receiver.

        Returns:
            The identity-proven destination, or none without a bound facade.

        Raises:
            ValueError: If the method has competing bound facade destinations.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        scope = module.get_source_binding_index().context_at(offset).environment
        receiver = runtime.expression_name(scope, reference)
        if receiver is not None:
            receiver = runtime.class_assignment_binding(receiver, classes_only=False)
        if (
            receiver is None
            or not types.abstract_class(component := receiver.get_object())
            or cls._component_facade(component)
        ):
            return None
        targets = claims.get((component, method), ())
        original = component.get_attributes().get(method)
        if original is None or not types.py_function(original.get_object()):
            return None
        destinations = cls._bound_destinations(scope, method, original, targets)
        if len(destinations) > 1:
            message = (
                "component method has competing bound facades: "
                f"{module.get_name()}:{reference}.{method}: "
                f"{sorted(destinations)}"
            )
            raise ValueError(message)
        return next(iter(destinations)) if destinations else None

    @staticmethod
    def _bound_destinations(
        scope: p.Infra.RopeScope,
        method: str,
        original: p.Infra.RopePyName,
        targets: Sequence[tuple[str, str, p.Infra.RopeClassObject]],
    ) -> set[str]:
        """Retain effective native callable identities in the consumer scope.

        Returns:
            Bound facade calls resolving to the original native callable.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        destinations: set[str] = set()
        for _root, target, holder in targets:
            public = runtime.expression_name(scope, target)
            if public is None or public.get_object() is not holder:
                continue
            destination = f"{target}.{method}"
            actual = runtime.expression_name(scope, destination)
            if actual is not None and original.get_object() is actual.get_object():
                destinations.add(destination)
        return destinations

    @staticmethod
    def _consumer_module(
        engine: p.Infra.RopeProject, path: Path
    ) -> p.Infra.RopePyModule:
        """Load one native source module through the captured project owner.

        Returns:
            The source module authenticated by the captured project.

        Raises:
            TypeError: If the consumer is not a native source module.

        """
        resource = engine.get_file(
            path.relative_to(Path(engine.root.real_path)).as_posix()
        )
        try:
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_parsed_module(
                engine.get_pymodule(resource)
            )
        except rope.base.exceptions.ModuleSyntaxError:
            # Conteúdo candidate do overlay pode ser inválido (staging do
            # quoted-move troca conteúdos no mesmo path): o consumo segue
            # com módulo vazio e a re-leitura settled pelo disco corrige.
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_parsed_module(
                FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                    engine, Path(path).read_text(encoding="utf-8")
                )
            )
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = f"component consumer has no native source module: {path}"
            raise TypeError(message)
        return module

    @staticmethod
    def _call_witness(
        rewrite: m.Infra.SourceRewrite,
        original: str,
        module: p.Infra.RopePyModule,
    ) -> t.JsonDict:
        """Translate Python UTF-8 byte columns to ast-grep character ranges.

        Returns:
            The exact source-text and character-range witness for this call.

        """
        first = module.lines.get_line_number(rewrite.start)
        last = module.lines.get_line_number(rewrite.end)
        return {
            "regex": f"^{re.escape(original)}$",
            "range": {
                "start": {
                    "line": first - 1,
                    "column": rewrite.start - module.lines.get_line_start(first),
                },
                "end": {
                    "line": last - 1,
                    "column": rewrite.end - module.lines.get_line_start(last),
                },
            },
        }

    @classmethod
    def _component_rule(
        cls,
        rule_id: str,
        relative: str,
        namespace: str,
        calls: Sequence[tuple[m.Infra.SourceRewrite, str, str]],
        module: p.Infra.RopePyModule,
    ) -> t.JsonMapping:
        """Group native callable-load witnesses by file and public namespace.

        Returns:
            One declarative rule for the identity-proven loads and replacements.

        Raises:
            ValueError: If a source spelling has competing facade destinations.

        """
        witnesses: list[t.JsonValue] = []
        replacements: dict[str, str] = {}
        for node, original, destination in calls:
            witnesses.append(cls._call_witness(node, original, module))
            if original in replacements and replacements[original] != destination:
                message = (
                    "component spelling has competing namespace destinations: "
                    f"{relative}:{original}"
                )
                raise ValueError(message)
            replacements[original] = destination
        rewriters: list[t.JsonValue] = [
            {
                "id": f"to-{index}",
                "rule": {"regex": f"^{re.escape(original)}$"},
                "fix": destination,
            }
            for index, (original, destination) in enumerate(
                sorted(replacements.items())
            )
        ]
        return {
            "id": rule_id,
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "severity": "error",
            "files": [f"**/{relative}"],
            "rule": {
                "kind": "attribute",
                "pattern": "$REF",
                "any": witnesses,
            },
            "rewriters": rewriters,
            "transform": {
                "RELOCATED": {
                    "rewrite": {
                        "source": "$REF",
                        "rewriters": [f"to-{index}" for index in range(len(rewriters))],
                    }
                }
            },
            "fix": "$RELOCATED",
            "message": (
                "Access the component method through its composed public "
                f"facade `{namespace}`."
            ),
        }

    @classmethod
    def codemod_facade_component_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Render native-proven component calls through their bound public facade.

        Calls share one rule per consumer file and public namespace, with exact
        native call-range alternatives. Bindings elect both receivers before
        rendering; spelling alone never admits a shadowed name. Constructors,
        class bases and entity references remain unchanged.

        Returns:
            Rules for the identity-proven calls in the captured project sources.

        """
        root = project.absolute()
        claims = cls._component_claims(root, source_project=snapshot.engine)
        if not claims:
            return {}
        prefix = (
            f"{c.Infra.FACADE_COMPONENT_RELOCATE_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}"
            f"{FlextInfraUtilitiesPyprojectConform.project_package_name(root)}"
        )
        rules: dict[str, t.JsonMapping] = {}
        for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
        ):
            module = cls._consumer_module(snapshot.engine, path)
            groups: dict[str, list[tuple[m.Infra.SourceRewrite, str, str]]] = {}
            for witness in cls._component_calls(module, claims):
                groups.setdefault(witness[2].rpartition(".")[0], []).append(witness)
            for namespace, calls in sorted(groups.items()):
                rule_id = (
                    f"{prefix}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{len(rules)}"
                )
                rules[rule_id] = cls._component_rule(
                    rule_id,
                    path.relative_to(root).as_posix(),
                    namespace,
                    calls,
                    module,
                )
        return rules

    @classmethod
    def facade_library_prefixes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrTuple:
        """Name every third-party distribution the project's imports resolve to.

        Each top-level module the project imports that is neither the standard
        library, the own package nor a FLEXT facade package is mapped to the
        installed distributions that provide it (``git`` resolves to
        ``gitpython``, so the capability prefix ``git_`` is not a library
        prefix). Nothing is listed: the set is the dependency declaration as
        installed.

        Returns:
            The normalized distribution names, sorted.

        """
        root = project.absolute()
        native = FlextInfraUtilitiesCodemodNativePackage
        known = {
            *sys.stdlib_module_names,
            *native.codemod_facade_packages(snapshot, root),
            *FlextInfraUtilitiesCodemodNative.codemod_own_package_names(root),
        }
        providers = packages_distributions()
        return tuple(
            sorted({
                distribution.lower().replace("-", "_").replace(".", "_")
                for module in native.codemod_imported_top_modules(snapshot, root)
                if module not in known and not module.startswith("_")
                for distribution in providers.get(module, ())
            })
        )

    @classmethod
    def codemod_library_member_name_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Render the one rule banning a library-prefixed facade member.

        A facade export is prefixed by its capability (``git_``,
        ``refactor_``, ``workspace_``), never by the third-party library that
        implements it (``rope_project``, ``RopeProject``, ``pytest_runner``):
        only the c/t/p/m/u families know the library (ADR-028; operator
        ruling 2026-10-25). The prefixes are the installed distributions of
        the project's imports (``facade_library_prefixes``). Detection-only:
        the rename map is produced from this scan and applied by the mass
        rename tooling with a deprecated-signature window.

        Returns:
            The single rule document keyed by its rule id, or nothing when the
            project imports no third-party library.

        """
        root = project.absolute()
        prefixes = cls.facade_library_prefixes(snapshot, root)
        if not prefixes:
            return {}
        snake = "|".join(re.escape(prefix) for prefix in prefixes)
        camel = "|".join(
            re.escape(prefix.replace("_", " ").title().replace(" ", ""))
            for prefix in prefixes
        )
        letters = "|".join(
            re.escape(letter)
            for letter in sorted(
                set(config.Infra.tooling.facade_members.owners.values())
            )
        )
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        rule_id = (
            f"{c.Infra.FACADE_LIBRARY_MEMBER_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "severity": "error",
                "rule": {
                    "kind": "attribute",
                    "regex": rf"^(?:{letters})\.",
                    "has": {
                        "field": "attribute",
                        "regex": rf"^(?:(?:{snake})(?:_|$)|(?:{camel})(?:[A-Z]|$))",
                    },
                },
                "message": (
                    "Facade member prefixed by a library name: export it under "
                    "its capability prefix instead."
                ),
            }
        }


__all__: list[str] = ["FlextInfraUtilitiesFacadeComponents"]
