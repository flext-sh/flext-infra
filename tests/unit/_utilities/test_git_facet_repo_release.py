"""Public u.Infra Git facet — an opened repository never outlives its call.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from pathlib import Path

from tests import m, tm, u


class TestsFlextInfraGitFacetRepoRelease:
    """Reading object data must not leave a persistent ``git cat-file`` child."""

    @staticmethod
    def _cat_file_children() -> tuple[int, ...]:
        """Return the live ``git cat-file`` child pids of this process."""
        pids: list[int] = []
        tasks = Path(f"/proc/{os.getpid()}/task")
        for children_file in tasks.glob("*/children"):
            for raw in children_file.read_text(encoding="utf-8").split():
                cmdline = Path(f"/proc/{raw}/cmdline")
                if cmdline.exists() and b"cat-file" in cmdline.read_bytes():
                    pids.append(int(raw))
        return tuple(pids)

    def test_head_and_identity_leave_no_cat_file_child(
        self,
        real_git_repo: Path,
    ) -> None:
        """Resolving HEAD and the semantic identity releases every opened Repo."""
        request = m.Infra.GitRepoRequest(repo_root=real_git_repo)
        tm.ok(u.Infra.git_repository_head(request))
        tm.ok(u.Infra.git_identity(request))
        tm.that(self._cat_file_children(), eq=())
