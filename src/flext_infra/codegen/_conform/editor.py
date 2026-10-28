"""Project editor configuration without evaluating Python source facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, deps as dependency_services, m, p, r, t, u
from flext_infra.codegen._conform.artifact_render import (
    FlextInfraCodegenConformArtifactRender,
)
from flext_infra.services._codegen.vscode import FlextInfraCodegenVscode


class FlextInfraCodegenConformEditor(
    FlextInfraCodegenConformArtifactRender,
    FlextInfraCodegenVscode,
):
    """Compose existing editor, analyzer and Git-ignore owners into one plan."""

    @staticmethod
    def _editor_snapshots(
        root: Path, destinations: frozenset[str]
    ) -> p.Result[t.MappingKV[str, m.Cli.AtomicFileState]]:
        """Read every destination before rendering its replacement.

        Returns:
            The destination file states.

        """
        result_type = r[t.MappingKV[str, m.Cli.AtomicFileState]]
        original: t.MutableMappingKV[str, m.Cli.AtomicFileState] = {}
        for relative in sorted(destinations):
            observed = u.Infra.codegen_target_snapshot(root / relative)
            if observed.failure:
                return result_type.from_failure(observed)
            original[relative] = observed.value
        return result_type.ok(original)

    def _editor_manifest(
        self,
        target: m.Infra.RepositoryConformTarget,
        codegen: m.Infra.CodegenConfigSpec,
        captured: m.Cli.AtomicFileState,
    ) -> p.Result[str]:
        """Render the analyzer table against the project manifest.

        Returns:
            The formatted manifest.

        """
        result_type = r[str]
        tooling = u.Infra.load_tooling_inputs(target.root)
        if tooling.failure:
            return result_type.from_failure(tooling)
        tool_config = tooling.value.document
        if captured.content is None:
            return result_type.fail(
                f"editor projection requires {c.PYPROJECT_FILENAME}"
            )
        manifest = dependency_services.FlextInfraEnsurePyrightConfigPhase(
            tool_config, codegen=codegen
        ).render_source(
            captured.content.decode(c.DEFAULT_ENCODING),
            context=m.Infra.PyprojectAnalyzerContext(
                is_root=target.make_profile is c.Infra.MakeProfile.WORKSPACE,
                repository_root=target.root,
                project_dir=target.root,
            ),
        )
        if manifest.failure:
            return result_type.from_failure(manifest)
        return u.Infra.format_toml_source(
            manifest.value,
            path=target.root / c.PYPROJECT_FILENAME,
            toolchain_root=self.state.repository_root,
            taplo_version=codegen.toolchain.tool_versions["taplo"],
        )

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
        original = self._editor_snapshots(target.root, destinations)
        if original.failure:
            return result_type.from_failure(original)
        manifest = self._editor_manifest(
            target, codegen, original.value[c.PYPROJECT_FILENAME]
        )
        if manifest.failure:
            return result_type.from_failure(manifest)
        settings = self.render_vscode_settings(
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
        plans: list[m.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_file_specs:
            relative = managed.path.as_posix()
            if relative not in destinations:
                continue
            content = (
                manifest.value
                if relative == c.PYPROJECT_FILENAME
                else (
                    ignored.value if relative == c.Infra.GITIGNORE else settings.value
                )
            )
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=target.root,
                    path=target.root / relative,
                    before=original.value[relative],
                    desired_content=content.encode(c.DEFAULT_ENCODING),
                    desired_mode=managed.mode,
                    owner=managed.owner,
                    policy=managed.policy,
                    tracking=managed.tracking,
                )
            )
        return result_type.ok(tuple(plans))


__all__: list[str] = ["FlextInfraCodegenConformEditor"]
