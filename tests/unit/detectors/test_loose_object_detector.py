"""Tests for loose object detector."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import m, u
from flext_infra.detectors.loose_object_detector import FlextInfraLooseObjectDetector

from pathlib import Path



class TestsFlextInfraLooseObjectDetector:
    """Behavior contract for loose object detection."""

    @staticmethod
    def _project(tmp_path: Path) -> tuple[Path, Path]:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        return project, package_dir

    @staticmethod
    def _violations(
        *, project: Path, file_path: Path
    ) -> tuple[m.Infra.LooseObjectViolation, ...]:
        parse_failures: list[m.Infra.ParseFailureViolation] = []
        with u.Infra.open_project(project) as rope_project:
            violations = FlextInfraLooseObjectDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=file_path,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_root=project,
                    project_name="demo-project",
                )
            )
        tm.that(parse_failures, eq=[])
        return tuple(violations)

    def test_skips_project_examples_surface(self, tmp_path: Path) -> None:
        project, _package_dir = self._project(tmp_path)
        examples_dir = project / "examples"
        examples_dir.mkdir()
        example_file = examples_dir / "demo.py"
        _ = example_file.write_text(
            "from __future__ import annotations\n\ndef main() -> None:\n    pass\n",
            encoding="utf-8",
        )

        violations = self._violations(project=project, file_path=example_file)

        tm.that(violations, eq=())

    def test_skips_generated_lazy_registry(self, tmp_path: Path) -> None:
        project, package_dir = self._project(tmp_path)
        exports_file = package_dir / "_exports.py"
        _ = exports_file.write_text(
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            "from __future__ import annotations\n\n"
            "DEMO_LAZY_IMPORTS = {}\n"
            "__all__ = ['DEMO_LAZY_IMPORTS']\n",
            encoding="utf-8",
        )

        violations = self._violations(project=project, file_path=exports_file)

        tm.that(violations, eq=())

    def test_allows_canonical_facade_alias_assignment(self, tmp_path: Path) -> None:
        project, package_dir = self._project(tmp_path)
        models_file = package_dir / "models.py"
        _ = models_file.write_text(
            "from __future__ import annotations\n\n"
            "class DemoProjectModels:\n"
            "    pass\n\n"
            "m: type[DemoProjectModels] = DemoProjectModels\n"
            "__all__ = ['DemoProjectModels', 'm']\n",
            encoding="utf-8",
        )

        violations = self._violations(project=project, file_path=models_file)

        tm.that(violations, eq=())

    def test_skips_empty_runtime_module(self, tmp_path: Path) -> None:
        project, package_dir = self._project(tmp_path)
        module_file = package_dir / "_utilities" / "implementations.py"
        module_file.parent.mkdir()
        _ = module_file.write_text(
            '"""Implementation registry reserved for generated entries."""\n\n'
            "from __future__ import annotations\n",
            encoding="utf-8",
        )

        violations = self._violations(project=project, file_path=module_file)

        tm.that(violations, eq=())
