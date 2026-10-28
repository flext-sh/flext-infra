"""Phase: Ensure standard Pyrefly configuration for max-strict typing.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from flext_infra.deps import FlextInfraExtraPathsManager


class FlextInfraEnsurePyreflyConfigPhase:
    """Ensure standard Pyrefly configuration for max-strict typing."""

    def __init__(
        self,
        tool_config: m.Infra.ToolConfigDocument,
        *,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Store tool configuration used when enforcing pyrefly project settings."""
        self._tool_config = tool_config
        self._codegen = codegen

    def _phase(
        self,
        *,
        context: m.Infra.PyprojectAnalyzerContext,
        paths_manager: FlextInfraExtraPathsManager | None,
    ) -> m.Infra.DepsToml.PhaseConfig:
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
        toml = m.Infra.DepsToml
        return toml.PhaseConfig(
            name="pyrefly",
            operations=(toml.SetOp(key=c.Infra.PYREFLY, value=options),),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        context: m.Infra.PyprojectAnalyzerContext,
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


__all__: list[str] = ["FlextInfraEnsurePyreflyConfigPhase"]
