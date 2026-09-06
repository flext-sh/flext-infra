"""Per-project artifact rendering for documentation generation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import config
from flext_infra._utilities._docs_generate_plan import (
    DocsRenderedArtifactTuple,
    FlextInfraUtilitiesDocsGeneratePlanMixin,
)
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.protocols import p


class FlextInfraUtilitiesDocsGenerateProjectMixin(
    FlextInfraUtilitiesDocsGeneratePlanMixin
):
    """Render the complete desired artifact inventory for one project scope."""

    @staticmethod
    def _module_names(scope: m.Infra.DocScope) -> list[str]:
        """Return config-owned public API module names for one distribution."""
        declared = config.Infra.codegen.make.docs.api_modules.get(scope.name, ())
        return [f"{scope.package_name}.{module}" for module in declared]

    @staticmethod
    def docs_project_artifacts(
        scope: m.Infra.DocScope,
    ) -> p.Result[tuple[DocsRenderedArtifactTuple, ...]]:
        """Render the complete target inventory for one FLEXT project."""
        analyzed_contract = FlextInfraUtilitiesDocsApi.public_contract(
            scope.path, scope.package_name
        )
        contract = FlextInfraUtilitiesDocsContract.docs_current_project_contract(
            scope.path, analyzed_contract
        )
        module_names = FlextInfraUtilitiesDocsGenerateProjectMixin._module_names(scope)
        rendered: list[tuple[Path, str]] = [
            (
                scope.path / "README.md",
                FlextInfraUtilitiesDocsRender.docs_project_readme(scope, contract),
            ),
            (
                scope.path / "docs/index.md",
                FlextInfraUtilitiesDocsRender.docs_project_index(scope, contract),
            ),
            (
                scope.path / "docs/guides/README.md",
                FlextInfraUtilitiesDocsRender.docs_guides_index(scope),
            ),
            (
                scope.path / "docs/api-reference/README.md",
                FlextInfraUtilitiesDocsRender.docs_api_readme(scope, contract),
            ),
            (
                scope.path / "mkdocs.yml",
                FlextInfraUtilitiesDocsRender.docs_project_mkdocs(
                    scope, contract, module_names
                ),
            ),
            (
                scope.path / "docs/api-reference/generated/modules/index.md",
                FlextInfraUtilitiesDocsRender.docs_modules_index(scope, module_names),
            ),
            (
                scope.path / "docs/api-reference/generated/overview.md",
                FlextInfraUtilitiesDocsRender.docs_overview_page(scope, contract),
            ),
            (
                scope.path / "docs/api-reference/generated/public-api.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    f"{scope.name} Public API", scope.package_name
                ),
            ),
        ]
        for module_name in module_names:
            relative = module_name.removeprefix(f"{scope.package_name}.").replace(
                ".", "/"
            )
            rendered.append((
                scope.path / "docs/api-reference/generated/modules" / f"{relative}.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    module_name, module_name
                ),
            ))
        pruned = (
            FlextInfraUtilitiesDocsGenerateProjectMixin._prune_generated_tree_artifacts(
                scope.path, scope.path / "docs/api-reference/generated", rendered
            )
        )
        if pruned.failure:
            return r[tuple[DocsRenderedArtifactTuple, ...]].from_failure(pruned)
        return FlextInfraUtilitiesDocsGenerateProjectMixin.docs_normalize_artifacts((
            *((scope.path, path, content) for path, content in rendered),
            *pruned.value,
        ))


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateProjectMixin"]
