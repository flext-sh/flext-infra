"""In-memory release forge implementing the ``p.Infra.ReleaseForge`` port.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from tests import m, p, r, u


class TestsFlextInfraReleaseForgeMemory:
    """Real forge state held in memory: releases, assets, bytes and effects.

    Every effect the publish phase performs is appended to ``effects`` in
    order, so a scenario observes exactly what reached the forge.
    """

    def __init__(
        self,
        tag_commit: str,
        *,
        native_digest: bool = True,
        upload_state: str = "uploaded",
    ) -> None:
        """Declare the remote tag commit and how uploads are recorded."""
        self.tag_commit = tag_commit
        self.native_digest = native_digest
        self.upload_state = upload_state
        self.releases: MutableSequence[m.Infra.GithubReleaseIdentity] = []
        self.assets: MutableMapping[int, MutableSequence[m.Infra.GithubReleaseAsset]] = {}
        self.blobs: MutableMapping[str, bytes] = {}
        self.effects: MutableSequence[str] = []

    def seed_release(self, tag: str, *, draft: bool) -> int:
        """Declare an existing remote release and return its identifier.

        Returns:
            The native identifier of the declared release.

        """
        release_id = len(self.releases) + 1
        self.releases.append(
            m.Infra.GithubReleaseIdentity(id=release_id, tag_name=tag, draft=draft),
        )
        self.assets[release_id] = []
        return release_id

    def seed_asset(
        self,
        release_id: int,
        name: str,
        content: bytes,
        *,
        digest: str | None,
        state: str = "uploaded",
    ) -> None:
        """Declare an existing remote asset with its bytes and native metadata."""
        self.assets[release_id].append(
            m.Infra.GithubReleaseAsset(name=name, digest=digest, state=state),
        )
        self.blobs[name] = content

    def release_forge_tag_commit(self, root: Path, tag: str) -> p.Result[str]:
        """Return the declared remote tag commit.

        Returns:
            The declared commit.

        """
        del root, tag
        return r[str].ok(self.tag_commit)

    def release_forge_releases(
        self,
        root: Path,
    ) -> p.Result[p.Infra.GithubReleaseInventory]:
        """Return every declared release.

        Returns:
            The complete inventory.

        """
        del root
        return r[p.Infra.GithubReleaseInventory].ok(
            m.Infra.GithubReleaseInventory(releases=tuple(self.releases)),
        )

    def release_forge_assets(
        self,
        root: Path,
        release_id: int,
    ) -> p.Result[p.Infra.GithubReleaseAssets]:
        """Return every asset of one declared release.

        Returns:
            The complete asset inventory.

        """
        del root
        return r[p.Infra.GithubReleaseAssets].ok(
            m.Infra.GithubReleaseAssets(assets=tuple(self.assets[release_id])),
        )

    def release_forge_download(
        self,
        root: Path,
        tag: str,
        name: str,
        destination: Path,
    ) -> p.Result[bool]:
        """Write the stored asset bytes to ``destination``.

        Returns:
            Success once the bytes are written.

        """
        del root, tag
        destination.write_bytes(self.blobs[name])
        return r[bool].ok(value=True)

    def release_forge_create_draft(
        self,
        root: Path,
        tag: str,
        title: str,
        notes: Path,
    ) -> p.Result[bool]:
        """Record a new draft release for ``tag``.

        Returns:
            Success once the draft exists.

        """
        del root, title, notes
        self.effects.append("create-draft")
        self.seed_release(tag, draft=True)
        return r[bool].ok(value=True)

    def release_forge_upload(
        self,
        root: Path,
        tag: str,
        paths: Sequence[str],
    ) -> p.Result[bool]:
        """Store each local file as an asset of the release for ``tag``.

        Returns:
            Success once every file is stored.

        """
        del root
        release = next(item for item in self.releases if item.tag_name == tag)
        for path in paths:
            local = Path(path)
            digest = f"sha256:{u.Cli.sha256_file(local)}" if self.native_digest else None
            self.effects.append(f"upload:{local.name}")
            self.seed_asset(
                release.id,
                local.name,
                local.read_bytes(),
                digest=digest,
                state=self.upload_state,
            )
        return r[bool].ok(value=True)

    def release_forge_publish(self, root: Path, tag: str) -> p.Result[bool]:
        """Mark the draft release for ``tag`` as published.

        Returns:
            Success once the release is public.

        """
        del root
        self.effects.append("publish")
        self.releases = [
            item.model_copy(update={"draft": False}) if item.tag_name == tag else item
            for item in self.releases
        ]
        return r[bool].ok(value=True)


__all__: list[str] = ["TestsFlextInfraReleaseForgeMemory"]
