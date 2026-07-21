"""Focused behavior tests for Rope import utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

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

    def test_organize_imports_treats_none_as_noop(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Rope returning ``None`` must be treated as a clean no-op."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            ("from __future__ import annotations\n\nimport os\nimport pathlib\n"),
            encoding="utf-8",
        )

        class _NoChangesOrganizer:
            def organize_imports(self, _resource: object) -> None:
                return None

        monkeypatch.setattr(
            u.Infra,
            "import_organizer",
            staticmethod(lambda _rope_project: _NoChangesOrganizer()),
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            tm.that(resource, none=False)
            result = u.Infra.organize_imports(rope.rope_project, resource, apply=False)

        tm.ok(result)
        tm.that(result.value, eq=False)

    def test_organize_imports_fails_on_unexpected_result_type(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unexpected rope organizer returns must not masquerade as no-op success."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            ("from __future__ import annotations\n\nimport os\nimport pathlib\n"),
            encoding="utf-8",
        )

        class _UnexpectedOrganizer:
            def organize_imports(self, _resource: object) -> object:
                return object()

        monkeypatch.setattr(
            u.Infra,
            "import_organizer",
            staticmethod(lambda _rope_project: _UnexpectedOrganizer()),
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            tm.that(resource, none=False)
            result = u.Infra.organize_imports(rope.rope_project, resource, apply=False)

        tm.fail(result)
        tm.that(result.error, none=False)
        tm.that(result.error, has="unexpected rope organize_imports result type")
