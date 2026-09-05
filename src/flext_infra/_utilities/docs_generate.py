"""Generation helpers for docs services."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u as cli_u
from flext_core import r
from flext_infra import config
from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra._utilities.docs_render import FlextInfraUtilitiesDocsRender
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra.protocols import p

type _DocsRenderedArtifact = t.Triple[Path, Path, str | None]


class FlextInfraUtilitiesDocsGenerate:
    """Reusable generation helpers exposed through ``u.Infra``."""

    @staticmethod
    def _module_names(scope: m.Infra.DocScope) -> list[str]:
        """Return config-owned public API module names for one distribution."""
        declared = config.Infra.codegen.make.docs.api_modules.get(scope.name, ())
        return [f"{scope.package_name}.{module}" for module in declared]

    @staticmethod
    def _directory_sort_key(path: Path) -> tuple[int, str]:
        """Return the stable parent-first ordering key for a directory."""
        return len(path.parts), path.as_posix()

    @staticmethod
    def _source_directory_exists(path: Path) -> p.Result[bool]:
        """Return source-directory presence after physical path authentication."""
        planned = cli_u.Cli.atomic_plan_directory_chain(path)
        if planned.failure:
            return r[bool].from_failure(planned)
        return r[bool].ok(not planned.value.directories)

    @staticmethod
    def _source_tree_files(
        root: Path,
        *,
        recursive: bool,
        suffixes: frozenset[str],
        excluded_names: frozenset[str] = frozenset(),
    ) -> p.Result[tuple[Path, ...]]:
        """List regular source files through one authenticated tree inventory."""
        planned = cli_u.Cli.atomic_plan_directory_chain(root)
        if planned.failure:
            return r[tuple[Path, ...]].from_failure(planned)
        if planned.value.directories:
            return r[tuple[Path, ...]].ok(())
        inventory = cli_u.Cli.atomic_inventory_physical_tree(root)
        if inventory.failure:
            return r[tuple[Path, ...]].from_failure(inventory)
        return r[tuple[Path, ...]].ok(
            tuple(
                entry.path
                for entry in inventory.value.entries
                if entry.kind == "file"
                and entry.path.suffix in suffixes
                and entry.path.name not in excluded_names
                and (recursive or entry.path.parent == root)
            )
        )

    @staticmethod
    def docs_source_paths(
        workspace_root: Path, extra_roots: t.SequenceOf[Path] = ()
    ) -> p.Result[tuple[Path, ...]]:
        """Discover every physical source consumed by one docs render."""
        roots = FlextInfraUtilitiesDocsScope.docs_workspace_roots(
            workspace_root, extra_roots
        )
        if roots.failure:
            return r[tuple[Path, ...]].from_failure(roots)
        paths: set[Path] = set()
        for root in roots.value:
            for fixed_path in (
                root / c.Infra.GITMODULES,
                root / c.Infra.PYPROJECT_FILENAME,
                root / c.Infra.DIR_DOCS / c.Infra.DOCS_CONFIG_FILENAME,
            ):
                state = cli_u.Cli.atomic_read_binary_file_state(
                    fixed_path, required=False
                )
                if state.failure:
                    return r[tuple[Path, ...]].from_failure(state)
                if state.value.content is not None:
                    paths.add(fixed_path)
            config_paths = FlextInfraUtilitiesDocsGenerate._source_tree_files(
                root / "config", recursive=False, suffixes=frozenset({".yaml", ".yml"})
            )
            if config_paths.failure:
                return r[tuple[Path, ...]].from_failure(config_paths)
            paths.update(config_paths.value)
            source_paths = FlextInfraUtilitiesDocsGenerate._source_tree_files(
                root / c.Infra.DEFAULT_SRC_DIR,
                recursive=True,
                suffixes=frozenset({".py"}),
            )
            if source_paths.failure:
                return r[tuple[Path, ...]].from_failure(source_paths)
            paths.update(source_paths.value)
            guide_paths = FlextInfraUtilitiesDocsGenerate._source_tree_files(
                root / c.Infra.DIR_DOCS / "guides",
                recursive=False,
                suffixes=frozenset({".md"}),
                excluded_names=frozenset({"README.md"}),
            )
            if guide_paths.failure:
                return r[tuple[Path, ...]].from_failure(guide_paths)
            paths.update(guide_paths.value)
        templates_root = Path(__file__).absolute().parent.parent / "templates"
        paths.update({
            templates_root / c.Infra.TEMPLATE_MKDOCS_PROJECT,
            templates_root / c.Infra.TEMPLATE_MKDOCS_ROOT,
        })
        return r[tuple[Path, ...]].ok(tuple(sorted(paths)))

    @staticmethod
    def docs_verify_sources(
        workspace_root: Path,
        source_states: t.SequenceOf[m.Cli.AtomicFileState],
        *,
        extra_roots: t.SequenceOf[Path] = (),
    ) -> p.Result[bool]:
        """Require exact source topology and physical states to remain unchanged."""
        discovered = FlextInfraUtilitiesDocsGenerate.docs_source_paths(
            workspace_root, extra_roots
        )
        if discovered.failure:
            return r[bool].from_failure(discovered)
        expected_paths = tuple(state.path for state in source_states)
        if discovered.value != expected_paths:
            added = sorted(set(discovered.value).difference(expected_paths))
            removed = sorted(set(expected_paths).difference(discovered.value))
            return r[bool].fail(
                "docs source topology changed during planning: "
                f"added={[path.as_posix() for path in added]}, "
                f"removed={[path.as_posix() for path in removed]}"
            )
        current = FlextInfraUtilitiesDocsContract.docs_snapshot_sources(
            discovered.value
        )
        if current.failure:
            return r[bool].from_failure(current)
        for expected, observed in zip(source_states, current.value, strict=True):
            if observed != expected:
                return r[bool].fail(
                    f"docs source changed during planning: {expected.path}"
                )
        return r[bool].ok(True)

    @staticmethod
    def docs_normalize_artifacts(
        artifacts: t.SequenceOf[_DocsRenderedArtifact],
    ) -> p.Result[tuple[_DocsRenderedArtifact, ...]]:
        """Validate one unique lexical owner and target without dereferencing."""
        normalized: list[_DocsRenderedArtifact] = []
        targets: set[Path] = set()
        for project, target, content in artifacts:
            if (
                not project.is_absolute()
                or not target.is_absolute()
                or ".." in project.parts
                or ".." in target.parts
            ):
                return r[tuple[_DocsRenderedArtifact, ...]].fail(
                    f"docs publication paths must be absolute and lexical: {target}"
                )
            try:
                target.relative_to(project)
            except ValueError:
                return r[tuple[_DocsRenderedArtifact, ...]].fail(
                    f"docs publication target escapes project {project}: {target}"
                )
            if target in targets:
                return r[tuple[_DocsRenderedArtifact, ...]].fail(
                    f"duplicate docs publication target: {target}"
                )
            targets.add(target)
            normalized.append((project, target, content))
        return r[tuple[_DocsRenderedArtifact, ...]].ok(tuple(normalized))

    @staticmethod
    def docs_required_directories(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[tuple[Path, ...]]:
        """Return unique target directories ordered parent before child."""
        required: set[Path] = set()
        for scoped in bundle.scopes:
            for artifact in scoped.artifacts:
                if artifact.desired_content is None:
                    continue
                parent = scoped.scope.path
                for part in artifact.relative_path.parent.parts:
                    parent /= part
                    required.add(parent)
        return r[tuple[Path, ...]].ok(
            tuple(
                sorted(
                    required, key=FlextInfraUtilitiesDocsGenerate._directory_sort_key
                )
            )
        )

    @staticmethod
    def docs_file_plans(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Snapshot targets from the canonical rendered artifact inventory."""
        workspace_root = bundle.scopes[0].scope.path
        scope_roots = tuple(scoped.scope.path for scoped in bundle.scopes)
        stable = FlextInfraUtilitiesDocsGenerate.docs_verify_sources(
            workspace_root, bundle.source_states, extra_roots=scope_roots
        )
        if stable.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(stable)
        plans: list[m.Infra.CodegenFilePlan] = []
        for scoped in bundle.scopes:
            for artifact in scoped.artifacts:
                planned = FlextInfraUtilitiesDocsContract.docs_file_plan(
                    scoped.scope.path,
                    scoped.scope.path / artifact.relative_path,
                    artifact.desired_content,
                    desired_mode=artifact.desired_mode,
                    source_states=bundle.source_states,
                )
                if planned.failure:
                    return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(planned)
                plans.append(planned.value)
        stable = FlextInfraUtilitiesDocsGenerate.docs_verify_sources(
            workspace_root, bundle.source_states, extra_roots=scope_roots
        )
        if stable.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(stable)
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(tuple(plans))

    @staticmethod
    def _prune_generated_tree_artifacts(
        project: Path, root: Path, rendered: t.SequenceOf[tuple[Path, str]]
    ) -> p.Result[tuple[_DocsRenderedArtifact, ...]]:
        """Describe stale files owned by one generated tree as absent artifacts."""
        planned = cli_u.Cli.atomic_plan_directory_chain(root)
        if planned.failure:
            return r[tuple[_DocsRenderedArtifact, ...]].from_failure(planned)
        if planned.value.directories:
            return r[tuple[_DocsRenderedArtifact, ...]].ok(())
        inventory = cli_u.Cli.atomic_inventory_physical_tree(root)
        if inventory.failure:
            return r[tuple[_DocsRenderedArtifact, ...]].from_failure(inventory)
        expected_paths = {
            path for path, _content in rendered if path.is_relative_to(root)
        }
        return r[tuple[_DocsRenderedArtifact, ...]].ok(
            tuple(
                (project, entry.path, None)
                for entry in inventory.value.entries
                if entry.kind == "file"
                and entry.path.suffix == ".md"
                and entry.path not in expected_paths
            )
        )

    @staticmethod
    def docs_project_artifacts(
        scope: m.Infra.DocScope,
    ) -> p.Result[tuple[_DocsRenderedArtifact, ...]]:
        """Render the complete target inventory for one FLEXT project."""
        analyzed_contract = FlextInfraUtilitiesDocsApi.public_contract(
            scope.path, scope.package_name
        )
        contract = FlextInfraUtilitiesDocsContract.docs_current_project_contract(
            scope.path, analyzed_contract
        )
        module_names = FlextInfraUtilitiesDocsGenerate._module_names(scope)
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
        pruned = FlextInfraUtilitiesDocsGenerate._prune_generated_tree_artifacts(
            scope.path, scope.path / "docs/api-reference/generated", rendered
        )
        if pruned.failure:
            return r[tuple[_DocsRenderedArtifact, ...]].from_failure(pruned)
        return FlextInfraUtilitiesDocsGenerate.docs_normalize_artifacts((
            *((scope.path, path, content) for path, content in rendered),
            *pruned.value,
        ))

    @staticmethod
    def docs_root_artifacts(
        workspace_root: Path, scopes: t.SequenceOf[m.Infra.DocScope]
    ) -> p.Result[tuple[_DocsRenderedArtifact, ...]]:
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
        # flext-o6h5 (agent: kimi) — root site aggregates per-project module
        # pages: module names come from the already-loaded public contract
        # and src paths feed the mkdocstrings resolution block.
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
            scope_modules[scope.name] = FlextInfraUtilitiesDocsGenerate._module_names(
                scope
            )
            src_dir = scope.path / "src"
            src_exists = FlextInfraUtilitiesDocsGenerate._source_directory_exists(
                src_dir
            )
            if src_exists.failure:
                return r[tuple[_DocsRenderedArtifact, ...]].from_failure(src_exists)
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
            # flext-o6h5 (agent: kimi) — per-project module pages reuse the
            # exact project-scope renderers (docs_modules_index +
            # docs_directive_page); index lives inside modules/ so relative
            # links resolve identically to the project-scope layout.
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
                module_path = modules_root / f"{relative}.md"
                rendered.append((
                    module_path,
                    FlextInfraUtilitiesDocsRender.docs_directive_page(
                        module_name, module_name
                    ),
                ))
            projects_index_entries.append({
                "name": scope.name,
                "module_count": str(len(module_names)),
            })
        projects_index_path = (
            workspace_root / "docs/api-reference/generated/projects/index.md"
        )
        rendered.append((
            projects_index_path,
            FlextInfraUtilitiesDocsRender.docs_root_projects_index(
                projects_index_entries
            ),
        ))
        api_pruned = FlextInfraUtilitiesDocsGenerate._prune_generated_tree_artifacts(
            workspace_root, workspace_root / "docs/api-reference/generated", rendered
        )
        if api_pruned.failure:
            return r[tuple[_DocsRenderedArtifact, ...]].from_failure(api_pruned)
        projects_pruned = (
            FlextInfraUtilitiesDocsGenerate._prune_generated_tree_artifacts(
                workspace_root, workspace_root / "docs/projects/generated", rendered
            )
        )
        if projects_pruned.failure:
            return r[tuple[_DocsRenderedArtifact, ...]].from_failure(projects_pruned)
        return FlextInfraUtilitiesDocsGenerate.docs_normalize_artifacts((
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
    ) -> p.Result[tuple[_DocsRenderedArtifact, ...]]:
        """Return the rendered artifact inventory for one docs scope."""
        if scope.name == c.Infra.RK_ROOT:
            return FlextInfraUtilitiesDocsGenerate.docs_root_artifacts(
                workspace_root, aggregate_scopes
            )
        return FlextInfraUtilitiesDocsGenerate.docs_project_artifacts(scope)


__all__: list[str] = ["FlextInfraUtilitiesDocsGenerate"]
