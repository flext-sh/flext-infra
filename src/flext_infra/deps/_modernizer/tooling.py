"""Render one canonical pyproject and resolve its typed template context.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from os.path import relpath
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.deps import FlextInfraExtraPathsManager
from flext_infra.deps.phases import FlextInfraToolTablesPhase

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraPyprojectModernizerTooling:
    """Conform in-memory pyproject sources and derive template runtime values."""

    if TYPE_CHECKING:
        # Members supplied by the composed modernizer service.
        @property
        def root(self) -> Path: ...

        repository_root: Path

        def _project_kind(
            self,
            path: Path,
            payload: t.JsonMapping,
            project_kind: str | None,
        ) -> str: ...

        @staticmethod
        def _read_document_state(
            path: Path,
            *,
            source: str | None = None,
        ) -> p.Result[m.Infra.PyprojectDocumentState]: ...

        def _apply_document_phases(
            self,
            state: m.Infra.PyprojectDocumentState,
            *,
            canonical_dev: t.StrSequence,
            topology: m.Infra.PyprojectDeclaredTopology,
        ) -> t.StrSequence: ...

        def _render_document_state(
            self,
            state: m.Infra.PyprojectDocumentState,
            changes: t.StrSequence,
            *,
            skip_comments: bool,
            format_source: bool = True,
            preserve_layout: bool = False,
        ) -> p.Result[t.StrSequence]: ...

    def conform_source(
        self,
        source: str,
        *,
        path: Path,
        format_source: bool = True,
        topology: m.Infra.PyprojectDeclaredTopology,
    ) -> p.Result[str]:
        """Return one canonical pyproject using the same phases as workspace apply.

        An atomic scaffold declares future roots before they exist on disk.
        Pyright combines those declarations with the canonical inventory of
        existing owned Python sources; a scaffold declaration cannot hide them.

        Returns:
            One canonical pyproject using the same phases as workspace apply.

        """
        conformed = self._conformed_document_state(source, path=path, topology=topology)
        if conformed.failure:
            return r[str].from_failure(conformed)
        state, changes = conformed.value
        rendered = self._render_document_state(
            state,
            changes,
            skip_comments=False,
            format_source=format_source,
        )
        if rendered.failure:
            return r[str].from_failure(rendered)
        return r[str].ok(state.rendered)

    def _conformed_document_state(
        self,
        source: str,
        *,
        path: Path,
        topology: m.Infra.PyprojectDeclaredTopology,
    ) -> p.Result[t.Pair[m.Infra.PyprojectDocumentState, t.StrSequence]]:
        """Read and apply canonical phases before a consumer chooses rendering.

        Returns:
            The validated document state and its phase changes.

        """
        result_type = r[t.Pair[m.Infra.PyprojectDocumentState, t.StrSequence]]
        state = self._read_document_state(path, source=source)
        if state.failure:
            return result_type.from_failure(state)
        canonical_dev: p.Result[t.StrSequence] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            u.Infra.canonical_dev_dependencies_from_payload(state.value.payload),
        )
        if canonical_dev.failure:
            return result_type.fail_op(
                "pyproject model validation", canonical_dev.error
            )
        changes = self._apply_document_phases(
            state.value,
            canonical_dev=canonical_dev.value,
            topology=topology,
        )
        return result_type.ok((state.value, changes))

    def resolve_tooling_context(
        self,
        request: m.Infra.ToolingContextRequest,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[m.Infra.ToolingRuntimeContext]:
        """Resolve typed Jinja values from the seed conformed to one topology.

        Returns:
            The resulting ``p.Result[m.Infra.ToolingRuntimeContext]``.

        """
        result_type = r[m.Infra.ToolingRuntimeContext]
        conformed = self._conformed_seed_tools(
            request.path,
            request.topology,
            request.scaffold_project,
            (request.project_name, request.package_name),
            (
                request.runtime_dependency_overlay,
                request.declared_project_dependencies,
            ),
        )
        if conformed.failure:
            return result_type.from_failure(conformed)
        tools, payload = conformed.value
        declared_python_dirs = request.topology.declared_python_dirs
        project_dir = request.path.parent
        raw_environments = u.Cli.json_as_sequence(
            tools.pyright.get("executionEnvironments"),
        )
        # Seed for a project whose analyzer paths were never synced yet. The
        # manager derives from directories that EXIST, so before src/ is
        # written it returns []. Writing that empty list made the next plan
        # re-derive ['src', '.'], so apply never reached its fixed point.
        # Prefer the DECLARED roots, exactly like the ensure-pyrefly phase.
        seed_manager = FlextInfraExtraPathsManager(repository_root=self.root)
        declared_roots, derived_mypy_path = self._derived_paths(
            project_dir,
            declared_python_dirs,
            seed_manager,
        )
        scalar_keys = frozenset({
            c.Infra.EXCLUDE,
            c.Infra.IGNORE,
            c.Infra.INCLUDE,
            c.Infra.EXTRA_PATHS,
            "executionEnvironments",
            "venv",
            "venvPath",
        })
        environments = self._pyright_environments(raw_environments)
        if environments.failure:
            return result_type.fail_op(
                "validate pyright execution environment",
                environments.error,
            )
        # Absent analyzer-path keys fall back to the DERIVED value: they are
        # written by the analyzer-path sync, so a project that has not run it
        # yet has them missing, and an empty default would make the NEXT plan
        # re-derive them, so apply would never reach its fixed point.
        validated: p.Result[m.Infra.ToolingRuntimeContext] = u.validate_value(
            m.Infra.ToolingRuntimeContext,
            {
                "project_kind": self._project_kind(
                    request.path,
                    payload,
                    request.topology.project_kind,
                ),
                "first_party": tools.first_party,
                "deptry_first_party": tuple(
                    FlextInfraToolTablesPhase.deptry_first_party_namespaces(
                        path=project_dir,
                        planned_sources=tuple(request.planned_sources),
                        repository_namespace_packages=(
                            request.topology.repository_namespace_packages
                        ),
                    ),
                ),
                "mypy_path": (
                    derived_mypy_path
                    if declared_roots
                    else tools.mypy_path or derived_mypy_path
                ),
                "ruff_runtime_evaluated_base_classes": (
                    u.Infra.runtime_evaluated_base_classes(
                        project_dir,
                        request.planned_sources,
                        config.Infra.tooling.tools.ruff.lint.flake8_type_checking.runtime_evaluated_roots,
                        source_project=source_project,
                    )
                ),
                "pyrefly_search_path": tools.pyrefly_search_path,
                "pyrefly_project_includes": tools.pyrefly_project_includes,
                "pyrefly_project_excludes": u.Infra.pyrefly_project_excludes(
                    config.Infra.tooling.tools.pyrefly.project_exclude_globs,
                ),
                "pyright_exclude": tools.pyright.get(c.Infra.EXCLUDE, ()),
                "pyright_ignore": tools.pyright.get(c.Infra.IGNORE, ()),
                "pyright_include": tools.pyright.get(c.Infra.INCLUDE, ()),
                "pyright_extra_paths": (
                    tools.pyright.get(c.Infra.EXTRA_PATHS)
                    or seed_manager.pyright_extra_paths(
                        project_dir=project_dir,
                        is_root=True,
                    )
                    or declared_roots
                ),
                "pyright_settings": [
                    {
                        "name": c.Infra.VENV_NAME,
                        "value": request.environment_dir.name,
                    },
                    {
                        "name": c.Infra.VENV_PATH,
                        "value": self._relative_environment_parent(
                            request.environment_dir.parent, project_dir
                        ),
                    },
                    *(
                        {"name": key, "value": value}
                        for key, value in sorted(tools.pyright.items())
                        if key not in scalar_keys
                    ),
                ],
                "pyright_execution_environments": environments.value,
                "ruff_src": tools.ruff_src,
                "ruff_extend_exclude": tools.ruff_extend_exclude,
            },
        )
        if validated.failure:
            return result_type.fail_op(
                "tooling runtime context validation",
                validated.error,
            )
        return result_type.ok(validated.value)

    def _live_dev_dependencies(self, path: Path) -> p.Result[t.StrSequence]:
        """Collect the live dev groups plus canonical dev dependencies.

        Returns:
            The resulting merged live dev dependency sequence.

        """
        if not path.is_file():
            return r[t.StrSequence].ok(())
        live_state = self._read_document_state(path)
        if live_state.failure:
            return r[t.StrSequence].from_failure(live_state)
        groups = (
            u.Cli.toml_mapping_child(
                live_state.value.payload,
                c.Infra.DEPENDENCY_GROUPS,
            )
            or {}
        )
        group_dev = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            groups.get(str(c.Infra.DEV), []),
            strict=True,
        )
        if group_dev.failure:
            return r[t.StrSequence].fail_op(
                "validate live dev dependencies",
                group_dev.error,
            )
        return r[t.StrSequence].ok((
            *group_dev.value,
            *u.Infra.canonical_dev_dependencies_from_payload(
                live_state.value.payload,
            ),
        ))

    def _conformed_seed_tools(
        self,
        path: Path,
        topology: m.Infra.PyprojectDeclaredTopology,
        scaffold_project: m.Infra.ScaffoldProjectSpec,
        names: t.Pair[t.NonEmptyStr, t.NonEmptyStr],
        overlays: t.Pair[t.StrSequence, t.StrSequence],
    ) -> p.Result[t.Pair[m.Infra.ToolingConformedTools, t.MappingKV[str, t.JsonValue]]]:
        """Conform a seeded document and validate its derived tool tables.

        Returns:
            The resulting ``(tools, payload)`` pair of the conformed document.

        """
        project_name, package_name = names
        runtime_dependency_overlay, declared_project_dependencies = overlays
        result_type = r[
            t.Pair[m.Infra.ToolingConformedTools, t.MappingKV[str, t.JsonValue]]
        ]
        declaration = u.Infra.load_repository_declaration_inputs(path.parent)
        if declaration.failure:
            return result_type.from_failure(declaration)
        live_dev_result = self._live_dev_dependencies(path)
        if live_dev_result.failure:
            return result_type.from_failure(live_dev_result)
        live_dev = live_dev_result.value
        # Seed only the target's requirements before deriving analyzer ownership.
        seed: t.JsonMapping = {
            c.Infra.PROJECT: {
                c.Infra.NAME: project_name,
                c.Infra.DEPENDENCIES: [
                    *declared_project_dependencies,
                    *runtime_dependency_overlay,
                ],
            },
            c.Infra.DEPENDENCY_GROUPS: {
                c.Infra.DEV: list(
                    u.Infra.project_development_requirements(
                        scaffold_project,
                        distribution=project_name,
                        kind=declaration.value.spec.kind,
                        declared=live_dev,
                    )
                ),
            },
            c.Infra.TOOL: {"flext": {"docs": {"package_name": package_name}}},
        }
        # Atomic scaffolds provide validated future roots;
        # existing repositories keep filesystem discovery through empty ones.
        conformed = self._conformed_document_state(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(seed)),
            path=path,
            topology=topology,
        )
        if conformed.failure:
            return result_type.from_failure(conformed)
        state, _ = conformed.value
        payload = state.payload
        tools_result: p.Result[m.Infra.ToolingConformedTools] = u.validate_value(
            m.Infra.ToolingConformedTools,
            u.Cli.toml_mapping_child(payload, c.Infra.TOOL) or {},
        )
        if tools_result.failure:
            return result_type.fail_op(
                f"tooling resolution for {path}",
                tools_result.error,
            )
        return result_type.ok((tools_result.value, payload))

    @staticmethod
    def _derived_paths(
        project_dir: Path,
        declared_python_dirs: t.StrSequence,
        seed_manager: FlextInfraExtraPathsManager,
    ) -> t.Pair[t.StrSequence, t.StrSequence]:
        """Derive the declared or discovered analyzer search roots.

        Returns:
            The ``(declared_roots, mypy_path)`` pair.

        """
        path_rules = config.Infra.tooling.tools.pyrefly.path_rules
        # A shared search path belongs to the project when the scaffold
        # declares it or the tree already has it — the same rule
        # `pyrefly_search_paths` applies after the write.
        declared_roots: t.StrSequence = (
            (
                path_rules.source_dir,
                *(
                    shared
                    for shared in path_rules.project_shared_search_paths
                    if shared in declared_python_dirs or (project_dir / shared).is_dir()
                ),
                path_rules.project_root,
            )
            if path_rules.source_dir in declared_python_dirs
            else ()
        )
        # Why: partial disk discovery returns ('.',) before src/ exists, which is
        # truthy and blocked declared_roots ('src', '.'). Prefer declared roots
        # for search/mypy whenever scaffolding supplied them; pyright extras keep
        # discovery order (sorted {'.', 'src'}) so the first write matches sync.
        # mypy and pyrefly diverge: mypy enumerates
        # each search-path root as a package root, so roots that re-spell the
        # same files make it abort with source-file-found-twice; pyrefly
        # resolves first-match and needs the extra roots.
        derived_search_path: t.StrSequence = (
            declared_roots
            or seed_manager.pyrefly_search_paths(
                project_dir=project_dir,
                is_root=True,
            )
        )
        derived_mypy_path: t.StrSequence = (
            tuple(root for root in declared_roots if root != ".")
            if declared_roots
            else derived_search_path
        )
        return (declared_roots, derived_mypy_path)

    @staticmethod
    def _pyright_environments(
        raw_environments: t.SequenceOf[t.JsonValue],
    ) -> p.Result[t.SequenceOf[m.Infra.ToolingPyrightEnvironment]]:
        """Validate the conformed pyright environments and order them by root.

        Returns:
            The resulting validated environments sorted by root.

        """
        environment_keys = frozenset({"root", c.Infra.EXTRA_PATHS})
        environments: t.MutableSequenceOf[m.Infra.ToolingPyrightEnvironment] = []
        for raw_environment in raw_environments:
            environment = u.Cli.json_as_mapping(raw_environment)
            validated_environment: p.Result[m.Infra.ToolingPyrightEnvironment] = (
                u.validate_value(
                    m.Infra.ToolingPyrightEnvironment,
                    {
                        "root": environment.get("root"),
                        "extra_paths": environment.get(c.Infra.EXTRA_PATHS, ()),
                        "settings": [
                            {"name": key, "value": value}
                            for key, value in sorted(environment.items())
                            if key not in environment_keys
                        ],
                    },
                )
            )
            if validated_environment.failure:
                return r[t.SequenceOf[m.Infra.ToolingPyrightEnvironment]].from_failure(
                    validated_environment,
                )
            environments.append(validated_environment.value)
        # Why: the canonical pyproject layer orders the
        # [[tool.pyright.executionEnvironments]] array tables by root, so a
        # declared order (for example src, tests, skills) re-renders differently
        # from the formatted output and `make gen` reports drift forever.
        # Canonicalize by root here so the first write already matches the
        # formatted file and generation reaches its fixed point.
        return r[t.SequenceOf[m.Infra.ToolingPyrightEnvironment]].ok(
            sorted(environments, key=lambda environment: environment.root or ""),
        )

    @staticmethod
    def _relative_environment_parent(
        environment_parent: Path,
        project_dir: Path,
    ) -> str:
        """Return the environment parent relative to the consuming project.

        Returns:
            The project-relative environment path.

        Raises:
            ValueError: If the paths are not absolute or not relative.

        """
        if not environment_parent.is_absolute() or not project_dir.is_absolute():
            msg = "environment paths must be absolute"
            raise ValueError(msg)
        try:
            return relpath(environment_parent, project_dir)
        except ValueError as exc:
            msg = "environment parent is not relative to the project"
            raise ValueError(msg) from exc


__all__: list[str] = ["FlextInfraPyprojectModernizerTooling"]
