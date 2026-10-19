"""Focused behavior tests for Rope import utilities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.workspace.rope import FlextInfraRopeWorkspace
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeImports:
    """Validate fail-fast behavior for Rope import utility wrappers."""

    @staticmethod
    def test_normalize_imports_removes_orphaned_imports_and_formats(
        tmp_path: Path,
    ) -> None:
        """Centralized import cleanup should leave one lint-clean module."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "import tempfile\n"
                "import os\n\n"
                "def keep() -> str:\n"
                "    return os.getcwd()\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            result = u.Infra.normalize_imports(
                rope.rope_project,
                file_paths=(module_path,),
            )

        tm.ok(result)
        tm.that(
            module_path.read_text(encoding="utf-8"),
            eq=(
                "from __future__ import annotations\n\n"
                "import os\n\n"
                "\n"
                "def keep() -> str:\n"
                "    return os.getcwd()\n"
            ),
        )

    @staticmethod
    def test_normalize_imports_preserves_quoted_cast_types(
        tmp_path: Path,
    ) -> None:
        """A type referenced only inside cast must retain its import."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            "from typing import Literal, cast\nimport tempfile\n\n"
            'value = cast("Literal[1]", 1)\n',
            encoding="utf-8",
        )
        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            tm.ok(
                u.Infra.normalize_imports(rope.rope_project, file_paths=(module_path,)),
            )
            source = module_path.read_text(encoding="utf-8")
            tm.that(source, has="from typing import Literal, cast")
            tm.that(source, lacks="tempfile")
            tm.that(
                tm.ok(
                    u.Infra.normalize_imports(
                        rope.rope_project,
                        file_paths=(module_path,),
                    ),
                ),
                eq=False,
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("module_source", "expected_change"),
        [
            pytest.param(
                (
                    "from __future__ import annotations\n\n"
                    "import os\n\n\n"
                    "def keep() -> str:\n"
                    "    return os.getcwd()\n"
                ),
                False,
                id="already-clean",
            ),
            pytest.param(
                (
                    "from __future__ import annotations\n\n"
                    "import os\n"
                    "import sys\n\n\n"
                    "def keep() -> str:\n"
                    "    return os.getcwd()\n"
                ),
                True,
                id="unused-import",
            ),
        ],
    )
    def test_organize_imports_detection_matches_module_state(
        tmp_path: Path,
        module_source: str,
        *,
        expected_change: bool,
    ) -> None:
        """Detection reports a pending organize change only for unorganized modules."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(module_source, encoding="utf-8")

        with FlextInfraRopeWorkspace.open_workspace(repository_root) as rope:
            resource = rope.resource(module_path)
            resource = tm.not_none(resource)
            result = u.Infra.organize_imports(rope.rope_project, resource, apply=False)

        tm.ok(result)
        tm.that(result.value, eq=expected_change)
