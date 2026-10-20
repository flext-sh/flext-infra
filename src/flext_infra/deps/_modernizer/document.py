"""Read, normalize, and render one pyproject document through every phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from flext_core import FlextRuntime

from flext_infra import c, config, m, r, t, u
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
from flext_infra.refactor import FlextInfraProjectClassifier

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraPyprojectModernizerDocument:
    """Own the parsed document state and the ordered phase pipeline."""

    if TYPE_CHECKING:
        # Members supplied by the composed modernizer service.
        tomlsort_sort_first: t.StrSequence
        managed_artifacts: m.Infra.ProjectManagedArtifactsResolution | None

        @property
        def root(self) -> Path: ...

        @staticmethod
        def _derived_paths(
            project_dir: Path,
            declared_python_dirs: t.StrSequence,
            seed_manager: FlextInfraExtraPathsManager,
            tool_config: m.Infra.ToolConfigDocument,
            *,
            is_root: bool,
        ) -> t.Pair[t.StrSequence, t.StrSequence]: ...

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

        Returns:
            The resulting ``p.Result[m.Infra.PyprojectDocumentState]``.

        """
        result_type = r[m.Infra.PyprojectDocumentState]
        if source is None:
            read = u.Cli.files_read_text(path)
            if read.failure:
                return result_type.from_failure(read)
            source = read.value
        recovered = u.Infra.recover_live_pyproject_text(source)
        if recovered.failure:
            return result_type.from_failure(recovered)
        document = u.Cli.toml_parse_text(recovered.value)
        if document is None:
            return result_type.fail(f"invalid TOML: {path}")
        payload_source = FlextRuntime.normalize_to_json_value(document.unwrap())
        validated: p.Result[t.MutableJsonMapping] = u.validate_value(
            t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER,
            payload_source,
        )
        if validated.failure:
            return result_type.fail_op("TOML payload validation", validated.error)
        return result_type.ok(
            m.Infra.PyprojectDocumentState(
                pyproject_path=path,
                original_rendered=source,
                payload=validated.value,
                document=document,
            ),
        )

    @staticmethod
    def _normalize_build_payload(payload: t.MutableJsonMapping) -> t.StrSequence:
        """Pin the hatchling backend and drop empty Poetry dependency groups.

        Returns:
            The resulting ``t.StrSequence``.

        """
        changes: t.MutableSequenceOf[str] = []
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

    @staticmethod
    def _ordered_keys(
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        preferred_first: t.StrSequence,
    ) -> t.Pair[t.StrSequence, t.StrSequence]:
        """Return current keys and their preferred-first, then alphabetical order.

        Returns:
            Current keys and their preferred-first, then alphabetical order.

        """
        current = [str(key) for key in container]
        ordered = [key for key in preferred_first if key in current]
        ordered.extend(sorted(set(current) - set(ordered)))
        return current, ordered

    @classmethod
    def _reorder_child(
        cls,
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        table_key: str,
    ) -> None:
        """Reorder a table child or every table in an array child."""
        table = u.Cli.toml_table_child(container, table_key)
        if table is not None:
            cls._reorder_table(table)
            return
        item = u.Cli.toml_item_child(container, table_key)
        if item is not None and u.Cli.toml_is_aot(item):
            for entry in item.body:
                cls._reorder_table(entry)

    @classmethod
    def _reorder_table(cls, table: t.Cli.TomlTable) -> None:
        """Reorder one validated TOML table and its table-like children."""
        current, ordered = cls._ordered_keys(table, ())
        for key in ordered:
            cls._reorder_child(table, key)
        items = {key: table[key] for key in current}
        if ordered != current:
            for key in current:
                del table[key]
            for key in ordered:
                table[key] = items[key]

    @classmethod
    def _reorder_document(
        cls,
        doc: t.Cli.TomlDocument,
        *,
        preferred_first: t.StrSequence,
    ) -> None:
        """Apply deterministic ordering to top-level groups and nested tables."""
        current, ordered = cls._ordered_keys(doc, preferred_first)
        if ordered != current:
            items = {key: doc[key] for key in current}
            for key in current:
                del doc[key]
            for key in ordered:
                doc[key] = items[key]
        for key in ordered:
            cls._reorder_child(doc, key)

    def _process_document_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
        source_migration: m.Infra.GitSourceReferenceMigration | None = None,
    ) -> p.Result[t.StrSequence]:
        """Run every phase over one discovered state; write unless ``dry_run``.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        if source_migration is not None:
            migrated = u.Infra.rewrite_git_source_references(
                state.payload, source_migration
            )
            if migrated.failure:
                return r[t.StrSequence].from_failure(migrated)
            if not migrated.value:
                state.rendered = state.original_rendered
                return r[t.StrSequence].ok(())
            rendered = self._render_document_state(
                state,
                migrated.value,
                skip_comments=True,
                format_source=False,
                preserve_layout=True,
            )
        else:
            manifests = u.Infra.load_workspace_manifest(state.pyproject_path.parent)
            if manifests.failure:
                return r[t.StrSequence].from_failure(manifests)
            manifest = manifests.value[0] if manifests.value else None
            project = manifest.project if manifest is not None else None
            topology = m.Infra.PyprojectDeclaredTopology.model_validate({
                **(
                    project.model_dump(
                        include=set(m.Infra.PyprojectDeclaredTopology.model_fields),
                    )
                    if project is not None
                    else {}
                ),
                "project_declaration_resource": (
                    FlextInfraEnsurePackagingPhase.declaration_resource(
                        package_name=(
                            project.package_name
                            if project is not None
                            else u.Infra.package_name_from_payload(
                                state.pyproject_path.parent,
                                state.payload,
                                u.Infra.docs_meta_from_payload(state.payload),
                            )
                        ),
                        package=manifest.repository.package,
                    )
                    if manifest is not None
                    else None
                ),
            })
            rendered = self._render_document_state(
                state,
                self._apply_document_phases(
                    state,
                    canonical_dev=canonical_dev,
                    topology=topology,
                ),
                skip_comments=skip_comments,
            )
        if rendered.failure:
            return rendered
        if state.rendered == state.original_rendered.rstrip() + "\n":
            return r[t.StrSequence].ok(())
        if not dry_run:
            u.write_file(
                state.pyproject_path, state.rendered, encoding=c.DEFAULT_ENCODING
            )
        return rendered

    def _apply_document_phases(
        self,
        state: m.Infra.PyprojectDocumentState,
        *,
        canonical_dev: t.StrSequence,
        topology: m.Infra.PyprojectDeclaredTopology,
        tool_config: m.Infra.ToolConfigDocument | None = None,
    ) -> t.StrSequence:
        """Run every managed phase, in order, over one parsed payload.

        Returns:
            The resulting ``t.StrSequence``.

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
        mypy_search_paths = (
            paths_manager.mypy_search_paths(project_dir=path.parent, is_root=is_root)
            if paths_manager is not None
            else self._derived_paths(
                path.parent,
                topology.declared_python_dirs,
                FlextInfraExtraPathsManager(repository_root=self.root),
                tooling,
                is_root=is_root,
            )[1]
        )
        managed_artifacts = self.managed_artifacts
        if managed_artifacts is None:
            managed_artifacts = u.Infra.load_project_managed_artifacts(
                path.parent,
            ).unwrap()
        changes: t.MutableSequenceOf[str] = [
            *self._normalize_build_payload(payload),
            *FlextInfraConsolidateGroupsPhase().apply_payload(payload, canonical_dev),
            *FlextInfraToolTablesPhase(tooling).apply_payload(
                payload,
                path=path,
                repository_namespace_packages=topology.repository_namespace_packages,
                mypy_search_paths=mypy_search_paths,
            ),
            # Pyrefly derives its include globs from the canonical Pyright
            # roots, so resolve Pyright first and converge in one pass.
            *FlextInfraEnsurePyrightConfigPhase(tooling).apply_payload(
                payload,
                context=analyzer_context,
                paths_manager=paths_manager,
                analysis_exclusions=topology.analysis_exclusions,
            ),
            # Declared roots are topology facts only during atomic creation;
            # normal modernization derives productive roots on disk.
            *FlextInfraEnsurePyreflyConfigPhase(tooling).apply_payload(
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
                    is_root=is_root,
                    mypy_search_paths=mypy_search_paths,
                ),
            )
        return changes

    def _render_document_state(
        self,
        state: m.Infra.PyprojectDocumentState,
        changes: t.StrSequence,
        *,
        skip_comments: bool,
        format_source: bool = True,
        preserve_layout: bool = False,
    ) -> p.Result[t.StrSequence]:
        """Order, annotate, and format one payload without writing to disk.

        A formatter failure is the result's failure, never a reported change.

        Args:
            state: The parsed document state to render.
            changes: The already-accumulated change entries to extend.
            skip_comments: Keep the inject-comments phase out of the render.
            format_source: Run the canonical TOML formatter.
            preserve_layout: Synchronize values through the original TOML tree.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        path = state.pyproject_path
        if preserve_layout:
            if state.document is None:
                return r[t.StrSequence].fail(
                    f"original TOML document is unavailable: {path}"
                )
            doc = state.document
            self._sync_document_values(doc, state.payload)
        else:
            doc = u.Cli.toml_document_from_mapping(state.payload)
            self._reorder_document(doc, preferred_first=self.tomlsort_sort_first)
        rendered = doc.as_string()
        comment_changes: t.StrSequence = ()
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
                return r[t.StrSequence].from_failure(formatted)
            rendered = formatted.value
        state.rendered = rendered.rstrip() + "\n"
        return r[t.StrSequence].ok((*changes, *comment_changes))

    @classmethod
    def _sync_document_values(
        cls,
        document: t.Cli.TomlDocument | t.Cli.TomlTable,
        payload: t.JsonMapping,
    ) -> None:
        """Synchronize changed semantic values through the original TOML tree."""
        for key, value in payload.items():
            if u.Cli.toml_value(document, key) == value:
                continue
            child = u.Cli.toml_table_child(document, key)
            if child is not None and isinstance(value, Mapping):
                cls._sync_document_values(child, value)
            elif isinstance(value, list) and all(
                isinstance(item, str) for item in value
            ):
                u.Cli.toml_sync_string_list(
                    document,
                    key,
                    tuple(item for item in value if isinstance(item, str)),
                )
            else:
                u.Cli.toml_sync_value(document, key, value)


__all__: list[str] = ["FlextInfraPyprojectModernizerDocument"]
