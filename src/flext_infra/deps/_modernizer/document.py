"""Read, normalize, and render one pyproject document through every phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import TYPE_CHECKING, Annotated, ClassVar

from flext_infra import FlextInfraProjectSelectionServiceBase, c, config, m, r, t, u
from flext_infra._models.deps import (
    GitSourceRefFromField,
    GitSourceRefToField,
    GitSourceUrlPrefixField,
)
from flext_infra.deps import FlextInfraExtraPathsManager
from flext_infra.deps.phases import (
    FlextInfraConsolidateGroupsPhase,
    FlextInfraEnsurePackagingPhase,
    FlextInfraEnsurePyreflyConfigPhase,
    FlextInfraEnsurePyrightConfigPhase,
    FlextInfraEnsureRuffConfigPhase,
    FlextInfraInjectCommentsPhase,
    FlextInfraToolTablesPhase,
)
from flext_infra.gates.lint_freeze import FlextInfraLintConfigFreezeGate
from flext_infra.refactor import FlextInfraProjectClassifier

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraPyprojectModernizerDocument(
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Own the parsed document state and the ordered phase pipeline."""

    @staticmethod
    def _config_sort_first() -> Sequence[str]:
        """Read the config-owned top-level TOML section order once.

        Returns:
            The resulting ``Sequence[str]``.

        """
        return u.Infra.native_tool_strings(
            config.Infra.tooling,
            "tomlsort",
            "sort_first",
        )

    audit: Annotated[
        bool,
        m.Field(default=False, description="Audit pyproject changes without writing"),
    ] = False
    skip_check: Annotated[
        bool,
        m.Field(alias="skip-check", description="Skip post-write validation"),
    ] = False
    skip_comments: Annotated[
        bool,
        m.Field(alias="skip-comments", description="Skip managed comment updates"),
    ] = False
    rewrite_constraints: Annotated[
        bool,
        m.Field(
            alias="rewrite-constraints",
            description="Rewrite dependency constraints from the provisioned runtime",
        ),
    ] = False
    managed_artifacts: Annotated[
        m.Infra.ProjectManagedArtifactsResolution | None,
        m.Field(
            default=None,
            exclude=True,
            description="Caller-owned project ManagedArtifacts resolution",
        ),
    ] = None
    git_source_url_prefix: GitSourceUrlPrefixField = None
    git_source_ref_from: GitSourceRefFromField = None
    git_source_ref_to: GitSourceRefToField = None
    tomlsort_sort_first: Sequence[str] = m.Field(
        default_factory=_config_sort_first,
        exclude=True,
        description="Config-owned top-level TOML section order",
    )

    def _project_kind(
        self,
        path: Path,
        payload: t.JsonMapping,
        project_kind: str | None,
    ) -> str:
        """Return the declared kind, classifying member projects on demand.

        Returns:
            The declared kind, classifying member projects on demand.

        """
        if project_kind is not None:
            return project_kind
        if path.parent.resolve() == self.root.resolve():
            return "core"
        return (
            FlextInfraProjectClassifier(path.parent, pyproject_payload=payload)
            .classify()
            .project_kind
        )

    @staticmethod
    def _read_document_state(
        path: Path,
        *,
        source: str | None = None,
    ) -> p.Result[m.Infra.PyprojectDocumentState]:
        """Parse one pyproject once into one validated plain payload state.

        Args:
            path: The path to the pyproject file.
            source: Optional raw content of the pyproject file.

        Returns:
            The resulting ``p.Result[m.Infra.PyprojectDocumentState]``.

        Raises:
            ValueError: If the project document has no captured content.


        """
        result_type = r[m.Infra.PyprojectDocumentState]
        before: m.Cli.AtomicFileState | None = None
        if source is None:
            read = u.Cli.atomic_read_binary_file_state(path, required=True)
            if read.failure:
                return result_type.from_failure(read)
            before = read.value
            if before.content is None:
                message = f"required project document has no captured content: {path}"
                raise ValueError(message)
            source = before.content.decode(c.DEFAULT_ENCODING)
        recovered = u.Infra.recover_live_pyproject_text(source)
        if recovered.failure:
            return result_type.from_failure(recovered)
        document = u.Cli.toml_parse_text(recovered.value)
        if document is None:
            return result_type.fail(f"invalid TOML: {path}")
        payload_source = u.normalize_to_json_value(document.unwrap())
        validated: p.Result[t.MutableJsonMapping] = u.validate_value(
            t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER,
            payload_source,
        )
        if validated.failure:
            return result_type.fail_op("TOML payload validation", validated.error)
        return result_type.ok(
            m.Infra.PyprojectDocumentState(
                pyproject_path=path,
                before=before,
                original_rendered=source,
                payload=validated.value,
                document=document,
            ),
        )

    @staticmethod
    def _normalize_build_payload(payload: t.MutableJsonMapping) -> Sequence[str]:
        """Pin the hatchling backend and drop empty Poetry dependency groups.

        Returns:
            The resulting ``Sequence[str]``.

        """
        changes: MutableSequence[str] = []
        if u.Cli.toml_mapping_child(payload, "build-system") is None:
            changes.append("created [build-system]")
        build_system = u.Cli.toml_mapping_ensure_table(payload, "build-system")
        if u.Cli.toml_mapping_sync_value(
            build_system,
            "build-backend",
            "hatchling.build",
        ):
            changes.append("build-system.build-backend set to hatchling.build")
        if u.Cli.toml_mapping_sync_string_list(
            build_system,
            "requires",
            ["hatchling"],
            sort_values=True,
        ):
            changes.append("build-system.requires set to ['hatchling']")
        groups = u.Cli.toml_mapping_path(
            payload,
            (c.Infra.TOOL, c.Infra.POETRY, c.Infra.GROUP),
        )
        if groups is None:
            return changes
        for name in [
            name
            for name in groups
            if u.Cli.toml_mapping_path(groups, (name, c.Infra.DEPENDENCIES)) == {}
        ]:
            del groups[name]
            changes.append(f"removed empty poetry group '{name}'")
        poetry = u.Cli.toml_mapping_path(payload, (c.Infra.TOOL, c.Infra.POETRY))
        if not groups and poetry is not None:
            del poetry[c.Infra.GROUP]
            changes.append("removed empty poetry group container")
        return changes

    _last_migration_render: ClassVar[p.Result[str] | None] = None

    def _apply_source_migration(
        self,
        state: m.Infra.PyprojectDocumentState,
        source_migration: m.Infra.GitSourceReferenceMigration,
    ) -> p.Result[Sequence[str]] | None:
        """Rewrite Git source references; produce the migration render.

        Returns:
            The early result when migration yields no change, or ``None``
            when the caller should proceed with the migration render.

        """
        migrated = u.Infra.rewrite_git_source_references(
            state.payload, source_migration
        )
        if migrated.failure:
            return r[Sequence[str]].from_failure(migrated)
        if not migrated.value:
            state.rendered = state.original_rendered
            return r[Sequence[str]].ok(())
        self._last_migration_render = self._render_document_state(
            state,
            migrated.value,
            skip_comments=True,
            format_source=False,
            preserve_layout=True,
        )
        return None

    def _process_document_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: Sequence[str],
        dry_run: bool,
        skip_comments: bool,
        source_migration: m.Infra.GitSourceReferenceMigration | None = None,
    ) -> p.Result[Sequence[str]]:
        """Run every phase over one discovered state; write unless ``dry_run``.

        Args:
            state: The current document state.
            canonical_dev: The canonical development dependencies.
            dry_run: Whether to perform a dry run without writing changes.
            skip_comments: Whether to skip comments during processing.
            source_migration: Optional Git source reference migration.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

        Raises:
            ValueError: If the project publication has no original capture.

        """
        if source_migration is not None:
            early = self._apply_source_migration(state, source_migration)
            if early is not None:
                return early
            rendered = self._last_migration_render
        else:
            rendered = self._render_declared_state(
                state,
                canonical_dev=canonical_dev,
                skip_comments=skip_comments,
            )
        if rendered.failure:
            return rendered
        if state.rendered == state.original_rendered:
            return r[Sequence[str]].ok(())
        if not dry_run:
            if state.before is None:
                message = (
                    "project publication has no original capture: "
                    f"{state.pyproject_path}"
                )
                raise ValueError(message)
            observations = FlextInfraLintConfigFreezeGate.require_projection(
                self.root, state
            )
            published = u.Infra.publish_codegen_plans(
                self.root,
                (
                    m.Infra.CodegenFilePlan(
                        project=state.pyproject_path.parent,
                        path=state.pyproject_path,
                        before=state.before,
                        desired_content=state.rendered.encode(c.DEFAULT_ENCODING),
                        desired_mode=state.before.mode,
                        owner=c.Infra.CLI_GROUP_DEPS,
                    ),
                    *observations,
                ),
            )
            if published.failure:
                return r.from_failure(published)
        if not rendered.value:
            return r[Sequence[str]].ok(("canonical pyproject rendering changed bytes",))
        return rendered

    def _render_declared_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: Sequence[str],
        skip_comments: bool,
    ) -> p.Result[Sequence[str]]:
        """Run every managed phase against the declared repository topology.

        Returns:
            The rendered change list, or the first declaration failure.

        """
        inputs = u.Infra.load_codegen_inputs(state.pyproject_path.parent)
        if inputs.failure:
            return r[Sequence[str]].from_failure(inputs)
        repository = inputs.value.spec.repository
        project = repository.project
        build_changes = self._normalize_build_payload(state.payload)
        topology = m.Infra.PyprojectDeclaredTopology.model_validate(
            project.model_dump(
                include=set(m.Infra.PyprojectDeclaredTopology.model_fields),
            )
            if project is not None
            else {},
        )
        return self._render_document_state(
            state,
            (
                *build_changes,
                *self._apply_document_phases(
                    state,
                    canonical_dev=canonical_dev,
                    topology=topology,
                    codegen=inputs.value.spec,
                ),
            ),
            skip_comments=skip_comments,
        )

    def _apply_document_phases(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: Sequence[str],
        topology: m.Infra.PyprojectDeclaredTopology,
        codegen: m.Infra.CodegenConfigSpec,
        tool_config: m.Infra.ToolConfigDocument | None = None,
    ) -> Sequence[str]:
        """Run every managed phase, in order, over one parsed payload.

        Returns:
            The resulting ``Sequence[str]``.

        """
        path, payload = state.pyproject_path, state.payload
        is_root = path.parent.resolve() == self.root.resolve()
        # Scaffold (pre-write) contexts have no on-disk project root yet: derive
        # analyzer configuration from declared roots only; disk discovery
        # converges on the first post-write conformance pass.
        exists = path.is_file()
        paths_manager = (
            FlextInfraExtraPathsManager(
                repository_root=self.root,
                analysis_exclusions=topology.analysis_exclusions or (),
            )
            if exists
            else None
        )
        analyzer_context = m.Infra.PyprojectAnalyzerContext(
            is_root=is_root,
            repository_root=self.root if exists else None,
            project_dir=path.parent if exists else None,
            declared_python_dirs=topology.declared_python_dirs,
            declared_python_dirs_are_complete=(
                topology.declared_python_dirs_are_complete
            ),
        )
        tooling = (
            u.Infra.load_tooling_inputs(path.parent).unwrap().document
            if tool_config is None
            else tool_config
        )
        path_rules = tooling.tools.pyrefly.path_rules
        if paths_manager is not None:
            mypy_search_paths = paths_manager.mypy_search_paths(project_dir=path.parent)
        elif path_rules.source_dir in topology.declared_python_dirs:
            mypy_search_paths = tuple(
                root
                for root in (
                    path_rules.source_dir,
                    *path_rules.project_shared_search_paths,
                )
                if root != path_rules.project_root
                and (
                    root in topology.declared_python_dirs
                    or (path.parent / root).is_dir()
                )
            )
        else:
            mypy_search_paths = FlextInfraExtraPathsManager(
                repository_root=self.root
            ).mypy_search_paths(project_dir=path.parent)
        managed_artifacts = self.managed_artifacts
        if managed_artifacts is None:
            managed_artifacts = u.Infra.load_project_managed_artifacts(
                path.parent,
            ).unwrap()
        changes: MutableSequence[str] = [
            *self._normalize_build_payload(payload),
            *FlextInfraConsolidateGroupsPhase().apply_payload(payload, canonical_dev),
            *FlextInfraToolTablesPhase(tooling, codegen=codegen).apply_payload(
                payload,
                path=path,
                repository_namespace_packages=topology.repository_namespace_packages,
                mypy_search_paths=mypy_search_paths,
            ),
            # Pyrefly derives its include globs from the canonical Pyright
            # roots, so resolve Pyright first and converge in one pass.
            *FlextInfraEnsurePyrightConfigPhase(tooling, codegen=codegen).apply_payload(
                payload,
                context=analyzer_context,
                paths_manager=paths_manager,
                analysis_exclusions=topology.analysis_exclusions,
            ),
            # Declared roots are topology facts only during atomic creation;
            # normal modernization derives productive roots on disk.
            *FlextInfraEnsurePyreflyConfigPhase(tooling, codegen=codegen).apply_payload(
                payload,
                context=(
                    analyzer_context
                    if exists
                    else analyzer_context.model_copy(
                        update={"declared_python_dirs_are_complete": True},
                    )
                ),
                paths_manager=paths_manager,
            ),
            *FlextInfraEnsureRuffConfigPhase(
                tooling,
                codegen=codegen,
            ).apply_payload(
                payload,
                path=path,
                analysis_exclusions=topology.analysis_exclusions,
                generated_python_roots=topology.declared_python_dirs,
                repository_namespace_packages=topology.repository_namespace_packages,
            ),
            *FlextInfraEnsurePackagingPhase().apply_payload(
                payload,
                path=path,
                topology=topology,
            ),
        ]
        if paths_manager is not None:
            changes.extend(
                paths_manager.sync_payload(
                    payload,
                    project_dir=path.parent,
                    mypy_search_paths=mypy_search_paths,
                ),
            )
        return changes

    def _render_document_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        changes: Sequence[str],
        *,
        skip_comments: bool,
        format_source: bool = True,
        preserve_layout: bool = False,
    ) -> p.Result[Sequence[str]]:
        """Order, annotate, and format one payload without writing to disk.

        A formatter failure is the result's failure, never a reported change.

        Args:
            state: The parsed document state to render.
            changes: The already-accumulated change entries to extend.
            skip_comments: Keep the inject-comments phase out of the render.
            format_source: Run the canonical TOML formatter.
            preserve_layout: Synchronize values through the original TOML tree.

        Returns:
            The resulting ``p.Result[Sequence[str]]``.

        """
        path = state.pyproject_path
        if preserve_layout:
            if state.document is None:
                return r[Sequence[str]].fail(
                    f"original TOML document is unavailable: {path}"
                )
            doc = state.document
            u.Infra.sync_document_values(doc, state.payload)
        else:
            canonical = u.Cli.JSON_MAPPING_ADAPTER.validate_python(
                u.Cli.json_sort_keys(dict(state.payload)),
            )
            preferred = {
                key: canonical[key]
                for key in self.tomlsort_sort_first
                if key in canonical
            }
            doc = u.Cli.toml_document_from_mapping({**preferred, **canonical})
        rendered = doc.as_string()
        comment_changes: Sequence[str] = ()
        if not skip_comments:
            rendered, comment_changes = FlextInfraInjectCommentsPhase().apply(rendered)
        if format_source:
            formatted = u.Infra.format_toml_source(
                rendered,
                path=path,
                toolchain_root=self.root,
                taplo_version=config.Infra.codegen.toolchain.tool_versions["taplo"],
                process_timeout_seconds=(
                    config.Infra.tooling.tools.tomlsort.process_timeout_seconds
                ),
            )
            if formatted.failure:
                return r[Sequence[str]].from_failure(formatted)
            rendered = formatted.value
        state.rendered = rendered.rstrip() + "\n"
        return r[Sequence[str]].ok((*changes, *comment_changes))


__all__: list[str] = ["FlextInfraPyprojectModernizerDocument"]
