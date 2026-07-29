"""Generate the lightweight CLI registry from the typed codegen SSOT."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra import config, u
from flext_infra.base import s
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenCliRegistry(s[bool]):
    """Render the import-free CLI descriptor projection used during selection."""

    @staticmethod
    def render(registry: p.Infra.CliRegistrySpec) -> p.Result[str]:
        """Render one validated registry without importing any route owner."""
        return r[str].create_from_callable(
            lambda: FlextInfraCodegenGenerationRenderersMixin.render_python_template(
                "cli_registry.py.j2",
                registry,
                target_filename=registry.output_path.as_posix(),
            ),
            error_code="CLI_REGISTRY_RENDER",
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Check or update the config-owned registry projection."""
        registry = config.Infra.codegen.cli_registry
        rendered = self.render(registry)
        if rendered.failure:
            return r[bool].fail(rendered.error or "CLI registry rendering failed")
        target = self.workspace_root / registry.output_path
        if target.is_file():
            current = u.Cli.files_read_text(target)
            if current.failure:
                return r[bool].fail(
                    current.error or f"CLI registry read failed: {target}"
                )
            if current.value == rendered.value:
                return r[bool].ok(True)
        if self.check_only or self.dry_run:
            return r[bool].fail(f"CLI registry projection is stale: {target}")
        write_result = u.Cli.atomic_write_text_file(target, rendered.value)
        if write_result.failure:
            return r[bool].fail(
                write_result.error or f"CLI registry write failed: {target}"
            )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenCliRegistry"]
