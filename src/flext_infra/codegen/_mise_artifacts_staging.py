"""Destination-local staging for complete newest-Mise artifact sets."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, config, m, u
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
        """Generate, hydrate, and validate all destination-local candidates.

        The owner decides the resolution once, before any effect. Online
        resolution regenerates the newest launcher through the committed seed
        and re-resolves every moving selector with ``mise lock --bump``; offline
        resolution copies the committed launchers and lock, so the same sources
        produce the same bytes without reaching any registry, and a project
        that never published them cannot be staged offline.
        """
        result_type = r[tuple[m.Infra.CodegenStagedFile, ...]]
        resolution = self._owner.resolution_mode()
        u.Cli.info(f"mise-toolchain: resolution={resolution}")
        newest: tuple[Path, Path, dict[str, str]] | None = None
        if resolution is c.Infra.MiseResolutionMode.ONLINE:
            resolved = self._resolve_newest(plan.projects[0])
            if resolved.failure:
                return result_type.from_failure(resolved)
            newest = resolved.value
        stages: list[Path] = []
        for project in plan.projects:
            if project.layout.transaction_root is None:
                return result_type.fail(
                    f"Mise transaction root is absent: {project.layout.selector}"
                )
            stage_root = project.layout.transaction_root / "stage"
            staged = self._stage_project(project, stage_root=stage_root, newest=newest)
            if staged.failure:
                return result_type.from_failure(staged)
            stages.append(stage_root)
        return candidates.publication_plan(plan.projects, tuple(stages))

    def _resolve_newest(
        self, project: m.Infra.MiseToolchainProjectState
    ) -> p.Result[tuple[Path, Path, dict[str, str]]]:
        """Resolve the newest Mise release through the committed seed launcher.

        Mirrors the setup bootstrap: the seed generates a launcher for the
        newest release into the transaction receipt, and that launcher proves
        its own runtime identity from release-addressed persistent storage.
        Returns the receipt launcher, the receipt root and its environment.
        """
        result_type = r[tuple[Path, Path, dict[str, str]]]
        layout = project.layout
        if layout.transaction_root is None:
            return result_type.fail(
                f"Mise transaction root is absent: {layout.selector}"
            )
        scratch = layout.transaction_root / "runtime"
        contract = u.Infra.mise_bootstrap_environment()
        prepared = process.prepare_isolation(scratch, contract)
        if prepared.failure:
            return result_type.from_failure(prepared)
        storage = u.Infra.prepare_mise_runtime_storage(
            layout.root, os.environ, contract
        )
        if storage.failure:
            return result_type.from_failure(storage)
        seed_state = (
            project.artifacts.windows_launcher
            if os.name == "nt"
            else project.artifacts.unix_launcher
        )
        if seed_state.content is None or seed_state.mode is None:
            return result_type.fail(
                "online Mise resolution needs the committed seed launcher: "
                f"{seed_state.path}"
            )
        seed = scratch / "seed" / "bin" / seed_state.path.name
        written = process.write_new(seed, seed_state.content, seed_state.mode)
        if written.failure:
            return result_type.from_failure(written)
        seed_release = self._owner.validate_seed(seed)
        if seed_release.failure:
            return result_type.from_failure(seed_release)
        seed_environment = process.environment(
            scratch, storage.value, seed_release.value, contract
        )
        if seed_environment.failure:
            return result_type.from_failure(seed_environment)
        if "MISE_GITHUB_CREDENTIAL_COMMAND" not in seed_environment.value:
            return result_type.fail(
                "MISE_GITHUB_CREDENTIAL_COMMAND is required for online Mise "
                "toolchain resolution"
            )
        receipt = scratch / "receipt"
        generated = process.run(
            (
                str(seed),
                "-C",
                str(scratch),
                "generate",
                "install-script",
                "--write",
                str(receipt / "bin" / "mise"),
                "--windows",
            ),
            cwd=scratch,
            env=process.no_config_environment(seed_environment.value),
            operation="Mise newest launcher generation",
        )
        if generated.failure:
            return result_type.from_failure(generated)
        normalized = self._apply_receipt_modes(receipt)
        if normalized.failure:
            return result_type.from_failure(normalized)
        release = self._owner.launcher_release(receipt)
        if release.failure:
            return result_type.from_failure(release)
        launcher = receipt / "bin" / ("mise.cmd" if os.name == "nt" else "mise")
        environment = process.environment(
            scratch, storage.value, release.value, contract
        )
        if environment.failure:
            return result_type.from_failure(environment)
        identity = process.run(
            (str(launcher), "--version"),
            cwd=scratch,
            env=process.no_config_environment(environment.value),
            operation="Mise newest runtime identity",
        )
        if identity.failure:
            return result_type.from_failure(identity)
        runtime_release = identity.value.removeprefix("mise ").split(maxsplit=1)[0]
        if runtime_release != release.value:
            return result_type.fail(
                "Mise runtime differs from its exact receipt: "
                f"expected={release.value} actual={runtime_release}"
            )
        u.Cli.info(f"mise-toolchain: resolved newest runtime={release.value}")
        return result_type.ok((launcher, receipt, environment.value))

    @staticmethod
    def _apply_receipt_modes(receipt: Path) -> p.Result[bool]:
        """Publish the generated receipt launchers with their exact modes."""
        for name, mode in files.ARTIFACT_SPECS[:2]:
            state = files.read_state(receipt / name, required=True)
            if state.failure:
                return r[bool].from_failure(state)
            if state.value.content is None:
                return r[bool].fail(f"generated Mise receipt is absent: {name}")
            normalized = u.Cli.atomic_write_binary_file_guarded(
                state.value, state.value.content, permission_mode=mode
            )
            if normalized.failure:
                return r[bool].from_failure(normalized)
        return r[bool].ok(True)

    def _stage_project(
        self,
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        newest: tuple[Path, Path, dict[str, str]] | None,
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
        launchers = self._launcher_sources(project, newest)
        if launchers.failure:
            return r[bool].from_failure(launchers)
        for source, (name, mode) in zip(
            launchers.value, files.ARTIFACT_SPECS[:2], strict=True
        ):
            if source.content is None:
                return r[bool].fail(f"Mise launcher source is absent: {name}")
            copied = process.write_new(stage_root / name, source.content, mode)
            if copied.failure:
                return copied
        lock = project.artifacts.lock
        if newest is None:
            # Offline: the published lock is the only authority, copied verbatim.
            if lock.content is None:
                return r[bool].fail(
                    "offline Mise resolution cannot stage an unpublished lock for "
                    f"{project.layout.selector}; network access is required"
                )
            copied_lock = process.write_new(
                stage_root / files.ARTIFACT_SPECS[2][0],
                lock.content,
                files.ARTIFACT_SPECS[2][1],
            )
            if copied_lock.failure:
                return copied_lock
        if newest is not None:
            # Online: the lock is resolved from the declaration, never seeded
            # from the published one. Seeding carries platforms the declaration
            # has since dropped, because `mise lock --bump` re-resolves the
            # entries it finds instead of pruning them to the declared set.
            resolved = self._resolve_lock(project, stage_root=stage_root, newest=newest)
            if resolved.failure:
                return resolved
            # A freshly resolved lock carries resolved versions but not every
            # artifact checksum; the owner downloads the exact resolved assets
            # and fills them, so the published lock is verifiable offline.
            u.Cli.info(
                f"mise-toolchain: hydrating lock checksums for {project.layout.selector}"
            )
            hydrated = self._owner.hydrate_lock_checksums_at(stage_root)
            if hydrated.failure:
                return r[bool].fail(
                    hydrated.error
                    or f"Mise checksum hydration failed for {project.layout.selector}"
                )
        validated = self._owner.validate_artifacts(stage_root)
        if validated.failure:
            return r[bool].from_failure(validated)
        return r[bool].ok(True)

    @staticmethod
    def _launcher_sources(
        project: m.Infra.MiseToolchainProjectState,
        newest: tuple[Path, Path, dict[str, str]] | None,
    ) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
        """Return the launcher pair to stage: newest receipt or committed bytes."""
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        if newest is not None:
            _launcher, receipt, _environment = newest
            states: list[m.Cli.AtomicFileState] = []
            for name, _mode in files.ARTIFACT_SPECS[:2]:
                state = files.read_state(receipt / name, required=True)
                if state.failure:
                    return result_type.from_failure(state)
                states.append(state.value)
            return result_type.ok(tuple(states))
        committed = (
            project.artifacts.unix_launcher,
            project.artifacts.windows_launcher,
        )
        if any(state.content is None for state in committed):
            return result_type.fail(
                "offline Mise resolution cannot stage an unpublished launcher for "
                f"{project.layout.selector}; network access is required"
            )
        return result_type.ok(committed)

    @staticmethod
    def _resolve_lock(
        project: m.Infra.MiseToolchainProjectState,
        *,
        stage_root: Path,
        newest: tuple[Path, Path, dict[str, str]],
    ) -> p.Result[bool]:
        """Re-resolve every moving selector of one staged project online."""
        launcher, _receipt, environment = newest
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
        state = files.read_state(stage_root / files.ARTIFACT_SPECS[2][0], required=True)
        if state.failure:
            return r[bool].from_failure(state)
        if state.value.content is None:
            return r[bool].fail(f"generated Mise lock is absent: {stage_root}")
        return u.Cli.atomic_write_binary_file_guarded(
            state.value, state.value.content, permission_mode=files.ARTIFACT_SPECS[2][1]
        )


__all__: list[str] = ["FlextInfraMiseStaging"]
