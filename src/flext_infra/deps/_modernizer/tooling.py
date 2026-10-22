"""Render one canonical pyproject and resolve its typed template context.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
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
            tool_config: m.Infra.ToolConfigDocument | None = None,
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
        tool_config: m.Infra.ToolConfigDocument | None = None,
    ) -> p.Result[t.Pair[m.Infra.PyprojectDocumentState, t.StrSequence]]:
        """Read and apply canonical phases before a consumer chooses rendering.

        Returns:
            The validated document state and its phase changes.

        """
        result_type = r[t.Pair[m.Infra.PyprojectDocumentState, t.StrSequence]]
        state = self._read_document_state(path, source=source)
        if state.failure:
            return result_type.from_failure(state)
        changes = self._apply_document_phases(
            state.value,
            canonical_dev=u.Infra.canonical_dev_dependencies_from_payload(
                state.value.payload
            ),
            topology=topology,
            tool_config=tool_config,
        )
        return result_type.ok((state.value, changes))

    def resolve_tooling_context(
        self,
        request: m.Infra.ToolingContextRequest,
        *,
        source_project: p.Infra.RopeProject | None = None,
        derive_runtime: bool = True,
    ) -> p.Result[m.Infra.ToolingRuntimeContext]:
        """Resolve typed Jinja values from the seed conformed to one topology.

        Returns:
            The resulting ``p.Result[m.Infra.ToolingRuntimeContext]``.

        """
        result_type = r[m.Infra.ToolingRuntimeContext]
        selected = u.Infra.load_tooling_inputs(
            request.path.parent, source_project=source_project
        )
        if selected.failure:
            return result_type.from_failure(selected)
        tool_config = selected.value.document
        conformed = self._conformed_seed_payload(
            request,
            tool_config=tool_config,
        )
        if conformed.failure:
            return result_type.from_failure(conformed)
        payload = conformed.value
        project_dir = request.path.parent
        deptry = u.Cli.toml_mapping_ensure_path(payload, (c.Infra.TOOL, "deptry"))
        deptry["known_first_party"] = list(
            FlextInfraToolTablesPhase.deptry_first_party_namespaces(
                path=project_dir,
                planned_sources=tuple(request.planned_sources),
                repository_namespace_packages=request.topology.repository_namespace_packages,
            ),
        )
        if derive_runtime:
            runtime = u.Cli.toml_mapping_ensure_path(
                payload,
                (
                    c.Infra.TOOL,
                    c.Infra.RUFF,
                    c.Infra.LINT_SECTION,
                    "flake8-type-checking",
                ),
            )
            runtime["runtime-evaluated-base-classes"] = list(
                u.Infra.runtime_evaluated_base_classes(
                    project_dir,
                    request.planned_sources,
                    tool_config.tools.ruff.lint.flake8_type_checking.runtime_evaluated_roots,
                    source_project=source_project,
                ),
            )
        return self.tooling_context_from_payload(
            payload,
            project_kind=self._project_kind(
                request.path, payload, request.topology.project_kind
            ),
            tool_config=tool_config,
            sources=selected.value.sources,
        )

    @staticmethod
    def tooling_configuration(
        tool_options: t.MappingKV[str, t.JsonMapping],
    ) -> p.Result[str]:
        """Serialize declared native tables through one ordered TOML boundary.

        Returns:
            Native TOML with recursively ordered keys and unchanged array order.

        """
        document = u.Cli.toml_document()
        for table_path, options in sorted(tool_options.items()):
            table = u.Cli.toml_ensure_path(
                document, (c.Infra.TOOL, *table_path.split("."))
            )
            for key, value in sorted(options.items()):
                table[key] = u.Cli.toml_item_from_json_value(value, sort_keys=True)
        return r[str].ok(u.Cli.toml_dumps(document))

    @classmethod
    def tooling_context_from_payload(
        cls,
        payload: t.MutableJsonMapping,
        *,
        project_kind: str,
        tool_config: m.Infra.ToolConfigDocument,
        sources: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.ToolingRuntimeContext]:
        """Project every declared table from one conformed native document.

        Returns:
            One synchronized configuration fragment and its native table views.

        """
        result_type = r[m.Infra.ToolingRuntimeContext]
        options: t.MutableMappingKV[str, t.JsonMapping] = {}
        for table_path in tool_config.settings:
            table = u.Cli.toml_mapping_path(
                payload, (c.Infra.TOOL, *table_path.split("."))
            )
            if table is None:
                error = ValueError(f"conformed tool table is absent: {table_path}")
                return result_type.fail(str(error), exception=error)
            options[table_path] = table
        configuration = cls.tooling_configuration(options)
        if configuration.failure:
            return result_type.from_failure(configuration)
        return result_type.ok(
            m.Infra.ToolingRuntimeContext(
                project_kind=project_kind,
                configuration=configuration.value,
                tool_options=options,
                sources=sources,
                document=tool_config,
            )
        )

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
            groups.get(c.Infra.DEV, []),
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

    def _conformed_seed_payload(
        self,
        request: m.Infra.ToolingContextRequest,
        *,
        tool_config: m.Infra.ToolConfigDocument,
    ) -> p.Result[t.MutableJsonMapping]:
        """Conform a seeded native document before projecting its managed tables.

        Returns:
            The conformed document carrying every native tool table.

        """
        result_type = r[t.MutableJsonMapping]
        declaration = u.Infra.load_repository_declaration_inputs(request.path.parent)
        if declaration.failure:
            return result_type.from_failure(declaration)
        live_dev_result = self._live_dev_dependencies(request.path)
        if live_dev_result.failure:
            return result_type.from_failure(live_dev_result)
        live_dev = live_dev_result.value
        # Seed only the target's requirements before deriving analyzer ownership.
        seed: t.JsonMapping = {
            c.Infra.PROJECT: {
                c.Infra.NAME: request.project_name,
                c.Infra.DEPENDENCIES: [
                    *request.declared_project_dependencies,
                    *request.runtime_dependency_overlay,
                ],
            },
            c.Infra.DEPENDENCY_GROUPS: {
                c.Infra.DEV: list(
                    u.Infra.project_development_requirements(
                        request.scaffold_project,
                        distribution=request.project_name,
                        kind=declaration.value.spec.kind,
                        declared=live_dev,
                    )
                ),
            },
            c.Infra.TOOL: {"flext": {"docs": {"package_name": request.package_name}}},
        }
        # Atomic scaffolds provide validated future roots;
        # existing repositories keep filesystem discovery through empty ones.
        conformed = self._conformed_document_state(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(seed)),
            path=request.path,
            topology=request.topology,
            tool_config=tool_config,
        )
        if conformed.failure:
            return result_type.from_failure(conformed)
        state, _ = conformed.value
        return result_type.ok(state.payload)


__all__: list[str] = ["FlextInfraPyprojectModernizerTooling"]
