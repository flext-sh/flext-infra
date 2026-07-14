"""Characterization tests pinning loose-object positive detections.

These lock the current behavior of every ``LooseObjectViolation.kind`` the
detector emits BEFORE the rope-structure boundary conversion, so the migration
is proven to preserve domain behavior (flext-law: no domain regression).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import m, u
from flext_infra.detectors.loose_object_detector import FlextInfraLooseObjectDetector

from pathlib import Path



class TestsFlextInfraLooseObjectCharacterization:
    """Pin every positive loose-object detection kind."""

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

    @classmethod
    def _kinds_for(cls, tmp_path: Path, source: str) -> set[tuple[str, str]]:
        project, package_dir = cls._project(tmp_path)
        module_file = package_dir / "widget.py"
        _ = module_file.write_text(source, encoding="utf-8")
        parse_failures: list[m.Infra.ParseFailureViolation] = []
        with u.Infra.open_project(project) as rope_project:
            violations = FlextInfraLooseObjectDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=module_file,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_root=project,
                    project_name="demo-project",
                )
            )
        return {(v.kind, v.name) for v in violations}

    def test_flags_loose_final_constant(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path, "from __future__ import annotations\n\nTIMEOUT = 30\n"
        )

        tm.that(("constant", "TIMEOUT") in kinds, eq=True)

    def test_flags_loose_collection_assignment(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path,
            "from __future__ import annotations\n\nVALUES = frozenset({1, 2})\n",
        )

        tm.that(("collection", "VALUES") in kinds, eq=True)

    def test_flags_loose_typevar(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path,
            "from __future__ import annotations\n"
            "from typing import TypeVar\n\n"
            "T = TypeVar('T')\n",
        )

        tm.that(("typevar", "T") in kinds, eq=True)

    def test_flags_loose_type_alias(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path, "from __future__ import annotations\n\ntype Alias = int\n"
        )

        tm.that(any(kind == "typealias" for kind, _ in kinds), eq=True)

    def test_flags_loose_function(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path,
            "from __future__ import annotations\n\ndef helper() -> None:\n    pass\n",
        )

        tm.that(("function", "helper") in kinds, eq=True)

    def test_flags_loose_enum_class(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path,
            "from __future__ import annotations\n"
            "from enum import StrEnum\n\n"
            "class Widget:\n"
            "    class Color(StrEnum):\n"
            "        RED = 'red'\n",
        )

        tm.that(("enum", "Color") in kinds, eq=True)

    def test_flags_loose_classvar_constant(self, tmp_path: Path) -> None:
        kinds = self._kinds_for(
            tmp_path,
            "from __future__ import annotations\n"
            "from typing import ClassVar\n\n"
            "class Widget:\n"
            "    LIMIT: ClassVar[int] = 5\n",
        )

        tm.that(("classvar", "LIMIT") in kinds, eq=True)
