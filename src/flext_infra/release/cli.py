"""Centralized CLI registration and handlers for release commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import cli
from flext_core import r

from flext_infra import FlextInfraReleaseOrchestrator, c, m, u

if TYPE_CHECKING:
    import typer


class FlextInfraCliRelease:
    """Release CLI group — composed into the centralized infra CLI."""

    def register_release(self, app: typer.Typer) -> None:
        """Register release commands on the given application."""
        cli.register_result_route(
            app,
            route=m.Cli.ResultCommandRouteModel(
                name="run",
                help_text="Run release orchestration CLI flow",
                model_cls=m.Infra.ReleaseRunInput,
                handler=self._handle_run,
                success_message="Release completed successfully",
                failure_message="Release failed",
            ),
        )

    @staticmethod
    def _resolve_version(
        version_arg: str,
        bump_arg: str,
        interactive: int,
        root_path: Path,
    ) -> r[str]:
        """Resolve the target release version from explicit or derived inputs."""
        if version_arg:
            requested = str(version_arg)
            parse_result = u.Infra.parse_semver(requested)
            if parse_result.is_failure:
                return r[str].fail(parse_result.error or "invalid version")
            return r[str].ok(requested)
        current_result = u.Infra.current_workspace_version(root_path)
        if current_result.is_failure:
            return r[str].fail(current_result.error or "cannot read current version")
        current = str(current_result.value)
        if bump_arg:
            bump_result = u.Infra.bump_version(current, bump_arg)
            if bump_result.is_failure:
                return r[str].fail(bump_result.error or "bump failed")
            return r[str].ok(str(bump_result.value))
        if interactive != 1:
            return r[str].ok(current)
        bump = u.norm_str(input("bump> "), case="lower")
        if bump not in {"major", "minor", "patch"}:
            return r[str].fail("invalid bump type")
        bump_result = u.Infra.bump_version(current, bump)
        if bump_result.is_failure:
            return r[str].fail(bump_result.error or "bump failed")
        return r[str].ok(str(bump_result.value))

    @staticmethod
    def _resolve_tag(tag_arg: str, version: str) -> r[str]:
        """Resolve the git tag that should be created for the release."""
        if tag_arg:
            requested = str(tag_arg)
            if not requested.startswith("v"):
                return r[str].fail("tag must start with v")
            return r[str].ok(requested)
        return r[str].ok(f"v{version}")

    @classmethod
    def _handle_run(cls, params: m.Infra.ReleaseRunInput) -> r[bool]:
        """Execute release orchestration with resolved version and phases."""
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        root_result = u.Infra.workspace_root(resolved_workspace)
        if root_result.is_failure:
            return r[bool].fail(root_result.error or "workspace root not found")
        root = Path(str(root_result.value))
        phases = (
            [
                c.Infra.Verbs.VALIDATE,
                c.Infra.VERSION,
                c.Infra.Directories.BUILD,
                "publish",
            ]
            if params.phase == "all"
            else [part.strip() for part in params.phase.split(",") if part.strip()]
        )
        needs_version = bool(
            {c.Infra.VERSION, c.Infra.Directories.BUILD, "publish"} & set(phases),
        )
        if needs_version:
            version_result = cls._resolve_version(
                params.version,
                params.bump,
                params.interactive,
                root,
            )
            if version_result.is_failure:
                return r[bool].fail(version_result.error or "version resolution failed")
            resolved_version = str(version_result.value)
        else:
            resolved_version = params.version or "0.0.0"
        tag_result = cls._resolve_tag(params.tag, resolved_version)
        if tag_result.is_failure:
            return r[bool].fail(tag_result.error or "tag resolution failed")
        service = FlextInfraReleaseOrchestrator()
        return service.run_release(
            m.Infra.ReleaseOrchestratorConfig(
                workspace_root=root,
                version=resolved_version,
                tag=str(tag_result.value),
                phases=phases,
                project_names=params.projects or None,
                dry_run=not params.apply,
                push=params.push,
                dev_suffix=params.dev_suffix,
                create_branches=params.create_branches == 1,
                next_dev=params.next_dev,
                next_bump=params.next_bump,
            ),
        )
