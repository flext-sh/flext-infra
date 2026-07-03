"""Focused behavior tests for Rope import utilities."""

from __future__ import annotations

from pathlib import Path

import pytest
import rope.refactor.importutils as rope_importutils

from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra.workspace.rope import FlextInfraRopeWorkspace
from flext_infra.tests.utilities import u


class TestsFlextInfraRopeImports:
    """Validate fail-fast behavior for Rope import utility wrappers."""

    def test_normalize_imports_removes_orphaned_imports_and_formats(
        self,
        tmp_path: Path,
    ) -> None:
        """Centralized import cleanup should leave one lint-clean module."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
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

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            result = FlextInfraUtilitiesRopeImports.normalize_imports(
                rope.rope_project,
                file_paths=(module_path,),
            )

        assert result.success
        assert module_path.read_text(encoding="utf-8") == (
            "from __future__ import annotations\n\n"
            "import os\n\n"
            "\n"
            "def keep() -> str:\n"
            "    return os.getcwd()\n"
        )

    def test_organize_imports_treats_none_as_noop(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Rope returning ``None`` must be treated as a clean no-op."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            ("from __future__ import annotations\n\nimport os\nimport pathlib\n"),
            encoding="utf-8",
        )

        def _no_changes(
            _self: rope_importutils.ImportOrganizer,
            _resource: object,
        ) -> None:
            return None

        monkeypatch.setattr(
            rope_importutils.ImportOrganizer,
            "organize_imports",
            _no_changes,
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            assert resource is not None
            result = FlextInfraUtilitiesRopeImports.organize_imports(
                rope.rope_project,
                resource,
                apply=False,
            )

        assert result.success
        assert result.value is False

    def test_organize_imports_fails_on_unexpected_result_type(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unexpected rope organizer returns must not masquerade as no-op success."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "service.py"
        module_path.write_text(
            ("from __future__ import annotations\n\nimport os\nimport pathlib\n"),
            encoding="utf-8",
        )

        def _unexpected_result(
            _self: rope_importutils.ImportOrganizer,
            _resource: object,
        ) -> object:
            return object()

        monkeypatch.setattr(
            rope_importutils.ImportOrganizer,
            "organize_imports",
            _unexpected_result,
        )

        with FlextInfraRopeWorkspace.open_workspace(workspace_root) as rope:
            resource = rope.resource(module_path)
            assert resource is not None
            result = FlextInfraUtilitiesRopeImports.organize_imports(
                rope.rope_project,
                resource,
                apply=False,
            )

        assert result.failure
        assert result.error is not None
        assert "unexpected rope organize_imports result type" in result.error

    def test_merge_aliases_raises_on_target_import_mismatch(
        self,
        tmp_path: Path,
    ) -> None:
        """Target import mismatches must raise instead of silently dropping moved aliases."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
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
            assert resource is not None
            module_imports = FlextInfraUtilitiesRopeCore.get_module_imports(
                rope.rope_project,
                resource,
            )
            assert module_imports is not None
            import_statements = FlextInfraUtilitiesRopeImports.import_statements(
                module_imports,
            )
            source_import = next(
                statement
                for statement in import_statements
                if FlextInfraUtilitiesRopeImports.import_statement_module_name(
                    statement,
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
