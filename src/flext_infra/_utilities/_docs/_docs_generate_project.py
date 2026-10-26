"""Per-project artifact rendering for documentation generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesProjectManagedArtifacts
from flext_infra._utilities._docs._docs_generate_plan import (
    FlextInfraUtilitiesDocsGeneratePlanMixin,
)
from flext_infra._utilities._docs._docs_guides import FlextInfraUtilitiesDocsGuidesMixin
from flext_infra._utilities._docs.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities._docs.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities._docs.docs_render import FlextInfraUtilitiesDocsRender


class FlextInfraUtilitiesDocsGenerateProjectMixin(
    FlextInfraUtilitiesDocsGeneratePlanMixin,
):
    """Render the complete desired artifact inventory for one project scope."""

    @staticmethod
    def _module_names(
        scope: m.Infra.DocScope,
    ) -> list[str]:
        """Return the public top-level modules of the scope's package.

        The public API is what the package itself declares public: every
        top-level module whose name is not private. It is derived from the
        package tree, never listed per distribution in configuration.

        Returns:
            The public top-level modules of the scope's package.

        """
        if not scope.package_name:
            return []
        package_dir = scope.path / c.Infra.DEFAULT_SRC_DIR / scope.package_name
        return [
            f"{scope.package_name}.{module.stem}"
            for module in sorted(package_dir.glob(c.Infra.EXT_PYTHON_GLOB))
            if module.suffix == ".py" and not module.stem.startswith("_")
        ]

    @staticmethod
    def docs_project_api_artifacts(
        scope: m.Infra.DocScope,
        *,
        width: int,
    ) -> list[t.Pair[Path, str]]:
        """Render package API pages before their owning tree is pruned.

        Returns:
            The resulting ``list[t.Pair[Path, str]]``.

        """
        module_names = FlextInfraUtilitiesDocsGenerateProjectMixin._module_names(scope)
        api_root = scope.path / "docs/api-reference/generated"
        rendered = [
            (
                api_root / "public-api.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    f"{scope.name} "
                    f"{scope.documentation_text(c.Infra.DocumentationText.PUBLIC_API)}",
                    scope.package_name,
                    width=width,
                ),
            ),
            (
                api_root / "modules/index.md",
                FlextInfraUtilitiesDocsRender.docs_modules_index(
                    scope, module_names, width=width
                ),
            ),
        ]
        for module_name in module_names:
            relative = module_name.removeprefix(f"{scope.package_name}.").replace(
                ".",
                "/",
            )
            rendered.append((
                api_root / "modules" / f"{relative}.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    module_name, module_name, width=width
                ),
            ))
        return rendered

    @staticmethod
    def docs_project_artifacts(
        scope: m.Infra.DocScope,
        *,
        repository_root: Path,
    ) -> p.Result[t.VariadicTuple[t.Infra.DocsRenderedArtifactTuple]]:
        """Render the complete target inventory for one FLEXT project.

        Returns:
            The resulting
                ``p.Result[t.VariadicTuple[t.Infra.DocsRenderedArtifactTuple]]``.

        """
        tooling = FlextInfraUtilitiesProjectManagedArtifacts.load_tooling_inputs(
            scope.path
        )
        if tooling.failure:
            return r[t.VariadicTuple[t.Infra.DocsRenderedArtifactTuple]].from_failure(
                tooling
            )
        width = FlextInfraUtilitiesDocsRender.docs_markdown_line_length(
            tooling.value.document
        )
        guides = FlextInfraUtilitiesDocsGuidesMixin.docs_project_guides_artifacts(
            scope,
            repository_root=repository_root,
        )
        if guides.failure:
            return r[t.VariadicTuple[t.Infra.DocsRenderedArtifactTuple]].from_failure(
                guides,
            )
        guide_paths = {
            path
            for path in (scope.path / "docs/guides").glob("*.md")
            if path.name != "README.md" and path.is_file()
        }
        guide_contents = (
            {path: path.read_text(encoding=c.DEFAULT_ENCODING) for path in guide_paths}
            if scope.documentation_language == "pt-BR"
            else {}
        )
        for _project, path, content in guides.value:
            if content is None:
                guide_paths.discard(path)
                guide_contents.pop(path, None)
            else:
                guide_paths.add(path)
                guide_contents[path] = content
        guide_titles = {
            path: title
            for path, content in guide_contents.items()
            if scope.documentation_language == "pt-BR"
            and (title := FlextInfraUtilitiesDocsContract.docs_contract_title(content))
        }
        analyzed_contract = FlextInfraUtilitiesDocsApi.public_contract(
            scope.path,
            scope.package_name,
        )
        contract = FlextInfraUtilitiesDocsContract.docs_current_project_contract(
            scope.path,
            analyzed_contract,
        )
        module_names = FlextInfraUtilitiesDocsGenerateProjectMixin._module_names(scope)
        rendered: list[t.Pair[Path, str]] = [
            (
                scope.path / "README.md",
                FlextInfraUtilitiesDocsRender.docs_project_readme(
                    scope, contract, width=width
                ),
            ),
            (
                scope.path / "docs/index.md",
                FlextInfraUtilitiesDocsRender.docs_project_index(
                    scope, contract, width=width
                ),
            ),
            (
                scope.path / "docs/guides/README.md",
                FlextInfraUtilitiesDocsRender.docs_guides_index(
                    scope,
                    guide_paths=tuple(sorted(guide_paths)),
                    guide_titles=guide_titles,
                    width=width,
                ),
            ),
            (
                scope.path / "docs/api-reference/README.md",
                FlextInfraUtilitiesDocsRender.docs_api_readme(
                    scope, contract, module_names, width=width
                ),
            ),
            (
                scope.path / "mkdocs.yml",
                (
                    # A standalone repository publishes its root MkDocs site
                    # under the canonical repository identity: the per-project
                    # " Documentation" suffix belongs to member sites, never to
                    # the repository root (root title contract, c6db82fb2).
                    FlextInfraUtilitiesDocsRender.docs_root_mkdocs(
                        contract,
                        ("src",),
                        repository_root=scope.path,
                        documentation_language=scope.documentation_language,
                    )
                    if scope.path == repository_root
                    else FlextInfraUtilitiesDocsRender.docs_project_mkdocs(
                        scope,
                        contract,
                    )
                ),
            ),
            (
                scope.path / "docs/api-reference/generated/overview.md",
                FlextInfraUtilitiesDocsRender.docs_overview_page(
                    scope, contract, module_names, width=width
                ),
            ),
            *FlextInfraUtilitiesDocsGenerateProjectMixin.docs_project_api_artifacts(
                scope, width=width
            ),
        ]
        pruned = (
            FlextInfraUtilitiesDocsGenerateProjectMixin._prune_generated_tree_artifacts(
                scope.path,
                scope.path / "docs/api-reference/generated",
                rendered,
            )
        )
        if pruned.failure:
            return r[t.VariadicTuple[t.Infra.DocsRenderedArtifactTuple]].from_failure(
                pruned,
            )
        return FlextInfraUtilitiesDocsGenerateProjectMixin.docs_normalize_artifacts((
            *((scope.path, path, content) for path, content in rendered),
            *guides.value,
            *pruned.value,
        ))


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerateProjectMixin"]
