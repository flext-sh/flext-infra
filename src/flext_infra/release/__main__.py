"""CLI entry point for release orchestration.

Usage:
    python -m flext_infra release --phase validate --dry-run --workspace .
    python -m flext_infra release --phase version --version 1.0.0 --workspace .
    python -m flext_infra release --phase all --version 1.0.0 --workspace . --dry-run

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator, c, m, output, t, u


def _resolve_version(
    version_arg: str,
    bump_arg: str,
    interactive: int,
    root_path: Path,
) -> str:
    if version_arg:
        requested = str(version_arg)
        parse_result = u.Infra.parse_semver(requested)
        if parse_result.is_failure:
            raise RuntimeError(parse_result.error or "invalid version")
        return requested
    current_result = u.Infra.current_workspace_version(root_path)
    if current_result.is_failure:
        raise RuntimeError(current_result.error or "cannot read current version")
    current: str = str(current_result.value)
    if bump_arg:
        bump_result = u.Infra.bump_version(current, bump_arg)
        if bump_result.is_failure:
            raise RuntimeError(bump_result.error or "bump failed")
        return str(bump_result.value)
    if interactive != 1:
        return str(current)
    bump = input("bump> ").strip().lower()
    if bump not in {"major", "minor", "patch"}:
        msg = "invalid bump type"
        raise RuntimeError(msg)
    bump_result = u.Infra.bump_version(current, bump)
    if bump_result.is_failure:
        raise RuntimeError(bump_result.error or "bump failed")
    return str(bump_result.value)


def _resolve_tag(tag_arg: str, version: str) -> str:
    if tag_arg:
        requested = str(tag_arg)
        if not requested.startswith("v"):
            msg = "tag must start with v"
            raise RuntimeError(msg)
        return requested
    return f"v{version}"


def run(argv: t.StrSequence | None = None) -> int:
    """Run release orchestration CLI flow."""
    parser = u.Infra.create_parser(
        prog="release",
        description="Release orchestration",
        include_apply=True,
    )
    _ = parser.add_argument("--phase", default="all")
    _ = parser.add_argument("--version", default="")
    _ = parser.add_argument("--tag", default="")
    _ = parser.add_argument("--bump", default="")
    _ = parser.add_argument("--interactive", type=int, default=1)
    _ = parser.add_argument("--push", action="store_true", default=False)
    _ = parser.add_argument("--dev-suffix", action="store_true", default=False)
    _ = parser.add_argument("--next-dev", action="store_true", default=False)
    _ = parser.add_argument("--next-bump", default="minor")
    _ = parser.add_argument("--create-branches", type=int, default=1)
    _ = parser.add_argument("--projects", nargs="*", default=[])
    args = parser.parse_args(argv)
    cli = u.Infra.resolve(args)
    root_result = u.Infra.workspace_root(cli.workspace)
    if root_result.is_failure:
        return u.Infra.exit_code(root_result)
    root: Path = Path(str(root_result.value))
    phases = (
        [
            c.Infra.Verbs.VALIDATE,
            c.Infra.Toml.VERSION,
            c.Infra.Directories.BUILD,
            "publish",
        ]
        if args.phase == "all"
        else [part.strip() for part in args.phase.split(",") if part.strip()]
    )
    needs_version = bool(
        {c.Infra.Toml.VERSION, c.Infra.Directories.BUILD, "publish"} & set(phases),
    )
    if needs_version:
        try:
            version = _resolve_version(
                args.version,
                args.bump,
                args.interactive,
                root,
            )
        except RuntimeError as exc:
            output.error(str(exc))
            return 1
    else:
        version = args.version or "0.0.0"
    tag = _resolve_tag(args.tag, version)
    service = FlextInfraReleaseOrchestrator()
    result = service.run_release(
        m.Infra.ReleaseOrchestratorConfig(
            workspace_root=root,
            version=version,
            tag=tag,
            phases=phases,
            project_names=args.projects or None,
            dry_run=cli.dry_run,
            push=args.push,
            dev_suffix=args.dev_suffix,
            create_branches=args.create_branches == 1,
            next_dev=args.next_dev,
            next_bump=args.next_bump,
        ),
    )
    return u.Infra.exit_code(result)


def main() -> int:
    """Run the release module entrypoint."""
    return u.Infra.run_cli(run)


if __name__ == "__main__":
    sys.exit(main())
