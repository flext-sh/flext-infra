from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraClassPlacementDetector
from tests import c, m, t


def test_detects_basemodel_in_non_model_file(
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(m.BaseModel):\n    pass\n",
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
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    target = tmp_path / "models.py"
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(m.BaseModel):\n    pass\n",
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
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    models_dir = tmp_path / "_models"
    models_dir.mkdir(parents=True)
    target = models_dir / "domain.py"
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(m.BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = FlextInfraClassPlacementDetector.detect_file(
        m.Infra.DetectorContext(
            file_path=target,
            rope_project=rope_project,
        ),
    )

    assert violations == []


def test_skips_settings_file(
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    settings_file_name = min(c.Infra.NAMESPACE_SETTINGS_FILE_NAMES)
    target = tmp_path / settings_file_name
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(m.BaseModel):\n    pass\n",
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
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    protected_file_name = min(c.Infra.NAMESPACE_PROTECTED_FILES)
    target = tmp_path / protected_file_name
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(m.BaseModel):\n    pass\n",
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
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "from pydantic import BaseModel\nclass _PrivateModel(m.BaseModel):\n    pass\n",
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
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "from pydantic import BaseModel\n"
        "from flext_core import FlextModels\n"
        "class FirstModel(m.BaseModel):\n"
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
    assert {violation.name for violation in violations} == {"FirstModel", "SecondModel"}


def test_non_pydantic_class_not_flagged(
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
