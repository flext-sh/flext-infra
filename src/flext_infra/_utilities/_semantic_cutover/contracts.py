"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import inspect
from functools import partial
from pathlib import Path

from flext_cli import cli, u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesProjectDiscovery,
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
        """Load typed policy; reject duplicate identities and undeclared families.

        The packaged catalogue holds only universal rules. A governed repository
        declares rules about its own symbols in the same relative path under its
        root; that overlay is optional, and its absence declares no rule.

        Returns:
            Packaged rules, then the repository's own rules, in file order.

        Raises:
            ValueError: If two rules share an identity or a rule names an
                undeclared facade family.

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
        """Prove the selected member for an ownership-transfer rule.

        Returns:
            The native receiver constraints the rule must satisfy.

        Raises:
            ValueError: The transfer rule lacks its single receiver constraint.

        """
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
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Reuse the native contract loop for an already validated rule domain.

        Args:
            workspace: Authenticated Rope workspace owning every source.
            sources: Current source text captured per absolute path.
            rules: Validated contract rules admitted for this domain.

        Returns:
            Content plans consumed by the existing semantic publication owner.

        Raises:
            ValueError: A rule names an undeclared Rope contract family.

        """
        items = cls._editable_sources(sources)
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
        epoch = cls._contract_epoch(workspace, working, rules)
        # A snapshot is a pure function of (working, epoch); restructuring only
        # plans a ChangeSet, so consecutive rules share one graph until a rule
        # actually changes a source.
        project: p.Infra.RopeProject | None = None
        try:
            project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                workspace.rope_project, working, captured=epoch
            )
            owned_modules = {
                FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        project, path
                    ),
                ).get_name(): path
                for path, _source in items
                if transfers and path.is_relative_to(workspace.repository_root)
            }
            implementation_owners: t.MutableMappingKV[
                t.Pair[str, str], t.Infra.RopeImplementationPaths
            ] = {}
            for primitive_identity in dict.fromkeys(
                rule.implementation_owner
                for rule in rules
                if rule.implementation_owner is not None
            ):
                implementation_owners[primitive_identity] = (
                    FlextInfraUtilitiesCodemodProject._implementation_owner_modules(
                        project,
                        m.Infra.CodemodContextCondition(
                            variable="OWNER",
                            predicate=c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
                            holds=False,
                            arg=primitive_identity,
                        ),
                        {**epoch.sources, **working},
                    )
                )
            for rule in rules:
                if project is None:
                    project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                        workspace.rope_project, working, captured=epoch
                    )
                resources = tuple(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    )
                    for path in working
                )
                implementation_paths = (
                    frozenset()
                    if rule.implementation_owner is None
                    else implementation_owners[rule.implementation_owner]
                )
                changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                    project,
                    m.Infra.RopeRestructureRequest(
                        pattern=rule.pattern,
                        goal=rule.goal,
                        arguments=cls._contract_arguments(rule),
                        resources=resources,
                        imports=rule.imports,
                        match_filter=partial(
                            cls._admit_contract_match,
                            project,
                            rule,
                            implementation_paths=implementation_paths,
                            owned_modules=owned_modules,
                        ),
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
        retired, providers = (
            FlextInfraUtilitiesSemanticDeclarationRetirement.retire_contract_owners(
                workspace, dict(items), working, rules, epoch, owned_modules
            )
        )
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
    def _contract_epoch(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
    ) -> p.Infra.CodemodSourceEpoch:
        """Capture the edited sources and every identity the rules constrain.

        Returns:
            The immutable source epoch shared by every rule of this plan.

        """
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
        implementation_paths: t.Infra.RopeImplementationPaths = frozenset(),
        owned_modules: t.MappingKV[str, t.Infra.RopeSourcePath] | None = None,
    ) -> bool:
        """Prove native receivers, evaluation safety and destination bindings.

        Returns:
            Whether the original occurrence belongs to the declared contract domain.

        Raises:
            ValueError: A declared capture cannot disappear or repeat safely,
                or the destination identity is not established.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        resource = module.get_resource()
        if resource is not None and Path(resource.real_path) in implementation_paths:
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
        """Elect a facade family from the module's native qualified identity.

        Returns:
            Whether the declared family admits this physical source module.

        Raises:
            ValueError: A family-constrained match has no physical source.

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
        """Require every declared builtin to retain its native lexical binding.

        Returns:
            Whether all declared builtin names are unshadowed.

        """
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
        """Preserve configured, escaping and rebound native factory products.

        Only discarded calls on the declared compatible receiver interface
        establish this proof. The factory expression itself is never inlined.
        """
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
        """Prove each destination and its preceding unconditional import.

        Returns:
            True when every existing destination retains its declared identity.

        Raises:
            ValueError: A destination is shadowed or its import does not precede it.

        """
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
