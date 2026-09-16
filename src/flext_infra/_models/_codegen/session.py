"""Transaction session models for the codegen runtime domain."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u

from ... import t
from .. import FlextInfraConfigModels
from ..codegen_toolchain import FlextInfraModelsCodegenToolchain
from .journal import FlextInfraModelsCodegenJournal


class FlextInfraModelsCodegenSession:
    """Private codegen session model domain partial."""

    class CodegenFileSessionPlan(m.ArbitraryTypesModel):
        """File-only transaction topology; contains no Mise artifact snapshot."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        layout: Annotated[
            FlextInfraModelsCodegenToolchain.MiseToolchainWorkspaceLayout,
            m.Field(description="Locked explicit file participant topology"),
        ]

        @u.model_validator(mode="after")
        def _validate_file_only(self) -> Self:
            if self.layout.projects or not self.layout.file_participants:
                msg = "file-only session must contain only file capabilities"
                raise ValueError(msg)
            return self

    class CodegenTransactionSession(m.ArbitraryTypesModel):
        """Immutable cursor for one live prepared generation transaction."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        plan: Annotated[
            FlextInfraModelsCodegenToolchain.MiseToolchainWorkspacePlan
            | FlextInfraModelsCodegenSession.CodegenFileSessionPlan,
            m.Field(description="Locked generation plan and physical layout"),
        ]
        journal: Annotated[
            FlextInfraModelsCodegenJournal.CodegenTransactionJournal,
            m.Field(description="Latest durable prepared journal payload"),
        ]
        journal_state: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Exact journal CAS state for the next transition"),
        ]
        written_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="Ordered destinations published by completed phases"),
        ] = ()

        @u.model_validator(mode="after")
        def _validate_cursor(self) -> Self:
            if self.journal.state != "prepared":
                msg = "active codegen transaction session must remain prepared"
                raise ValueError(msg)
            if self.plan.layout.transaction_id != self.journal.transaction_id:
                msg = "codegen session layout and journal transaction ids differ"
                raise ValueError(msg)
            return self

    class CodegenPhaseAnalysis(m.ArbitraryTypesModel):
        """Immutable planner receipt reused for publication verification."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True, extra="forbid")

        phase: Annotated[
            Literal["docs", "lazy-init"],
            m.Field(description="Generation phase that produced this receipt"),
        ]
        files: Annotated[
            t.VariadicTuple[FlextInfraConfigModels.CodegenFilePlan],
            m.Field(description="Ordered desired publication states"),
        ]
        inputs: Annotated[
            t.VariadicTuple[m.Cli.AtomicFileState],
            m.Field(description="Ordered complete authenticated planner inputs"),
        ]

        @u.model_validator(mode="after")
        def _validate_unique_paths(self) -> Self:
            """Reject ambiguous receipts with competing path authorities."""
            file_paths = tuple(file.path for file in self.files)
            if len(set(file_paths)) != len(file_paths):
                msg = "codegen phase receipt destination paths must be unique"
                raise ValueError(msg)
            input_paths = tuple(state.path for state in self.inputs)
            if len(set(input_paths)) != len(input_paths):
                msg = "codegen phase receipt input paths must be unique"
                raise ValueError(msg)
            return self
