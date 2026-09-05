"""Destination-local staging for complete newest-Mise artifact sets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import config, m, u
from flext_infra.codegen import (
    _mise_artifacts_candidates as candidates,
    _mise_artifacts_files as files,
    _mise_artifacts_process as process,
)
from flext_infra.codegen._mise_artifacts_runtime import FlextInfraMiseRuntime

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseStaging:
    """Build every replacement before the journal permits live publication."""

    def __init__(self, owner: p.Infra.MiseArtifactsOwner) -> None:
        self._owner = owner
        self._runtime = FlextInfraMiseRuntime(owner)

    def stage(
        self,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        *,
        credential_command: str | None,
        reuse_live: bool,
    ) -> p.Result[tuple[m.Cli.AtomicFilePublication, ...]]:
        """Generate, hydrate, and validate all destination-local candidates."""
        if reuse_live:
            return self._stage_live(plan)
        if credential_command is None:
            return r[tuple[m.Cli.AtomicFilePublication, ...]].fail(
                "Mise materialization requires an authenticated credential command"
            )
        receipt = self._runtime.latest_receipt(
            plan.projects[0], credential_command=credential_command
        )
        if receipt.failure:
            return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(receipt)
        runtime_scratch = plan.projects[0].layout.transaction_root / "runtime"
        environment = process.credential_environment(
            runtime_scratch, credential_command
        )
        launcher = receipt.value / "bin" / ("mise.cmd" if os.name == "nt" else "mise")
        credential = process.validate_credential_source(
            launcher,
            cwd=runtime_scratch,
            env=environment,
            timeout_seconds=config.Infra.codegen.toolchain.mise_network_timeout_seconds,
        )
        if credential.failure:
            return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(credential)
        receipt_states = candidates.receipt_states(receipt.value)
        if receipt_states.failure:
            return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(
                receipt_states
            )
        staged_projects: list[tuple[m.Infra.MiseToolchainProjectState, Path]] = []
        for project in plan.projects:
            stage_root = project.layout.transaction_root / "stage"
            staged = self._prepare_project(
                project, stage_root=stage_root, receipt_states=receipt_states.value
            )
            if staged.failure:
                return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(staged)
            staged_projects.append((project, stage_root))
        grouped: dict[bytes, list[tuple[m.Infra.MiseToolchainProjectState, Path]]] = {}
        for project, stage_root in staged_projects:
            grouped.setdefault(project.config.replacement_content, []).append((
                project,
                stage_root,
            ))
        for group_index, group in enumerate(grouped.values(), start=1):
            representative, representative_stage = group[0]
            u.Cli.info(
                "mise-toolchain: resolve "
                f"group={group_index}/{len(grouped)} projects={len(group)} "
                f"owner={representative.layout.selector}"
            )
            generated = self._generate_lock(
                representative,
                stage_root=representative_stage,
                launcher=launcher,
                environment=environment,
            )
            if generated.failure:
                return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(
                    generated
                )
            for project, stage_root in group:
                if stage_root != representative_stage:
                    reused = self._reuse_lock(representative_stage, stage_root)
                    if reused.failure:
                        return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(
                            reused
                        )
                validated = self._validate_project(project, stage_root)
                if validated.failure:
                    return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(
                        validated
                    )
        return candidates.publication_plan(
            plan.projects, tuple(stage for _, stage in staged_projects)
        )

    def _stage_live(
        self, plan: m.Infra.MiseToolchainWorkspacePlan
    ) -> p.Result[tuple[m.Cli.AtomicFilePublication, ...]]:
        """Stage the already-validated immutable toolchain without network work."""
        staged_projects: list[tuple[m.Infra.MiseToolchainProjectState, Path]] = []
        for project in plan.projects:
            stage_root = project.layout.transaction_root / "stage"
            try:
                (stage_root / "bin").mkdir(parents=True, exist_ok=False)
            except OSError as exc:
                return r[tuple[m.Cli.AtomicFilePublication, ...]].fail_op(
                    f"create Mise stage for {project.layout.selector}", exc
                )
            states = (
                project.config.before,
                project.artifacts.unix_launcher,
                project.artifacts.windows_launcher,
                project.artifacts.lock,
            )
            for source, (name, mode) in zip(
                states, files.PUBLICATION_SPECS, strict=True
            ):
                if source.content is None:
                    return r[tuple[m.Cli.AtomicFilePublication, ...]].fail(
                        f"validated live Mise artifact is absent: {source.path}"
                    )
                copied = u.Cli.atomic_create_binary_file_guarded(
                    stage_root / name, source.content, permission_mode=mode
                )
                if copied.failure:
                    return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(
                        copied
                    )
            validated = self._validate_project(project, stage_root)
            if validated.failure:
                return r[tuple[m.Cli.AtomicFilePublication, ...]].from_failure(
                    validated
                )
            staged_projects.append((project, stage_root))
        return candidates.publication_plan(
            plan.projects, tuple(stage for _, stage in staged_projects)
        )

    @staticmethod
    def _prepare_project(
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        receipt_states: tuple[m.Cli.AtomicFileState, ...],
    ) -> p.Result[bool]:
        """Stage immutable config and launchers without resolving the network."""
        try:
            (stage_root / "bin").mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            return r[bool].fail_op(
                f"create Mise stage for {project.layout.selector}", exc
            )
        config_write = u.Cli.atomic_create_binary_file_guarded(
            stage_root / files.CONFIG_SPEC[0],
            project.config.replacement_content,
            permission_mode=project.config.replacement_mode,
        )
        if config_write.failure:
            return config_write
        for source, (name, mode) in zip(
            receipt_states, files.ARTIFACT_SPECS[:2], strict=True
        ):
            if source.content is None:
                return r[bool].fail(f"validated Mise receipt is absent: {name}")
            copied = u.Cli.atomic_create_binary_file_guarded(
                stage_root / name, source.content, permission_mode=mode
            )
            if copied.failure:
                return copied
        return r[bool].ok(True)

    def _generate_lock(
        self,
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        launcher: Path,
        environment: dict[str, str],
    ) -> p.Result[bool]:
        """Resolve one unique staged config into a complete validated lock."""
        project_environment = dict(environment)
        project_environment.update({
            "MISE_CEILING_PATHS": str(stage_root.parent),
            "MISE_TRUSTED_CONFIG_PATHS": str(stage_root),
        })
        locked = process.run_live(
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
            output_path=stage_root.parent / "mise-lock.log",
            timeout_seconds=config.Infra.codegen.toolchain.mise_lock_timeout_seconds,
        )
        if locked.failure:
            return r[bool].from_failure(locked)
        hydrated = self._owner.hydrate_lock_checksums_at(stage_root)
        if hydrated.failure:
            return r[bool].fail(
                hydrated.error
                or f"Mise checksum hydration failed for {project.layout.selector}"
            )
        normalized = candidates.normalize_lock_mode(stage_root / "mise.lock")
        if normalized.failure:
            return normalized
        return r[bool].ok(True)

    @staticmethod
    def _reuse_lock(source_stage: Path, target_stage: Path) -> p.Result[bool]:
        """Reuse a lock only when its generated config bytes are identical."""
        source_config = u.Cli.atomic_read_binary_file_state(
            source_stage / files.CONFIG_SPEC[0], required=True
        )
        target_config = u.Cli.atomic_read_binary_file_state(
            target_stage / files.CONFIG_SPEC[0], required=True
        )
        if (
            source_config.failure
            or target_config.failure
            or source_config.value.content != target_config.value.content
        ):
            return r[bool].fail("Mise lock reuse requires identical staged configs")
        source_lock = u.Cli.atomic_read_binary_file_state(
            source_stage / "mise.lock", required=True
        )
        if source_lock.failure or source_lock.value.content is None:
            return r[bool].fail(source_lock.error or "generated Mise lock is absent")
        return u.Cli.atomic_create_binary_file_guarded(
            target_stage / "mise.lock", source_lock.value.content, permission_mode=0o644
        )

    def _validate_project(
        self, project: m.Infra.MiseToolchainProjectState, stage_root: Path
    ) -> p.Result[bool]:
        """Validate one staged project against its own source authority."""
        validated = self._owner.validate_artifacts(
            stage_root, config_sources=project.config.sources
        )
        if validated.failure:
            return r[bool].fail(
                validated.error
                or f"Mise artifact validation failed for {project.layout.selector}"
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraMiseStaging"]
