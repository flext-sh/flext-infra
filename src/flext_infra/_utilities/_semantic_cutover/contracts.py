"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from functools import partial
from pathlib import Path

from flext_cli import cli, u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._rope_analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities._semantic_cutover.declaration_relocation import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
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
                for rule in cls.declared_contract_rules(
                    Path(workspace.rope_project.root.real_path)
                )
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
        overlay = repository_root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        catalogues = (packaged,) + (
            (overlay,) if overlay != packaged and overlay.exists() else ()
        )
        rules = tuple(
            rule
            for catalogue in catalogues
            for rule in m.Infra.RopeContractRules.model_validate(
                u.Cli.yaml_safe_load(catalogue).unwrap()
            ).rules
        )
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
        return rules

    @classmethod
    def plan_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
        rules: t.SequenceOf[p.Infra.RopeContractRule],
    ) -> p.Result[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Reuse the native contract loop for an already validated rule domain.

        Returns:
            Content plans consumed by the existing semantic publication owner.

        """
        items = cls._editable_sources(sources)
        if not items:
            return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(())
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
                        arguments=rule.arguments,
                        resources=resources,
                        imports=rule.imports,
                        match_filter=partial(
                            cls._admit_contract_match,
                            project,
                            rule,
                            implementation_paths=implementation_paths,
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
        return r[t.VariadicTuple[p.Infra.SemanticMigrationEdit]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    changes=tuple(applied[path]),
                )
                for path, source in items
                if source != working[path]
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
    ) -> bool:
        """Prove native receivers, evaluation safety and destination bindings.

        Returns:
            Whether the original occurrence belongs to the declared contract domain.

        Raises:
            ValueError: A declared capture cannot disappear or repeat safely,
                or the destination identity is not established.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        resource = module.get_resource()
        if resource is not None and Path(resource.real_path) in implementation_paths:
            return False
        if rule.receiver_methods and not cls._admitted_factory_receiver(
            project, module, match, rule.receiver_methods
        ):
            return False
        scope = runtime.scope_at(module, match.get_region()[0])
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
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
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

        def discarded_emission(node: p.Infra.RopeAstNode) -> bool:
            member = parents.get(id(node))
            invocation = parents.get(id(member))
            statement = parents.get(id(invocation))
            return (
                isinstance(member, ast.Attribute)
                and member.value is node
                and member.attr in methods
                and isinstance(invocation, ast.Call)
                and invocation.func is member
                and isinstance(statement, ast.Expr)
                and statement.value is invocation
            )

        assignment = parents.get(id(call))
        if not isinstance(assignment, ast.Assign | ast.AnnAssign):
            return discarded_emission(call)
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
        uses = 0
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
            uses += 1
        return definitions == 1 and uses > 0

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
