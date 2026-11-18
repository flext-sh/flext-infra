"""Facade-component phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import c, m, p, r, u
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.transformers._semantic import FlextInfraTransformersSemanticPublication


class FlextInfraCodemodLoopPhaseFacadeComponents:
    """Facade-component callback: domain owners, model nesting and consumers.

    Each transforms authored sources, which generation never does: a private
    ``_x`` domain's owner moves into the sibling module ``x.py`` that composes
    its parts (composed-part publication is single-owner), a singleton model
    nests under its family owner, and a callable reached through a composed
    component is rewired to its facade receiver. Generation only projects the
    facades these declarations determine.
    """

    name: str = "facade-components"

    def __init__(self) -> None:
        """Retain the protocol organization admitted by this phase's plan."""
        self.protocol_organization: p.Infra.ProtocolOrganizationPlan | None = None

    def plan(
        self,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan domain owners, model nesting, then the consumers they compose.

        Returns:
            The planned file plans, or the first planning failure.

        """
        del preflight
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        project = rope_workspace.rope_project
        files: list[p.Infra.CodegenFilePlan] = []
        objects = tuple(
            item
            for path in sorted(sources)
            if "_protocols" in path.parts
            for item in rope_workspace.objects(
                path, include_local_scopes=True, include_references=True
            )
        )
        census = u.Infra.protocol_contract_census(
            rope_workspace, sources=sources, objects=objects
        )
        self.protocol_organization = u.Infra.plan_protocol_contract_organization(
            rope_workspace, sources=sources, census=census
        )
        files.extend(self.protocol_organization.files)
        declared_files = u.Infra.codegen_compose_file_plans(
            (*project.source_plans, *files), ordered=True
        )
        rope_workspace.bind_candidate(declared_files=declared_files)
        sources = {
            **sources,
            **{
                plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                for plan in files
                if plan.desired_content is not None
            },
        }
        for project_root in u.Infra.governed_project_roots(root):
            if not u.Infra.namespace_enabled(project_root):
                continue
            codegen = u.Infra.load_codegen_inputs(project_root).unwrap().spec
            files.extend(
                rope_workspace.domain_owner_projection(
                    declared_files=u.Infra.codegen_compose_file_plans(
                        (*declared_files, *files), ordered=True
                    ),
                    initializer=FlextInfraCodegenLazyInit.plan_candidate,
                ).files
            )
            nested = u.Infra.plan_singleton_model_nesting(
                rope_workspace, sources, codegen
            )
            if nested.failure:
                return result_type.from_failure(nested)
            declared = {plan.path: plan for plan in files}
            files.extend(
                u.Infra.source_file_plan_from_edit(
                    project_root,
                    edit,
                    source_project=project,
                    declared_files=declared,
                )
                for edit in nested.value
            )
            files.extend(
                u.Infra.plan_component_consumers(
                    project_root,
                    source_project=project,
                    declared_files=tuple(files),
                )
            )
        return result_type.ok(tuple(files))

    @classmethod
    def apply(
        cls,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Publish the planned nesting and consumers with their lazy exports.

        Returns:
            Whether any source changed, or the first failure.

        """
        sources = {
            path: captured.text
            for path, captured in u.Infra.workspace_sources(
                rope_workspace.snapshot
            ).items()
        }
        planned = cls().plan(root, preflight, rope_workspace, sources=sources)
        if planned.failure:
            return r[bool].from_failure(planned)
        if not planned.value:
            return r[bool].ok(value=False)
        return (
            FlextInfraTransformersSemanticPublication.publish_semantic_artifact_plans(
                planned.value,
                repository_root=root,
                options=m.Infra.SemanticPublicationOptions(projection_roots=(root,)),
            ).map(bool)
        )


__all__: list[str] = ["FlextInfraCodemodLoopPhaseFacadeComponents"]
