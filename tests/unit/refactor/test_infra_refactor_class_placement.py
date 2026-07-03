from __future__ import annotations

from pathlib import Path

from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
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
