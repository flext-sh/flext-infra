"""Release orchestration lifecycle dispatch and execution helpers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, override

from flext_cli import cli
from flext_infra import c, m, p, r, t, u

if TYPE_CHECKING:
    class _ReleaseOrchestratorContract(Protocol):
        phase: str
        tag: str

        @property
        def root(self) -> Path:
            ...

        @property
        def logger(self) -> p.Logger:
            ...

        @property
        def project_names(self) -> t.StrSequence | None:
            ...

        version: str
        bump: str
        interactive: int

        @property
        def effective_dry_run(self) -> bool:
            ...
        push: bool
        dev_suffix: bool
        create_branches: int
        next_dev: bool
        next_bump: str

        def phase_validate(
            self,
            workspace_root: Path,
            *,
            dry_run: bool = False,
        ) -> p.Result[bool]:
            ...

        def phase_version(
            self,
            ctx: m.Infra.ReleasePhaseDispatchConfig,
        ) -> p.Result[bool]:
            ...

        def phase_build(
            self,
            ctx: m.Infra.ReleasePhaseDispatchConfig,
        ) -> p.Result[bool]:
            ...

        def phase_publish(
            self,
            ctx: m.Infra.ReleasePhaseDispatchConfig,
        ) -> p.Result[bool]:
            ...

        def _resolve_tag(
            self,
            tag_arg: str,
            version: str,
        ) -> p.Result[str]:
            ...

        def _build_release_stages(
            self,
            phases: t.StrSequence,
            dispatch_cfg: m.Infra.ReleasePhaseDispatchConfig,
        ) -> t.SequenceOf[m.Cli.PipelineStageSpec]:
            ...

        def _make_phase_handler(
            self,
            phase_name: str,
            dispatch_cfg: m.Infra.ReleasePhaseDispatchConfig,
        ) -> t.Cli.PipelineHandler:
            ...

        def _dispatch_phase(
            self,
            ctx: m.Infra.ReleasePhaseDispatchConfig,
        ) -> p.Result[bool]:
            ...

        def _create_tag(self, workspace_root: Path, tag: str) -> p.Result[bool]:
            ...

        def _push_release(self, workspace_root: Path, tag: str) -> p.Result[bool]:
            ...

        def _collect_changes(
            self,
            workspace_root: Path,
            previous: str,
            tag: str,
        ) -> p.Result[str]:
            ...

        def _previous_tag(self, workspace_root: Path, tag: str) -> p.Result[str]:
            ...

        def _generate_notes(
            self,
            ctx: m.Infra.ReleasePhaseDispatchConfig,
            output_path: Path,
        ) -> p.Result[bool]:
            ...

        def _create_branches(
            self,
            workspace_root: Path,
            version: str,
            project_names: t.StrSequence,
        ) -> p.Result[bool]:
            ...

        def _bump_next_dev(
            self,
            workspace_root: Path,
            version: str,
            project_names: t.StrSequence,
            bump: str,
        ) -> p.Result[bool]:
            ...

        def _version_update_files(
            self,
            files: t.SequenceOf[Path],
            target: str,
            *,
            dry_run: bool,
        ) -> int:
            ...

        def _build_targets(
            self,
            workspace_root: Path,
            project_names: t.StrSequence,
        ) -> t.SequenceOf[t.Pair[str, Path]]:
            ...

        def _version_files(
            self,
            workspace_root: Path,
            project_names: t.StrSequence,
        ) -> t.SequenceOf[Path]:
            ...

        @property
        def phase_names(self) -> t.StrSequence:
            ...

        def _resolve_version(
            self,
            version_arg: str,
            bump_arg: str,
            interactive: int,
            root_path: Path,
        ) -> p.Result[str]:
            ...

        def run_release(
            self,
            release_config: m.Infra.ReleaseOrchestratorConfig,
        ) -> p.Result[bool]:
            ...


class FlextInfraReleaseOrchestratorDispatchMixin:
    """Core release orchestrator flow and phase dispatch."""

    @property
    def phase_names(self: _ReleaseOrchestratorContract) -> t.StrSequence:
        """Return normalized phase sequence for release execution."""
        return u.Infra.resolve_phase_names(self.phase)

    def _resolve_version(
        self: _ReleaseOrchestratorContract,
        version_arg: str,
        bump_arg: str,
        interactive: int,
        root_path: Path,
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
        self: _ReleaseOrchestratorContract,
        release_config: m.Infra.ReleaseOrchestratorConfig,
    ) -> p.Result[bool]:
        """Run release workflow via the configured pipeline."""
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
        final_result: p.Result[bool] = r[bool].ok(True)
        invalid_phase = next(
            (phase for phase in phases if phase not in c.Infra.VALID_PHASES),
            None,
        )
        if invalid_phase is not None:
            final_result = r[bool].fail(f"invalid phase: {invalid_phase}")

        if final_result.success:
            self.logger.info(
                "release_run_started",
                release_version=spec.version,
                release_tag=spec.tag,
                phases=str(phases),
                projects=str(names),
            )
            if create_branches and not dry_run:
                final_result = self._create_branches(workspace_root, version, names)

        if final_result.success:
            dispatch_cfg = m.Infra.ReleasePhaseDispatchConfig(
                phase=c.Infra.VERB_VALIDATE,
                workspace_root=workspace_root,
                version=spec.version,
                tag=spec.tag,
                project_names=names,
                dry_run=dry_run,
                push=push,
                dev_suffix=dev_suffix,
            )
            active_stages = self._build_release_stages(phases, dispatch_cfg)
            pipeline_result = cli.pipeline(
                active_stages,
                workspace_root=workspace_root,
                settings={
                    "dry_run": dry_run,
                    "push": push,
                    "dev_suffix": dev_suffix,
                },
                fail_fast=True,
                logger=self.logger,
            )
            if pipeline_result.failure:
                final_result = r[bool].fail(
                    pipeline_result.error or "pipeline execution failed"
                )
            elif failed := next(
                (s for s in pipeline_result.value.failed_stages if s.error),
                None,
            ):
                final_result = r[bool].fail(failed.error)
            elif next_dev and not dry_run:
                final_result = self._bump_next_dev(
                    workspace_root,
                    version,
                    names,
                    next_bump,
                )
            else:
                self.logger.info("release_run_completed", status=c.Infra.RK_OK)
                final_result = r[bool].ok(True)
        return final_result

    @override
    def execute(self: _ReleaseOrchestratorContract) -> p.Result[bool]:
        """Execute release with resolved configuration."""
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
            ),
        )

    def _build_release_stages(
        self: _ReleaseOrchestratorContract,
        phases: t.StrSequence,
        dispatch_cfg: m.Infra.ReleasePhaseDispatchConfig,
    ) -> t.SequenceOf[m.Cli.PipelineStageSpec]:
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
        self: _ReleaseOrchestratorContract,
        workspace_root: Path,
        *,
        dry_run: bool = False,
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
        self: _ReleaseOrchestratorContract,
        phase_name: str,
        dispatch_cfg: m.Infra.ReleasePhaseDispatchConfig,
    ) -> t.Cli.PipelineHandler:
        """Adapt a phase handler to pipeline stage result contract."""

        def handler(
            _ctx: m.Cli.PipelineStageContext,
        ) -> p.Result[m.Cli.PipelineStageResult]:
            phase_cfg = dispatch_cfg.model_copy(update={"phase": phase_name})
            phase_result = self._dispatch_phase(phase_cfg)
            if phase_result.failure:
                return r[m.Cli.PipelineStageResult].fail(
                    phase_result.error or f"{phase_name} failed",
                )
            return cli.ok_stage(phase_name)

        return handler

    def _dispatch_phase(
        self: _ReleaseOrchestratorContract,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
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

    def _collect_changes(
        self: _ReleaseOrchestratorContract,
        workspace_root: Path,
        previous: str,
        tag: str,
    ) -> p.Result[str]:
        """Collect commit messages in release tag range."""
        rev = f"{previous}..{tag}" if previous else tag
        return u.Cli.capture([c.Infra.GIT, "log", "--oneline", rev], cwd=workspace_root)

    def _previous_tag(self, workspace_root: Path, tag: str) -> p.Result[str]:
        """Find previous release tag for changelog generation."""
        return u.Cli.capture(
            [c.Infra.GIT, "describe", "--tags", "--abbrev=0", f"{tag}^"],
            cwd=workspace_root,
        )

    def _create_branches(
        self: _ReleaseOrchestratorContract,
        workspace_root: Path,
        version: str,
        project_names: t.StrSequence,
    ) -> p.Result[bool]:
        """Create release branches for workspace and selected projects."""
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
                project_result = u.Cli.run_checked(
                    [c.Infra.GIT, "checkout", "-B", branch],
                    cwd=project.path,
                )
                if project_result.failure:
                    return project_result
        return r[bool].ok(True)

    @override
    def _create_tag(self: _ReleaseOrchestratorContract, workspace_root: Path, tag: str) -> p.Result[bool]:
        """Create annotated Git tag if needed."""
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

    @override
    def _push_release(self: _ReleaseOrchestratorContract, workspace_root: Path, tag: str) -> p.Result[bool]:
        """Push branch and tag to origin."""
        return u.Cli.run_checked(
            [c.Infra.GIT, "push", c.Infra.GIT_ORIGIN, c.Infra.GIT_HEAD, tag],
            cwd=workspace_root,
        )

    def _bump_next_dev(
        self: _ReleaseOrchestratorContract,
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
            self.logger.info("release_next_dev_version", version=f"{next_version}-dev")
        return result

    def _generate_notes(
        self: _ReleaseOrchestratorContract,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        output_path: Path,
    ) -> p.Result[bool]:
        """Generate release notes with project diff context."""
        workspace_root = ctx.workspace_root
        tag = ctx.tag
        previous_result = self._previous_tag(workspace_root, tag)
        previous: str = previous_result.value if previous_result.success else ""
        changes_result = self._collect_changes(workspace_root, previous, tag)
        changes: str = changes_result.value if changes_result.success else ""
        projects_result = u.Infra.resolve_projects(workspace_root, ctx.project_names)
        project_list: t.SequenceOf[m.Infra.ProjectInfo] = (
            projects_result.unwrap() if projects_result.success else []
        )
        return u.Infra.generate_notes(
            ctx.version,
            tag,
            project_list,
            changes,
            output_path,
        )


__all__: list[str] = ["FlextInfraReleaseOrchestratorDispatchMixin"]
