from __future__ import annotations

from pathlib import Path

import pytest

try:
    from flext_infra import c
    from flext_infra.refactor.dependency_analyzer import ClassPlacementDetector
except ImportError as exc:
    pytest.skip(f"refactor package unavailable: {exc}", allow_module_level=True)


def test_detects_basemodel_in_non_model_file(tmp_path: Path) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert len(violations) == 1
    assert violations[0].name == "PublicModel"
    assert violations[0].base_class == "BaseModel"


def test_detects_attribute_base_class(tmp_path: Path) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "from flext_core import FlextModels\n"
        "class PublicModel(FlextModels.ArbitraryTypesModel):\n"
        "    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert len(violations) == 1
    assert violations[0].name == "PublicModel"
    assert violations[0].base_class == "ArbitraryTypesModel"


def test_skips_models_file(tmp_path: Path) -> None:
    target = tmp_path / "models.py"
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert violations == []


def test_skips_models_directory(tmp_path: Path) -> None:
    models_dir = tmp_path / "_models"
    models_dir.mkdir(parents=True)
    target = models_dir / "domain.py"
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert violations == []


def test_skips_settings_file(tmp_path: Path) -> None:
    settings_file_name = min(c.Infra.Refactor.NAMESPACE_SETTINGS_FILE_NAMES)
    target = tmp_path / settings_file_name
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert violations == []


def test_skips_protected_files(tmp_path: Path) -> None:
    protected_file_name = min(c.Infra.Refactor.NAMESPACE_PROTECTED_FILES)
    target = tmp_path / protected_file_name
    target.write_text(
        "from pydantic import BaseModel\nclass PublicModel(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert violations == []


def test_skips_private_class(tmp_path: Path) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "from pydantic import BaseModel\nclass _PrivateModel(BaseModel):\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert violations == []


def test_detects_multiple_models(tmp_path: Path) -> None:
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

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert len(violations) == 2
    assert {violation.name for violation in violations} == {"FirstModel", "SecondModel"}


def test_non_pydantic_class_not_flagged(tmp_path: Path) -> None:
    target = tmp_path / "consumer.py"
    target.write_text(
        "class PlainClass:\n    pass\n",
        encoding="utf-8",
    )

    violations = ClassPlacementDetector.detect_file(file_path=target)

    assert violations == []
