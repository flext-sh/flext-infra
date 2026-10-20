"""Transaction and session models for the codegen pipeline.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import (
    FlextInfraModelsBase,
    FlextInfraModelsCheck,
    FlextInfraModelsCodegenToolchain,
    FlextInfraModelsRope,
)
from flext_infra._models._codegen import (
    FlextInfraModelsCodegenJournalModels,
    FlextInfraModelsCodegenPipelineModels,
)
from flext_infra._models._config import FlextInfraConfigModels
from flext_infra._models.workspace import FlextInfraModelsWorkspace


class FlextInfraModelsCodegenTransactionModels:
    """Transaction and session models for the codegen pipeline."""

    class CodegenSourcePreviewOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Authenticated inputs and runtime boundaries for one source preview."""

        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(), description="Pinned source states authenticated by the preview"
        )
        runtime_root: Path | None = m.Field(
            default=None, description="Explicit physical runtime owner when supplied"
        )
        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        runtime_check: bool = m.Field(
            default=True,
            description="Validate the candidate through its native runtime",
        )
        modes: t.MappingKV[Path, int] | None = m.Field(
            default=None,
            description="Declared file modes for the staged source updates",
        )

    class StageSourceOptions(FlextInfraModelsBase.FrozenArbitrary):
        """Authenticated inputs, topology and declarations for a source candidate."""

        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            default=(), description="Pinned source states of the staging invocation"
        )
        workspaces: tuple[Path, ...] = m.Field(
            default=(), description="Explicit composition scopes of the staged view"
        )
        modes: t.MappingKV[Path, int] | None = m.Field(
            default=None, description="Declared source modes preserved during staging"
        )
        declared_files: tuple[FlextInfraConfigModels.CodegenFilePlan, ...] = m.Field(
            default=(), description="Authenticated candidate file declarations"
        )
        source_directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = m.Field(
            default=(), description="Original native source election receipts"
        )
        source_query_topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = m.Field(
            default=(), description="Original native source query ancestry"
        )

    class StagePackagePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Pinned package/dependency inputs and the declared public facade contract."""

        package: str = m.Field(description="Selected canonical package namespace")
        module: str = m.Field(description="Selected public facade module")
        classname: str = m.Field(description="Published class preserved by projection")
        owner_module: str = m.Field(description="Canonical complete private owner")
        upstream: t.VariadicTuple[t.Pair[str, str]] = m.Field(
            description="Declared upstream base imports"
        )
        members: t.StrSequence = m.Field(
            description="Owner declarations inherited by the public facade"
        )
        layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Pinned package layouts"
        )
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            description="Pinned source/resource/metadata states"
        )
        workspace_packages: t.StrSequence = m.Field(
            description="Workspace namespaces requiring sealed origins"
        )

    class StageSourcePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Pinned project closure and desired bytes for effect-free validation."""

        version: Literal[1] = m.Field(default=1, description="Source receipt version")
        workspace: Path = m.Field(description="Canonical source workspace root")
        workspaces: tuple[Path, ...] = m.Field(
            default=(),
            description="Explicit composition scopes, never a parent-directory scan",
        )
        roots: tuple[Path, ...] = m.Field(
            description="Discovered project roots covering the pinned source closure"
        )
        inputs: tuple[m.Cli.AtomicFileState, ...] = m.Field(
            description="Exact source and configuration observations"
        )
        source_directories: tuple[m.Cli.AtomicDirectoryInventory, ...] = m.Field(
            default=(), description="Native directory elections of this source epoch"
        )
        source_query_topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = m.Field(
            default=(), description="Native root and source query identities"
        )
        prepared_hashes: t.VariadicTuple[t.Pair[Path, str | None]] = m.Field(
            default=(), description="Exact prepared update digests; None retires a file"
        )
        directory_publications: tuple[m.Cli.AtomicDirectoryState, ...] = m.Field(
            default=(), description="Journal-proven own directory births for admission"
        )
        updates: t.MappingKV[Path, str | None] = m.Field(
            description=(
                "Desired sources keyed by live destination; None retires an artifact"
            ),
        )
        modes: t.MappingKV[Path, int] = m.Field(
            default_factory=lambda: MappingProxyType[Path, int]({}),
            description="Desired file-effect modes derived from original move sources",
        )
        declared_files: tuple[FlextInfraConfigModels.CodegenFilePlan, ...] = m.Field(
            default=(),
            description=(
                "Original file/absence witnesses with the current desired effects"
            ),
        )
        layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Original project layouts in the desired import closure",
        )
        workspace_packages: tuple[str, ...] = m.Field(
            description="Declared workspace namespaces with sealed candidate origins",
        )

    class SemanticSourcePlan(m.ImmutableValueModel):
        """Authenticated source campaign independent of explicit rename intent."""

        candidate: FlextInfraModelsCodegenTransactionModels.StageSourcePlan = m.Field(
            description="Authenticated complete source and runtime candidate closure"
        )
        consumer_roots: t.VariadicTuple[Path] = m.Field(
            default=(),
            description="External scopes elected before producer publication",
        )
        source_states: t.VariadicTuple[m.Cli.AtomicFileState] = m.Field(
            default=(), description="Original physical binding and consumption epoch"
        )
        source_directories: t.VariadicTuple[m.Cli.AtomicDirectoryInventory] = m.Field(
            default=(), description="Original native directory-election receipts"
        )
        source_query_topology: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = m.Field(
            default=(), description="Original native path-election topology receipts"
        )

    class StagePackageView(FlextInfraModelsBase.FrozenArbitrary):
        """Journal-owned materialized package view, never another source of truth."""

        plan: FlextInfraModelsCodegenTransactionModels.StagePackagePlan = m.Field(
            description="Pinned input and public-feature contract"
        )
        root: Path = m.Field(
            description="Runtime artifact inside a registered transaction root"
        )
        layouts: tuple[FlextInfraModelsRope.RopeProjectLayout, ...] = m.Field(
            description="Actual materialized package origins"
        )
        manifest: m.Cli.AtomicPhysicalTreeManifest = m.Field(
            description="Descriptor-authenticated candidate tree"
        )
        target: m.Cli.AtomicPhysicalTreeEntry = m.Field(
            description="Exact desired facade bytes and physical identity"
        )

    class CodegenTransactionJournal(FlextInfraModelsBase.FrozenArbitrary):
        """Persisted recovery contract for one workspace-wide generation."""

        version: Annotated[
            Literal[9],
            m.Field(description="Exact journal schema version"),
        ]
        transaction_id: Annotated[
            str,
            m.Field(
                pattern=r"^[0-9a-f]{32}$",
                description="Unpredictable generation transaction identity",
            ),
        ]
        scope_device: Annotated[
            int,
            m.Field(ge=0, strict=True, description="Scope directory device"),
        ]
        scope_inode: Annotated[
            int,
            m.Field(gt=0, strict=True, description="Scope directory inode"),
        ]
        state: Annotated[
            Literal["staging", "prepared", "committed"],
            m.Field(description="Durable publication transition state"),
        ]
        projects: Annotated[
            tuple[FlextInfraModelsCodegenJournalModels.CodegenJournalProject, ...],
            m.Field(description="Ordered project selectors owned by this transaction"),
        ]
        file_participants: Annotated[
            tuple[FlextInfraModelsCodegenToolchain.CodegenFileParticipant, ...],
            m.Field(description="Exact physical file publication capabilities"),
        ] = ()
        sources: Annotated[
            tuple[FlextInfraModelsCodegenJournalModels.CodegenJournalSource, ...],
            m.Field(description="Source identities used by staging"),
        ]
        outputs: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenJournalSource
        ] = m.Field(default=(), description="Complete output proof, including no-ops")
        generator_sources: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenJournalSource
        ] = m.Field(default=(), description="Captured loaded generator implementation")
        generator_trees: tuple[m.Cli.AtomicPhysicalTreeManifest, ...] = m.Field(
            default=(), description="Producer resource membership before planning"
        )
        generator_modules: t.VariadicTuple[t.Pair[str, Path]] = m.Field(
            default=(), description="Immutable producer module election"
        )
        generator_reference: FlextInfraModelsWorkspace.NativeImportReference | None = (
            m.Field(
                default=None,
                description="Immutable native producer epoch before effects",
            )
        )
        source_topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = m.Field(
            default=(),
            description="Source-owner directory witnesses for observation",
        )
        source_directories: tuple[t.Pair[str, m.Cli.AtomicDirectoryInventory], ...] = (
            m.Field(
                default=(),
                strict=True,
                description="Native source election query receipts",
            )
        )
        source_query_topology: tuple[
            t.Pair[str, m.Cli.AtomicDirectoryChainPlan], ...
        ] = m.Field(
            default=(),
            strict=True,
            description="Historical ancestry inputs of native source queries",
        )
        scope_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="Source-owner roots for topology observation",
        )
        source_scope: Path | None = m.Field(
            default=None, description="Member elected by the native docs source owner"
        )
        phase: c.Infra.CodegenStagedFilePhase | None = m.Field(
            default=None, description="Actual publication phase"
        )
        directories: Annotated[
            t.VariadicTuple[
                FlextInfraModelsCodegenJournalModels.CodegenJournalDirectory
            ],
            m.Field(description="Directories whose prior absence authorizes creation"),
        ]
        entries: Annotated[
            tuple[FlextInfraModelsCodegenJournalModels.CodegenJournalEntry, ...],
            m.Field(description="Recoverable artifact transitions"),
        ]
        staging_intents: Annotated[
            tuple[FlextInfraModelsCodegenJournalModels.CodegenStagingIntent, ...],
            m.Field(description="Durable authority for staging bytes before creation"),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_lifecycle(self) -> Self:
            """Bind staging and publication payloads to one safe project set.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If generation journal requires an explicit participant; or
                    if Mise root selector must be first when present; or if Mise journal
                    project selectors must be unique; or if staging codegen journal must
                    not authorize live transitions; or if staging codegen journal cannot
                    generate a transaction root; or if codegen journal destination paths
                    must be unique; or if codegen journal entry has no project
                    participant; or if codegen journal directory paths must be unique;
                    or if codegen journal directory has no project participant; or if
                    a source dependency is duplicated or lacks same-phase authority.

            """
            participants: t.VariadicTuple[
                FlextInfraModelsCodegenJournalModels.CodegenJournalProject
                | FlextInfraModelsCodegenToolchain.CodegenFileParticipant
            ] = (*self.projects, *self.file_participants)
            selectors = tuple(project.selector for project in participants)
            if not selectors:
                msg = "generation journal requires an explicit participant"
                raise ValueError(msg)
            if selectors[0] != "." and "." in selectors:
                msg = "Mise root selector must be first when present"
                raise ValueError(msg)
            if len(set(selectors)) != len(selectors):
                msg = "Mise journal project selectors must be unique"
                raise ValueError(msg)
            self._validate_staging_authority()
            self._validate_participant_coverage(selectors)
            source_keys = {(source.phase, source.path) for source in self.sources}
            directory_keys = {
                (phase, receipt.root.path) for phase, receipt in self.source_directories
            }
            topology_keys = {
                (phase, receipt.target) for phase, receipt in self.source_query_topology
            }
            if len(directory_keys) != len(self.source_directories) or len(
                topology_keys
            ) != len(self.source_query_topology):
                msg_0 = "journal native query receipts require unique phase paths"
                raise ValueError(msg_0)
            for entry in self.entries:
                if len(set(entry.source_paths)) != len(entry.source_paths):
                    msg = "journal entry source dependencies must be unique"
                    raise ValueError(msg)
                if any(
                    (entry.phase, path) not in source_keys
                    for path in entry.source_paths
                ):
                    msg = "journal entry source dependency has no same-phase authority"
                    raise ValueError(msg)
                if any(
                    (entry.phase, path) not in directory_keys
                    for path in entry.source_directory_paths
                ) or any(
                    (entry.phase, path) not in topology_keys
                    for path in entry.source_query_topology_paths
                ):
                    msg_0 = "journal native query reference lacks same-phase authority"
                    raise ValueError(msg_0)
            staging_paths = tuple(intent.before.path for intent in self.staging_intents)
            if len(set(staging_paths)) != len(staging_paths):
                msg = "staging intention paths must have unique authority"
                raise ValueError(msg)
            return self

        def _validate_staging_authority(self) -> None:
            """Reject live transitions a staging journal may never authorize.

            Raises:
                ValueError: If staging codegen journal must not authorize live
                    transitions; or if staging codegen journal cannot generate a
                    transaction root.

            """
            if self.state == "staging" and self.entries:
                msg = "staging codegen journal must not authorize live transitions"
                raise ValueError(msg)
            if self.state == "staging" and any(
                directory.disposition == "generated"
                and directory.phase == "transaction"
                for directory in self.directories
            ):
                # A staging journal authorizes no live transition — that is the
                # `entries` rule above. It must still authorize the destination
                # directory of a file phase: staging snapshots the live target,
                # which requires a physical parent, so a generated destination
                # can never be recorded after the entries it makes possible.
                # Rollback removes them with the temporary roots
                # (`include_generated` for any non-committed journal). Only the
                # transaction's own roots stay restricted to `temporary`.
                msg = "staging codegen journal cannot generate a transaction root"
                raise ValueError(msg)

        def _validate_participant_coverage(self, selectors: t.StrSequence) -> None:
            """Require unique destination paths covered by declared participants.

            Raises:
                ValueError: If codegen journal destination paths must be unique; or
                    if codegen journal entry has no project participant; or if codegen
                    journal directory paths must be unique; or if codegen journal
                    directory has no project participant.

            """
            entry_paths = tuple(entry.path for entry in self.entries)
            staging_paths = tuple(
                path
                for entry in self.entries
                for path in (entry.desired_staging, entry.original_staging)
                if path is not None
            )
            if len(set(staging_paths)) != len(staging_paths):
                msg = "journal preimage/replacement staging has competing owners"
                raise ValueError(msg)
            if len(set(entry_paths)) != len(entry_paths):
                msg = "codegen journal destination paths must be unique"
                raise ValueError(msg)
            if any(entry.project not in selectors for entry in self.entries):
                msg = "codegen journal entry has no project participant"
                raise ValueError(msg)
            directory_paths = tuple(directory.path for directory in self.directories)
            if len(set(directory_paths)) != len(directory_paths):
                msg = "codegen journal directory paths must be unique"
                raise ValueError(msg)
            if any(
                directory.project not in selectors for directory in self.directories
            ):
                msg = "codegen journal directory has no project participant"
                raise ValueError(msg)

    class CodegenFootprintRequest(m.Value):
        """Inspect recorded generation authority, not prospective generation inputs."""

        root: Path = m.Field(description="Repository or workspace coordination root")

    class CodegenFootprint(m.Value):
        """Observed journal identity and recorded physical effect footprint."""

        scope_root: Path = m.Field(description="Authenticated coordination root")
        journal_path: Path = m.Field(description="Canonical journal anchor")
        snapshot_identity: str = m.Field(
            description="Normalized canonical file-state fields excluding raw content",
        )
        snapshot_sha256: str | None = m.Field(
            description="Digest of the exact observed journal bytes, or absent",
        )
        journal_version: int | None = m.Field(
            description="Schema version read from the typed journal, or absent",
        )
        transaction_id: str | None = m.Field(
            description="Transaction identity read from the typed journal, or absent",
        )
        normalized_journal_sha256: str | None = m.Field(
            description="Digest of the parsed journal representation, not disk bytes",
        )
        authorized_roots: tuple[Path, ...] = m.Field(
            default=(),
            description="Physical roots authorized by current topology",
        )
        journal_state: Literal["absent", "staging", "prepared", "committed"] = m.Field(
            description="Observed durable state, never a readiness or green receipt",
        )
        pending_roots: tuple[Path, ...] = m.Field(
            description="Actual recorded participant roots",
        )
        pending_destinations: tuple[str, ...] = m.Field(
            description="Journal-relative destination selectors",
        )
        pending_directories: tuple[str, ...] = m.Field(
            description="Journal-relative directory selectors",
        )
        pending_staging: tuple[Path, ...] = m.Field(
            description="Absolute recorded staging paths",
        )
        journal: (
            FlextInfraModelsCodegenTransactionModels.CodegenTransactionJournal | None
        ) = m.Field(
            default=None,
            exclude=True,
            description="Typed observed recovery authority",
        )
        snapshot: m.Cli.AtomicFileState = m.Field(
            exclude=True,
            description="Exact journal observation retained for revalidation",
        )

    class CodegenFileSessionPlan(FlextInfraModelsBase.FrozenArbitrary):
        """File-only transaction topology; contains no Mise artifact snapshot."""

        layout: Annotated[
            FlextInfraModelsCodegenToolchain.MiseToolchainWorkspaceLayout,
            m.Field(description="Locked explicit file participant topology"),
        ]

        @m.model_validator(mode="after")
        def _validate_file_only(self) -> Self:
            if self.layout.projects or not self.layout.file_participants:
                msg = "file-only session must contain only file capabilities"
                raise ValueError(msg)
            return self

    class CodegenTransactionSession(
        FlextInfraModelsBase.FrozenArbitrary, strict=True, validate_default=True
    ):
        """Immutable cursor for one live prepared generation transaction."""

        plan: Annotated[
            FlextInfraModelsCodegenToolchain.MiseToolchainWorkspacePlan
            | FlextInfraModelsCodegenTransactionModels.CodegenFileSessionPlan,
            m.Field(description="Locked generation plan and physical layout"),
        ]
        journal: Annotated[
            FlextInfraModelsCodegenTransactionModels.CodegenTransactionJournal,
            m.Field(description="Latest durable prepared journal payload"),
        ]
        journal_state: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Exact journal CAS state for the next transition"),
        ]
        written_files: Annotated[
            tuple[Path, ...],
            m.Field(description="Ordered destinations published by completed phases"),
        ] = ()
        published_files: t.VariadicTuple[
            FlextInfraModelsCodegenJournalModels.CodegenStagedFile
        ] = m.Field(
            default=(), exclude=True, description="Actual admitted states across phases"
        )
        retained_files: tuple[Path, ...] = m.Field(
            default=(),
            description="Authored destinations retained during per-file election",
        )
        issues: tuple[FlextInfraModelsCheck.Issue, ...] = m.Field(
            default=(),
            description="Publication failures retained across successful phases",
        )
        exception: BaseException | None = m.Field(
            default=None,
            exclude=True,
            description="First native publication cause",
        )

        @m.model_validator(mode="after")
        def _validate_cursor(self) -> Self:
            if self.journal.state != "prepared":
                msg = "active codegen transaction session must remain prepared"
                raise ValueError(msg)
            if self.plan.layout.transaction_id != self.journal.transaction_id:
                msg = "codegen session layout and journal transaction ids differ"
                raise ValueError(msg)
            return self

    class CodegenPhasePublicationPolicy(
        FlextInfraModelsBase.FrozenArbitrary, strict=True, validate_default=True
    ):
        """Caller-owned directories and native admission for one publication."""

        directories: tuple[Path, ...] = m.Field(
            description="Exact generated directories requested by the caller",
        )
        source_topology: tuple[m.Cli.AtomicDirectoryChainPlan, ...] = m.Field(
            default=(), description="Authenticated source directory ancestry"
        )
        scope_roots: tuple[Path, ...] = m.Field(
            default=(), description="Source membership roots for this publication"
        )
        source_scope: Path | None = m.Field(
            default=None,
            description="Selected source scope within the membership roots",
        )
        admission: FlextInfraModelsCodegenPipelineModels.CodegenPhaseOutcome | None = (
            m.Field(
                default=None,
                exclude=True,
                description="Exact prior batch admission when the caller captured it",
            )
        )
        staged_validator: (
            Callable[
                [
                    FlextInfraModelsCodegenTransactionModels.CodegenTransactionSession,
                    t.VariadicTuple[
                        FlextInfraModelsCodegenJournalModels.CodegenStagedFile
                    ],
                ],
                p.Result[
                    FlextInfraModelsCodegenTransactionModels.CodegenTransactionSession
                ],
            ]
            | None
        ) = m.Field(
            default=None,
            exclude=True,
            description="Real staged consumer required before publishing this batch",
        )


__all__: list[str] = ["FlextInfraModelsCodegenTransactionModels"]
