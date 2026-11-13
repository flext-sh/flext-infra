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

import io
import re
import sys
import tokenize
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from functools import partial
from importlib.metadata import packages_distributions
from pathlib import Path

from flext_cli import u
from rope.base import ast, exceptions as rope_exceptions

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesProtectedEditLinting,
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
    FlextInfraUtilitiesRopeSourceBindingCollector,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisExports,
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticCutoverFacadeBases,
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
        context: p.Infra.ModuleSkeletonRenderContext,
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

    @classmethod
    def facade_component_declarations(
        cls,
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
        alias_composers = cls._facade_namespace_alias_composers(project, declarations)
        return tuple(
            declaration
            for declaration in declarations
            if declaration[1].get_name() not in alias_composers
        )

    @staticmethod
    def _facade_namespace_alias_composers(
        project: p.Infra.RopeProject,
        declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
    ) -> frozenset[str]:
        """Exclude pure alias namespaces from flattened facade base selection.

        A composer has no bases or behavior of its own and binds only exported
        sibling parts as simple class attributes. The parts retain the flattened
        facade contract; the composer remains independently published by its
        own package without becoming a duplicate facade base.

        Returns:
            Names of namespace-only declarations excluded from base selection.

        """
        names = frozenset(owner.get_name() for _path, owner in declarations)
        composers: set[str] = set()
        by_path: dict[Path, list[p.Infra.RopeSourceClass]] = {}
        for path, owner in declarations:
            by_path.setdefault(path, []).append(owner)
        for path, owners in by_path.items():
            tree = ast.parse(project.source_text(path))
            nodes = {
                node.name: node for node in tree.body if isinstance(node, ast.ClassDef)
            }
            for owner in owners:
                node = nodes.get(owner.get_name())
                if node is None or node.bases:
                    continue
                aliases: set[str] = set()
                for statement in node.body:
                    if (
                        isinstance(statement, ast.Expr)
                        and isinstance(statement.value, ast.Constant)
                        and isinstance(statement.value.value, str)
                    ):
                        continue
                    if not (
                        isinstance(statement, ast.Assign)
                        and len(statement.targets) == 1
                        and isinstance(statement.targets[0], ast.Name)
                        and isinstance(statement.value, ast.Name)
                        and statement.value.id in names
                    ):
                        aliases.clear()
                        break
                    aliases.add(statement.value.id)
                if aliases:
                    composers.add(owner.get_name())
        return frozenset(composers)

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
    def facade_domain_owner_observation(
        cls,
        project: p.Infra.RopeProject,
        domain: Path,
        family_declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
    ) -> list[tuple[Path, str]]:
        """Observe the declared owner of one private domain, wherever it lives.

        The owner is, in order: the class the canonical sibling ``x.py``
        declares; else the one class of ``_x`` that no other class declared
        in ``_x`` extends (native superclasses); else a family declaration
        that extends every such maximal part, which ``make mod`` moves to the
        canonical sibling. A domain with none of them has no owner yet, and
        ``make mod`` creates it.

        Returns:
            The observed owner, or no owner when the domain declares none.

        """
        canonical = domain.parent / f"{domain.name.lstrip('_')}.py"
        declared = [
            (path, owner) for path, owner in family_declarations if path == canonical
        ]
        if declared:
            return [(path, owner.get_name()) for path, owner in declared]
        parts = list(cls.facade_component_declarations(project, domain))
        extended = {
            id(ancestor)
            for _path, owner in parts
            for ancestor in cls._native_ancestors(owner)
        }
        maximal = [(path, owner) for path, owner in parts if id(owner) not in extended]
        if len(maximal) == 1:
            return [(maximal[0][0], maximal[0][1].get_name())]
        required = {id(owner) for _path, owner in maximal}
        composers = [
            (path, owner, {id(ancestor) for ancestor in cls._native_ancestors(owner)})
            for path, owner in family_declarations
        ]
        composers = [
            (path, owner, ancestors)
            for path, owner, ancestors in composers
            if maximal and required <= ancestors
        ]
        return [
            (path, owner.get_name())
            for path, owner, ancestors in composers
            if not any(id(other) in ancestors for _p, other, _a in composers)
        ]

    @classmethod
    def _family_subfacade_owner_map(
        cls,
        project: p.Infra.RopeProject,
        directories: Sequence[Path],
        family_declarations: Mapping[
            Path, Sequence[tuple[Path, p.Infra.RopeSourceClass]]
        ],
    ) -> dict[Path, list[tuple[Path, str]]]:
        """Elect each domain owner by declaration, never by inference.

        Composed-part publication is single-owner: generation accepts only an
        observed owner declared by the canonical sibling ``x.py`` or inside
        ``_x`` itself. An owner declared anywhere else, several owners or none
        is a source defect; generation never compensates for it.

        Returns:
            Each requested domain with its declared owner.

        Raises:
            ValueError: If a domain has no owner in place or several.

        """
        elected: dict[Path, list[tuple[Path, str]]] = {}
        for domain in sorted(directories):
            canonical = domain.parent / f"{domain.name.lstrip('_')}.py"
            owners = cls.facade_domain_owner_observation(
                project, domain, family_declarations[domain.parent]
            )
            if len(owners) != 1 or not (
                owners[0][0] == canonical or owners[0][0].is_relative_to(domain)
            ):
                parts = [
                    f"{path.name}:{owner.get_name()}"
                    for path, owner in cls.facade_component_declarations(
                        project, domain
                    )
                ]
                message = (
                    f"Facade domain {domain} has {len(owners)} owners in place "
                    f"{[f'{path.name}:{name}' for path, name in owners]} for its "
                    f"parts {parts}; declare the canonical sibling "
                    f"{canonical.name} with one class composing its parts"
                )
                raise ValueError(message)
            elected[domain] = owners
        return elected

    @staticmethod
    def _native_ancestors(
        owner: p.Infra.RopeSourceClass,
    ) -> tuple[p.Infra.RopePyObject, ...]:
        """Return every native ancestor class of ``owner`` (excluding itself).

        Returns:
            The transitive native superclasses.

        """
        seen: dict[int, p.Infra.RopePyObject] = {}
        pending = list(owner.get_superclasses())
        while pending:
            ancestor = pending.pop()
            if id(ancestor) in seen:
                continue
            seen[id(ancestor)] = ancestor
            if FlextInfraUtilitiesRopeRuntimeTypes.py_class(ancestor):
                pending.extend(ancestor.get_superclasses())
        return tuple(seen.values())

    @classmethod
    def _facade_project_classes(
        cls,
        project: p.Infra.RopeProject,
        providers: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> dict[int, p.Infra.RopeSourceClass]:
        """Collect every provider class and ancestor declared in this project.

        Returns:
            The project's source classes keyed by native identity.

        """
        root = Path(project.root.real_path)
        runtime = FlextInfraUtilitiesRopeRuntimeTypes
        classes: dict[int, p.Infra.RopeSourceClass] = {}
        for _name, provider in providers:
            if not runtime.py_class(provider):
                continue
            for klass in (provider, *cls._native_ancestors(provider)):
                if not runtime.py_class(klass):
                    continue
                resource = klass.get_module().get_resource()
                if resource is not None and Path(resource.real_path).is_relative_to(
                    root
                ):
                    classes[id(klass)] = klass
        return classes

    @classmethod
    def _facade_member_collisions(
        cls,
        project: p.Infra.RopeProject,
        providers: Sequence[tuple[str, p.Infra.RopePyObject]],
        namespace: str,
    ) -> p.Result[bool]:
        """Refuse a composition in which two unrelated parts declare one member.

        Method resolution would silently pick one of them for every caller that
        reaches the member through the composed facade. Only classes declared
        in this project count; a part that extends another overrides it, and
        parts that bind the same object (one re-export) agree. The
        facade's own ``namespace`` class is composed from every part that
        declares it, so its homonyms are the composition, not a collision.

        Returns:
            True, or the first member two unrelated project parts declare.

        """
        classes = cls._facade_project_classes(project, providers)
        lineage = {
            key: frozenset(id(a) for a in cls._native_ancestors(klass))
            for key, klass in classes.items()
        }
        declaring: dict[str, list[int]] = {}
        for key, klass in classes.items():
            type_only = cls._facade_type_only_members(klass)
            for member in klass.get_scope().get_defined_names():
                if (
                    not member.startswith("__")
                    and member != namespace
                    and member not in type_only
                ):
                    declaring.setdefault(member, []).append(key)
        collisions: list[str] = []
        for member, keys in sorted(declaring.items()):
            roots = [
                key
                for key in keys
                if not any(other in lineage and key in lineage[other] for other in keys)
            ]
            bound = {
                id(classes[key].get_scope().get_defined_names()[member].get_object())
                for key in roots
            }
            if len(roots) > 1 and len(bound) > 1:
                names = sorted(classes[key].get_name() for key in roots)
                message = (
                    f"Facade composition declares {member!r} in unrelated parts "
                    f"{names}; rename one of them or let one part extend the other"
                )
                collisions.append(message)
        if collisions:
            return r[bool].fail("\n".join(collisions))
        return r[bool].ok(value=True)

    @staticmethod
    def _facade_type_checking_guard(
        module: p.Infra.RopePyModule,
        test: ast.expr,
    ) -> bool | None:
        """Prove a type-checking guard through its native lexical import binding.

        Returns:
            Native import proof, or None when the expression is not a typing guard.

        """
        if not FlextInfraUtilitiesRopeSourceBindingCollector.type_checking_test(test):
            return None
        head = test.value if isinstance(test, ast.Attribute) else test
        offset = FlextInfraUtilitiesRopeRuntime.source_offset(module.source_code, head)
        environment = module.get_source_binding_index().context_at(offset).environment
        binding = environment.lookup(head.id) if isinstance(head, ast.Name) else None
        runtime = FlextInfraUtilitiesRopeRuntimeTypes
        imported = None
        if isinstance(test, ast.Name) and runtime.imported_name(binding):
            if binding.imported_name == "TYPE_CHECKING":
                imported = binding.imported_module
        elif isinstance(test, ast.Attribute) and runtime.imported_module(binding):
            imported = binding
        return (
            imported is not None
            and imported.level == 0
            and imported.module_name in {"typing", "typing_extensions"}
        )

    @classmethod
    def _facade_type_only_members(
        cls,
        klass: p.Infra.RopeSourceClass,
    ) -> frozenset[str]:
        """Exclude only declarations behind import-proven type-checking guards.

        Unknown guards and any runtime declaration of the same name retain the
        original Rope collision semantics. Nested scopes do not bind class locals.

        Returns:
            Names declared exclusively in proven type-only branches.

        """
        definition = klass.get_ast()
        if not isinstance(definition, ast.ClassDef):
            return frozenset()
        module = klass.get_module()
        type_only: set[str] = set()
        possible_runtime: set[str] = set()
        pending: list[tuple[ast.AST, bool]] = [
            (node, False) for node in definition.body
        ]
        while pending:
            node, guarded = pending.pop()
            if (
                isinstance(node, ast.If)
                and (proven := cls._facade_type_checking_guard(module, node.test))
                is not None
            ):
                pending.extend((child, guarded or proven) for child in node.body)
                pending.extend((child, guarded) for child in node.orelse)
                continue
            names = type_only if guarded else possible_runtime
            if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                names.add(node.name)
                continue
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
            elif isinstance(node, ast.Import | ast.ImportFrom):
                names.update(
                    alias.asname or alias.name.split(".")[0] for alias in node.names
                )
            elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar):
                if node.name is not None:
                    names.add(node.name)
            elif isinstance(node, ast.MatchMapping) and node.rest is not None:
                names.add(node.rest)
            pending.extend((child, guarded) for child in ast.iter_child_nodes(node))
        return frozenset(type_only - possible_runtime)

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
        family: c.Infra.FacadeFamily | p.Infra.FacadeFamily,
        owner_name: str | None = None,
    ) -> p.Result[str]:
        """Compose declared native providers while retaining authored source bodies.

        Native layouts supply every span and lexical environment. Import operations
        and the change collector remain Rope's owners; no source is parsed here.

        Returns:
            The complete unchanged-body source candidate, never a published effect.

        """
        selected = c.Infra.FacadeFamily(
            family.letter if isinstance(family, m.Infra.FacadeFamily) else family
        )
        headers = (
            FlextInfraUtilitiesSemanticCutoverFacadeBases.facade_import_base_edits(
                Path(project.root.real_path),
                {path: project.source_text(path)},
                (path,),
                source_project=project,
            )
        )
        if headers.failure:
            return r[str].from_failure(headers)
        if headers.value:
            declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                Path(project.root.real_path),
                (),
                {edit.file_path: edit.updated_source for edit in headers.value},
                source_project=project,
            )
            with project.source_view(
                declared_files=declared, additional_source_folders=None
            ):
                return cls.facade_component_source(
                    project, path, directory, family=selected, owner_name=owner_name
                )
        settled = cls._facade_settled_initializers(project, (path, directory))
        if settled.failure:
            return r[str].from_failure(settled)
        resource = FlextInfraUtilitiesRopeRuntimeModules.file_resource_at(project, path)
        planned = cls._facade_component_plan(
            project, path, directory, family=selected, owner_name=owner_name
        )
        if planned.failure:
            return r[str].from_failure(planned)
        module, owner, namespace = planned.value[:3]
        step = cls._facade_indent_step(project)
        source = cls._facade_sorted_imports(
            project, path, resource, module.source_code, planned.value[5]
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
                projected.value, source, planned.value[4], step
            )
        return rendered.flat_map(
            lambda text: FlextInfraUtilitiesProtectedEditLinting.normalize_source(
                Path(project.root.real_path),
                path,
                text,
                before_source=(
                    None
                    if text.startswith(c.Infra.AUTOGEN_HEADER)
                    else module.source_code
                ),
            )
        ).flat_map(
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
            list[t.Infra.RopeFromImport],
        ]
    ]:
        """Plan the facade composition against the module's own native epoch.

        Returns:
            The module, owner, namespace layout, retained bases and added
            imports, or the first failure.

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
                    list[t.Infra.RopeFromImport],
                ]
            ].from_failure(resolved)
        owner, namespace = resolved.value[0], resolved.value[1]
        index = module.get_source_binding_index()
        framed = cls._facade_namespace_bases(
            module,
            namespace,
            path,
            directory=directory,
            declared_names=frozenset(
                provider.get_name()
                for _path, provider in cls._facade_protocol_bootstrap_declarations(
                    directory, family, namespace, resolved.value[2]
                )
            ),
        )
        if framed.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    list[t.Infra.RopeFromImport],
                ]
            ].from_failure(framed)
        layout, bases = framed.value
        # A namespace-only wrapper is already represented by its nested class.
        # Composing the wrapper again would introduce a second, incompatible
        # class-valued member with the namespace's own name.
        wrappers = tuple(
            provider
            for _origin, provider in resolved.value[2]
            if namespace is not owner
            and set(provider.get_attributes()) == {namespace.get_name()}
            and provider.get_attributes()[namespace.get_name()].get_object()
            in namespace.get_mro()[1:]
        )
        bases = [
            (expression, base)
            for expression, base in bases
            if base not in wrappers
            and not any(
                base in provider.get_mro()[1:]
                for _origin, provider in resolved.value[2]
                if provider is not base
            )
        ]
        aliases = cls._facade_namespace_aliases(index, namespace)
        providers = cls._facade_admitted_providers(
            project,
            (
                owner,
                namespace,
                tuple(
                    (origin, provider)
                    for origin, provider in (
                        cls._facade_protocol_bootstrap_declarations(
                            directory, family, namespace, resolved.value[2]
                        )
                    )
                    if provider not in wrappers
                ),
                resolved.value[3],
            ),
            family=family,
            aliases=aliases,
            bases=bases,
        )
        if providers.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    list[t.Infra.RopeFromImport],
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
        ).flat_map(
            lambda retained: cls._facade_member_collisions(
                project, retained[0], namespace.get_name()
            ).map(lambda _settled: retained)
        )
        if composed.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    list[t.Infra.RopeFromImport],
                ]
            ].from_failure(composed)
        # Utility storage admits only ClassVar/Final members
        # (``utility_namespace_declaration``); its nominal providers keep their
        # own instance role and never reach the namespace.
        loose = cls._facade_loose_declarations(
            project,
            owner,
            () if family is c.Infra.FacadeFamily.U else providers.value[1],
            (aliases, composed.value[0]),
        )
        if loose.failure:
            return r[
                tuple[
                    p.Infra.RopeSourceModule,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClass,
                    p.Infra.RopeSourceClassLayout,
                    list[tuple[str, p.Infra.RopePyObject]],
                    list[t.Infra.RopeFromImport],
                ]
            ].from_failure(loose)
        return r[
            tuple[
                p.Infra.RopeSourceModule,
                p.Infra.RopeSourceClass,
                p.Infra.RopeSourceClass,
                p.Infra.RopeSourceClassLayout,
                list[tuple[str, p.Infra.RopePyObject]],
                list[t.Infra.RopeFromImport],
            ]
        ].ok((
            module,
            owner,
            namespace,
            layout,
            composed.value[0],
            cls._facade_planned_imports(
                cls._facade_declaring_packages(project, resolved.value[2]),
                composed.value[1],
            ),
        ))

    @staticmethod
    def _facade_protocol_bootstrap_declarations(
        directory: Path,
        family: c.Infra.FacadeFamily,
        namespace: p.Infra.RopeSourceClass,
        declarations: tuple[tuple[Path, p.Infra.RopeSourceClass], ...],
    ) -> tuple[tuple[Path, p.Infra.RopeSourceClass], ...]:
        """Use persisted source-bootstrap protocol owners instead of rediscovery.

        The bootstrap facade has already authenticated and linearized its direct
        protocol holders. Re-enumerating ``_protocols`` here reintroduces legacy
        aggregate holders alongside their canonical replacements, which creates
        duplicate nested contract declarations before the regular planner can
        render the same reduced MRO.

        Returns:
            Direct canonical holders from the persisted protocol facade, or the
            normal family declarations when the facade is authored.

        """
        module = namespace.get_module()
        source = module.source_code
        if (
            family is not c.Infra.FacadeFamily.P
            or directory.name != "_protocols"
            or not source.startswith(
                "# AUTO-GENERATED FILE - Source bootstrap protocol facade."
            )
        ):
            return declarations
        declared = {}
        for path, provider in declarations:
            module = provider.get_module()
            declared[module.get_name(), provider.get_name()] = (path, provider)
        selected = []
        for provider in namespace.get_superclasses():
            if not isinstance(provider, p.Infra.RopeNamedObject):
                continue
            module = provider.get_module()
            if module is None:
                continue
            key = (module.get_name(), provider.get_name())
            if key in declared:
                selected.append(declared[key])
        selected = tuple(selected)
        return selected or declarations

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

        Raises:
            InconsistentHierarchyError: If ``not
                module.source_code.startswith(c.Infra.AUTOGEN_HEADER)``.

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
        sources.update(cls._facade_owner_domain_sources(project, sources))
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
        try:
            namespaces = cls._facade_inherited_namespaces(
                owner, directory, resolver_factory=resolver_factory, project=project
            )
        except rope_exceptions.InconsistentHierarchyError:
            if not module.source_code.startswith(c.Infra.AUTOGEN_HEADER):
                raise
            namespaces = ()
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
    def _facade_owner_domain_sources(
        project: p.Infra.RopeProject,
        sources: Mapping[str, tuple[Path, str]],
    ) -> dict[str, tuple[Path, str]]:
        """Capture the private domain each sibling owner composes.

        A sibling owner ``x.py`` composes the parts of ``_x`` through that
        family package, so resolving its bases needs the package initializer
        and every part module, including parts this run projects but that
        are not on disk yet (the project view carries the candidate). Each
        domain is listed through that view; the repository is not rescanned.

        Returns:
            The domain modules not already captured, keyed by module name.

        """
        root = Path(project.root.real_path)
        domains = {
            origin.parent / f"_{origin.stem}" for origin, _source in sources.values()
        }
        captured: dict[str, tuple[Path, str]] = {}
        for candidate in (
            child
            for domain in sorted(domains)
            if project.source_query(domain, "isdir")
            for child in project.source_children(domain)
            if child.suffix == c.Infra.EXT_PYTHON
            and project.source_query(child, "isfile")
        ):
            name = FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                candidate, project_root=root, source_project=project
            )
            if name not in sources:
                captured[name] = (candidate, project.source_text(candidate))
        return captured

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
            else frozenset[Path](),
            Path(project.root.real_path).resolve(),
        )
        # A generated facade's own base list is the previous projection, which
        # this run re-derives from the family declarations: a base it no longer
        # resolves awaits that re-render instead of blocking it. A facade the
        # generator scaffolds in this run is the same kind of projection.
        rendered = project.source_text(path).startswith(c.Infra.AUTOGEN_HEADER) or any(
            plan.path == path
            and plan.before.content is None
            and plan.desired_content is not None
            for plan in project.source_plans
        )
        proven: list[tuple[p.Infra.SourceClassReference]] = []
        # A class nested in a deferred holder is reached through the holder's
        # stale bases, so it awaits the same re-render.
        deferred_holders: set[tuple[str, ...]] = set()
        for reference, holder in cls._facade_class_references(
            FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                module, source_project=project
            ),
            owner,
        ):
            if any(
                reference.attributes[:depth] in deferred_holders
                for depth in range(1, len(reference.attributes))
            ):
                deferred_holders.add(reference.attributes)
                continue
            deferred = cls._facade_class_deferred(
                project, (path, module, holder), admitted, rendered=rendered
            )
            if deferred.failure:
                return result_type.from_failure(deferred)
            if deferred.value:
                deferred_holders.add(reference.attributes)
            else:
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
        *,
        rendered: bool,
    ) -> p.Result[bool]:
        """Classify one facade class by the provenance of its unresolved bases.

        ``admitted`` holds the generated family barrel identities (empty when
        the barrel is authored) and the project root. In a ``rendered``
        (generated) facade an unresolved base belongs to the stale projection
        the run re-derives, so it defers instead of failing.

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
                if rendered:
                    deferred = True
                    continue
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
                if rendered:
                    deferred = True
                    continue
                return r[bool].fail(
                    f"Unresolved facade base: {path}:{expression}: {provider.error}",
                    exception=provider.exception,
                )
            if provider.value in family or (
                rendered and provider.value.is_relative_to(root)
            ):
                deferred = True
            elif provider.value.is_relative_to(root):
                return r[bool].fail(f"Unresolved facade base: {path}:{expression}")
        return r[bool].ok(value=deferred)

    @staticmethod
    def _facade_class_references(
        module_name: str,
        owner: p.Infra.RopeSourceClass,
    ) -> Generator[tuple[p.Infra.SourceClassReference, p.Infra.RopeSourceClass]]:
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

        Generated class storage remains a namespace when an obsolete model
        base would otherwise classify the holder as a whole data model.

        Returns:
            Every nested type class bound by an abstract parent attribute or a
            family-directory base, in declaration order.

        Raises:
            InconsistentHierarchyError: If ``not rendered``.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        payload = FlextInfraUtilitiesDeclarationPayload
        rendered = owner.get_module().source_code.startswith(c.Infra.AUTOGEN_HEADER)
        nested: list[p.Infra.RopeSourceClass] = []
        storage: set[p.Infra.RopeSourceClass] = set()
        for scope in owner.get_scope().get_scopes():
            child = scope.pyobject
            if not types.py_class(child):
                continue
            try:
                classified = (
                    FlextInfraUtilitiesFacadeMembers.class_kind(
                        child,
                        resolver_factory=resolver_factory,
                        source_project=project,
                    )
                    is c.Infra.FacadeMemberKind.TYPE
                )
            except rope_exceptions.InconsistentHierarchyError:
                if not rendered:
                    raise
                classified = True
            if rendered:
                aliases = FlextInfraUtilitiesFacadeComponents._facade_namespace_aliases(
                    child.get_module().get_source_binding_index(), child
                )
                if (
                    bool(aliases)
                    and all(types.abstract_class(value) for value in aliases.values())
                    and payload.utility_namespace_declaration(project, child)
                ):
                    storage.add(child)
                    classified = True
            if classified:
                nested.append(child)
        return tuple(
            child
            for child in nested
            if (
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
                or child in storage
            )
        )

    @staticmethod
    def _facade_namespace_bases(
        module: p.Infra.RopeSourceModule,
        namespace: p.Infra.RopeSourceClass,
        path: Path,
        *,
        directory: Path,
        declared_names: frozenset[str],
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
        index = module.get_source_binding_index()
        layout = index.class_layout(namespace.get_scope())
        source = module.source_code
        # A generated facade's base list is the previous projection; a base it
        # no longer resolves is re-derived from the family providers.
        rendered = source.startswith(c.Infra.AUTOGEN_HEADER)
        bases: list[tuple[str, p.Infra.RopePyObject]] = []
        for (start, end), binding in layout.base_bindings:
            if binding is None:
                if rendered:
                    continue
                message = f"Unresolved facade base: {path}:{source[start:end]}"
                return r[
                    tuple[
                        p.Infra.RopeSourceClassLayout,
                        list[tuple[str, p.Infra.RopePyObject]],
                    ]
                ].fail(message)
            base = binding.get_object()
            if rendered:
                if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(base):
                    continue
                base_module = base.get_module()
                resource = None if base_module is None else base_module.get_resource()
                if (
                    resource is not None
                    and Path(resource.real_path).is_relative_to(directory)
                    and base.get_name() in declared_names
                ):
                    continue
            bases.append((source[start:end], base))
        return FlextInfraUtilitiesFacadeComponents._facade_namespace_bindings(
            module, index, namespace, path
        ).map(lambda _bound: (layout, bases))

    @staticmethod
    def _facade_resolved_assignments(
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
    ) -> tuple[p.Infra.RopeSourceAssignmentLayout, ...]:
        """Resolve every namespace assignment except model metadata and publications.

        A ``Name = Name`` publication reads its value from the module scope
        (``facade_self_publications``); resolving it in the class scope would
        infer the attribute from itself.

        Returns:
            Each direct assignment with its native value and root bindings.

        """
        source = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
            namespace.get_module()
        ).source_code
        return tuple(
            assignment
            for declaration in index.assignment_layouts(namespace.get_scope())
            if declaration.targets
            and declaration.targets[0][0] != c.Infra.MODEL_CONFIG_ATTRIBUTE
            and (
                declaration.value is None
                or source[declaration.value[0] : declaration.value[1]]
                != declaration.targets[0][0]
            )
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
    ) -> dict[str, p.Infra.RopePyObject]:
        """Read the namespace's resolved assignments as bound target identities.

        Returns:
            Every bound target name with its resolved value.

        """
        return {
            target_name: assignment.value_binding.get_object()
            for assignment in cls._facade_resolved_assignments(index, namespace)
            if assignment.value_binding is not None
            for target_name, _region in assignment.targets
        }

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
            kind = FlextInfraUtilitiesFacadeMembers.class_kind(
                provider, resolver_factory=resolver_factory, source_project=project
            )
            if family is c.Infra.FacadeFamily.M and any(
                isinstance(ancestor, p.Infra.RopeBuiltinClass)
                and isinstance(ancestor.builtin, type)
                and ancestor.builtin is not object
                for ancestor in provider.get_mro()[1:]
            ):
                nominal.append(provider)
                continue
            # A constants part is a namespace holder whatever its MRO carries
            # (ENFORCE-042 makes it descend from FlextSettings): it composes.
            # A utility provider is judged by its own storage role below:
            # utility facades publish no nominal aliases, so a nominal verdict
            # here would drop its behavior from the facade entirely.
            if (
                kind is not c.Infra.FacadeMemberKind.TYPE
                and family is not c.Infra.FacadeFamily.C
                and family is not c.Infra.FacadeFamily.U
                and (
                    family is not c.Infra.FacadeFamily.P
                    or kind is not c.Infra.FacadeMemberKind.PROTOCOL
                )
            ):
                nominal.append(provider)
                continue
            # A provider a namespace alias already publishes is never also
            # composed: the alias is its publication (``Base = Owner``).
            if family is not c.Infra.FacadeFamily.U and provider in aliases.values():
                continue
            if family is c.Infra.FacadeFamily.U:
                if cls._utility_provider_nominal(project, provider, bases):
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
        project: p.Infra.RopeProject,
        provider: p.Infra.RopeSourceClass,
        bases: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> bool:
        """Whether a utility provider publishes nominally instead of composing.

        Returns:
            True for instance behavior, inherited instance callables absent from
            the facade bases, or a provider without meaningful class callables or
            admissible class storage.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        if any(
            isinstance(base, types.runtime_type("rope.base.builtins", "BuiltinType"))
            for base in provider.get_mro()[1:]
        ):
            return False
        # A namespace holder of classes (declared or inherited from its parts,
        # e.g. a composition of manager namespaces) composes as storage.
        if any(
            types.py_class(scope.pyobject)
            for ancestor in provider.get_mro()
            if types.py_class(ancestor)
            for scope in ancestor.get_scope().get_scopes()
        ):
            return False
        # A namespace holder binding its part classes as attributes composes
        # them exactly like nested declarations do. A class-body ``X = X``
        # reads ``X`` from the module scope, where Rope's inference of the
        # class-scope name does not look.
        module_names = provider.get_module().get_scope().get_names()
        if any(
            isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Name)
            and (bound := module_names.get(statement.value.id)) is not None
            and types.py_class(bound.get_object())
            for statement in provider.get_ast().body
        ):
            return False
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

        # Instance behavior inherited from an upstream utility facade the
        # provider extends (``FlextTestsUtilities.Tests``) is that facade's
        # surface; any other inherited instance callable, a model base's
        # included, keeps the provider nominal.
        def from_utility_facade(value: p.Infra.RopePyObject) -> bool:
            module_obj = value.get_module()
            if module_obj is None:
                return False
            module = module_obj.get_name()
            return module.endswith(".utilities") or "._utilities" in module

        inherited_instance = any(
            types.py_function(value := attribute.get_object())
            and value.get_kind() not in {"classmethod", "staticmethod"}
            and not from_utility_facade(value)
            and not any(
                (existing := base.get_attributes().get(name)) is not None
                and existing.get_object() is value
                for _expression, base in bases
            )
            for name, attribute in provider.get_attributes().items()
        )
        # Extending a class is meaningful in itself: an upstream base the
        # engine cannot resolve to source still carries its behavior. Annotated
        # class storage (``Member: ClassVar[...] = value``) is the namespace's
        # own publication, reached as ``u.Ns.Member``: a provider whose storage
        # is wholly admissible class storage composes; instance fields (a
        # decorated data carrier) keep it nominal.
        storage = bool(
            provider
            .get_module()
            .get_source_binding_index()
            .class_layout(provider.get_scope())
            .annotated_bindings
        ) and FlextInfraUtilitiesDeclarationPayload.utility_namespace_declaration(
            project, provider
        )
        meaningful = bool(methods) or bool(provider.get_superclasses()) or storage
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
            binding = provider.get_name()
            # A provider a retained base already composes (itself or through
            # its MRO) is not appended again: a second listing beside that base
            # can contradict the inherited order (C3) on the next pass.
            if any(
                base is provider
                or (
                    FlextInfraUtilitiesRopeRuntimeTypes.py_class(base)
                    and provider in base.get_mro()[1:]
                )
                for _expression, base in retained
            ):
                if any(
                    expression == binding and cls._same_facade_target(base, provider)
                    for expression, base in retained
                ):
                    bindings.append(binding)
                continue
            occupied = module.get_scope().get_names().get(binding)
            # A generated facade's own imports are the previous projection the
            # render replaces; only a non-import binding is an occupation there.
            stale_import = module.source_code.startswith(
                c.Infra.AUTOGEN_HEADER
            ) and FlextInfraUtilitiesRopeRuntimeTypes.imported_name(occupied)
            if (
                occupied is not None
                and not stale_import
                and not cls._same_facade_target(occupied.get_object(), provider)
            ):
                message = f"Occupied facade provider binding: {path}:{binding}"
                return r[
                    tuple[list[tuple[str, p.Infra.RopePyObject]], tuple[str, ...]]
                ].fail(message)
            if stale_import:
                retained = [
                    (expression, base)
                    for expression, base in retained
                    if expression != binding
                ]
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
                base = None if binding is None else binding.get_object()
                if types.abstract_class(base):
                    names.setdefault(base.get_name())
            pending.extend(
                child for child in scope.get_scopes() if types.py_class(child.pyobject)
            )
        return tuple(names)

    @classmethod
    def _facade_loose_declarations(
        cls,
        project: p.Infra.RopeProject,
        owner: p.Infra.RopeSourceClass,
        nominal: Sequence[p.Infra.RopeSourceClass],
        bound: tuple[
            Mapping[str, p.Infra.RopePyObject],
            Sequence[tuple[str, p.Infra.RopePyObject]],
        ],
    ) -> p.Result[bool]:
        """Refuse family classes declared outside their module's part class.

        Every module keeps its declarations inside its single top-level class:
        a family class reaches the facade only nested in its part class and
        composed through the MRO. A provider an authored alias or a retained
        base already reaches is composed, not loose.

        Returns:
            True, or every loose declaration with the part class it must move
            into.

        """
        aliases, retained = bound
        loose: list[str] = []
        for provider in nominal:
            if provider in aliases.values() or any(
                base is provider
                or (
                    FlextInfraUtilitiesRopeRuntimeTypes.py_class(base)
                    and any(
                        cls._same_facade_target(ancestor, provider)
                        for ancestor in base.get_mro()[1:]
                    )
                )
                for _expression, base in retained
            ):
                continue
            module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                provider.get_module(), source_project=project
            )
            part = owner.get_name() + u.derive_class_stem(
                module.rpartition(".")[2].strip("_")
            )
            loose.append(f"{module}.{provider.get_name()} -> {part}")
        if loose:
            return r[bool].fail(
                "Module-level family declarations must nest in their part class"
                f" (make mod): {', '.join(loose)}"
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _facade_declaring_packages(
        project: p.Infra.RopeProject,
        declarations: Sequence[tuple[Path, p.Infra.RopeSourceClass]],
    ) -> dict[str, str]:
        """Bind each part to the family package that publishes it.

        A generated facade imports through the nearest package lazy export,
        never a module path below it (ADR-028 Decision 10): a part declared in
        a ``_<family>`` package is imported from that family package; any
        other part keeps its defining module.

        Returns:
            Each declaration name with its importing package.

        """
        directories = frozenset(
            family.directory
            for family in FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        )
        packages: dict[str, str] = {}
        for _origin, declaration in declarations:
            module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                declaration.get_module(), source_project=project
            )
            parent, _separator, _leaf = module.rpartition(".")
            packages[declaration.get_name()] = (
                parent if parent.rpartition(".")[2] in directories else module
            )
        return packages

    @staticmethod
    def _facade_planned_imports(
        packages: Mapping[str, str],
        bindings: Sequence[str],
    ) -> list[t.Infra.RopeFromImport]:
        """Build the imports this planning adds on top of the module's own epoch.

        The rewritten text replay adds only this delta, never the module's
        original statements (a cross-epoch replay glues the class header).
        Bindings of one package share one import statement.

        Returns:
            One import per importing package.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        grouped: dict[str, list[str]] = {}
        for binding in bindings:
            grouped.setdefault(packages[binding], []).append(binding)
        return [
            runtime.from_import(
                package, 0, tuple((binding, None) for binding in sorted(names))
            )
            for package, names in grouped.items()
        ]

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
            bindings = frozenset(
                alias or name
                for imported in added_imports
                for name, alias in imported.names_and_aliases
            )
            for statement in native_imports.imports:
                before = statement.import_info
                if FlextInfraUtilitiesRopeRuntimeTypes.from_import_info(before):
                    statement.import_info = runtime.from_import(
                        before.module_name,
                        before.level,
                        tuple(
                            (name, alias)
                            for name, alias in before.names_and_aliases
                            if (alias or name) not in bindings
                        ),
                    )
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
        retained: Sequence[tuple[str, p.Infra.RopePyObject]],
        step: int,
    ) -> p.Result[str]:
        """Fill the module skeleton from the projected namespace layout.

        Returns:
            Rendered source or the template owner's original typed failure.

        """
        current, actual = projected
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
            (current, actual),
            source,
            (layout, end),
            step,
            retained,
        )
        class_line = scope.get_start()
        desired_bases = tuple(expression for expression, _base in retained)
        unchanged_header = desired_bases == tuple(
            source[first:last] for first, last in layout.bases
        )
        dropped = frozenset(
            source[first:last]
            for first, last in layout.bases
            if source[first:last] not in desired_bases
        )
        context = m.Infra.ModuleSkeletonRenderContext(
            class_name=actual.get_name(),
            base_class=None,
            base_module=None,
            module_prefix=cls._facade_prune_dropped_imports(
                source[: layout.region[0]],
                dropped,
                source[layout.region[0] :].replace(
                    source[layout.region[0] : layout.header_end], ""
                )
                + " ".join(desired_bases),
            ),
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
            managed_header=None
            if source.startswith(c.Infra.AUTOGEN_HEADER)
            else c.Infra.AUTOGEN_HEADER,
        )
        return cls.generate_module_skeleton(context=context)

    @staticmethod
    def _facade_prune_dropped_imports(
        prefix: str, dropped: frozenset[str], remainder: str
    ) -> str:
        """Remove the header imports of bases the composition no longer lists.

        A base dropped from the class header (redundant through another base's
        MRO) leaves its import unused; an import that the rest of the module
        still reads stays. Only plain names imported by ``from x import ...``
        are pruned, by their own source segment, so the remaining statement
        keeps its authored layout.

        Returns:
            The module prefix without the dropped bases' unused imports.

        """
        # Usage outside the import statements: the rest of the module plus the
        # prefix itself (an enclosing facade header lives before the layout).
        usage = (
            re.sub(
                r"(?ms)^(?:from [\w.]+ import \(.*?\)|(?:from|import) [^\n]*)$",
                "",
                prefix,
            )
            + remainder
        )
        names = {
            name
            for name in dropped
            if name.isidentifier()
            and re.search(rf"\b{re.escape(name)}\b", usage) is None
        }
        for name in sorted(names):
            # One alias per line inside a parenthesized ``from`` import.
            prefix = re.sub(
                rf"(?m)^[ \t]+{re.escape(name)},?[ \t]*\n(?=(?:[ \t]+\w[^\n]*\n)*\))",
                "",
                prefix,
            )
            # An alias inside a single-line ``from`` import.
            prefix = re.sub(
                rf"(?m)^(from [\w.]+ import [^\n(]*?)\b{re.escape(name)}\b, ",
                r"\1",
                prefix,
            )
            prefix = re.sub(
                rf"(?m)^(from [\w.]+ import [^\n(]*?), {re.escape(name)}\b(?=[ \t]*$)",
                r"\1",
                prefix,
            )
            prefix = re.sub(
                rf"(?m)^from [\w.]+ import {re.escape(name)}[ \t]*\n", "", prefix
            )
        return re.sub(r"(?m)^from [\w.]+ import \(\s*\)[ \t]*\n", "", prefix)

    @classmethod
    def _facade_body_source(
        cls,
        projected: tuple[p.Infra.RopeSourceModule, p.Infra.RopeSourceClass],
        source: str,
        frame: tuple[p.Infra.RopeSourceClassLayout, int],
        step: int,
        retained: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> str:
        """Split the namespace body, retiring obsolete generated bindings.

        A managed body whose every statement retired keeps a ``pass`` so the
        namespace stays a valid class body.

        Returns:
            The verbatim body text without its retired statements.

        """
        current, actual = projected
        layout, end = frame
        scope = actual.get_scope()
        index = current.get_source_binding_index()
        retired = (
            cls._facade_retired_bindings(index, actual, source, retained)
            | cls._facade_retired_publications((current, scope), retained)
            if source.startswith(c.Infra.AUTOGEN_HEADER)
            else frozenset[tuple[int, int]]()
        )
        body_source = cls._facade_retained_body(
            index, scope, source, (layout.header_end, end), retired
        )
        if retired and not body_source.strip():
            class_indent = source[
                current.lines.get_line_start(scope.get_start()) : layout.region[0]
            ]
            return f"\n{class_indent}{' ' * step}pass"
        return body_source

    @staticmethod
    def facade_self_publications(
        module: p.Infra.RopeSourceModule, scope: p.Infra.RopeScope
    ) -> dict[str, tuple[tuple[int, int], p.Infra.RopePyName | None]]:
        """Read the ``Name = Name`` publications of one class body.

        A class-body ``Name = Name`` (annotated or not) reads ``Name`` from
        the module scope, so its target is that module binding, never the
        class attribute the statement assigns.

        Returns:
            Each publication name with its statement region and module binding.

        """
        source = module.source_code
        names = module.get_scope().get_names()
        publications: dict[str, tuple[tuple[int, int], p.Infra.RopePyName | None]] = {}
        for declaration in module.get_source_binding_index().assignment_layouts(scope):
            if declaration.value is None or len(declaration.targets) != 1:
                continue
            name = declaration.targets[0][0]
            begin, end = declaration.value
            if source[begin:end] == name:
                publications[name] = (declaration.region, names.get(name))
        return publications

    @classmethod
    def _facade_retired_publications(
        cls,
        projected: tuple[p.Infra.RopeSourceModule, p.Infra.RopeScope],
        retained: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> frozenset[tuple[int, int]]:
        """Find the ``Name = Name`` publications this composition retires.

        A generated publication is obsolete once its module binding no longer
        resolves to a class (its declaration moved into a part class) or once
        a retained base reaches the name through its MRO.

        Returns:
            The statement regions of every obsolete publication.

        """
        module, scope = projected
        types = FlextInfraUtilitiesRopeRuntimeTypes
        retired: set[tuple[int, int]] = set()
        for name, (region, binding) in cls.facade_self_publications(
            module, scope
        ).items():
            target = None if binding is None else binding.get_object()
            if not types.abstract_class(target) or any(
                types.py_class(base)
                and (
                    name in base.get_attributes()
                    or (
                        types.py_class(target)
                        and any(
                            cls._same_facade_target(ancestor, target)
                            for ancestor in base.get_mro()[1:]
                        )
                    )
                )
                for _expression, base in retained
            ):
                retired.add(region)
        return frozenset(retired)

    @classmethod
    def _facade_retired_bindings(
        cls,
        index: p.Infra.RopeSourceBindingIndex,
        namespace: p.Infra.RopeSourceClass,
        source: str,
        retained: Sequence[tuple[str, p.Infra.RopePyObject]],
    ) -> frozenset[tuple[int, int]]:
        """Retire generated class aliases inherited from their declared owner.

        Only a managed (generated) facade body is projection: a binding that
        reads a member off an inherited owner (``Name = Owner.Member``) is
        already supplied by composition or is obsolete residue of an earlier
        generation. An authored body stays verbatim.

        Returns:
            The statement regions of every obsolete generated binding.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        inherited = {
            ancestor
            for _expression, base in retained
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
            if any(
                owner is ancestor
                or (
                    types.py_class(ancestor)
                    and cls._same_facade_target(owner, ancestor)
                )
                for ancestor in inherited
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
    def _facade_retained_body(
        index: p.Infra.RopeSourceBindingIndex,
        scope: p.Infra.RopeScope,
        source: str,
        span: tuple[int, int],
        retired: frozenset[tuple[int, int]],
    ) -> str:
        """Keep the authored body span without the lines of retired bindings.

        Returns:
            The verbatim body text without its retired statements.

        """
        cursor, end = span
        parts: list[str] = []
        for declaration in index.assignment_layouts(scope):
            if declaration.region not in retired:
                continue
            line_start = source.rfind("\n", 0, declaration.region[0]) + 1
            line_end = source.find("\n", declaration.region[1])
            parts.append(source[cursor:line_start])
            cursor = len(source) if line_end < 0 else line_end + 1
        parts.append(source[cursor:end])
        return "".join(parts)

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
    def plan_component_consumers(
        cls,
        root: Path,
        *,
        source_project: p.Infra.RopeProject,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
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
        components = cls._component_methods(claims)
        declared = {plan.path: plan for plan in declared_files}
        plans: list[p.Infra.CodegenFilePlan] = []
        for resource in source_project.get_python_files():
            path = Path(resource.real_path)
            module = cls._consumer_module(source_project, path)
            calls = cls._component_calls(module, claims, components)
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
        selection: tuple[str, frozenset[str] | None],
        source_project: p.Infra.RopeProject,
    ) -> Sequence[tuple[p.Infra.RopeClassObject, str]]:
        """Keep component receivers only when their effective method is identical.

        Returns:
            The resulting ``Sequence[tuple[p.Infra.RopeClassObject, str]]``.

        """
        members = FlextInfraUtilitiesFacadeMembers
        target, referenced_paths = selection
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
                and (
                    referenced_paths is None or f"{target}.{member}" in referenced_paths
                )
            )
        return tuple(composed)

    @classmethod
    def _component_claims(
        cls,
        project: Path,
        *,
        source_project: p.Infra.RopeProject,
        referenced_paths: frozenset[str] | None = None,
    ) -> t.Infra.FacadeComponentClaims:
        """Retain native receiver identities while discovering public composition.

        Returns:
            Each claimed component method with its composing facade targets.

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
                if referenced_paths is not None and not any(
                    path == target or path.startswith(f"{target}.")
                    for path in referenced_paths
                ):
                    continue
                for identity in cls._composed_methods(
                    root,
                    letters,
                    holder,
                    selection=(target, referenced_paths),
                    source_project=source_project,
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
        claims: t.Infra.FacadeComponentClaims,
        components: Mapping[str, frozenset[str]],
    ) -> Sequence[tuple[p.Infra.SourceRewrite, str, str]]:
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
        textual occurrence of the same method name. ``components`` names each
        claimed component's methods (``_component_methods``).

        Returns:
            Native source changes, original references and public destinations.

        Raises:
            TypeError: If component consumer has no native module tree.

        """
        source = module.source_code
        methods = cls._component_candidate_methods(source, components)
        if not methods:
            return ()
        words = FlextInfraUtilitiesRopeRuntimeModules.runtime_callable(
            "rope.base.worder", "Worder"
        )(source)
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Component references require native word regions"
            raise TypeError(message)
        index = module.get_source_binding_index()
        references: dict[tuple[int, int], tuple[p.Infra.SourceRewrite, str, str]] = {}
        for start, method in cls._claimed_name_offsets(source, methods):
            first, last = words.get_primary_range(start)
            prefix, name, offset = words.get_splitted_primary_before(last)
            context = index.context_at(offset)
            if (
                not prefix
                or name != method
                or context.access != "read"
                or context.role == "class-base"
                or not cls._component_receiver_candidate(context.environment, prefix)
            ):
                continue
            destination = cls._component_destination(
                module, prefix, method, offset, claims
            )
            if destination is not None:
                references[first, last] = (
                    m.Infra.SourceRewrite(start=first, end=last, text=destination),
                    source[first:last],
                    destination,
                )
        return tuple(value for _region, value in sorted(references.items()))

    @staticmethod
    def _claimed_name_offsets(
        source: str, methods: frozenset[str]
    ) -> Generator[tuple[int, str]]:
        """Yield the offset of every name token spelling a claimed method.

        One tokenization serves every method of the module: it yields exactly
        the offsets the native lexical finder (rope ``Finder`` without
        filters) yields per method, whose token search keeps the NAME tokens
        equal to its name. The tokenizer emits the replacement-field names of
        an f-string as NAME tokens of their own (PEP 701).

        Yields:
            Each claimed name's source offset and the name, in source order.

        """
        line_starts = [0]
        for line in source.splitlines(keepends=True):
            line_starts.append(line_starts[-1] + len(line))
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NAME and token.string in methods:
                row, column = token.start
                yield line_starts[row - 1] + column, token.string

    @staticmethod
    def _component_methods(
        claims: t.Infra.FacadeComponentClaims,
    ) -> Mapping[str, frozenset[str]]:
        """Group the claimed methods by the name of their component class.

        Returns:
            Each claimed component's name with its claimed methods.

        """
        methods: dict[str, set[str]] = {}
        for component, method in claims:
            methods.setdefault(component.get_name(), set()).add(method)
        return {name: frozenset(owned) for name, owned in methods.items()}

    @staticmethod
    def _component_candidate_methods(
        source: str, components: Mapping[str, frozenset[str]]
    ) -> frozenset[str]:
        """Select the claimed methods whose component this module names.

        A lexical receiver names its component class in the module itself:
        through the import, the declaration or the bare alias the receiver
        proof accepts. A module that never spells a component's name holds no
        receiver of it, so its methods need no occurrence search there.

        Returns:
            The methods of every component the source names.

        """
        return frozenset(
            method
            for name, owned in components.items()
            if name in source
            for method in owned
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
        claims: t.Infra.FacadeComponentClaims,
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
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_parsed_module(
            engine.get_pymodule(resource)
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = f"component consumer has no native source module: {path}"
            raise TypeError(message)
        return module

    @staticmethod
    def _call_witness(
        rewrite: p.Infra.SourceRewrite,
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
        calls: Sequence[tuple[p.Infra.SourceRewrite, str, str]],
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
    def codemod_facade_census_facts(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> p.Infra.FacadeCensus:
        """Read the project's facade census once from the injected snapshot.

        The member, ownership and component renderers of one rendering share
        it as their facts: the lineage, the foreign member references and
        names, the misplaced members and the component claims are derived a
        single time over the snapshot's sources instead of once per renderer.
        Member classification shares one captured-source resolver across the
        census and misplaced-member queries, within this unchanged view only.

        Returns:
            The census bound to ``snapshot`` and the absolute project root.

        """
        root = project.absolute()
        members = FlextInfraUtilitiesFacadeMembers
        engine = snapshot.engine
        resolver_factory = (
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver_factory(
                engine,
                sources=FlextInfraUtilitiesWorkspaceSnapshot.project_captured_sources(
                    engine
                ),
            )
        )
        cache: MutableMapping[
            int,
            tuple[
                p.Infra.RopePyName | p.Infra.RopePyObject,
                c.Infra.FacadeMemberKind,
            ],
        ] = {}
        referenced, reference_paths = members.facade_references(snapshot, root)
        lineage, references, exposed = members.facade_member_census(
            root,
            source_project=engine,
            resolver_factory=resolver_factory,
            referenced=referenced,
            cache=cache,
        )
        return m.Infra.FacadeCensus(
            snapshot=snapshot,
            project=root,
            lineage=lineage,
            references=references,
            exposed=exposed,
            missing=members.facade_misplaced_members(
                FlextInfraUtilitiesPyprojectConform.project_package_name(root),
                source_project=engine,
                resolver_factory=resolver_factory,
                cache=cache,
            ),
            claims=cls._component_claims(
                root,
                source_project=engine,
                referenced_paths=reference_paths,
            ),
        )

    @classmethod
    def codemod_facade_component_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        census: p.Infra.FacadeCensus,
    ) -> Mapping[str, t.JsonMapping]:
        """Render native-proven component calls through their bound public facade.

        Calls share one rule per consumer file and public namespace, with exact
        native call-range alternatives. Bindings elect both receivers before
        rendering; spelling alone never admits a shadowed name. Constructors,
        class bases and entity references remain unchanged. ``census`` is the
        rendering's facade census.

        Returns:
            Rules for the identity-proven calls in the captured project sources.

        """
        root = FlextInfraUtilitiesFacadeMembers.facade_census_root(
            census, snapshot, project
        )
        claims = census.claims
        if not claims:
            return {}
        components = cls._component_methods(claims)
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
            groups: dict[str, list[tuple[p.Infra.SourceRewrite, str, str]]] = {}
            for witness in cls._component_calls(module, claims, components):
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
        installed. A distribution the project itself names is a domain
        capability, not a leak: a package or subpackage of the project with
        that name (an importable directory under its own package roots, never the
        tests tier), or one declared in the repository's ``domain_capabilities``,
        is removed, as is every declared stdlib backport.

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
        artifacts = FlextInfraUtilitiesProjectManagedArtifacts
        declared = artifacts.load_repository_declaration_inputs(
            root, source_project=snapshot.engine
        ).unwrap()

        def normalized(name: str) -> str:
            return name.lower().replace("-", "_").replace(".", "_")

        exempt = {
            normalized(name)
            for name in (
                *declared.spec.domain_capabilities,
                *config.Infra.tooling.lazy_init.stdlib_backports,
            )
        }
        resolved = root.resolve()
        tiers = c.Infra.NON_PUBLIC_LAZY_ROOTS
        package_roots = {
            base / name
            for name in FlextInfraUtilitiesCodemodNative.codemod_own_package_names(root)
            if name not in tiers
            for base in (resolved, resolved / c.Infra.DEFAULT_SRC_DIR)
        }
        exempt.update(
            normalized(part)
            for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
                snapshot, root
            )
            if path.name == c.Infra.INIT_PY
            for package_root in package_roots
            if path.parent.is_relative_to(package_root)
            for part in path.parent.relative_to(package_root).parts
        )
        return tuple(
            sorted({
                distribution
                for module in native.codemod_imported_top_modules(snapshot, root)
                if module not in known and not module.startswith("_")
                for distribution in map(normalized, providers.get(module, ()))
                if distribution not in exempt
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
