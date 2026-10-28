"""Aggregate workspace artifact rendering for documentation generation.

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

from collections import Counter
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesProjectManagedArtifacts
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsGenerateProject,
    FlextInfraUtilitiesDocsRender,
)


class FlextInfraUtilitiesDocsGenerateRoot(
    FlextInfraUtilitiesDocsGenerateProject,
):
    """Render aggregate docs from the complete discovered project set."""

    @staticmethod
    def _aggregate_root_pages(
        repository_root: Path,
        inputs: m.Infra.DocsRootInputs,
        src_paths: Sequence[str],
        catalog_entries: Sequence[m.Infra.DocsCatalogEntry],
    ) -> list[tuple[Path, str]]:
        """Render the static aggregate mkdocs and catalog root pages.

        Args:
            repository_root: Repository receiving the rendered root pages.
            inputs: Workspace-level contract, exclusions and source inputs.
            src_paths: Workspace-relative source roots of every scope.
            catalog_entries: Catalog entries of every discovered project.

        Returns:
            The resulting ``list[tuple[Path, str]]``.

        """
        width = inputs.markdown_width
        return [
            (
                repository_root / "mkdocs.yml",
                FlextInfraUtilitiesDocsRender.docs_root_mkdocs(
                    inputs.workspace_contract,
                    src_paths,
                    repository_root=repository_root,
                ),
            ),
            (
                repository_root / "docs/projects/generated/catalog.md",
                FlextInfraUtilitiesDocsRender.docs_project_catalog_page(
                    catalog_entries, exclude_docs=inputs.exclude_docs, width=width
                ),
            ),
        ]

    @classmethod
    def _root_rendered(
        cls,
        repository_root: Path,
        scopes: Sequence[m.Infra.DocScope],
        inputs: m.Infra.DocsRootInputs,
    ) -> p.Result[
        tuple[
            list[tuple[Path, str]],
            list[m.Infra.DocScope],
            MutableMapping[str, list[str]],
        ]
    ]:
        """Render the aggregate root pages and collect per-project inputs.

        Args:
            repository_root: Repository receiving the rendered root pages.
            scopes: Complete discovered docs scope set.
            inputs: Workspace-level contract, exclusions and source inputs.

        Returns:
            The resulting ``(rendered, project scopes, scope modules)`` triple.

        """
        width = inputs.markdown_width
        project_scopes = [scope for scope in scopes if scope.path != repository_root]
        catalog_entries: MutableSequence[m.Infra.DocsCatalogEntry] = []
        scope_modules: MutableMapping[str, list[str]] = {}
        src_paths: MutableSequence[str] = []
        root_api: list[tuple[Path, str]] = []
        for scope in scopes:
            if scope.name == c.Infra.RK_ROOT:
                continue
            if (scope.path / c.Infra.DEFAULT_SRC_DIR).is_dir():
                src_paths.append(
                    (scope.path / "src").relative_to(repository_root).as_posix(),
                )
            if scope.path == repository_root:
                if scope.package_name:
                    root_api.extend(
                        FlextInfraUtilitiesDocsGenerateRoot.docs_project_api_artifacts(
                            scope, width=width
                        ),
                    )
                continue
            project_contract = (
                FlextInfraUtilitiesDocsContract.docs_current_project_contract(
                    scope.path,
                    FlextInfraUtilitiesDocsApi.public_contract(
                        scope.path,
                        scope.package_name,
                    ),
                )
            )
            scope_modules[scope.name] = (
                FlextInfraUtilitiesDocsGenerateRoot._module_names(scope)
            )
            catalog_entries.append(
                m.Infra.DocsCatalogEntry(
                    name=scope.name,
                    project_class=scope.project_class,
                    package_name=scope.package_name,
                    description=str(project_contract.get("description", "")).strip(),
                    api_page=f"../../api-reference/generated/{scope.name}.md",
                ),
            )
        class_counts = Counter(entry.project_class for entry in catalog_entries)
        rendered: list[tuple[Path, str]] = [
            *root_api,
            *cls._aggregate_root_pages(
                repository_root,
                inputs,
                src_paths,
                catalog_entries,
            ),
            (
                repository_root / "docs/api-reference/generated/overview.md",
                FlextInfraUtilitiesDocsRender.docs_root_overview_page(
                    inputs.workspace_contract,
                    project_count=len(project_scopes),
                    class_counts=tuple(
                        m.Infra.DocsClassCount(project_class=name, count=count)
                        for name, count in sorted(class_counts.items())
                    ),
                    width=width,
                ),
            ),
        ]
        return r[
            tuple[
                list[tuple[Path, str]],
                list[m.Infra.DocScope],
                MutableMapping[str, list[str]],
            ]
        ].ok((rendered, project_scopes, dict(scope_modules)))

    @staticmethod
    def _project_rendered(
        repository_root: Path,
        project_scopes: Sequence[m.Infra.DocScope],
        scope_modules: Mapping[str, list[str]],
        rendered: list[tuple[Path, str]],
        *,
        width: int,
    ) -> list[tuple[Path, str]]:
        """Append every project's generated API pages and the projects index.

        Returns:
            The resulting ``list[tuple[Path, str]]``.

        """
        projects_index_entries: MutableSequence[m.Infra.DocsProjectIndexEntry] = []
        for scope in project_scopes:
            rendered.append((
                repository_root / "docs/api-reference/generated" / f"{scope.name}.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    f"{scope.name} Public API", scope.package_name, width=width
                ),
            ))
            module_names = scope_modules.get(scope.name, [])
            modules_root = (
                repository_root
                / "docs/api-reference/generated/projects"
                / scope.name
                / "modules"
            )
            rendered.append((
                modules_root / "index.md",
                FlextInfraUtilitiesDocsRender.docs_modules_index(
                    scope, module_names, width=width
                ),
            ))
            for module_name in module_names:
                relative = module_name.removeprefix(f"{scope.package_name}.").replace(
                    ".",
                    "/",
                )
                rendered.append((
                    modules_root / f"{relative}.md",
                    FlextInfraUtilitiesDocsRender.docs_directive_page(
                        module_name, module_name, width=width
                    ),
                ))
            projects_index_entries.append(
                m.Infra.DocsProjectIndexEntry(
                    name=scope.name,
                    module_count=len(module_names),
                ),
            )
        rendered.append((
            repository_root / "docs/api-reference/generated/projects/index.md",
            FlextInfraUtilitiesDocsRender.docs_root_projects_index(
                projects_index_entries, width=width
            ),
        ))
        return rendered

    @classmethod
    def _prune_generated(
        cls,
        repository_root: Path,
        rendered: Sequence[tuple[Path, str]],
    ) -> p.Result[
        tuple[
            tuple[t.Infra.DocsRenderedArtifactTuple, ...],
            tuple[t.Infra.DocsRenderedArtifactTuple, ...],
        ]
    ]:
        """Prune both generated docs trees against the rendered inventory.

        Returns:
            The resulting ``(api, projects)`` pruned artifact pair.

        """
        api_pruned = (
            FlextInfraUtilitiesDocsGenerateRoot._prune_generated_tree_artifacts(
                repository_root,
                repository_root / "docs/api-reference/generated",
                rendered,
            )
        )
        if api_pruned.failure:
            return r[
                tuple[
                    tuple[t.Infra.DocsRenderedArtifactTuple, ...],
                    tuple[t.Infra.DocsRenderedArtifactTuple, ...],
                ]
            ].from_failure(api_pruned)
        projects_pruned = (
            FlextInfraUtilitiesDocsGenerateRoot._prune_generated_tree_artifacts(
                repository_root,
                repository_root / "docs/projects/generated",
                rendered,
            )
        )
        if projects_pruned.failure:
            return r[
                tuple[
                    tuple[t.Infra.DocsRenderedArtifactTuple, ...],
                    tuple[t.Infra.DocsRenderedArtifactTuple, ...],
                ]
            ].from_failure(projects_pruned)
        return r[
            tuple[
                tuple[t.Infra.DocsRenderedArtifactTuple, ...],
                tuple[t.Infra.DocsRenderedArtifactTuple, ...],
            ]
        ].ok((api_pruned.value, projects_pruned.value))

    @classmethod
    def docs_root_artifacts(
        cls,
        repository_root: Path,
        scopes: Sequence[m.Infra.DocScope],
    ) -> p.Result[tuple[t.Infra.DocsRenderedArtifactTuple, ...]]:
        """Render aggregate root targets from the complete discovered project set.

        Returns:
            The resulting
                ``p.Result[tuple[t.Infra.DocsRenderedArtifactTuple, ...]]``.

        """
        tooling = FlextInfraUtilitiesProjectManagedArtifacts.load_tooling_inputs(
            repository_root
        )
        if tooling.failure:
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].from_failure(
                tooling
            )
        width = FlextInfraUtilitiesDocsRender.docs_markdown_line_length(
            tooling.value.document
        )
        workspace_contract = FlextInfraUtilitiesDocsContract.docs_workspace_contract(
            repository_root,
        )
        exclude_docs = FlextInfraUtilitiesDocsRender.as_string_sequence(
            workspace_contract,
            "exclude_docs",
        )
        aggregated = cls._root_rendered(
            repository_root,
            scopes,
            m.Infra.DocsRootInputs(
                workspace_contract=workspace_contract,
                markdown_width=width,
                exclude_docs=exclude_docs,
            ),
        )
        if aggregated.failure:
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].from_failure(
                aggregated,
            )
        rendered, project_scopes, scope_modules = aggregated.value
        rendered = cls._project_rendered(
            repository_root,
            project_scopes,
            scope_modules,
            rendered,
            width=width,
        )
        pruned = cls._prune_generated(repository_root, rendered)
        if pruned.failure:
            return r[tuple[t.Infra.DocsRenderedArtifactTuple, ...]].from_failure(
                pruned,
            )
        return FlextInfraUtilitiesDocsGenerateRoot.docs_normalize_artifacts((
            *((repository_root, path, content) for path, content in rendered),
            *pruned.value[0],
            *pruned.value[1],
        ))

    @staticmethod
    def docs_scope_artifacts(
        scope: m.Infra.DocScope,
        *,
        repository_root: Path,
        aggregate_scopes: Sequence[m.Infra.DocScope],
    ) -> p.Result[tuple[t.Infra.DocsRenderedArtifactTuple, ...]]:
        """Return the rendered artifact inventory for one docs scope.

        The scope label is the only topology input (see ``build_scopes``).

        Returns:
            The rendered artifact inventory for one docs scope.

        """
        if scope.name == c.Infra.RK_ROOT:
            return FlextInfraUtilitiesDocsGenerateRoot.docs_root_artifacts(
                repository_root,
                aggregate_scopes,
            )
        return FlextInfraUtilitiesDocsGenerateRoot.docs_project_artifacts(
            scope,
            repository_root=repository_root,
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateRoot"]
