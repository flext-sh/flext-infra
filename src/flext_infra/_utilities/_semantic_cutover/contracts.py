"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from flext_cli import cli, u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
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
    FlextInfraUtilitiesSemanticCutoverEdits,
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)
from flext_infra._utilities._semantic_cutover.declaration_retirement import (
    FlextInfraUtilitiesSemanticDeclarationRetirement,
)
from flext_infra._utilities._semantic_cutover.family_type_references import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities._semantic_cutover.private_imports import (
    FlextInfraUtilitiesSemanticCutoverPrivateImports,
)


class FlextInfraUtilitiesSemanticContracts(FlextInfraUtilitiesSemanticCutoverEdits):
    """Reuse the joint semantic loop and immutable Rope source inventory."""

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
        """Load universal and elected repo rules; reject duplicate IDs/unknown families."""
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
                u.type_adapter(t.JsonMapping).dump_json(parsed)
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

    @staticmethod
    def _contract_arguments(
        rule: p.Infra.RopeContractRule,
    ) -> t.MappingKV[str, str | t.StrSequence]:
        """Require a transfer's single native receiver constraint."""
        if rule.ownership_transfer is None:
            return rule.arguments
        if len(rule.arguments) != 1 or not all(
            isinstance(value, str) and value.startswith("name=")
            for value in rule.arguments.values()
        ):
            message = (
                f"{rule.id}: ownership transfer requires one native receiver constraint"
            )
            raise ValueError(message)
        return {}

    @classmethod
    def plan_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
        *,
        captured: p.Infra.CodemodSourceEpoch | None = None,
        annotation_only: bool = False,
        class_alias_only: bool = False,
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Plan native changes against one authenticated source epoch.

        Filters narrow matches without weakening receiver or import proofs.
        """
        items = cls._editable_sources(sources)
        # Elect receivers without making unrelated generated sources editable.
        providers: dict[t.Infra.RopeSourcePath, str] = {}
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
        items = tuple(sorted({**dict(items), **providers}.items()))
        staged_receivers = frozenset(
            path
            for path in providers
            if sources[path].startswith(c.Infra.AUTOGEN_HEADERS)
        )
        if not items or not rules:
            return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(())
        transfers = any(rule.ownership_transfer is not None for rule in rules)
        if transfers:
            for rule in rules:
                if rule.ownership_transfer is None:
                    continue
                owner = (
                    FlextInfraUtilitiesSemanticDeclarationRelocation.contract_rule_root(
                        workspace.repository_root, rule
                    )
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
                    message = (
                        f"{rule.id}: an external library declaration cannot retire"
                    )
                    raise ValueError(message)
        working = dict(items)
        applied: t.MutableMappingKV[
            t.Infra.RopeSourcePath, t.MutableSequenceOf[str]
        ] = {}
        epoch = (
            captured
            if captured is not None
            else cls._contract_epoch(workspace, sources, rules)
        )
        # Every snapshot retains the staged view and the original captured epoch.
        project: p.Infra.RopeProject | None = None
        try:
            project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                workspace.rope_project, {**sources, **working}, captured=epoch
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
                for path, _source in items
                if transfers and path.is_relative_to(workspace.repository_root)
            }
            implementation_owners: t.MutableMappingKV[
                t.Pair[str, str], t.Infra.RopeImplementationPaths
            ] = {}
            for rule in rules:
                if project is None:
                    project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                        workspace.rope_project, {**sources, **working}, captured=epoch
                    )
                resources = tuple(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    )
                    for path in working
                )
                selected_project = project

                def admit(
                    module: p.Infra.RopePyModule,
                    match: p.Infra.RopeContractMatch,
                ) -> bool:
                    first, last = match.get_region()
                    if annotation_only and not any(
                        begin <= first < last <= end
                        for begin, end, _line in FlextInfraUtilitiesSemanticFamilyTypeReferences.annotation_regions(
                            module.source_code, module
                        )
                    ):
                        return False
                    if class_alias_only:
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
                    return cls._admit_contract_match(
                        selected_project,
                        rule,
                        module,
                        match,
                        implementation_owners=implementation_owners,
                        sources={**epoch.sources, **working},
                        owned_modules=owned_modules,
                    )

                changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                    project,
                    m.Infra.RopeRestructureRequest(
                        pattern=rule.pattern,
                        goal=rule.goal,
                        arguments=cls._contract_arguments(rule),
                        resources=resources,
                        imports=rule.imports,
                        match_filter=admit,
                    ),
                )
                members = FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                    changes.changes, f"{rule.id}: invalid Rope content changes"
                ).unwrap()
                changed = False
                for change in members:
                    path = Path(change.resource.real_path).resolve()
                    proposed = FlextInfraUtilitiesSemanticDeclarationRelocation._remove_orphaned_imports(
                        project,
                        change.resource,
                        working[path],
                        change.new_contents,
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
        retirement_sources = {**sources, **working}
        retired, providers = (
            FlextInfraUtilitiesSemanticDeclarationRetirement.retire_contract_owners(
                workspace, retirement_sources, rules, epoch, owned_modules
            )
        )
        working.update((path, retirement_sources[path]) for path in working)
        if captured is not None and staged_receivers:
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

    @staticmethod
    def _normalize_projected_consumers(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MutableMappingKV[Path, str],
        epoch: p.Infra.CodemodSourceEpoch,
        consumers: t.SequenceOf[Path],
        receivers: frozenset[Path],
    ) -> tuple[Path, ...]:
        """Reuse facade election and import cutover inside the captured source epoch."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        imports = FlextInfraUtilitiesPrivateImportFacades
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
            modules = imports.source_modules(sources, ())
            facades = imports.discover(modules)
            bindings, _exports = imports.declared_exports(modules)
            bases = FlextInfraUtilitiesPrivateImportAncestry.class_bases(modules)
            family = (
                layout.package_dir
                / FlextInfraUtilitiesCodegenNamespace.facade_families()["p"].directory
            )
            root = Path(project.root.real_path)
            resolve = FlextInfraUtilitiesRopeCore.resolve_pymodule
            for path in consumers:
                if path == facade or path.is_relative_to(family):
                    continue
                module_resource = project.get_resource(
                    path.relative_to(root).as_posix()
                )
                module = resolve(project, module_resource)
                specs: list[t.Infra.PrivateImportSpec] = []
                native_imports = (
                    FlextInfraUtilitiesSemanticDeclarationRelocation.native_import_infos
                )
                references = FlextInfraUtilitiesSemanticFamilyTypeReferences
                for information in native_imports(project, module):
                    if not isinstance(information, p.Infra.RopeFromImport):
                        continue
                    for name, alias in information.names_and_aliases:
                        local = alias or name
                        binding = runtime.expression_name(module.get_scope(), local)
                        if binding is None:
                            msg = f"consumer import has no native binding: {local} in {path}"
                            raise ValueError(msg)
                        owner = binding.get_object().get_module()
                        resource = owner.get_resource() if owner is not None else None
                        if (
                            owner is None
                            or resource is None
                            or Path(resource.real_path) not in receivers
                        ):
                            continue
                        qualified = (
                            f"{owner.get_name()}.{binding.get_object().get_name()}"
                        )
                        reference = imports.public_reference(
                            owners=facades.get(layout.package_name, ()),
                            package=layout.package_name,
                            qualified=qualified,
                            bindings=bindings,
                            class_bases=bases,
                        )
                        if reference is None or reference.partition(".")[0] != "p":
                            msg = f"projected receiver has no unique public protocol export: {qualified}"
                            raise ValueError(msg)
                        primaries = [
                            (sources[path][begin:end], runtime.scope_at(module, begin))
                            for begin, end in references.reference_regions(
                                sources[path]
                            )
                        ]
                        primaries.extend(
                            (value[begin:end], lexical)
                            for value, lexical, _line in references.scoped_quoted_type_references(
                                sources[path], project, module
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
                                module_name=layout.package_name,
                            )
                            if not runtime.same_name(
                                public, runtime.expression_name(lexical, primary)
                            ):
                                msg = f"public receiver changes native identity: {primary} in {path}"
                                raise ValueError(msg)
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
                            layout.package_name,
                            reference,
                        ))
                if specs:
                    updated, _operations = (
                        FlextInfraUtilitiesSemanticCutoverPrivateImports._rewrite_private_imports(
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
        finally:
            project.close()

    @staticmethod
    def _contract_epoch(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
    ) -> p.Infra.CodemodSourceEpoch:
        """Capture the sources and every identity the rules constrain."""
        prefix = c.Infra.ROPE_NAME_CONSTRAINT_PREFIX
        return FlextInfraUtilitiesCodemodProject.identity_source_epoch(
            Path(workspace.rope_project.root.real_path),
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
        implementation_owners: t.MutableMappingKV[
            t.Pair[str, str], t.Infra.RopeImplementationPaths
        ],
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        owned_modules: t.MappingKV[str, t.Infra.RopeSourcePath] | None = None,
    ) -> bool:
        """Prove native receivers, evaluation safety and destination bindings."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        resource = module.get_resource()
        if rule.implementation_owner is not None:
            identity = rule.implementation_owner
            # Native matching elects the analysis; unrelated rules need no graph walk.
            if identity not in implementation_owners:
                implementation_owners[identity] = (
                    FlextInfraUtilitiesCodemodProject._implementation_owner_modules(
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
        if rule.call_target is not None:
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
            if rule.missing_keywords:
                if any(
                    keyword.arg in rule.missing_keywords
                    for keyword in invocation.keywords
                ):
                    return False
                if any(keyword.arg is None for keyword in invocation.keywords):
                    msg_0 = (
                        f"{rule.id}: expanded keywords cannot prove missing "
                        "injected ports"
                    )
                    raise ValueError(msg_0)
        elif rule.missing_keywords:
            msg_0 = f"{rule.id}: missing-keyword proof requires a call target"
            raise ValueError(msg_0)
        if rule.receiver_methods and not cls._admitted_factory_receiver(
            project, module, match, rule.receiver_methods
        ):
            return False
        scope = runtime.scope_at(module, match.get_region()[0])
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
                    message = f"{rule.id}: transferred owner is absent but a receiver survives"
                    raise ValueError(message)
                return False
            unknown = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
                "rope.base.pyobjects", "get_unknown"
            )()
            if actual is None or actual.get_object() == unknown:
                message = f"{rule.id}: unproven transferred receiver in {module.get_name()}:{scope.get_start()}"
                raise ValueError(message)
            if not runtime.same_name(original, actual):
                return False
        if rule.scope_kinds and scope.get_kind() not in rule.scope_kinds:
            return False
        if rule.families and not cls._admitted_family(rule, module):
            return False
        ancestry = FlextInfraUtilitiesDeclarationPayload.class_ancestry(scope.pyobject)
        if rule.model_bases and not any(
            runtime.qualified_name(project, name).get_object() in ancestry
            for name in rule.model_bases
        ):
            return False
        for capture in rule.drops:
            if not isinstance(match.get_ast(capture), ast.Constant):
                message = (
                    f"{rule.id}: cannot discard authored evaluation of {capture} "
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
        if (
            rule.reorders_annotation
            and len(refactors.word_call_regions(module.source_code, match.get_region()))
            != 1
        ):
            message = (
                f"{rule.id}: annotation evaluation cannot reorder authored calls "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)
        if not cls._admitted_unshadowed_builtins(rule, scope):
            return False
        return cls._admitted_bindings(
            project,
            rule,
            module,
            scope,
            match.get_region()[0],
        )

    @staticmethod
    def _admitted_family(
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
    ) -> bool:
        """Elect a physical source's family from its native qualified identity."""
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
        """Require every builtin to retain its native lexical binding."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        return all(
            (lexical := runtime.lexical_scope(scope, name)) is not None
            and lexical.get_kind() == c.Infra.RopeScopeKind.MODULE
            and name not in lexical.get_defined_names()
            for name in rule.unshadowed_builtins
        )

    @staticmethod
    def _admitted_factory_receiver(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        methods: t.StrSequence,
    ) -> bool:
        """Admit discarded compatible receivers; never inline factory evaluation."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            message = "factory receiver requires the original native syntax tree"
            raise TypeError(message)
        parents = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        nodes = {
            (type(node), runtime.source_offset(module.source_code, node)): node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call | ast.Name)
        }
        start, _end = match.get_region()
        call = nodes.get((ast.Call, start))
        if not isinstance(call, ast.Call):
            return False

        result_contract = inspect.get_annotations(getattr(p.Logger, methods[0])).get(
            "return"
        )

        def prove_value(argument: p.Infra.RopeAstNode) -> None:
            if not isinstance(argument, ast.AST):
                message = "native logging argument proof requires source syntax"
                raise TypeError(message)
            if any(
                refactors.semantic_capture(
                    project, module, argument, f"type=builtins.{native}", name=""
                )
                for native in ("str", "bool", "int", "float")
            ):
                return
            u.type_adapter(t.JsonValue).validate_python(
                ast.literal_eval(argument), strict=True
            )

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
                return False
            native_scope = runtime.scope_at(
                module, runtime.source_offset(module.source_code, member)
            )
            if (
                runtime.resolve_symbol(native_scope, member) is None
                or any(keyword.arg is None for keyword in invocation.keywords)
                or any(
                    isinstance(argument, ast.Starred) for argument in invocation.args
                )
            ):
                message = f"unproven native bound context: {module.get_name()}:{invocation.lineno}"
                raise ValueError(message)
            signature = inspect.signature(declared)
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
                message = f"unproven native bound keywords: {module.get_name()}:{invocation.lineno}"
                raise ValueError(message)
            for argument in invocation.args:
                if not refactors.semantic_capture(
                    project, module, argument, "type=builtins.str", name=""
                ):
                    message = f"unproven native bound key: {module.get_name()}:{invocation.lineno}"
                    raise ValueError(message)
            for keyword in invocation.keywords:
                prove_value(keyword.value)
            call = invocation

        def discarded_emission(node: p.Infra.RopeAstNode) -> bool:
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

        def prove_arguments(node: p.Infra.RopeAstNode) -> None:
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
                or any(
                    isinstance(argument, ast.Starred) for argument in invocation.args
                )
            ):
                message = f"unproven native logging emission contract: {module.get_name()}:{invocation.lineno}"
                raise ValueError(message)
            if not refactors.semantic_capture(
                project, module, invocation.args[0], "type=builtins.str", name=""
            ):
                message = f"logging migration requires a proven string message: {module.get_name()}:{invocation.lineno}"
                raise ValueError(message)
            for argument in invocation.args[1:]:
                # Native literals have no authored evaluation to discard or run
                # during planning; the canonical JSON port proves the payload.
                prove_value(argument)

        assignment = parents.get(id(call))
        if not isinstance(assignment, ast.Assign | ast.AnnAssign):
            if not discarded_emission(call):
                return False
            prove_arguments(call)
            return True
        if assignment.value is not call:
            return False
        if isinstance(assignment, ast.Assign):
            if len(assignment.targets) != 1:
                return False
            target = assignment.targets[0]
        else:
            target = assignment.target
        if not isinstance(target, ast.Name):
            return False
        if (
            target.id
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                module.source_code
            )
        ):
            return False
        offset = runtime.source_offset(module.source_code, target)
        scope = runtime.scope_at(module, offset)
        if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
            return False
        binding = runtime.resolve_symbol(scope, target)
        if binding is None:
            return False
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
            if receiver is None or not discarded_emission(receiver):
                return False
            uses.append(receiver)
        if definitions != 1 or not uses:
            return False
        for receiver in uses:
            prove_arguments(receiver)
        return True

    @staticmethod
    def _admitted_bindings(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        offset: int,
    ) -> bool:
        """Prove each destination and its preceding unconditional import."""
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        for expression, expected in rule.bindings.items():
            identity = runtime.qualified_name(project, expected)
            root = expression.split(".", 1)[0]
            root_name = runtime.expression_name(scope, root)
            if root_name is None:
                continue
            actual = runtime.expression_name(scope, expression)
            if not runtime.same_name(identity, actual):
                message = (
                    f"{rule.id}: destination {expression} is shadowed "
                    f"in {module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
            if isinstance(
                root_name, (p.Infra.RopeImportedName, p.Infra.RopeImportedModule)
            ) and not runtime.imported_binding_precedes(project, module, root, offset):
                message = (
                    f"{rule.id}: destination {expression} has no preceding "
                    f"unconditional import in {module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
        return True


__all__: list[str] = ["FlextInfraUtilitiesSemanticContracts"]
