"""Source ownership and authenticated reads across nested workspace members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraSnapshotSourceOwnership:
    """Member ordering never changes the nearest real source owner."""

    @staticmethod
    @pytest.mark.parametrize("reverse_members", [False, True])
    def test_nested_and_equal_depth_members_keep_authenticated_sources(
        tmp_path: Path, *, reverse_members: bool
    ) -> None:
        """The same file remains owned and authenticated under either ordering."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owners = (root, package / "alpha", package / "bravo", package / "alpha/nested")
        for owner in owners:
            owner.mkdir(parents=True, exist_ok=True)
            (owner / "owned.py").write_text(
                f"OWNER = {owner.name!r}\n", encoding=c.DEFAULT_ENCODING
            )
        members = tuple(reversed(owners)) if reverse_members else owners
        with u.Infra.workspace_snapshot(root, members) as snapshot:
            for owner in owners:
                path = owner / "owned.py"
                original = tm.ok(
                    u.Cli.atomic_read_binary_file_state(path, required=True)
                )
                captured = u.Infra.workspace_source(snapshot, path)
                tm.that(captured.member, eq=owner.resolve())
                tm.that(captured.state, eq=original)
                tm.that(captured.text.encode(c.DEFAULT_ENCODING), eq=original.content)
                tm.that(u.Infra.workspace_source(snapshot, path) is captured, eq=True)

    @staticmethod
    def test_source_outside_declared_members_remains_refused(tmp_path: Path) -> None:
        """An existing file outside the elected members never acquires an owner."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        outside = root / "outside.py"
        outside.write_text("VALUE = 'outside'\n", encoding=c.DEFAULT_ENCODING)
        with u.Infra.workspace_snapshot(root, (package,)) as snapshot:
            with pytest.raises(ValueError, match="outside every member"):
                u.Infra.workspace_source(snapshot, outside)
            tm.fail(outside in snapshot.sources)
