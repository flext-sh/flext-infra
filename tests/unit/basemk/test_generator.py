"""Public generator tests for base.mk generation and writing."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from flext_infra import m
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

    def test_generator_targets_declared_direct_git_dependencies(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "fixture-project"\nversion = "0.1.0"\n'
            'dependencies = [\n'
            '  "Branch_Alpha @ git+https://example.invalid/alpha.git@main",\n'
            '  "branch-beta[cli] @ git+ssh://git@example.invalid/beta.git@develop",\n'
            '  "stable-registry>=1.2",\n'
            ']\n',
            encoding="utf-8",
        )

        result = FlextInfraBaseMkGenerator(workspace_root=tmp_path).generate_basemk()

        tm.ok(result)
        tm.that(
            result.value,
            has=(
                "$(UV) lock --upgrade-package branch-alpha "
                "--upgrade-package branch-beta"
            ),
        )
        tm.that(result.value, lacks="--upgrade-package stable-registry")

    def test_generator_keeps_plain_lock_without_direct_git_dependencies(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "fixture-project"\nversion = "0.1.0"\n'
            'dependencies = ["stable-registry>=1.2"]\n',
            encoding="utf-8",
        )

        result = FlextInfraBaseMkGenerator(workspace_root=tmp_path).generate_basemk()

        tm.ok(result)
        tm.that(result.value, has="\t$(Q)$(UV) lock\n")
        tm.that(result.value, lacks="--upgrade-package")

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
