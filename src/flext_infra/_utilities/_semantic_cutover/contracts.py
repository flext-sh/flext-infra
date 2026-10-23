"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import inspect
from collections.abc import Iterator, Mapping
from pathlib import Path

from flext_cli import cli, u
from rope.base.pyobjects import PyObject

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesPrivateImportAncestry,
    FlextInfraUtilitiesPrivateImportFacades,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope_analysis import FlextInfraUtilitiesRopeAnalysisExports
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticCutoverClassScope,
    FlextInfraUtilitiesSemanticCutoverModelFields,
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)
from flext_infra._utilities._semantic_cutover.declaration_retirement import (
    FlextInfraUtilitiesSemanticDeclarationRetirement,
)
from flext_infra._utilities._semantic_cutover.delegations import (
    FlextInfraUtilitiesSemanticDelegations,
)
from flext_infra._utilities._semantic_cutover.family_type_references import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities._semantic_cutover.private_imports import (
    FlextInfraUtilitiesSemanticCutoverPrivateImports,
)


class FlextInfraUtilitiesSemanticContracts(
    FlextInfraUtilitiesSemanticCutoverModelFields
):
    """Reuse the joint semantic loop and immutable Rope source inventory."""

    class _ContractSources(Mapping[Path, str]):
        """Read-only live view of staged updates over authenticated source inputs."""

        def __init__(
            self,
            updates: t.MappingKV[Path, str],
            originals: t.MappingKV[Path, str],
        ) -> None:
            """Retain both source layers by reference without widening their access."""
            self._updates = updates
            self._originals = originals

        def __getitem__(self, path: Path) -> str:
            """Return the staged value when present, otherwise its original input."""
            return (
                self._updates[path] if path in self._updates else self._originals[path]
            )

        def __iter__(self) -> Iterator[Path]:
            """Preserve original key order and append newly staged paths.

            Yields:
                Each source path once, in the source overlay's stable order.

            """
            yield from self._originals
            yield from (path for path in self._updates if path not in self._originals)

        def __len__(self) -> int:
            """Count each path once without materializing or copying source data.

            Returns:
                The number of distinct paths in the live overlay.

            """
            return len(self._originals) + sum(
                path not in self._originals for path in self._updates
            )

    @classmethod
    def _plan_rope_contracts(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Return source-authenticated edits for the normalization phase's rules."""
        return cls.plan_contract_rules(
            workspace,
            sources,
            tuple(
                rule
                for rule in cls.declared_contract_rules(workspace.repository_root)
                if rule.phase == c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION
            ),
        )

    @staticmethod
    def declared_contract_rules(
        repository_root: t.Infra.RopeSourcePath,
    ) -> t.SequenceOf[p.Infra.RopeContractRule]:
        """Load universal and elected repo rules with unique IDs and known families.

        Returns:
            Authenticated rules from the packaged and elected project catalogues.

        Raises:
            ValueError: If a catalogue disappears, IDs collide, or ownership or
                family declarations are invalid.

        """
        packaged = (
            type(config).ssot_config_dir().parent
            / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        )
        roots = dict.fromkeys((
            repository_root.resolve(),
            *FlextInfraUtilitiesProjectDiscovery.discover_rope_project_roots(
                repository_root
            ),
        ))
        catalogues = (
            packaged,
            *(
                root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
                for root in roots
                if root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH != packaged
                and (root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH).is_file()
            ),
        )
        rules: t.MutableSequenceOf[p.Infra.RopeContractRule] = []
        for catalogue in catalogues:
            state = u.Cli.atomic_read_binary_file_state(
                catalogue, required=True
            ).unwrap()
            if state.content is None:
                message = f"Rope contract catalogue disappeared: {catalogue}"
                raise ValueError(message)
            parsed = u.Cli.yaml_parse(state.content.decode(c.DEFAULT_ENCODING)).unwrap()
            declared = m.Infra.RopeContractRules.model_validate_json(
                u.json_mapping_adapter().dump_json(parsed)
            )
            for rule in declared.rules:
                if rule.ownership_transfer is not None and catalogue == packaged:
                    message = (
                        f"{rule.id}: ownership transfer requires its project catalogue"
                    )
                    raise ValueError(message)
                rules.append(rule.model_copy(update={"source_states": (state,)}))
        ids = [rule.id for rule in rules]
        if len(ids) != len(set(ids)):
            message = "duplicate Rope contract rule identities"
            raise ValueError(message)
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        for rule in rules:
            unknown = set(rule.families).difference(families)
            if unknown:
                message = f"{rule.id}: undeclared Rope contract families: {unknown}"
                raise ValueError(message)
        return tuple(rules)

    @classmethod
    def plan_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
        *,
        captured: p.Infra.CodemodSourceEpoch | None = None,
        options: m.Infra.ContractAdmissionOptions | None = None,
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Plan native changes against one authenticated source epoch.

        Returns:
            Source-authenticated edits for the selected native contract rules.

        """
        providers = cls._contract_receiver_sources(workspace, sources, rules, captured)
        items = tuple(
            sorted({**dict(cls._editable_sources(sources)), **providers}.items())
        )
        staged_receivers = frozenset(
            path
            for path in providers
            if sources[path].startswith(c.Infra.AUTOGEN_HEADERS)
        )
        if not items or not rules:
            return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(())
        cls._require_owned_contract_transfers(workspace, rules)
        epoch = (
            captured
            if captured is not None
            else cls._contract_epoch(workspace, sources, rules)
        )
        working, applied, owned_modules = cls._apply_contract_rules(
            workspace,
            sources,
            rules,
            (items, epoch),
            (
                options.annotation_only if options is not None else False,
                options.class_alias_only if options is not None else False,
            ),
        )
        return cls._finish_contract_edits(
            workspace,
            sources,
            rules,
            (items, epoch, staged_receivers, captured is not None),
            (working, applied, owned_modules),
        )

    @staticmethod
    def _contract_receiver_sources(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
        captured: p.Infra.CodemodSourceEpoch | None,
    ) -> t.MutableMappingKV[t.Infra.RopeSourcePath, str]:
        # Elect receivers without making unrelated generated sources editable.
        providers: t.MutableMappingKV[t.Infra.RopeSourcePath, str] = {}
        for rule in rules:
            if rule.ownership_transfer is None and captured is None:
                continue
            for identity in rule.bindings.values():
                binding = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                    workspace.rope_project, identity
                )
                module = binding.get_object().get_module()
                resource = module.get_resource() if module is not None else None
                if resource is None:
                    msg = f"{rule.id}: transfer receiver has no native source"
                    raise ValueError(msg)
                path = Path(resource.real_path).resolve()
                if path in sources:
                    providers[path] = sources[path]
        return providers

    @staticmethod
    def _require_owned_contract_transfers(
        workspace: p.Infra.RopeWorkspaceDsl,
        rules: t.SequenceOf[p.Infra.RopeContractRule],
    ) -> None:
        for rule in rules:
            if rule.ownership_transfer is None:
                continue
            owner = FlextInfraUtilitiesSemanticDeclarationRelocation.contract_rule_root(
                workspace.repository_root, rule
            )
            layout = FlextInfraUtilitiesCodegenNamespace.layout(
                owner,
                rope_project=workspace.rope_project
                if workspace.rope_project.authenticated_sources
                else None,
            )
            if layout is None:
                msg = "ownership transfer requires its declared project namespace"
                raise ValueError(msg)
            if not (
                rule.ownership_transfer[0] == layout.package_name
                or rule.ownership_transfer[0].startswith(f"{layout.package_name}.")
            ):
                message = f"{rule.id}: an external library declaration cannot retire"
                raise ValueError(message)

    @classmethod
    def _apply_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
        context: tuple[tuple[tuple[Path, str], ...], p.Infra.CodemodSourceEpoch],
        restrictions: tuple[bool, bool],
    ) -> tuple[
        t.MutableMappingKV[Path, str],
        t.MutableMappingKV[Path, t.MutableSequenceOf[str]],
        t.MutableMappingKV[str, Path],
    ]:
        working = dict(context[0])
        proposed_sources = cls._ContractSources(working, sources)
        relocation = FlextInfraUtilitiesSemanticDeclarationRelocation
        applied: t.MutableMappingKV[Path, t.MutableSequenceOf[str]] = {}
        project: p.Infra.RopeProject | None = None
        try:
            project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                workspace.rope_project, proposed_sources, captured=context[1]
            )
            owned_modules = {
                FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix()
                        ),
                        path,
                    ),
                ).get_name(): path
                for path, _source in context[0]
                if any(rule.ownership_transfer is not None for rule in rules)
                and path.is_relative_to(workspace.repository_root)
            }
            implementation_owners: t.MutableMappingKV[
                t.Pair[str, str], t.Infra.RopeImplementationPaths
            ] = {}
            for declared_rule in rules:
                if project is None:
                    project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                        workspace.rope_project,
                        proposed_sources,
                        captured=context[1],
                    )
                resources = tuple(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    )
                    for path in working
                )
                templates = cls._field_contract_templates(
                    project, declared_rule, resources
                )
                for pattern, goal in templates:
                    rule = (
                        m.Infra.RopeContractRule.model_validate(
                            declared_rule, from_attributes=True
                        ).model_copy(update={"pattern": pattern, "goal": goal})
                        if declared_rule.defaulted_field
                        else declared_rule
                    )
                    if project is None:
                        project = (
                            FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                                workspace.rope_project,
                                proposed_sources,
                                captured=context[1],
                            )
                        )
                    members = cls._contract_rule_members(
                        project,
                        rule,
                        proposed_sources,
                        (implementation_owners, context[1], working, owned_modules),
                        restrictions,
                    )
                    changed = False
                    for change in members:
                        path = Path(change.resource.real_path).resolve()
                        proposed = relocation.remove_orphaned_imports(
                            project, change.resource, working[path], change.new_contents
                        )
                        if proposed == working[path]:
                            continue
                        working[path] = proposed
                        applied.setdefault(path, []).append(rule.id)
                        changed = True
                    cli.display_text(
                        f"mod: Rope contract {rule.id}: changed_files={len(members)}"
                    )
                    if changed:
                        project.close()
                        project = None
        finally:
            if project is not None:
                project.close()
        return working, applied, owned_modules

    @classmethod
    def _contract_rule_members(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        sources: t.MappingKV[Path, str],
        context: tuple[
            t.MutableMappingKV[t.Pair[str, str], t.Infra.RopeImplementationPaths],
            p.Infra.CodemodSourceEpoch,
            t.MappingKV[Path, str],
            t.MappingKV[str, Path],
        ],
        restrictions: tuple[bool, bool],
    ) -> list[p.Infra.RopeChangeContents]:
        operation = m.Infra.RopeContractRule.model_validate(rule, from_attributes=True)
        if operation.operation == "materialize-delegations":
            return FlextInfraUtilitiesSemanticDelegations.materialize_delegations(
                project, sources, tuple(context[2]), rule.id
            )
        resources = tuple(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            )
            for path in context[2]
        )
        members: list[p.Infra.RopeChangeContents] = []
        for (
            selected_rule,
            selected_resources,
        ) in FlextInfraUtilitiesImportLaw.import_contract_routes(
            project, rule, resources, sources
        ):

            def admit(
                module: p.Infra.RopePyModule,
                match: p.Infra.RopeContractMatch,
                selected_rule: p.Infra.RopeContractRule = selected_rule,
            ) -> bool:
                return cls._admit_contract_restrictions(
                    module, match, restrictions
                ) and (
                    cls._admit_contract_match(
                        project,
                        selected_rule,
                        module,
                        match,
                        context=(
                            context[0],
                            sources,
                            context[3],
                        ),
                    )
                )

            changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                project,
                m.Infra.RopeRestructureRequest(
                    pattern=selected_rule.pattern,
                    goal=selected_rule.goal,
                    arguments=cls._contract_arguments(selected_rule),
                    resources=selected_resources,
                    imports=selected_rule.imports,
                    match_filter=admit,
                ),
            )
            members.extend(
                FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                    changes.changes, f"{rule.id}: invalid Rope content changes"
                ).unwrap()
            )
        return members

    @staticmethod
    def _admit_contract_restrictions(
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        restrictions: tuple[bool, bool],
    ) -> bool:
        first, last = match.get_region()
        references = FlextInfraUtilitiesSemanticFamilyTypeReferences
        if restrictions[0] and not any(
            begin <= first < last <= end
            for begin, end, _line in references.annotation_regions(
                module.source_code, module
            )
        ):
            return False
        if restrictions[1]:
            captured_node = match.get_ast("receiver")
            tree = module.get_ast()
            if not isinstance(tree, ast.Module):
                msg = "class-alias transfer has no native module AST"
                raise TypeError(msg)
            if (
                not any(
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.value is captured_node
                    for node in ast.walk(tree)
                )
                or FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                    module, first
                ).get_kind()
                != c.Infra.RopeScopeKind.CLASS
            ):
                return False
        return True

    @classmethod
    def _finish_contract_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
        context: tuple[
            tuple[tuple[Path, str], ...],
            p.Infra.CodemodSourceEpoch,
            frozenset[Path],
            bool,
        ],
        result: tuple[
            t.MutableMappingKV[Path, str],
            t.MutableMappingKV[Path, t.MutableSequenceOf[str]],
            t.MutableMappingKV[str, Path],
        ],
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        items, epoch, staged_receivers, captured = context
        working, applied, owned_modules = result
        retirement_sources = {**sources, **working}
        retired, providers = (
            FlextInfraUtilitiesSemanticDeclarationRetirement.retire_contract_owners(
                workspace, retirement_sources, rules, epoch, owned_modules
            )
        )
        working.update((path, retirement_sources[path]) for path in working)
        if captured and staged_receivers:
            normalized = cls._normalize_projected_consumers(
                workspace, retirement_sources, epoch, tuple(working), staged_receivers
            )
            items = tuple(
                sorted(
                    {
                        **dict(items),
                        **{path: sources[path] for path in normalized},
                    }.items()
                )
            )
            working.update((path, retirement_sources[path]) for path in normalized)
        for path, original in items:
            if working[path] != original or path in providers:
                applied.setdefault(path, []).append(
                    "completed native ownership transfer"
                )
        inputs = (
            *epoch.snapshot.states,
            *(state for rule in rules for state in rule.source_states),
        )
        return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    retire_file=path in retired,
                    source_states=inputs,
                    changes=tuple(applied[path]),
                )
                for path, source in items
                if source != working[path] or path in providers
            )
        )

    @classmethod
    def _normalize_projected_consumers(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MutableMappingKV[Path, str],
        epoch: p.Infra.CodemodSourceEpoch,
        consumers: t.SequenceOf[Path],
        receivers: frozenset[Path],
    ) -> tuple[Path, ...]:
        """Reuse facade election and import cutover inside the captured source epoch.

        Returns:
            Paths whose projected facade or consumer imports changed.

        Raises:
            ValueError: If the captured project has no declared layout or public
                protocol facade.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        project = runtime.snapshot_project(
            workspace.rope_project, sources, captured=epoch
        )
        changed: list[Path] = []
        try:
            layout = FlextInfraUtilitiesCodegenNamespace.layout(
                workspace.repository_root, rope_project=project
            )
            if layout is None:
                msg = "projected consumers have no elected project layout"
                raise ValueError(msg)
            facade = FlextInfraUtilitiesCodegenFacades.facade_module_path(
                layout.package_dir, "p", project=project, sources=sources
            )
            rendered = FlextInfraUtilitiesCodegenFacades.render_utility_facade(
                layout.package_dir, family="p", project=project, sources=sources
            )
            if facade is None or rendered is None:
                msg = "projected receivers have no canonical public protocol facade"
                raise ValueError(msg)
            if sources[facade] != rendered:
                sources[facade] = rendered
                changed.append(facade)
            project.close()
            project = runtime.snapshot_project(
                workspace.rope_project, sources, captured=epoch
            )
            changed.extend(
                cls._normalize_projected_imports(
                    project,
                    sources,
                    consumers,
                    receivers,
                    (layout.package_name, layout.package_dir, facade),
                )
            )
            return tuple(changed)
        finally:
            project.close()

    @classmethod
    def _normalize_projected_imports(
        cls,
        project: p.Infra.RopeProject,
        sources: t.MutableMappingKV[Path, str],
        consumers: t.SequenceOf[Path],
        receivers: frozenset[Path],
        package: tuple[str, Path, Path],
    ) -> tuple[Path, ...]:
        imports = FlextInfraUtilitiesPrivateImportFacades
        modules = imports.source_modules(sources, ())
        facades = imports.discover(modules)
        bindings, _exports = imports.declared_exports(modules)
        bases = FlextInfraUtilitiesPrivateImportAncestry.class_bases(modules)
        family = (
            package[1]
            / FlextInfraUtilitiesCodegenNamespace.facade_families()["p"].directory
        )
        changed: list[Path] = []
        for path in consumers:
            if path == package[2] or path.is_relative_to(family):
                continue
            module_resource = project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix()
            )
            specs = cls._projected_consumer_specs(
                project,
                module_resource,
                (path, sources[path]),
                (receivers, package[0]),
                (facades, bindings, bases),
            )
            if specs:
                updated, _operations = (
                    FlextInfraUtilitiesSemanticCutoverPrivateImports.rewrite_private_imports(
                        path,
                        sources[path],
                        file_specs=specs,
                        direct_specs={},
                        facades=facades,
                    )
                )
                if updated != sources[path]:
                    sources[path] = updated
                    changed.append(path)
        return tuple(changed)

    @classmethod
    def _projected_consumer_specs(
        cls,
        project: p.Infra.RopeProject,
        module_resource: p.Infra.RopeResource,
        entry: tuple[Path, str],
        receivers: tuple[frozenset[Path], str],
        inventory: tuple[
            t.MappingKV[str, t.VariadicTuple[t.Quad[ast.Module, str, str, str]]],
            t.MappingKV[str, set[str]],
            t.MappingKV[str, t.VariadicTuple[str]],
        ],
    ) -> list[t.Infra.PrivateImportSpec]:
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            project,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                module_resource, entry[0]
            ),
        )
        specs: list[t.Infra.PrivateImportSpec] = []
        native_imports = (
            FlextInfraUtilitiesSemanticDeclarationRelocation.native_import_infos
        )
        for information in native_imports(project, module):
            if not isinstance(information, p.Infra.RopeFromImport):
                continue
            for name, alias in information.names_and_aliases:
                reference = cls._projected_import_reference(
                    project, module, entry, (alias or name, *receivers), inventory
                )
                if reference is None:
                    continue
                imported_module = FlextInfraUtilitiesRopeAnalysis.resolve_import_module(
                    current_package=FlextInfraUtilitiesRopeAnalysis.package_name_for_module(
                        module.get_name(), module_resource
                    ),
                    module_name=information.module_name,
                    level=information.level,
                )
                specs.append((
                    imported_module,
                    name,
                    f"{imported_module}.{name}",
                    receivers[1],
                    reference,
                ))
        return specs

    @classmethod
    def _projected_import_reference(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        entry: tuple[Path, str],
        receiver: tuple[str, frozenset[Path], str],
        inventory: tuple[
            t.MappingKV[str, t.VariadicTuple[t.Quad[ast.Module, str, str, str]]],
            t.MappingKV[str, set[str]],
            t.MappingKV[str, t.VariadicTuple[str]],
        ],
    ) -> str | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        local, receivers, package = receiver
        binding = runtime.expression_name(module.get_scope(), local)
        if binding is None:
            msg = f"consumer import has no native binding: {local} in {entry[0]}"
            raise ValueError(msg)
        owner = binding.get_object().get_module()
        resource = owner.get_resource() if owner is not None else None
        if (
            owner is None
            or resource is None
            or Path(resource.real_path) not in receivers
        ):
            return None
        qualified = f"{owner.get_name()}.{binding.get_object().get_name()}"
        reference = FlextInfraUtilitiesPrivateImportFacades.public_reference(
            owners=inventory[0].get(package, ()),
            package=package,
            qualified=qualified,
            bindings=inventory[1],
            class_bases=inventory[2],
        )
        if reference is None or reference.partition(".")[0] != "p":
            msg = (
                f"projected receiver has no unique public protocol export: {qualified}"
            )
            raise ValueError(msg)
        cls._require_projected_import_identity(
            project, module, entry, (local, binding), (package, reference)
        )
        return reference

    @staticmethod
    def _require_projected_import_identity(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        entry: tuple[Path, str],
        receiver: tuple[str, p.Infra.RopePyName],
        destination: tuple[str, str],
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        references = FlextInfraUtilitiesSemanticFamilyTypeReferences
        path, source = entry
        local, binding = receiver
        package, reference = destination
        primaries = [
            (source[begin:end], runtime.scope_at(module, begin))
            for begin, end in references.reference_regions(source)
        ]
        primaries.extend(
            (value[begin:end], lexical)
            for value, lexical, _line in references.scoped_quoted_type_references(
                source, project, module
            )
            for begin, end in references.reference_regions(value)
        )
        for primary, lexical in primaries:
            root, separator, tail = primary.partition(".")
            if root != local or not runtime.same_name(
                binding, runtime.expression_name(lexical, root)
            ):
                continue
            public = runtime.qualified_name(
                project,
                reference + (f".{tail}" if separator else ""),
                module_name=package,
            )
            if not runtime.same_name(public, runtime.expression_name(lexical, primary)):
                msg = f"public receiver changes native identity: {primary} in {path}"
                raise ValueError(msg)

    @staticmethod
    def _contract_epoch(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
    ) -> p.Infra.CodemodSourceEpoch:
        """Capture the sources and every identity the rules constrain.

        Returns:
            An immutable epoch containing the rules' source identities.

        """
        prefix = c.Infra.ROPE_NAME_CONSTRAINT_PREFIX
        return FlextInfraUtilitiesCodemodProject.identity_source_epoch(
            workspace.rope_project,
            tuple(sources),
            (
                *(
                    value.removeprefix(prefix)
                    for rule in rules
                    for constraint in rule.arguments.values()
                    for value in (
                        (constraint,) if isinstance(constraint, str) else constraint
                    )
                    if value.startswith(prefix)
                ),
                *(identity for rule in rules for identity in rule.bindings.values()),
                *(base for rule in rules for base in rule.model_bases),
                *(origin for rule in rules for origin in rule.readonly_origins),
                *(
                    ".".join(rule.implementation_owner)
                    for rule in rules
                    if rule.implementation_owner is not None
                ),
            ),
        )

    @classmethod
    def _admit_contract_match(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        *,
        context: tuple[
            t.MutableMappingKV[t.Pair[str, str], t.Infra.RopeImplementationPaths],
            t.MappingKV[t.Infra.RopeSourcePath, str],
            t.MappingKV[str, t.Infra.RopeSourcePath] | None,
        ],
    ) -> bool:
        """Prove native receivers, evaluation safety and destination bindings.

        Args:
            project: The rope project containing the module.
            rule: The contract rule being evaluated.
            module: The Python module under consideration.
            match: The specific contract match instance.
            context: A tuple containing the current state of implementation owners,
              sources, and owned modules.

        Returns:
            Whether every native admission proof accepts the captured match.

        Raises:
            ValueError: If the contract cannot be admitted due to assertion lowering
              requirements.

        """
        implementation_owners, sources, owned_modules = context
        if not cls._admit_contract_origin(
            project, rule, module, match, (implementation_owners, sources)
        ) or not cls._admit_contract_call(project, rule, module, match):
            return False
        if rule.receiver_methods and not cls._admitted_factory_receiver(
            project, module, match, rule.receiver_methods
        ):
            return False
        scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
            module, match.get_region()[0]
        )
        if not cls._admit_contract_transfer(
            project, rule, module, match, (scope, owned_modules)
        ) or not cls._admit_contract_scope(project, rule, module, scope):
            return False
        if not cls._admit_readonly_contract(project, rule, match, scope):
            return False
        cls._require_deferred_annotation(project, rule, module, match, (scope, sources))
        cls._require_contract_evaluation(project, rule, module, match, scope)
        if not cls._admitted_unshadowed_builtins(rule, scope):
            if rule.pattern.startswith("assert "):
                message = (
                    f"{rule.id}: assert lowering requires unshadowed builtins "
                    f"in {module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
            return False
        return FlextInfraUtilitiesImportLaw.import_contract_bindings(
            project, rule, module, scope, match.get_region()[0]
        )

    @staticmethod
    def _admit_contract_origin(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        context: tuple[
            t.MutableMappingKV[t.Pair[str, str], t.Infra.RopeImplementationPaths],
            t.MappingKV[t.Infra.RopeSourcePath, str],
        ],
    ) -> bool:
        implementation_owners, sources = context
        resource = module.get_resource()
        if rule.value_default is not None:
            default = match.get_ast(rule.value_default)
            if isinstance(default, ast.Constant) and default.value is Ellipsis:
                return False
        if rule.factory_default is not None:
            factory = match.get_ast(rule.factory_default)
            if isinstance(factory, ast.Constant) and factory.value is None:
                return False
            if rule.readonly_contract is not None and not isinstance(
                factory, ast.Name | ast.Attribute
            ):
                return False
        if rule.implementation_owner is not None:
            identity = rule.implementation_owner
            if identity not in implementation_owners:
                implementation_owners[identity] = (
                    FlextInfraUtilitiesCodemodProject.implementation_owner_modules(
                        project,
                        m.Infra.CodemodContextCondition(
                            variable="OWNER",
                            predicate=c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
                            holds=False,
                            arg=identity,
                        ),
                        sources,
                    )
                )
            if (
                resource is not None
                and Path(resource.real_path) in implementation_owners[identity]
            ):
                return False
        return True

    @classmethod
    def _admit_contract_call(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
    ) -> bool:
        if rule.required_field or rule.defaulted_field or rule.private_attribute:
            if not cls._admitted_field_metadata(project, rule, module, match):
                return False
        elif rule.call_target is not None:
            captured = match.get_ast(rule.call_target)
            tree = module.get_ast()
            if captured is None or not isinstance(tree, ast.AST):
                msg = f"{rule.id}: call target requires an original native AST capture"
                raise ValueError(msg)
            invocation = next(
                (
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and node.func is captured
                ),
                None,
            )
            if invocation is None:
                return False
            return cls._admit_invocation_arguments(rule, invocation)
        elif rule.explicit_arguments:
            message = f"{rule.id}: explicit-argument proof requires a call target"
            raise ValueError(message)
        elif rule.missing_keywords:
            msg_0 = f"{rule.id}: missing-keyword proof requires a call target"
            raise ValueError(msg_0)
        return True

    @staticmethod
    def _admit_invocation_arguments(
        rule: p.Infra.RopeContractRule,
        invocation: ast.Call,
    ) -> bool:
        if rule.explicit_arguments and (
            any(isinstance(argument, ast.Starred) for argument in invocation.args)
            or any(keyword.arg is None for keyword in invocation.keywords)
        ):
            message = f"{rule.id}: expanded arguments have no proven contract"
            raise ValueError(message)
        if rule.missing_keywords:
            if any(
                keyword.arg in rule.missing_keywords for keyword in invocation.keywords
            ):
                return False
            if any(keyword.arg is None for keyword in invocation.keywords):
                message = (
                    f"{rule.id}: expanded keywords cannot prove missing injected ports"
                )
                raise ValueError(message)
        return True

    @staticmethod
    def _admit_contract_transfer(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        context: tuple[
            p.Infra.RopeScope,
            t.MappingKV[str, t.Infra.RopeSourcePath] | None,
        ],
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope, owned_modules = context
        if rule.ownership_transfer is not None:
            if owned_modules is None:
                message = (
                    f"{rule.id}: ownership transfer has no original project inventory"
                )
                raise ValueError(message)
            relocation = FlextInfraUtilitiesSemanticDeclarationRetirement
            original = relocation.contract_transfer_binding(
                project, rule.ownership_transfer, owned_modules
            )
            first, last = match.get_region()
            expression = ast.parse(module.source_code[first:last], mode="eval").body
            selected = (
                expression.func if isinstance(expression, ast.Call) else expression
            )
            actual = runtime.resolve_symbol(scope, selected)
            if original is None:
                # Already-migrated destinations and unrelated homonyms are not
                # original receivers. An unresolved original receiver is not a
                # successful retirement receipt.
                if any(
                    FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                        project,
                        module,
                        match.get_ast(capture),
                        constraints,
                        name=capture,
                    )
                    for capture, constraints in rule.arguments.items()
                ):
                    message = (
                        f"{rule.id}: transferred owner is absent "
                        "but a receiver survives"
                    )
                    raise ValueError(message)
                return False
            unknown = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
                "rope.base.pyobjects", "get_unknown"
            )()
            if actual is None or actual.get_object() == unknown:
                message = (
                    f"{rule.id}: unproven transferred receiver in "
                    f"{module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
            if not runtime.same_name(original, actual):
                return False
        return True

    @classmethod
    def _admit_contract_scope(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if rule.scope_kinds and scope.get_kind() not in rule.scope_kinds:
            return False
        if rule.families and not cls._admitted_family(rule, module):
            return False
        ancestry = FlextInfraUtilitiesDeclarationPayload.class_ancestry(scope.pyobject)
        return not (
            rule.model_bases
            and not any(
                runtime.qualified_name(project, name).get_object() in ancestry
                for name in rule.model_bases
            )
        )

    @staticmethod
    def _admit_readonly_contract(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        match: p.Infra.RopeContractMatch,
        scope: p.Infra.RopeScope,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if rule.readonly_contract is not None:
            if not rule.readonly_origins:
                message = f"{rule.id}: read-only admission requires native origins"
                raise ValueError(message)
            contract = match.get_ast(rule.readonly_contract)
            if not isinstance(contract, ast.expr):
                message = f"{rule.id}: read-only contract has no native expression"
                raise ValueError(message)
            origin = runtime.annotation_origin(project, contract, scope)
            unknown = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
                "rope.base.pyobjects", "get_unknown"
            )()
            if (
                origin is None
                or origin.get_object() == unknown
                or not any(
                    (expected := runtime.qualified_name(project, identity)).get_object()
                    != unknown
                    and runtime.same_name(origin, expected)
                    for identity in rule.readonly_origins
                )
            ):
                return False
        return True

    @classmethod
    def _require_deferred_annotation(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        context: tuple[p.Infra.RopeScope, t.MappingKV[t.Infra.RopeSourcePath, str]],
    ) -> None:
        scope, sources = context
        if rule.deferred_contract is not None:
            captured = match.get_ast(rule.deferred_contract)
            tree = module.get_ast()
            if not isinstance(tree, ast.AST):
                message = "native deferred contract module has no Python syntax tree"
                raise TypeError(message)
            annotation = next(
                (
                    node.annotation
                    for node in ast.walk(tree)
                    if isinstance(node, ast.AnnAssign)
                    and any(part is captured for part in ast.walk(node.annotation))
                ),
                None,
            )
            if annotation is None:
                message = (
                    f"{rule.id}: deferred contract has no complete field annotation"
                )
                raise ValueError(message)
            cls._require_deferred_contract(
                project, rule, module, (scope, annotation, match), sources
            )

    @classmethod
    def _require_contract_evaluation(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        scope: p.Infra.RopeScope,
    ) -> None:
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        if rule.pattern.startswith("assert "):
            source = module.source_code
            region = match.get_region()
            tree = module.get_ast()
            if not isinstance(tree, ast.Module):
                message = f"{rule.id}: assert lowering requires its native module AST"
                raise TypeError(message)
            statement = next(
                (
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Assert)
                    and node.test is match.get_ast("predicate")
                ),
                None,
            )
            message = (
                f"{rule.id}: assert lowering requires a complete standalone statement "
                f"with retained trivia in {module.get_name()}:"
                f"{statement.lineno if statement is not None else scope.get_start()}"
            )
            line_start = source.rfind("\n", 0, region[0]) + 1
            partial_line = (
                source[line_start : region[0]].strip()
                or source[region[1] :].partition("\n")[0].strip()
            )
            if (
                statement is None
                or statement.msg is not match.get_ast("message")
                or (
                    ast.get_source_segment(source, statement)
                    != source[region[0] : region[1]]
                )
                or partial_line
                or source[:line_start].rstrip("\r\n").endswith("\\")
            ):
                raise ValueError(message)
            captures = tuple(
                refactors.semantic_capture_region(match, name)
                for name in ("predicate", "message")
                if match.get_ast(name) is not None
            )
            # Native Restructure retains only captured text and reindents every
            # subsequent line. Never drop trivia or indent a literal's payload.
            for ignored in refactors.ignored_regions(source):
                if region[0] <= ignored[0] < region[1] and (
                    (
                        source[ignored[0] : ignored[1]].startswith("#")
                        and not any(
                            start <= ignored[0] < ignored[1] <= stop
                            for start, stop in captures
                        )
                    )
                    or (
                        line_start < region[0]
                        and len(source[ignored[0] : ignored[1]].splitlines()) > 1
                    )
                ):
                    raise ValueError(message)
        discarded = next(
            (
                capture
                for capture in rule.drops
                if not isinstance(match.get_ast(capture), ast.Constant)
            ),
            None,
        )
        if discarded is not None:
            message = (
                f"{rule.id}: cannot discard authored evaluation of {discarded} "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)
        # Only the capture the goal evaluates again must be free of calls; the
        # rest of the declaration (Annotated metadata, the field call) runs once.
        if rule.repeats is not None and refactors.word_call_regions(
            module.source_code,
            refactors.semantic_capture_region(match, rule.repeats),
        ):
            message = (
                f"{rule.id}: annotation evaluation cannot repeat authored calls "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)
        if rule.repeats is not None and not cls._admitted_repeated_contract(
            scope, match.get_ast(rule.repeats)
        ):
            message = (
                f"{rule.id}: annotation has an unbound enclosing owner; "
                "retain the native factory and fix its declaring source"
            )
            raise ValueError(message)
        if (
            rule.reorders_annotation
            and len(cls._field_reordered_calls(project, rule, module, match)) != 1
        ):
            message = (
                f"{rule.id}: annotation evaluation cannot reorder authored calls "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)

    @classmethod
    def _require_deferred_contract(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        contract: tuple[p.Infra.RopeScope, ast.expr, p.Infra.RopeContractMatch],
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Prove native closure identities without evaluating or unquoting types.

        Raises:
            ValueError: If the field has no proven native resolution.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        field = contract[2].get_ast("field")
        field_binding = (
            runtime.resolve_symbol(contract[0], field)
            if isinstance(field, ast.expr)
            else None
        )
        message = (
            f"{rule.id}: deferred contract has no proven native resolution "
            f"in {module.get_name()}:{contract[0].get_start()}; "
            "fix the declaring source with its actual resolved contract"
        )
        if field_binding is None:
            raise ValueError(message)
        pending = [(contract[1], contract[0], frozenset[str]())]
        metadata: list[tuple[ast.expr, p.Infra.RopeScope]] = []
        visited: set[tuple[str, int]] = set()
        intrinsics = cls._deferred_intrinsics(project, rule)
        while pending:
            current = pending.pop()
            cls._deferred_expression_aliases(
                project,
                current,
                (sources, message, intrinsics),
                metadata,
                (pending, visited),
            )
        if metadata:
            cls._require_idempotent_metadata(
                project, tuple(metadata), field_binding, message, sources
            )

    @staticmethod
    def _deferred_intrinsics(
        project: p.Infra.RopeProject, rule: p.Infra.RopeContractRule
    ) -> tuple[
        t.MappingKV[str, p.Infra.RopePyName],
        tuple[p.Infra.RopePyName, ...],
        t.Infra.RopeNativeObject,
    ]:
        builtin_module = project.get_module("__builtin__")
        names = FlextInfraUtilitiesSemanticContracts._deferred_builtin_names(
            builtin_module
        )
        intrinsic_types = tuple(
            FlextInfraUtilitiesRopeRuntimeModules.qualified_name(project, identity)
            for identity in (
                *rule.readonly_origins,
                "typing.Annotated",
                "typing.Literal",
            )
        )
        unknown = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
            "rope.base.pyobjects", "get_unknown"
        )()
        if not isinstance(unknown, PyObject):
            message = "native unknown sentinel has no Rope object identity"
            raise TypeError(message)
        return names, intrinsic_types, unknown

    @staticmethod
    def _deferred_builtin_names(
        module: p.AttributeProbe,
    ) -> t.MappingKV[str, p.Infra.RopePyName]:
        if not isinstance(module, p.Infra.RopeSemanticModule):
            message = "native builtins module has no semantic module contract"
            raise TypeError(message)
        return module.get_attributes()

    @classmethod
    def _deferred_expression_aliases(
        cls,
        project: p.Infra.RopeProject,
        expression: tuple[ast.expr, p.Infra.RopeScope, frozenset[str]],
        context: tuple[
            t.MappingKV[t.Infra.RopeSourcePath, str],
            str,
            tuple[
                t.MappingKV[str, p.Infra.RopePyName],
                tuple[p.Infra.RopePyName, ...],
                t.Infra.RopeNativeObject,
            ],
        ],
        metadata: list[tuple[ast.expr, p.Infra.RopeScope]],
        state: tuple[
            list[tuple[ast.expr, p.Infra.RopeScope, frozenset[str]]],
            set[tuple[str, int]],
        ],
    ) -> None:
        lexical = expression[1]
        closure: p.Infra.RopeScope | None = lexical
        while closure is not None and closure.get_kind() == c.Infra.RopeScopeKind.CLASS:
            closure = closure.parent
        if closure is None:
            raise ValueError(context[1])
        holder = lexical.pyobject.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder):
            raise ValueError(context[1])
        source = ast.unparse(expression[0])
        tree = ast.parse(source, mode="eval")
        protected = (
            FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_payload_ranges(
                source, project, lexical
            )
        )
        metadata_regions = cls._deferred_metadata_regions(
            project, (source, tree), lexical, metadata, (protected, context[1])
        )
        cls._deferred_reference_aliases(
            project,
            (source, tree, expression[2], metadata_regions),
            (lexical, closure, holder),
            context,
            state,
        )

    @staticmethod
    def _deferred_metadata_regions(
        project: p.Infra.RopeProject,
        syntax: tuple[str, ast.Expression],
        lexical: p.Infra.RopeScope,
        metadata: list[tuple[ast.expr, p.Infra.RopeScope]],
        context: tuple[frozenset[t.Pair[int, int]], str],
    ) -> list[tuple[int, int]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        source, tree = syntax
        protected, message = context
        calls: set[ast.Call] = set()
        regions: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript) or not isinstance(
                node.slice, ast.Tuple
            ):
                continue
            binding = runtime.resolve_symbol(lexical, node.value)
            if binding is None or not runtime.same_name(
                binding, runtime.qualified_name(project, "typing.Annotated")
            ):
                continue
            for item in node.slice.elts[1:]:
                metadata.append((item, lexical))
                text = ast.get_source_segment(source, item)
                if text is None:
                    failure = f"{message}; metadata has no source region"
                    raise ValueError(failure)
                begin = runtime.source_offset(source, item)
                regions.append((begin, begin + len(text)))
                calls.update(
                    child for child in ast.walk(item) if isinstance(child, ast.Call)
                )
        FlextInfraUtilitiesSemanticContracts._require_deferred_evaluation(
            syntax, protected, calls, message
        )
        return regions

    @staticmethod
    def _require_deferred_evaluation(
        syntax: tuple[str, ast.Expression],
        protected: frozenset[t.Pair[int, int]],
        calls: set[ast.Call],
        message: str,
    ) -> None:
        source, tree = syntax
        for (
            begin,
            end,
            _metadata,
        ) in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(source):
            if FlextInfraUtilitiesSemanticFamilyTypeReferences.string_constant(
                source[begin:end]
            ) is not None and not any(
                first <= begin and end <= last for first, last in protected
            ):
                failure = f"{message}; quoted type identity is unresolved"
                raise ValueError(failure)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if node not in calls:
                failure = f"{message}; authored evaluation cannot repeat"
                raise ValueError(failure)

    @classmethod
    def _deferred_reference_aliases(
        cls,
        project: p.Infra.RopeProject,
        syntax: tuple[str, ast.Expression, frozenset[str], list[tuple[int, int]]],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope, p.Infra.RopeSourceModule],
        context: tuple[
            t.MappingKV[t.Infra.RopeSourcePath, str],
            str,
            tuple[
                t.MappingKV[str, p.Infra.RopePyName],
                tuple[p.Infra.RopePyName, ...],
                t.Infra.RopeNativeObject,
            ],
        ],
        state: tuple[
            list[tuple[ast.expr, p.Infra.RopeScope, frozenset[str]]],
            set[tuple[str, int]],
        ],
    ) -> None:
        source, tree, parameters, regions = syntax
        identifiers = {
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Name | ast.Attribute)
        }
        for (
            begin,
            end,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(source):
            primary = source[begin:end]
            if primary not in identifiers or primary.partition(".")[0] in parameters:
                continue
            alias = cls._deferred_primary_alias(
                project,
                (primary, any(a <= begin and end <= b for a, b in regions)),
                scopes,
                context,
            )
            if alias is not None:
                cls._enqueue_deferred_alias(alias, state[0], state[1], context[1])

    @staticmethod
    def _deferred_primary_alias(
        project: p.Infra.RopeProject,
        reference: tuple[str, bool],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope, p.Infra.RopeSourceModule],
        context: tuple[
            t.MappingKV[t.Infra.RopeSourcePath, str],
            str,
            tuple[
                t.MappingKV[str, p.Infra.RopePyName],
                tuple[p.Infra.RopePyName, ...],
                t.Infra.RopeNativeObject,
            ],
        ],
    ) -> tuple[ast.TypeAlias, p.Infra.RopeScope] | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        primary, metadata = reference
        lexical, closure, holder = scopes
        sources, message, intrinsics = context
        original = runtime.expression_name(lexical, primary)
        actual = runtime.expression_name(closure, primary)
        alias = (
            runtime.annotation_alias_definition(original)
            if original is not None
            else None
        )
        if (
            original is None
            or actual is None
            or (
                FlextInfraUtilitiesSemanticContracts._is_unknown_native_object(
                    actual.get_object(), intrinsics[2]
                )
                and alias is None
            )
            or not runtime.same_name(original, actual)
        ):
            failure = f"{message}; unresolved closure identity: {primary}"
            raise ValueError(failure)
        if metadata:
            return None
        builtin = intrinsics[0].get(primary)
        if builtin is not None and runtime.same_name(builtin, actual):
            return None
        if alias is not None or any(
            runtime.same_name(expected, actual) for expected in intrinsics[1]
        ):
            stable = all(
                FlextInfraUtilitiesCodemodProject.single_reaching_binding(
                    holder, closure, candidate, len(holder.source_code)
                )
                for candidate in dict.fromkeys((primary.partition(".")[0], primary))
            )
        else:
            stable = FlextInfraUtilitiesCodemodProject.stable_binding_chain(
                (project, holder, closure), primary, len(holder.source_code), sources
            )
        if not stable:
            failure = f"{message}; unstable closure binding: {primary}"
            raise ValueError(failure)
        return alias

    @staticmethod
    def _is_unknown_native_object(
        value: p.AttributeProbe,
        unknown: t.Infra.RopeNativeObject,
    ) -> bool:
        if not isinstance(value, PyObject):
            message = "native binding has no Rope object identity"
            raise TypeError(message)
        return (value == unknown) is True

    @staticmethod
    def _enqueue_deferred_alias(
        alias: tuple[ast.TypeAlias, p.Infra.RopeScope],
        pending: list[tuple[ast.expr, p.Infra.RopeScope, frozenset[str]]],
        visited: set[tuple[str, int]],
        message: str,
    ) -> None:
        declaration, owner_scope = alias
        owner = owner_scope.pyobject.get_module()
        if owner is None:
            raise ValueError(message)
        key = (owner.get_name(), declaration.lineno)
        if key in visited:
            return
        visited.add(key)
        parameters: set[str] = set()
        for parameter in declaration.type_params:
            if not isinstance(
                parameter, ast.TypeVar | ast.ParamSpec | ast.TypeVarTuple
            ):
                failure = "native alias has an unknown type parameter"
                raise TypeError(failure)
            parameters.add(parameter.name)
        pending.append((declaration.value, owner_scope, frozenset(parameters)))

    @staticmethod
    def _metadata_constructors(
        project: p.Infra.RopeProject,
        field: p.Infra.RopePyName,
        failure: str,
    ) -> list[tuple[p.Infra.RopePyName, bool]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        # The SDK owns the declarative constraint constructors, not a local name list.
        lookup = runtime.qualified_name(
            project, "pydantic.fields.FieldInfo.metadata_lookup"
        )
        owner, line = runtime.definition_location(lookup)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(owner):
            raise ValueError(failure)
        owner_tree = owner.get_ast()
        if not isinstance(owner_tree, ast.AST):
            message = "native metadata owner has no Python syntax tree"
            raise TypeError(message)
        table = next(
            (
                node
                for node in ast.walk(owner_tree)
                if isinstance(node, ast.AnnAssign)
                and node.lineno == line
                and isinstance(node.value, ast.Dict)
            ),
            None,
        )
        if table is None or not isinstance(table.value, ast.Dict):
            raise ValueError(failure)
        table_scope = runtime.scope_at(
            owner, runtime.source_offset(owner.source_code, table)
        )
        constructors: list[tuple[p.Infra.RopePyName, bool]] = [(field, False)]
        dataclass = runtime.qualified_name(project, "dataclasses.dataclass")
        for value in table.value.values:
            if not isinstance(value, ast.Name | ast.Attribute):
                continue
            binding = runtime.resolve_symbol(table_scope, value)
            if binding is None:
                raise ValueError(failure)
            constructors.append((
                binding,
                FlextInfraUtilitiesSemanticContracts._metadata_constructor_frozen(
                    dataclass, binding, failure
                ),
            ))
        return constructors

    @staticmethod
    def _metadata_constructor_frozen(
        dataclass: p.Infra.RopePyName,
        binding: p.Infra.RopePyName,
        failure: str,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        origin, location = runtime.definition_location(binding)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(origin):
            raise ValueError(failure)
        origin_tree = origin.get_ast()
        if not isinstance(origin_tree, ast.AST):
            message = "native metadata constructor has no Python syntax tree"
            raise TypeError(message)
        declaration = next(
            (
                node
                for node in ast.walk(origin_tree)
                if isinstance(node, ast.ClassDef) and node.lineno == location
            ),
            None,
        )
        if declaration is None:
            raise ValueError(failure)
        lexical = runtime.scope_at(
            origin, runtime.source_offset(origin.source_code, declaration)
        )
        return any(
            isinstance(decorator, ast.Call)
            and (factory := runtime.resolve_symbol(lexical, decorator.func)) is not None
            and runtime.same_name(dataclass, factory)
            and any(
                keyword.arg == "frozen"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in decorator.keywords
            )
            for decorator in declaration.decorator_list
        )

    @classmethod
    def _require_idempotent_metadata(
        cls,
        project: p.Infra.RopeProject,
        metadata: t.VariadicTuple[t.Pair[ast.expr, p.Infra.RopeScope]],
        field: p.Infra.RopePyName,
        message: str,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Require declarative metadata, not merely a stable binding to a callback.

        Raises:
            ValueError: If authored metadata effects cannot be proven idempotent.

        """
        failure = f"{message}; additional validation effects are not proven idempotent"
        constructors = cls._metadata_constructors(project, field, failure)
        pending = [
            (node, lexical, False, frozenset[tuple[str, int]]())
            for node, lexical in metadata
        ]
        while pending:
            node, lexical, bound, visiting = pending.pop()
            children: list[ast.expr]
            match node:
                case ast.Constant():
                    continue
                case ast.Tuple() | ast.List() | ast.Set():
                    if bound and not isinstance(node, ast.Tuple):
                        raise ValueError(failure)
                    children = list(node.elts)
                case ast.Dict():
                    if bound or any(key is None for key in node.keys):
                        raise ValueError(failure)
                    children = [
                        key for key in node.keys if key is not None
                    ] + node.values
                case ast.UnaryOp(op=ast.UAdd() | ast.USub()):
                    children = [node.operand]
                case ast.Call():
                    children = cls._metadata_call_children(
                        node, lexical, (bound, constructors), failure
                    )
                case ast.Name() | ast.Attribute():
                    value = cls._metadata_bound_value(
                        project, node, lexical, (sources, failure, visiting)
                    )
                    pending.append((
                        value[0],
                        value[1],
                        True,
                        visiting | {value[2]},
                    ))
                    continue
                case _:
                    raise ValueError(failure)
            pending.extend((child, lexical, False, visiting) for child in children)

    @staticmethod
    def _metadata_call_children(
        node: ast.Call,
        lexical: p.Infra.RopeScope,
        constructors: tuple[bool, t.SequenceOf[tuple[p.Infra.RopePyName, bool]]],
        failure: str,
    ) -> list[ast.expr]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        bound, declared = constructors
        actual = runtime.resolve_symbol(lexical, node.func)
        # A stable mutable metadata instance can acquire a different schema.
        if actual is None or not any(
            runtime.same_name(actual, constructor) and (not bound or frozen)
            for constructor, frozen in declared
        ):
            raise ValueError(failure)
        holder = lexical.pyobject.get_module()
        callee = ast.unparse(node.func)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder) or not all(
            FlextInfraUtilitiesCodemodProject.single_reaching_binding(
                holder, lexical, candidate, len(holder.source_code)
            )
            for candidate in dict.fromkeys((callee.partition(".")[0], callee))
        ):
            raise ValueError(failure)
        return list(node.args) + [item.value for item in node.keywords]

    @staticmethod
    def _metadata_bound_value(
        project: p.Infra.RopeProject,
        node: ast.Name | ast.Attribute,
        lexical: p.Infra.RopeScope,
        context: tuple[
            t.MappingKV[t.Infra.RopeSourcePath, str], str, frozenset[tuple[str, int]]
        ],
    ) -> tuple[ast.expr, p.Infra.RopeScope, tuple[str, int]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        sources, failure, visiting = context
        binding = runtime.resolve_symbol(lexical, node)
        if binding is None:
            raise ValueError(failure)
        module = lexical.pyobject.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module) or not (
            FlextInfraUtilitiesCodemodProject.stable_binding_chain(
                (project, module, lexical),
                ast.unparse(node),
                len(module.source_code),
                sources,
            )
        ):
            raise ValueError(failure)
        holder, location = runtime.definition_location(binding)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder):
            raise ValueError(failure)
        if location is None:
            raise ValueError(failure)
        key = (holder.get_name(), location)
        if key in visiting:
            raise ValueError(failure)
        bound_name = (
            binding.imported_name
            if isinstance(binding, p.Infra.RopeImportedName)
            else ast.unparse(node).rpartition(".")[-1]
        )
        holder_tree = holder.get_ast()
        if not isinstance(holder_tree, ast.AST):
            message = "native metadata binding has no Python syntax tree"
            raise TypeError(message)
        declaration = next(
            (
                item
                for item in ast.walk(holder_tree)
                if isinstance(item, ast.Assign | ast.AnnAssign)
                and item.lineno == location
                and item.value is not None
                and any(
                    isinstance(target, ast.Name) and target.id == bound_name
                    for target in (
                        item.targets if isinstance(item, ast.Assign) else (item.target,)
                    )
                )
            ),
            None,
        )
        if declaration is None or declaration.value is None:
            raise ValueError(failure)
        return (
            declaration.value,
            runtime.scope_at(
                holder, runtime.source_offset(holder.source_code, declaration)
            ),
            key,
        )

    @staticmethod
    def _admitted_repeated_contract(
        scope: p.Infra.RopeScope,
        contract: p.AttributeProbe | None,
    ) -> bool:
        """Keep annotation-only references to classes still under construction lazy.

        Returns:
            Whether repeated evaluation avoids enclosing classes under construction.

        Raises:
            TypeError: If the capture has no original Python syntax tree.

        """
        if not isinstance(contract, ast.AST):
            message = "repeated contract requires the original native syntax tree"
            raise TypeError(message)
        constructing: list[p.Infra.RopePyObject] = []
        enclosing: p.Infra.RopeScope | None = scope
        while (
            enclosing is not None
            and enclosing.get_kind() == c.Infra.RopeScopeKind.CLASS
        ):
            constructing.append(enclosing.pyobject)
            enclosing = enclosing.parent
        if not constructing:
            return True
        pending: list[tuple[ast.AST, frozenset[str]]] = [(contract, frozenset())]
        while pending:
            node, bound = pending.pop()
            primary = node
            while isinstance(primary, ast.Attribute):
                primary = primary.value
            if (
                isinstance(node, ast.Name | ast.Attribute)
                and isinstance(primary, ast.Name)
                and isinstance(primary.ctx, ast.Load)
                and primary.id not in bound
            ):
                binding = FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(
                    scope, node
                )
                if binding is not None and binding.get_object() in constructing:
                    return False
            for (
                children,
                local,
            ) in FlextInfraUtilitiesSemanticCutoverClassScope.evaluated_parts(node):
                pending.extend((child, bound | local) for child in children)
        return True

    @staticmethod
    def _admitted_family(
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
    ) -> bool:
        """Elect a physical source's family from its native qualified identity.

        Returns:
            Whether the elected family is declared by the contract rule.

        Raises:
            ValueError: If the family-constrained module has no source resource.

        """
        if module.get_resource() is None:
            message = f"{rule.id}: family-constrained match has no source resource"
            raise ValueError(message)
        _package, *parts = module.get_name().split(".")
        if not parts:
            return False
        family = (
            FlextInfraUtilitiesCodegenNamespace.facade_family_of_file(
                f"{parts[0]}.py",
            )
            if len(parts) == 1
            else FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                parts[0],
            )
        )
        return family in rule.families

    @staticmethod
    def _admitted_unshadowed_builtins(
        rule: p.Infra.RopeContractRule,
        scope: p.Infra.RopeScope,
    ) -> bool:
        """Require every builtin to retain its native lexical binding.

        Returns:
            Whether all required builtin names remain unshadowed.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        return all(
            (lexical := runtime.lexical_scope(scope, name)) is not None
            and lexical.get_kind() == c.Infra.RopeScopeKind.MODULE
            and name not in lexical.get_defined_names()
            for name in rule.unshadowed_builtins
        )

    @classmethod
    def _admitted_factory_receiver(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        methods: t.StrSequence,
    ) -> bool:
        """Admit discarded compatible receivers; never inline factory evaluation.

        Returns:
            Whether the captured factory has only proven discarded consumers.

        Raises:
            TypeError: If the receiver has no original Python syntax tree.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            message = "factory receiver requires the original native syntax tree"
            raise TypeError(message)
        parents = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        nodes: t.MutableMappingKV[tuple[type[ast.AST], int], ast.AST] = {
            (type(node), runtime.source_offset(module.source_code, node)): node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call | ast.Name)
        }
        start, _end = match.get_region()
        call = nodes.get((ast.Call, start))
        if not isinstance(call, ast.Call):
            return False

        result_contract: str | None = inspect.get_annotations(
            getattr(p.Logger, methods[0])
        ).get("return")
        return cls._admit_factory_uses(
            project,
            module,
            cls._factory_bound_receiver(project, module, call, parents),
            (parents, nodes, methods, result_contract),
        )

    @staticmethod
    def _prove_logging_value(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        argument: p.Infra.RopeAstNode,
    ) -> None:
        if not isinstance(argument, ast.AST):
            message = "native logging argument proof requires source syntax"
            raise TypeError(message)
        if any(
            FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                project, module, argument, f"type=builtins.{native}", name=""
            )
            for native in ("str", "bool", "int", "float")
        ):
            return
        u.json_value_adapter().validate_python(ast.literal_eval(argument), strict=True)

    @classmethod
    def _factory_bound_receiver(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        call: ast.Call,
        parents: t.MappingKV[int, ast.AST],
    ) -> ast.Call | None:
        while (
            isinstance(member := parents.get(id(call)), ast.Attribute)
            and member.value is call
        ):
            declared = getattr(p.Logger, member.attr, None)
            if (
                not callable(declared)
                or inspect.get_annotations(declared).get("return") != "Self"
            ):
                break
            invocation = parents.get(id(member))
            if not isinstance(invocation, ast.Call) or invocation.func is not member:
                return None
            cls._require_factory_bound_call(
                project, module, member, invocation, inspect.signature(declared)
            )
            call = invocation
        return call

    @classmethod
    def _require_factory_bound_call(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        member: ast.Attribute,
        invocation: ast.Call,
        signature: inspect.Signature,
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        native_scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, member)
        )
        if (
            runtime.resolve_symbol(native_scope, member) is None
            or any(keyword.arg is None for keyword in invocation.keywords)
            or any(isinstance(argument, ast.Starred) for argument in invocation.args)
        ):
            message = (
                "unproven native bound context: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        signature.bind(
            None,
            *invocation.args,
            **{
                keyword.arg: keyword.value
                for keyword in invocation.keywords
                if keyword.arg is not None
            },
        )
        if invocation.keywords and not any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        ):
            message = (
                "unproven native bound keywords: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        for argument in invocation.args:
            if not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                project, module, argument, "type=builtins.str", name=""
            ):
                message = (
                    "unproven native bound key: "
                    f"{module.get_name()}:{invocation.lineno}"
                )
                raise ValueError(message)
        for keyword in invocation.keywords:
            cls._prove_logging_value(project, module, keyword.value)

    @staticmethod
    def _discarded_logging_emission(
        node: p.Infra.RopeAstNode,
        parents: t.MappingKV[int, ast.AST],
        methods: t.StrSequence,
        result_contract: str | None,
    ) -> bool:
        member = parents.get(id(node))
        invocation = parents.get(id(member))
        statement = parents.get(id(invocation))
        declared = (
            getattr(p.Logger, member.attr, None)
            if isinstance(member, ast.Attribute)
            else None
        )
        output = (
            getattr(p.OutputLogger, member.attr, None)
            if isinstance(member, ast.Attribute)
            else None
        )
        return (
            isinstance(member, ast.Attribute)
            and member.value is node
            and (
                member.attr in methods
                or callable(output)
                or (
                    callable(declared)
                    and inspect.get_annotations(declared).get("return")
                    == result_contract
                )
            )
            and isinstance(invocation, ast.Call)
            and invocation.func is member
            and isinstance(statement, ast.Expr)
            and statement.value is invocation
        )

    @classmethod
    def _prove_logging_arguments(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: p.Infra.RopeAstNode,
        parents: t.MappingKV[int, ast.AST],
        methods: t.StrSequence,
    ) -> None:
        member = parents[id(node)]
        invocation = parents[id(member)]
        if not isinstance(member, ast.Attribute) or not isinstance(
            invocation, ast.Call
        ):
            message = "native emission proof has no method invocation"
            raise TypeError(message)
        if (
            member.attr not in methods
            or not invocation.args
            or invocation.keywords
            or any(isinstance(argument, ast.Starred) for argument in invocation.args)
        ):
            message = (
                "unproven native logging emission contract: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        if not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
            project, module, invocation.args[0], "type=builtins.str", name=""
        ):
            message = (
                "logging migration requires a proven string message: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        for argument in invocation.args[1:]:
            # Native literals have no authored evaluation to discard or run
            # during planning; the canonical JSON port proves the payload.
            cls._prove_logging_value(project, module, argument)

    @classmethod
    def _admit_factory_uses(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        call: ast.Call | None,
        context: tuple[
            t.MappingKV[int, ast.AST],
            t.MappingKV[tuple[type[ast.AST], int], ast.AST],
            t.StrSequence,
            str | None,
        ],
    ) -> bool:
        if call is None:
            return False
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        parents, _nodes, methods, result_contract = context
        assignment = parents.get(id(call))
        if not isinstance(assignment, ast.Assign | ast.AnnAssign):
            if not cls._discarded_logging_emission(
                call, parents, methods, result_contract
            ):
                return False
            cls._prove_logging_arguments(project, module, call, parents, methods)
            return True
        target = cls._factory_assignment_target(module, call, assignment)
        if target is None:
            return False
        offset = runtime.source_offset(module.source_code, target)
        scope = runtime.scope_at(module, offset)
        if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
            return False
        binding = runtime.resolve_symbol(scope, target)
        return binding is not None and cls._admit_factory_occurrences(
            project, module, (target, binding, offset), context
        )

    @staticmethod
    def _factory_assignment_target(
        module: p.Infra.RopePyModule,
        call: ast.Call,
        assignment: ast.Assign | ast.AnnAssign,
    ) -> ast.Name | None:
        if assignment.value is not call:
            return None
        if isinstance(assignment, ast.Assign):
            if len(assignment.targets) != 1:
                return None
            target = assignment.targets[0]
        else:
            target = assignment.target
        if not isinstance(target, ast.Name):
            return None
        if (
            target.id
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                module.source_code
            )
        ):
            return None
        return target

    @classmethod
    def _admit_factory_occurrences(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        target_binding: tuple[ast.Name, p.Infra.RopePyName, int],
        context: tuple[
            t.MappingKV[int, ast.AST],
            t.MappingKV[tuple[type[ast.AST], int], ast.AST],
            t.StrSequence,
            str | None,
        ],
    ) -> bool:
        parents, nodes, methods, result_contract = context
        target, binding, offset = target_binding
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project, target.id, binding, imports=False, in_hierarchy=False
        )
        definitions = 0
        uses: t.MutableSequenceOf[p.Infra.RopeAstNode] = []
        for occurrence in finder.find_occurrences(pymodule=module):
            position, _stop = occurrence.get_word_range()
            if occurrence.is_defined() or occurrence.is_written():
                if position != offset:
                    return False
                definitions += 1
                continue
            receiver = nodes.get((ast.Name, position))
            if receiver is None or not cls._discarded_logging_emission(
                receiver, parents, methods, result_contract
            ):
                return False
            uses.append(receiver)
        if definitions != 1 or not uses:
            return False
        for receiver in uses:
            cls._prove_logging_arguments(project, module, receiver, parents, methods)
        return True


__all__: list[str] = ["FlextInfraUtilitiesSemanticContracts"]
