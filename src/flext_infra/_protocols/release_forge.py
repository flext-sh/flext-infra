"""Forge port consumed by the release publish phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path

    from flext_cli import p

    from flext_infra._protocols import FlextInfraProtocolsRelease


class FlextInfraProtocolsReleaseForge:
    """Release forge protocols exposed through ``p.Infra``."""

    @runtime_checkable
    class ReleaseForge(Protocol):
        """Smallest forge surface the atomic draft-then-publish flow consumes.

        The composition root binds the native forge owner; every method is
        one remote read or one remote effect and returns its first failure.
        """

        def release_forge_tag_commit(self, root: Path, tag: str) -> p.Result[str]:
            """Return the commit the remote tag resolves to."""
            ...

        def release_forge_releases(
            self,
            root: Path,
        ) -> p.Result[FlextInfraProtocolsRelease.GithubReleaseInventory]:
            """Return the complete paginated release inventory."""
            ...

        def release_forge_assets(
            self,
            root: Path,
            release_id: int,
        ) -> p.Result[FlextInfraProtocolsRelease.GithubReleaseAssets]:
            """Return the complete paginated asset inventory of one release."""
            ...

        def release_forge_download(
            self,
            root: Path,
            tag: str,
            name: str,
            destination: Path,
        ) -> p.Result[bool]:
            """Download one release asset's bytes to ``destination``."""
            ...

        def release_forge_create_draft(
            self,
            root: Path,
            tag: str,
            title: str,
            notes: Path,
        ) -> p.Result[bool]:
            """Create an unpublished draft release for an existing remote tag."""
            ...

        def release_forge_upload(
            self,
            root: Path,
            tag: str,
            paths: Sequence[str],
        ) -> p.Result[bool]:
            """Upload local files as assets of the release for ``tag``."""
            ...

        def release_forge_publish(self, root: Path, tag: str) -> p.Result[bool]:
            """Publish the draft release for ``tag``: the single commit point."""
            ...


__all__: list[str] = ["FlextInfraProtocolsReleaseForge"]
