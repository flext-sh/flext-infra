"""Workspace manifest, integration, and policy models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._constants.config import FlextInfraConstantsConfig
from flext_infra._models._config.beads import FlextInfraModelsConfigBeads
from flext_infra._models._config.contexts import FlextInfraModelsConfigContexts
from flext_infra._models._config.contract import FlextInfraModelsConfigContract
from flext_infra._models._config.make import FlextInfraModelsConfigMake


class FlextInfraModelsConfigWorkspace:
    """Workspace manifest, integration, and policy models."""

    class GitSubmoduleDeclaration(m.ContractModel):
        """One Git configuration section parsed by its canonical owner."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
        )

        path: Annotated[
            Path,
            m.Field(description="Submodule path relative to the superproject root"),
        ]
        url: Annotated[
            str,
            m.Field(description="Declared URL; empty when undeclared"),
        ]
        branch: Annotated[
            str,
            m.Field(description="Declared branch; empty when undeclared"),
        ]
        managed: Annotated[
            bool | None,
            m.Field(
                description=(
                    "Native Git boolean: absent inherits participation; "
                    "true participates and false does not"
                ),
            ),
        ]
        layer: Annotated[
            FlextInfraConstantsConfig.MemberArchitectureLayer | None,
            m.Field(
                description=(
                    "Declared architecture layer (domain or platform); "
                    "absent leaves the member outside the layered sets"
                ),
            ),
        ] = None

    class RefactorConfigSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Refactor file-selection configuration."""

        project_scan_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Relative directories scanned for candidate files"),
        ]
        file_extensions: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Allowed file extensions (empty = all by pattern)"),
        ] = m.Field(default_factory=tuple)

    class DependencyCommitSourceSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One dependency distribution resolved to an immutable Git commit.

        A staged candidate and a workspace member's recorded gitlink are the
        same fact: a distribution, its canonical repository and the exact
        commit it resolves to.
        """

        distribution: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact dependency distribution name"),
        ]
        url: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical HTTPS Git repository URL"),
        ]
        commit: Annotated[
            t.NonEmptyStr,
            m.Field(description="Full immutable Git commit OID"),
        ]

        @m.model_validator(mode="after")
        def _validate_source(self) -> Self:
            if not self.url.startswith("https://") or not self.url.endswith(
                c.GIT_DIR_NAME
            ):
                msg = "dependency commit source URL must be canonical HTTPS Git"
                raise ValueError(msg)
            if c.Infra.GIT_COMMIT_OID_RE.fullmatch(self.commit) is None:
                msg = "dependency commit source must pin a full Git OID"
                raise ValueError(msg)
            return self

    class CandidateDependenciesSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Share candidate-source validation without changing declaration shape."""

        candidate_dependencies: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.DependencyCommitSourceSpec, ...],
            m.Field(description="Candidate-only exact dependency Git sources"),
        ] = ()

        @m.field_validator("candidate_dependencies")
        @classmethod
        def _validate_candidate_dependencies(
            cls,
            values: tuple[
                FlextInfraModelsConfigWorkspace.DependencyCommitSourceSpec, ...
            ],
        ) -> tuple[FlextInfraModelsConfigWorkspace.DependencyCommitSourceSpec, ...]:
            """Require one immutable candidate per distribution and repository.

            Returns:
                The validated candidate dependency tuple unchanged.

            Raises:
                ValueError: If any distribution or repository URL repeats.

            """
            distributions = tuple(
                t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(item.distribution)
                for item in values
            )
            if len(set(distributions)) != len(distributions):
                msg = "candidate dependency distributions must be unique"
                raise ValueError(msg)
            urls = tuple(item.url for item in values)
            if len(set(urls)) != len(urls):
                msg = "candidate dependency repository URLs must be unique"
                raise ValueError(msg)
            return values

    class RepositoryDeltaSpec(CandidateDependenciesSpec):
        """Own repository differences; Git and project metadata own identity.

        The effective codegen configuration composes this declaration from the
        library defaults, the selected repository and its local overlay. It
        never declares another runtime repository or workspace participant.
        Recovery targets authorize bounded publication into existing worktrees.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            use_enum_values=False, extra="forbid"
        )

        project: Annotated[
            FlextInfraModelsConfigContexts.ProjectSpec | None,
            m.Field(description="Explicit metadata for a new project scaffold"),
        ] = None
        integration: Annotated[
            FlextInfraModelsConfigContexts.WorkspaceIntegrationSpec | None,
            m.Field(description="Explicit repository integration contract"),
        ] = None
        docs_audit: Annotated[
            FlextInfraModelsConfigContract.DocsAuditOverridesSpec,
            m.Field(description="Own documentation audit declarations"),
        ] = m.Field(
            default_factory=FlextInfraModelsConfigContract.DocsAuditOverridesSpec,
        )
        namespace_scan_dirs: Annotated[
            Sequence[str],
            m.Field(description="Own namespace analysis roots"),
        ] = ()
        candidate_bootstrap_targets: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.CandidateBootstrapTargetSpec, ...],
            m.Field(description="Declared candidate worktrees and recovery surfaces"),
        ] = ()
        workspace_inventory_command: Annotated[
            Sequence[str],
            m.Field(
                description=(
                    "Own public host inventory argv; empty leaves host discovery "
                    "unselected, with no external participant catalogue"
                ),
            ),
        ] = ()
        refactor: Annotated[
            FlextInfraModelsConfigWorkspace.RefactorConfigSpec | None,
            m.Field(description="Own refactor file-selection declaration"),
        ] = None
        beads_enabled: Annotated[
            bool,
            m.Field(description="Repository participates in the Beads contract"),
        ] = True
        gascity_enabled: Annotated[
            bool,
            m.Field(description="Repository consumes the Gas City runtime contract"),
        ] = True
        ci_enabled: Annotated[
            bool,
            m.Field(description="Repository projects its canonical CI surface"),
        ] = True
        ci_matrix_auto_run: Annotated[
            bool,
            m.Field(description="Repository enables automatic CI matrix execution"),
        ] = False
        codegen: Annotated[
            FlextInfraConstantsConfig.CodegenKind,
            m.Field(description="Own canonical generation policy"),
        ] = FlextInfraConstantsConfig.CodegenKind.CONFORM
        kind: Annotated[
            FlextInfraConstantsConfig.ProjectKind,
            m.Field(description="Own governance profile and architecture boundary"),
        ] = FlextInfraConstantsConfig.ProjectKind.INTERNAL_FLEXT
        state: Annotated[
            FlextInfraConstantsConfig.RepositoryState,
            m.Field(description="Own lifecycle participation policy"),
        ] = FlextInfraConstantsConfig.RepositoryState.ACTIVE
        read_only: Annotated[
            bool,
            m.Field(description="Repository rejects generated mutations"),
        ] = False
        publishes_release: Annotated[
            bool,
            m.Field(description="Repository declares the generated release protocol"),
        ] = False
        uv_link_mode: Annotated[
            Literal["clone", "copy", "hardlink", "symlink"] | None,
            m.Field(description="Own uv installation link-mode declaration"),
        ] = None
        duplication_trees: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Own additional duplication-analysis trees"),
        ] = ()
        examples_module: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                pattern=r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$",
                description="Own explicit examples module",
            ),
        ] = None
        extra_verbs: Annotated[
            tuple[FlextInfraModelsConfigMake.MakeVerbSpec, ...],
            m.Field(description="Own additional public Make commands"),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraModelsConfigContexts.ScriptDispatchSpec | None,
            m.Field(description="Own script command routing contract"),
        ] = None

    class CandidateBootstrapTargetSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One declared worktree and canonical conform surface."""

        # The planner's surface contract takes the enum member, so the
        # contract base's value coercion is switched off here.
        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        path: Annotated[Path, m.Field(description="Relative candidate worktree path")]
        what: Annotated[
            FlextInfraConstantsConfig.CodegenConformSurface,
            m.Field(description="Canonical generator surface for this target"),
        ]

        @m.field_validator("path", mode="before")
        @classmethod
        def _validate_path_input[TPayload](cls, value: TPayload) -> TPayload:
            if isinstance(value, str) and not value.strip():
                msg = "candidate bootstrap path must not be empty"
                raise ValueError(msg)
            return value

        @m.model_validator(mode="after")
        def _validate_path(self) -> Self:
            if self.path.is_absolute():
                msg = "candidate bootstrap path must be relative"
                raise ValueError(msg)
            return self

    class DependencyGroupInclude(m.ContractModel):
        """One native PEP 735 inclusion at its original array position."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        include_group: Annotated[
            t.NonEmptyStr,
            m.Field(alias="include-group", description="Referenced dependency group"),
        ]

    class DependencyGroupEntries(m.RootModel[tuple[str | DependencyGroupInclude, ...]]):
        """Native ordered PEP 735 entries, without resolving local references."""

        @m.model_validator(mode="before")
        @classmethod
        def toml_array(
            cls, value: t.JsonValue
        ) -> t.JsonValue | tuple[t.JsonValue, ...]:
            """Freeze an array while retaining each native inclusion table.

            Returns:
                The array frozen as a tuple, or the untouched payload.

            """
            return tuple(value) if isinstance(value, list) else value

    class DependencyGroupDeclarations(m.ContractModel):
        """Shared native dependency-group grammar and local reference graph."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(populate_by_name=True)

        dependency_groups: Annotated[
            Mapping[
                str,
                tuple[
                    str | FlextInfraModelsConfigWorkspace.DependencyGroupInclude, ...
                ],
            ],
            m.Field(
                alias="dependency-groups", description="Ordered native group entries"
            ),
        ]

        @m.field_validator("dependency_groups", mode="before")
        @classmethod
        def toml_group_arrays(
            cls, value: t.JsonValue
        ) -> t.JsonValue | Mapping[str, t.JsonValue | tuple[t.JsonValue, ...]]:
            """Freeze TOML containers without converting inclusion tables to strings.

            Returns:
                The mapping with every group array frozen as a tuple, or the
                untouched payload.

            """
            if isinstance(value, dict):
                return {
                    name: tuple(entries) if isinstance(entries, list) else entries
                    for name, entries in value.items()
                }
            return value

        @m.field_validator("dependency_groups")
        @classmethod
        def local_group_graph(
            cls,
            groups: Mapping[
                str,
                tuple[
                    str | FlextInfraModelsConfigWorkspace.DependencyGroupInclude, ...
                ],
            ],
        ) -> Mapping[
            str,
            tuple[str | FlextInfraModelsConfigWorkspace.DependencyGroupInclude, ...],
        ]:
            """Reject missing, ambiguous or cyclic local group inclusions.

            Returns:
                The validated group entries with their inclusion graph.

            Raises:
                ValueError: If dependency group names have colliding normalized
                    identities; or if a group includes an undeclared group; or
                    if the local group inclusions form a cycle.

            """
            canonical = t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python
            names = {canonical(name): name for name in groups}
            if len(names) != len(groups):
                msg = "dependency group names have colliding normalized identities"
                raise ValueError(msg)
            graph: dict[str, tuple[str, ...]] = {}
            for name, entries in groups.items():
                references = tuple(
                    canonical(entry.include_group)
                    for entry in entries
                    if not isinstance(entry, str)
                )
                if any(reference not in names for reference in references):
                    msg = f"dependency group includes an undeclared group: {name}"
                    raise ValueError(msg)
                graph[canonical(name)] = references
            active: list[str] = []
            visited: set[str] = set()

            def visit(name: str) -> None:
                if name in active:
                    msg = "cyclic dependency group inclusion: " + " -> ".join(
                        (*active, name),
                    )
                    raise ValueError(msg)
                if name in visited:
                    return
                active.append(name)
                for reference in graph[name]:
                    visit(reference)
                active.pop()
                visited.add(name)

            for name in graph:
                visit(name)
            return groups

    class DependencyManifestSpec(DependencyGroupDeclarations, m.ExternalContractModel):
        """Dependency facts one member's own ``pyproject.toml`` declares.

        The external-contract preset reads this subset of the native document
        and ignores its other tables.
        """

        name: Annotated[
            t.NonEmptyStr,
            m.Field(
                validation_alias=m.AliasPath("project", "name"),
                description="PEP 621 distribution name",
            ),
        ]
        dependencies: Annotated[
            Sequence[str],
            m.Field(
                validation_alias=m.AliasPath("project", "dependencies"),
                description="PEP 621 runtime requirements",
            ),
        ] = ()
        dependency_groups: Annotated[
            Mapping[
                str,
                tuple[
                    str | FlextInfraModelsConfigWorkspace.DependencyGroupInclude, ...
                ],
            ],
            m.Field(
                validation_alias=c.Infra.DEPENDENCY_GROUPS,
                description="PEP 735 dependency groups (dev, codegen, ...)",
            ),
        ] = m.Field(
            default_factory=lambda: MappingProxyType[
                str,
                tuple[
                    str | FlextInfraModelsConfigWorkspace.DependencyGroupInclude, ...
                ],
            ]({}),
        )

    class DependencyEdgeSpec(m.ContractModel):
        """One directed requirement edge between two workspace members."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
        )

        dependent: Annotated[
            t.NonEmptyStr,
            m.Field(description="Member distribution declaring the requirement"),
        ]
        dependency: Annotated[
            t.NonEmptyStr,
            m.Field(description="Member distribution it requires"),
        ]

    type CandidateBootstrapTargets = tuple[CandidateBootstrapTargetSpec, ...]
    """Shared declaration type for repeated candidate worktree target fields."""

    class WorkspaceBeadsServerSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Optional Dolt connection declared by a versioned workspace manifest."""

        backend: Annotated[
            Literal["dolt"],
            m.Field(description="Workspace ledger storage engine"),
        ]
        mode: Annotated[
            Literal["server"],
            m.Field(description="Workspace ledger connection mode"),
        ]
        shared_server: Annotated[
            Literal[False],
            m.Field(description="Workspace ledger uses an external Dolt endpoint"),
        ] = False
        host: Annotated[t.NonEmptyStr, m.Field(description="Dolt server host")]
        port: Annotated[
            int,
            m.Field(ge=1, le=65535, description="Dolt server TCP port"),
        ]
        user: Annotated[t.NonEmptyStr, m.Field(description="Dolt server user")]
        auto_commit: Annotated[
            Literal["off", "on", "batch"],
            m.Field(description="Dolt auto-commit policy"),
        ]

    class RepositoryPolicyOverlaySpec(FlextInfraModelsConfigContract.ConfigContract):
        """Bounded per-project policy declared by a workspace manifest."""

        project: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical project distribution"),
        ]
        beads_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the repository participates in Beads; an overlay "
                    "that omits it means the same as no overlay (enabled)"
                ),
            ),
        ] = True
        ci_enabled: Annotated[
            bool,
            m.Field(description="Whether conform owns the CI surface"),
        ] = True
        ci_matrix_auto_run: Annotated[
            bool,
            m.Field(description="Whether the CI matrix runs automatically"),
        ] = False
        gascity_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the repository consumes the Gas City runtime "
                    "contract (city-owned Dolt server, gc tool projection, "
                    "inherited endpoint keys). False renders the standalone "
                    "shape: repository-local Dolt server owned by Beads."
                ),
            ),
        ] = True

    class WorkspaceExclusionSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One explicitly excluded workspace-relative path."""

        path: Annotated[Path, m.Field(description="Workspace-relative path")]
        reason: Annotated[t.NonEmptyStr, m.Field(description="Exclusion rationale")]

    class WorkspaceManifestSpec(CandidateDependenciesSpec):
        """Complete versioned input contract for ``config/workspace.yaml``."""

        version: Annotated[
            int,
            m.Field(
                ge=c.Infra.WORKSPACE_MANIFEST_VERSION,
                le=c.Infra.WORKSPACE_MANIFEST_VERSION,
                description="Workspace manifest schema version",
            ),
        ]
        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        docs_audit: Annotated[
            FlextInfraModelsConfigContract.DocsAuditOverridesSpec,
            m.Field(
                description="Repository-owned documentation audit declarations",
            ),
        ] = m.Field(
            default_factory=FlextInfraModelsConfigContract.DocsAuditOverridesSpec
        )
        namespace_scan_dirs: Annotated[
            Sequence[str],
            m.Field(
                description=(
                    "Repository-level production roots the namespace validator "
                    "enforces; an empty declaration keeps every root in scope, and "
                    "an explicit project-level declaration wins"
                ),
            ),
        ] = ()
        ledger_id: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional workspace ledger database identity"),
        ] = None
        ledger_prefix: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional workspace issue-prefix identity"),
        ] = None
        beads_server: Annotated[
            FlextInfraModelsConfigWorkspace.WorkspaceBeadsServerSpec | None,
            m.Field(description="Optional workspace-local Dolt connection"),
        ] = None
        repository: Annotated[
            FlextInfraModelsConfigContexts.RepositoryRef,
            m.Field(description="Root repository declaration"),
        ]
        project: Annotated[
            FlextInfraModelsConfigContexts.ProjectSpec | None,
            m.Field(description="Optional project creation metadata"),
        ] = None
        members: Annotated[
            tuple[FlextInfraModelsConfigContexts.RepositoryRef, ...],
            m.Field(description="Declared member repository contracts"),
        ] = ()
        external_dependency_paths: Annotated[
            tuple[Path, ...],
            m.Field(description="Declared external dependency paths"),
        ] = ()
        content_only: Annotated[
            tuple[Path, ...],
            m.Field(description="Content-only Gitlink paths"),
        ] = ()
        exclusions: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.WorkspaceExclusionSpec, ...],
            m.Field(description="Explicit workspace exclusions"),
        ] = ()
        integration: Annotated[
            FlextInfraModelsConfigContexts.WorkspaceIntegrationSpec | None,
            m.Field(description="Optional integration provider overlay"),
        ] = None
        candidate_bootstrap_targets: Annotated[
            FlextInfraModelsConfigWorkspace.CandidateBootstrapTargets,
            m.Field(description="Declared candidate worktrees conformed by Infra"),
        ] = ()
        repository_policy_overlays: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.RepositoryPolicyOverlaySpec, ...],
            m.Field(description="Repository-local policy overlays"),
        ] = ()
        external_consumers: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.ExternalConsumerSpec, ...],
            m.Field(
                description=(
                    "Out-of-workspace repositories propagation adjusts as"
                    " guests through their own make verbs"
                ),
            ),
        ] = ()
        refactor: Annotated[
            FlextInfraModelsConfigWorkspace.RefactorConfigSpec | None,
            m.Field(description="Refactor file-selection configuration"),
        ] = None

        @m.model_validator(mode="after")
        def _validate_references(self) -> Self:
            """Reject ambiguous paths and policy references in the full document.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If ``invalid_paths``; or if composed project paths must be
                    unique; or if composed projects cannot also be external
                    dependencies; or if repository policy overlays must be unique; or if
                    ``unknown_projects``; or if candidate dependency distributions must
                    be unique; or if candidate bootstrap targets must be unique.

            """
            external_paths = (*self.external_dependency_paths, *self.content_only)
            invalid_paths = tuple(
                path
                for path in external_paths
                if path.is_absolute() or not path.parts or ".." in path.parts
            )
            if invalid_paths:
                msg = "workspace dependency paths must be relative: " + ", ".join(
                    path.as_posix() for path in invalid_paths
                )
                raise ValueError(msg)
            member_paths = tuple(item.path for item in self.members)
            if len(set(member_paths)) != len(member_paths):
                msg = "composed project paths must be unique"
                raise ValueError(msg)
            if set(member_paths).intersection(external_paths):
                msg = "composed projects cannot also be external dependencies"
                raise ValueError(msg)
            projects = tuple(item.project for item in self.repository_policy_overlays)
            if len(set(projects)) != len(projects):
                msg = "repository policy overlays must be unique"
                raise ValueError(msg)
            repository_names = {
                item.distribution for item in (self.repository, *self.members)
            }
            unknown_projects = set(projects).difference(repository_names)
            if unknown_projects:
                msg = (
                    "repository policy overlays reference unknown projects: "
                    + ", ".join(sorted(unknown_projects))
                )
                raise ValueError(msg)
            targets = self.candidate_bootstrap_targets
            if len({target.path for target in targets}) != len(targets):
                msg = "candidate bootstrap targets must be unique"
                raise ValueError(msg)
            return self

    class CodegenBootstrapSource(FlextInfraModelsConfigContract.ConfigContract):
        """Explicit dependency provenance before a scaffold has project metadata."""

        url: Annotated[t.NonEmptyStr, m.Field(description="Infrastructure Git URL")]
        ref: Annotated[t.NonEmptyStr, m.Field(description="Infrastructure Git ref")]

    class HostWorkspaceInventoryEntry(FlextInfraModelsConfigContract.ConfigContract):
        """One checkout identity received from the public host inventory."""

        project_id: Annotated[
            t.NonEmptyStr, m.Field(description="Forge project identity")
        ]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Resolved forge owner")]
        path: Annotated[Path, m.Field(description="Physical checkout root")]
        checkout_id: Annotated[t.NonEmptyStr, m.Field(description="Checkout identity")]
        governing_checkout_id: Annotated[
            t.NonEmptyStr, m.Field(description="Project's governing checkout identity")
        ]
        project_profile: Annotated[
            FlextInfraConstantsConfig.ProjectKind | Literal["unclassified"],
            m.Field(description="Host's declared governance and architecture profile"),
        ]
        upstream_project_id: Annotated[
            str | None, m.Field(description="Declared fork upstream identity")
        ]
        effective_ref: Annotated[
            str | None, m.Field(description="Host's resolved checkout reference")
        ]

    class HostWorkspaceInventory(FlextInfraModelsConfigContract.ConfigContract):
        """Exact public host inventory envelope parsed once at ingress."""

        entries: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.HostWorkspaceInventoryEntry, ...],
            m.Field(description="Canonical discovered checkout identities"),
        ]

    class ExternalConsumerSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One out-of-workspace repository propagation adjusts as a guest.

        The consumer keeps its own governance: propagation only advances its
        declared lane through the consumer's own canonical ``make`` verbs, so
        FLEXT architecture is never imposed on a non-member repository.
        """

        name: Annotated[t.NonEmptyStr, m.Field(description="Consumer display name")]
        root: Annotated[
            Path,
            m.Field(
                description=(
                    "Absolute checkout root of the consumer repository outside"
                    " this workspace"
                ),
            ),
        ]
        integration_branch: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Consumer integration branch; absent defers to the"
                    " resolver's provider fallback"
                ),
            ),
        ] = None
        fix_namespace: Annotated[
            bool,
            m.Field(description="Run the consumer's make fix-namespace verb"),
        ] = True
        fix_accessors: Annotated[
            bool,
            m.Field(description="Run the consumer's make fix-accessors verb"),
        ] = True

    class WorkspaceSpec(CandidateDependenciesSpec):
        """Local identity plus topology read from this repository's Git inputs."""

        inputs: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True,
                description="Original topology and declaration observations",
            ),
        ] = ()
        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        docs_audit: Annotated[
            FlextInfraModelsConfigContract.DocsAuditOverridesSpec,
            m.Field(
                description="Validated local documentation audit declarations",
            ),
        ] = m.Field(
            default_factory=FlextInfraModelsConfigContract.DocsAuditOverridesSpec
        )
        beads: Annotated[
            FlextInfraModelsConfigBeads.BeadsProjectSpec | None,
            m.Field(description="Repository-local Beads identity when enabled"),
        ] = None
        gascity_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Gas City runtime-contract participation resolved from the "
                    "matched repository policy overlay; True when the checkout "
                    "declares no manifest or no overlay."
                ),
            ),
        ] = True
        repository: Annotated[
            FlextInfraModelsConfigContexts.RepositoryRef,
            m.Field(description="Local repository Git contract"),
        ]
        project: Annotated[
            FlextInfraModelsConfigContexts.ProjectSpec | None,
            m.Field(description="Metadata required only when materializing a new tree"),
        ] = None
        flext_source: Annotated[
            FlextInfraModelsConfigWorkspace.CodegenBootstrapSource | None,
            m.Field(
                description=(
                    "FLEXT dependency source required before the first pyproject "
                    "exists; generated dependencies own provenance afterwards."
                ),
            ),
        ] = None
        namespace_scan_dirs: Annotated[
            Sequence[str],
            m.Field(
                description=(
                    "Repository-level production roots the namespace validator "
                    "enforces; an empty declaration keeps every root in scope, and "
                    "an explicit project-level declaration wins"
                ),
            ),
        ] = ()
        integration: Annotated[
            FlextInfraModelsConfigContexts.WorkspaceIntegrationSpec | None,
            m.Field(
                description=(
                    "Declared integration provider and branch from the workspace "
                    "manifest; the resolver consults it before any Git fact"
                ),
            ),
        ] = None
        candidate_bootstrap_targets: Annotated[
            FlextInfraModelsConfigWorkspace.CandidateBootstrapTargets,
            m.Field(description="Declared candidate worktrees for bootstrap"),
        ] = ()
        subprojects: Annotated[
            tuple[FlextInfraModelsConfigContexts.RepositoryRef, ...],
            m.Field(description="Direct governed repositories from local .gitmodules"),
        ] = ()
        pending_subprojects: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.GitSubmoduleDeclaration, ...],
            m.Field(
                description="Managed Git declarations awaiting checkout provisioning",
            ),
        ] = ()
        external_dependency_paths: Annotated[
            tuple[Path, ...],
            m.Field(description="Observed external or fork Git submodule paths"),
        ] = ()
        external_consumers: Annotated[
            tuple[FlextInfraModelsConfigWorkspace.ExternalConsumerSpec, ...],
            m.Field(
                description=(
                    "Out-of-workspace repositories propagation adjusts as"
                    " guests through their own make verbs"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_topology_paths(self) -> Self:
            """Reject duplicate, ambiguous, or escaping topology paths.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If external dependency paths must be workspace-relative; or
                    if external dependency paths must be unique; or if subproject paths
                    must be unique; or if external dependencies cannot also be governed
                    subprojects; or if external consumers must declare unique names
                    with absolute roots.

            """
            invalid_external_paths = tuple(
                path
                for path in self.external_dependency_paths
                if path.is_absolute() or not path.parts or ".." in path.parts
            )
            if invalid_external_paths:
                msg = (
                    "external dependency paths must be workspace-relative: "
                    f"{', '.join(path.as_posix() for path in invalid_external_paths)}"
                )
                raise ValueError(msg)
            if len(set(self.external_dependency_paths)) != len(
                self.external_dependency_paths,
            ):
                msg = "external dependency paths must be unique"
                raise ValueError(msg)
            subproject_paths = {item.path for item in self.subprojects}
            if len(subproject_paths) != len(self.subprojects):
                msg = "subproject paths must be unique"
                raise ValueError(msg)
            overlap = subproject_paths.intersection(self.external_dependency_paths)
            if overlap:
                msg = (
                    "external dependencies cannot also be governed subprojects: "
                    f"{', '.join(sorted(path.as_posix() for path in overlap))}"
                )
                raise ValueError(msg)
            pending_paths = {item.path for item in self.pending_subprojects}
            invalid_pending_paths = tuple(
                item.path
                for item in self.pending_subprojects
                if item.path.is_absolute()
                or not item.path.parts
                or ".." in item.path.parts
                or item.managed is False
            )
            if invalid_pending_paths:
                msg = (
                    "pending subprojects require managed workspace-relative paths: "
                    + ", ".join(path.as_posix() for path in invalid_pending_paths)
                )
                raise ValueError(msg)
            if len(pending_paths) != len(self.pending_subprojects):
                msg = "pending subproject paths must be unique"
                raise ValueError(msg)
            if pending_paths.intersection(
                subproject_paths | set(self.external_dependency_paths),
            ):
                msg = "pending subprojects cannot also have resolved identities"
                raise ValueError(msg)
            consumer_names = [item.name for item in self.external_consumers]
            if len(set(consumer_names)) != len(consumer_names):
                msg = "external consumer names must be unique"
                raise ValueError(msg)
            relative_roots = tuple(
                item.root
                for item in self.external_consumers
                if not item.root.is_absolute()
            )
            if relative_roots:
                msg = (
                    "external consumer roots must be absolute: "
                    f"{', '.join(path.as_posix() for path in relative_roots)}"
                )
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsConfigWorkspace"]
