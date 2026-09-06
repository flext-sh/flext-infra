"""Destination-local staging for complete newest-Mise artifact sets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.codegen import _mise_artifacts_candidates as candidates
from flext_infra.codegen import _mise_artifacts_files as files
from flext_infra.codegen import _mise_artifacts_process as process
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
        resolution: c.Infra.MiseResolutionMode,
        credential_command: str,
    ) -> p.Result[tuple[m.Infra.MiseToolchainPublication, ...]]:
        """Generate, hydrate, and validate all destination-local candidates.

        Online resolution regenerates the newest launcher through the isolated
        seed and re-resolves every moving selector with ``mise lock --bump``.
        Offline resolution copies the published launchers and lock, so the same
        sources produce the same bytes without reaching any registry; a project
        that has never published an artifact cannot be staged offline.
        """
        result_type = r[tuple[m.Infra.MiseToolchainPublication, ...]]
        online = resolution is c.Infra.MiseResolutionMode.ONLINE
        launcher: Path | None = None
        environment: dict[str, str] = {}
        receipt_states: tuple[m.Cli.AtomicFileState, ...] | None = None
        if online:
            data_root = plan.layout.state_root / files.BOOTSTRAP_DIR_NAME
            receipt = self._runtime.latest_receipt(
                plan.projects[0],
                data_root=data_root,
                credential_command=credential_command,
            )
            if receipt.failure:
                return result_type.from_failure(receipt)
            runtime_scratch = plan.projects[0].layout.transaction_root / "runtime"
            environment = process.credential_environment(
                runtime_scratch, data_root=data_root, command=credential_command
            )
            launcher = (
                receipt.value / "bin" / ("mise.cmd" if os.name == "nt" else "mise")
            )
            credential = process.validate_credential_source(
                launcher, cwd=runtime_scratch, env=environment
            )
            if credential.failure:
                return result_type.from_failure(credential)
            resolved_states = candidates.receipt_states(receipt.value)
            if resolved_states.failure:
                return result_type.from_failure(resolved_states)
            receipt_states = resolved_states.value
        stages: list[Path] = []
        for project in plan.projects:
            stage_root = project.layout.transaction_root / "stage"
            published = self._published_launchers(project)
            if receipt_states is None and published.failure:
                return result_type.from_failure(published)
            staged = self._stage_project(
                project,
                stage_root=stage_root,
                launcher=launcher,
                receipt_states=receipt_states or published.value,
                environment=environment,
            )
            if staged.failure:
                return result_type.from_failure(staged)
            stages.append(stage_root)
        return candidates.publication_plan(plan.projects, tuple(stages))

    @staticmethod
    def _published_launchers(
        project: m.Infra.MiseToolchainProjectState,
    ) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
        """Return the published launcher pair an offline stage copies verbatim."""
        artifacts = project.artifacts
        launchers = (artifacts.unix_launcher, artifacts.windows_launcher)
        if artifacts.lock.content is None or any(
            launcher.content is None for launcher in launchers
        ):
            return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                "offline Mise resolution cannot stage an unpublished toolchain "
                f"for {project.layout.selector}; network access is required"
            )
        return r[tuple[m.Cli.AtomicFileState, ...]].ok(launchers)

    def _stage_project(
        self,
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        launcher: Path | None,
        receipt_states: tuple[m.Cli.AtomicFileState, ...],
        environment: dict[str, str],
    ) -> p.Result[bool]:
        """Build and validate one project without reading mutable source bytes."""
        try:
            (stage_root / "bin").mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            return r[bool].fail_op(
                f"create Mise stage for {project.layout.selector}", exc
            )
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
                stage_root / "mise.lock", lock_before.content, 0o644
            )
            if copied_lock.failure:
                return copied_lock
        if launcher is not None:
            u.Cli.info(f"mise-toolchain: resolving lock for {project.layout.selector}")
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
            u.Cli.info(
                f"mise-toolchain: hydrating lock checksums for {project.layout.selector}"
            )
        hydrated = self._owner.hydrate_lock_checksums_at(stage_root)
        if hydrated.failure:
            return r[bool].fail(
                hydrated.error
                or f"Mise checksum hydration failed for {project.layout.selector}"
            )
        normalized = candidates.normalize_lock_mode(stage_root / "mise.lock")
        if normalized.failure:
            return normalized
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
