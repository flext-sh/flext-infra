"""Unit tests for namespace enforcer detection and auto-fix behaviors."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.detectors.loose_object_detector import FlextInfraLooseObjectDetector
from flext_infra.detectors.manual_protocol_detector import (
    FlextInfraManualProtocolDetector,
)
from flext_infra.refactor.namespace_enforcer import FlextInfraNamespaceEnforcer
from tests import m

from tests import t



class TestsFlextInfraRefactorInfraRefactorNamespaceEnforcer:
    """Behavior contract for test_infra_refactor_namespace_enforcer."""

    def test_namespace_enforcer_creates_missing_facades_and_rewrites_imports(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (pkg / "service.py").write_text(
            "from flext_core import c, m, r, p, t, u, p\nfrom flext_infra import c, m, t, u, p\n\nVALUE = 1",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=True
        )

        tm.that(report.total_facades_missing, eq=0)
        tm.that(report.total_import_violations, eq=0)
        tm.that((pkg / "constants.py").exists(), eq=True)
        tm.that((pkg / "typings.py").exists(), eq=True)
        tm.that((pkg / "protocols.py").exists(), eq=True)
        tm.that((pkg / "models.py").exists(), eq=True)
        tm.that((pkg / "utilities.py").exists(), eq=True)

        service_source = (pkg / "service.py").read_text(encoding="utf-8")
        tm.that(service_source, has="from __future__ import annotations")
        tm.that(service_source, has="VALUE = 1")
        tm.that(service_source, lacks="from flext_core import c, m, r, p, t, u, p")
        tm.that(service_source, lacks="from flext_infra import c, m, t, u, p")
        tm.that(service_source, lacks="from sample_pkg import")

    def test_namespace_enforcer_detects_manual_typings_and_compat_aliases(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\nfrom typing import TypeAlias\n\nPayloadMap: TypeAlias = dict[str, str]\nLegacyResult = ModernResult",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_manual_typing_violations, gt=0)
        tm.that(report.total_compatibility_alias_violations, gt=0)

    def test_namespace_enforcer_splits_foreign_canonical_aliases(
        self, tmp_path: Path
    ) -> None:
        """ENFORCE-080 has a distinct report field from legacy aliases."""
        workspace = tmp_path / "workspace"
        project = workspace / "flext-infra"
        pkg = project / "src" / "flext_infra"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='flext-infra'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        models_dir = pkg / "_models"
        typings_dir = pkg / "_typings"
        models_dir.mkdir()
        typings_dir.mkdir()
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import c, r, t\n\n"
            "VALUE = c.MAX_SIZE\n"
            "RESULT: r.Result[str] | None = None\n"
            "NAMES: t.StrSequence = ()\n",
            encoding="utf-8",
        )
        _ = (pkg / "submodule_consumer.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core.typings import (\n"
            "    FlextTypes as t,\n"
            ")\n\n"
            "NAMES: t.StrSequence = ()\n",
            encoding="utf-8",
        )
        _ = (models_dir / "base.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import m\n\n"
            "class DemoModel(m.Base):\n"
            "    value: str\n",
            encoding="utf-8",
        )
        _ = (typings_dir / "base.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import m, t\n\n"
            "Payload = t.StrMapping\n"
            "ModelBase = m.Base\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        project_report = report.projects[0]
        tm.that(report.total_compatibility_alias_violations, eq=0)
        tm.that(report.total_foreign_canonical_alias_violations, gt=0)
        tm.that(project_report.compatibility_alias_violations, empty=True)
        tm.that(project_report.foreign_canonical_alias_violations, empty=False)
        violation_paths = {
            Path(violation.file).relative_to(pkg).as_posix()
            for violation in project_report.foreign_canonical_alias_violations
        }
        tm.that(violation_paths, has="submodule_consumer.py")
        tm.that(violation_paths, lacks="_models/base.py")
        tm.that(violation_paths, lacks="_typings/base.py")
        rendered = FlextInfraNamespaceEnforcer.render_text(report)
        tm.that(rendered, has="Foreign canonical alias violations:")

    def test_namespace_enforcer_detects_manual_protocol_outside_canonical_files(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\nfrom typing import Protocol\n\nclass ServiceContract(Protocol):\n    def run(self) -> str:\n        ...",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_manual_protocol_violations, eq=1)
        project_report = report.projects[0]
        violations = project_report.manual_protocol_violations
        tm.that(len(violations), eq=1)
        violation = violations[0]
        tm.that(violation.name, eq="ServiceContract")
        rendered = FlextInfraNamespaceEnforcer.render_text(report)
        tm.that(rendered, has="Manual protocol violations: 1")

    def test_namespace_enforcer_detects_internal_private_imports(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\nfrom flext_core import FlextUtilitiesGuards\nfrom sample_pkg.protocols import _InternalContract\n\n_ = FlextUtilitiesGuards\n_ = _InternalContract",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_internal_import_violations, gt=0)
        rendered = FlextInfraNamespaceEnforcer.render_text(report)
        tm.that(rendered, has="Internal import violations:")

    def test_manual_protocol_detector_sanctions_private_protocols_directory(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        proto_dir = tmp_path / "_protocols"
        proto_dir.mkdir(parents=True)
        target = proto_dir / "base.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class BaseContract(Protocol):\n"
            "    def run(self) -> str: ...\n",
            encoding="utf-8",
        )

        violations = FlextInfraManualProtocolDetector.detect_file(
            m.Infra.DetectorContext(file_path=target, rope_project=rope_project)
        )

        tm.that(violations, empty=True)

    def test_manual_protocol_detector_sanctions_canonical_protocols_file(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "protocols.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class BaseContract(Protocol):\n"
            "    def run(self) -> str: ...\n",
            encoding="utf-8",
        )

        violations = FlextInfraManualProtocolDetector.detect_file(
            m.Infra.DetectorContext(file_path=target, rope_project=rope_project)
        )

        tm.that(violations, empty=True)

    def test_manual_protocol_detector_flags_protocol_in_service_module(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "service.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class ServiceContract(Protocol):\n"
            "    def run(self) -> str: ...\n",
            encoding="utf-8",
        )

        violations = FlextInfraManualProtocolDetector.detect_file(
            m.Infra.DetectorContext(file_path=target, rope_project=rope_project)
        )

        tm.that(len(violations), eq=1)
        tm.that(violations[0].name, eq="ServiceContract")

    def test_namespace_enforcer_exempts_same_package_facade_assembly_imports(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        parts_pkg = pkg / "_parts"
        nested_pkg = pkg / "nested"
        parts_pkg.mkdir(parents=True)
        nested_pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (nested_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (parts_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (parts_pkg / "impl.py").write_text(
            "from __future__ import annotations\n\n"
            "class _PartsMixin:\n"
            "    pass\n\n"
            "class PartsImpl(_PartsMixin):\n"
            "    pass\n",
            encoding="utf-8",
        )
        _ = (pkg / "service.py").write_text(
            "from __future__ import annotations\n"
            "from sample_pkg._parts.impl import PartsImpl, _PartsMixin\n\n"
            "class Service(PartsImpl, _PartsMixin):\n"
            "    pass\n",
            encoding="utf-8",
        )
        _ = (nested_pkg / "_base.py").write_text(
            "from __future__ import annotations\n\nclass _NestedMixin:\n    pass\n",
            encoding="utf-8",
        )
        _ = (nested_pkg / "impl.py").write_text(
            "from __future__ import annotations\n"
            "from ._base import _NestedMixin\n\n"
            "class NestedService(_NestedMixin):\n"
            "    pass\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_internal_import_violations, eq=0)

    def test_namespace_enforcer_flags_cross_package_private_import_from_tests_tree(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        parts_pkg = pkg / "_parts"
        tests_dir = project / "tests"
        parts_pkg.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\n"
            "name='sample'\n"
            "[tool.hatch.build.targets.wheel]\n"
            "packages=['src/sample_pkg']\n",
            encoding="utf-8",
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (parts_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (parts_pkg / "impl.py").write_text(
            "from __future__ import annotations\n\nclass PartsImpl:\n    pass\n",
            encoding="utf-8",
        )
        _ = (tests_dir / "helper.py").write_text(
            "from __future__ import annotations\n"
            "from sample_pkg._parts.impl import PartsImpl\n\n"
            "_ = PartsImpl\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_internal_import_violations, eq=1)
        violation = report.projects[0].internal_import_violations[0]
        tm.that(violation.file.replace("\\", "/"), has="tests/helper.py")

    def test_namespace_enforcer_allows_pytest_whitebox_project_private_import(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        parts_pkg = pkg / "_parts"
        tests_dir = project / "tests"
        parts_pkg.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\n"
            "name='sample'\n"
            "[tool.hatch.build.targets.wheel]\n"
            "packages=['src/sample_pkg']\n",
            encoding="utf-8",
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (parts_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (parts_pkg / "impl.py").write_text(
            "from __future__ import annotations\n\nclass PartsImpl:\n    pass\n",
            encoding="utf-8",
        )
        _ = (tests_dir / "test_parts.py").write_text(
            "from __future__ import annotations\n"
            "from sample_pkg._parts.impl import PartsImpl\n\n"
            "def test_parts_impl() -> None:\n"
            "    assert PartsImpl() is not None\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_internal_import_violations, eq=0)

    def test_namespace_enforce_does_not_expose_in_place_diff(self) -> None:
        tm.that(m.Infra.RefactorNamespaceEnforceInput.model_fields, lacks="diff")

    def test_loose_object_detector_detects_module_logger_assignment(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from flext_core import FlextLogger\n\n"
            "logger = u.fetch_logger(__name__)\n\n"
            "class DemoTarget:\n"
            "    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that(len(violations), eq=1)
        tm.that(violations[0].kind, eq="logger")
        tm.that(violations[0].name, eq="logger")

    def test_loose_object_detector_flags_private_function_as_loose(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n"
            "\n"
            "def _helper() -> None:\n"
            "    return None\n"
            "\n"
            "class DemoTarget:\n"
            "    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        function_violations = [v for v in violations if v.kind == "function"]
        tm.that(len(function_violations), eq=1)
        tm.that(function_violations[0].name, eq="_helper")

    def test_loose_object_detector_enforces_single_class_pattern(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n\nVALUE = 1\n", encoding="utf-8"
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        single_class = [v for v in violations if v.kind == "single_class"]
        tm.that(len(single_class), eq=1)

    def test_loose_object_detector_skips_private_base_module_mro_contract(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "_base.py"
        target.write_text(
            "from __future__ import annotations\n\n"
            "class _DemoTyping:\n"
            "    pass\n\n"
            "class _DemoBase:\n"
            "    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that([v for v in violations if v.kind == "single_class"], empty=True)

    def test_loose_object_detector_skips_pytest_module_functions(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        target = tests_dir / "test_sample.py"
        target.write_text(
            "from __future__ import annotations\n\n"
            "import pytest\n\n"
            "@pytest.fixture\n"
            "def sample_value() -> int:\n"
            "    return 1\n\n"
            "def test_sample_value(sample_value: int) -> None:\n"
            "    assert sample_value == 1\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that(violations, empty=True)

    def test_loose_object_detector_skips_typings_module_exception(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "typings.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from typing import TypeVar\n"
            "\n"
            "TValue = TypeVar('TValue')\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that(violations, empty=True)

    def test_loose_object_detector_skips_canonical_alias_module_exception(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "cli.py"
        target.write_text(
            "from __future__ import annotations\n"
            "\n"
            "def _adapter() -> None:\n"
            "    return None\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that(violations, empty=True)

    def test_loose_object_detector_flags_classvar_outside_constants_class(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from pathlib import Path\n"
            "from typing import ClassVar\n\n"
            "class ServiceConfig:\n"
            "    HOME: ClassVar[Path] = Path.home()\n"
            "    AI_HUB: ClassVar[Path] = Path('.ai-hub')\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        classvar_violations = [v for v in violations if v.kind == "classvar"]
        tm.that(len(classvar_violations), eq=2)
        tm.that({v.name for v in classvar_violations}, eq={"HOME", "AI_HUB"})
        tm.that(classvar_violations[0].suggestion, has="Constants")

    def test_loose_object_detector_skips_classvar_in_constants_class(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from pathlib import Path\n"
            "from typing import ClassVar\n\n"
            "class SampleConstants:\n"
            "    HOME: ClassVar[Path] = Path.home()\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that([v for v in violations if v.kind == "classvar"], empty=True)

    def test_loose_object_detector_skips_classvar_in_constants_module(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "_constants" / "service.py"
        target.parent.mkdir(parents=True)
        target.write_text(
            "from __future__ import annotations\n"
            "from pathlib import Path\n"
            "from typing import ClassVar\n\n"
            "class ServiceConfig:\n"
            "    HOME: ClassVar[Path] = Path.home()\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that([v for v in violations if v.kind == "classvar"], empty=True)

    def test_loose_object_detector_flags_typing_classvar(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n"
            "import typing\n\n"
            "class ServiceConfig:\n"
            "    HOME: typing.ClassVar[str] = 'home'\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        classvar_violations = [v for v in violations if v.kind == "classvar"]
        tm.that(len(classvar_violations), eq=1)
        tm.that(classvar_violations[0].name, eq="HOME")

    def test_loose_object_detector_skips_private_classvar(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "target.py"
        target.write_text(
            "from __future__ import annotations\n"
            "from typing import ClassVar\n\n"
            "class ServiceConfig:\n"
            "    _INTERNAL: ClassVar[str] = 'secret'\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that([v for v in violations if v.kind == "classvar"], empty=True)

    def test_loose_object_detector_skips_init_module_exception(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "__init__.py"
        target.write_text(
            "from __future__ import annotations\n\n_LAZY_IMPORTS = {}\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that(violations, empty=True)

    def test_loose_object_detector_skips_canonical_class_alias_in_single_class_count(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = tmp_path / "protocols.py"
        target.write_text(
            "from __future__ import annotations\n"
            "\n"
            "class SampleProtocols:\n"
            "    pass\n"
            "\n"
            "p = SampleProtocols\n",
            encoding="utf-8",
        )

        violations = FlextInfraLooseObjectDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target, project_name="sample-proj", rope_project=rope_project
            )
        )

        tm.that(violations, empty=True)

    def test_namespace_enforcer_apply_moves_manual_protocol_to_protocols_file(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\nfrom typing import Protocol\n\nclass ServiceContract(Protocol):\n    def run(self) -> str:\n        ...\n\nclass ServiceImpl:\n    def run(self) -> str:\n        return 'ok'",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=True
        )

        tm.that(report.total_manual_protocol_violations, eq=0)
        protocols_file = pkg / "protocols.py"
        tm.that(protocols_file.exists(), eq=True)

        protocols_source = protocols_file.read_text(encoding="utf-8")
        tm.that(protocols_source, has="class ServiceContract(Protocol):")
        tm.that(protocols_source, has="from __future__ import annotations")
        tm.that(protocols_source, has="from typing import Protocol")

    def test_namespace_enforcer_apply_keeps_autofixes_when_other_violations_remain(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\n"
            "import logging\n"
            "from typing import Protocol\n\n"
            "logger = logging.getLogger(__name__)\n\n"
            "class ServiceContract(Protocol):\n"
            "    def run(self) -> str:\n"
            "        ...\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=True
        )

        tm.that(report.has_violations, eq=True)
        tm.that(report.total_manual_protocol_violations, eq=0)
        tm.that(report.total_loose_objects, gt=0)
        tm.that((pkg / "protocols.py").exists(), eq=True)
        tm.that(
            (pkg / "protocols.py").read_text(encoding="utf-8"),
            has="class ServiceContract(Protocol):",
        )
        tm.that(
            service_file.read_text(encoding="utf-8"),
            lacks="class ServiceContract(Protocol):",
        )

    def test_namespace_enforcer_detects_cyclic_imports_in_tests_directory(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        test_pkg = project / "tests"
        pkg.mkdir(parents=True)
        test_pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (test_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (test_pkg / "a.py").write_text(
            "from __future__ import annotations\nfrom tests.b import value_b\nvalue_a = value_b\n",
            encoding="utf-8",
        )
        _ = (test_pkg / "b.py").write_text(
            "from __future__ import annotations\nfrom tests.a import value_a\nvalue_b = value_a\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_cyclic_imports, gte=1)

    def test_namespace_enforcer_skips_mro_completeness_for_tests_typings(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        test_pkg = project / "tests"
        pkg.mkdir(parents=True)
        test_pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (pkg / "typings.py").write_text(
            "from __future__ import annotations\n\n"
            "class SampleTypes:\n"
            "    pass\n\n"
            "t = SampleTypes\n",
            encoding="utf-8",
        )
        _ = (test_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (test_pkg / "typings.py").write_text(
            "from __future__ import annotations\n\n"
            "class TestsSampleTypes:\n"
            "    pass\n\n"
            "t = TestsSampleTypes\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_parse_failures, eq=0)

    def test_namespace_enforcer_detects_missing_runtime_alias_outside_src(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        examples_dir = project / "examples"
        pkg.mkdir(parents=True)
        examples_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (examples_dir / "constants.py").write_text(
            "from __future__ import annotations\n\nclass DemoConstants:\n    pass\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_runtime_alias_violations, gt=0)

    def test_namespace_enforcer_respects_tool_flext_namespace_scan_dirs(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        examples_dir = project / "examples"
        pkg.mkdir(parents=True)
        examples_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n\n[tool.flext.namespace]\nscan_dirs = ['src']\n",
            encoding="utf-8",
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (examples_dir / "constants.py").write_text(
            "from __future__ import annotations\n\nclass DemoConstants:\n    pass\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_runtime_alias_violations, eq=0)

    def test_namespace_enforcer_skips_dynamic_dirs_by_default(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        docs_dir = project / "docs"
        pkg.mkdir(parents=True)
        docs_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (docs_dir / "contracts.py").write_text(
            "from __future__ import annotations\nfrom typing import Protocol\n\nclass HiddenContract(Protocol):\n    def run(self) -> str:\n        ...\n",
            encoding="utf-8",
        )

        report = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(
            apply=False
        )

        tm.that(report.total_manual_protocol_violations, eq=0)

    def test_namespace_enforcer_apply_keeps_script_shebang_when_adding_future(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        scripts_dir = project / "scripts"
        pkg.mkdir(parents=True)
        scripts_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        script_file = scripts_dir / "run.py"
        _ = script_file.write_text(
            "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nprint('ok')\n",
            encoding="utf-8",
        )

        _ = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(apply=True)

        rewritten_lines = script_file.read_text(encoding="utf-8").splitlines()
        tm.that(rewritten_lines[0], eq="#!/usr/bin/env python3")
        tm.that(rewritten_lines[1], eq="# -*- coding: utf-8 -*-")
        tm.that(rewritten_lines, has="from __future__ import annotations")

    def test_namespace_enforcer_apply_inserts_future_after_single_line_module_docstring(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        tests_dir = project / "tests"
        pkg.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        target_file = tests_dir / "base_improved.py"
        _ = target_file.write_text(
            '"""Improved test base with high automation and real functionality."""\n'
            "from pathlib import Path\n"
            "\n"
            "class DemoMigrationTestBase:\n"
            '    """Highly automated test base with real functionality patterns."""\n'
            "    temp_dir: Path\n",
            encoding="utf-8",
        )

        _ = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(apply=True)

        rewritten_lines = target_file.read_text(encoding="utf-8").splitlines()
        tm.that(rewritten_lines[0].startswith('"""Improved test base'), eq=True)
        tm.that(rewritten_lines[2], eq="from __future__ import annotations")

    def test_namespace_enforcer_does_not_rewrite_indented_import_aliases(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        service_file = pkg / "service.py"
        _ = service_file.write_text(
            "from __future__ import annotations\n\n"
            "def runner() -> None:\n"
            "    from flext_core import System\n"
            "    _ = System\n",
            encoding="utf-8",
        )

        _ = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(apply=True)

        service_source = service_file.read_text(encoding="utf-8")
        tm.that(service_source, has="    from flext_core import System")

    def test_namespace_enforcer_does_not_rewrite_multiline_import_alias_blocks(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-proj"
        pkg = project / "src" / "sample_pkg"
        pkg.mkdir(parents=True)
        _ = (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (pkg / "__init__.py").write_text("", encoding="utf-8")
        module_file = pkg / "constants.py"
        _ = module_file.write_text(
            "from __future__ import annotations\n"
            "from flext_infra import (\n"
            "    FlextInfraConstantsCore,\n"
            "    FlextInfraConstantsSharedInfra,\n"
            ")\n"
            "\n"
            "class DemoConstants:\n"
            "    pass\n",
            encoding="utf-8",
        )

        _ = FlextInfraNamespaceEnforcer(workspace_root=workspace).enforce(apply=True)

        module_source = module_file.read_text(encoding="utf-8")
        tm.that(module_source, has="from flext_infra import (")
        tm.that(module_source, has="FlextInfraConstantsCore")
