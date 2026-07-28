"""Compatibility facade for the canonical generated Makefile template."""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import c, config, m, p, r, s, t, u


def _templates_dir() -> Path:
    """Resolve templates directory relative to this package."""
    return Path(__file__).resolve().parent.parent / "templates"


class FlextInfraBaseMkTemplateRenderer(s[str]):
    """Render the sole Makefile owner through its typed codegen context."""

    @staticmethod
    def default_config() -> m.Infra.BaseMkConfig:
        """Return default base.mk generation configuration."""
        return m.Infra.BaseMkConfig(project_name=c.Infra.DEFAULT_UNNAMED)

    @staticmethod
    def normalize_config(
        settings: m.Infra.BaseMkConfig | t.ScalarMapping | None,
    ) -> p.Result[m.Infra.BaseMkConfig]:
        """Normalize user-provided config to the canonical BaseMk model."""
        if settings is None:
            return r[m.Infra.BaseMkConfig].ok(
                FlextInfraBaseMkTemplateRenderer.default_config()
            )
        if isinstance(settings, m.Infra.BaseMkConfig):
            return r[m.Infra.BaseMkConfig].ok(settings)
        try:
            normalized = m.Infra.BaseMkConfig.model_validate(settings)
            return r[m.Infra.BaseMkConfig].ok(normalized)
        except c.EXC_TYPE_VALIDATION as exc:
            return r[m.Infra.BaseMkConfig].fail_op(
                "base.mk configuration validation", exc
            )

    @override
    def execute(self) -> p.Result[str]:
        """Execute."""
        return self.render_all()

    def render_all(self, settings: m.Infra.BaseMkConfig | None = None) -> p.Result[str]:
        """Render the canonical standalone Makefile through the codegen SSOT."""
        active_config = settings or self.default_config()
        codegen = config.Infra.codegen
        entry = next(
            (
                candidate
                for candidate in codegen.templates.entries
                if candidate.destination == c.Infra.MAKEFILE_FILENAME
            ),
            None,
        )
        if entry is None:
            return r[str].fail(
                "Makefile template is missing from codegen configuration"
            )
        context = m.Infra.MakefileRenderSpec(
            dist=active_config.project_name,
            make_profile=c.Infra.MakeProfile.STANDALONE,
            workspace_root_rel=".",
            workspace_members=(),
            workspace_repositories=(),
            workspace_content_only=(),
            uv_link_mode=codegen.toolchain.uv_link_mode,
            make=codegen.make,
            extra_verbs=(),
            script_dispatch=None,
            makefile_custom_include=c.Infra.MAKEFILE_CUSTOM_INCLUDE,
            orchestrated_verbs=tuple(c.Infra.ORCHESTRATED_PROJECT_VERBS),
            workspace_cli_group=c.Infra.CLI_GROUP_WORKSPACE,
            project_selection_conflict_error=c.Infra.PROJECT_SELECTION_CONFLICT_ERROR,
            mypy_memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            mypy_timeout_seconds=c.Infra.MYPY_TIMEOUT_SECONDS_DEFAULT,
            mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
            mypy_signal_exit_offset=c.Infra.PROCESS_SIGNAL_EXIT_OFFSET,
            prlimit_command=c.Infra.PRLIMIT_COMMAND,
            prlimit_address_space_option=c.Infra.PRLIMIT_ADDRESS_SPACE_OPTION,
            timeout_command=c.Infra.TIMEOUT_COMMAND,
            timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
        )
        templates_root = (_templates_dir() / codegen.templates.root).resolve()
        return u.Cli.template_render(templates_root / entry.source, context)


__all__: list[str] = ["FlextInfraBaseMkTemplateRenderer"]
