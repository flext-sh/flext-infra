"""Project editor configuration without evaluating Python source facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen._conform.artifact_render import (
    FlextInfraCodegenConformArtifactRender,
)
from flext_infra.deps import FlextInfraEnsurePyrightConfigPhase
from flext_infra.services._codegen.vscode import FlextInfraCodegenVscodeMixin


class FlextInfraCodegenConformEditor(FlextInfraCodegenConformArtifactRender):
    """Compose existing editor, analyzer and Git-ignore owners into one plan."""

    def _plan_existing_editor(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Bind all editor projections to the declarations read in this request.

        Returns:
            The atomic publisher's ordinary governed file plans.

        """
        result_type = r[t.SequenceOf[m.Infra.CodegenFilePlan]]
        loaded = u.Infra.load_codegen_inputs(target.root)
        if loaded.failure:
            return result_type.from_failure(loaded)
        codegen = loaded.value.spec
        destinations = self._editor_destinations(codegen)
        original: t.MutableMappingKV[
            str, m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan
        ] = {}
        for relative in sorted(destinations):
            observed = u.Infra.codegen_target_snapshot(target.root / relative)
            if observed.failure:
                return result_type.from_failure(observed)
            original[relative] = observed.value
        tooling = u.Infra.load_config_document_inputs(
            target.root, filename="tooling.yaml"
        )
        if tooling.failure:
            return result_type.from_failure(tooling)
        namespace = u.json_mapping_adapter().validate_python(
            tooling.value.values["Infra"]
        )
        tool_config = m.Infra.ToolConfigDocument.model_validate(namespace["tooling"])
        captured = original[c.PYPROJECT_FILENAME]
        if (
            isinstance(captured, m.Cli.AtomicDirectoryChainPlan)
            or captured.content is None
        ):
            return result_type.fail(
                f"editor projection requires {c.PYPROJECT_FILENAME}"
            )
        phase = FlextInfraEnsurePyrightConfigPhase(tool_config, codegen=codegen)
        manifest = phase.render_source(
            captured.content.decode(c.DEFAULT_ENCODING),
            context=m.Infra.PyprojectAnalyzerContext(
                is_root=target.make_profile is c.Infra.MakeProfile.WORKSPACE,
                repository_root=target.root,
                project_dir=target.root,
            ),
        )
        if manifest.failure:
            return result_type.from_failure(manifest)
        formatted = u.Infra.format_toml_source(
            manifest.value,
            path=target.root / c.PYPROJECT_FILENAME,
            toolchain_root=self.state.repository_root,
            taplo_version=codegen.toolchain.tool_versions["taplo"],
        )
        if formatted.failure:
            return result_type.from_failure(formatted)
        settings = FlextInfraCodegenVscodeMixin.render_vscode_settings(
            target.root, spec=codegen.vscode, codegen=codegen
        )
        if settings.failure:
            return result_type.from_failure(settings)
        ignored = u.Infra.render_project_gitignore(
            codegen,
            profile=target.make_profile,
            project_name=target.repository.name,
            workspace=workspace,
            project_dir=target.root,
        )
        if ignored.failure:
            return result_type.from_failure(ignored)
        sources = (
            *loaded.value.sources,
            *tooling.value.sources,
            *(
                state
                for state in original.values()
                if isinstance(state, m.Cli.AtomicFileState)
            ),
        )
        plans: list[m.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_file_specs:
            relative = managed.path.as_posix()
            if relative not in destinations:
                continue
            content = (
                formatted.value
                if relative == c.PYPROJECT_FILENAME
                else (
                    ignored.value if relative == c.Infra.GITIGNORE else settings.value
                )
            )
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=target.root,
                    path=target.root / relative,
                    before=original[relative],
                    desired_content=content.encode(c.DEFAULT_ENCODING),
                    desired_mode=managed.mode,
                    source_states=sources,
                    owner=managed.owner,
                    policy=managed.policy,
                    tracking=managed.tracking,
                )
            )
        return result_type.ok(tuple(plans))
