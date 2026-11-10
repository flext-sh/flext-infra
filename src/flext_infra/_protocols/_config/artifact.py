# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/artifact
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract
from flext_infra._typings import FlextInfraTypesBase

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import (
        FlextInfraProtocolsDepsToolConfig,
        FlextInfraProtocolsLayout,
        FlextInfraProtocolsMiseToolchain,
        FlextInfraProtocolsProjectArtifacts,
    )
    from flext_infra._protocols._codegen import (
        FlextInfraProtocolsCodegenPipeline,
        FlextInfraProtocolsCodegenTransaction,
    )
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigContexts,
        FlextInfraProtocolsConfigMake,
        FlextInfraProtocolsConfigProvider,
        FlextInfraProtocolsConfigRender,
        FlextInfraProtocolsConfigRepository,
        FlextInfraProtocolsConfigScaffold,
        FlextInfraProtocolsConfigTemplates,
        FlextInfraProtocolsConfigWorkspace,
    )


class FlextInfraProtocolsConfigArtifact:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenArtifactSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Basename of the resource."""
            ...

        @property
        def is_dir(self) -> bool:
            """Directory (vs file) resource."""
            ...

        @property
        def vscode_exclude(self) -> bool:
            """Feed VS Code files.exclude + search.exclude."""
            ...

        @property
        def watch_exclude(self) -> bool:
            """Feed VS Code files.watcherExclude."""
            ...

        @property
        def gitignore(self) -> bool:
            """Feed the Python/tool section of .gitignore."""
            ...

        @property
        def source_scan_ignore(self) -> bool:
            """Feed source_scan.ignored_resources."""
            ...

        @property
        def retired_typing_root(self) -> bool:
            """Owned retired typing tree retained in path-policy inventory."""
            ...

        @property
        def generated_source(self) -> bool:
            """Structural member projected from the owning model.

            Tracked directory of generator output that ships and imports as a
            regular package: never gitignored and given a generated package
            initializer, without excluding executable source from analysis or
            establishing third-party provenance.
            """
            ...

        @property
        def analysis_exclude(self) -> bool:
            """Structural member projected from the owning model.

            Feed the declared directory-exclusion registry: tree-walking analyzers
            (discovery, docs, markdown, census, worktree deltas) never descend into
            this machine-emitted artifact.
            """
            ...

        @property
        def resolver_owned(self) -> bool:
            """Structural member projected from the owning model.

            Package-manager lockfile emission: sibling packages of one tool family
            share resolved dependency lines by construction, so the resolver owns
            the content and clone detection never reads it.
            """
            ...

    @runtime_checkable
    class DeclaredExclusionsSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def tool_state(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Non-artifact tool homes and scratch roots (agent sync home, transient
            test scratch).
            """
            ...

        @property
        def archive_roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Immutable archive contracts: historical evidence trees that are never
            production input to any analyzer.
            """
            ...

        @property
        def docs(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Docs-scanner delta: generated sites and documentation report outputs
            excluded from live documentation.
            """
            ...

        @property
        def markdown(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Positive repository-relative Markdown exclusion patterns not derived
            from analyzer or full-generated artifact ownership.
            """
            ...

        @property
        def docs_publish(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Repository-relative page patterns excluded from site publication, not
            from physical documentation copying.
            """
            ...

        @property
        def docs_copy(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Repository-relative documentation patterns excluded from physical
            copying and site publication.
            """
            ...

        @property
        def pyproject_scan(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            pyproject-discovery delta: non-productive trees whose pyproject tables
            never declare workspace membership.
            """
            ...

        @property
        def check(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Quality-check delta: editor/agent state, report outputs, and caches
            excluded from every check surface.
            """
            ...

        @property
        def validation_clone(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Validation-clone delta: directories excluded when cloning a project tree
            for post-apply validation.
            """
            ...

        @property
        def worktree_transaction(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Worktree-transaction delta: cache directories excluded from isolated
            worktree transaction deltas.
            """
            ...

        @property
        def deps_discovery(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Dependency-discovery delta: directories skipped while searching for
            pyproject declarations.
            """
            ...

        @property
        def scenario_data_roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Project-relative fixture materialization and pytest collection roots:
            scenario data that no analyzer lints, formats or types.
            """
            ...

    @runtime_checkable
    class CodegenGovernedPlanRequest(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Repository root of the artifact."""
            ...

        @property
        def relative(self) -> Path:
            """Artifact path relative to the repository root."""
            ...

        @property
        def governed(self) -> FlextInfraProtocolsConfigTemplates.ManagedFileSpec:
            """Declared governance for the artifact."""
            ...

        @property
        def current(self) -> str:
            """Current on-disk text; empty when absent."""
            ...

        @property
        def vscode_spec(
            self,
        ) -> FlextInfraProtocolsConfigTemplates.CodegenVscodeSpec | None:
            """Declared vscode settings spec when present."""
            ...

    @runtime_checkable
    class CodegenLocCapSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def max_lines(self) -> int:
            """Per-module code-LOC ceiling."""
            ...

    @runtime_checkable
    class CodegenAstGrepRendererSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            u.Infra renderer mapping a project root to native rule documents keyed
            by '<shape>' or '<shape>--<qualifier>'.
            """
            ...

        @property
        def shapes(self) -> tuple[t.NonEmptyStr, ...]:
            """Rule shapes the renderer is registered to emit."""
            ...

        @property
        def shapes_from(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            u.Infra producer deriving the renderer's shapes from their source of
            truth, instead of a declared list.
            """
            ...

        @property
        def facts(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            u.Infra facts producer whose typed model the stage passes to the
            renderer, computed once per generation.
            """
            ...

        @property
        def enforce(self) -> FlextInfraTypesBase.EnforcementIds:
            """Laws every rendered document enforces (stamped)."""
            ...

    @runtime_checkable
    class CodegenAstGrepSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def producers(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            u.Infra producer names; each maps a project root to its native utility
            rules keyed by utility id.
            """
            ...

        @property
        def renderers(
            self,
        ) -> tuple[FlextInfraProtocolsConfigArtifact.CodegenAstGrepRendererSpec, ...]:
            """Structural member projected from the owning model.

            Renderers emitting generated native rule documents, run after the
            utility producers.
            """
            ...

        @property
        def scopes(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            u.Infra file-scope producer names; each maps a project root to project-
            relative file sets keyed by the selector a catalog rule names under
            metadata.scope.
            """
            ...

    @runtime_checkable
    class RetiredProjectionSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> t.NonEmptyStr:
            """Repository-relative retired projection path."""
            ...

        @property
        def evidence(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Literal bytes the generated file carries; removal requires the match so
            conform never deletes a hand-written file.
            """
            ...

    @runtime_checkable
    class CodegenModesSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_default(self) -> int:
            """Rendered artifacts without a managed mode."""
            ...

        @property
        def file_private(self) -> int:
            """Engine-private lock and mutex files."""
            ...

        @property
        def directory_private(self) -> int:
            """Engine-only state and staging trees."""
            ...

        @property
        def directory_generated(self) -> int:
            """Generated directory trees in consumers."""
            ...

    @runtime_checkable
    class CodegenArtifactScopeSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def artifacts(
            self,
        ) -> tuple[FlextInfraProtocolsConfigArtifact.CodegenArtifactSpec, ...]:
            """Structural member projected from the owning model.

            Ephemeral/generated artifact SSOT; every ignore/exclude projection
            derives from this list.
            """
            ...

        @property
        def vscode_files_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.exclude`` entries from the artifact SSOT."""
            ...

        @property
        def vscode_watcher_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.watcherExclude`` entries from the SSOT."""
            ...

        @property
        def vscode_search_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``search.exclude`` entries from the artifact SSOT."""
            ...

        @property
        def source_scan_ignored(self) -> tuple[str, ...]:
            """Derived ``source_scan.ignored_resources`` names from the SSOT."""
            ...

        @property
        def generated_sources(self) -> tuple[str, ...]:
            """Derived names of the tracked generator-owned source trees."""
            ...

        @property
        def generated_source_globs(self) -> tuple[str, ...]:
            """Derived generation-ownership globs, not analyzer exemptions."""
            ...

    @runtime_checkable
    class CodegenEngineSpec(CodegenArtifactScopeSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def runtime_module_overrides(
            self,
        ) -> Mapping[
            t.NonEmptyStr, Mapping[Literal["config", "settings"], t.NonEmptyStr]
        ]:
            """Structural member projected from the owning model.

            Runtime module stems by canonical project distribution and closed
            singleton role (config/settings); omitted roles retain the fleet module
            name. Declared stems must be public Python identifiers distinct from
            root aliases and each other.
            """
            ...

        @property
        def repository(self) -> FlextInfraProtocolsConfigWorkspace.RepositoryDeltaSpec:
            """This repository's self-owned declaration differences."""
            ...

        @property
        def version(self) -> int:
            """Config schema version."""
            ...

        @property
        def retired_projections(
            self,
        ) -> tuple[str | FlextInfraProtocolsConfigArtifact.RetiredProjectionSpec, ...]:
            """Structural member projected from the owning model.

            Repository-relative generated projections that no template renders any
            more; generation removes them from consumers. A plain string removes
            files carrying the generated marker; a mapping adds the exact evidence
            bytes required for removal.
            """
            ...

        @property
        def fresh_import_workers(self) -> int:
            """Concurrent fresh-import subprocesses."""
            ...

        @property
        def lint_snapshot_workers(self) -> int:
            """Concurrent protected-edit lint snapshot threads."""
            ...

        @property
        def loc_cap(self) -> FlextInfraProtocolsConfigArtifact.CodegenLocCapSpec:
            """Per-module code-LOC ceiling policy."""
            ...

        @property
        def ast_grep(self) -> FlextInfraProtocolsConfigArtifact.CodegenAstGrepSpec:
            """Generated native ast-grep utility rules."""
            ...

        @property
        def modes(self) -> FlextInfraProtocolsConfigArtifact.CodegenModesSpec:
            """Filesystem modes the pipeline emits (the mode SSOT)."""
            ...

        @property
        def toolchain(self) -> FlextInfraProtocolsMiseToolchain.ToolchainSpec:
            """Exact generated toolchain."""
            ...

    @runtime_checkable
    class CodegenCiSpec(CodegenEngineSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def github_actions(
            self,
        ) -> Mapping[str, FlextInfraProtocolsConfigProvider.GithubActionPinSpec]:
            """Immutable GitHub Action catalog."""
            ...

        @property
        def checkout_submodules(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Default actions/checkout submodules mode for every generated workflow.
            'false' keeps CI green on projects whose submodules are private: the
            default GITHUB_TOKEN cannot clone sibling private repositories and
            'recursive' aborts the job at checkout.
            """
            ...

        @property
        def checkout_submodules_overrides(self) -> Mapping[str, str]:
            """Structural member projected from the owning model.

            Per-distribution override of checkout_submodules, for projects that
            really do exercise their subprojects in CI.
            """
            ...

        @property
        def ci_private_submodules(
            self,
        ) -> Mapping[str, FlextInfraProtocolsConfigProvider.CiPrivateSubmodulesSpec]:
            """Structural member projected from the owning model.

            Per-distribution private submodule deploy-key contracts rendered into
            generated CI before make setup.
            """
            ...

        @property
        def ci_private_dependency_auth(
            self,
        ) -> Mapping[
            str, FlextInfraProtocolsConfigProvider.CiPrivateDependencyAuthSpec
        ]:
            """Structural member projected from the owning model.

            Per-distribution GitHub App identity minting installation tokens for
            private git dependencies in generated CI.
            """
            ...

        @property
        def ci_system_packages(self) -> Mapping[str, tuple[t.NonEmptyStr, ...]]:
            """Structural member projected from the owning model.

            Per-distribution runner packages (Ubuntu apt names) the generated CI
            installs before the gates run.
            """
            ...

        @property
        def ci_package_registry_read(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Distributions whose generated CI gates resolve GitHub Packages (for
            example private GHCR OCI dependencies); only these grant the ci job
            packages: read, every other job and distribution stays contents-only.
            """
            ...

        @property
        def sonarcloud(self) -> FlextInfraProtocolsConfigRender.SonarcloudSpec:
            """Fleet SonarCloud automatic-analysis scope policy."""
            ...

    @runtime_checkable
    class CodegenWorkspaceSpec(CodegenCiSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def infra_repository(
            self,
        ) -> FlextInfraProtocolsConfigProvider.RepositorySourceSpec:
            """Canonical infrastructure repository identity."""
            ...

        @property
        def branch_policy(self) -> FlextInfraProtocolsConfigProvider.BranchPolicySpec:
            """Global branch policy (CI triggers, integration line)."""
            ...

        @property
        def profiles(self) -> tuple[FlextInfraProtocolsConfigContexts.ProfileSpec, ...]:
            """Ordered Make profiles."""
            ...

        @property
        def make(self) -> FlextInfraProtocolsConfigMake.MakeSpec:
            """Canonical Make contract."""
            ...

        @property
        def vscode(self) -> FlextInfraProtocolsConfigTemplates.CodegenVscodeSpec:
            """Canonical VS Code settings merge contract."""
            ...

        @property
        def exclusions(
            self,
        ) -> FlextInfraProtocolsConfigArtifact.DeclaredExclusionsSpec:
            """Structural member projected from the owning model.

            Declared directory-exclusion registry: the one SSOT every scanner
            exclusion derives from.
            """
            ...

        @property
        def layout(self) -> FlextInfraProtocolsLayout.LayoutSpec:
            """Structural member projected from the owning model.

            Declarative project-layout conformance contract consumed by the layout
            engine and the layout quality gate.
            """
            ...

    @runtime_checkable
    class CodegenConfigSpec(CodegenWorkspaceSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def analyzer_exclude_globs(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Project declared artifacts and walker exclusions into analyzer globs.
            """
            ...

        @property
        def markdown_exclude_globs(self) -> tuple[str, ...]:
            """Derive Markdown scope without hiding authored or merged documents."""
            ...

        @property
        def docs_publish_patterns(self) -> tuple[str, ...]:
            """Compose page and copy exclusions in repository coordinates."""
            ...

        @property
        def docs_copy_patterns(self) -> tuple[str, ...]:
            """Expose declared copy exclusions without importing Markdown scope."""
            ...

        @property
        def analysis_excluded_dirs(self) -> tuple[str, ...]:
            """Derived base directory exclusion set every walker composes."""
            ...

        @property
        def docs_excluded_dirs(self) -> tuple[str, ...]:
            """Derived live-documentation exclusion set."""
            ...

        @property
        def pyproject_scan_excluded_dirs(self) -> tuple[str, ...]:
            """Derived pyproject-discovery exclusion set."""
            ...

        @property
        def check_excluded_dirs(self) -> tuple[str, ...]:
            """Derived quality-check exclusion set."""
            ...

        @property
        def validation_clone_excluded_dirs(self) -> tuple[str, ...]:
            """Derived validation-clone exclusion set."""
            ...

        @property
        def worktree_transaction_excluded_dirs(self) -> tuple[str, ...]:
            """Derived worktree-transaction exclusion set."""
            ...

        @property
        def deps_discovery_excluded_dirs(self) -> tuple[str, ...]:
            """Derived dependency-discovery exclusion set."""
            ...

        @property
        def resolver_owned_files(self) -> tuple[str, ...]:
            """Derived filenames whose content the package resolver owns."""
            ...

        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraProtocolsConfigScaffold.ScaffoldGitignoreSectionSpec, ...]:
            """Structural member projected from the owning model.

            Derived canonical ``.gitignore`` sections (SSOT order, deduplicated).
            """
            ...

        @property
        def gitignore_artifact_patterns(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Derived ``.gitignore`` artifact patterns from the SSOT (stable order).
            """
            ...

        @property
        def managed_file_specs(
            self,
        ) -> tuple[FlextInfraProtocolsConfigTemplates.ManagedFileSpec, ...]:
            """Derive managed views once per catalog from its single declaration."""
            ...

        @property
        def scaffold(self) -> FlextInfraProtocolsConfigScaffold.ScaffoldSpec:
            """Typed new-project scaffold policy."""
            ...

        @property
        def templates(self) -> FlextInfraProtocolsConfigTemplates.TemplatesSpec:
            """Single artifact declaration and ownership catalog."""
            ...

    @runtime_checkable
    class RepositoryDeclarationInputs(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def spec(self) -> FlextInfraProtocolsConfigWorkspace.RepositoryDeltaSpec:
            """Validated repository declaration subsection."""
            ...

        @property
        def kind(self) -> c.Infra.ProjectKind:
            """Structural member projected from the owning model.

            Governance kind the repository declares, validated once when the
            declaration is loaded.
            """
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Exact consulted configuration input states."""
            ...

    @runtime_checkable
    class CodegenInputs(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def spec(self) -> FlextInfraProtocolsConfigArtifact.CodegenConfigSpec:
            """Validated effective repository codegen declaration."""
            ...

        @property
        def kind(self) -> c.Infra.ProjectKind:
            """Structural member projected from the owning model.

            Governance kind the repository declares, validated once when the
            declaration is loaded.
            """
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Exact consulted config input states."""
            ...

    @runtime_checkable
    class CodegenConformSurfaceContract(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def destinations(self) -> frozenset[str] | None:
            """Output paths selected for conformance planning."""
            ...

        @property
        def complete_governed(self) -> bool:
            """Whether every governed output is represented."""
            ...

        @property
        def delegates(self) -> bool:
            """Whether delegated templates are planned."""
            ...

        @property
        def pyproject(self) -> bool:
            """Whether project metadata is planned."""
            ...

        @property
        def templates(self) -> bool:
            """Whether managed templates are planned."""
            ...

        @property
        def tooling(self) -> bool:
            """Whether selected outputs consume resolved tooling."""
            ...

        @property
        def custom(self) -> bool:
            """Whether custom Make policy is planned."""
            ...

    @runtime_checkable
    class CodegenGenerateRequest(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Repository or workspace root."""
            ...

        @property
        def what(self) -> c.Infra.CodegenConformSurface:
            """Managed file selection."""
            ...

        @property
        def scope(self) -> c.Infra.CodegenConformScope:
            """Repository selection scope."""
            ...

        @property
        def module(self) -> str | None:
            """Exact package or module for a file-only surface."""
            ...

    @runtime_checkable
    class CodegenConformRequest(CodegenGenerateRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def mode(self) -> c.Infra.CodegenConformMode:
            """Read-only check or atomic apply."""
            ...

    @runtime_checkable
    class ArtifactRenderRoute(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entry(self) -> FlextInfraProtocolsConfigTemplates.TemplateEntrySpec:
            """Catalog entry being rendered."""
            ...

        destination: str
        failure_prefix: str

        @property
        def project_context(
            self,
        ) -> FlextInfraProtocolsConfigContexts.ProjectRenderContext | None:
            """Project-scoped render context, when declared."""
            ...

        @property
        def planned_manifests(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...]:
            """Planned manifests the bootstrap closure reads."""
            ...

    @runtime_checkable
    class CodegenRenderInputs(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target(self) -> FlextInfraProtocolsConfigRepository.RepositoryConformTarget:
            """Conformance identity and root being rendered."""
            ...

        @property
        def workspace(self) -> FlextInfraProtocolsConfigWorkspace.WorkspaceSpec:
            """Workspace manifest governing the repository."""
            ...

        @property
        def codegen(self) -> FlextInfraProtocolsConfigArtifact.CodegenConfigSpec:
            """Codegen contract the repository renders under."""
            ...

        @property
        def tooling_runtime(
            self,
        ) -> FlextInfraProtocolsDepsToolConfig.ToolingRuntimeContext | None:
            """Tooling values resolved only when outputs consume them."""
            ...

        @property
        def managed_artifacts(
            self,
        ) -> FlextInfraProtocolsProjectArtifacts.ProjectManagedArtifactsSnapshot:
            """Project managed-artifact catalog overlaid on renders."""
            ...

        integration_branch: str | None
        planned_direct_sources: tuple[str, ...] | None

    @runtime_checkable
    class CodegenRepositoryPlanTask(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def ports(
            self,
        ) -> FlextInfraProtocolsCodegenPipeline.CodegenConformPorts | None:
            """Caller-bound capabilities shared by repository phases."""
            ...

        @property
        def provider_plans(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...] | None:
            """Structural member projected from the owning model.

            Original lazy plans of the selected cohort, supplied as planning data;
            publication still requires live admission.
            """
            ...

        @property
        def selected_inputs(
            self,
        ) -> FlextInfraProtocolsConfigArtifact.CodegenInputs | None:
            """Invoking repository's already captured configuration."""
            ...

        @property
        def root(self) -> Path:
            """Generation scope root."""
            ...

        @property
        def workspace(self) -> FlextInfraProtocolsConfigWorkspace.WorkspaceSpec:
            """Workspace governing the selection."""
            ...

        @property
        def initial_workspace(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.WorkspaceSpec | None:
            """Validated scaffold specification, when any."""
            ...

        @property
        def current_target(
            self,
        ) -> FlextInfraProtocolsConfigRepository.RepositoryConformTarget:
            """Conform target of the invoking repository."""
            ...

        @property
        def repository(self) -> FlextInfraProtocolsConfigRepository.RepositoryRef:
            """Repository this task plans."""
            ...

        @property
        def surface(self) -> c.Infra.CodegenConformSurface:
            """Requested surface resolved against each target policy."""
            ...

    @runtime_checkable
    class CodegenPlanningFileEvidence(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Actual destination identity."""
            ...

        @property
        def desired_digest(self) -> str | None:
            """Desired content digest; absent for planned removal."""
            ...

        @property
        def desired_mode(self) -> int | None:
            """Planned destination mode."""
            ...

        @property
        def owner(self) -> str:
            """Canonical artifact owner."""
            ...

        @property
        def policy(self) -> Literal["full", "merge"] | None:
            """Governed artifact policy."""
            ...

    @runtime_checkable
    class CodegenPlanningRepositoryEvidence(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr:
            """Repository identity."""
            ...

        @property
        def root(self) -> Path:
            """Actual selected repository root."""
            ...

        @property
        def candidate_kind(self) -> Literal["git", "unversioned"]:
            """Whether this root owns an independent Git candidate."""
            ...

        @property
        def candidate_sha(self) -> str | None:
            """Selected repository HEAD; absent without a Git candidate."""
            ...

        @property
        def candidate_dirty(self) -> bool | None:
            """Candidate worktree state; absent without Git ownership."""
            ...

        @property
        def files(
            self,
        ) -> tuple[FlextInfraProtocolsConfigArtifact.CodegenPlanningFileEvidence, ...]:
            """Planned destination identities and content digests."""
            ...

        @property
        def elapsed(self) -> float:
            """Planning wall seconds."""
            ...

    @runtime_checkable
    class CodegenPlanningReport(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Invoking generation scope."""
            ...

        @property
        def outcomes(
            self,
        ) -> tuple[
            FlextInfraProtocolsConfigArtifact.CodegenPlanningRepositoryEvidence, ...
        ]:
            """Every selected repository's native planning outcome."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigArtifact",
]
