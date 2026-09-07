"""Aggregate workspace artifact rendering for documentation generation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

from .._utilities._docs_generate_plan import DocsRenderedArtifactTuple
from .._utilities._docs_generate_project import (
    FlextInfraUtilitiesDocsGenerateProjectMixin,
)
from .._utilities.docs_api import FlextInfraUtilitiesDocsApi
from .._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from .._utilities.docs_render import FlextInfraUtilitiesDocsRender

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesDocsGenerateRootMixin(
    FlextInfraUtilitiesDocsGenerateProjectMixin
):
    """Render aggregate docs from the complete discovered project set."""

    @staticmethod
    def docs_root_artifacts(
        workspace_root: Path, scopes: t.SequenceOf[m.Infra.DocScope]
    ) -> p.Result[t.VariadicTuple[DocsRenderedArtifactTuple]]:
        """Render aggregate root targets from the complete discovered project set."""
        workspace_contract = FlextInfraUtilitiesDocsContract.docs_workspace_contract(
            workspace_root
        )
        exclude_docs = FlextInfraUtilitiesDocsRender.as_string_sequence(
            workspace_contract, "exclude_docs"
        )
        project_scopes = [scope for scope in scopes if scope.name != c.Infra.RK_ROOT]
        catalog_entries: t.MutableSequenceOf[dict[str, str]] = []
        class_counts: dict[str, int] = {}
        scope_modules: dict[str, list[str]] = {}
        src_paths: t.MutableSequenceOf[str] = []
        for scope in project_scopes:
            class_counts[scope.project_class] = (
                class_counts.get(scope.project_class, 0) + 1
            )
            analyzed_contract = FlextInfraUtilitiesDocsApi.public_contract(
                scope.path, scope.package_name
            )
            project_contract = (
                FlextInfraUtilitiesDocsContract.docs_current_project_contract(
                    scope.path, analyzed_contract
                )
            )
            scope_modules[scope.name] = (
                FlextInfraUtilitiesDocsGenerateRootMixin._module_names(scope)
            )
            src_dir = scope.path / "src"
            src_exists = (
                FlextInfraUtilitiesDocsGenerateRootMixin._source_directory_exists(
                    src_dir
                )
            )
            if src_exists.failure:
                return r[tuple[DocsRenderedArtifactTuple, ...]].from_failure(src_exists)
            if src_exists.value:
                src_paths.append(src_dir.relative_to(workspace_root).as_posix())
            catalog_entries.append({
                "name": scope.name,
                "project_class": scope.project_class,
                "package_name": scope.package_name,
                "description": str(project_contract.get("description", "")).strip(),
                "api_page": f"../../api-reference/generated/{scope.name}.md",
            })
        rendered: list[tuple[Path, str]] = [
            (
                workspace_root / "mkdocs.yml",
                FlextInfraUtilitiesDocsRender.docs_root_mkdocs(
                    workspace_contract, src_paths
                ),
            ),
            (
                workspace_root / "docs/api-reference/generated/overview.md",
                FlextInfraUtilitiesDocsRender.docs_root_overview_page(
                    workspace_contract,
                    project_count=len(project_scopes),
                    class_counts=class_counts,
                ),
            ),
            (
                workspace_root / "docs/projects/generated/catalog.md",
                FlextInfraUtilitiesDocsRender.docs_project_catalog_page(
                    catalog_entries, exclude_docs=exclude_docs
                ),
            ),
        ]
        projects_index_entries: t.MutableSequenceOf[dict[str, str]] = []
        for scope in project_scopes:
            rendered.append((
                workspace_root / "docs/api-reference/generated" / f"{scope.name}.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    f"{scope.name} Public API", scope.package_name
                ),
            ))
            module_names = scope_modules.get(scope.name, [])
            modules_root = (
                workspace_root
                / "docs/api-reference/generated/projects"
                / scope.name
                / "modules"
            )
            rendered.append((
                modules_root / "index.md",
                FlextInfraUtilitiesDocsRender.docs_modules_index(scope, module_names),
            ))
            for module_name in module_names:
                relative = module_name.removeprefix(f"{scope.package_name}.").replace(
                    ".", "/"
                )
                rendered.append((
                    modules_root / f"{relative}.md",
                    FlextInfraUtilitiesDocsRender.docs_directive_page(
                        module_name, module_name
                    ),
                ))
            projects_index_entries.append({
                "name": scope.name,
                "module_count": str(len(module_names)),
            })
        rendered.append((
            workspace_root / "docs/api-reference/generated/projects/index.md",
            FlextInfraUtilitiesDocsRender.docs_root_projects_index(
                projects_index_entries
            ),
        ))
        api_pruned = (
            FlextInfraUtilitiesDocsGenerateRootMixin._prune_generated_tree_artifacts(
                workspace_root,
                workspace_root / "docs/api-reference/generated",
                rendered,
            )
        )
        if api_pruned.failure:
            return r[tuple[DocsRenderedArtifactTuple, ...]].from_failure(api_pruned)
        projects_pruned = (
            FlextInfraUtilitiesDocsGenerateRootMixin._prune_generated_tree_artifacts(
                workspace_root, workspace_root / "docs/projects/generated", rendered
            )
        )
        if projects_pruned.failure:
            return r[tuple[DocsRenderedArtifactTuple, ...]].from_failure(
                projects_pruned
            )
        return FlextInfraUtilitiesDocsGenerateRootMixin.docs_normalize_artifacts((
            *((workspace_root, path, content) for path, content in rendered),
            *api_pruned.value,
            *projects_pruned.value,
        ))

    @staticmethod
    def docs_scope_artifacts(
        scope: m.Infra.DocScope,
        *,
        workspace_root: Path,
        aggregate_scopes: t.SequenceOf[m.Infra.DocScope],
    ) -> p.Result[t.VariadicTuple[DocsRenderedArtifactTuple]]:
        """Return the rendered artifact inventory for one docs scope."""
        if scope.name == c.Infra.RK_ROOT:
            return FlextInfraUtilitiesDocsGenerateRootMixin.docs_root_artifacts(
                workspace_root, aggregate_scopes
            )
        return FlextInfraUtilitiesDocsGenerateRootMixin.docs_project_artifacts(scope)


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateRootMixin"]
