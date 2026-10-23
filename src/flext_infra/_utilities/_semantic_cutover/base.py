"""Composed semantic cutover planner exposing one parameterized entry point.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesSemanticCutoverAliases,
    FlextInfraUtilitiesSemanticCutoverDynamicEnvironment,
    FlextInfraUtilitiesSemanticCutoverFacadeBases,
    FlextInfraUtilitiesSemanticCutoverModelFields,
    FlextInfraUtilitiesSemanticCutoverModuleLayout,
    FlextInfraUtilitiesSemanticCutoverNesting,
    FlextInfraUtilitiesSemanticCutoverPrivateImports,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticConstantConsumers,
    FlextInfraUtilitiesSemanticDeclarationRelocation,
)
from flext_infra._utilities._semantic_cutover.contracts import (
    FlextInfraUtilitiesSemanticContracts,
)
from flext_infra._utilities._semantic_cutover.model_aliases import (
    FlextInfraUtilitiesSemanticModelAliases,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverBase(
    FlextInfraUtilitiesSemanticContracts,
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticConstantConsumers,
    FlextInfraUtilitiesSemanticCutoverNesting,
    FlextInfraUtilitiesSemanticCutoverAliases,
    FlextInfraUtilitiesSemanticCutoverPrivateImports,
    FlextInfraUtilitiesSemanticCutoverFacadeBases,
    FlextInfraUtilitiesSemanticCutoverModelFields,
    FlextInfraUtilitiesSemanticCutoverDynamicEnvironment,
    FlextInfraUtilitiesSemanticCutoverModuleLayout,
):
    """Plan every semantic ``make mod`` cutover through one typed contract."""

    @classmethod
    def plan_semantic_cutover(
        cls,
        phase: c.Infra.SemanticCutoverPhase,
        *,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModOccurrence] = (),
        import_normalizer: p.Infra.SourceImportNormalizer | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
    ) -> p.ResultView[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Plan one phase without effects; the first exception escapes unchanged.

        ``rope_workspace`` supplies the repository root that reported findings
        are relative to and, for class nesting, the module ownership policy.
        Finding-driven phases select their own rule findings from ``findings``.

        Returns:
            The immutable result view of the selected phase's source edits.

        Raises:
            ValueError: If the phase is unsupported.

        """
        if not phase:
            message = f"unsupported semantic cutover phase: {phase}"
            raise ValueError(message)
        root = rope_workspace.repository_root
        rule_id = c.Infra.SEMANTIC_CUTOVER_RULE_IDS.get(phase)
        selected = tuple(finding for finding in findings if finding.rule_id == rule_id)
        if phase in {
            c.Infra.SemanticCutoverPhase.CLASS_NESTING,
            c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT,
        }:
            if codegen is None:
                captured = (
                    FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(root)
                )
                if captured.failure:
                    return r[
                        t.VariadicTuple[m.Infra.SemanticMigrationEdit]
                    ].from_failure(captured)
                codegen = captured.value.spec
            if phase is c.Infra.SemanticCutoverPhase.CLASS_NESTING:
                return cls._plan_class_nesting(rope_workspace, sources, codegen)
            return cls._plan_dynamic_environment(
                root, sources, selected, rope_workspace=rope_workspace, codegen=codegen
            )
        match phase:
            case (
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
                | c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
                | c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION
                | c.Infra.SemanticCutoverPhase.COMPAT_ALIAS
                | c.Infra.SemanticCutoverPhase.PRIVATE_IMPORT
                | c.Infra.SemanticCutoverPhase.FACADE_BASE
                | c.Infra.SemanticCutoverPhase.MODEL_FIELDS
            ):
                return cls._plan_selected_phase_dispatch(
                    phase,
                    rope_workspace,
                    sources,
                    selected,
                    import_normalizer,
                )
            case (
                c.Infra.SemanticCutoverPhase.MODULE_END
                | c.Infra.SemanticCutoverPhase.NOTICE_LAST
            ):
                return cls._plan_ordered_phase(phase, root, sources, selected)

    @classmethod
    def _plan_behavior_and_declarations(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Keep consumer rebinding and declaration relocation in one candidate.

        Args:
            rope_workspace: The rope workspace for refactoring.
            sources: A mapping of source file paths to their contents.

        Returns:
            A result containing a tuple of semantic migration edits.

        """
        with closing(
            FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                rope_workspace.rope_project, sources
            )
        ) as project:
            consumers = cls._plan_behavior_consumers(
                rope_workspace.repository_root, sources, native_project=project
            )
        if consumers.failure:
            return consumers
        working = dict(sources)
        for edit in consumers.value:
            working[edit.file_path] = edit.updated_source
        declarations = cls._plan_declaration_relocation(rope_workspace, working)
        if declarations.failure:
            return declarations
        for edit in declarations.value:
            working[edit.file_path] = edit.updated_source
        if consumers.value:
            cls._preflight_declaration_graph(rope_workspace, sources, working)
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    changes=("resolved behavior and declaration ownership",),
                )
                for path, source in sources.items()
                if working[path] != source
            )
        )

    @classmethod
    def _plan_selected_phase_dispatch(
        cls,
        phase: c.Infra.SemanticCutoverPhase,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
        selected: t.SequenceOf[m.Infra.ModOccurrence],
        import_normalizer: p.Infra.SourceImportNormalizer | None,
    ) -> p.ResultView[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        root = rope_workspace.repository_root
        dispatch = {
            c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION: lambda: (
                cls._plan_behavior_and_declarations(rope_workspace, sources)
            ),
            c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS: lambda: (
                cls._plan_constant_consumers(rope_workspace, sources)
            ),
            c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION: lambda: (
                cls._plan_rope_contracts(rope_workspace, sources)
            ),
            c.Infra.SemanticCutoverPhase.COMPAT_ALIAS: lambda: cls._plan_alias_cutover(
                rope_workspace, sources, selected, import_normalizer
            ),
            c.Infra.SemanticCutoverPhase.PRIVATE_IMPORT: lambda: (
                cls._plan_private_imports(root, sources, selected)
            ),
            c.Infra.SemanticCutoverPhase.FACADE_BASE: lambda: cls._plan_facade_bases(
                root, sources, selected
            ),
            c.Infra.SemanticCutoverPhase.MODEL_FIELDS: lambda: cls._plan_model_fields(
                sources
            ),
        }
        factory = dispatch.get(phase)
        if factory is None:
            message = f"unsupported semantic cutover phase: {phase}"
            raise ValueError(message)
        return factory()

    @classmethod
    def _plan_alias_cutover(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
        selected: t.SequenceOf[m.Infra.ModOccurrence],
        import_normalizer: p.Infra.SourceImportNormalizer | None,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose model-alias retirement with existing API-alias policy.

        Returns:
            The composed migration edits, or the first planning failure.

        """
        aliases = FlextInfraUtilitiesSemanticModelAliases.plan_model_aliases(
            workspace, sources
        )
        if aliases.failure:
            return aliases
        working = dict(sources)
        working.update((edit.file_path, edit.updated_source) for edit in aliases.value)
        api = cls._plan_api_aliases(workspace, working, selected, import_normalizer)
        if api.failure:
            return api
        working.update((edit.file_path, edit.updated_source) for edit in api.value)
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    changes=("composed native alias retirement",),
                )
                for path, source in sources.items()
                if working[path] != source
            )
        )

    @classmethod
    def _plan_ordered_phase(
        cls,
        phase: c.Infra.SemanticCutoverPhase,
        root: Path,
        sources: t.MappingKV[Path, str],
        selected: t.SequenceOf[m.Infra.ModOccurrence],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan one order-driven cutover phase.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        Raises:
            ValueError: When the phase is not order-driven.

        """
        match phase:
            case c.Infra.SemanticCutoverPhase.MODULE_END:
                return cls._plan_module_end(root, sources, selected)
            case c.Infra.SemanticCutoverPhase.NOTICE_LAST:
                return cls._plan_notice_last(root, sources, selected)
            case _:
                message = f"unsupported semantic cutover phase: {phase}"
                raise ValueError(message)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverBase"]
