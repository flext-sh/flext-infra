"""Load and compose project-owned managed-artifact configuration."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import c, m, p, u


class FlextInfraUtilitiesProjectManagedArtifacts:
    """Single owner for ``ManagedArtifacts`` across ``config/*.yaml`` files."""

    @staticmethod
    def load(project_dir: Path) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
        """Load every YAML and compose each artifact by its declared policy."""
        config_dir = project_dir / c.CONFIG_DIR_NAME
        empty = m.Infra.ProjectManagedArtifactsResolution(
            artifacts=m.Infra.ProjectManagedArtifactsConfig(), mise_tool_sources={}
        )
        if not config_dir.is_dir():
            return r[m.Infra.ProjectManagedArtifactsResolution].ok(empty)
        loaded = u.Cli.config_load_dir(config_dir)
        if loaded.failure:
            return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                loaded.error or f"project config load failed: {config_dir}"
            )
        ruff_ignores: dict[str, set[str]] = {}
        mise_tools: dict[str, str] = {}
        mise_sources: dict[str, Path] = {}
        for document in loaded.value.values():
            managed = document.data.get("ManagedArtifacts")
            if not managed:
                continue
            project_config = m.Infra.ProjectConfigDocument.model_validate({
                "ManagedArtifacts": managed
            })
            artifacts = project_config.ManagedArtifacts
            for pattern, rules in artifacts.Ruff.per_file_ignores.items():
                ruff_ignores.setdefault(pattern, set()).update(rules)
            if document.source_path is None:
                return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                    "project configuration document has no source path"
                )
            source = Path(document.source_path)
            for selector, version in artifacts.Mise.tools.items():
                previous = mise_sources.get(selector)
                if previous is not None:
                    return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                        "duplicate project Mise selector "
                        f"{selector!r}: {previous} and {source}"
                    )
                mise_tools[selector] = version
                mise_sources[selector] = source
        artifacts = m.Infra.ProjectManagedArtifactsConfig(
            Ruff=m.Infra.ProjectRuffConfig(
                per_file_ignores={
                    pattern: tuple(sorted(rules))
                    for pattern, rules in sorted(ruff_ignores.items())
                }
            ),
            Mise=m.Infra.ProjectMiseConfig(tools=dict(sorted(mise_tools.items()))),
        )
        return r[m.Infra.ProjectManagedArtifactsResolution].ok(
            m.Infra.ProjectManagedArtifactsResolution(
                artifacts=artifacts,
                mise_tool_sources=dict(sorted(mise_sources.items())),
            )
        )

    @classmethod
    def compose_mise_toml(cls, project_dir: Path, rendered: str) -> p.Result[str]:
        """Add local tools through TOML types and reject global collisions."""
        resolved = cls.load(project_dir)
        if resolved.failure:
            return r[str].fail(resolved.error or "project artifact load failed")
        local_tools = resolved.value.artifacts.Mise.tools
        if not local_tools:
            return r[str].ok(rendered)
        doc = u.Cli.toml_parse_text(rendered)
        if doc is None:
            return r[str].fail("canonical .mise.toml template is invalid")
        tools = u.Cli.toml_ensure_table(doc, "tools")
        for selector, version in local_tools.items():
            if selector in tools:
                source = resolved.value.mise_tool_sources[selector]
                return r[str].fail(
                    "project Mise selector collides with fleet tool "
                    f"{selector!r}: global .mise.toml template and {source}"
                )
            tools[selector] = version
        return r[str].ok(u.Cli.toml_dumps(doc))


__all__: tuple[str, ...] = ("FlextInfraUtilitiesProjectManagedArtifacts",)
