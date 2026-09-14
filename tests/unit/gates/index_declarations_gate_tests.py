"""Tests for FlextInfraIndexDeclarationsGate.

The gate proves every indexed gitlink is declared by the repository itself.
The fixture builds real repositories inside ``tmp_path``: the defect is a
property of a real index, so a stub would prove nothing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra.gates.index_declarations import FlextInfraIndexDeclarationsGate
from tests import m, u

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class TestsFlextInfraIndexDeclarationsGate:
    """Every indexed gitlink must be declared in `.gitmodules`."""

    @pytest.fixture
    def gate_result(self, tmp_path: Path) -> Callable[..., m.Infra.GateResult]:
        """Build a repository with the requested defects and run the gate over it.

        One owner for the whole arrange-act pair: the tests differ only in which
        defect they seed.
        """

        def run(
            *, orphan_gitlink: bool = False, declare_gitlink: bool = False
        ) -> m.Infra.GateResult:
            u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=tmp_path)).unwrap()
            (tmp_path / ".gitignore").write_text("ignored/\n", encoding="utf-8")
            (tmp_path / "kept.txt").write_text("kept\n", encoding="utf-8")
            u.Infra.git_add_paths(
                m.Infra.GitPathsRequest(
                    repo_root=tmp_path, paths=(".gitignore", "kept.txt")
                )
            ).unwrap()
            if orphan_gitlink:
                nested = tmp_path / "nested"
                nested.mkdir()
                u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=nested)).unwrap()
                (nested / "file.txt").write_text("inner\n", encoding="utf-8")
                u.Infra.git_add_paths(
                    m.Infra.GitPathsRequest(repo_root=nested, paths=("file.txt",))
                ).unwrap()
                u.Infra.git_commit(
                    m.Infra.GitCommitRequest(repo_root=nested, message="inner")
                ).unwrap()
                # Staging a directory that carries its own .git records a gitlink,
                # with no .gitmodules section and no warning. Porcelain `git add`
                # is what does that; the index-level add skips the directory.
                u.Infra.git_stage_paths(
                    m.Infra.GitPathsRequest(repo_root=tmp_path, paths=("nested",))
                ).unwrap()
                if declare_gitlink:
                    (tmp_path / ".gitmodules").write_text(
                        '[submodule "nested"]\n\tpath = nested\n'
                        "\turl = https://example.invalid/nested.git\n",
                        encoding="utf-8",
                    )
                    u.Infra.git_add_paths(
                        m.Infra.GitPathsRequest(repo_root=tmp_path, paths=(".gitmodules",))
                    ).unwrap()
            u.Infra.git_commit(
                m.Infra.GitCommitRequest(repo_root=tmp_path, message="seed")
            ).unwrap()
            context = m.Infra.GateContext(
                repository_root=tmp_path, reports_dir=tmp_path / ".reports"
            )
            gate = FlextInfraIndexDeclarationsGate(repository_root=tmp_path)
            return gate.check(tmp_path, context).result

        return run

    def test_consistent_repository_passes(
        self, gate_result: Callable[..., m.Infra.GateResult]
    ) -> None:
        result = gate_result()
        tm.that(result.passed, eq=True)
        tm.that(len(result.errors), eq=0)

    def test_undeclared_gitlink_fails_naming_the_path(
        self, gate_result: Callable[..., m.Infra.GateResult]
    ) -> None:
        result = gate_result(orphan_gitlink=True)
        tm.that(result.passed, eq=False)
        tm.that(len(result.errors), eq=1)
        tm.that(result.errors[0], has="nested")
        tm.that(result.errors[0], has=".gitmodules")

    def test_declared_gitlink_passes(
        self, gate_result: Callable[..., m.Infra.GateResult]
    ) -> None:
        # The same gitlink, now declared, is legitimate topology and must not
        # be reported: the gate judges the declaration, never the mode.
        result = gate_result(orphan_gitlink=True, declare_gitlink=True)
        tm.that(result.passed, eq=True)
        tm.that(len(result.errors), eq=0)


__all__: list[str] = ["TestsFlextInfraIndexDeclarationsGate"]
