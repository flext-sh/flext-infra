"""Native GitHub CLI owner of the release forge port.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from glob import escape
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r


class FlextInfraUtilitiesReleaseForge:
    """Bind every release forge read and effect to one ``gh`` invocation."""

    @staticmethod
    def release_forge_tag_commit(root: Path, tag: str) -> p.Result[str]:
        """Return the commit the remote tag resolves to.

        Returns:
            The remote commit SHA, or the first read failure.

        """
        return u.Cli.capture(
            [
                c.Infra.GH,
                "api",
                f"repos/{{owner}}/{{repo}}/commits/{tag}",
                "--jq",
                ".sha",
            ],
            cwd=root,
        ).map(str.strip)

    @staticmethod
    def release_forge_releases(
        root: Path,
    ) -> p.Result[p.Infra.GithubReleaseInventory]:
        """Return the complete paginated release inventory, drafts included.

        Returns:
            The typed inventory, or the first read or validation failure.

        """
        inventory = u.Cli.capture(
            [
                c.Infra.GH,
                "api",
                "repos/{owner}/{repo}/releases",
                "--paginate",
                "--slurp",
                "--jq",
                "{releases: [.[][] | {id, tag_name, draft}]}",
            ],
            cwd=root,
        )
        if inventory.failure:
            return r[p.Infra.GithubReleaseInventory].from_failure(inventory)
        return u.validate_value(
            m.Infra.GithubReleaseInventory,
            inventory.value,
            from_json=True,
        )

    @staticmethod
    def release_forge_assets(
        root: Path,
        release_id: int,
    ) -> p.Result[p.Infra.GithubReleaseAssets]:
        """Return the complete paginated asset inventory of one release.

        Returns:
            The typed asset inventory, or the first read or validation failure.

        """
        inventory = u.Cli.capture(
            [
                c.Infra.GH,
                "api",
                f"repos/{{owner}}/{{repo}}/releases/{release_id}/assets",
                "--paginate",
                "--slurp",
                "--jq",
                "{assets: [.[][] | {name, digest, state}]}",
            ],
            cwd=root,
        )
        if inventory.failure:
            return r[p.Infra.GithubReleaseAssets].from_failure(inventory)
        return u.validate_value(
            m.Infra.GithubReleaseAssets,
            inventory.value,
            from_json=True,
        )

    @staticmethod
    def release_forge_download(
        root: Path,
        tag: str,
        name: str,
        destination: Path,
    ) -> p.Result[bool]:
        """Download one release asset's bytes to ``destination``.

        Returns:
            Success once ``gh`` wrote the asset, or its failure.

        """
        return u.Cli.run_checked(
            [
                c.Infra.GH,
                "release",
                "download",
                tag,
                "--pattern",
                escape(name),
                "--output",
                str(destination),
            ],
            cwd=root,
        )

    @staticmethod
    def release_forge_create_draft(
        root: Path,
        tag: str,
        title: str,
        notes: Path,
    ) -> p.Result[bool]:
        """Create an unpublished draft release for an existing remote tag.

        Returns:
            Success once the draft exists, or the native failure.

        """
        return u.Cli.run_checked(
            [
                c.Infra.GH,
                "release",
                "create",
                tag,
                "--draft",
                "--verify-tag",
                "--title",
                title,
                "--notes-file",
                str(notes),
            ],
            cwd=root,
        )

    @staticmethod
    def release_forge_upload(
        root: Path,
        tag: str,
        paths: Sequence[str],
    ) -> p.Result[bool]:
        """Upload local files as assets of the release for ``tag``.

        Returns:
            Success once every file was uploaded, or the native failure.

        """
        return u.Cli.run_checked(
            [c.Infra.GH, "release", "upload", tag, *paths],
            cwd=root,
        )

    @staticmethod
    def release_forge_publish(root: Path, tag: str) -> p.Result[bool]:
        """Publish the draft release for ``tag``: the single commit point.

        Returns:
            Success once the release is public, or the native failure.

        """
        return u.Cli.run_checked(
            [c.Infra.GH, "release", "edit", tag, "--draft=false"],
            cwd=root,
        )


__all__: list[str] = ["FlextInfraUtilitiesReleaseForge"]
