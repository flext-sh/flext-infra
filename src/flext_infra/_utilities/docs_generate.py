"""Generation helpers for docs services."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesDocs,
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsRender,
    FlextInfraUtilitiesPatterns,
    c,
    m,
    t,
)


class FlextInfraUtilitiesDocsGenerate:
    """Reusable generation helpers exposed through ``u.Infra``."""

    @staticmethod
    def _module_names(contract: t.Infra.ContainerDict) -> list[str]:
        """Extract normalized module names from one docs contract payload."""
        try:
            items = t.Infra.INFRA_SEQ_ADAPTER.validate_python(
                contract.get("modules", [])
            )
        except ValidationError:
            return []
        return [str(item) for item in items]

    @staticmethod
    def _prune_generated_tree(
        root: Path,
        expected: Sequence[Path],
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Prune stale files from one tool-owned generated tree."""
        if not root.exists():
            return []
        expected_paths = {path.resolve() for path in expected}
        removed: MutableSequence[m.Infra.GeneratedFile] = []
        for path in sorted(root.rglob("*.md")):
            if path.resolve() in expected_paths:
                continue
            if apply:
                path.unlink(missing_ok=True)
            removed.append(
                m.Infra.GeneratedFile(
                    path=path.as_posix(),
                    written=apply,
                )
            )
        return removed

    @staticmethod
    def docs_project_generated_files(
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Generate the managed docs artifacts for one FLEXT project."""
        contract = FlextInfraUtilitiesDocsContract.docs_contract(
            scope.path,
            scope.package_name,
        )
        module_names = FlextInfraUtilitiesDocsGenerate._module_names(contract)
        expected_generated: MutableSequence[Path] = [
            scope.path / "docs/api-reference/generated/overview.md",
            scope.path / "docs/api-reference/generated/public-api.md",
            scope.path / "docs/api-reference/generated/modules/index.md",
        ]
        files: MutableSequence[m.Infra.GeneratedFile] = [
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "docs/index.md",
                FlextInfraUtilitiesDocsRender.docs_project_index(scope, contract),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "docs/guides/README.md",
                FlextInfraUtilitiesDocsRender.docs_guides_index(scope),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "docs/api-reference/README.md",
                FlextInfraUtilitiesDocsRender.docs_api_readme(scope, contract),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "mkdocs.yml",
                FlextInfraUtilitiesDocsRender.docs_project_mkdocs(
                    scope,
                    contract,
                    module_names,
                ),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "docs/api-reference/generated/modules/index.md",
                FlextInfraUtilitiesDocsRender.docs_modules_index(
                    scope,
                    module_names,
                ),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "docs/api-reference/generated/overview.md",
                FlextInfraUtilitiesDocsRender.docs_overview_page(scope, contract),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                scope.path / "docs/api-reference/generated/public-api.md",
                FlextInfraUtilitiesDocsRender.docs_directive_page(
                    f"{scope.name} Public API",
                    scope.package_name,
                ),
                apply=apply,
            ),
        ]
        for module_name in module_names:
            relative = module_name.removeprefix(f"{scope.package_name}.").replace(
                ".", "/"
            )
            expected_generated.append(
                scope.path / "docs/api-reference/generated/modules" / f"{relative}.md"
            )
            files.append(
                FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                    scope.path
                    / "docs/api-reference/generated/modules"
                    / f"{relative}.md",
                    FlextInfraUtilitiesDocsRender.docs_directive_page(
                        module_name,
                        module_name,
                    ),
                    apply=apply,
                ),
            )
        files.extend(
            FlextInfraUtilitiesDocsGenerate._prune_generated_tree(
                scope.path / "docs/api-reference/generated",
                expected_generated,
                apply=apply,
            )
        )
        return files

    @staticmethod
    def docs_project_guides_files(
        scope: m.Infra.DocScope,
        *,
        workspace_root: Path,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Return project guide files managed by generation.

        Guide propagation is intentionally disabled; curated guides stay local.
        """
        _ = scope
        _ = workspace_root
        _ = apply
        return []

    @staticmethod
    def docs_project_mkdocs_files(
        scope: m.Infra.DocScope,
        *,
        apply: bool,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Return the managed mkdocs settings file when it does not exist yet."""
        path = scope.path / "mkdocs.yml"
        if path.exists():
            return []
        contract = FlextInfraUtilitiesDocsContract.docs_contract(
            scope.path,
            scope.package_name,
        )
        module_names = FlextInfraUtilitiesDocsGenerate._module_names(contract)
        return [
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                path,
                FlextInfraUtilitiesDocsRender.docs_project_mkdocs(
                    scope,
                    contract,
                    module_names,
                ),
                apply=apply,
                overwrite=False,
            )
        ]

    @staticmethod
    def docs_root_generated_files(
        workspace_root: Path,
        *,
        apply: bool,
        projects: Sequence[str] | None = None,
    ) -> Sequence[m.Infra.GeneratedFile]:
        """Generate root workspace docs artifacts from discovered FLEXT projects."""
        workspace_contract = FlextInfraUtilitiesDocsContract.docs_workspace_contract(
            workspace_root
        )
        scopes_result = FlextInfraUtilitiesDocs.build_scopes(
            workspace_root,
            projects,
            c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
        )
        scopes = (
            [scope for scope in scopes_result.value if scope.name != c.Infra.RK_ROOT]
            if scopes_result.success
            else []
        )
        catalog_entries: MutableSequence[dict[str, str]] = []
        class_counts: dict[str, int] = {}
        for scope in scopes:
            class_counts[scope.project_class] = (
                class_counts.get(scope.project_class, 0) + 1
            )
            project_contract = FlextInfraUtilitiesDocsContract.docs_contract(
                scope.path,
                scope.package_name,
            )
            catalog_entries.append({
                "name": scope.name,
                "project_class": scope.project_class,
                "package_name": scope.package_name,
                "description": str(project_contract.get("description", "")).strip(),
                "api_page": f"../../api-reference/generated/{scope.name}.md",
            })
        expected_api_generated: MutableSequence[Path] = [
            workspace_root / "docs/api-reference/generated/overview.md",
        ]
        expected_project_generated: MutableSequence[Path] = [
            workspace_root / "docs/projects/generated/catalog.md",
        ]
        files: MutableSequence[m.Infra.GeneratedFile] = [
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                workspace_root / "mkdocs.yml",
                FlextInfraUtilitiesDocsRender.docs_root_mkdocs(workspace_contract),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                workspace_root / "docs/api-reference/generated/overview.md",
                FlextInfraUtilitiesDocsRender.docs_root_overview_page(
                    workspace_contract,
                    project_count=len(scopes),
                    class_counts=class_counts,
                ),
                apply=apply,
            ),
            FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                workspace_root / "docs/projects/generated/catalog.md",
                FlextInfraUtilitiesDocsRender.docs_project_catalog_page(
                    catalog_entries
                ),
                apply=apply,
            ),
        ]
        for scope in scopes:
            expected_api_generated.append(
                workspace_root / "docs/api-reference/generated" / f"{scope.name}.md"
            )
            files.append(
                FlextInfraUtilitiesDocsContract.docs_write_if_needed(
                    workspace_root
                    / "docs/api-reference/generated"
                    / f"{scope.name}.md",
                    FlextInfraUtilitiesDocsRender.docs_directive_page(
                        f"{scope.name} Public API",
                        scope.package_name,
                    ),
                    apply=apply,
                ),
            )
        files.extend(
            FlextInfraUtilitiesDocsGenerate._prune_generated_tree(
                workspace_root / "docs/api-reference/generated",
                expected_api_generated,
                apply=apply,
            )
        )
        files.extend(
            FlextInfraUtilitiesDocsGenerate._prune_generated_tree(
                workspace_root / "docs/projects/generated",
                expected_project_generated,
                apply=apply,
            )
        )
        return files

    @staticmethod
    def docs_generate_scope(
        scope: m.Infra.DocScope,
        *,
        apply: bool,
        workspace_root: Path,
        projects: Sequence[str] | None = None,
    ) -> m.Infra.DocsPhaseReport:
        """Generate one scope and persist the standard reports."""
        files = (
            FlextInfraUtilitiesDocsGenerate.docs_root_generated_files(
                workspace_root,
                apply=apply,
                projects=projects,
            )
            if scope.name == c.Infra.RK_ROOT
            else FlextInfraUtilitiesDocsGenerate.docs_project_generated_files(
                scope,
                apply=apply,
            )
        )
        generated = u.count(files, lambda item: item.written)
        _ = u.Cli.json_write(
            scope.report_dir / "generate-summary.json",
            {
                c.Infra.RK_SUMMARY: {
                    c.Infra.RK_SCOPE: scope.name,
                    "generated": generated,
                    "apply": apply,
                },
                "files": [
                    {"path": item.path, "written": item.written} for item in files
                ],
            },
        )
        _ = FlextInfraUtilitiesDocs.write_markdown(
            scope.report_dir / "generate-report.md",
            [
                "# Docs Generate Report",
                "",
                f"Scope: {scope.name}",
                f"Generated files: {generated}",
            ],
        )
        return m.Infra.DocsPhaseReport(
            phase="generate",
            scope=scope.name,
            generated=generated,
            applied=apply,
            source="code-docstring-ssot",
            items=[
                m.Infra.DocsPhaseItemModel(
                    phase="generate",
                    path=item.path,
                    written=item.written,
                )
                for item in files
            ],
            result=c.Infra.STATUS_OK if apply else c.Infra.STATUS_WARN,
            reason="generated" if apply else "dry-run",
            passed=apply,
        )

    @staticmethod
    def docs_project_guide_content(
        content: str,
        project_name: str,
        guide_name: str,
    ) -> str:
        """Return guide content normalized for project-local publication."""
        lines = content.splitlines()
        title = Path(guide_name).stem.replace("_", " ").replace("-", " ").strip()
        body_lines = lines
        for index, line in enumerate(lines):
            match = FlextInfraUtilitiesPatterns.HEADING_RE.match(line)
            if match is None:
                continue
            title = match.group(1).strip() or title
            body_lines = lines[index + 1 :]
            break
        body = "\n".join(body_lines).lstrip()
        heading = f"# {project_name} - {title}"
        return f"{heading}\n\n{body}".rstrip() + "\n"

    @staticmethod
    def docs_sanitize_internal_anchor_links(content: str) -> str:
        """Replace local markdown links with plain text while preserving externals."""
        return FlextInfraUtilitiesPatterns.MARKDOWN_LINK_RE.sub(
            lambda match: (
                match.group(0)
                if match.group(2).startswith(("http://", "https://", "#", "mailto:"))
                else match.group(1)
            ),
            content,
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerate"]
