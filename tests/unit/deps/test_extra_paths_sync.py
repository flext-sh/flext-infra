"""Test the projected type-checker search paths.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from flext_infra.deps import FlextInfraExtraPathsManager
from tests import tm


class TestsFlextInfraDepsExtraPathsSync:
    """Behavior contract for the projected Pyright and Mypy search paths."""

    @staticmethod
    def test_projected_paths_keep_the_source_root_first(tmp_path: Path) -> None:
        """Both projections order the source root first; Mypy omits the root."""
        rules = config.Infra.tooling.tools.pyrefly.path_rules
        (tmp_path / rules.source_dir).mkdir()
        manager = FlextInfraExtraPathsManager(repository_root=tmp_path)
        tm.that(
            manager.pyright_extra_paths(),
            eq=(rules.source_dir, rules.project_root),
        )
        tm.that(
            manager.mypy_search_paths(project_dir=tmp_path),
            eq=(rules.source_dir,),
        )
