"""Destination-local staging for complete newest-Mise artifact sets."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import _mise_artifacts_candidates as candidates
from ._mise_artifacts_files import FlextInfraMiseArtifactsFiles as files
from ._mise_artifacts_process import FlextInfraMiseArtifactsProcess as process

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraMiseStaging:
    """Build every replacement before the journal permits live publication."""

    def __init__(self, owner: p.Infra.MiseArtifactsOwner) -> None:
        self._owner = owner

    def stage(
        self, plan: m.Infra.MiseToolchainWorkspacePlan
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]:
        """Stage the root-owned launcher fleet alongside each declaration."""
        if not plan.projects:
            return r[tuple[m.Infra.CodegenStagedFile, ...]].fail(
                "Mise plan declares no projects"
            )
        seed_project = next(
            (project for project in plan.projects if project.layout.selector == "."),
            plan.projects[0],
        )
        seed_launchers = (
            seed_project.artifacts.unix_launcher,
            seed_project.artifacts.windows_launcher,
        )
        if any(state.content is None for state in seed_launchers):
            return r[tuple[m.Infra.CodegenStagedFile, ...]].fail(
                f"Mise launcher seed is absent: {seed_project.layout.selector}"
            )
        stages: list[Path] = []
        for project in plan.projects:
            if project.layout.transaction_root is None:
                return r[tuple[m.Infra.CodegenStagedFile, ...]].fail(
                    f"Mise transaction root is absent: {project.layout.selector}"
                )
            stage_root = project.layout.transaction_root / "stage"
            staged = self._stage_project(
                project, stage_root=stage_root, seed_launchers=seed_launchers
            )
            if staged.failure:
                return r[tuple[m.Infra.CodegenStagedFile, ...]].from_failure(staged)
            stages.append(stage_root)
        return candidates.publication_plan(plan.projects, tuple(stages))

    def _stage_project(
        self,
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        seed_launchers: t.Pair[m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Build and validate one project without reading mutable source bytes."""
        stage_plan = u.Cli.atomic_plan_directory_chain(stage_root / "bin")
        if stage_plan.failure:
            return r[bool].from_failure(stage_plan)
        if tuple(stage_plan.value.directories) != (stage_root, stage_root / "bin"):
            return r[bool].fail(
                f"Mise stage already exists for {project.layout.selector}"
            )
        created = u.Cli.atomic_create_directory_chain_guarded(
            stage_plan.value, permission_mode=0o700
        )
        if created.failure:
            return r[bool].from_failure(created)
        config_write = process.write_new(
            stage_root / files.CONFIG_SPEC[0],
            project.config.replacement_content,
            project.config.replacement_mode,
        )
        if config_write.failure:
            return config_write
        for source, (name, mode) in zip(
            seed_launchers, files.ARTIFACT_SPECS, strict=True
        ):
            copied = process.write_new(stage_root / name, source.content, mode)
            if copied.failure:
                return copied
        validated = self._owner.validate_artifacts(stage_root)
        if validated.failure:
            return r[bool].from_failure(validated)
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraMiseStaging"]
