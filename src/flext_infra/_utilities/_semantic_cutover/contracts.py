"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import partial
from pathlib import Path

from flext_cli import cli, u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
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
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Return source-authenticated edits for the normalization phase's rules."""
        return cls.plan_contract_rules(
            workspace,
            sources,
            tuple(
                rule
                for rule in cls.declared_contract_rules()
                if rule.phase == c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION
            ),
        )

    @staticmethod
    def declared_contract_rules() -> t.SequenceOf[m.Infra.RopeContractRule]:
        """Load typed policy; reject duplicate identities and undeclared families.

        Returns:
            Declared Rope contract rules in configuration order.

        Raises:
            ValueError: If two rules share an identity or a rule names an
                undeclared facade family.


        """
        rules = m.Infra.RopeContractRules.model_validate(
            u.Cli.yaml_safe_load(
                type(config).ssot_config_dir().parent
                / c.Infra.CODEMOD_ROPE_RULES_RELPATH
                / "contracts.yaml"
            ).unwrap()
        ).rules
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
        sources: t.MappingKV[Path, str],
        rules: t.SequenceOf[m.Infra.RopeContractRule],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Reuse the native contract loop for an already validated rule domain.

        Returns:
            Content plans consumed by the existing semantic publication owner.

        """
        items = cls._editable_sources(sources)
        if not items:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
        working = dict(items)
        applied: dict[Path, list[str]] = {}
        for rule in rules:
            project = FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                workspace.rope_project, working
            )
            try:
                resources = tuple(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    )
                    for path in working
                )
                changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                    project,
                    m.Infra.RopeRestructureRequest(
                        pattern=rule.pattern,
                        goal=rule.goal,
                        arguments=rule.arguments,
                        resources=resources,
                        imports=rule.imports,
                        match_filter=partial(cls._admit_contract_match, project, rule),
                    ),
                )
                members = FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                    changes.changes, f"{rule.id}: invalid Rope content changes"
                ).unwrap()
                for change in members:
                    path = Path(change.resource.real_path).resolve()
                    if change.new_contents == working[path]:
                        continue
                    working[path] = change.new_contents
                    applied.setdefault(path, []).append(rule.id)
                cli.display_text(
                    f"mod: Rope contract {rule.id}: changed_files={len(members)}"
                )
            finally:
                project.close()
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
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

    @classmethod
    def _admit_contract_match(
        cls,
        project: p.Infra.RopeProject,
        rule: m.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
    ) -> bool:
        """Prove each occurrence's model ancestry and destination bindings.

        Returns:
            Whether the native occurrence belongs to this rule's model domain.

        Raises:
            ValueError: If a family-constrained occurrence has no source resource.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
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
        if rule.repeats_annotation or rule.reorders_annotation:
            calls = FlextInfraUtilitiesRopeRuntimeRefactors.word_call_regions(
                module.source_code, match.get_region()
            )
            if len(calls) != 1:
                message = (
                    f"{rule.id}: annotation evaluation cannot repeat or reorder "
                    f"authored calls "
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
        rule: m.Infra.RopeContractRule,
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
        rule: m.Infra.RopeContractRule,
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
    def _admitted_bindings(
        project: p.Infra.RopeProject,
        rule: m.Infra.RopeContractRule,
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
