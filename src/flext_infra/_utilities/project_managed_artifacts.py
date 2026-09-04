"""Load and compose project-owned managed-artifact configuration."""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path

from flext_core import r
from flext_cli import u
from flext_infra import c, config, m, p, t


class FlextInfraUtilitiesProjectManagedArtifacts:
    """Single owner for ``ManagedArtifacts`` across ``config/*.yaml`` files."""

    @staticmethod
    def validate_mise_tool_selectors(
        selectors: t.StrSequence, *, source: Path
    ) -> p.Result[bool]:
        """Reject alternate distributions of fleet-owned tool identities."""
        toolchain = config.Infra.codegen.toolchain
        protected_tools = tuple(
            (owner, getattr(toolchain, owner))
            for owner in toolchain.protected_mise_tools
        )
        for selector in selectors:
            for owner, tool in protected_tools:
                if not any(
                    fnmatchcase(selector, pattern) for pattern in tool.selector_patterns
                ):
                    continue
                if selector == tool.selector:
                    break
                return r[bool].fail(
                    "project Mise selector declares an alternate distribution "
                    f"for fleet identity {owner!r}: {selector!r} in "
                    f"{source}; canonical selector is {tool.selector!r}"
                )
        return r[bool].ok(True)

    @staticmethod
    def load_project_managed_artifacts(
        project_dir: Path,
    ) -> p.Result[m.Infra.ProjectManagedArtifactsResolution]:
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
        mise_tools: dict[str, m.Infra.ProjectMiseTool] = {}
        mise_sources: dict[str, Path] = {}
        gitignore_patterns: list[str] = []
        fleet_platforms = frozenset(config.Infra.codegen.toolchain.mise_lock_platforms)
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
            for pattern in artifacts.Gitignore.patterns:
                if pattern not in gitignore_patterns:
                    gitignore_patterns.append(pattern)
            if document.source_path is None:
                return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                    "project configuration document has no source path"
                )
            source = Path(document.source_path)
            for selector, tool in artifacts.Mise.tools.items():
                previous = mise_sources.get(selector)
                if previous is not None:
                    return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                        "duplicate project Mise selector "
                        f"{selector!r}: {previous} and {source}"
                    )
                unknown = sorted(set(tool.platforms or ()) - fleet_platforms)
                if unknown:
                    return r[m.Infra.ProjectManagedArtifactsResolution].fail(
                        f"project Mise selector {selector!r} in {source} declares "
                        f"platforms outside the fleet lock platforms: {unknown}"
                    )
                mise_tools[selector] = tool
                mise_sources[selector] = source
        artifacts = m.Infra.ProjectManagedArtifactsConfig(
            Ruff=m.Infra.ProjectRuffConfig(
                per_file_ignores={
                    pattern: tuple(sorted(rules))
                    for pattern, rules in sorted(ruff_ignores.items())
                }
            ),
            Mise=m.Infra.ProjectMiseConfig(tools=dict(sorted(mise_tools.items()))),
            Gitignore=m.Infra.ProjectGitignoreConfig(
                patterns=tuple(gitignore_patterns)
            ),
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
        resolved = cls.load_project_managed_artifacts(project_dir)
        if resolved.failure:
            return r[str].fail(resolved.error or "project artifact load failed")
        local_tools = resolved.value.artifacts.Mise.tools
        if not local_tools:
            return r[str].ok(rendered)
        for selector in local_tools:
            selector_validation = cls.validate_mise_tool_selectors(
                (selector,), source=resolved.value.mise_tool_sources[selector]
            )
            if selector_validation.failure:
                return r[str].fail(
                    selector_validation.error
                    or "project Mise identity validation failed"
                )
        doc = u.Cli.toml_parse_text(rendered)
        if doc is None:
            return r[str].fail("canonical .mise.toml template is invalid")
        tools = u.Cli.toml_ensure_table(doc, "tools")
        for selector, tool in local_tools.items():
            if selector in tools:
                source = resolved.value.mise_tool_sources[selector]
                return r[str].fail(
                    "project Mise selector collides with fleet tool "
                    f"{selector!r}: global .mise.toml template and {source}"
                )
            tools[selector] = tool.version
        return r[str].ok(u.Cli.toml_dumps(doc))

    @classmethod
    def lock_platform_exclusions(
        cls, project_dir: Path
    ) -> p.Result[t.MappingKV[str, frozenset[str]]]:
        """Platforms each project-owned selector cannot lock, derived from its declaration."""
        resolved = cls.load_project_managed_artifacts(project_dir)
        if resolved.failure:
            return r[t.MappingKV[str, frozenset[str]]].fail(
                resolved.error or "project artifact load failed"
            )
        fleet_platforms = frozenset(config.Infra.codegen.toolchain.mise_lock_platforms)
        # Absent platforms: the tool locks on every fleet platform. A declared
        # tuple (possibly empty, for backends without per-platform assets)
        # records exactly the platforms the lock may carry.
        exclusions = {
            selector: fleet_platforms - frozenset(tool.platforms)
            for selector, tool in resolved.value.artifacts.Mise.tools.items()
            if tool.platforms is not None
        }
        return r[t.MappingKV[str, frozenset[str]]].ok(exclusions)


__all__: tuple[str, ...] = ("FlextInfraUtilitiesProjectManagedArtifacts",)
