"""Destination-local staging for complete newest-Mise artifact sets."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, u

from ._mise_artifacts_candidates import publication_plan
from ._mise_artifacts_files import FlextInfraMiseArtifactsFiles as files
from ._mise_artifacts_process import FlextInfraMiseArtifactsProcess as process

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraMiseStaging:
    """Build every replacement before the journal permits live publication."""

    def stage(
        self, plan: m.Infra.MiseToolchainWorkspacePlan
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Infra.CodegenStagedFile],
            t.VariadicTuple[m.Cli.AtomicDirectoryState],
        ]
    ]:
        """Stage the packaged launcher fleet alongside each declaration."""
        result_type = r[
            tuple[
                tuple[m.Infra.CodegenStagedFile, ...],
                tuple[m.Cli.AtomicDirectoryState, ...],
            ]
        ]
        if not plan.projects:
            return result_type.fail("Mise plan declares no projects")
        packaged = files.packaged_launchers()
        if packaged.failure:
            return result_type.from_failure(packaged)
        return self._stage_projects(plan, packaged.value)

    def _stage_projects(
        self,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        seed_launchers: t.VariadicTuple[bytes],
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Infra.CodegenStagedFile],
            t.VariadicTuple[m.Cli.AtomicDirectoryState],
        ]
    ]:
        """Stage the seed launcher pair into every selected project."""
        result_type = r[
            tuple[
                tuple[m.Infra.CodegenStagedFile, ...],
                tuple[m.Cli.AtomicDirectoryState, ...],
            ]
        ]
        publications: list[m.Infra.CodegenStagedFile] = []
        directories: list[m.Cli.AtomicDirectoryState] = []
        for project in plan.projects:
            if project.layout.transaction_root is None:
                return result_type.fail(
                    f"Mise transaction root is absent: {project.layout.selector}"
                )
            stage_root = project.layout.transaction_root / "stage"
            staged = self._stage_project(
                project, stage_root=stage_root, seed_launchers=seed_launchers
            )
            if staged.failure:
                return result_type.from_failure(staged)
            receipts = publication_plan((project,), (stage_root,))
            if receipts.failure:
                return result_type.from_failure(receipts)
            publications.extend(receipts.value)
            directories.extend(staged.value)
        return result_type.ok((tuple(publications), tuple(directories)))

    def _stage_project(
        self,
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        seed_launchers: t.VariadicTuple[bytes],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicDirectoryState]]:
        """Build one project and retain its guarded directory creation receipts."""
        result_type = r[tuple[m.Cli.AtomicDirectoryState, ...]]
        stage_plan = u.Cli.atomic_plan_directory_chain(stage_root / "bin")
        if stage_plan.failure:
            return result_type.from_failure(stage_plan)
        if tuple(stage_plan.value.directories) != (stage_root, stage_root / "bin"):
            return result_type.fail(
                f"Mise stage already exists for {project.layout.selector}"
            )
        created = u.Cli.atomic_create_directory_chain_guarded(
            stage_plan.value, permission_mode=0o700
        )
        if created.failure:
            return result_type.from_failure(created)
        config_write = process.write_new(
            stage_root / c.Infra.CONFIG_SPEC[0],
            project.config.replacement_content,
            project.config.replacement_mode,
        )
        if config_write.failure:
            return result_type.from_failure(config_write)
        for content, (name, mode) in zip(
            seed_launchers, c.Infra.ARTIFACT_SPECS, strict=True
        ):
            copied = process.write_new(stage_root / name, content, mode)
            if copied.failure:
                return result_type.from_failure(copied)
        return result_type.ok(tuple(created.value))


__all__: list[str] = ["FlextInfraMiseStaging"]
