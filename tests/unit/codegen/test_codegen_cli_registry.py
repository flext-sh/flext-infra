"""Config/generator round-trip tests for the lightweight CLI registry."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, m
from flext_infra.codegen.cli_registry import FlextInfraCodegenCliRegistry
from flext_tests import tm


class TestsFlextInfraCodegenCliRegistry:
    """Prove the checked-in registry is a byte-exact config projection."""

    def test_checked_in_projection_matches_typed_config(self) -> None:
        """Render the production SSOT and compare its versioned projection."""
        rendered = FlextInfraCodegenCliRegistry.render(
            config.Infra.codegen.cli_registry
        )

        tm.ok(rendered)
        target = Path.cwd() / config.Infra.codegen.cli_registry.output_path
        tm.that(target.read_text(encoding="utf-8"), eq=rendered.value)

    def test_arbitrary_valid_catalog_round_trips_without_route_imports(self) -> None:
        """Render arbitrary valid descriptors without freezing production values."""
        registry = m.Infra.CliRegistrySpec.model_validate({
            "repository": "example",
            "output_path": "src/example/_generated_cli_registry.py",
            "options": (
                {"name": "--sample", "arity": 1},
                {"name": "--flag", "arity": 0},
            ),
            "groups": (
                {
                    "name": "sample",
                    "help_text": "Sample commands",
                    "what_strategy": "validate-command",
                    "commands": (
                        {
                            "name": "inspect-item",
                            "help_text": "Inspect one item",
                            "loader_ref": (
                                "flext_infra.services.cli_routes_validate_commands:"
                                "ValidationCommandRoutes.load_inspect_item"
                            ),
                        },
                    ),
                },
            ),
        })

        rendered = FlextInfraCodegenCliRegistry.render(registry)

        tm.ok(rendered)
        tm.that(rendered.value, has='"--sample": 1')
        tm.that(rendered.value, has='"sample": "validate-command"')
        tm.that(
            rendered.value,
            has=(
                '"inspect-item": "flext_infra.services.'
                "cli_routes_validate_commands:"
                'ValidationCommandRoutes.load_inspect_item"'
            ),
        )
        tm.that(rendered.value, lacks="import flext_infra.services")
