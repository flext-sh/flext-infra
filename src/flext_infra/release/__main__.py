"""CLI entry point for release orchestration.

Usage:
    python -m flext_infra release --phase validate --apply --workspace .
    python -m flext_infra release --phase version --version 1.0.0 --workspace .
    python -m flext_infra release --phase all --version 1.0.0 --workspace .

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from flext_cli import cli
from flext_core import FlextRuntime, r
from pydantic import BaseModel, Field

from flext_infra import FlextInfraReleaseOrchestrator, c, m, t, u

# ── Input Model ──────────────────────────────────────────────


class ReleaseInput(BaseModel):
    """CLI input for release orchestration — fields become CLI options."""

    workspace: Annotated[
        str | None, Field(default=None, description="Workspace root directory")
    ]
    apply: Annotated[bool, Field(default=False, description="Apply changes")]
    phase: Annotated[str, Field(default="all", description="Release phase")]
    version: Annotated[str, Field(default="", description="Version string")]
    tag: Annotated[str, Field(default="", description="Git tag (e.g. v1.0.0)")]
    bump: Annotated[str, Field(default="", description="Bump type (major/minor/patch)")]
    interactive: Annotated[
        int, Field(default=1, description="Interactive mode (1=yes, 0=no)")
    ]
    push: Annotated[bool, Field(default=False, description="Push to remote")]
    dev_suffix: Annotated[bool, Field(default=False, description="Add dev suffix")]
    next_dev: Annotated[
        bool, Field(default=False, description="Prepare next dev version")
    ]
    next_bump: Annotated[
        str, Field(default="minor", description="Bump type for next dev version")
    ]
    create_branches: Annotated[
        int, Field(default=1, description="Create release branches (1=yes, 0=no)")
    ]
    projects: Annotated[
        list[str] | None,
        Field(default=None, description="Project names to release"),
    ]


# ── Helpers ──────────────────────────────────────────────────


def _resolve_version(
    version_arg: str,
    bump_arg: str,
    interactive: int,
    root_path: Path,
) -> r[str]:
    if version_arg:
        requested = str(version_arg)
        parse_result = u.Infra.parse_semver(requested)
        if parse_result.is_failure:
            return r[str].fail(parse_result.error or "invalid version")
        return r[str].ok(requested)
    current_result = u.Infra.current_workspace_version(root_path)
    if current_result.is_failure:
        return r[str].fail(current_result.error or "cannot read current version")
    current: str = str(current_result.value)
    if bump_arg:
        bump_result = u.Infra.bump_version(current, bump_arg)
        if bump_result.is_failure:
            return r[str].fail(bump_result.error or "bump failed")
        return r[str].ok(str(bump_result.value))
    if interactive != 1:
        return r[str].ok(current)
    bump = typer.prompt("Bump type", type=str).strip().lower()
    if bump not in {"major", "minor", "patch"}:
        return r[str].fail("invalid bump type")
    bump_result = u.Infra.bump_version(current, bump)
    if bump_result.is_failure:
        return r[str].fail(bump_result.error or "bump failed")
    return r[str].ok(str(bump_result.value))


def _resolve_tag(tag_arg: str, version: str) -> r[str]:
    if tag_arg:
        requested = str(tag_arg)
        if not requested.startswith("v"):
            return r[str].fail("tag must start with v")
        return r[str].ok(requested)
    return r[str].ok(f"v{version}")


# ── Router ───────────────────────────────────────────────────


class FlextInfraReleaseCli:
    """Declarative CLI router for release orchestration."""

    def __init__(self) -> None:
        """Initialize CLI app and register declarative routes."""
        self._app = cli.create_app_with_common_params(
            name="release",
            help_text="Release orchestration",
        )
        self._register_commands()

    def run(self, args: t.StrSequence | None = None) -> r[bool]:
        """Execute the CLI application."""
        return cli.execute_app(self._app, prog_name="release", args=args)

    def _register_commands(self) -> None:
        cli.register_result_route(
            self._app,
            route=m.Cli.ResultCommandRouteModel(
                name="run",
                help_text="Run release orchestration CLI flow",
                model_cls=ReleaseInput,
                handler=self._handle_run,
                success_message="Release completed successfully",
                failure_message="Release failed",
            ),
        )

    @staticmethod
    def _handle_run(params: ReleaseInput) -> r[bool]:
        """Execute release orchestration with resolved version and phases."""
        resolved_workspace = Path(params.workspace) if params.workspace else Path.cwd()
        dry_run = not params.apply
        root_result = u.Infra.workspace_root(resolved_workspace)
        if root_result.is_failure:
            return r[bool].fail(
                root_result.error or "workspace root not found",
            )
        root: Path = Path(str(root_result.value))
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
            version_result = _resolve_version(
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
        tag_result = _resolve_tag(params.tag, resolved_version)
        if tag_result.is_failure:
            return r[bool].fail(tag_result.error or "tag resolution failed")
        resolved_tag = str(tag_result.value)
        service = FlextInfraReleaseOrchestrator()
        return service.run_release(
            m.Infra.ReleaseOrchestratorConfig(
                workspace_root=root,
                version=resolved_version,
                tag=resolved_tag,
                phases=phases,
                project_names=params.projects or None,
                dry_run=dry_run,
                push=params.push,
                dev_suffix=params.dev_suffix,
                create_branches=params.create_branches == 1,
                next_dev=params.next_dev,
                next_bump=params.next_bump,
            ),
        )


# ── Entry Point ──────────────────────────────────────────────


def main(argv: t.StrSequence | None = None) -> int:
    """Run the release module entrypoint."""
    FlextRuntime.ensure_structlog_configured()
    result = FlextInfraReleaseCli().run(argv)
    return 0 if result.is_success else 1


if __name__ == "__main__":
    sys.exit(main())
