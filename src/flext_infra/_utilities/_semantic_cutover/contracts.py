"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
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
        """Plan the declared contract rules without publishing any source.

        Args:
            workspace: The Rope workspace context for the migration.
            sources: A mapping of file paths to their current source content.

        Returns:
            Source-authenticated edits for the existing semantic transaction.

        Raises:
            ValueError: If there are duplicate Rope contract rule identities.
        """
        items = cls._editable_sources(sources)
        if not items:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(())
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
                resources = tuple(
                    resource
                    for resource in resources
                    if cls._model_declarations(project, resource, rule)
                )
                if not resources:
                    continue
                changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                    project,
                    rule.pattern,
                    rule.goal,
                    arguments=rule.arguments,
                    resources=resources,
                    imports=rule.imports,
                )
                members = FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                    changes.changes, f"{rule.id}: invalid Rope content changes"
                ).unwrap()
                for change in members:
                    path = Path(change.resource.real_path).resolve()
                    if change.new_contents == working[path]:
                        continue
                    cls._require_destination_bindings(project, change.resource, rule)
                    working[path] = change.new_contents
                    applied.setdefault(path, []).append(rule.id)
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

    @staticmethod
    def _model_declarations(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        rule: m.Infra.RopeContractRule,
    ) -> bool:
        """Prove model ancestry for every native match before restructuring.

        Returns:
            Whether this resource has applicable, ancestry-proven occurrences.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = project.get_pymodule(resource)
        matches = FlextInfraUtilitiesRopeRuntimeRefactors.contract_matches(
            module, rule.pattern, rule.arguments
        )
        if not matches:
            return False
        ancestors = tuple(
            runtime.qualified_name(project, name).get_object()
            for name in rule.model_bases
        )
        for match in matches:
            scope = runtime.scope_at(module, match.get_region()[0])
            pending = [scope.pyobject]
            found: list[p.Infra.RopePyObject] = []
            while pending:
                value = pending.pop()
                if value in found:
                    continue
                found.append(value)
                if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(value):
                    pending.extend(value.get_superclasses())
            if ancestors and not any(value in found for value in ancestors):
                return False
        return True

    @staticmethod
    def _require_destination_bindings(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        rule: m.Infra.RopeContractRule,
    ) -> None:
        """Refuse captures by existing module, class or function bindings.

        Raises:
            ValueError: When a destination name has a competing lexical identity.
        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        module = project.get_pymodule(resource)
        pending = [module.get_scope()]
        for expression, expected in rule.bindings.items():
            identity = runtime.qualified_name(project, expected)
            scopes = list(pending)
            while scopes:
                scope = scopes.pop()
                scopes.extend(scope.get_scopes())
                root = expression.split(".", 1)[0]
                if root not in scope.get_defined_names():
                    continue
                actual = runtime.expression_name(scope, expression)
                if not runtime.same_name(identity, actual):
                    message = (
                        f"{rule.id}: destination {expression} is shadowed "
                        f"in {resource.path}:{scope.get_start()}"
                    )
                    raise ValueError(message)


__all__: list[str] = ["FlextInfraUtilitiesSemanticContracts"]
