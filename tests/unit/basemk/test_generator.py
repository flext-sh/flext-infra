"""Public generator tests for base.mk generation and writing."""

from __future__ import annotations

import io
from pathlib import Path

from flext_infra import FlextInfraBaseMkGenerator, m


def test_generator_initializes_with_default_engine() -> None:
    assert FlextInfraBaseMkGenerator() is not None


def test_generator_execute_returns_generated_content() -> None:
    result = FlextInfraBaseMkGenerator(project_name="demo-project").execute()

    assert result.success, result.error
    assert "PROJECT_NAME ?= demo-project" in result.value


def test_generator_generate_with_none_config_uses_default() -> None:
    result = FlextInfraBaseMkGenerator().generate_basemk(config=None)

    assert result.success, result.error
    assert "PROJECT_NAME ?=" in result.value


def test_generator_generate_with_basemk_config_object() -> None:
    config = m.Infra.BaseMkConfig(
        project_name="test-proj",
        python_version="3.13",
        core_stack="python",
        package_manager="poetry",
        source_dir="src",
        tests_dir="tests",
        lint_gates=["mypy"],
        test_command="pytest",
    )

    result = FlextInfraBaseMkGenerator().generate_basemk(config=config)

    assert result.success, result.error
    assert "PROJECT_NAME ?= test-proj" in result.value


def test_generator_generate_with_invalid_mapping_fails() -> None:
    result = FlextInfraBaseMkGenerator().generate_basemk(config={"invalid_key": "x"})

    assert result.failure
    assert "validation failed" in (result.error or "")


def test_generator_write_to_file(tmp_path: Path) -> None:
    output_path = tmp_path / "test.mk"
    content = "all:\n\t@echo 'test'\n"

    result = FlextInfraBaseMkGenerator().write(content, output=output_path)

    assert result.success, result.error
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == content


def test_generator_write_creates_parent_directories(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "dir" / "test.mk"

    result = FlextInfraBaseMkGenerator().write("all:\n\t@true\n", output=output_path)

    assert result.success, result.error
    assert output_path.exists()


def test_generator_write_to_stream() -> None:
    stream = io.StringIO()
    content = "all:\n\t@echo 'test'\n"

    result = FlextInfraBaseMkGenerator().write(content, stream=stream)

    assert result.success, result.error
    assert stream.getvalue() == content


def test_generator_write_fails_without_output_or_stream() -> None:
    result = FlextInfraBaseMkGenerator().write("all:\n\t@echo 'test'\n")

    assert result.failure
    assert "stdout stream is required" in (result.error or "")
