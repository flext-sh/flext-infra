"""Public generator tests for base.mk generation and writing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import io
from pathlib import Path

from flext_tests import tm

from flext_infra import m
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator


class TestsFlextInfraBasemkGenerator:
    """Behavior contract for test_generator."""

    def test_generator_initializes_with_default_renderer(self) -> None:
        """Initialize the generator with its default renderer."""
        tm.that(FlextInfraBaseMkGenerator(), none=False)

    def test_generator_execute_returns_generated_content(self) -> None:
        """Generate base.mk content through the public execute contract."""
        result = FlextInfraBaseMkGenerator(project_name="demo-project").execute()

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= demo-project")

    def test_generator_generate_with_none_config_uses_default(self) -> None:
        """Use default settings when no base.mk configuration is provided."""
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?=")

    def test_generator_generate_with_basemk_config_object(self) -> None:
        """Generate base.mk content from a validated configuration model."""
        settings = m.Infra.BaseMkConfig(
            project_name="test-proj",
            python_version="3.13",
            package_manager="poetry",
            source_dir="src",
            tests_dir="tests",
            lint_gates=["mypy"],
            test_command="pytest",
        )

        result = FlextInfraBaseMkGenerator().generate_basemk(settings=settings)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= test-proj")

    def test_generator_generate_with_invalid_mapping_fails(self) -> None:
        """Return a failure for an invalid configuration mapping."""
        result = FlextInfraBaseMkGenerator().generate_basemk(
            settings={"invalid_key": "x"}
        )

        tm.fail(result)
        tm.that((result.error or ""), has="validation failed")

    def test_generator_write_to_file(self, tmp_path: Path) -> None:
        """Write generated content to a filesystem path."""
        output_path = tmp_path / "test.mk"
        content = "all:\n\t@echo 'test'\n"

        result = FlextInfraBaseMkGenerator().write(content, output=output_path)

        tm.ok(result)
        tm.that(output_path.exists(), eq=True)
        tm.that(output_path.read_text(encoding="utf-8"), eq=content)

    def test_generator_write_creates_parent_directories(self, tmp_path: Path) -> None:
        """Create parent directories before writing generated content."""
        output_path = tmp_path / "nested" / "dir" / "test.mk"

        result = FlextInfraBaseMkGenerator().write(
            "all:\n\t@true\n", output=output_path
        )

        tm.ok(result)
        tm.that(output_path.exists(), eq=True)

    def test_generator_write_to_stream(self) -> None:
        """Write generated content to an output stream."""
        stream = io.StringIO()
        content = "all:\n\t@echo 'test'\n"

        result = FlextInfraBaseMkGenerator().write(content, stream=stream)

        tm.ok(result)
        tm.that(stream.getvalue(), eq=content)

    def test_generator_write_fails_without_output_or_stream(self) -> None:
        """Return a failure when no output target is provided."""
        result = FlextInfraBaseMkGenerator().write("all:\n\t@echo 'test'\n")

        tm.fail(result)
        tm.that((result.error or ""), has="stdout stream is required")
