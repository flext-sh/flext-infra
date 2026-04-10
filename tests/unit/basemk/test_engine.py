"""Public rendering tests for the base.mk template engine."""

from __future__ import annotations

from _pytest.capture import CaptureFixture

from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkTemplateEngine,
    m,
    main as infra_main,
)


def basemk_main(argv: list[str]) -> int:
    return infra_main(["basemk", *argv])


def test_render_all_generates_large_makefile() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()

    assert result.is_success, result.error
    assert len(result.value.splitlines()) > 400


def test_render_all_has_no_scripts_path_references() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()

    assert result.is_success, result.error
    assert "scripts/" not in result.value


def test_render_all_with_config_override() -> None:
    config = m.Infra.BaseMkConfig(
        project_name="sample-project",
        python_version="3.13",
        core_stack="python",
        package_manager="poetry",
        source_dir="src",
        tests_dir="tests",
        lint_gates=["lint", "mypy"],
        test_command="pytest",
    )

    result = FlextInfraBaseMkGenerator().generate_basemk(config)

    assert result.is_success, result.error
    assert "PROJECT_NAME ?= sample-project" in result.value


def test_render_single_missing_template_fails() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_single("missing-template.mk.j2")

    assert result.is_failure
    assert "template render failed" in (result.error or "")


def test_basemk_cli_generate_to_stdout(capsys: CaptureFixture[str]) -> None:
    exit_code = basemk_main(["generate", "--project-name", "cli-project"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "PROJECT_NAME ?= cli-project" in captured.out


def test_engine_execute_returns_string() -> None:
    result = FlextInfraBaseMkTemplateEngine().execute()

    assert result.is_success, result.error
    assert isinstance(result.value, str)
    assert result.value


def test_render_all_exposes_canonical_public_targets() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()

    assert result.is_success, result.error
    text = result.value
    for part in (
        ".PHONY: help boot build check scan fmt docs test val clean pr",
        "STANDARD_VERBS := boot build check scan fmt docs test val clean pr",
        "boot: ## Complete setup",
        "scan: ## Run all security checks",
        "fmt: ## Run code formatting",
        "val: ## Run validate gates",
    ):
        assert part in text
    assert "setup build check security format docs" not in text
    assert "docs-base" not in text
    assert "docs-sync-scripts" not in text


def test_render_all_declares_and_documents_runtime_options() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()

    assert result.is_success, result.error
    text = result.value
    for part in (
        "FIX ?=",
        'echo "  CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,go,type"',
        'echo "  FILE=src/foo.py             Single file for check/fmt/test"',
        'echo "  CHANGED_ONLY=1              Git-changed Python files for check"',
        'echo "  DIAG=1                      Emit extended pytest diagnostics"',
        'echo "  FIX=1                       Auto-fix supported gates"',
    ):
        assert part in text
    assert "check-fast" not in text
