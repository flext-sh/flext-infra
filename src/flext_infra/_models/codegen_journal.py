"""Journal, recovery, and transaction models for the codegen pipeline."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u

from .. import t
from .codegen_toolchain import FlextInfraModelsCodegenToolchain


class FlextInfraModelsCodegenJournal:
    """Journal, recovery, and transaction models for the codegen pipeline."""

    class CodegenJournalProject(m.ArbitraryTypesModel):
        """One journal participant bound to its physical directory identity."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        selector: Annotated[
            t.NonEmptyStr, m.Field(description="Workspace-relative project selector")
        ]
        device: Annotated[
            int, m.Field(ge=0, strict=True, description="Project directory device")
        ]
        inode: Annotated[
            int, m.Field(gt=0, strict=True, description="Project directory inode")
        ]

        @u.field_validator("selector")
        @classmethod
        def _validate_selector(cls, value: str) -> str:
            relative = Path(value)
            if (
                relative.is_absolute()
                or relative.as_posix() != value
                or ".." in relative.parts
            ):
                msg = f"unsafe codegen project selector: {value}"
                raise ValueError(msg)
            return value

    class CodegenJournalDirectory(m.ArbitraryTypesModel):
        """One journal-authorized directory creation and its physical identity."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        phase: Annotated[
            t.NonEmptyStr,
            m.Field(description="Generation phase that owns the directory"),
        ]
        project: Annotated[
            t.NonEmptyStr,
            m.Field(description="Journal project selector owning the directory"),
        ]
        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Workspace-relative directory proven absent"),
        ]
        disposition: Annotated[
            Literal["temporary", "generated"],
            m.Field(description="Commit-time retention policy for the directory"),
        ]
        before: Annotated[
            m.Cli.AtomicDirectoryState | None,
            m.Field(description="Exact absent leaf and existing-parent binding"),
        ] = None
        created: Annotated[
            m.Cli.AtomicDirectoryState | None,
            m.Field(description="Exact physical identity returned by guarded creation"),
        ] = None
        manifest: Annotated[
            m.Cli.AtomicPhysicalTreeManifest | None,
            m.Field(description="Last durable authorized temporary-tree manifest"),
        ] = None

        @u.field_validator("path")
        @classmethod
        def _validate_path(cls, value: str) -> str:
            """Keep the durable authority lexical and inside the workspace."""
            relative = Path(value)
            if (
                relative.is_absolute()
                or relative.as_posix() != value
                or value in {"", "."}
                or ".." in relative.parts
            ):
                msg = f"unsafe codegen journal directory: {value}"
                raise ValueError(msg)
            return value

        @u.model_validator(mode="after")
        def _validate_disposition(self) -> Self:
            """Bind lifecycle metadata to one physical leaf path."""
            if (self.phase == "transaction") != (self.disposition == "temporary"):
                msg = "transaction phase and temporary disposition must coincide"
                raise ValueError(msg)
            if self.before is not None and self.before.exists:
                msg = "codegen directory preflight state must be absent"
                raise ValueError(msg)
            if self.created is not None and not self.created.exists:
                msg = "codegen directory created state must be present"
                raise ValueError(msg)
            if (
                self.before is not None
                and self.created is not None
                and self.before.path != self.created.path
            ):
                msg = "codegen directory states belong to different paths"
                raise ValueError(msg)
            if self.manifest is not None:
                created = self.created
                root = self.manifest.root
                if created is None or self.disposition != "temporary":
                    msg = "only a created temporary directory may own a tree manifest"
                    raise ValueError(msg)
                manifest_identity = (
                    root.path,
                    root.parent_device,
                    root.parent_inode,
                    root.mode,
                    root.device,
                    root.inode,
                    root.file_attributes,
                    root.reparse_tag,
                )
                created_identity = (
                    created.path,
                    created.parent_device,
                    created.parent_inode,
                    created.mode,
                    created.device,
                    created.inode,
                    created.file_attributes,
                    created.reparse_tag,
                )
                if manifest_identity != created_identity:
                    msg = "temporary-tree manifest differs from created directory"
                    raise ValueError(msg)
            return self

    class CodegenJournalSource(m.ArbitraryTypesModel):
        """One immutable source identity, including authenticated absence."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        phase: Annotated[
            t.NonEmptyStr, m.Field(description="Generation phase that consumed source")
        ]
        path: Annotated[Path, m.Field(description="Absolute authenticated source path")]
        parent_device: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Source parent device")
        ]
        parent_inode: Annotated[
            int | None, m.Field(gt=0, strict=True, description="Source parent inode")
        ]
        sha256: Annotated[
            str | None,
            m.Field(
                pattern=r"^[0-9a-f]{64}$",
                description="Exact source-byte SHA-256 identity",
            ),
        ]
        mode: Annotated[
            int | None,
            m.Field(
                ge=0, le=0o7777, strict=True, description="Exact source permission bits"
            ),
        ]
        device: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Source device identity")
        ]
        inode: Annotated[
            int | None, m.Field(gt=0, strict=True, description="Source inode identity")
        ]
        link_count: Annotated[
            Literal[1] | None, m.Field(description="Unique physical source link count")
        ]
        absent_parent: Annotated[
            m.Cli.AtomicDirectoryChainPlan | None,
            m.Field(
                description="Physical ancestor witness when the source parent is absent"
            ),
        ] = None
        file_attributes: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Host file attributes")
        ] = None
        reparse_tag: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Host reparse tag")
        ] = None

        @u.field_validator("path")
        @classmethod
        def _validate_source_path(cls, value: Path) -> Path:
            """Reject relative or lexically escaping source identities."""
            if not value.is_absolute() or ".." in value.parts:
                msg = f"unsafe generation source path: {value}"
                raise ValueError(msg)
            return value

        @u.model_validator(mode="after")
        def _validate_source_physical_state(self) -> Self:
            """Reject a persisted source identity that represents a reparse point."""
            physical = (
                self.sha256,
                self.mode,
                self.device,
                self.inode,
                self.link_count,
            )
            populated = tuple(value is not None for value in physical)
            if any(populated) != all(populated):
                msg = "generation source physical identity is incomplete"
                raise ValueError(msg)
            parent = (self.parent_device, self.parent_inode)
            if (parent[0] is None) != (parent[1] is None):
                msg = "generation source parent identity is incomplete"
                raise ValueError(msg)
            if self.parent_device is None:
                if any(populated) or self.absent_parent is None:
                    msg = "absent source parent requires an authenticated ancestor witness"
                    raise ValueError(msg)
                if (
                    self.absent_parent.target != self.path.parent
                    or not self.absent_parent.directories
                ):
                    msg = "source absence witness does not describe its missing parent"
                    raise ValueError(msg)
            elif self.absent_parent is not None:
                msg = "existing source parent cannot carry an absence witness"
                raise ValueError(msg)
            if not any(populated) and (
                self.file_attributes is not None or self.reparse_tag is not None
            ):
                msg = "absent generation source cannot carry host metadata"
                raise ValueError(msg)
            marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            if self.reparse_tag not in {None, 0} or (
                self.file_attributes is not None and bool(self.file_attributes & marker)
            ):
                msg = f"generation source is a reparse point: {self.path}"
                raise ValueError(msg)
            return self

    class CodegenJournalEntry(m.ArbitraryTypesModel):
        """Recoverable full before/after identity for one generated file."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        phase: Annotated[
            t.NonEmptyStr, m.Field(description="Generation phase owning this entry")
        ]
        project: Annotated[
            t.NonEmptyStr,
            m.Field(description="Journal project selector owning this entry"),
        ]
        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Workspace-relative live file destination"),
        ]
        desired_staging: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Workspace-relative staged replacement path"),
        ] = None
        original_exists: Annotated[
            bool,
            m.Field(
                strict=True, description="Whether the destination existed at preflight"
            ),
        ]
        original_parent_device: Annotated[
            int, m.Field(ge=0, strict=True, description="Original parent device")
        ]
        original_parent_inode: Annotated[
            int, m.Field(gt=0, strict=True, description="Original parent inode")
        ]
        original_backup: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Workspace-relative original-byte backup"),
        ] = None
        original_sha256: Annotated[
            str | None,
            m.Field(
                pattern=r"^[0-9a-f]{64}$",
                description="Exact original-byte SHA-256 identity when present",
            ),
        ] = None
        original_mode: Annotated[
            int | None,
            m.Field(
                ge=0,
                le=0o7777,
                strict=True,
                description="Exact original permission bits when present",
            ),
        ] = None
        original_device: Annotated[
            int | None,
            m.Field(ge=0, strict=True, description="Original device identity"),
        ] = None
        original_inode: Annotated[
            int | None,
            m.Field(gt=0, strict=True, description="Original inode identity"),
        ] = None
        original_link_count: Annotated[
            Literal[1] | None,
            m.Field(description="Original unique physical link count"),
        ] = None
        original_file_attributes: Annotated[
            int | None,
            m.Field(ge=0, strict=True, description="Original host attributes"),
        ] = None
        original_reparse_tag: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Original reparse tag")
        ] = None
        desired_exists: Annotated[
            bool, m.Field(strict=True, description="Whether publication leaves a file")
        ]
        desired_parent_device: Annotated[
            int, m.Field(ge=0, strict=True, description="Desired live parent device")
        ]
        desired_parent_inode: Annotated[
            int, m.Field(gt=0, strict=True, description="Desired live parent inode")
        ]
        desired_sha256: Annotated[
            str | None,
            m.Field(
                pattern=r"^[0-9a-f]{64}$",
                description="Exact desired-byte SHA-256 identity",
            ),
        ] = None
        desired_mode: Annotated[
            int | None,
            m.Field(
                ge=0, le=0o7777, strict=True, description="Desired permission bits"
            ),
        ] = None
        desired_device: Annotated[
            int | None,
            m.Field(ge=0, strict=True, description="Staged replacement device"),
        ] = None
        desired_inode: Annotated[
            int | None,
            m.Field(gt=0, strict=True, description="Staged replacement inode"),
        ] = None
        desired_link_count: Annotated[
            Literal[1] | None,
            m.Field(description="Staged replacement unique link count"),
        ] = None
        desired_file_attributes: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Staged host attributes")
        ] = None
        desired_reparse_tag: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Staged reparse tag")
        ] = None
        rollback_exists: Annotated[
            bool | None,
            m.Field(
                strict=True,
                description="Recovery target presence once rollback is durable",
            ),
        ] = None
        rollback_parent_device: Annotated[
            int | None,
            m.Field(ge=0, strict=True, description="Rollback live parent device"),
        ] = None
        rollback_parent_inode: Annotated[
            int | None,
            m.Field(gt=0, strict=True, description="Rollback live parent inode"),
        ] = None
        rollback_sha256: Annotated[
            str | None,
            m.Field(pattern=r"^[0-9a-f]{64}$", description="Rollback bytes identity"),
        ] = None
        rollback_mode: Annotated[
            int | None,
            m.Field(ge=0, le=0o7777, strict=True, description="Rollback mode"),
        ] = None
        rollback_device: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Rollback staged device")
        ] = None
        rollback_inode: Annotated[
            int | None, m.Field(gt=0, strict=True, description="Rollback staged inode")
        ] = None
        rollback_link_count: Annotated[
            Literal[1] | None, m.Field(description="Rollback staged unique link count")
        ] = None
        rollback_file_attributes: Annotated[
            int | None,
            m.Field(ge=0, strict=True, description="Rollback host attributes"),
        ] = None
        rollback_reparse_tag: Annotated[
            int | None, m.Field(ge=0, strict=True, description="Rollback reparse tag")
        ] = None
        rollback_staging: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Workspace-relative durable rollback candidate path"),
        ] = None

        @u.field_validator(
            "path", "original_backup", "desired_staging", "rollback_staging"
        )
        @classmethod
        def _validate_relative_file_path(cls, value: str | None) -> str | None:
            if value is None:
                return None
            relative = Path(value)
            if (
                relative.is_absolute()
                or relative.as_posix() != value
                or value in {"", "."}
                or ".." in relative.parts
            ):
                msg = f"unsafe codegen journal file path: {value}"
                raise ValueError(msg)
            return value

        @u.model_validator(mode="after")
        def _validate_original_tuple(self) -> Self:
            """Require complete recovery identity exactly when original existed."""
            original = (
                self.original_backup,
                self.original_sha256,
                self.original_mode,
                self.original_device,
                self.original_inode,
                self.original_link_count,
            )
            populated = tuple(value is not None for value in original)
            if (self.original_exists and not all(populated)) or (
                not self.original_exists and any(populated)
            ):
                msg = "Mise journal original recovery tuple is inconsistent"
                raise ValueError(msg)
            if not self.original_exists and (
                self.original_file_attributes is not None
                or self.original_reparse_tag is not None
            ):
                msg = "absent codegen original cannot contain host metadata"
                raise ValueError(msg)
            desired = (
                self.desired_sha256,
                self.desired_mode,
                self.desired_device,
                self.desired_inode,
                self.desired_link_count,
            )
            desired_populated = tuple(value is not None for value in desired)
            if (self.desired_exists and not all(desired_populated)) or (
                not self.desired_exists and any(desired_populated)
            ):
                msg = "codegen journal desired identity is inconsistent"
                raise ValueError(msg)
            if self.desired_exists != (self.desired_staging is not None):
                msg = "codegen journal desired staging path is inconsistent"
                raise ValueError(msg)
            if not self.desired_exists and (
                self.desired_file_attributes is not None
                or self.desired_reparse_tag is not None
            ):
                msg = "absent codegen desired state cannot contain host metadata"
                raise ValueError(msg)
            rollback = (
                self.rollback_sha256,
                self.rollback_mode,
                self.rollback_device,
                self.rollback_inode,
                self.rollback_link_count,
            )
            rollback_populated = tuple(value is not None for value in rollback)
            rollback_parent = (self.rollback_parent_device, self.rollback_parent_inode)
            parent_populated = tuple(value is not None for value in rollback_parent)
            if self.rollback_exists is None and (
                any(rollback_populated) or any(parent_populated)
            ):
                msg = "codegen journal rollback identity has no presence state"
                raise ValueError(msg)
            if self.rollback_exists is not None and not all(parent_populated):
                msg = "codegen journal rollback parent identity is incomplete"
                raise ValueError(msg)
            if self.rollback_exists is True and not all(rollback_populated):
                msg = "codegen journal rollback identity is incomplete"
                raise ValueError(msg)
            if (self.rollback_exists is True) != (self.rollback_staging is not None):
                msg = "codegen journal rollback staging path is inconsistent"
                raise ValueError(msg)
            if self.rollback_exists is False and any(rollback_populated):
                msg = "absent codegen rollback cannot contain file identity"
                raise ValueError(msg)
            if self.rollback_exists is False and (
                self.rollback_file_attributes is not None
                or self.rollback_reparse_tag is not None
            ):
                msg = "absent codegen rollback cannot contain host metadata"
                raise ValueError(msg)
            marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            physical = (
                (self.original_file_attributes, self.original_reparse_tag),
                (self.desired_file_attributes, self.desired_reparse_tag),
                (self.rollback_file_attributes, self.rollback_reparse_tag),
            )
            if any(
                reparse not in {None, 0}
                or (attributes is not None and bool(attributes & marker))
                for attributes, reparse in physical
            ):
                msg = f"codegen journal contains a reparse identity: {self.path}"
                raise ValueError(msg)
            return self

    class CodegenRecoveryAction(m.ArbitraryTypesModel):
        """One preclassified recovery decision with no live effect applied."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        entry: Annotated[
            FlextInfraModelsCodegenJournal.CodegenJournalEntry,
            m.Field(description="Journal entry owning the recovery decision"),
        ]
        current: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Exact live target state used for classification"),
        ]
        operation: Annotated[
            Literal["noop", "delete", "restore"],
            m.Field(description="Only authorized recovery effect for the target"),
        ]

    class CodegenTransactionJournal(m.ArbitraryTypesModel):
        """Persisted recovery contract for one workspace-wide generation."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        version: Annotated[
            Literal[8], m.Field(description="Exact journal schema version")
        ]
        transaction_id: Annotated[
            str,
            m.Field(
                pattern=r"^[0-9a-f]{32}$",
                description="Unpredictable generation transaction identity",
            ),
        ]
        scope_device: Annotated[
            int, m.Field(ge=0, strict=True, description="Scope directory device")
        ]
        scope_inode: Annotated[
            int, m.Field(gt=0, strict=True, description="Scope directory inode")
        ]
        state: Annotated[
            Literal["staging", "prepared", "recovering", "committed"],
            m.Field(description="Durable publication transition state"),
        ]
        projects: Annotated[
            t.VariadicTuple[FlextInfraModelsCodegenJournal.CodegenJournalProject],
            m.Field(description="Ordered project selectors owned by this transaction"),
        ]
        file_participants: Annotated[
            t.VariadicTuple[FlextInfraModelsCodegenToolchain.CodegenFileParticipant],
            m.Field(description="Exact physical file publication capabilities"),
        ] = ()
        sources: Annotated[
            t.VariadicTuple[FlextInfraModelsCodegenJournal.CodegenJournalSource],
            m.Field(description="Source identities used by staging"),
        ]
        directories: Annotated[
            t.VariadicTuple[FlextInfraModelsCodegenJournal.CodegenJournalDirectory],
            m.Field(description="Directories whose prior absence authorizes creation"),
        ]
        entries: Annotated[
            t.VariadicTuple[FlextInfraModelsCodegenJournal.CodegenJournalEntry],
            m.Field(description="Recoverable artifact transitions"),
        ]

        @u.model_validator(mode="after")
        def _validate_lifecycle(self) -> Self:
            """Bind staging and publication payloads to one safe project set."""
            selectors = tuple(
                project.selector
                for project in (*self.projects, *self.file_participants)
            )
            if not selectors:
                msg = "generation journal requires an explicit participant"
                raise ValueError(msg)
            if selectors[0] != "." and "." in selectors:
                msg = "Mise root selector must be first when present"
                raise ValueError(msg)
            if len(set(selectors)) != len(selectors):
                msg = "Mise journal project selectors must be unique"
                raise ValueError(msg)
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
            entry_paths = tuple(entry.path for entry in self.entries)
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
            recovery_declared = tuple(
                entry.rollback_exists is not None for entry in self.entries
            )
            if self.state == "recovering" and not all(recovery_declared):
                msg = "recovering codegen journal lacks rollback identities"
                raise ValueError(msg)
            if self.state != "recovering" and any(recovery_declared):
                msg = "non-recovering codegen journal contains rollback identities"
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsCodegenJournal"]
