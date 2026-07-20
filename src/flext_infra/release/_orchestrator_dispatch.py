"""Release orchestration lifecycle dispatch and execution helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r
from flext_infra import c, m, p, t, u

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraReleaseOrchestratorDispatchMixin:
    """Core release orchestrator flow and phase dispatch."""

    if TYPE_CHECKING:
        phase: str
        tag: str
        version: str
        bump: str
        interactive: int
        push: bool
        dev_suffix: bool
        create_branches: int
        next_dev: bool
        next_bump: str

        @property
        def root(self) -> Path: ...

        @property
        def logger(self) -> p.Logger: ...

        @property
        def project_names(self) -> t.StrSequence | None: ...

        @property
        def effective_dry_run(self) -> bool: ...

        def phase_version(
            self, ctx: p.Infra.ReleasePhaseDispatchConfig
        ) -> p.Result[bool]: ...

        def phase_build(
            self, ctx: p.Infra.ReleasePhaseDispatchConfig
        ) -> p.Result[bool]: ...

        def phase_publish(
            self, ctx: p.Infra.ReleasePhaseDispatchConfig
        ) -> p.Result[bool]: ...

        def _build_targets(
            self, workspace_root: Path, project_names: t.StrSequence
        ) -> p.Result[t.SequenceOf[t.Pair[str, Path]]]: ...

        def _version_files(
            self, workspace_root: Path, project_names: t.StrSequence
        ) -> p.Result[t.SequenceOf[Path]]: ...

        def _version_update_files(
            self, files: t.SequenceOf[Path], target: str, *, dry_run: bool
        ) -> p.Result[int]: ...

    @property
    def phase_names(self) -> t.StrSequence:
        """Normalized phase sequence for release execution."""
        return u.Infra.resolve_phase_names(self.phase)

    def _resolve_version(
        self, version_arg: str, bump_arg: str, interactive: int, root_path: Path
    ) -> p.Result[str]:
        """Resolve release version from explicit or interactive inputs."""
        if version_arg:
            requested = version_arg
            parse_result = u.Infra.parse_semver(requested)
            return (
                r[str].ok(requested)
                if parse_result.success
                else r[str].fail(parse_result.error or "invalid version")
            )
        current_result = u.Infra.current_workspace_version(root_path)
        if current_result.failure:
            return r[str].fail(current_result.error or "cannot read current version")
        current = current_result.value

        requested_bump = bump_arg
        if (not requested_bump) and interactive == 1:
            requested_bump = u.norm_str(input("bump> "), case="lower")
        if not requested_bump:
            return r[str].ok(current)
        return u.Infra.bump_version(current, requested_bump)

    @staticmethod
    def _resolve_tag(tag_arg: str, version: str) -> p.Result[str]:
        """Resolve tag string from explicit argument or semantic version."""
        if tag_arg:
            if not tag_arg.startswith("v"):
                return r[str].fail("tag must start with v")
            return r[str].ok(tag_arg)
        return r[str].ok(f"v{version}")

    def run_release(
        self, release_config: p.Infra.ReleaseOrchestratorConfig
    ) -> p.Result[bool]:
        """Run release workflow via the configured pipeline."""
        try:
            spec = m.Infra.ReleaseSpec(
                version=release_config.version,
                tag=release_config.tag,
                bump_type=release_config.next_bump,
            )
        except c.ValidationError as exc:
            return r[bool].fail_op("validate release identity", exc)
        invalid_phase = next(
            (
                phase
                for phase in release_config.phases
                if phase not in c.Infra.VALID_PHASES
            ),
            None,
        )
        if invalid_phase is not None:
            return r[bool].fail(f"invalid phase: {invalid_phase}")
        names = release_config.project_names or ()
        self.logger.info(
            "release_run_started",
            release_version=spec.version,
            release_tag=spec.tag,
            phases=str(release_config.phases),
            projects=str(names),
        )
        if release_config.create_branches and not release_config.dry_run:
            branch_result = self._create_branches(
                release_config.workspace_root, spec.version, names
            )
            if branch_result.failure:
                return branch_result
        return self._run_release_pipeline(release_config, spec, names)

    def _run_release_pipeline(
        self,
        release_config: p.Infra.ReleaseOrchestratorConfig,
        spec: p.Infra.ReleaseSpec,
        names: t.StrSequence,
    ) -> p.Result[bool]:
        """Execute configured release stages and the optional next-dev bump."""
        dispatch_cfg = m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_VALIDATE,
            workspace_root=release_config.workspace_root,
            version=spec.version,
            tag=spec.tag,
            project_names=names,
            dry_run=release_config.dry_run,
            push=release_config.push,
            dev_suffix=release_config.dev_suffix,
        )
        pipeline_result = cli.pipeline(
            self._build_release_stages(release_config.phases, dispatch_cfg),
            context=cli.stage_context(
                release_config.workspace_root,
                settings={
                    "dry_run": release_config.dry_run,
                    "push": release_config.push,
                    "dev_suffix": release_config.dev_suffix,
                },
            ),
            fail_fast=True,
            logger=self.logger,
        )
        if pipeline_result.failure:
            return r[bool].fail(pipeline_result.error or "pipeline execution failed")
        failed = next(
            (stage for stage in pipeline_result.value.failed_stages if stage.error),
            None,
        )
        if failed is not None:
            return r[bool].fail(failed.error)
        if release_config.next_dev and not release_config.dry_run:
            return self._bump_next_dev(
                release_config.workspace_root,
                spec.version,
                names,
                release_config.next_bump,
            )
        self.logger.info("release_run_completed", status=c.Infra.RK_OK)
        return r[bool].ok(True)

    def execute(self) -> p.Result[bool]:
        """Execute release with resolved configuration."""
        root = self.root
        phases = self.phase_names
        project_names = self.project_names
        needs_version = bool(
            {c.Infra.ReleasePhase.VERSION, c.Infra.DIR_BUILD, c.Infra.VERB_PUBLISH}
            & set(phases)
        )
        if needs_version:
            version_result = self._resolve_version(
                self.version, self.bump, self.interactive, root
            )
            if version_result.failure:
                return r[bool].fail(version_result.error or "version resolution failed")
            resolved_version = version_result.value
        else:
            resolved_version = self.version or "0.0.0"

        tag_result = self._resolve_tag(self.tag, resolved_version)
        if tag_result.failure:
            return r[bool].fail(tag_result.error or "tag resolution failed")
        return self.run_release(
            m.Infra.ReleaseOrchestratorConfig(
                workspace_root=root,
                version=resolved_version,
                tag=tag_result.value,
                phases=phases,
                project_names=project_names,
                dry_run=self.effective_dry_run,
                push=self.push,
                dev_suffix=self.dev_suffix,
                create_branches=self.create_branches == 1,
                next_dev=self.next_dev,
                next_bump=self.next_bump,
            )
        )

    def _build_release_stages(
        self, phases: t.StrSequence, dispatch_cfg: p.Infra.ReleasePhaseDispatchConfig
    ) -> t.SequenceOf[p.Cli.PipelineStageSpec]:
        """Build release stage specs preserving declared order."""
        active: set[str] = set(phases)
        phase_order: t.StrSequence = [
            c.Infra.VERB_VALIDATE,
            c.Infra.ReleasePhase.VERSION,
            c.Infra.DIR_BUILD,
            c.Infra.VERB_PUBLISH,
        ]
        active_stage_order: t.MutableSequenceOf[str] = []
        handlers: dict[str, t.Cli.PipelineHandler] = {}
        for phase_name in phase_order:
            if phase_name not in active:
                continue
            active_stage_order.append(phase_name)
            handlers[phase_name] = self._make_phase_handler(phase_name, dispatch_cfg)
        return cli.linear_pipeline(active_stage_order, handlers)

    def phase_validate(
        self, workspace_root: Path, *, dry_run: bool = False
    ) -> p.Result[bool]:
        """Execute validation phase via workspace val command."""
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

    def _make_phase_handler(
        self, phase_name: str, dispatch_cfg: p.Infra.ReleasePhaseDispatchConfig
    ) -> t.Cli.PipelineHandler:
        """Adapt a phase handler to pipeline stage result contract."""

        def handler(
            _ctx: p.Cli.PipelineStageContext,
        ) -> p.Result[p.Cli.PipelineStageResult]:
            phase_cfg = m.Infra.ReleasePhaseDispatchConfig(
                workspace_root=dispatch_cfg.workspace_root,
                project_names=dispatch_cfg.project_names,
                version=dispatch_cfg.version,
                tag=dispatch_cfg.tag,
                push=dispatch_cfg.push,
                dev_suffix=dispatch_cfg.dev_suffix,
                dry_run=dispatch_cfg.dry_run,
                phase=phase_name,
            )
            phase_result = self._dispatch_phase(phase_cfg)
            if phase_result.failure:
                return r[p.Cli.PipelineStageResult].fail(
                    phase_result.error or f"{phase_name} failed"
                )
            return cli.ok_stage(phase_name)

        return handler

    def _dispatch_phase(
        self, ctx: p.Infra.ReleasePhaseDispatchConfig
    ) -> p.Result[bool]:
        """Route to the configured release phase implementation."""
        match ctx.phase:
            case c.Infra.VERB_VALIDATE:
                return self.phase_validate(ctx.workspace_root, dry_run=ctx.dry_run)
            case c.Infra.ReleasePhase.VERSION:
                return self.phase_version(ctx)
            case c.Infra.DIR_BUILD:
                return self.phase_build(ctx)
            case c.Infra.VERB_PUBLISH:
                return self.phase_publish(ctx)
            case phase:
                return r[bool].fail(f"unknown phase: {phase}")

    def _collect_changes(self, workspace_root: Path, previous: str) -> p.Result[str]:
        """Collect commit messages in release tag range."""
        rev = f"{previous}..{c.Infra.GIT_HEAD}" if previous else c.Infra.GIT_HEAD
        return u.Cli.capture([c.Infra.GIT, "log", "--oneline", rev], cwd=workspace_root)

    def _previous_tag(self, workspace_root: Path, tag: str) -> p.Result[str]:
        """Find previous release tag for changelog generation."""
        tags_result = u.Cli.capture(
            [c.Infra.GIT, "tag", "--list", "--sort=-version:refname"],
            cwd=workspace_root,
        )
        if tags_result.failure:
            return r[str].fail(tags_result.error or "release tag listing failed")
        previous = next(
            (
                candidate
                for candidate in tags_result.value.splitlines()
                if candidate and candidate != tag
            ),
            "",
        )
        return r[str].ok(previous)

    @staticmethod
    def _preflight_release_branch(repository: Path, branch: str) -> p.Result[bool]:
        """Require a clean repository and a non-conflicting release branch."""
        status_result = u.Cli.capture(
            [c.Infra.GIT, "status", "--porcelain"], cwd=repository
        )
        if status_result.failure:
            return r[bool].fail(status_result.error or "branch status check failed")
        if status_result.value.strip():
            return r[bool].fail(f"release branch repository is dirty: {repository}")
        current_result = u.Cli.capture(
            [c.Infra.GIT, "branch", "--show-current"], cwd=repository
        )
        if current_result.failure:
            return r[bool].fail(current_result.error or "current branch check failed")
        if current_result.value.strip() == branch:
            return r[bool].ok(False)
        exists_result = u.Cli.capture(
            [c.Infra.GIT, "branch", "--list", branch], cwd=repository
        )
        if exists_result.failure:
            return r[bool].fail(exists_result.error or "release branch check failed")
        if exists_result.value.strip():
            return r[bool].fail(
                f"release branch already exists without being active: {repository}"
            )
        return r[bool].ok(True)

    def _create_branches(
        self, workspace_root: Path, version: str, project_names: t.StrSequence
    ) -> p.Result[bool]:
        """Create release branches for workspace and selected projects."""
        branch = f"release/{version}"
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.failure:
            return r[bool].fail(
                projects_result.error or "release project resolution failed"
            )
        repositories = (
            workspace_root,
            *(project.path for project in projects_result.value),
        )
        pending: t.MutableSequenceOf[Path] = []
        for repository in repositories:
            preflight_result = self._preflight_release_branch(repository, branch)
            if preflight_result.failure:
                return r[bool].fail(
                    preflight_result.error
                    or f"release branch preflight failed: {repository}"
                )
            if preflight_result.value:
                pending.append(repository)
        for repository in pending:
            switch_result = u.Cli.run_checked(
                [c.Infra.GIT, "switch", "--create", branch], cwd=repository
            )
            if switch_result.failure:
                return r[bool].fail(
                    switch_result.error
                    or f"release branch creation failed: {repository}"
                )
        return r[bool].ok(True)

    def _create_tag(self, workspace_root: Path, tag: str) -> p.Result[bool]:
        """Create annotated Git tag if needed."""
        exists_capture = u.Cli.capture(
            [c.Infra.GIT, "tag", "-l", tag], cwd=workspace_root
        )
        if exists_capture.failure:
            return r[bool].fail(exists_capture.error or "tag check failed")
        if exists_capture.value.strip() == tag:
            return r[bool].ok(True)
        return u.Cli.run_checked(
            [c.Infra.GIT, "tag", "-a", tag, "-m", f"release: {tag}"], cwd=workspace_root
        )

    def _push_release(self, workspace_root: Path, tag: str) -> p.Result[bool]:
        """Push branch and tag to origin."""
        return u.Cli.run_checked(
            [c.Infra.GIT, "push", c.Infra.GIT_ORIGIN, c.Infra.GIT_HEAD, tag],
            cwd=workspace_root,
        )

    def _bump_next_dev(
        self,
        workspace_root: Path,
        version: str,
        project_names: t.StrSequence,
        bump: str,
    ) -> p.Result[bool]:
        """Bump workspace to next development version."""
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
            self.logger.info("release_next_dev_version", version=f"{next_version}.dev0")
        return result

    def _generate_notes(
        self, ctx: p.Infra.ReleasePhaseDispatchConfig, output_path: Path
    ) -> p.Result[bool]:
        """Generate release notes with project diff context."""
        workspace_root = ctx.workspace_root
        tag = ctx.tag
        previous_result = self._previous_tag(workspace_root, tag)
        if previous_result.failure:
            return r[bool].fail(
                previous_result.error or "previous release tag resolution failed"
            )
        changes_result = self._collect_changes(workspace_root, previous_result.value)
        if changes_result.failure:
            return r[bool].fail(
                changes_result.error or "release change collection failed"
            )
        projects_result = u.Infra.resolve_projects(workspace_root, ctx.project_names)
        if projects_result.failure:
            return r[bool].fail(
                projects_result.error or "release project resolution failed"
            )
        return u.Infra.generate_notes(
            ctx.version, tag, projects_result.value, changes_result.value, output_path
        )


__all__: list[str] = ["FlextInfraReleaseOrchestratorDispatchMixin"]
