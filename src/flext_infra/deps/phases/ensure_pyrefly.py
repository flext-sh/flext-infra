"""Phase: Ensure standard Pyrefly configuration for max-strict typing.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u

if TYPE_CHECKING:
    from flext_infra.deps import FlextInfraExtraPathsManager


class FlextInfraEnsurePyreflyConfigPhase:
    """Ensure standard Pyrefly configuration for max-strict typing."""

    def __init__(
        self,
        tool_config: p.Infra.ToolConfigDocument,
        *,
        codegen: p.Infra.CodegenConfigSpec,
    ) -> None:
        """Store tool configuration used when enforcing pyrefly project settings."""
        self._tool_config = tool_config
        self._codegen = codegen

    def _phase(
        self,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None,
    ) -> p.Infra.PhaseConfig:
        """Build the canonical pyrefly phase definition.

        Returns:
            The resulting ``m.Infra.DepsToml.PhaseConfig``.

        """
        path_rules = self._tool_config.tools.pyrefly.path_rules
        project_dir = context.project_dir
        declared_python_dirs = context.declared_python_dirs
        if project_dir is not None and paths_manager is not None:
            expected_search: Sequence[str] = paths_manager.pyrefly_search_paths(
                project_dir=project_dir,
            )
            expected_includes: Sequence[str] = paths_manager.pyrefly_project_includes(
                project_dir=project_dir,
                is_root=context.is_root,
            )
        else:
            expected_search = [path_rules.source_dir]
            expected_includes = [f"{path_rules.source_dir}/**/*.py*"]
        # Keep pre-write Pyrefly scope identical to the first
        # post-write discovery without fabricating directories on disk.
        if context.declared_python_dirs_are_complete:
            declared_import_roots = (
                (path_rules.source_dir,)
                if path_rules.source_dir in declared_python_dirs
                else ()
            )
            # Why (fleet-wide fix): sorted({...}) places "."
            # before "src" (ASCII '.' < 's'), so pyrefly resolves every
            # module twice (pkg.X via src AND src.pkg.X via "."),
            # producing phantom bad-argument-type errors. The declared
            # source import root must stay first; everything else (typically
            # ".", for tests.* resolution) sorts after it.
            merged_search = {
                *expected_search,
                *path_rules.project_shared_search_paths,
                path_rules.project_root,
            }
            if not declared_import_roots:
                merged_search.discard(path_rules.source_dir)
            merged_search.difference_update(declared_import_roots)
            expected_search = [*declared_import_roots, *sorted(merged_search)]
            # Analysis roots belong in
            # project-includes; only import roots belong in search-path.
            expected_includes = tuple(
                f"{directory}/**/*.py*" for directory in declared_python_dirs
            )
        options = u.Infra.native_tool_configuration(self._tool_config, c.Infra.PYREFLY)
        options.update({
            c.Infra.PYTHON_VERSION_HYPHEN: self._codegen.toolchain.python_version,
            # Import search order is semantic and stays with the path owner.
            c.Infra.SEARCH_PATH: list[t.JsonValue](expected_search),
            c.Infra.PROJECT_INCLUDES: list[t.JsonValue](sorted(expected_includes)),
            c.Infra.PROJECT_EXCLUDES: list[t.JsonValue](
                u.Infra.pyrefly_project_excludes(
                    u.Infra.native_tool_strings(
                        self._tool_config,
                        c.Infra.PYREFLY,
                        c.Infra.PROJECT_EXCLUDES,
                    ),
                    codegen=self._codegen,
                )
            ),
        })
        # Operator-authorized global axioms render as ignore in every
        # project; the declaration lives once, in tools.pyrefly.
        errors = u.Cli.toml_mapping_ensure_table(options, c.Infra.SUB_CONFIG_ERRORS)
        for rule in self._tool_config.tools.pyrefly.ruling_disabled_rules:
            errors[rule] = "ignore"
        # Authorized path exceptions scope their rule levels through
        # glob-matched sub-configs relative to this file.
        sub_configs: list[t.JsonValue] = [
            {
                c.Infra.SUB_CONFIG_MATCHES: root,
                c.Infra.SUB_CONFIG_ERRORS: dict(levels),
            }
            for root, levels in u.Infra.diagnostic_exception_levels(
                self._tool_config,
                c.Infra.PYREFLY,
                context.repository_root if context.is_root else project_dir,
            )
        ]
        if sub_configs:
            options[c.Infra.SUB_CONFIG] = sub_configs
        toml = m.Infra.DepsToml
        return toml.PhaseConfig(
            name="pyrefly",
            operations=(toml.SetOp(key=c.Infra.PYREFLY, value=options),),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> Sequence[str]:
        """Apply canonical pyrefly settings to one normalized payload.

        Returns:
            The resulting ``Sequence[str]``.

        """
        return u.Infra.apply_toml_phases(
            payload,
            self._phase(
                context=context,
                paths_manager=paths_manager,
            ),
        )

    def render_source(
        self,
        source: str,
        *,
        context: p.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None = None,
    ) -> p.Result[str]:
        """Project only the analyzer table, preserving the rest of the document.

        The caller injects the analyzer inputs its full modernization owns.

        Returns:
            TOML with the same configuration emitted by full modernization.

        """
        parsed = u.Cli.toml_mapping_from_text_result(source)
        if parsed.failure:
            return r[str].from_failure(parsed)
        payload: t.MutableJsonMapping = dict(parsed.value)
        self.apply_payload(payload, context=context, paths_manager=paths_manager)
        document = u.Cli.toml_parse_text(source)
        if document is None:
            return r[str].fail(
                "validated TOML could not be parsed for round-trip editing"
            )
        tool = u.Cli.toml_ensure_table(document, c.Infra.TOOL)
        expected = u.Cli.toml_mapping_path(payload, (c.Infra.TOOL, c.Infra.PYREFLY))
        if expected is None:
            return r[str].fail("Pyrefly projection produced no analyzer table")
        ordered = u.Cli.json_dumps(u.normalize_to_json_value(expected), sort_keys=True)
        if ordered.failure:
            return r[str].from_failure(ordered)
        # This table is generated in full. Replacing its value also normalizes
        # nested object keys while retaining semantic list order.
        tool[c.Infra.PYREFLY] = u.json_mapping_adapter().validate_json(ordered.value)
        return r[str].ok(u.Cli.toml_dumps(document))


__all__: list[str] = ["FlextInfraEnsurePyreflyConfigPhase"]
