"""Generated search paths never leave the project that owns them.

A search-path entry is written into a project's own ``pyproject.toml``, so it
describes that project forever. ``../<sibling>/src`` describes the *host* the
generator happened to run on: it is wrong in any clone whose siblings sit
elsewhere, it is absent in a worktree that materializes one project alone, and
it makes the same generator emit different content per checkout. Cross-checkout
dependencies resolve through their installed distributions instead (flext-c6di).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

from tests import c, tm
from tests.unit.deps.extra_paths_support import TestsFlextInfraExtraPathsSupport

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraExtraPathsArePure:
    """No emitted entry may address another project on the filesystem."""

    @staticmethod
    def test_workspace_project_source_roots_are_not_emitted_at_the_root(
        tmp_path: Path,
    ) -> None:
        """A UV workspace project is a distribution, not a search path."""
        _ = TestsFlextInfraExtraPathsSupport.workspace_with_dependency(tmp_path)

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        result = manager.pyrefly_search_paths(project_dir=tmp_path)

        tm.that(
            result,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(tmp_path),
        )

    @staticmethod
    def test_sibling_source_roots_are_not_emitted_for_a_member(
        tmp_path: Path,
    ) -> None:
        """A member never reaches out of its own root to find a dependency."""
        consumer = TestsFlextInfraExtraPathsSupport.project(
            tmp_path,
            "flext-ldap",
            "flext_ldap",
        )
        consumer.joinpath(c.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                "name = 'flext-ldap'\n"
                "dependencies = ['flext-core']\n"
                "[tool.uv.sources]\n"
                "flext-core = { path = '../flext-core', editable = true }\n"
            ),
            encoding="utf-8",
        )
        _ = TestsFlextInfraExtraPathsSupport.project(
            tmp_path,
            "flext-core",
            "flext_core",
        )

        manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path)
        search_paths = manager.pyrefly_search_paths(project_dir=consumer)
        extra_paths = manager.pyright_extra_paths()

        for entry in (*search_paths, *extra_paths):
            tm.that(
                entry.startswith(".."),
                truth=False,
                msg=f"generated search path leaves the project: {entry}",
            )
        tm.that(
            search_paths,
            eq=TestsFlextInfraExtraPathsSupport.expected_pyrefly_paths(consumer),
        )

    @staticmethod
    def test_search_paths_survive_a_project_only_worktree(tmp_path: Path) -> None:
        """The same project alone on disk yields the same entries.

        A `make work` lane materializes one project without its siblings. Entries
        derived from sibling existence differ there, so `make gen` in the lane
        would rewrite what the primary just generated.
        """
        with_siblings = TestsFlextInfraExtraPathsSupport.project(
            tmp_path / "workspace",
            "flext-ldap",
            "flext_ldap",
        )
        _ = TestsFlextInfraExtraPathsSupport.project(
            tmp_path / "workspace",
            "flext-core",
            "flext_core",
        )
        alone = TestsFlextInfraExtraPathsSupport.project(
            tmp_path / "lane",
            "flext-ldap",
            "flext_ldap",
        )

        workspace_manager = TestsFlextInfraExtraPathsSupport.manager(
            tmp_path / "workspace",
        )
        lane_manager = TestsFlextInfraExtraPathsSupport.manager(tmp_path / "lane")

        tm.that(
            workspace_manager.pyrefly_search_paths(
                project_dir=with_siblings,
            ),
            eq=lane_manager.pyrefly_search_paths(project_dir=alone),
        )
