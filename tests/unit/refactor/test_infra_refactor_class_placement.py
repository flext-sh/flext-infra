from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
)
from flext_infra.fixers.rope_fixer import FlextInfraRopeFixerAdapter
from flext_infra.refactor.classvar_constant_autofix import (
    FlextInfraRefactorClassvarConstantAutofix,
)
from tests.constants import c
from tests.models import m
from tests.typings import t


class TestsFlextInfraRefactorInfraRefactorClassPlacement:
    """Behavior contract for test_infra_refactor_class_placement."""

    def test_detects_basemodel_in_non_model_file(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert len(violations) == 1
        assert violations[0].name == "PublicModel"
        assert violations[0].base_class == "BaseModel"

    def test_detects_attribute_base_class(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "from flext_core import FlextModels\n"
            "class PublicModel(FlextModels.ArbitraryTypesModel):\n"
            "    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert len(violations) == 1
        assert violations[0].name == "PublicModel"
        assert violations[0].base_class == "ArbitraryTypesModel"

    def test_skips_models_file(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "models.py"
        target.write_text(
            "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_skips_models_directory(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True)
        target = models_dir / "domain.py"
        target.write_text(
            "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_skips_private_models_directory(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        models_dir = tmp_path / "_models"
        models_dir.mkdir(parents=True)
        target = models_dir / "domain.py"
        target.write_text(
            "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_skips_sanctioned_root_namespace_files(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        for file_name in ("result.py", "lazy.py", "mixins.py"):
            target = tmp_path / file_name
            target.write_text(
                "from pydantic import BaseModel\n"
                "class PublicModel(BaseModel):\n"
                "    pass\n",
                encoding="utf-8",
            )

            violations = FlextInfraClassPlacementDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=target,
                    rope_project=rope_project,
                ),
            )

            assert violations == [], file_name

    def test_skips_settings_file(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        settings_file_name = min(c.Infra.NAMESPACE_SETTINGS_FILE_NAMES)
        target = tmp_path / settings_file_name
        target.write_text(
            "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_skips_protected_files(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        protected_file_name = min(c.Infra.NAMESPACE_PROTECTED_FILES)
        target = tmp_path / protected_file_name
        target.write_text(
            "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_skips_private_class(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "from pydantic import BaseModel\nclass _PrivateModel(BaseModel):\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_detects_multiple_models(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "from pydantic import BaseModel\n"
            "from flext_core import FlextModels\n"
            "class FirstModel(BaseModel):\n"
            "    pass\n"
            "class SecondModel(FlextModels.ArbitraryTypesModel):\n"
            "    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert len(violations) == 2
        assert {violation.name for violation in violations} == {
            "FirstModel",
            "SecondModel",
        }

    def test_non_pydantic_class_not_flagged(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "class PlainClass:\n    pass\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_detects_classvar_constant_outside_constants(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "from typing import ClassVar\n"
            "class PlainClass:\n"
            "    GROUPS: ClassVar[frozenset[str]] = frozenset({'a'})\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert len(violations) == 1
        assert violations[0].name == "GROUPS"
        assert violations[0].action == "classvar_relocation"

    def test_detects_implicit_constant_without_classvar(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        target = tmp_path / "consumer.py"
        target.write_text(
            "class PlainClass:\n    GROUPS = frozenset({'a'})\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert len(violations) == 1
        assert violations[0].name == "GROUPS"
        assert violations[0].action == "classvar_relocation"

    def test_skips_implicit_constant_inside_constants_directory(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        constants_dir = tmp_path / "_constants"
        constants_dir.mkdir(parents=True)
        target = constants_dir / "domain.py"
        target.write_text(
            "class PlainClass:\n    GROUPS = frozenset({'a'})\n",
            encoding="utf-8",
        )

        violations = FlextInfraClassPlacementDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=target,
                rope_project=rope_project,
            ),
        )

        assert violations == []

    def test_autofix_moves_implicit_constant(
        self,
        tmp_path: Path,
    ) -> None:
        """Autofix can relocate an implicit UPPER_CASE class constant."""
        pkg = tmp_path / "src" / "demo"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "service.py").write_text(
            "class DemoService:\n"
            "    GROUPS = frozenset({'a'})\n"
            "    def run(self) -> None:\n"
            "        print(DemoService.GROUPS)\n",
            encoding="utf-8",
        )
        constants_mod = pkg / "_constants.py"
        constants_mod.write_text('"""Constants."""\n', encoding="utf-8")

        result = FlextInfraRefactorClassvarConstantAutofix.apply(
            tmp_path,
            "demo.service.DemoService",
            "GROUPS",
            "demo._constants",
            dry_run=True,
        )

        touched_files = result["touched_files"]
        assert isinstance(touched_files, (list, tuple))
        assert "demo/service.py" in " ".join(str(p) for p in touched_files)
        assert "demo/_constants.py" in " ".join(str(p) for p in touched_files)
        target_text = result["target_text"]
        source_text = result["source_text"]
        assert isinstance(target_text, str) and isinstance(source_text, str)
        assert "GROUPS = frozenset({'a'})" in target_text
        assert "GROUPS = frozenset({'a'})" not in source_text

    def test_autofix_dry_run_fails_missing_constants_module(
        self,
        tmp_path: Path,
    ) -> None:
        """Dry-run fails loud when the canonical constants module is absent."""
        pkg = tmp_path / "src" / "demo"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        constants_mod = pkg / "_constants.py"
        (pkg / "service.py").write_text(
            "class DemoService:\n"
            "    GROUPS = frozenset({'a'})\n"
            "    def run(self) -> None:\n"
            "        print(DemoService.GROUPS)\n",
            encoding="utf-8",
        )

        with pytest.raises(TypeError, match=r"constants module demo\._constants"):
            FlextInfraRefactorClassvarConstantAutofix.apply(
                tmp_path,
                "demo.service.DemoService",
                "GROUPS",
                "demo._constants",
                dry_run=True,
            )

        assert not constants_mod.exists()

    def test_autofix_dry_run_resolves_project_tests_package(
        self,
        tmp_path: Path,
    ) -> None:
        """Project-local Rope roots resolve top-level tests packages."""
        tests_pkg = tmp_path / "tests" / "unit"
        tests_pkg.mkdir(parents=True)
        (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (tests_pkg / "__init__.py").write_text("", encoding="utf-8")
        (tests_pkg / "_constants.py").write_text('"""Constants."""\n', encoding="utf-8")
        (tests_pkg / "test_execution_result.py").write_text(
            "class TestsDemo:\n"
            "    TEST_VALUE = 1.5\n"
            "    def test_value(self) -> None:\n"
            "        assert self.TEST_VALUE == 1.5\n",
            encoding="utf-8",
        )

        result = FlextInfraRefactorClassvarConstantAutofix.apply(
            tmp_path,
            "tests.unit.test_execution_result.TestsDemo",
            "TEST_VALUE",
            "tests.unit._constants",
            dry_run=True,
        )

        target_text = result["target_text"]
        source_text = result["source_text"]
        assert isinstance(target_text, str) and isinstance(source_text, str)
        assert "TEST_VALUE = 1.5" in target_text
        assert "TEST_VALUE = 1.5" not in source_text

    def test_classvar_constants_module_for_tests_package(self, tmp_path: Path) -> None:
        """ENFORCE-079 maps project tests modules to sibling _constants."""
        file_path = tmp_path / "tests" / "unit" / "test_execution_result.py"

        constants_module = FlextInfraRopeFixerAdapter._constants_module_for_file(
            file_path,
            module_name="tests.unit.test_execution_result",
            project_root=tmp_path,
        )

        assert constants_module == "tests.unit._constants"

    def test_autofix_apply_inserts_import_after_module_header(
        self,
        tmp_path: Path,
    ) -> None:
        """Apply mode inserts constants import at module scope."""
        pkg = tmp_path / "src" / "demo"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "_constants.py").write_text('"""Constants."""\n', encoding="utf-8")
        service = pkg / "service.py"
        service.write_text(
            '"""Demo service."""\n\n'
            "from __future__ import annotations\n\n"
            "class DemoService:\n"
            "    VALUE = 1.5\n\n"
            "    def run(self) -> float:\n"
            '        """Return value."""\n'
            "        return self.VALUE\n",
            encoding="utf-8",
        )

        FlextInfraRefactorClassvarConstantAutofix.apply(
            tmp_path,
            "demo.service.DemoService",
            "VALUE",
            "demo._constants",
            dry_run=False,
        )

        source_text = service.read_text(encoding="utf-8")
        assert "from __future__ import annotations" in source_text
        assert "from . import _constants" in source_text
        assert source_text.index(
            "from __future__ import annotations"
        ) < source_text.index(
            "from . import _constants",
        )
        assert '"""Return value."""\nfrom . import _constants' not in source_text
        assert "return _constants.VALUE" in source_text

    def test_autofix_apply_moves_multiline_classvar_to_src_constants(
        self,
        tmp_path: Path,
    ) -> None:
        """Apply mode moves multiline constants to the package src tree."""
        pkg = tmp_path / "src" / "demo"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        constants_pkg = pkg / "_constants"
        constants_pkg.mkdir()
        (constants_pkg / "__init__.py").write_text("", encoding="utf-8")
        (constants_pkg / "factory.py").write_text(
            '"""Factory constants."""\n',
            encoding="utf-8",
        )
        (pkg / "typings.py").write_text(
            "from typing import TypeAlias\n\n"
            "JsonMapping: TypeAlias = dict[str, int | bool]\n",
            encoding="utf-8",
        )
        service = pkg / "service.py"
        service.write_text(
            '"""Demo service."""\n\n'
            "from __future__ import annotations\n\n"
            "from collections.abc import Mapping\n"
            "from typing import ClassVar\n\n"
            "from demo.typings import t\n\n"
            "class DemoService:\n"
            "    PRESETS: ClassVar[Mapping[str, t.JsonMapping]] = {\n"
            '        "development": {\n'
            '            "batch_size": 100,\n'
            '            "enabled": True,\n'
            "        },\n"
            "    }\n\n"
            "    def run(self) -> t.JsonMapping:\n"
            '        return self.PRESETS["development"]\n',
            encoding="utf-8",
        )

        FlextInfraRefactorClassvarConstantAutofix.apply(
            tmp_path,
            "demo.service.DemoService",
            "PRESETS",
            "demo._constants.factory",
            dry_run=False,
        )

        constants = pkg / "_constants" / "factory.py"
        constants_init = pkg / "_constants" / "__init__.py"
        source_text = service.read_text(encoding="utf-8")
        constants_text = constants.read_text(encoding="utf-8")
        assert constants.exists()
        assert constants_init.exists()
        assert "PRESETS: ClassVar" not in source_text
        assert 'return factory.PRESETS["development"]' in source_text
        assert "from ._constants import factory" in source_text
        assert "from collections.abc import Mapping" in constants_text
        assert "from typing import ClassVar" not in constants_text
        assert "from demo.typings import t" in constants_text
        assert "PRESETS: Mapping[str, t.JsonMapping]" in constants_text
        assert '    "development": {' in constants_text
        assert '"batch_size": 100' in constants_text
