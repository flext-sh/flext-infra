"""Tests for FlextBasemkEngine to achieve full coverage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from flext_tests import tm
from jinja2 import TemplateError

from flext_core import r
from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraBaseMkTemplateEngine,
    main as infra_main,
)
from tests import m as im, t


def basemk_main(argv: list[str] | None = None) -> int:
    args = ["basemk"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


class _InvalidTemplateEngine:
    def render_all(self, config: im.Infra.BaseMkConfig | None = None) -> r[str]:
        del config
        return r[str].ok("ifneq (,\n")


def test_render_all_generates_large_makefile() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()
    tm.ok(result)
    content = result.value
    assert len(content.splitlines()) > 400


def test_render_all_has_no_scripts_path_references() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()
    tm.ok(result)
    assert "scripts/" not in result.value


def test_generator_renders_with_config_override() -> None:
    config = im.Infra.BaseMkConfig(
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
    tm.ok(result)
    assert "PROJECT_NAME ?= sample-project" in result.value


def test_generator_fails_for_invalid_make_syntax() -> None:
    result = FlextInfraBaseMkGenerator(
        template_engine=_InvalidTemplateEngine(),
    ).generate_basemk()
    tm.fail(result)
    assert result.error is not None
    assert "validation failed" in result.error


def test_generator_write_saves_output_file(tmp_path: Path) -> None:
    output_path = tmp_path / "base.mk"
    content = "all:\n\t@true\n"
    result = FlextInfraBaseMkGenerator().write(content, output=output_path)
    tm.ok(result)
    assert output_path.read_text(encoding="utf-8") == content


def test_basemk_cli_generate_to_stdout(capsys: CaptureFixture[str]) -> None:
    exit_code = basemk_main(["generate", "--project-name", "cli-project"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PROJECT_NAME ?= cli-project" in captured.out


def test_basemk_cli_generate_to_file(tmp_path: Path) -> None:
    output_path = tmp_path / "base.mk"
    exit_code = basemk_main(["generate", "--output", str(output_path)])
    assert exit_code == 0
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").startswith(
        "# ====================================",
    )


def test_basemk_engine_render_all_returns_string() -> None:
    """Test engine.render_all() returns string."""
    engine = FlextInfraBaseMkTemplateEngine()
    result = engine.render_all()
    tm.ok(result)
    assert isinstance(result.value, str) and result.value


def test_basemk_engine_render_all_with_valid_config() -> None:
    """Test engine.render_all() with explicit config."""
    config = im.Infra.BaseMkConfig(
        project_name="test-project",
        python_version="3.13",
        core_stack="python",
        package_manager="poetry",
        source_dir="src",
        tests_dir="tests",
        lint_gates=["mypy", "ruff"],
        test_command="pytest",
    )
    engine = FlextInfraBaseMkTemplateEngine()
    result = engine.render_all(config=config)
    tm.ok(result)
    assert "PROJECT_NAME ?= test-project" in result.value


def test_basemk_engine_execute_calls_render_all() -> None:
    """Test engine.execute() calls render_all()."""
    engine = FlextInfraBaseMkTemplateEngine()
    result = engine.execute()
    tm.ok(result)
    assert isinstance(result.value, str)
    assert result.value


def test_basemk_engine_render_all_handles_template_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test engine.render_all() handles TemplateError gracefully."""

    def mock_get_template(*args: t.Scalar, **kwargs: t.Scalar) -> None:
        msg = "Template not found"
        raise TemplateError(msg)

    engine = FlextInfraBaseMkTemplateEngine()
    result = engine.render_all()
    tm.fail(result)
    assert isinstance(result.error, str)
    assert isinstance(result.error, str)
    assert "template render failed" in result.error


def test_render_all_exposes_canonical_public_targets() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()
    tm.ok(result)
    tm.that(
        result.value,
        has=[
            ".PHONY: help boot build check scan fmt docs test val clean pr",
            "STANDARD_VERBS := boot build check scan fmt docs test val clean pr",
            "boot: ## Complete setup",
            "scan: ## Run all security checks",
            "fmt: ## Run code formatting",
            "val: ## Run validate gates",
        ],
    )
    assert "setup build check security format docs" not in result.value
    assert "docs-base" not in result.value
    assert "docs-sync-scripts" not in result.value


def test_render_all_declares_and_documents_runtime_options() -> None:
    result = FlextInfraBaseMkTemplateEngine().render_all()
    tm.ok(result)
    tm.that(
        result.value,
        has=[
            "FIX ?=",
            'echo "  CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,go,type"',
            'echo "  FILE=src/foo.py             Single file for check/fmt/test"',
            'echo "  CHANGED_ONLY=1              Git-changed Python files for check"',
            'echo "  DIAG=1                      Emit extended pytest diagnostics"',
            'echo "  FIX=1                       Auto-fix supported gates"',
        ],
    )
    assert "check-fast" not in result.value
