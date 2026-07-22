"""External-worktree contract for generated uv project resolution."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


def _run(command: list[str], cwd: Path) -> None:
    result = u.Cli.run_raw(command, cwd=cwd)
    tm.that(result.success, eq=True)


class TestsFlextInfraBasemkWorktreeUvContract:
    """Resolve uv sources against the canonical checkout from any worktree."""

    def test_external_worktree_uses_canonical_project_and_lane_environment(
        self, tmp_path: Path
    ) -> None:
        canonical_root = tmp_path / "canonical" / "consumer"
        lane_root = tmp_path / "lanes" / "consumer-feature"
        canonical_root.mkdir(parents=True)
        lane_root.parent.mkdir(parents=True)
        _run(["git", "init", "-q"], canonical_root)
        _run(["git", "config", "user.email", "tests@flext.sh"], canonical_root)
        _run(["git", "config", "user.name", "FLEXT Tests"], canonical_root)
        (canonical_root / "tracked.txt").write_text("fixture\n", encoding="utf-8")
        _run(["git", "add", "tracked.txt"], canonical_root)
        _run(["git", "commit", "-q", "-m", "fixture"], canonical_root)
        _run(
            ["git", "worktree", "add", "-q", str(lane_root), "-b", "feature"],
            canonical_root,
        )

        rendered = tm.ok(FlextInfraBaseMkGenerator().generate_basemk())
        (lane_root / "base.mk").write_text(rendered, encoding="utf-8")
        (lane_root / "Makefile").write_text(
            "include base.mk\n"
            "print-uv-roots:\n"
            '\t@printf \'%s\\n%s\\n\' "$(UV_PROJECT)" "$(UV_PROJECT_ENVIRONMENT)"\n',
            encoding="utf-8",
        )

        active_env = os.environ.copy()
        inherited_keys = (
            "FLEXT_ROOT",
            "FLEXT_STANDALONE",
            "FLEXT_WORKSPACE_ROOT",
            "UV_PROJECT",
            "UV_PROJECT_ENVIRONMENT",
            "VIRTUAL_ENV",
            "WORKSPACE_ROOT",
        )
        for key in inherited_keys:
            active_env.pop(key, None)
        active_env.update({"MAKEFLAGS": "", "MAKEOVERRIDES": ""})
        result = u.Cli.run_raw(
            ["make", "print-uv-roots"],
            cwd=lane_root,
            env=active_env,
            remove_env_keys=inherited_keys,
        )

        output = [
            line
            for line in tm.ok(result).stdout.splitlines()
            if line.startswith(str(tmp_path))
        ]
        tm.that(output, eq=[str(canonical_root), str(lane_root / ".venv")])


__all__: tuple[str, ...] = ()
