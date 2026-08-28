"""Behavior contract for deferred-self-reference and recursive-model detection.

Both defects share one root cause: a nested model that cannot name what it
depends on while its own class body executes. The canonical repair is
diamond-FLEXT composition, so the detector must fire on the deferral and stay
silent once the model is composed through inherited namespaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, u
from flext_infra.detectors.deferred_self_reference_detector import (
    FlextInfraDeferredSelfReferenceDetector,
)
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

_DEFERRED = "DEFERRED_SELF_REFERENCE"
_RECURSIVE = "RECURSIVE_MODEL"


class TestsFlextInfraDeferredSelfReferenceDetector:
    """Behavior contract for deferred-self-reference detection."""

    @staticmethod
    def _codes(tmp_path: Path, source: str) -> tuple[str, ...]:
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        module = package_dir / "subject.py"
        _ = module.write_text(source, encoding="utf-8")
        with u.Infra.open_project(project) as rope_project:
            issues = FlextInfraDeferredSelfReferenceDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=module, project_root=project, rope_project=rope_project
                )
            )
        return tuple(issue.code for issue in issues)

    def test_lambda_factory_reaching_the_enclosing_class_is_reported(
        self, tmp_path: Path
    ) -> None:
        """A default_factory deferring the outer class name is the core defect."""
        source = (
            "class Outer:\n"
            "    class Leaf:\n"
            "        pass\n"
            "    class Holder:\n"
            "        leaf: Outer.Leaf = Field(default_factory=lambda: Outer.Leaf())\n"
        )
        tm.that(self._codes(tmp_path, source), eq=(_DEFERRED,))

    def test_diamond_flext_composition_is_accepted(self, tmp_path: Path) -> None:
        """The canonical repair resolves the model eagerly, so it must be clean."""
        source = (
            "class Base:\n"
            "    class Leaf:\n"
            "        pass\n"
            "class Outer(Base):\n"
            "    class Holder:\n"
            "        leaf: Base.Leaf = Field(default_factory=Base.Leaf)\n"
        )
        tm.that(self._codes(tmp_path, source), eq=())

    def test_value_factories_are_not_deferred_references(self, tmp_path: Path) -> None:
        """A lambda producing an immutable default names no enclosing class."""
        source = (
            "class Outer:\n"
            "    class Holder:\n"
            "        mapping: Map = Field(default_factory=lambda: MappingProxyType({}))\n"
            "        missing: object = Field(default_factory=lambda: None)\n"
        )
        tm.that(self._codes(tmp_path, source), eq=())

    def test_self_annotated_field_is_reported_as_recursive(
        self, tmp_path: Path
    ) -> None:
        """A field typed as its own owner cannot be instantiated."""
        source = "class Node:\n    child: Node | None = None\n"
        tm.that(self._codes(tmp_path, source), eq=(_RECURSIVE,))

    def test_classvar_singleton_slot_is_not_recursive(self, tmp_path: Path) -> None:
        """A ClassVar slot is never instantiated as a field."""
        source = "class Config:\n    _instance: ClassVar[Config | None] = None\n"
        tm.that(self._codes(tmp_path, source), eq=())

    def test_type_adapter_table_is_not_recursive(self, tmp_path: Path) -> None:
        """A TypeAdapter table types a converter, not an instantiated field."""
        source = (
            "class Types:\n"
            "    ADAPTER: m.TypeAdapter[t.SequenceOf[Types.Payload]] = m.TypeAdapter(\n"
            "        t.SequenceOf[Payload]\n"
            "    )\n"
        )
        tm.that(self._codes(tmp_path, source), eq=())

    def test_annotated_local_inside_a_method_is_not_a_field(
        self, tmp_path: Path
    ) -> None:
        """A method body runs after the class is bound, so neither defect applies."""
        source = (
            "class Service:\n"
            "    def run(self) -> object:\n"
            "        resolved: Service.Inner = build()\n"
            "        return resolved\n"
        )
        tm.that(self._codes(tmp_path, source), eq=())

    def test_report_names_the_flext_repair(self, tmp_path: Path) -> None:
        """The finding must tell the author how to fix it, not just that it failed."""
        project = tmp_path / "demo-project"
        package_dir = project / "src" / "demo_project"
        package_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='demo-project'\n", encoding="utf-8"
        )
        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")
        module = package_dir / "subject.py"
        _ = module.write_text(
            "class Outer:\n"
            "    class Leaf:\n"
            "        pass\n"
            "    class Holder:\n"
            "        leaf: Outer.Leaf = Field(default_factory=lambda: Outer.Leaf())\n",
            encoding="utf-8",
        )
        with u.Infra.open_project(project) as rope_project:
            issues = FlextInfraDeferredSelfReferenceDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=module, project_root=project, rope_project=rope_project
                )
            )
        tm.that(len(issues), eq=1)
        tm.that(issues[0].message, has="FLEXT")
        tm.that(issues[0].line, eq=5)
