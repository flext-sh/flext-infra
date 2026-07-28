"""Public rendering tests for the base.mk template renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config, m, main as infra_main
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture

_MIN_RENDERED_LINES = 400


class TestsFlextInfraBasemkRenderer:
    """Behavior contract for test_renderer."""

    def test_render_all_generates_large_makefile(self) -> None:
        """Render the complete base Makefile surface."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        tm.that(len(result.value.splitlines()), gt=_MIN_RENDERED_LINES)

    def test_setup_is_self_contained_and_uses_external_uv(self) -> None:
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        for required in (
            "UV ?= uv",
            "$(UV) venv --clear",
            "$(UV) sync --project",
            "submodule update --init --recursive",
            "--no-install-project",
        ):
            tm.that(rendered, has=required)
        for forbidden in ("poetry", "UV_VERSION", "3.13."):
            tm.that(rendered, lacks=forbidden)

    def test_render_all_has_no_scripts_path_references(self) -> None:
        """Exclude legacy script paths from the rendered contract."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        tm.that(result.value, lacks="scripts/")

    def test_render_all_environment_gate_fails_closed(self) -> None:
        """Reject a missing managed environment instead of selecting a fallback."""
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        tm.that(rendered, has="_builtin_require_environment:")
        tm.that(rendered, has="ERROR: missing environment interpreter")
        tm.that(rendered, lacks="python3 ||")
        tm.that(rendered, lacks="python ||")

    def test_render_all_builds_with_canonical_uv_command(self) -> None:
        """Build distributions without unrelated codegen or Poetry commands."""
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        tm.that(rendered, has='$(UV) build --project "$(PROJECT_ROOT)"')
        tm.that(rendered, has="UV ?= uv")
        tm.that(rendered, lacks="$(PROJECT_INFRA_CODEGEN) grpc")
        tm.that(rendered, lacks="$(POETRY) build")

    def test_render_all_with_config_override(self) -> None:
        """Render validated project-specific settings."""
        settings = m.Infra.BaseMkConfig(project_name="sample-project")

        result = FlextInfraBaseMkGenerator().generate_basemk(settings)

        tm.ok(result)
        tm.that(result.value, has="PROJECT_NAME := sample-project")

    def test_renderer_resolves_the_single_manifest_owner(self) -> None:
        """Render the exact template selected by the codegen manifest."""
        entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(entries, len=1)
        tm.that(entries[0].source, eq="base/Makefile.j2")

    def test_basemk_cli_generate_to_stdout(self, capsys: CaptureFixture[str]) -> None:
        """Generate the public base Makefile through the CLI."""
        exit_code = infra_main(["basemk", "generate", "--project-name", "cli-project"])
        captured = capsys.readouterr()

        tm.that(exit_code, eq=0)
        tm.that(captured.out, has="PROJECT_NAME := cli-project")

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
            "PUBLIC_VERBS := help setup deps build check test format run status docs clean release codegen worktree",
            ".PHONY: $(PUBLIC_VERBS) $(_BUILTIN_HANDLERS)",
            "_builtin_setup_environment:",
            "_builtin_build_artifacts:",
            "_builtin_check_all:",
            "_builtin_test_all:",
            "_builtin_format_apply:",
        ):
            tm.that(text, has=part)
        tm.that(text, lacks="boot:")
        tm.that(text, lacks="fmt:")
        tm.that(text, lacks="scan:")

    def test_render_all_declares_and_documents_runtime_options(self) -> None:
        """Document the runtime options accepted by generated targets."""
        result = FlextInfraBaseMkTemplateRenderer().render_all()

        tm.ok(result)
        text = result.value
        for part in (
            "CHECK_GATES ?=",
            "PYTEST_ARGS ?=",
            "PROJECT ?=",
            "PROJECTS ?=",
            "BRANCH ?=",
            "BASE ?= HEAD",
            "'format' 'check'",
            "'codegen' 'check'",
        ):
            tm.that(text, has=part)
        tm.that(text, lacks="FIX ?=")
