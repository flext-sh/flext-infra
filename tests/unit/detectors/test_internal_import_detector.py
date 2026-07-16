"""Tests for internal import detector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import m, u
from flext_infra.detectors.internal_import_detector import (
    FlextInfraInternalImportDetector,
)

from pathlib import Path



class TestsFlextInfraInternalImportDetector:
    """Behavior contract for internal import detection."""

    def test_allows_public_dunder_version_module_import(self, tmp_path: Path) -> None:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        version_file = package_dir / "__version__.py"
        _ = version_file.write_text(
            "from __future__ import annotations\n"
            "from flext_core.__version__ import FlextVersion\n\n"
            "class DemoProjectVersion(FlextVersion):\n"
            "    pass\n",
            encoding="utf-8",
        )

        parse_failures: list[p.Infra.ParseFailureViolation] = []
        with u.Infra.open_project(project) as rope_project:
            violations = FlextInfraInternalImportDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=version_file,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_root=project,
                )
            )

        tm.that(parse_failures, eq=[])
        tm.that(violations, eq=[])

    def test_allows_private_local_alias_for_public_external_symbol(
        self, tmp_path: Path
    ) -> None:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        constants_file = package_dir / "constants.py"
        _ = constants_file.write_text(
            "from __future__ import annotations\n"
            "from pathlib import Path as _Path\n\n"
            "class DemoProjectConstants:\n"
            "    ROOT = _Path('.')\n",
            encoding="utf-8",
        )

        parse_failures: list[p.Infra.ParseFailureViolation] = []
        with u.Infra.open_project(project) as rope_project:
            violations = FlextInfraInternalImportDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=constants_file,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_root=project,
                )
            )

        tm.that(parse_failures, eq=[])
        tm.that(violations, eq=[])
