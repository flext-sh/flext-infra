"""Focused behavior tests for Rope import utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime
from flext_infra.workspace.rope import FlextInfraRopeWorkspace
from tests import u

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
            result = FlextInfraUtilitiesRopeImports.normalize_imports(
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

    def test_ensure_canonical_alias_imports_restores_string_referenced_alias(
        self, tmp_path: Path
    ) -> None:
        """String-referenced runtime aliases removed by Ruff must be restored."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                'def keep(value: "c.Infra.PathLike") -> str:\n'
                "    return str(value)\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            result = FlextInfraUtilitiesRopeImports._ensure_canonical_alias_imports(
                rope.rope_project, {module_path.resolve(): [("flext_core", ("c",))]}
            )

        updated = module_path.read_text(encoding="utf-8")
        tm.ok(result)
        tm.that(result.value, eq=True)
        tm.that(updated, has="from flext_core import c")
        tm.that(updated, has="c.Infra.PathLike")

    def test_ensure_canonical_alias_imports_ignores_unreferenced_alias(
        self, tmp_path: Path
    ) -> None:
        """Unreferenced runtime aliases must not be restored after Ruff cleanup."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "def keep() -> str:\n"
                "    return 'ok'\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            result = FlextInfraUtilitiesRopeImports._ensure_canonical_alias_imports(
                rope.rope_project, {module_path.resolve(): [("flext_core", ("c",))]}
            )

        updated = module_path.read_text(encoding="utf-8")
        tm.ok(result)
        tm.that(result.value, eq=False)
        tm.that(updated, lacks="from flext_core import c")
        tm.that(updated, has="return 'ok'")

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
            FlextInfraUtilitiesRopeRuntime,
            "import_organizer",
            staticmethod(lambda _rope_project: _NoChangesOrganizer()),
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            tm.that(resource, none=False)
            result = FlextInfraUtilitiesRopeImports.organize_imports(
                rope.rope_project, resource, apply=False
            )

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
            FlextInfraUtilitiesRopeRuntime,
            "import_organizer",
            staticmethod(lambda _rope_project: _UnexpectedOrganizer()),
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            tm.that(resource, none=False)
            result = FlextInfraUtilitiesRopeImports.organize_imports(
                rope.rope_project, resource, apply=False
            )

        tm.fail(result)
        tm.that(result.error, none=False)
        tm.that(result.error, has="unexpected rope organize_imports result type")

    def test_merge_aliases_raises_on_target_import_mismatch(
        self, tmp_path: Path
    ) -> None:
        """Target import mismatches must raise instead of silently dropping moved aliases."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-demo", package_name="flext_demo"
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                "from sample_pkg.source import moved\n"
            ),
            encoding="utf-8",
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            tm.that(resource, none=False)
            module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
                rope.rope_project, resource
            )
            tm.that(module_imports, none=False)
            import_statements = FlextInfraUtilitiesRopeImports.import_statements(
                module_imports
            )
            source_import = next(
                statement
                for statement in import_statements
                if FlextInfraUtilitiesRopeImports.import_statement_module_name(
                    statement
                )
                == "sample_pkg.source"
            )

            with pytest.raises(
                RuntimeError,
                match=r"rope target import mismatch for sample_pkg\.target",
            ):
                FlextInfraUtilitiesRopeImports._merge_aliases_into_target(
                    module_imports,
                    target_import_stmt=source_import,
                    target_module="sample_pkg.target",
                    moved_aliases={"moved"},
                )
