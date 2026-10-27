"""Fleet-owned mise tool composition at its owner.

``codegen conform`` exclusively owns ``.mise.toml`` (workspace environment
sync stopped writing it when the toolchain transaction landed), so the
composition rule is proven through the immutable project snapshot and the
public composer that turns that source view into the managed file.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import tm, u


class TestsFlextInfraMiseDistributionPolicy:
    """Fleet tools win over a project's stale local declaration."""

    @staticmethod
    def _workspace(root: Path) -> Path:
        u.Tests.WorktreeFixture.write_python_project(root, "fixture")
        return root

    def test_project_pin_of_packaged_tool_fails_closed(
        self,
        tmp_path: Path,
    ) -> None:
        """A project selector that the packaged toolchain owns is a duplicate.

        One owner per tool: composing ``.mise.toml`` never picks a winner
        between the packaged pin and a project redeclaration of the same
        selector; it fails naming the project source so the residue is
        removed at its owner.
        """
        root = self._workspace(tmp_path / "project")
        config_dir = root / "config"
        config_dir.mkdir()
        toolchain = config.Infra.codegen.toolchain
        selector, version = (
            toolchain.tool_selectors["qlty"],
            toolchain.tool_versions["qlty"],
        )
        (config_dir / "tools.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n"
            f'      "{selector}":\n        version: "{version}.divergent"\n',
            encoding="utf-8",
        )

        snapshot = tm.ok(u.Infra.snapshot_project_managed_artifacts(root))
        result = u.Infra.compose_mise_toml_from_snapshot(
            snapshot.sources,
            f'[tools]\n"{selector}" = "{version}"\n',
        )

        tm.fail(
            result,
            has=f"project Mise selector {selector!r} ({config_dir / 'tools.yaml'})",
        )
