"""Destination-local staging for complete newest-Mise artifact sets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import (
    _mise_artifacts_candidates as candidates,
    _mise_artifacts_files as files,
    _mise_artifacts_process as process,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseStaging:
    """Build every replacement before the journal permits live publication."""

    def __init__(self, owner: p.Infra.MiseArtifactsOwner) -> None:
        self._owner = owner

    def stage(
        self, plan: m.Infra.MiseToolchainWorkspacePlan
    ) -> p.Result[tuple[m.Infra.CodegenStagedFile, ...]]:
        """Stage and validate the committed lock selected before publication."""
        stages: list[Path] = []
        for project in plan.projects:
            if project.layout.transaction_root is None:
                return r[tuple[m.Infra.CodegenStagedFile, ...]].fail(
                    f"Mise transaction root is absent: {project.layout.selector}"
                )
            stage_root = project.layout.transaction_root / "stage"
            staged = self._stage_project(project, stage_root=stage_root)
            if staged.failure:
                return r[tuple[m.Infra.CodegenStagedFile, ...]].from_failure(staged)
            stages.append(stage_root)
        runtime_inventory = u.Cli.atomic_inventory_physical_tree(runtime_scratch)
        if runtime_inventory.failure:
            return r[tuple[m.Infra.CodegenStagedFile, ...]].from_failure(
                runtime_inventory
            )
        runtime_cleanup = u.Cli.atomic_cleanup_physical_tree_guarded(
            runtime_inventory.value
        )
        if runtime_cleanup.failure:
            return r[tuple[m.Infra.CodegenStagedFile, ...]].from_failure(
                runtime_cleanup
            )
        return candidates.publication_plan(plan.projects, tuple(stages))

    @staticmethod
    def _lock_resolution_is_required(
        project: m.Infra.MiseToolchainProjectState,
    ) -> bool:
        """Return whether this project's lock must be resolved from the network."""
        return (
            project.artifacts.lock.content is None
            or project.config.before.content != project.config.replacement_content
        )

    def _stage_project(
        self, project: m.Infra.MiseToolchainProjectState, *, stage_root: Path
    ) -> p.Result[bool]:
        """Build and validate one project without reading mutable source bytes."""
        stage_plan = u.Cli.atomic_plan_directory_chain(
            stage_root / c.Infra.MISE_LAUNCHER_DIRECTORY
        )
        if stage_plan.failure:
            return r[bool].from_failure(stage_plan)
        if tuple(stage_plan.value.directories) != (
            stage_root,
            stage_root / c.Infra.MISE_LAUNCHER_DIRECTORY,
        ):
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
            receipt_states, files.ARTIFACT_SPECS[:2], strict=True
        ):
            if source.content is None:
                return r[bool].fail(f"validated Mise receipt is absent: {name}")
            copied = process.write_new(stage_root / name, source.content, mode)
            if copied.failure:
                return copied
        lock_before = project.artifacts.lock
        if lock_before.content is not None:
            copied_lock = process.write_new(
                stage_root / c.Infra.MISE_LOCK_FILENAME,
                lock_before.content,
                files.ARTIFACT_SPECS[2][1],
            )
            if copied_lock.failure:
                return copied_lock
        if self._lock_resolution_is_required(project):
            project_environment = dict(environment)
            project_environment.update({
                "MISE_CEILING_PATHS": str(stage_root.parent),
                "MISE_TRUSTED_CONFIG_PATHS": str(stage_root),
            })
            locked = process.run(
                (
                    str(launcher),
                    "-C",
                    str(stage_root),
                    "lock",
                    "--bump",
                    "--platform",
                    ",".join(config.Infra.codegen.toolchain.mise_lock_platforms),
                ),
                cwd=stage_root,
                env=project_environment,
                operation=f"Mise lock generation for {project.layout.selector}",
            )
            if locked.failure:
                return r[bool].from_failure(locked)
        hydrated = self._owner.hydrate_lock_checksums_at(stage_root)
        if hydrated.failure:
            return r[bool].fail(
                hydrated.error
                or f"Mise checksum hydration failed for {project.layout.selector}"
            )
        normalized = candidates.normalize_lock_mode(
            stage_root / c.Infra.MISE_LOCK_FILENAME
        )
        if normalized.failure:
            return normalized
        validated = self._owner.validate_artifacts(stage_root)
        if validated.failure:
            return r[bool].from_failure(validated)
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraMiseStaging"]
