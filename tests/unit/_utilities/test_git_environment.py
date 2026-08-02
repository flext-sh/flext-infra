"""Real Git isolation tests for explicit repository boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c
from flext_tests import tm
from tests import u


class TestsGitEnvironmentIsolation:
    """Prove ambient repository-local variables cannot redirect Git commands."""

    def test_explicit_repository_ignores_ambient_git_repository(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        origin = tmp_path / "origin"
        target = tmp_path / "target"
        origin.mkdir()
        target.mkdir()
        origin_file = origin / "origin.txt"
        target_file = target / "target.txt"
        origin_file.write_text("origin\n", encoding="utf-8")
        u.Tests.initialize_git_repo(origin)
        u.Tests.initialize_git_repo(target)
        target_file.write_text("target\n", encoding="utf-8")
        origin_index = origin / c.Infra.GIT_DIR / "index"
        index_before = origin_index.read_bytes()

        monkeypatch.setenv("GIT_INDEX_FILE", str(origin_index))
        monkeypatch.setenv("GIT_DIR", str(origin / c.Infra.GIT_DIR))
        monkeypatch.setenv("GIT_WORK_TREE", str(origin))

        tm.ok(u.Infra.git_capture(target, ("add", target_file.name)))
        target_status = tm.ok(
            u.Infra.git_capture_bytes(
                target, ("status", "--porcelain=v1", "-z")
            )
        )
        tm.that(origin_index.read_bytes(), eq=index_before)
        origin_status = tm.ok(u.Infra.git_capture(origin, ("status", "--short")))

        tm.that(
            target_status,
            eq=f"A  {target_file.name}\0".encode(c.Cli.ENCODING_DEFAULT),
        )
        tm.that(origin_status, eq="")
