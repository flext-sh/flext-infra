"""Public generator tests for base.mk generation and writing."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from flext_infra import config, m
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraBasemkGenerator:
    """Behavior contract for test_generator."""

    def test_generator_initializes_with_default_renderer(self) -> None:
        """Construct the generator with its canonical default renderer."""
        tm.that(FlextInfraBaseMkGenerator(), none=False)

    def test_generator_execute_returns_generated_content(self) -> None:
        """Return rendered base.mk content from the public execute surface."""
        result = FlextInfraBaseMkGenerator(project_name="demo-project").execute()

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= demo-project")

    def test_generator_generate_with_none_config_uses_default(self) -> None:
        """Resolve canonical defaults when no explicit generation config is supplied."""
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?=")

    def test_generator_pr_booleans_do_not_render_as_positional_values(self) -> None:
        """Reject positional values for generated Click boolean options."""
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        tm.that('--draft "$(PR_DRAFT)"' not in result.value, eq=True)

    def test_generator_pr_booleans_render_click_dual_flags(self) -> None:
        """Render generated PR booleans through Click dual-flag syntax."""
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        tm.that(result.value, has="$(if $(filter 1,$(PR_DRAFT)),--draft,--no-draft)")

    def test_generator_generate_with_basemk_config_object(self) -> None:
        """Render from the validated BaseMk configuration model."""
        make_spec = config.Infra.codegen.make
        settings = m.Infra.BaseMkConfig(
            project_name="test-proj",
            python_version="3.13",
            source_dir="src",
            tests_dir="tests",
            lint_gates=["mypy"],
            test_item_timeout_seconds=make_spec.test_item_timeout_seconds,
            test_session_timeout_seconds=make_spec.test_session_timeout_seconds,
            test_shard_count=make_spec.test_shard_count,
            test_shard_parallelism=make_spec.test_shard_parallelism,
        )

        result = FlextInfraBaseMkGenerator().generate_basemk(settings=settings)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= test-proj")

    def test_generator_generate_with_invalid_mapping_fails(self) -> None:
        """Fail closed when generation receives an invalid settings mapping."""
        result = FlextInfraBaseMkGenerator().generate_basemk(
            settings={"invalid_key": "x"}
        )

        tm.fail(result)
        tm.that((result.error or ""), has="validation failed")

    def test_generator_write_to_file(self, tmp_path: Path) -> None:
        """Write generated content to the requested filesystem destination."""
        output_path = tmp_path / "test.mk"
        content = "all:\n\t@echo 'test'\n"

        result = FlextInfraBaseMkGenerator().write(content, output=output_path)

        tm.ok(result)
        tm.that(output_path.exists(), eq=True)
        tm.that(output_path.read_text(encoding="utf-8"), eq=content)

    def test_generator_write_creates_parent_directories(self, tmp_path: Path) -> None:
        """Create missing parent directories before writing generated content."""
        output_path = tmp_path / "nested" / "dir" / "test.mk"

        result = FlextInfraBaseMkGenerator().write(
            "all:\n\t@true\n", output=output_path
        )

        tm.ok(result)
        tm.that(output_path.exists(), eq=True)

    def test_generator_write_to_stream(self) -> None:
        """Write generated content to an explicitly supplied text stream."""
        stream = io.StringIO()
        content = "all:\n\t@echo 'test'\n"

        result = FlextInfraBaseMkGenerator().write(content, stream=stream)

        tm.ok(result)
        tm.that(stream.getvalue(), eq=content)

    def test_generator_write_fails_without_output_or_stream(self) -> None:
        """Fail closed when neither a path nor an output stream is supplied."""
        result = FlextInfraBaseMkGenerator().write("all:\n\t@echo 'test'\n")

        tm.fail(result)
        tm.that((result.error or ""), has="stdout stream is required")
