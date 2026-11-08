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
from flext_infra.deps.phases import FlextInfraEnsurePyrightConfigPhase
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
        manifest = FlextInfraEnsurePyrightConfigPhase(
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
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Bind editor projections to the declarations read in this request.

        Returns:
            The atomic publisher's ordinary governed file plans.

        """
        result_type = r[Sequence[p.Infra.CodegenFilePlan]]
        loaded = u.Infra.load_codegen_inputs(target.root)
        if loaded.failure:
            return result_type.from_failure(loaded)
        codegen = loaded.value.spec
        selected = self._editor_destinations(codegen)
        original = self._editor_snapshots(target.root, selected)
        if original.failure:
            return result_type.from_failure(original)
        plans: list[p.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_file_specs:
            relative = managed.path.as_posix()
            if relative not in selected:
                continue
            content = self._editor_content(
                target, workspace, codegen, relative, original.value[relative]
            )
            if content.failure:
                return result_type.from_failure(content)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=target.root,
                    path=target.root / relative,
                    before=original.value[relative],
                    desired_content=content.value.encode(c.DEFAULT_ENCODING),
                    desired_mode=managed.mode,
                    owner=managed.owner,
                    policy=managed.policy,
                    tracking=managed.tracking,
                )
            )
        return result_type.ok(tuple(plans))

    def _editor_content(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
        relative: str,
        before: p.Cli.AtomicFileState,
    ) -> p.Result[str]:
        """Render the one editor projection owned by ``relative``.

        Returns:
            The canonical text of that destination.

        """
        if relative == c.PYPROJECT_FILENAME:
            return self._editor_manifest(target, codegen, before)
        if relative == c.Infra.GITIGNORE:
            return u.Infra.render_project_gitignore(
                codegen,
                profile=target.make_profile,
                project_name=target.repository.name,
                workspace=workspace,
                project_dir=target.root,
            )
        return self.render_vscode_settings(
            target.root, spec=codegen.vscode, codegen=codegen
        )


__all__: list[str] = ["FlextInfraCodegenConformEditor"]
