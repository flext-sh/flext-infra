"""Project-owned Mise tools: declaration, composition, and lock platform scope.

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

from pathlib import Path

import pytest

from flext_infra import config, m
from tests import tm, u


class TestsFlextInfraProjectMiseTools:
    """A project declares its own tools without touching the fleet catalog."""

    @staticmethod
    def _project(root: Path, tools_yaml: str) -> Path:
        root.mkdir(parents=True)
        (root / "config").mkdir()
        (root / "config" / "managed-artifacts.yaml").write_text(
            tools_yaml,
            encoding="utf-8",
        )
        return root

    def test_declared_tool_reaches_generated_mise_toml(self, tmp_path: Path) -> None:
        """Test declared tool reaches generated mise toml."""
        root = self._project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool":\n'
            '        version: "1.2.3"\n',
        )

        snapshot = tm.ok(u.Infra.snapshot_project_managed_artifacts(root))
        python_version = config.Infra.codegen.toolchain.python_version
        composed = u.Infra.compose_mise_toml_from_snapshot(
            snapshot.sources,
            f'[tools]\npython = "{python_version}"\n',
        )

        tools = u.Tests.toml_table_at(tm.ok(composed), "tools")
        tm.that(tools["github:example/tool"] == "1.2.3", truth=True)
        tm.that(tools["python"] == python_version, truth=True)

    def test_version_string_shorthand_is_not_a_declaration(
        self,
        tmp_path: Path,
    ) -> None:
        """Test version string shorthand is not a declaration."""
        root = self._project(
            tmp_path / "project",
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      "github:example/tool": "1.2.3"\n',
        )

        with pytest.raises(m.ValidationError):
            u.Infra.load_project_managed_artifacts(root)
