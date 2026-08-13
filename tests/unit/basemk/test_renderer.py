"""Public rendering tests for the base.mk template renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, main as infra_main
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture

# R12 moved every verb recipe into the project Makefile; base.mk now carries
# only the shared infrastructure surface (detection, venv, preflight, daemons,
# pr, clean), so the rendered contract is smaller than the pre-R12 file.
_MIN_RENDERED_LINES = 250


class TestsFlextInfraBasemkRenderer:
    """Behavior contract for test_renderer."""

    def test_render_all_generates_large_makefile(self) -> None:
        """Render the complete base Makefile surface."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        tm.that(len(result.value.splitlines()), gt=_MIN_RENDERED_LINES)

    def test_bootstrap_setup_is_self_contained_and_branch_aware(self) -> None:
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer.render_bootstrap_include())

        for required in (
            "SETUP_ROOT := $(shell git rev-parse --show-toplevel)",
            "SETUP_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)",
            'UV_PROJECT_ENVIRONMENT="$(SETUP_VENV)"',
            "SETUP_BIN := $(SETUP_ROOT)/.bin",
            "MISE_DATA_DIR := $(SETUP_ROOT)/.tools",
            "SETUP_MISE ?= $(SETUP_BIN)/mise",
            "SETUP_UV := $(MISE_DATA_DIR)/shims/uv",
            "github.com/jdx/mise/releases/download",
            "$(SETUP_MISE) install --yes",
            "$(SETUP_UV_ENV) uv sync --project",
            "git submodule update --init --recursive",
            'test -z "$$(git status --porcelain)"',
            'test "$$(git rev-parse HEAD)" = "$$sha1"',
            "refs/heads/$(SETUP_BRANCH)",
            'git checkout --quiet -b "$(SETUP_BRANCH)"',
            "$(SETUP_PYTHON) -m flext_infra",
        ):
            tm.that(rendered, has=required)
        for forbidden in (
            "SETUP_UV ?= uv",
            "python -m venv",
            "BOOTSTRAP_PIP",
            "pip install",
            "poetry",
            "mise exec",
            "$(PYTHON_CMD) -c 'import flext_infra'",
        ):
            tm.that(rendered, lacks=forbidden)

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

    def test_render_all_builds_with_canonical_uv_command(self) -> None:
        """Bind uv to the resolved runtime without Poetry or codegen commands."""
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        # R12: `build` is a project-Makefile verb now. base.mk still owns the uv
        # binding every verb inherits.
        tm.that(rendered, has="UV ?= uv")
        tm.that(rendered, has="override UV_PROJECT := $(WORKSPACE_ROOT)")
        tm.that(rendered, has="override UV_PROJECT_ENVIRONMENT := $(ACTIVE_VENV)")
        tm.that(rendered, lacks="$(PROJECT_INFRA_CODEGEN) grpc")
        tm.that(rendered, lacks="$(POETRY) build")

    def test_render_all_with_config_override(self) -> None:
        """Render validated project-specific settings."""
        settings = m.Infra.BaseMkConfig(
            project_name="sample-project",
            python_version="3.13",
            source_dir="src",
            tests_dir="tests",
            lint_gates=["lint", "mypy"],
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
            ".PHONY: help boot build check scan fmt test val clean pr",
            "STANDARD_VERBS := boot build check scan fmt test val clean pr",
            "clean: ## Clean artifacts",
            "pr: ## Manage pull requests for this repository",
        ):
            tm.that(text, has=part)
        # R12: the docs verb is exterminated — docs is a WHAT selector on the
        # standard verbs, never a target of its own.
        tm.that(text, lacks="docs-serve")
        tm.that(text, lacks="docs-base")
        tm.that(text, lacks="docs-sync-scripts")

    def test_render_all_declares_and_documents_runtime_options(self) -> None:
        """Document the runtime options accepted by generated targets."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        text = result.value
        for part in (
            "FIX ?=",
            "CHECK_GATES ?=",
            "CHANGED_ONLY ?=",
            "DIAG ?= 0",
            "PYTEST_ARGS ?=",
        ):
            tm.that(text, has=part)
        tm.that(text, lacks="check-fast")
