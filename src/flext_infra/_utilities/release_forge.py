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
    def _release_forge_pages[TPage: p.StrictBoundaryModel](
        root: Path,
        endpoint: str,
        page_filter: str,
        page_model: type[TPage],
    ) -> p.Result[tuple[TPage, ...]]:
        """Read every page of one paginated endpoint as a validated page model.

        ``gh api --paginate`` applies ``--jq`` to each page and prints one
        JSON document per page (``--slurp`` is rejected together with
        ``--jq``), so each line is one page validated by its strict model.

        Returns:
            The validated pages in API order, or the first read or validation
            failure.

        """
        captured = u.Cli.capture(
            [c.Infra.GH, "api", endpoint, "--paginate", "--jq", page_filter],
            cwd=root,
        )
        if captured.failure:
            return r[tuple[TPage, ...]].from_failure(captured)
        pages: list[TPage] = []
        for line in captured.value.splitlines():
            page = u.validate_value(page_model, line, from_json=True)
            if page.failure:
                return r[tuple[TPage, ...]].from_failure(page)
            pages.append(page.value)
        return r[tuple[TPage, ...]].ok(tuple(pages))

    @staticmethod
    def release_forge_releases(
        root: Path,
    ) -> p.Result[p.Infra.GithubReleaseInventory]:
        """Return the complete paginated release inventory, drafts included.

        Returns:
            The typed inventory, or the first read or validation failure.

        """
        pages = FlextInfraUtilitiesReleaseForge._release_forge_pages(
            root,
            "repos/{owner}/{repo}/releases",
            "{releases: [.[] | {id, tag_name, draft}]}",
            m.Infra.GithubReleaseInventory,
        )
        return pages.map(
            lambda inventories: m.Infra.GithubReleaseInventory(
                releases=tuple(
                    release for page in inventories for release in page.releases
                ),
            ),
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
        pages = FlextInfraUtilitiesReleaseForge._release_forge_pages(
            root,
            f"repos/{{owner}}/{{repo}}/releases/{release_id}/assets",
            "{assets: [.[] | {name, digest, state}]}",
            m.Infra.GithubReleaseAssets,
        )
        return pages.map(
            lambda inventories: m.Infra.GithubReleaseAssets(
                assets=tuple(asset for page in inventories for asset in page.assets),
            ),
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
