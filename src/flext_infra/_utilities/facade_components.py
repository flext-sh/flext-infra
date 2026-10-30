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
from collections.abc import Mapping, Sequence
from importlib.metadata import packages_distributions
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
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
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesTypesRopeRuntime,
)
from flext_infra._utilities._rope._analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._rope._analysis.importstate import (
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesFacadeComponents:
    """Derive component-to-namespace references and render their relocation."""

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
            module = runtime.require_source_object(
                project.get_pymodule(runtime.file_resource_at(project, path))
            )
            exported = (
                FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                    module
                )
            )
            for scope in module.get_scope().get_scopes():
                owner = scope.pyobject
                if not FlextInfraUtilitiesTypesRopeRuntime.py_class(owner):
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
    def family_subfacade_owners(
        cls,
        project: p.Infra.RopeProject,
        directory: Path,
    ) -> list[tuple[Path, str]]:
        """Elect actual compositions by native base and publication identity.

        Returns:
            Maximal native owners at the canonical sibling precedence.

        """
        types = FlextInfraUtilitiesTypesRopeRuntime
        canonical = directory.parent / f"{directory.name.lstrip('_')}.py"
        elected: list[tuple[Path, p.Infra.RopeSourceClass]] = []
        for path, owner in (
            *cls.facade_component_declarations(project, directory.parent),
            *cls.facade_component_declarations(project, directory),
        ):
            index = owner.get_module().get_source_binding_index()
            suppliers = tuple(owner.get_superclasses())
            if not any(
                types.py_class(supplier)
                and (resource := supplier.get_module().get_resource()) is not None
                and Path(resource.real_path).parent == directory
                for supplier in suppliers
            ):
                suppliers = (
                    *suppliers,
                    *(
                        binding.value_binding.get_object()
                        for declaration in index.assignment_layouts(owner.get_scope())
                        if declaration.targets
                        and declaration.targets[0][0] != c.Infra.MODEL_CONFIG_ATTRIBUTE
                        for binding in index.assignment_layouts(
                            owner.get_scope(),
                            name=declaration.targets[0][0],
                            resolve_values=True,
                        )
                        if binding.region == declaration.region
                        and binding.value_binding is not None
                        and types.py_class(binding.value_binding.get_object())
                    ),
                )
            origins = {
                Path(resource.real_path).parent
                for supplier in suppliers
                if types.py_class(supplier)
                and supplier is not owner
                and (resource := supplier.get_module().get_resource()) is not None
            }
            if directory in origins and (
                path == canonical
                or len({origin for origin in origins if origin.name.startswith("_")})
                == 1
            ):
                elected.append((path, owner))
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
                other is not owner and owner in other.get_mro()[1:]
                for other_path, other in elected
                if (other_path == canonical, other_path.parent == directory) == priority
            )
        ]

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
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesTypesRopeRuntime
        resource = runtime.file_resource_at(project, path)
        module = runtime.require_source_object(
            project.get_pymodule(resource), "facade component source"
        )
        published = FlextInfraUtilitiesRopeAnalysisImportState.published_facade_owner(
            project, resource
        )
        name = (
            owner_name
            if owner_name is not None
            else (published[1] if published is not None else None)
        )
        if name is None or name not in module.get_attributes():
            message = f"Facade has no native published class: {path}"
            return r[str].fail(message)
        owner = module.get_attributes()[name].get_object()
        if not types.py_class(owner):
            message = f"Facade publication is not a source class: {path}:{name}"
            return r[str].fail(message)
        nested = tuple(
            scope.pyobject
            for scope in owner.get_scope().get_scopes()
            if types.py_class(scope.pyobject)
        )
        payload = FlextInfraUtilitiesDeclarationPayload
        entity_bases = tuple(
            payload.identity_name(project, identity).get_object()
            for identity in ("enum.Enum", "pydantic.BaseModel", "typing.Protocol")
        )
        namespaces = tuple(
            child
            for child in nested
            if not any(base in entity_bases for base in child.get_mro())
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
                    and (resource := base.get_module().get_resource()) is not None
                    and Path(resource.real_path).is_relative_to(directory)
                    for base in child.get_superclasses()
                )
            )
        )
        if len(namespaces) > 1:
            message = f"Competing inherited facade namespaces: {path}"
            return r[str].fail(message)
        namespace = namespaces[0] if namespaces else owner
        index = module.get_source_binding_index()
        layout = index.class_layout(namespace.get_scope())
        source = module.source_code
        bases: list[tuple[str, p.Infra.RopePyObject]] = []
        for (start, end), binding in layout.base_bindings:
            if binding is None:
                message = f"Unresolved facade base: {path}:{source[start:end]}"
                return r[str].fail(message)
            bases.append((source[start:end], binding.get_object()))
        assignments = tuple(
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
        aliases = {
            target_name: assignment.value_binding.get_object()
            for assignment in assignments
            if assignment.value_binding is not None
            for target_name, _region in assignment.targets
        }
        admitted: list[tuple[Path, p.Infra.RopeSourceClass]] = []
        nominal: list[p.Infra.RopeSourceClass] = []
        for provider_path, provider in cls.facade_component_declarations(
            project, directory
        ):
            ancestry = provider.get_mro()
            if any(ancestor in entity_bases for ancestor in ancestry):
                nominal.append(provider)
                continue
            if family is c.Infra.FacadeFamily.M and provider in aliases.values():
                continue
            if family is c.Infra.FacadeFamily.U:
                methods = tuple(
                    scope.pyobject
                    for scope in provider.get_scope().get_scopes()
                    if types.py_function(scope.pyobject)
                )
                if any(
                    method.get_kind() not in {"classmethod", "staticmethod"}
                    for method in methods
                ):
                    nominal.append(provider)
                    continue
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
                if inherited_instance or not meaningful:
                    nominal.append(provider)
                    continue
                if not payload.utility_namespace_declaration(project, provider):
                    message = (
                        "Utility provider has an unresolved namespace storage role: "
                        f"{provider_path}:{provider.get_name()}"
                    )
                    return r[str].fail(message)
            admitted.append((provider_path, provider))
        maximal = tuple(
            (provider_path, provider)
            for provider_path, provider in admitted
            if not any(
                other is not provider and provider in other.get_mro()[1:]
                for _, other in admitted
            )
        )
        imports = runtime.module_imports_for_pymodule(project, module)
        package = FlextInfraUtilitiesProjectDiscovery.package_name_for_dir(
            directory, project_root=Path(project.root.real_path), source_project=project
        )
        retained = [
            (expression, base)
            for expression, base in bases
            if not any(base in provider.get_mro()[1:] for _, provider in maximal)
        ]
        for _provider_path, provider in maximal:
            if any(base is provider for _expression, base in retained):
                continue
            binding = provider.get_name()
            occupied = module.get_scope().get_names().get(binding)
            if occupied is not None and occupied.get_object() is not provider:
                message = f"Occupied facade provider binding: {path}:{binding}"
                return r[str].fail(message)
            imports.add_import(runtime.from_import(package, 0, ((binding, None),)))
            retained.append((binding, provider))
        rewrites: list[m.Infra.SourceRewrite] = []
        if tuple(expression for expression, _ in retained) != tuple(
            expression for expression, _ in bases
        ):
            if layout.bases:
                first, last = layout.bases[0][0], layout.bases[-1][1]
                replacement = ", ".join(expression for expression, _ in retained)
            elif layout.arguments_region is not None:
                first = last = layout.arguments_region[0]
                replacement = ", ".join(expression for expression, _ in retained)
                if layout.keywords:
                    replacement += ", "
            else:
                first = last = layout.bases_insertion_offset
                replacement = (
                    "(" + ", ".join(expression for expression, _ in retained) + ")"
                )
            rewrites.append(
                m.Infra.SourceRewrite(start=first, end=last, text=replacement)
            )
        missing = tuple(
            provider for provider in nominal if provider not in aliases.values()
        )
        if missing:
            body_line = module.lines.get_line_number(layout.body[0])
            indent = source[module.lines.get_line_start(body_line) : layout.body[0]]
            if indent.strip():
                class_line = namespace.get_scope().get_start()
                prefix = source[
                    module.lines.get_line_start(class_line) : layout.region[0]
                ]
                step = u.type_adapter(int).validate_python(
                    runtime.runtime_callable("rope.refactor.sourceutils", "get_indent")(
                        project
                    ),
                    strict=True,
                )
                indent = prefix + " " * step
                rewrites.append(
                    m.Infra.SourceRewrite(
                        start=layout.body[0], end=layout.body[0], text="\n" + indent
                    )
                )
            publications: list[str] = []
            for provider in missing:
                published_name = provider.get_name()
                occupied = namespace.get_scope().get_defined_names().get(published_name)
                if occupied is not None:
                    message = (
                        f"Occupied nominal facade publication: {path}:{published_name}"
                    )
                    return r[str].fail(message)
                imported = module.get_scope().get_names().get(published_name)
                if imported is not None and imported.get_object() is not provider:
                    message = f"Occupied nominal facade import: {path}:{published_name}"
                    return r[str].fail(message)
                imports.add_import(
                    runtime.from_import(package, 0, ((published_name, None),))
                )
                publications.append(
                    f"{indent}{published_name}: TypeAlias = {published_name}"
                )
            imports.add_import(runtime.from_import("typing", 0, (("TypeAlias", None),)))
            insertion = module.lines.get_line_end(
                module.lines.get_line_number(layout.body[1])
            )
            rewrites.append(
                m.Infra.SourceRewrite(
                    start=insertion,
                    end=insertion,
                    text="\n" + "\n".join(publications),
                )
            )
        for assignment in assignments:
            if (
                assignment.value_binding is None
                or not types.abstract_class(assignment.value_binding.get_object())
                or assignment.value is None
                or len(assignment.targets) != 1
                or assignment.type_parameters
            ):
                continue
            if assignment.annotation is not None:
                first, last = assignment.annotation
                annotation = runtime.expression_name(
                    index.context_at(first).environment, source[first:last]
                )
                if annotation is not None and runtime.same_name(
                    annotation,
                    runtime.qualified_name(project, "TypeAlias", module_name="typing"),
                ):
                    continue
            target, _region = assignment.targets[0]
            first, last = assignment.value
            imports.add_import(runtime.from_import("typing", 0, (("TypeAlias", None),)))
            rewrites.append(
                m.Infra.SourceRewrite(
                    start=assignment.region[0],
                    end=assignment.region[1],
                    text=f"{target}: TypeAlias = {source[first:last]}",
                )
            )
        if rewrites:
            source = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                resource, source, rewrites
            ).new_contents
        declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path), (), {path: source}, source_project=project
        )
        with project.source_view(
            declared_files=declared, additional_source_folders=None
        ):
            candidate = runtime.require_source_object(project.get_pymodule(resource))
            changes = runtime.module_imports_for_pymodule(project, candidate)
            for statement in imports.imports:
                changes.add_import(statement.import_info)
            changes.remove_duplicates()
            changes.sort_imports()
            source = changes.get_changed_source()
        return r[str].ok(
            source
            if source.startswith(c.Infra.AUTOGEN_HEADER)
            else (f"{c.Infra.AUTOGEN_HEADER}\n{source}")
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

        Returns:
            Exact native assignment edits with their original physical witnesses.

        Raises:
            ValueError: A published alias remains consumed or changes callable identity.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesTypesRopeRuntime
        publications: dict[
            tuple[p.Infra.RopeClassObject, str], p.Infra.RopeClassObject
        ] = {}
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for path in paths:
            module = runtime.require_source_object(
                project.get_pymodule(runtime.file_resource_at(project, path))
            )
            if not module.source_code.startswith(c.Infra.AUTOGEN_HEADER):
                continue
            index = module.get_source_binding_index()
            rewrites: list[m.Infra.SourceRewrite] = []
            for owner_scope in module.get_scope().get_scopes():
                scopes = (owner_scope, *owner_scope.get_scopes())
                for scope in scopes:
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
                        binding = assignment.value_binding
                        if binding is None or len(assignment.targets) != 1:
                            continue
                        target = binding.get_object()
                        if not types.py_class(target) or target not in ancestry[1:]:
                            continue
                        if not FlextInfraUtilitiesDeclarationPayload.utility_behavior_provider(
                            project, target
                        ):
                            continue
                        for name, member in target.get_attributes().items():
                            if name.startswith("_") or not types.py_function(
                                member.get_object()
                            ):
                                continue
                            effective = owner.get_attributes().get(name)
                            if (
                                effective is None
                                or effective.get_object() is not member.get_object()
                            ):
                                message = (
                                    f"Composed callable identity differs: {path}:{name}"
                                )
                                raise ValueError(message)
                        publications[owner, assignment.targets[0][0]] = target
                        rewrites.append(
                            m.Infra.SourceRewrite(
                                start=assignment.region[0],
                                end=assignment.region[1],
                                text="",
                            )
                        )
            if rewrites:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=module.source_code,
                        updated_source=FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                            runtime.file_resource_at(project, path),
                            module.source_code,
                            rewrites,
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
        for resource in source_project.get_python_files():
            path = Path(resource.real_path)
            module = cls._consumer_module(source_project, path)
            calls = cls._component_calls(module, claims)
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
                        or not FlextInfraUtilitiesTypesRopeRuntime.py_class(
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
                if not FlextInfraUtilitiesTypesRopeRuntime.py_class(holder):
                    message = f"facade namespace has no native scope: {root}.{target}"
                    raise ValueError(message)
                for nested in holder.get_scope().get_scopes():
                    if nested.get_kind() != "Class":
                        continue
                    value = FlextInfraUtilitiesTypesRopeRuntime.require_class_object(
                        nested.pyobject, f"{root}.{target}"
                    )
                    if not value.get_name().startswith("_"):
                        pending.append((value, f"{target}.{value.get_name()}"))
        return tuple(holders)

    @staticmethod
    def _component_ancestors(
        holder: p.Infra.RopeSourceClass,
    ) -> tuple[p.Infra.RopeClassObject, ...]:
        """Require every ancestor in the holder's native method resolution order.

        Every native entry passes through the strict class guard. An unresolved
        declared base retains its admission failure instead of partial ancestry.

        Returns:
            Every native ancestor once, in method resolution order.

        """
        runtime = FlextInfraUtilitiesTypesRopeRuntime
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
                and FlextInfraUtilitiesTypesRopeRuntime.py_function(
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

        Returns:
            Native source changes, original references and public destinations.

        Raises:
            TypeError: If component consumer has no native module tree.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        words = runtime.runtime_callable("rope.base.worder", "Worder")(
            module.source_code
        )
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Component references require native word regions"
            raise TypeError(message)
        index = module.get_source_binding_index()
        references: dict[tuple[int, int], tuple[m.Infra.SourceRewrite, str, str]] = {}
        queried: set[tuple[str, p.Infra.RopePyObject]] = set()
        for component, method in claims:
            original = component.get_attributes()[method]
            identity = (method, original.get_object())
            if identity in queried:
                continue
            queried.add(identity)
            finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
                module.pycore.project,
                method,
                original,
                imports=False,
                in_hierarchy=True,
            )
            try:
                occurrences = finder.find_occurrences(pymodule=module)
            except TypeError:
                # A inferência de um subscrito do consumidor pode atravessar
                # um alias genérico cujos parâmetros não são TypeVar
                # (contrato do typing): sem ocorrências provadas por este
                # método, o caminho segue vazio — não é falha do consumo.
                continue
            for occurrence in occurrences:
                first, last = occurrence.get_primary_range()
                prefix, name, offset = words.get_splitted_primary_before(last)
                context = index.context_at(offset)
                if (
                    not prefix
                    or name != method
                    or context.access != "read"
                    or context.role == "class-base"
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
        types = FlextInfraUtilitiesTypesRopeRuntime
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
        module = FlextInfraUtilitiesTypesRopeRuntime.require_parsed_module(
            engine.get_pymodule(resource, force_errors=True)
        )
        if not FlextInfraUtilitiesTypesRopeRuntime.source_module(module):
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
