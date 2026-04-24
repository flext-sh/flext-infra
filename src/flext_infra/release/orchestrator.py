"""Release orchestration service.

Manages the full release lifecycle through composable phases: validate,
version, build, and publish. Each phase returns r for railway-style
error handling. Migrated from scripts/release/run.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Callable,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import Annotated, override

from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    FlextInfraReleaseOrchestratorPhases,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraReleaseOrchestrator(
    FlextInfraReleaseOrchestratorPhases,
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Service for release lifecycle orchestration."""

    version: Annotated[str, m.Field(description="Version string")] = ""
    tag: Annotated[str, m.Field(description="Git tag (e.g. v1.0.0)")] = ""
    push: Annotated[bool, m.Field(description="Push to remote")] = False
    dev_suffix: Annotated[bool, m.Field(description="Add dev suffix")] = False
    phase: Annotated[str, m.Field(description="Release phase")] = "all"
    bump: Annotated[str, m.Field(description="Bump type (major/minor/patch)")] = ""
    interactive: Annotated[
        int, m.Field(description="Interactive mode (1=yes, 0=no)")
    ] = 1
    next_dev: Annotated[bool, m.Field(description="Prepare next dev version")] = False
    next_bump: Annotated[str, m.Field(description="Bump type for next dev version")] = (
        "minor"
    )
    create_branches: Annotated[
        int, m.Field(description="Create release branches (1=yes, 0=no)")
    ] = 1

    @property
    def phase_names(self) -> t.StrSequence:
        """Return the normalized phase sequence for release execution."""
        return u.Infra.resolve_phase_names(self.phase)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the release CLI flow."""
        root = self.root
        phases = self.phase_names
        project_names = self.project_names
        needs_version = bool(
            {
                c.Infra.ReleasePhase.VERSION,
                c.Infra.DIR_BUILD,
                c.Infra.VERB_PUBLISH,
            }
            & set(phases),
        )
        if needs_version:
            version_result = self._resolve_version(
                self.version,
                self.bump,
                self.interactive,
                root,
            )
            if version_result.failure:
                return r[bool].fail(version_result.error or "version resolution failed")
            resolved_version = str(version_result.value)
        else:
            resolved_version = self.version or "0.0.0"
        tag_result = self._resolve_tag(self.tag, resolved_version)
        if tag_result.failure:
            return r[bool].fail(tag_result.error or "tag resolution failed")
        return self.run_release(
            m.Infra.ReleaseOrchestratorConfig(
                workspace_root=root,
                version=resolved_version,
                tag=str(tag_result.value),
                phases=phases,
                project_names=project_names,
                dry_run=self.effective_dry_run,
                push=self.push,
                dev_suffix=self.dev_suffix,
                create_branches=self.create_branches == 1,
                next_dev=self.next_dev,
                next_bump=self.next_bump,
            ),
        )

    def _resolve_version(
        self,
        version_arg: str,
        bump_arg: str,
        interactive: int,
        root_path: Path,
    ) -> p.Result[str]:
        """Resolve the target release version from explicit or derived inputs."""
        if version_arg:
            requested = str(version_arg)
            parse_result = u.Infra.parse_semver(requested)
            if parse_result.failure:
                return r[str].fail(parse_result.error or "invalid version")
            return r[str].ok(requested)
        current_result = u.Infra.current_workspace_version(root_path)
        if current_result.failure:
            return r[str].fail(current_result.error or "cannot read current version")
        current = str(current_result.value)
        if bump_arg:
            bump_result = u.Infra.bump_version(current, bump_arg)
            if bump_result.failure:
                return r[str].fail(bump_result.error or "bump failed")
            return r[str].ok(str(bump_result.value))
        if interactive != 1:
            return r[str].ok(current)
        bump = u.norm_str(input("bump> "), case="lower")
        if bump not in {"major", "minor", "patch"}:
            return r[str].fail("invalid bump type")
        bump_result = u.Infra.bump_version(current, bump)
        if bump_result.failure:
            return r[str].fail(bump_result.error or "bump failed")
        return r[str].ok(str(bump_result.value))

    @staticmethod
    def _resolve_tag(tag_arg: str, version: str) -> p.Result[str]:
        """Resolve the git tag that should be created for the release."""
        if tag_arg:
            requested = str(tag_arg)
            if not requested.startswith("v"):
                return r[str].fail("tag must start with v")
            return r[str].ok(requested)
        return r[str].ok(f"v{version}")

    def run_release(
        self,
        release_config: m.Infra.ReleaseOrchestratorConfig,
    ) -> p.Result[bool]:
        """Run release workflow via DAG pipeline execution."""
        workspace_root = release_config.workspace_root
        version = release_config.version
        tag = release_config.tag
        phases = release_config.phases
        dry_run = release_config.dry_run
        push = release_config.push
        dev_suffix = release_config.dev_suffix
        create_branches = release_config.create_branches
        next_dev = release_config.next_dev
        next_bump = release_config.next_bump
        names = release_config.project_names or []
        spec = m.Infra.ReleaseSpec(
            version=version,
            tag=tag,
            bump_type=next_bump,
        )
        for phase in phases:
            if phase not in c.Infra.VALID_PHASES:
                return r[bool].fail(f"invalid phase: {phase}")
        self.logger.info(
            "release_run_started",
            release_version=spec.version,
            release_tag=spec.tag,
            phases=str(phases),
            projects=str(names),
        )
        if create_branches and (not dry_run):
            branch_result = self._create_branches(workspace_root, version, names)
            if branch_result.failure:
                return branch_result

        dispatch_cfg = m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_VALIDATE,  # placeholder — overridden per stage
            workspace_root=workspace_root,
            version=spec.version,
            tag=spec.tag,
            project_names=names,
            dry_run=dry_run,
            push=push,
            dev_suffix=dev_suffix,
        )

        pipeline_ctx = m.Cli.PipelineStageContext(
            workspace_root=workspace_root,
            shared={},
            settings={
                "dry_run": dry_run,
                "push": push,
                "dev_suffix": dev_suffix,
            },
        )

        active_stages = self._build_release_stages(phases, dispatch_cfg)

        pipeline_result = u.Cli.execute_pipeline(
            active_stages,
            pipeline_ctx,
            fail_fast=True,
        )
        if pipeline_result.failure:
            return r[bool].fail(pipeline_result.error or "pipeline execution failed")

        result = pipeline_result.value
        if not result.success:
            failed = result.failed_stages
            error_msg = failed[0].error if failed else "pipeline failed"
            return r[bool].fail(error_msg or "pipeline failed")

        if next_dev and (not dry_run):
            return self._bump_next_dev(workspace_root, version, names, next_bump)
        self.logger.info("release_run_completed", status=c.Infra.RK_OK)
        return r[bool].ok(True)

    def _build_release_stages(
        self,
        phases: t.StrSequence,
        dispatch_cfg: m.Infra.ReleasePhaseDispatchConfig,
    ) -> Sequence[m.Cli.PipelineStageSpec]:
        """Build DAG stage specs from the requested release phases.

        Dependencies chain only between active phases, preserving their
        canonical order: validate → version → build → publish.
        """
        active: set[str] = set(phases)
        phase_order: t.StrSequence = [
            c.Infra.VERB_VALIDATE,
            c.Infra.ReleasePhase.VERSION,
            c.Infra.DIR_BUILD,
            c.Infra.VERB_PUBLISH,
        ]
        stage_list: MutableSequence[m.Cli.PipelineStageSpec] = []
        prev: str | None = None
        for phase_name in phase_order:
            if phase_name not in active:
                continue
            deps: frozenset[str] = (
                frozenset((prev,)) if prev is not None else frozenset()
            )
            stage_list.append(
                m.Cli.PipelineStageSpec(
                    stage_id=phase_name,
                    depends_on=deps,
                    handler=self._make_phase_handler(phase_name, dispatch_cfg),
                ),
            )
            prev = phase_name
        return stage_list

    def _make_phase_handler(
        self,
        phase_name: str,
        dispatch_cfg: m.Infra.ReleasePhaseDispatchConfig,
    ) -> Callable[[m.Cli.PipelineStageContext], p.Result[m.Cli.PipelineStageResult]]:
        """Create a handler closure that adapts r[bool] to r[PipelineStageResult]."""

        def handler(
            _ctx: m.Cli.PipelineStageContext,
        ) -> p.Result[m.Cli.PipelineStageResult]:
            phase_cfg = dispatch_cfg.model_copy(update={"phase": phase_name})
            phase_result = self._dispatch_phase(phase_cfg)
            if phase_result.failure:
                return r[m.Cli.PipelineStageResult].fail(
                    phase_result.error or f"{phase_name} failed",
                )
            return r[m.Cli.PipelineStageResult].ok(
                m.Cli.PipelineStageResult(
                    stage_id=phase_name,
                    status=c.Cli.PipelineStageStatus.OK,
                ),
            )

        return handler

    def phase_validate(
        self, workspace_root: Path, *, dry_run: bool = False
    ) -> p.Result[bool]:
        """Execute validation phase via the workspace make validation target."""
        if dry_run:
            self.logger.info(
                "release_phase_validate",
                action="dry-run",
                status=c.Cli.PipelineStageStatus.OK,
            )
            return r[bool].ok(True)
        return u.Cli.run_checked(
            [c.Infra.MAKE, "val", "VALIDATE_SCOPE=workspace"], cwd=workspace_root
        )

    @override
    def _build_targets(
        self,
        workspace_root: Path,
        project_names: t.StrSequence,
    ) -> Sequence[t.Pair[str, Path]]:
        """Resolve unique build targets from project names."""
        targets: MutableSequence[t.Pair[str, Path]] = [
            (c.Infra.RK_ROOT, workspace_root),
        ]
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.success:
            targets.extend((p.name, p.path) for p in projects_result.value)
        seen: t.Infra.StrSet = set()
        seen_paths: set[Path] = set()
        unique: MutableSequence[t.Pair[str, Path]] = []
        for name, path in targets:
            resolved_path = path.resolve()
            if name in seen or resolved_path in seen_paths or not path.exists():
                continue
            seen.add(name)
            seen_paths.add(resolved_path)
            unique.append((name, path))
        return unique

    def _bump_next_dev(
        self,
        workspace_root: Path,
        version: str,
        project_names: t.StrSequence,
        bump: str,
    ) -> p.Result[bool]:
        """Bump to the next development version."""
        bump_result = u.Infra.bump_version(version, bump)
        if bump_result.failure:
            return r[bool].fail(bump_result.error or "bump failed")
        next_version = bump_result.value
        ctx = m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.ReleasePhase.VERSION,
            workspace_root=workspace_root,
            version=next_version,
            tag=f"v{next_version}",
            project_names=project_names,
            dev_suffix=True,
        )
        result = self.phase_version(ctx)
        if result.success:
            self.logger.info("release_next_dev_version", version=f"{next_version}-dev")
        return result

    def _collect_changes(
        self, workspace_root: Path, previous: str, tag: str
    ) -> p.Result[str]:
        """Collect Git commit messages between two tags."""
        rev = f"{previous}..{tag}" if previous else tag
        return u.Cli.capture([c.Infra.GIT, "log", "--oneline", rev], cwd=workspace_root)

    def _create_branches(
        self,
        workspace_root: Path,
        version: str,
        project_names: t.StrSequence,
    ) -> p.Result[bool]:
        """Create local release branches for workspace and projects."""
        branch = f"release/{version}"
        result = u.Cli.run_checked(
            [c.Infra.GIT, "checkout", "-B", branch],
            cwd=workspace_root,
        )
        if result.failure:
            return result
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.success:
            for project in projects_result.value:
                proj_result = u.Cli.run_checked(
                    [c.Infra.GIT, "checkout", "-B", branch],
                    cwd=project.path,
                )
                if proj_result.failure:
                    return proj_result
        return r[bool].ok(True)

    @override
    def _create_tag(self, workspace_root: Path, tag: str) -> p.Result[bool]:
        """Create an annotated Git tag if it does not already exist."""
        exists_capture = u.Cli.capture(
            [c.Infra.GIT, "tag", "-l", tag],
            cwd=workspace_root,
        )
        if exists_capture.failure:
            return r[bool].fail(exists_capture.error or "tag check failed")
        if exists_capture.unwrap().strip() == tag:
            return r[bool].ok(True)
        return u.Cli.run_checked(
            [c.Infra.GIT, "tag", "-a", tag, "-m", f"release: {tag}"],
            cwd=workspace_root,
        )

    def _dispatch_phase(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
    ) -> p.Result[bool]:
        """Route to the correct phase method."""
        phase = ctx.phase
        if phase == c.Infra.VERB_VALIDATE:
            return self.phase_validate(ctx.workspace_root, dry_run=ctx.dry_run)
        if phase == c.Infra.ReleasePhase.VERSION:
            return self.phase_version(ctx)
        if phase == c.Infra.DIR_BUILD:
            return self.phase_build(ctx)
        if phase == c.Infra.VERB_PUBLISH:
            return self.phase_publish(ctx)
        return r[bool].fail(f"unknown phase: {phase}")

    @override
    def _generate_notes(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        output_path: Path,
    ) -> p.Result[bool]:
        """Generate release notes from Git history."""
        workspace_root = ctx.workspace_root
        tag = ctx.tag
        previous_result = self._previous_tag(workspace_root, tag)
        previous: str = str(previous_result.value) if previous_result.success else ""
        changes_result = self._collect_changes(workspace_root, previous, tag)
        changes: str = str(changes_result.value) if changes_result.success else ""
        projects_result = u.Infra.resolve_projects(workspace_root, ctx.project_names)
        project_list: Sequence[m.Infra.ProjectInfo] = (
            projects_result.unwrap() if projects_result.success else []
        )
        return u.Infra.generate_notes(
            ctx.version,
            tag,
            project_list,
            changes,
            output_path,
        )

    def _previous_tag(self, workspace_root: Path, tag: str) -> p.Result[str]:
        """Find the tag immediately preceding the given tag."""
        return u.Cli.capture(
            [c.Infra.GIT, "describe", "--tags", "--abbrev=0", f"{tag}^"],
            cwd=workspace_root,
        )

    @override
    def _push_release(self, workspace_root: Path, tag: str) -> p.Result[bool]:
        """Push branch and tag to remote origin."""
        return u.Cli.run_checked(
            [c.Infra.GIT, "push", c.Infra.GIT_ORIGIN, c.Infra.GIT_HEAD, tag],
            cwd=workspace_root,
        )

    @override
    def _version_files(
        self,
        workspace_root: Path,
        project_names: t.StrSequence,
    ) -> Sequence[Path]:
        """Discover pyproject.toml files that need version updates."""
        files: MutableSequence[Path] = [
            workspace_root / c.Infra.PYPROJECT_FILENAME,
        ]
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.success:
            projects: Sequence[m.Infra.ProjectInfo] = projects_result.value
            for project in projects:
                pyproject = project.path / c.Infra.PYPROJECT_FILENAME
                if pyproject.exists():
                    files.append(pyproject)
        return sorted({path.resolve() for path in files if path.exists()})


__all__: list[str] = ["FlextInfraReleaseOrchestrator"]
