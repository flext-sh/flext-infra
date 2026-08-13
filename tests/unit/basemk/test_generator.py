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
        tm.that(FlextInfraBaseMkGenerator(), none=False)

    def test_generator_execute_returns_generated_content(self) -> None:
        result = FlextInfraBaseMkGenerator(project_name="demo-project").execute()

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= demo-project")

    def test_generator_generate_with_none_config_uses_default(self) -> None:
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?=")

    def test_generator_pr_booleans_do_not_render_as_positional_values(self) -> None:
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        for variable in (
            "PR_DRAFT",
            "PR_AUTO",
            "PR_DELETE_BRANCH",
            "PR_CHECKS_STRICT",
            "PR_RELEASE_ON_MERGE",
        ):
            tm.that(
                f'--{variable[3:].lower().replace("_", "-")} "$({variable})"'
                not in result.value,
                eq=True,
            )

    def test_generator_pr_booleans_render_click_dual_flags(self) -> None:
        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        expected_flags = {
            "PR_DRAFT": ("--draft", "--no-draft"),
            "PR_AUTO": ("--auto", "--no-auto"),
            "PR_DELETE_BRANCH": ("--delete-branch", "--no-delete-branch"),
            "PR_CHECKS_STRICT": ("--checks-strict", "--no-checks-strict"),
            "PR_RELEASE_ON_MERGE": ("--release-on-merge", "--no-release-on-merge"),
        }
        for variable, (enabled_flag, disabled_flag) in expected_flags.items():
            tm.that(
                result.value,
                has=f"$(if $(filter 1,$({variable})),{enabled_flag},{disabled_flag})",
            )

    def test_generator_enforces_pytest_process_deadline(self) -> None:
        """The rendered base.mk carries the config-owned invocation deadline.

        mro-wkii.17.37 renamed the hard process boundary to
        ``PYTEST_RUN_TIMEOUT_SECONDS`` and moved enforcement into the typed
        Python runner, so the generated Make surface publishes the budget and
        delegates execution instead of wrapping pytest in a shell timeout.
        """
        policy = config.Infra.tooling.tools.pytest

        result = FlextInfraBaseMkGenerator().generate_basemk(settings=None)

        tm.ok(result)
        tm.that(
            result.value,
            has=(f"PYTEST_PROCESS_TIMEOUT_SECONDS ?= {policy.process_timeout_seconds}"),
        )
        # R12 (commit 2f7b8900d): base.mk declares only the verbs it ships a
        # recipe for, so the pytest invocation moved to the generated project
        # Makefile. base.mk's remaining duty is to PUBLISH the bounded-process
        # wrapper built from the config budget, which the project recipe consumes.
        tm.that(result.value, has="PYTEST_BOUNDED = ")
        tm.that(result.value, has="$(PYTEST_PROCESS_TIMEOUT_SECONDS)s")

    def test_generator_generate_with_basemk_config_object(self) -> None:
        settings = m.Infra.BaseMkConfig(
            project_name="test-proj",
            python_version="3.13",
            source_dir="src",
            tests_dir="tests",
            lint_gates=["mypy"],
        )

        result = FlextInfraBaseMkGenerator().generate_basemk(settings=settings)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= test-proj")

    def test_generator_generate_with_invalid_mapping_fails(self) -> None:
        result = FlextInfraBaseMkGenerator().generate_basemk(
            settings={"invalid_key": "x"}
        )

        tm.fail(result)
        tm.that((result.error or ""), has="validation failed")

    def test_generator_write_to_file(self, tmp_path: Path) -> None:
        output_path = tmp_path / "test.mk"
        content = "all:\n\t@echo 'test'\n"

        result = FlextInfraBaseMkGenerator().write(content, output=output_path)

        tm.ok(result)
        tm.that(output_path.exists(), eq=True)
        tm.that(output_path.read_text(encoding="utf-8"), eq=content)

    def test_generator_write_creates_parent_directories(self, tmp_path: Path) -> None:
        output_path = tmp_path / "nested" / "dir" / "test.mk"

        result = FlextInfraBaseMkGenerator().write(
            "all:\n\t@true\n", output=output_path
        )

        tm.ok(result)
        tm.that(output_path.exists(), eq=True)

    def test_generator_write_to_stream(self) -> None:
        stream = io.StringIO()
        content = "all:\n\t@echo 'test'\n"

        result = FlextInfraBaseMkGenerator().write(content, stream=stream)

        tm.ok(result)
        tm.that(stream.getvalue(), eq=content)

    def test_generator_write_fails_without_output_or_stream(self) -> None:
        result = FlextInfraBaseMkGenerator().write("all:\n\t@echo 'test'\n")

        tm.fail(result)
        tm.that((result.error or ""), has="stdout stream is required")
