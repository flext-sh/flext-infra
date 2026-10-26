"""Codegen artifact, conform, and plan result models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cached_property
from keyword import iskeyword
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

import flext_core
from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import (
    FlextInfraModelsCheck,
    FlextInfraModelsDepsToolConfig,
    FlextInfraModelsDepsToolConfigProjectArtifacts,
    FlextInfraModelsLayout,
    FlextInfraModelsMiseToolchain,
)
from flext_infra._models._config import (
    FlextInfraConfigModelsContexts,
    FlextInfraConfigModelsContract,
    FlextInfraConfigModelsMake,
    FlextInfraConfigModelsProvider,
    FlextInfraConfigModelsRefactorCampaigns,
    FlextInfraConfigModelsRender,
    FlextInfraConfigModelsScaffold,
    FlextInfraConfigModelsTemplates,
    FlextInfraConfigModelsWorkspace,
)
from flext_infra._models._git import FlextInfraModelsGitWorktreeState


class FlextInfraConfigModelsArtifact(FlextInfraConfigModelsRefactorCampaigns):
    """Codegen artifact, conform, and plan result models."""

    class CodegenArtifactSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One ephemeral/generated resource every ignore/exclude derives from."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Basename of the resource")]
        is_dir: Annotated[bool, m.Field(description="Directory (vs file) resource")] = (
            True
        )
        vscode_exclude: Annotated[
            bool,
            m.Field(description="Feed VS Code files.exclude + search.exclude"),
        ] = True
        watch_exclude: Annotated[
            bool,
            m.Field(description="Feed VS Code files.watcherExclude"),
        ] = True
        gitignore: Annotated[
            bool,
            m.Field(description="Feed the Python/tool section of .gitignore"),
        ] = True
        source_scan_ignore: Annotated[
            bool,
            m.Field(description="Feed source_scan.ignored_resources"),
        ] = False
        retired_typing_root: Annotated[
            bool,
            m.Field(
                description=(
                    "Owned retired typing tree retained in path-policy inventory"
                ),
            ),
        ] = False
        generated_source: Annotated[
            bool,
            m.Field(
                description=(
                    "Tracked directory of foreign-generator output (for example "
                    "protoc modules) that ships and imports as a regular "
                    "package: never gitignored, ignored by every source scan, "
                    "excluded by every lint/type/codemod gate, and given a "
                    "generated package initializer"
                ),
            ),
        ] = False
        analysis_exclude: Annotated[
            bool,
            m.Field(
                description=(
                    "Feed the declared directory-exclusion registry: "
                    "tree-walking analyzers (discovery, docs, markdown, "
                    "census, worktree deltas) never descend into this "
                    "machine-emitted artifact"
                ),
            ),
        ] = False
        resolver_owned: Annotated[
            bool,
            m.Field(
                description=(
                    "Package-manager lockfile emission: sibling packages of "
                    "one tool family share resolved dependency lines by "
                    "construction, so the resolver owns the content and "
                    "clone detection never reads it"
                ),
            ),
        ] = False

        @m.model_validator(mode="after")
        def _validate_generated_source_is_directory(self) -> Self:
            """Require a generated source tree to be a directory resource.

            Returns:
                The validated artifact.

            Raises:
                ValueError: If a file resource is declared a generated source.

            """
            if (self.generated_source or self.retired_typing_root) and not self.is_dir:
                msg = f"generated source artifact must be a directory: {self.name}"
                raise ValueError(msg)
            return self

    class DeclaredExclusionsSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Declared directory-exclusion registry (the one exclusion SSOT).

        Every name here is a declared topology fact, not a per-scanner
        exemption: tool-state homes, immutable archive roots, editor/agent
        state, and per-scanner deltas compose with the artifact SSOT
        (``analysis_exclude``) and the VCS-derived names into each consumer's
        derived set. Rules derive from these declarations; adding an exclusion
        is a config declaration, never a code edit.
        """

        tool_state: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Non-artifact tool homes and scratch roots (agent sync "
                    "home, transient test scratch)"
                ),
            ),
        ] = ()
        archive_roots: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Immutable archive contracts: historical evidence trees "
                    "that are never production input to any analyzer"
                ),
            ),
        ] = ()
        docs: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Docs-scanner delta: generated sites and documentation "
                    "report outputs excluded from live documentation"
                ),
            ),
        ] = ()
        markdown: Annotated[
            t.VariadicTuple[Annotated[t.NonEmptyStr, m.Field(pattern=r"^[^!]")]],
            m.Field(
                description=(
                    "Positive repository-relative Markdown exclusion patterns "
                    "not derived from analyzer or full-generated artifact ownership"
                ),
            ),
        ]
        docs_publish: Annotated[
            t.VariadicTuple[Annotated[t.NonEmptyStr, m.Field(pattern=r"^[^!]")]],
            m.Field(
                description=(
                    "Repository-relative page patterns excluded from site "
                    "publication, not from physical documentation copying"
                ),
            ),
        ]
        docs_copy: Annotated[
            t.VariadicTuple[Annotated[t.NonEmptyStr, m.Field(pattern=r"^[^!]")]],
            m.Field(
                description=(
                    "Repository-relative documentation patterns excluded from "
                    "physical copying and site publication"
                ),
            ),
        ]
        pyproject_scan: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "pyproject-discovery delta: non-productive trees whose "
                    "pyproject tables never declare workspace membership"
                ),
            ),
        ] = ()
        check: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Quality-check delta: editor/agent state, report "
                    "outputs, and caches excluded from every check surface"
                ),
            ),
        ] = ()
        validation_clone: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Validation-clone delta: directories excluded when "
                    "cloning a project tree for post-apply validation"
                ),
            ),
        ] = ()
        worktree_transaction: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Worktree-transaction delta: cache directories excluded "
                    "from isolated worktree transaction deltas"
                ),
            ),
        ] = ()
        deps_discovery: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Dependency-discovery delta: directories skipped while "
                    "searching for pyproject declarations"
                ),
            ),
        ] = ()
        parameterized_case_dirs: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Structured test-case parameterization directories: "
                    "fixture twins whose bodies mirror their case tables"
                ),
            ),
        ] = ()
        part_container_dirs: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Declared part-container directories: mechanical "
                    "declaration splits whose overlap is structural, not "
                    "authored duplication"
                ),
            ),
        ] = ()
        helper_modules: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Declared helper module filenames (coverage aggregation "
                    "and similar mechanical companions)"
                ),
            ),
        ] = ()
        scenario_data_roots: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Project-relative roots of tests-tier scenario trees "
                    "(ADR-028): complete roots and descendants are artifacts "
                    "the engines under test consume as data, never governed code"
                ),
            ),
        ] = ()

    class CodegenGovernedPlanRequest(FlextInfraConfigModelsContract.ConfigContract):
        """Resolved inputs for planning one governed artifact's file plan."""

        root: Annotated[Path, m.Field(description="Repository root of the artifact")]
        relative: Annotated[
            Path,
            m.Field(description="Artifact path relative to the repository root"),
        ]
        governed: Annotated[
            FlextInfraConfigModelsTemplates.ManagedFileSpec,
            m.Field(description="Declared governance for the artifact"),
        ]
        current: Annotated[
            str,
            m.Field(description="Current on-disk text; empty when absent"),
        ]
        vscode_spec: Annotated[
            FlextInfraConfigModelsTemplates.CodegenVscodeSpec | None,
            m.Field(description="Declared vscode settings spec when present"),
        ] = None

    class CodegenLocCapSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Per-module logical-LOC ceiling policy (scc code lines)."""

        max_lines: Annotated[
            int,
            m.Field(ge=1, description="Per-module code-LOC ceiling"),
        ]

    class CodegenAstGrepRendererSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One u.Infra renderer of generated native rule documents."""

        name: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "u.Infra renderer mapping a project root to native rule "
                    "documents keyed by '<shape>' or '<shape>--<qualifier>'"
                ),
            ),
        ]
        shapes: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Rule shapes the renderer is registered to emit"),
        ] = ()
        shapes_from: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "u.Infra producer deriving the renderer's shapes from their "
                    "source of truth, instead of a declared list"
                ),
            ),
        ] = None
        facts: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "u.Infra facts producer whose typed model the stage passes "
                    "to the renderer, computed once per generation"
                ),
            ),
        ] = None

        @m.model_validator(mode="after")
        def _validate_one_shape_source(self) -> Self:
            """Require exactly one shape source: a declared list or its producer.

            Returns:
                The validated renderer declaration.

            Raises:
                ValueError: If both or neither shape sources are declared.

            """
            if bool(self.shapes) == (self.shapes_from is not None):
                msg = (
                    f"ast-grep renderer {self.name} declares exactly one of "
                    "shapes or shapes_from"
                )
                raise ValueError(msg)
            return self

    class CodegenAstGrepSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Native ast-grep utilities and rules rendered in memory from SSOT facts."""

        producers: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "u.Infra producer names; each maps a project root to its "
                    "native utility rules keyed by utility id"
                ),
            ),
        ]
        renderers: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.CodegenAstGrepRendererSpec],
            m.Field(
                description=(
                    "Renderers emitting generated native rule documents, run "
                    "after the utility producers"
                ),
            ),
        ]
        scopes: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "u.Infra file-scope producer names; each maps a project root "
                    "to project-relative file sets keyed by the selector a "
                    "catalog rule names under metadata.scope"
                ),
            ),
        ]

    class RetiredProjectionSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One retired projection and the generated evidence that owns it."""

        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository-relative retired projection path"),
        ]
        evidence: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Literal bytes the generated file carries; removal requires "
                    "the match so conform never deletes a hand-written file"
                ),
            ),
        ]

    class CodegenModesSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Filesystem modes the codegen pipeline emits (the mode SSOT)."""

        file_default: Annotated[
            int,
            m.Field(
                ge=0,
                le=0o7777,
                description="Rendered artifacts without a managed mode",
            ),
        ]
        file_private: Annotated[
            int,
            m.Field(ge=0, le=0o7777, description="Engine-private lock and mutex files"),
        ]
        directory_private: Annotated[
            int,
            m.Field(ge=0, le=0o7777, description="Engine-only state and staging trees"),
        ]
        directory_generated: Annotated[
            int,
            m.Field(
                ge=0,
                le=0o7777,
                description="Generated directory trees in consumers",
            ),
        ]

    class CodegenArtifactScopeSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Declared artifacts and their editor, source and generated-tree views."""

        artifacts: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.CodegenArtifactSpec],
            m.Field(
                min_length=1,
                description=(
                    "Ephemeral/generated artifact SSOT; every ignore/exclude "
                    "projection derives from this list"
                ),
            ),
        ]

        @m.computed_field
        @property
        def vscode_files_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.exclude`` entries from the artifact SSOT.

            Returns:
                The resulting ``Mapping[str, bool]``.

            """
            return {
                f"**/{artifact.name}": True
                for artifact in self.artifacts
                if artifact.vscode_exclude
            }

        @m.computed_field
        @property
        def vscode_watcher_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.watcherExclude`` entries from the SSOT.

            Returns:
                The resulting ``Mapping[str, bool]``.

            """
            return {
                (
                    f"**/{artifact.name}/**"
                    if artifact.is_dir
                    else f"**/{artifact.name}"
                ): True
                for artifact in self.artifacts
                if artifact.watch_exclude
            }

        @m.computed_field
        @property
        def vscode_search_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``search.exclude`` entries from the artifact SSOT.

            Returns:
                The resulting ``Mapping[str, bool]``.

            """
            return dict(self.vscode_files_exclude_map)

        @m.computed_field
        @property
        def source_scan_ignored(self) -> t.VariadicTuple[str]:
            """Derived ``source_scan.ignored_resources`` names from the SSOT.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                artifact.name
                for artifact in self.artifacts
                if artifact.source_scan_ignore or artifact.generated_source
            )

        @m.computed_field
        @property
        def generated_sources(self) -> t.VariadicTuple[str]:
            """Derived names of the tracked foreign-generator source trees.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                artifact.name
                for artifact in self.artifacts
                if artifact.generated_source
            )

        @m.computed_field
        @property
        def generated_source_globs(self) -> t.VariadicTuple[str]:
            """Derived path globs every analyzer excludes for generated sources.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(f"**/{name}/**" for name in self.generated_sources)

    class CodegenConfigSpec(CodegenArtifactScopeSpec):
        """Fully modeled content of ``config/codegen.yaml``."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid")

        runtime_module_overrides: Annotated[
            Mapping[
                t.NonEmptyStr, Mapping[Literal["config", "settings"], t.NonEmptyStr]
            ],
            m.Field(
                description=(
                    "Runtime module stems by canonical project distribution and "
                    "closed singleton role (config/settings); omitted roles retain "
                    "the fleet module name. Declared stems must be public Python "
                    "identifiers distinct from root aliases and each other"
                ),
            ),
        ] = m.Field(
            default_factory=flext_core.u.empty(
                Mapping[
                    t.NonEmptyStr,
                    Mapping[Literal["config", "settings"], t.NonEmptyStr],
                ]
            ),
            validate_default=True,
        )

        @m.field_validator("runtime_module_overrides")
        @classmethod
        def validate_runtime_module_overrides(
            cls,
            value: Mapping[str, Mapping[Literal["config", "settings"], str]],
        ) -> Mapping[str, Mapping[Literal["config", "settings"], str]]:
            """Reject invalid physical owners before any source planning.

            Returns:
                The same validated project-to-runtime-module declarations.

            Raises:
                ValueError: If a project identity or module destination is invalid.

            """
            for project, roles in value.items():
                if project != t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(
                    project
                ):
                    msg = f"runtime module project identity is not canonical: {project}"
                    raise ValueError(msg)
                stems = tuple(roles.values())
                for stem in stems:
                    if (
                        not stem.isidentifier()
                        or iskeyword(stem)
                        or stem.startswith("_")
                        or stem in {"config", "settings"}
                        or stem in c.Infra.PUBLIC_ROOT_ALIAS_ORDER
                    ):
                        msg = f"invalid runtime module stem for {project}: {stem}"
                        raise ValueError(msg)
                if len(set(stems)) != len(stems):
                    msg = f"duplicate runtime module destinations for {project}"
                    raise ValueError(msg)
            return value

        repository: Annotated[
            FlextInfraConfigModelsWorkspace.RepositoryDeltaSpec,
            m.Field(
                description="This repository's self-owned declaration differences",
            ),
        ] = m.Field(default_factory=FlextInfraConfigModelsWorkspace.RepositoryDeltaSpec)
        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        retired_projections: Annotated[
            t.VariadicTuple[str | FlextInfraConfigModelsArtifact.RetiredProjectionSpec],
            m.Field(
                description=(
                    "Repository-relative generated projections that no template "
                    "renders any more; generation removes them from consumers. "
                    "A plain string removes files carrying the generated marker; "
                    "a mapping adds the exact evidence bytes required for removal"
                ),
            ),
        ]
        fresh_import_workers: Annotated[
            int,
            m.Field(ge=1, le=16, description="Concurrent fresh-import subprocesses"),
        ]
        lint_snapshot_workers: Annotated[
            int,
            m.Field(
                ge=1,
                le=16,
                description="Concurrent protected-edit lint snapshot threads",
            ),
        ]
        loc_cap: Annotated[
            FlextInfraConfigModelsArtifact.CodegenLocCapSpec,
            m.Field(description="Per-module code-LOC ceiling policy"),
        ]
        ast_grep: Annotated[
            FlextInfraConfigModelsArtifact.CodegenAstGrepSpec,
            m.Field(description="Generated native ast-grep utility rules"),
        ]
        modes: Annotated[
            FlextInfraConfigModelsArtifact.CodegenModesSpec,
            m.Field(description="Filesystem modes the pipeline emits (the mode SSOT)"),
        ]
        toolchain: Annotated[
            FlextInfraModelsMiseToolchain.ToolchainSpec,
            m.Field(description="Exact generated toolchain"),
        ]
        github_actions: Annotated[
            Mapping[str, FlextInfraConfigModelsProvider.GithubActionPinSpec],
            m.Field(description="Immutable GitHub Action catalog"),
        ]
        checkout_submodules: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^(true|false|recursive)$",
                description=(
                    "Default actions/checkout submodules mode for every "
                    "generated workflow. 'false' keeps CI green on projects "
                    "whose submodules are private: the default GITHUB_TOKEN "
                    "cannot clone sibling private repositories and "
                    "'recursive' aborts the job at checkout"
                ),
            ),
        ]
        checkout_submodules_overrides: Annotated[
            Mapping[str, str],
            m.Field(
                description=(
                    "Per-distribution override of checkout_submodules, for "
                    "projects that really do exercise their subprojects in CI"
                ),
            ),
        ]
        ci_private_submodules: Annotated[
            Mapping[str, FlextInfraConfigModelsProvider.CiPrivateSubmodulesSpec],
            m.Field(
                description=(
                    "Per-distribution private submodule deploy-key contracts "
                    "rendered into generated CI before make setup"
                ),
            ),
        ]
        ci_private_dependency_auth: Annotated[
            Mapping[str, FlextInfraConfigModelsProvider.CiPrivateDependencyAuthSpec],
            m.Field(
                description=(
                    "Per-distribution GitHub App identity minting installation "
                    "tokens for private git dependencies in generated CI"
                ),
            ),
        ]
        ci_system_packages: Annotated[
            Mapping[str, t.VariadicTuple[t.NonEmptyStr]],
            m.Field(
                description=(
                    "Per-distribution runner packages (Ubuntu apt names) the "
                    "generated CI installs before the gates run"
                ),
            ),
        ]
        ci_package_registry_read: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Distributions whose generated CI gates resolve GitHub "
                    "Packages (for example private GHCR OCI dependencies); only "
                    "these grant the ci job packages: read, every other job "
                    "and distribution stays contents-only"
                ),
            ),
        ]
        sonarcloud: Annotated[
            FlextInfraConfigModelsRender.SonarcloudSpec,
            m.Field(description="Fleet SonarCloud automatic-analysis scope policy"),
        ]
        infra_repository: Annotated[
            FlextInfraConfigModelsProvider.RepositorySourceSpec,
            m.Field(description="Canonical infrastructure repository identity"),
        ]
        branch_policy: Annotated[
            FlextInfraConfigModelsProvider.BranchPolicySpec,
            m.Field(description="Global branch policy (CI triggers, integration line)"),
        ]
        profiles: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsContexts.ProfileSpec],
            m.Field(description="Ordered Make profiles"),
        ]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        vscode: Annotated[
            FlextInfraConfigModelsTemplates.CodegenVscodeSpec,
            m.Field(description="Canonical VS Code settings merge contract"),
        ]
        exclusions: Annotated[
            FlextInfraConfigModelsArtifact.DeclaredExclusionsSpec,
            m.Field(
                description=(
                    "Declared directory-exclusion registry: the one SSOT "
                    "every scanner exclusion derives from"
                ),
            ),
        ]
        layout: Annotated[
            FlextInfraModelsLayout.LayoutSpec,
            m.Field(
                description=(
                    "Declarative project-layout conformance contract consumed "
                    "by the layout engine and the layout quality gate"
                ),
            ),
        ]

        @m.computed_field
        @property
        def analyzer_exclude_globs(self) -> t.VariadicTuple[str]:
            """Project declared artifacts and walker exclusions into analyzer globs.

            Returns:
                File patterns and recursive directory patterns, in stable order.

            """
            return tuple(
                sorted(
                    {
                        (
                            f"**/{artifact.name}/**"
                            if artifact.is_dir
                            else f"**/{artifact.name}"
                        )
                        for artifact in self.artifacts
                        if artifact.analysis_exclude or artifact.generated_source
                    }
                    | {f"**/{name}/**" for name in self.check_excluded_dirs}
                    | set(self.scenario_data_globs)
                )
            )

        @m.computed_field
        @property
        def markdown_exclude_globs(self) -> t.VariadicTuple[str]:
            """Derive Markdown scope without hiding authored or merged documents.

            Returns:
                Analyzer, full-generated Markdown and declared residual patterns.

            """
            return tuple(
                sorted(
                    set(self.analyzer_exclude_globs)
                    | {
                        entry.destination
                        for entry in self.templates.entries
                        if entry.ownership is not None
                        and entry.ownership.policy == c.Infra.MANAGED_FILE_POLICY_FULL
                        and Path(entry.destination).suffix == ".md"
                    }
                    | set(self.exclusions.markdown)
                )
            )

        @m.computed_field
        @property
        def docs_publish_patterns(self) -> t.VariadicTuple[str]:
            """Compose page and copy exclusions in repository coordinates.

            Returns:
                Page and copy patterns in declaration order, without duplicates.

            """
            return tuple(
                dict.fromkeys((
                    *self.exclusions.docs_publish,
                    *self.exclusions.docs_copy,
                ))
            )

        @m.computed_field
        @property
        def docs_copy_patterns(self) -> t.VariadicTuple[str]:
            """Expose declared copy exclusions without importing Markdown scope.

            Returns:
                Copy patterns in declaration order, without duplicates.

            """
            return tuple(dict.fromkeys(self.exclusions.docs_copy))

        @m.computed_field
        @property
        def scenario_data_globs(self) -> t.VariadicTuple[str]:
            """Derived globs of complete artifact trees at each declared root.

            Returns:
                One recursive pattern per declared root.

            """
            return tuple(
                f"**/{root}/**" for root in self.exclusions.scenario_data_roots
            )

        @m.computed_field
        @property
        def analysis_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived base directory exclusion set every walker composes.

            Machine-emitted artifacts flagged ``analysis_exclude`` plus the
            declared tool-state roots plus the VCS-derived names (Git
            internals and the worktree namespace) form the one base set the
            per-scanner derivations extend.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    {
                        artifact.name
                        for artifact in self.artifacts
                        if artifact.analysis_exclude and artifact.is_dir
                    }
                    | set(self.exclusions.tool_state)
                    | {c.Infra.GIT_DIR, c.Infra.WORKTREES_DIRNAME},
                ),
            )

        @m.computed_field
        @property
        def docs_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived live-documentation exclusion set.

            The base walker set plus the declared archive roots and the
            generated-site/report delta: live docs exclude generated sites
            and immutable or historical evidence roots.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    set(self.analysis_excluded_dirs)
                    | set(self.exclusions.archive_roots)
                    | set(self.exclusions.docs)
                )
            )

        @m.computed_field
        @property
        def pyproject_scan_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived pyproject-discovery exclusion set.

            The base walker set plus the declared archive roots and the
            pyproject-scan delta whose trees never declare workspace
            membership.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    set(self.analysis_excluded_dirs)
                    | set(self.exclusions.archive_roots)
                    | set(self.exclusions.pyproject_scan)
                )
            )

        @m.computed_field
        @property
        def check_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived quality-check exclusion set.

            The base walker set plus the declared archive roots and the
            check delta (editor/agent state, report outputs, caches).

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    set(self.analysis_excluded_dirs)
                    | set(self.exclusions.archive_roots)
                    | set(self.exclusions.check)
                )
            )

        @m.computed_field
        @property
        def validation_clone_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived validation-clone exclusion set.

            The base walker set plus the declared archive roots and the
            validation-clone delta applied while cloning a project tree for
            post-apply validation.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    set(self.analysis_excluded_dirs)
                    | set(self.exclusions.archive_roots)
                    | set(self.exclusions.validation_clone)
                )
            )

        @m.computed_field
        @property
        def worktree_transaction_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived worktree-transaction exclusion set.

            The base walker set plus the declared archive roots and the
            cache delta excluded from isolated worktree transaction deltas.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    set(self.analysis_excluded_dirs)
                    | set(self.exclusions.archive_roots)
                    | set(self.exclusions.worktree_transaction)
                )
            )

        @m.computed_field
        @property
        def deps_discovery_excluded_dirs(self) -> t.VariadicTuple[str]:
            """Derived dependency-discovery exclusion set.

            The base walker set plus the declared archive roots and the
            dependency-discovery delta skipped while searching for pyproject
            declarations.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    set(self.analysis_excluded_dirs)
                    | set(self.exclusions.archive_roots)
                    | set(self.exclusions.deps_discovery)
                )
            )

        @m.computed_field
        @property
        def resolver_owned_files(self) -> t.VariadicTuple[str]:
            """Derived filenames whose content the package resolver owns.

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            return tuple(
                sorted(
                    artifact.name
                    for artifact in self.artifacts
                    if artifact.resolver_owned
                )
            )

        # The canonical .gitignore body is ONE computed
        # projection — the artifact SSOT feeds the Python/build section and the
        # static scaffold sections carry only what the SSOT cannot express
        # (file globs, secrets, editor/OS noise). Per-project exception fields
        # (extra_ignored / allowed dirs) land in their typed owner;
        # this projection is the seam they will extend.
        @m.computed_field
        @property
        def gitignore_sections(
            self,
        ) -> t.VariadicTuple[
            FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec
        ]:
            """Derived canonical ``.gitignore`` sections (SSOT order, deduplicated).

            Ignore files are order-sensitive: a pattern placed before a
            catch-all such as ``/*`` is dead, and a directory ignored before
            its own ``!`` negation is never re-allowed. The declared sections
            are therefore emitted in their declared order, and derived artifact
            patterns are appended -- never prepended -- so a whitelist policy
            expressed in the SSOT survives the projection intact.

            Returns:
                The resulting
                    ``t.VariadicTuple[FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec]``.

            """
            scaffold_sections = self.scaffold.gitignore_sections
            # A declared section may already govern a derived artifact, in
            # either direction: a whitelist re-allows `.agents/` with `!`, so
            # appending a bare `.agents/` ignore would contradict the declared
            # policy. Only artifacts the SSOT never mentions are appended.
            governed = {
                pattern.lstrip("!")
                for section in scaffold_sections
                for pattern in section.patterns
            }
            managed_allowed: t.MutableSequenceOf[str] = []
            declared_patterns = {
                pattern for section in scaffold_sections for pattern in section.patterns
            }
            versioned_paths = tuple(managed.path for managed in self.managed_file_specs)
            for path in versioned_paths:
                parts = path.parts
                candidates = [
                    *(f"!{'/'.join(parts[:depth])}/" for depth in range(1, len(parts))),
                    f"!{path.as_posix()}",
                ]
                managed_allowed.extend(
                    candidate
                    for candidate in candidates
                    if candidate not in declared_patterns
                    and candidate not in managed_allowed
                )
            derived: t.MutableSequenceOf[str] = []
            for pattern in self.gitignore_artifact_patterns:
                if pattern not in governed and pattern not in derived:
                    derived.append(pattern)
            sections: t.MutableSequenceOf[
                FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec
            ] = []
            # Declared sections are emitted verbatim. Cross-section dedup is
            # unsound for ignore files: repeating `.beads/*` after an
            # intervening `!.beads/` is what keeps the directory scanned, so
            # dropping the repeat silently un-ignores its contents.
            sections.extend(scaffold_sections)
            # Derived artifacts are appended as their own trailing section: an
            # ignore file is evaluated in order, so injecting them into the
            # first section would place them before any `!` negation the policy
            # declares later and silently un-ignore governed paths.
            if derived:
                sections.append(
                    FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec(
                        name=c.Infra.GITIGNORE_DERIVED_SECTION_NAME,
                        patterns=tuple(derived),
                    ),
                )
            if managed_allowed:
                sections.append(
                    FlextInfraConfigModelsScaffold.ScaffoldGitignoreSectionSpec(
                        name=c.Infra.GITIGNORE_MANAGED_SECTION_NAME,
                        patterns=tuple(managed_allowed),
                    ),
                )
            return tuple(sections)

        @m.computed_field
        @property
        def gitignore_artifact_patterns(self) -> t.VariadicTuple[str]:
            """Derived ``.gitignore`` artifact patterns from the SSOT (stable order).

            Returns:
                The resulting ``t.VariadicTuple[str]``.

            """
            # A generated source tree is tracked: ignoring it would hide the
            # modules a regeneration adds from ``git add``.
            return tuple(
                f"{artifact.name}/" if artifact.is_dir else artifact.name
                for artifact in self.artifacts
                if artifact.gitignore and not artifact.generated_source
            )

        @m.computed_field
        @cached_property
        def managed_file_specs(
            self,
        ) -> t.VariadicTuple[FlextInfraConfigModelsTemplates.ManagedFileSpec]:
            """Derive managed views once per catalog from its single declaration.

            Returns:
                The owned artifacts, excluding authored scaffold seeds.

            """
            return tuple(
                FlextInfraConfigModelsTemplates.ManagedFileSpec(
                    path=Path(entry.destination),
                    **entry.ownership.model_dump(exclude_computed_fields=True),
                )
                for entry in self.templates.entries
                if entry.ownership is not None
            )

        scaffold: Annotated[
            FlextInfraConfigModelsScaffold.ScaffoldSpec,
            m.Field(description="Typed new-project scaffold policy"),
        ]
        templates: Annotated[
            FlextInfraConfigModelsTemplates.TemplatesSpec,
            m.Field(description="Single artifact declaration and ownership catalog"),
        ]
        # flext-infra owns generic conform policy only. The set
        # of projects it serves is NOT its knowledge — each repository's own
        # .gitmodules is the read-only topology authority.

        @m.model_validator(mode="after")
        def _validate_github_artifact_ownership(self) -> Self:
            """Keep generated GitHub artifacts full-owned and authored seeds explicit.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If a GitHub artifact lacks full template ownership.

            """
            non_full = sorted(
                entry.destination
                for entry in self.templates.entries
                if Path(entry.destination).parts[:1] == (".github",)
                and entry.ownership is not None
                and (
                    entry.ownership.policy != c.Infra.MANAGED_FILE_POLICY_FULL
                    or entry.source is None
                )
            )
            if non_full:
                msg = f"GitHub artifacts must be full-managed: {non_full}"
                raise ValueError(msg)
            return self

    class RepositoryDeclarationInputs(FlextInfraConfigModelsContract.ConfigContract):
        """Self-owned topology policy and the exact consulted configuration states."""

        spec: Annotated[
            FlextInfraConfigModelsWorkspace.RepositoryDeltaSpec,
            m.Field(description="Validated repository declaration subsection"),
        ]
        sources: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                exclude=True, description="Exact consulted configuration input states"
            ),
        ] = ()

    class CodegenInputs(FlextInfraConfigModelsContract.ConfigContract):
        """Full effective codegen policy and its ordered consulted snapshots."""

        spec: Annotated[
            FlextInfraConfigModelsArtifact.CodegenConfigSpec,
            m.Field(description="Validated effective repository codegen declaration"),
        ]
        sources: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(exclude=True, description="Exact consulted config input states"),
        ] = ()

    class CodegenConformSurfaceContract(m.Value):
        """Typed ownership contract for one requested conformance surface."""

        # Why: leaf conform planning contract lives on
        # m.Infra only (not nested in services).
        destinations: Annotated[
            frozenset[str] | None,
            m.Field(description="Output paths selected for conformance planning"),
        ] = None
        complete_governed: Annotated[
            bool,
            m.Field(description="Whether every governed output is represented"),
        ] = False
        delegates: Annotated[
            bool,
            m.Field(description="Whether delegated templates are planned"),
        ] = True
        pyproject: Annotated[
            bool,
            m.Field(description="Whether project metadata is planned"),
        ] = True
        templates: Annotated[
            bool,
            m.Field(description="Whether managed templates are planned"),
        ] = True
        tooling: Annotated[
            bool,
            m.Field(description="Whether selected outputs consume resolved tooling"),
        ] = True
        custom: Annotated[
            bool,
            m.Field(description="Whether custom Make policy is planned"),
        ] = True

    class CodegenGenerateRequest(FlextInfraConfigModelsContract.ConfigContract):
        """Validated projection inputs for ``flext-infra codegen generate``."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)
        root: Annotated[Path, m.Field(description="Repository or workspace root")]
        what: Annotated[
            c.Infra.CodegenConformSurface,
            m.Field(description="Managed file selection"),
        ] = c.Infra.CodegenConformSurface.ALL
        scope: Annotated[
            c.Infra.CodegenConformScope,
            m.Field(description="Repository selection scope"),
        ] = c.Infra.CodegenConformScope.SELF
        module: Annotated[
            str | None,
            m.Field(description="Exact package or module for a file-only surface"),
        ] = None

        @m.model_validator(mode="after")
        def _validate_lazy_init_scope(self) -> Self:
            """Reject selectors that would escape a file-only surface contract.

            Returns:
                The request with a coherent surface and repository selection.

            Raises:
                ValueError: If the module or repository selector is incompatible.

            """
            file_only = self.what in c.Infra.FILE_ONLY_SURFACES
            facades = self.what == c.Infra.CodegenConformSurface.FACADES
            if self.module is not None and not file_only:
                msg = "--module belongs only to lazy-init or facades"
                raise ValueError(msg)
            if facades and self.module is None:
                msg = "facades requires an exact destination --module"
                raise ValueError(msg)
            if (
                file_only
                and self.module is not None
                and self.scope != c.Infra.CodegenConformScope.SELF
            ):
                msg = "an exact module requires the self repository scope"
                raise ValueError(msg)
            if (
                self.what in c.Infra.SELF_SCOPE_SURFACES
                and self.scope != c.Infra.CodegenConformScope.SELF
            ):
                msg = f"{self.what} requires the self repository scope"
                raise ValueError(msg)
            return self

    class CodegenConformRequest(CodegenGenerateRequest):
        """Add explicit checking and declaration repair to projection inputs."""

        mode: Annotated[
            c.Infra.CodegenConformMode,
            m.Field(description="Read-only check or atomic apply"),
        ] = c.Infra.CodegenConformMode.CHECK
        declaration_kind: Annotated[
            c.Infra.ProjectKind | None,
            m.Field(
                description="Explicit self-owned kind supplied by native bootstrap"
            ),
        ] = None

        @m.model_validator(mode="after")
        def _validate_declaration_kind(self) -> Self:
            """Keep explicit kind bootstrap on the target's own Makefile.

            Returns:
                The request with a coherent explicit bootstrap selection.

            Raises:
                ValueError: If kind bootstrap addresses another surface or scope.

            """
            if self.declaration_kind is not None and (
                self.what != c.Infra.CodegenConformSurface.MAKEFILE
                or self.scope != c.Infra.CodegenConformScope.SELF
            ):
                msg = "kind bootstrap requires the target's self Makefile surface"
                raise ValueError(msg)
            return self

    class CodegenRenderInputs(m.StrictModel):
        """One repository planner's managed state over frozen policy references."""

        target: Annotated[
            FlextInfraConfigModelsContexts.RepositoryConformTarget,
            m.Field(
                frozen=True, description="Conformance identity and root being rendered"
            ),
        ]
        workspace: Annotated[
            FlextInfraConfigModelsWorkspace.WorkspaceSpec,
            m.Field(
                frozen=True, description="Workspace manifest governing the repository"
            ),
        ]
        codegen: Annotated[
            FlextInfraConfigModelsArtifact.CodegenConfigSpec,
            m.Field(
                frozen=True, description="Codegen contract the repository renders under"
            ),
        ]
        tooling_runtime: FlextInfraModelsDepsToolConfig.ToolingRuntimeContext | None = (
            m.Field(
                description="Tooling values resolved only when outputs consume them"
            )
        )
        managed_artifacts: Annotated[
            FlextInfraModelsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsSnapshot,
            m.Field(
                frozen=True,
                description="Project managed-artifact catalog overlaid on renders",
            ),
        ]
        integration_branch: Annotated[
            str | None,
            m.Field(
                frozen=True,
                description=(
                    "Integration branch the repository integrates on, resolved "
                    "once per plan for the project context and every workflow; "
                    "None when Git publishes none, so a render that needs it "
                    "fails with the resolver's own cause"
                ),
            ),
        ]
        planned_direct_sources: t.VariadicTuple[str] | None = m.Field(
            default=None,
            description=(
                "Requirement names the pyproject composed in this plan "
                "takes by direct reference (forks and local projects). "
                "Planners compose the pyproject first and record them; "
                "None means this plan composes no pyproject, so the "
                "committed one is the source"
            ),
        )

    class CodegenFilePlan(m.Cli.FileChange):
        """One managed file change plus its governed ownership metadata."""

        project: Annotated[Path, m.Field(description="Physical owning project root")]
        owner: Annotated[
            str,
            m.Field(description="Canonical artifact owner, empty for scaffold files"),
        ] = ""
        policy: Annotated[
            Literal["full", "merge"] | None,
            m.Field(description="Governed root artifact policy"),
        ] = None
        tracking: Annotated[
            Literal["versioned", "runtime-local"],
            m.Field(description="Declared persistence policy of this artifact"),
        ] = "versioned"
        index_before: Annotated[
            FlextInfraModelsGitWorktreeState.GitWorktreeIndexEntry | None,
            m.Field(description="Captured index entry scheduled for retirement"),
        ] = None
        tracking_dependencies: Annotated[
            t.VariadicTuple[Path],
            m.Field(
                description=(
                    "Portable declaration destinations required before retirement"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def validate_publication_identity(self) -> Self:
            """Keep every plan inside its project and its retirement consistent.

            Returns:
                The validated plan.

            Raises:
                ValueError: If the plan escapes its project, publishes a
                    first-party stub, or declares an inconsistent retirement.

            """
            if not self.project.is_absolute() or not self.path.is_relative_to(
                self.project
            ):
                msg = f"codegen path escapes owning project: {self.path}"
                raise ValueError(msg)
            if self.path.suffix == ".pyi" and self.desired_content is not None:
                msg = f"first-party .pyi publication is forbidden: {self.path}"
                raise ValueError(msg)
            if self.index_before is not None and (
                self.tracking != "runtime-local"
                or self.index_before.path.is_absolute()
                or self.project / self.index_before.path != self.path
            ):
                msg = "index retirement must match its runtime-local artifact"
                raise ValueError(msg)
            if any(
                not path.is_relative_to(self.project)
                for path in self.tracking_dependencies
            ):
                msg = "tracking declaration escapes the owning project"
                raise ValueError(msg)
            return self

    class CodegenRepositoryPlanTask(FlextInfraConfigModelsContract.ConfigContract):
        """One repository's read-only planning inputs sent to a fleet worker."""

        ports: Annotated[
            t.Port[p.Infra.CodegenConformPorts] | None,
            m.Field(
                exclude=True,
                description="Caller-bound capabilities shared by repository phases",
            ),
        ] = None
        provider_plans: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.CodegenFilePlan] | None,
            m.Field(
                exclude=True,
                description=(
                    "Original lazy plans of the selected cohort, supplied as "
                    "planning data; publication still requires live admission"
                ),
            ),
        ] = None
        selected_inputs: Annotated[
            FlextInfraConfigModelsArtifact.CodegenInputs | None,
            m.Field(
                exclude=True,
                description="Invoking repository's already captured configuration",
            ),
        ] = None
        root: Annotated[Path, m.Field(description="Generation scope root")]
        workspace: Annotated[
            FlextInfraConfigModelsWorkspace.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        initial_workspace: Annotated[
            FlextInfraConfigModelsWorkspace.WorkspaceSpec | None,
            m.Field(description="Validated scaffold specification, when any"),
        ] = None
        current_target: Annotated[
            FlextInfraConfigModelsContexts.RepositoryConformTarget,
            m.Field(description="Conform target of the invoking repository"),
        ]
        repository: Annotated[
            FlextInfraConfigModelsContexts.RepositoryRef,
            m.Field(description="Repository this task plans"),
        ]
        surface: Annotated[
            c.Infra.CodegenConformSurface,
            m.Field(
                description="Requested surface resolved against each target policy"
            ),
        ]

    class CodegenPlanningFileEvidence(FlextInfraConfigModelsContract.ConfigContract):
        """One planned destination without source bytes or captured file state."""

        path: Annotated[Path, m.Field(description="Actual destination identity")]
        desired_digest: Annotated[
            str | None,
            m.Field(
                pattern=r"^sha256:[a-f0-9]{64}$",
                description="Desired content digest; absent for planned removal",
            ),
        ]
        desired_mode: Annotated[
            int | None,
            m.Field(ge=0, le=0o7777, description="Planned destination mode"),
        ]
        owner: Annotated[str, m.Field(description="Canonical artifact owner")]
        policy: Annotated[
            Literal["full", "merge"] | None,
            m.Field(description="Governed artifact policy"),
        ]

    class CodegenPlanningRepositoryEvidence(
        FlextInfraConfigModelsContract.ConfigContract,
    ):
        """Candidate and target inventory safe for report artifact publication."""

        repository: Annotated[t.NonEmptyStr, m.Field(description="Repository identity")]
        root: Annotated[Path, m.Field(description="Actual selected repository root")]
        candidate_kind: Annotated[
            Literal["git", "unversioned"],
            m.Field(description="Whether this root owns an independent Git candidate"),
        ]
        candidate_sha: Annotated[
            str | None,
            m.Field(
                pattern=r"^[a-f0-9]{40}$",
                description="Selected repository HEAD; absent without a Git candidate",
            ),
        ]
        candidate_dirty: Annotated[
            bool | None,
            m.Field(
                description=("Candidate worktree state; absent without Git ownership")
            ),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.CodegenPlanningFileEvidence],
            m.Field(description="Planned destination identities and content digests"),
        ]
        issues: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
            m.Field(description="Native target failures from original planning"),
        ]
        error: Annotated[str, m.Field(description="Original planning failure message")]
        error_type: Annotated[str, m.Field(description="Original exception identity")]
        error_traceback: Annotated[
            str,
            m.Field(description="Original planning traceback without reconstruction"),
        ]
        elapsed: Annotated[float, m.Field(ge=0, description="Planning wall seconds")]

    class CodegenPlanningReport(FlextInfraConfigModelsContract.ConfigContract):
        """Candidate and target evidence excluding source snapshots and commands."""

        root: Annotated[Path, m.Field(description="Invoking generation scope")]
        outcomes: Annotated[
            t.VariadicTuple[
                FlextInfraConfigModelsArtifact.CodegenPlanningRepositoryEvidence
            ],
            m.Field(description="Every selected repository's native planning outcome"),
        ]


__all__: list[str] = ["FlextInfraConfigModelsArtifact"]
