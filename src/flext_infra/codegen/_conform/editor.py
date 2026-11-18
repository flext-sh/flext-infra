"""Project editor configuration without evaluating Python source facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, u
from flext_infra.codegen._conform.artifact_render import (
    FlextInfraCodegenConformArtifactRender,
)
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.services._codegen import FlextInfraCodegenVscode


class FlextInfraCodegenConformEditor(
    FlextInfraCodegenConformArtifactRender,
    FlextInfraCodegenVscode,
):
    """Compose existing editor, analyzer and Git-ignore owners into one plan."""

    @staticmethod
    def _editor_snapshots(
        root: Path, destinations: frozenset[str]
    ) -> p.Result[Mapping[str, p.Cli.AtomicFileState]]:
        """Read every destination before rendering its replacement.

        Returns:
            The destination file states.

        """
        result_type = r[Mapping[str, m.Cli.AtomicFileState]]
        original: MutableMapping[str, p.Cli.AtomicFileState] = {}
        for relative in sorted(destinations):
            observed = u.Infra.codegen_target_snapshot(root / relative)
            if observed.failure:
                return result_type.from_failure(observed)
            original[relative] = observed.value
        return result_type.ok(original)

    def _editor_manifest(
        self,
        target: p.Infra.RepositoryConformTarget,
        codegen: p.Infra.CodegenConfigSpec,
        captured: p.Cli.AtomicFileState,
    ) -> p.Result[tuple[str, tuple[p.Cli.AtomicFileState, ...]]]:
        """Render the analyzer table against the project manifest.

        Returns:
            The formatted manifest and its consumed tooling declarations.

        """
        result_type = r[tuple[str, tuple[p.Cli.AtomicFileState, ...]]]
        tooling = u.Infra.load_tooling_inputs(target.root)
        if tooling.failure:
            return result_type.from_failure(tooling)
        tool_config = tooling.value.document
        if captured.content is None:
            return result_type.fail(
                f"editor projection requires {c.PYPROJECT_FILENAME}"
            )
        manifest = FlextInfraPyprojectModernizer(
            repository_root=target.root, skip_check=True
        ).render_analyzer_source(
            captured.content.decode(c.DEFAULT_ENCODING),
            path=captured.path,
            topology=self._existing_topology(target, codegen),
            codegen=codegen,
            tool_config=tool_config,
        )
        if manifest.failure:
            return result_type.from_failure(manifest)
        return u.Infra.format_toml_source(
            manifest.value,
            path=target.root / c.PYPROJECT_FILENAME,
            toolchain_root=self.state.repository_root,
            taplo_version=codegen.toolchain.tool_versions["taplo"],
        ).map(lambda text: (text, tooling.value.sources))

    def _plan_existing_editor(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Bind editor projections to the declarations read in this request.

        Returns:
            The atomic publisher's ordinary governed file plans.

        """
        result_type = r[Sequence[p.Infra.CodegenFilePlan]]
        artifacts = u.Infra.snapshot_project_managed_artifacts(target.root)
        if artifacts.failure:
            return result_type.from_failure(artifacts)
        render_inputs = self.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=None,
            managed_artifacts=artifacts.value,
        )
        selected = self._editor_destinations(codegen)
        original = self._editor_snapshots(target.root, selected)
        if original.failure:
            return result_type.from_failure(original)
        plans: list[p.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_file_specs:
            relative = managed.path.as_posix()
            if relative not in selected:
                continue
            entry = next(
                entry
                for entry in codegen.templates.entries
                if Path(entry.destination) == managed.path
            )
            if target.make_profile not in entry.profiles:
                continue
            content = self._editor_content(
                render_inputs, entry, managed, original.value[relative]
            )
            if content.failure:
                return result_type.from_failure(content)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=target.root,
                    path=target.root / relative,
                    before=original.value[relative],
                    desired_content=content.value[0].encode(c.DEFAULT_ENCODING),
                    desired_mode=managed.mode,
                    owner=managed.owner,
                    policy=managed.policy,
                    tracking=managed.tracking,
                    inputs=(
                        *workspace.inputs,
                        *target.vscode_sources,
                        *(
                            artifacts.value.sources
                            if relative == c.Infra.GITIGNORE
                            else ()
                        ),
                        *content.value[1],
                    ),
                )
            )
        return result_type.ok(tuple(plans))

    def _editor_content(
        self,
        render_inputs: p.Infra.CodegenRenderInputs,
        entry: p.Infra.TemplateEntrySpec,
        managed: p.Infra.ManagedFileSpec,
        before: p.Cli.AtomicFileState,
    ) -> p.Result[tuple[str, tuple[p.Cli.AtomicFileState, ...]]]:
        """Render the one editor projection owned by ``relative``.

        Returns:
            The canonical text and consumed template source observations.

        """
        target = render_inputs.target
        codegen = render_inputs.codegen
        relative = managed.path.as_posix()
        if relative == c.PYPROJECT_FILENAME:
            return self._editor_manifest(target, codegen, before)
        if managed.owner == c.Infra.CODEGEN_OWNER_VSCODE:
            return self.render_vscode_settings(
                target.root, spec=codegen.vscode, codegen=codegen
            ).map(lambda text: (text, ()))
        return self._rendered_artifact_source(
            render_inputs,
            m.Infra.ArtifactRenderRoute.model_validate({
                "entry": entry,
                "destination": relative,
                "failure_prefix": "",
                "project_context": None,
            }),
        ).flat_map(
            lambda rendered: self.compose_project_artifact(
                target.root,
                relative,
                rendered.rendered,
                render_inputs=render_inputs,
            ).map(lambda text: (text, rendered.source_states))
        )


__all__: list[str] = ["FlextInfraCodegenConformEditor"]
