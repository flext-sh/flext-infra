"""Phase: mirror every config-owned tool table whose shape is pure policy data.

pytest, mypy, pydantic-mypy, codespell, hatch metadata, tomlsort, yamlfix,
deptry namespaces, vulture, and coverage share one behavior: each table is a
direct projection of ``config.Infra.tooling``. One declarative phase set owns
them so no per-tool class re-implements the same apply contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, deps, m, p, t, workspace
from flext_infra._utilities import (
    FlextInfraUtilitiesNativeTooling,
    FlextInfraUtilitiesProjectDiscovery,
)
from flext_infra._utilities._docs import FlextInfraUtilitiesDocsScopeProjects
from flext_infra._utilities._pyproject.conform import (
    FlextInfraUtilitiesPyprojectConform,
)
from flext_infra._utilities._pyproject.toml_phases import (
    FlextInfraUtilitiesPyprojectTomlPhases,
)
from flext_infra._utilities._rope.rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraToolTablesPhase:
    """Apply the config-owned policy tables to one normalized payload."""

    def __init__(
        self,
        tool_config: m.Infra.ToolConfigDocument,
        *,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> None:
        """Capture the canonical tooling document projected into each table."""
        self._tool_config = tool_config
        self._codegen = codegen

    @staticmethod
    def first_party_namespaces(
        *,
        path: Path,
        planned_sources: Sequence[Path] = (),
        source_project: p.Infra.RopeProject | None = None,
    ) -> Sequence[str]:
        """Compose Ruff's import-order families over owned target namespaces.

        Returns:
            The sorted namespaces in the declared import-order family.

        """
        return sorted({
            *FlextInfraToolTablesPhase.deptry_first_party_namespaces(
                path=path,
                planned_sources=planned_sources,
                source_project=source_project,
            ),
            *FlextInfraToolTablesPhase._workspace_project_namespaces(
                path, source_project=source_project
            ),
        })

    @staticmethod
    def deptry_first_party_namespaces(
        *,
        path: Path,
        planned_sources: Sequence[Path] = (),
        repository_namespace_packages: Sequence[str] = (),
        source_project: p.Infra.RopeProject | None = None,
    ) -> Sequence[str]:
        """Derive only packages owned by this target's production tree.

        Peer distributions remain dependencies even when their source checkouts
        share a superproject or their packages are installed in the same runtime.

        Returns:
            Target-local live and planned production namespaces.

        """
        src_dir = path / c.Infra.DEFAULT_SRC_DIR
        planned_parts = (
            source.relative_to(src_dir).parts
            for source in planned_sources
            if source.is_relative_to(src_dir)
        )
        planned_packages = {
            parts[0]
            for parts in planned_parts
            if len(parts) > 1 and parts[0].isidentifier()
        }
        return sorted({
            *FlextInfraUtilitiesRopeSource.discover_first_party_namespaces(
                path, source_project=source_project
            ),
            *planned_packages,
            *repository_namespace_packages,
        })

    @staticmethod
    def _workspace_project_namespaces(
        project_dir: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Sequence[str]:
        """Discover child project packages when generating repository root settings.

        Returns:
            The resulting ``Sequence[str]``.

        Raises:
            ValueError: If ``discovered.failure``.

        """
        if not (
            (project_dir / c.PYPROJECT_FILENAME).is_file()
            if source_project is None
            else source_project.source_query(
                project_dir / c.PYPROJECT_FILENAME, "isfile"
            )
        ):
            return ()
        # Topology law: only a repository that declares .gitmodules composes
        # child projects; a standalone checkout has none to discover.
        if not (
            (project_dir / c.Infra.GITMODULES).is_file()
            if source_project is None
            else source_project.source_query(project_dir / c.Infra.GITMODULES, "isfile")
        ):
            return ()
        if source_project is not None:
            return sorted({
                namespace.replace("-", "_")
                for project in (
                    FlextInfraUtilitiesProjectDiscovery.discover_project_roots
                )(project_dir, source_project=source_project)
                if project != project_dir
                for namespace in (
                    FlextInfraUtilitiesPyprojectConform.project_package_name(
                        project, source_project=source_project
                    ),
                )
                if namespace and namespace.replace("-", "_").isidentifier()
            })
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            project_dir,
            allow_unprovisioned_members=True,
        )
        if observed.failure:
            raise ValueError(observed.error)
        if observed.value.repository.role != c.Infra.MakeProfile.WORKSPACE:
            return ()
        discovered = FlextInfraUtilitiesDocsScopeProjects.discover_projects(project_dir)
        if discovered.failure:
            # A real discovery error (malformed pyproject, IO) must never
            # silently generate root Ruff settings with an empty child-package
            # list — that conformed artifact would drift from the workspace
            # with no signal. Mirrors _workspace_exclusion_globs fail-loud.
            raise ValueError(
                discovered.error or "workspace project discovery is unavailable",
            )
        return sorted({
            project.package_name.replace("-", "_")
            for project in discovered.value
            if (
                project.package_name
                and project.package_name.replace("-", "_").isidentifier()
                and project.declared_subproject
            )
        })

    @staticmethod
    def _native_phase(tool: str, payload: t.JsonDict) -> m.Infra.DepsToml.PhaseConfig:
        """Replace a governed native table through the shared TOML primitive.

        Returns:
            A phase whose image is the complete elected declared table.

        """
        path = tool.split(".")
        return m.Infra.DepsToml.PhaseConfig(
            name=tool,
            table_path=tuple(path[:-1]),
            operations=(m.Infra.DepsToml.SetOp(key=path[-1], value=payload),),
        )

    def _mypy_phase(
        self, mypy_search_paths: Sequence[str]
    ) -> m.Infra.DepsToml.PhaseConfig:
        """Combine native options with the Mypy execution policy.

        Returns:
            The complete Mypy table, preserving option and plugin array order.

        """
        policy = self._tool_config.tools.mypy
        payload = FlextInfraUtilitiesNativeTooling.native_tool_configuration(
            self._tool_config, c.Infra.MYPY
        )
        payload[c.Infra.PYTHON_VERSION_UNDERSCORE] = (
            self._codegen.toolchain.python_version
        )
        payload["mypy_path"] = list(mypy_search_paths)
        # One exclusion owner: the codegen artifact registry, as Mypy's regex.
        payload["exclude"] = FlextInfraUtilitiesNativeTooling.native_exclude_regex(
            self._codegen.analyzer_exclude_globs
        )
        if policy.ruling_disable_error_codes:
            payload["disable_error_code"] = list(policy.ruling_disable_error_codes)
        payload["overrides"] = [
            {
                "module": list(entry.modules),
                **FlextInfraUtilitiesNativeTooling.configuration_pairs(entry.settings),
            }
            for entry in policy.overrides
        ]
        return self._native_phase(c.Infra.MYPY, payload)

    def _pytest_phase(self) -> m.Infra.DepsToml.PhaseConfig:
        """Project native pytest options and its shared operational vocabulary.

        Returns:
            The complete pytest table with derived runtime declarations.

        """
        policy = self._tool_config.tools.pytest
        payload = FlextInfraUtilitiesNativeTooling.native_tool_configuration(
            self._tool_config, c.Infra.PYTEST
        )
        options = u.Cli.toml_mapping_ensure_table(payload, c.Infra.INI_OPTIONS)
        options[c.Infra.FLEXT_SLOW_TIMEOUT_SECONDS] = str(policy.slow_timeout_seconds)
        options[c.Infra.MARKERS] = list(policy.standard_markers)
        # fixture_tree materializes scenario trees from the one declared root
        # (ADR-028 point 6); the flext-tests plugin registers and reads the key.
        (scenario_root,) = self._codegen.exclusions.scenario_data_roots
        options[c.Infra.FLEXT_FIXTURE_TREES_ROOT] = scenario_root
        # Additive collection exclusions retain pytest's native recursion
        # defaults and any elected project-specific norecursedirs policy.
        options["addopts"] = list(
            dict.fromkeys((
                *FlextInfraUtilitiesNativeTooling.native_tool_strings(
                    self._tool_config, "pytest.ini_options", "addopts"
                ),
                *(
                    f"--ignore={root}"
                    for root in self._codegen.exclusions.scenario_data_roots
                ),
            ))
        )
        # Test plugins read the Make CI context through these ini keys, so no
        # test runtime imports flext-infra to learn it.
        ci = self._codegen.make.ci
        options[c.Infra.FLEXT_MAKE_CI_VARIABLE] = ci.variable
        options[c.Infra.FLEXT_MAKE_CI_VALUE] = ci.value
        return self._native_phase(c.Infra.PYTEST, payload)

    def _vulture_phase(self, path: Path) -> m.Infra.DepsToml.PhaseConfig:
        """Filter declared native roots through the workspace participation owner.

        Returns:
            The complete Vulture table with only participating roots.

        """
        payload = FlextInfraUtilitiesNativeTooling.native_tool_configuration(
            self._tool_config, "vulture"
        )
        excluded = self.excluded_roots(path)
        paths = FlextInfraUtilitiesNativeTooling.native_tool_strings(
            self._tool_config,
            "vulture",
            "paths",
        )
        payload["paths"] = [root for root in paths if root not in excluded]
        return self._native_phase("vulture", payload)

    def _deptry_phase(
        self, path: Path, repository_namespace_packages: Sequence[str]
    ) -> m.Infra.DepsToml.PhaseConfig:
        """Add target-owned namespaces to the elected native options.

        Returns:
            The complete Deptry table with first-party classification.

        """
        payload = FlextInfraUtilitiesNativeTooling.native_tool_configuration(
            self._tool_config, c.Infra.DEPTRY
        )
        payload[c.Infra.KNOWN_FIRST_PARTY_UNDERSCORE] = list(
            self.deptry_first_party_namespaces(
                path=path,
                repository_namespace_packages=repository_namespace_packages,
            )
        )
        return self._native_phase(c.Infra.DEPTRY, payload)

    @staticmethod
    def excluded_roots(project_dir: Path) -> frozenset[str]:
        """First segments of the workspace manifest's declared non-participants.

        A workspace that retired a tree declares it once in its manifest
        (``exclusions``, ``content_only`` or ``external_dependency_paths``);
        every root-scoped projection (vulture paths, ruff src/namespace-
        packages) filters on this declared set instead of
        probing the disk, which oscillates between the deps pass and the
        root-materializing gen pass. An invalid manifest fails loud.

        Returns:
            The resulting ``frozenset[str]``.

        """
        return frozenset(
            Path(path).parts[0]
            for path in (
                FlextInfraUtilitiesProjectDiscovery.repository_nonparticipant_paths(
                    project_dir.resolve()
                )
            )
        )

    def _phases(
        self,
        *,
        path: Path,
        repository_namespace_packages: Sequence[str],
        mypy_search_paths: Sequence[str],
    ) -> Sequence[m.Infra.DepsToml.PhaseConfig]:
        """Compose declarative tables and the registered semantic owners.

        Returns:
            Native table replacements followed by topology and runtime policy.

        Raises:
            KeyError: If a declared tool is missing from the registry.

        """
        declared_tables = self._tool_config.settings
        tables = tuple(
            table
            for table in sorted(declared_tables)
            if table.partition(".")[0] not in self._tool_config.derived_tool_roots
            and not any(
                ".".join(table.split(".")[:length]) in declared_tables
                for length in range(1, len(table.split(".")))
            )
        )
        native_roots = {
            root: FlextInfraUtilitiesNativeTooling.native_tool_configuration(
                self._tool_config, root
            )
            for root in sorted({table.partition(".")[0] for table in tables})
        }
        native_phases: list[m.Infra.DepsToml.PhaseConfig] = []
        for table in tables:
            path_parts = table.split(".")
            image = native_roots[path_parts[0]]
            for segment in path_parts[1:]:
                nested = image.get(segment)
                if not isinstance(nested, dict):
                    msg = f"Declared native tool table is unavailable: {table}"
                    raise KeyError(msg)
                image = nested
            native_phases.append(self._native_phase(table, image))
        return (
            *native_phases,
            self._mypy_phase(mypy_search_paths),
            self._pytest_phase(),
            self._vulture_phase(path),
            self._deptry_phase(path, repository_namespace_packages),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        path: Path,
        repository_namespace_packages: Sequence[str] = (),
        mypy_search_paths: Sequence[str] | None = None,
    ) -> Sequence[str]:
        """Apply every policy table to one normalized payload.

        Returns:
            The resulting ``Sequence[str]``.

        """
        elected_mypy_paths = (
            deps.FlextInfraExtraPathsManager(
                repository_root=path.parent
            ).mypy_search_paths(project_dir=path.parent)
            if mypy_search_paths is None
            else mypy_search_paths
        )
        return FlextInfraUtilitiesPyprojectTomlPhases.apply_toml_phases(
            payload,
            *self._phases(
                path=path.parent,
                repository_namespace_packages=repository_namespace_packages,
                mypy_search_paths=elected_mypy_paths,
            ),
        )


__all__: list[str] = ["FlextInfraToolTablesPhase"]
