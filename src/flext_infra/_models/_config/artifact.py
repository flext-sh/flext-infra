"""Codegen artifact, conform, and plan result models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import (
    FlextInfraModelsCheck,
    FlextInfraModelsDepsToolConfig,
    FlextInfraModelsDepsToolConfigProjectArtifacts,
    FlextInfraModelsLayout,
    FlextInfraModelsMiseToolchain,
)
from flext_infra._models._config.contexts import FlextInfraConfigModelsContexts
from flext_infra._models._config.contract import FlextInfraConfigModelsContract
from flext_infra._models._config.make import FlextInfraConfigModelsMake
from flext_infra._models._config.provider import FlextInfraConfigModelsProvider
from flext_infra._models._config.release import FlextInfraConfigModelsRelease
from flext_infra._models._config.render import FlextInfraConfigModelsRender
from flext_infra._models._config.scaffold import FlextInfraConfigModelsScaffold
from flext_infra._models._config.templates import FlextInfraConfigModelsTemplates
from flext_infra._models._config.workspace import FlextInfraConfigModelsWorkspace
from flext_infra._models._git.worktree_state import FlextInfraModelsGitWorktreeState


class FlextInfraConfigModelsArtifact:
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

        @m.model_validator(mode="after")
        def _validate_generated_source_is_directory(self) -> Self:
            """Require a generated source tree to be a directory resource.

            Returns:
                The validated artifact.

            Raises:
                ValueError: If a file resource is declared a generated source.

            """
            if self.generated_source and not self.is_dir:
                msg = f"generated source artifact must be a directory: {self.name}"
                raise ValueError(msg)
            return self

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
        runtime_root: Annotated[
            Path | None,
            m.Field(description="Runtime root when the artifact belongs to the root"),
        ] = None
        vscode_spec: Annotated[
            FlextInfraConfigModelsTemplates.CodegenVscodeSpec | None,
            m.Field(description="Declared vscode settings spec when present"),
        ] = None
        source_states: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True, description="Exact inputs of the injected declaration"
            ),
        ] = ()

    class CodegenLocCapSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Per-module logical-LOC ceiling policy (scc code lines)."""

        max_lines: Annotated[
            int,
            m.Field(ge=1, description="Per-module code-LOC ceiling"),
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

    class CodegenConfigSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Fully modeled content of ``config/codegen.yaml``."""

        repository: Annotated[
            FlextInfraConfigModelsWorkspace.RepositoryDeltaSpec,
            m.Field(
                default_factory=FlextInfraConfigModelsWorkspace.RepositoryDeltaSpec,
                description="This repository's self-owned declaration differences",
            ),
        ]
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
        fleet_workers: Annotated[
            int,
            m.Field(
                ge=1,
                le=32,
                description=(
                    "Worker processes for independent read-only per-repository "
                    "work of one fleet run"
                ),
            ),
        ]
        loc_cap: Annotated[
            FlextInfraConfigModelsArtifact.CodegenLocCapSpec,
            m.Field(description="Per-module code-LOC ceiling policy"),
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
        uv_exclude_dependencies: Annotated[
            t.VariadicTuple[
                FlextInfraConfigModelsRender.UvScopedDependencyExclusionSpec
            ],
            m.Field(description="Project-scoped official uv dependency exclusions"),
        ] = ()
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
                f"**/{artifact.name}/**": True
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
            for managed in self.managed_files:
                parts = managed.path.parts
                candidates = [
                    *(f"!{'/'.join(parts[:depth])}/" for depth in range(1, len(parts))),
                    f"!{managed.path.as_posix()}",
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

        managed_files: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsTemplates.ManagedFileSpec],
            m.Field(description="Files owned by conform"),
        ]
        scaffold: Annotated[
            FlextInfraConfigModelsScaffold.ScaffoldSpec,
            m.Field(description="Typed new-project scaffold policy"),
        ]
        templates: Annotated[
            FlextInfraConfigModelsTemplates.TemplatesSpec,
            m.Field(description="New-project-only scaffold template manifest"),
        ]
        # flext-infra owns generic conform policy only. The set
        # of projects it serves is NOT its knowledge — each repository's own
        # .gitmodules is the read-only topology authority.

        @m.model_validator(mode="after")
        def _validate_github_artifact_ownership(self) -> Self:
            """Require one full-managed conform owner for every GitHub template.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If GitHub artifacts must have exactly one template and
                    managed owner; or if GitHub template/managed ownership mismatch; or
                    if GitHub artifacts must be full-managed.

            """
            github_templates = tuple(
                Path(entry.destination)
                for entry in self.templates.entries
                if Path(entry.destination).parts[:1] == (".github",)
            )
            github_managed = tuple(
                managed
                for managed in self.managed_files
                if managed.path.parts[:1] == (".github",)
            )
            template_paths = set(github_templates)
            managed_paths = {managed.path for managed in github_managed}
            duplicate_templates = len(github_templates) != len(template_paths)
            duplicate_managed = len(github_managed) != len(managed_paths)
            if duplicate_templates or duplicate_managed:
                msg = (
                    "GitHub artifacts must have exactly one template and managed owner"
                )
                raise ValueError(msg)
            if template_paths != managed_paths:
                missing_owners = sorted(
                    path.as_posix() for path in template_paths - managed_paths
                )
                missing_templates = sorted(
                    path.as_posix() for path in managed_paths - template_paths
                )
                msg = (
                    "GitHub template/managed ownership mismatch: "
                    f"missing owners={missing_owners}, "
                    f"missing templates={missing_templates}"
                )
                raise ValueError(msg)
            non_full = sorted(
                managed.path.as_posix()
                for managed in github_managed
                if managed.policy != c.Infra.MANAGED_FILE_POLICY_FULL
            )
            if non_full:
                msg = f"GitHub artifacts must be full-managed: {non_full}"
                raise ValueError(msg)
            return self

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
        dependencies_only: Annotated[
            bool,
            m.Field(description="Whether planning is dependency-only"),
        ] = False
        runtime_bindings: Annotated[
            bool,
            m.Field(description="Select only declared checkout-local runtime bindings"),
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
        custom: Annotated[
            bool,
            m.Field(description="Whether custom Make policy is planned"),
        ] = True

    class CodegenConformRequest(FlextInfraConfigModelsContract.ConfigContract):
        """Validated public request for ``flext-infra codegen conform``."""

        root: Annotated[Path, m.Field(description="Repository or workspace root")]
        what: Annotated[
            c.Infra.CodegenConformSurface,
            m.Field(description="Managed file selection"),
        ] = c.Infra.CodegenConformSurface.ALL
        scope: Annotated[
            c.Infra.CodegenConformScope,
            m.Field(description="Repository selection scope"),
        ] = c.Infra.CodegenConformScope.SELF
        mode: Annotated[
            c.Infra.CodegenConformMode,
            m.Field(description="Read-only check or atomic apply"),
        ] = c.Infra.CodegenConformMode.CHECK
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
            file_only = self.what in {
                c.Infra.CodegenConformSurface.LAZY_INIT,
                c.Infra.CodegenConformSurface.FACADES,
            }
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
                self.what
                in {
                    c.Infra.CodegenConformSurface.MISE_CONFIG,
                    c.Infra.CodegenConformSurface.ENVRC,
                }
                and self.scope != c.Infra.CodegenConformScope.SELF
            ):
                msg = f"{self.what} requires the self repository scope"
                raise ValueError(msg)
            return self

    class CodegenArtifactComposition(FlextInfraConfigModelsContract.ConfigContract):
        """Rendered artifact plus the exact source states used to compose it."""

        rendered: Annotated[
            str,
            m.Field(description="Fully composed managed-file content"),
        ]
        source_states: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(description="Ordered immutable sources consumed by composition"),
        ] = ()

    class CodegenRenderInputs(FlextInfraConfigModelsContract.ConfigContract):
        """Resolved inputs shared by every governed render of one repository.

        A conform planner resolves them once per repository; every template
        render, overlay composition, and pyproject conformance of that
        repository then reads these same values.
        """

        target: Annotated[
            FlextInfraConfigModelsContexts.RepositoryConformTarget,
            m.Field(description="Conformance identity and root being rendered"),
        ]
        workspace: Annotated[
            FlextInfraConfigModelsWorkspace.WorkspaceSpec,
            m.Field(description="Workspace manifest governing the repository"),
        ]
        codegen: Annotated[
            FlextInfraConfigModelsArtifact.CodegenConfigSpec,
            m.Field(description="Codegen contract the repository renders under"),
        ]
        tooling_runtime: Annotated[
            FlextInfraModelsDepsToolConfig.ToolingRuntimeContext,
            m.Field(description="Tooling values resolved for the repository"),
        ]
        managed_artifacts: Annotated[
            FlextInfraModelsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsSnapshot,
            m.Field(description="Project managed-artifact catalog overlaid on renders"),
        ]
        integration_branch: Annotated[
            str | None,
            m.Field(
                description=(
                    "Integration branch the repository integrates on, resolved "
                    "once per plan for the project context and every workflow; "
                    "None when Git publishes none, so a render that needs it "
                    "fails with the resolver's own cause"
                ),
            ),
        ]
        planned_direct_sources: Annotated[
            t.VariadicTuple[str] | None,
            m.Field(
                description=(
                    "Requirement names the pyproject composed in this plan "
                    "takes by direct reference (forks and local projects). "
                    "Planners compose the pyproject first and record them; "
                    "None means this plan composes no pyproject, so the "
                    "committed one is the source"
                ),
            ),
        ] = None

    class CodegenFilePlan(FlextInfraConfigModelsContract.ConfigContract):
        """Exact before state and desired state for one managed file."""

        project: Annotated[Path, m.Field(description="Physical owning project root")]
        path: Annotated[Path, m.Field(description="Absolute managed file path")]
        before: Annotated[
            m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan,
            m.Field(
                description=(
                    "Descriptor-authenticated file state, or the exact absent "
                    "parent chain captured by read-only planning"
                ),
            ),
        ]
        desired_content: Annotated[
            bytes | None,
            m.Field(
                strict=True,
                description="Exact desired bytes, or None for an absent destination",
            ),
        ]
        desired_mode: Annotated[
            int | None,
            m.Field(
                ge=0,
                le=0o7777,
                strict=True,
                description="Exact desired mode, or None for an absent destination",
            ),
        ]
        source_states: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(
                exclude=True,
                description="Exact source states that produced rendered content",
            ),
        ] = ()
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
        def _validate_publication_identity(self) -> Self:
            """Bind one complete desired state to its exact project and target.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If codegen project and path must be absolute; or if codegen
                    desired bytes and mode must be present or absent together; or if
                    codegen before state belongs to another path; or if codegen absent
                    parent plan is inconsistent with its destination; or if codegen path
                    escapes owning project.

            """
            if not self.project.is_absolute() or not self.path.is_absolute():
                msg = "codegen project and path must be absolute"
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
            if isinstance(self.before, m.Cli.AtomicFileState):
                if self.before.path != self.path:
                    msg = "codegen before state belongs to another path"
                    raise ValueError(msg)
            elif (
                self.before.target != self.path.parent
                or not self.before.directories
                or self.desired_content is None
            ):
                msg = "codegen absent parent plan is inconsistent with its destination"
                raise ValueError(msg)
            try:
                self.path.relative_to(self.project)
            except ValueError as exc:
                msg = f"codegen path escapes owning project: {self.path}"
                raise ValueError(msg) from exc
            desired = (self.desired_content, self.desired_mode)
            if any(value is None for value in desired) != all(
                value is None for value in desired
            ):
                msg = (
                    "codegen desired bytes and mode must be present or absent together"
                )
                raise ValueError(msg)
            return self

    class CodegenRepositoryPlanTask(FlextInfraConfigModelsContract.ConfigContract):
        """One repository's read-only planning inputs sent to a fleet worker."""

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
        contract: Annotated[
            FlextInfraConfigModelsArtifact.CodegenConformSurfaceContract,
            m.Field(description="Surface contract of the selected scope"),
        ]

    class CodegenRepositoryPlanOutcome(FlextInfraConfigModelsContract.ConfigContract):
        """One repository's planned files and environment, or its failure."""

        model_config = m.ConfigDict(arbitrary_types_allowed=True)
        exception: BaseException | None = m.Field(
            default=None,
            exclude=True,
            description="First native target planning cause",
        )
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Planned repository name"),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.CodegenFilePlan],
            m.Field(description="Governed and retired file plans"),
        ] = ()
        environment: Annotated[
            FlextInfraConfigModelsRelease.UvEnvironmentPlan | None,
            m.Field(description="uv environment plan of the repository"),
        ] = None
        error: Annotated[
            str,
            m.Field(description="Planning failure, empty on success"),
        ] = ""
        error_type: Annotated[
            str,
            m.Field(description="Original qualified exception type, when raised"),
        ] = ""
        error_traceback: Annotated[
            str,
            m.Field(description="Original planning traceback, without local variables"),
        ] = ""
        issues: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
            m.Field(description="Native failures attributed to individual targets"),
        ] = ()
        elapsed: Annotated[
            float,
            m.Field(ge=0, description="Planning wall seconds"),
        ] = 0.0

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

    class CodegenPlan(FlextInfraConfigModelsContract.ConfigContract):
        """Fully validated plan produced before any managed-file write."""

        model_config = m.ConfigDict(arbitrary_types_allowed=True)
        exception: BaseException | None = m.Field(
            default=None,
            exclude=True,
            description="First native target failure carried into publication",
        )
        request: Annotated[
            FlextInfraConfigModelsArtifact.CodegenConformRequest,
            m.Field(description="Validated public request"),
        ]
        repositories: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsContexts.RepositoryRef],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            FlextInfraConfigModelsWorkspace.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        make_spec: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        uv_environments: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsRelease.UvEnvironmentPlan],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.CodegenFilePlan],
            m.Field(description="All render results validated before application"),
        ]
        issues: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.Issue],
            m.Field(description="Planning failures retained alongside valid outputs"),
        ] = ()

    class CodegenResult(FlextInfraConfigModelsContract.ConfigContract):
        """Public conformance outcome for check and apply modes."""

        plan: Annotated[
            FlextInfraConfigModelsArtifact.CodegenPlan,
            m.Field(description="Plan that governed the operation"),
        ]
        written_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Files atomically replaced by apply"),
        ] = ()
        errors: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Fail-closed validation or write errors"),
        ] = ()

    class RenameCampaignSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One declared CSV-driven rename campaign applied by the mod verb."""

        csv: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Config-directory-relative path to the old,new rename-list "
                    "CSV; the list ships with the declaring config"
                ),
            ),
        ]
        roots: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description=(
                    "Repository-root-relative scan directories; empty selects "
                    "the whole repository root"
                ),
            ),
        ] = ()
        bindings: Annotated[
            t.MappingKV[str, t.StrSequence],
            m.Field(
                description=(
                    "CSV expression prefixes mapped "
                    "to current public Rope owner identities"
                ),
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, t.StrSequence]({}))
        text_globs: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Explicit root-relative non-Python "
                    "documentation and configuration text surfaces"
                ),
            ),
        ] = ()
        python_documentation: Annotated[
            bool,
            m.Field(
                description=(
                    "Rename comments and actual Python docstrings "
                    "without changing executable strings"
                ),
            ),
        ] = False
        exclude_globs: Annotated[
            t.StrSequence,
            m.Field(
                description="Generated projections excluded from campaign targets",
            ),
        ] = ()

        @staticmethod
        def _is_escaping_path(value: str) -> bool:
            """Whether one configured path escapes its declared relative owner.

            Returns:
                The resulting ``bool``.

            """
            path = Path(value)
            return bool(
                path.is_absolute()
                or PureWindowsPath(value).root
                or not path.parts
                or ".." in path.parts
                or "\\" in value
                or PureWindowsPath(value).drive,
            )

        @m.model_validator(mode="after")
        def _validate_source_paths(self) -> Self:
            """Keep campaign drivers and scan roots inside their declared owners.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If CSV campaign path must be relative and non-escaping.

            """
            for value in (self.csv, *self.roots):
                if self._is_escaping_path(value):
                    msg = (
                        f"CSV campaign path must be relative and non-escaping: {value}"
                    )
                    raise ValueError(msg)
            return self

    class RefactorCsvCampaignsSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Declared CSV-driven rename campaigns for the mod verb's rename phase."""

        campaigns: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.RenameCampaignSpec],
            m.Field(default=(), description="Ordered rename campaigns"),
        ] = ()

    class SedPatternSpec(FlextInfraConfigModelsContract.ConfigContract):
        """One declared literal regex substitution applied across the mod scope."""

        pattern: Annotated[t.NonEmptyStr, m.Field(description="Regex source to match")]
        replacement: Annotated[str, m.Field(description="Literal replacement text")]
        file_glob: Annotated[
            t.NonEmptyStr | None, m.Field(description="Optional file glob filter")
        ] = None
        flags: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description=("Regex flags by name (IGNORECASE, MULTILINE, DOTALL)"),
            ),
        ] = ()
        description: Annotated[
            t.NonEmptyStr | None,
            m.Field(default=None, description="Why this substitution exists"),
        ] = None

    class SedPatternsSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Declared sed-by-list substitution set with optional per-pattern filters."""

        patterns: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsArtifact.SedPatternSpec],
            m.Field(default=(), description="Ordered substitution patterns"),
        ] = ()
