"""Public rendering tests for the base.mk template renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config, m, main as infra_main
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


class TestsFlextInfraBasemkRenderer:
    """Behavior contract for test_renderer."""

    def test_bootstrap_setup_is_self_contained_and_branch_aware(self) -> None:
        rendered: str = tm.ok(
            FlextInfraBaseMkTemplateRenderer.render_bootstrap_include()
        )

        for required in (
            'SETUP_ROOT := $(shell git -C "$(BOOTSTRAP_OWNER)" rev-parse --show-toplevel)',
            'SETUP_BRANCH := $(shell git -C "$(SETUP_ROOT)" rev-parse --abbrev-ref HEAD)',
            'UV_PROJECT_ENVIRONMENT="$(SETUP_VENV)"',
            "BOOTSTRAP_OWNER :=",
            "TRACKED_MISE := $(SETUP_ROOT)/bin/mise",
            "SYSTEM_MISE_VERSION :=",
            '"$(SETUP_MISE)" -C "$(SETUP_ROOT)" exec -- uv',
            f'uv_required="{config.Infra.codegen.toolchain.uv_version}"',
            '"$$mise" trust "$$project_root/.mise.toml"',
            "install --locked --yes",
            "$(SETUP_UV) sync --project",
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
            "MISE_DATA_DIR := $(SETUP_ROOT)",
            "BOOTSTRAP_PIP",
            "pip install",
            "poetry",
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
        rendered: str = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

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
