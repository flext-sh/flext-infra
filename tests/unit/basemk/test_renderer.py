"""Public rendering tests for the base.mk template renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, main as infra_main
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm

from _pytest.capture import CaptureFixture


_MIN_RENDERED_LINES = 400


class TestsFlextInfraBasemkRenderer:
    """Behavior contract for test_renderer."""

    def test_render_all_generates_large_makefile(self) -> None:
        """Render the complete base Makefile surface."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        tm.that(len(result.value.splitlines()), gt=_MIN_RENDERED_LINES)

    def test_render_all_has_no_scripts_path_references(self) -> None:
        """Exclude legacy script paths from the rendered contract."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        tm.that(result.value, lacks="scripts/")

    def test_render_all_preflight_is_read_only_and_fail_closed(self) -> None:
        """Reject stale state without deleting environments or syncing source."""
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        tm.that(rendered, has="define VALIDATE_CANONICAL_BASE_MK")
        tm.that(rendered, has="basemk-validate")
        tm.that(rendered, has="Project-local .venv violates")
        tm.that(rendered, lacks="AUTO_SYNC_BASE_AND_SCRIPTS")
        tm.that(rendered, lacks="rm -rf .venv")

    def test_render_all_with_config_override(self) -> None:
        """Render validated project-specific settings."""
        settings = m.Infra.BaseMkConfig(
            project_name="sample-project",
            python_version="3.13",
            package_manager="poetry",
            source_dir="src",
            tests_dir="tests",
            lint_gates=["lint", "mypy"],
            test_command="pytest",
        )

        result = FlextInfraBaseMkGenerator().generate_basemk(settings)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME ?= sample-project")

    def test_render_single_missing_template_fails(self) -> None:
        """Reject a template name outside the canonical inventory."""
        result = FlextInfraBaseMkTemplateRenderer().render_single(
            "missing-template.mk.j2"
        )

        tm.fail(result)
        tm.that((result.error or ""), has="template render failed")

    def test_basemk_cli_generate_to_stdout(self, capsys: CaptureFixture[str]) -> None:
        """Generate the public base Makefile through the CLI."""
        exit_code = infra_main(["basemk", "generate", "--project-name", "cli-project"])
        captured = capsys.readouterr()

        tm.that(exit_code, eq=0)
        tm.that(captured.out, has="PROJECT_NAME ?= cli-project")

    def test_renderer_execute_returns_string(self) -> None:
        """Return rendered text from the service execution contract."""
        result = FlextInfraBaseMkTemplateRenderer().execute()

        tm.ok(result)
        tm.that(result.value, is_=str)
        tm.that(result.value, empty=False)

    def test_render_all_exposes_canonical_public_targets(self) -> None:
        """Expose exactly the canonical public Make targets."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        text = result.value
        for part in (
            ".PHONY: help boot build check scan fmt docs docs-serve test val clean pr",
            "STANDARD_VERBS := boot build check scan fmt docs test val clean pr",
            "boot: ## Complete setup",
            "scan: ## Run all security checks",
            "fmt: ## Run code formatting",
            "val: ## Run validate gates",
        ):
            tm.that(text, has=part)
        tm.that(text, lacks="setup build check security format docs")
        tm.that(text, lacks="docs-base")
        tm.that(text, lacks="docs-sync-scripts")

    def test_render_all_declares_and_documents_runtime_options(self) -> None:
        """Document the runtime options accepted by generated targets."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        text = result.value
        for part in (
            "FIX ?=",
            'echo "  CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,smells,type"',
            'echo "  FILE=src/foo.py             Single file for check/fmt/test"',
            'echo "  CHANGED_ONLY=1              Git-changed Python files for check"',
            'echo "  DIAG=1                      Emit extended pytest diagnostics"',
            'echo "  FIX=1                       Auto-fix supported gates"',
        ):
            tm.that(text, has=part)
        tm.that(text, lacks="check-fast")
