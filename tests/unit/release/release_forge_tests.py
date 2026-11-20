"""Release forge inventories read every paginated page through the native gh.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from json import dumps, loads
from pathlib import Path

from tests import m, t, tm, u


class TestsFlextInfraReleaseForge:
    """Behavior contract for the release forge's paginated inventories."""

    _GH = Path(__file__).parents[2] / "fixtures" / "release-forge-gh"

    @classmethod
    def _pages(cls, tmp_path: Path, pages: tuple[str, ...]) -> t.StrMapping:
        """Serve one JSON document per page and route ``gh`` to the double.

        Returns:
            The environment scope that serves those pages.

        """
        served = tmp_path / "pages.jsonl"
        served.write_text("".join(f"{page}\n" for page in pages), encoding="utf-8")
        return {
            "PATH": f"{cls._GH}{os.pathsep}{os.environ['PATH']}",
            "RELEASE_FORGE_PAGES": str(served),
        }

    @classmethod
    def test_releases_join_every_page(cls, tmp_path: Path) -> None:
        """Each page validates on its own and the inventory keeps API order."""
        first = m.Infra.GithubReleaseIdentity(id=2, tag_name="v0.12.1", draft=False)
        second = m.Infra.GithubReleaseIdentity(id=1, tag_name="v0.12.0", draft=True)
        env = cls._pages(
            tmp_path,
            tuple(
                m.Infra.GithubReleaseInventory(releases=(release,)).model_dump_json()
                for release in (first, second)
            ),
        )

        with tm.scope(env=env):
            inventory = tm.ok(u.Infra.release_forge_releases(tmp_path))

        tm.that(inventory.releases, eq=(first, second))

    @classmethod
    def test_assets_join_every_page(cls, tmp_path: Path) -> None:
        """Assets of every page form the one release asset inventory."""
        wheel = m.Infra.GithubReleaseAsset(name="flext_infra.whl", state="uploaded")
        sdist = m.Infra.GithubReleaseAsset(name="flext_infra.tar.gz", state="new")
        env = cls._pages(
            tmp_path,
            tuple(
                m.Infra.GithubReleaseAssets(assets=(asset,)).model_dump_json()
                for asset in (wheel, sdist)
            ),
        )

        with tm.scope(env=env):
            inventory = tm.ok(u.Infra.release_forge_assets(tmp_path, 7))

        tm.that(inventory.assets, eq=(wheel, sdist))

    @classmethod
    def test_a_page_outside_the_contract_fails(cls, tmp_path: Path) -> None:
        """A page carrying an undeclared field fails strict validation."""
        release = m.Infra.GithubReleaseIdentity(id=1, tag_name="v0.12.0", draft=False)
        page = loads(
            m.Infra.GithubReleaseInventory(releases=(release,)).model_dump_json()
        )
        page["undeclared"] = True
        env = cls._pages(tmp_path, (dumps(page),))

        with tm.scope(env=env):
            result = u.Infra.release_forge_releases(tmp_path)

        tm.that(result.failure, eq=True)
