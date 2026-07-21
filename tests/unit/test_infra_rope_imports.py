"""Focused behavior tests for Rope import utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.workspace.rope import FlextInfraRopeWorkspace
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeImports:
    """Validate fail-fast behavior for Rope import utility wrappers."""

    def test_normalize_imports_removes_orphaned_imports_and_formats(
        self, tmp_path: Path
    ) -> None:
        """Centralized import cleanup should leave one lint-clean module."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
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

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            result = u.Infra.normalize_imports(
                rope.rope_project, file_paths=(module_path,)
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

    def test_organize_imports_treats_already_clean_module_as_noop(
        self, tmp_path: Path
    ) -> None:
        """An already-organized module yields a clean no-op result."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "import os\n\n\n"
                "def keep() -> str:\n"
                "    return os.getcwd()\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            assert resource is not None
            result = u.Infra.organize_imports(
                rope.rope_project, resource, apply=False
            )

        tm.ok(result)
        tm.that(result.value, eq=False)

    def test_organize_imports_reports_change_for_unused_import(
        self, tmp_path: Path
    ) -> None:
        """A module with an unused import yields a pending organize change."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "import os\n"
                "import sys\n\n\n"
                "def keep() -> str:\n"
                "    return os.getcwd()\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            assert resource is not None
            result = u.Infra.organize_imports(
                rope.rope_project, resource, apply=False
            )

        tm.ok(result)
        tm.that(result.value, eq=True)
