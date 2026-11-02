# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_infra import c, t


class FlextInfraProtocolsScan:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class ModScanPublication(Protocol):
        """Structural data contract projected from the owning model."""

        command: c.Infra.ModScanCommand
        scope: Sequence[str]
        relative_path: Path = ...
        repositories: Sequence[str] = ...
        rule_ids: Sequence[str] = ...

    @runtime_checkable
    class ScanViolation(Protocol):
        """Structural data contract projected from the owning model."""

        message: str
        severity: str
        rule_id: str | None = ...

    @runtime_checkable
    class ModNativeRecord(Protocol):
        """Structural data contract projected from the owning model."""

        offset: int
        length: int
        sha256: str

    @runtime_checkable
    class ModReplacementOffsets(Protocol):
        """Structural data contract projected from the owning model."""

        start: int
        end: int

    @runtime_checkable
    class ModOccurrence(Protocol):
        """Structural data contract projected from the owning model."""

        rule_file: t.NonEmptyStr
        rule_id: t.NonEmptyStr
        repository: t.NonEmptyStr
        catalog_digest: str | None = ...
        message: str | None = ...
        module_absence: bool = ...
        file: Path
        source_owner: Literal["authored", "generator"] = ...
        source_state: m.Cli.AtomicFileState | None = ...
        range: t.JsonMapping
        text: str
        replacement: str | None = ...
        actionable: bool
        classification: c.Infra.ModScanFindingClass
        replacement_offsets: FlextInfraProtocolsScan.ModReplacementOffsets | None = ...

    @runtime_checkable
    class ModScanFinding(Protocol):
        """Structural data contract projected from the owning model."""

        rule_file: t.NonEmptyStr
        rule_id: t.NonEmptyStr
        repository: t.NonEmptyStr
        catalog_digest: str | None = ...
        message: str | None = ...
        module_absence: bool = ...
        file: Path
        source_owner: Literal["authored", "generator"] = ...
        source_state: m.Cli.AtomicFileState | None = ...
        range: t.JsonMapping
        text: str
        replacement: str | None = ...
        actionable: bool
        classification: c.Infra.ModScanFindingClass
        replacement_offsets: FlextInfraProtocolsScan.ModReplacementOffsets | None = ...
        severity: Literal["error", "warning", "info", "hint"] = ...
        origin: Literal[
            c.Infra.ModFindingOrigin.AST_GREP, c.Infra.ModFindingOrigin.OWNED_PATH
        ] = ...
        native_record: FlextInfraProtocolsScan.ModNativeRecord = ...
        native_receipt: m.Cli.AtomicFileReceipt | None = ...

    @runtime_checkable
    class ModScanFindingReference(Protocol):
        """Structural data contract projected from the owning model."""

        rule_file: t.NonEmptyStr
        rule_id: t.NonEmptyStr
        repository: t.NonEmptyStr
        catalog_digest: str | None = ...
        message: str | None = ...
        module_absence: bool = ...
        file: Path
        source_owner: Literal["authored", "generator"] = ...
        source_state: m.Cli.AtomicFileState | None = ...
        range: t.JsonMapping
        text: str
        replacement: str | None = ...
        actionable: bool
        classification: c.Infra.ModScanFindingClass
        replacement_offsets: FlextInfraProtocolsScan.ModReplacementOffsets | None = ...
        severity: Literal["error", "warning", "info", "hint"] = ...
        origin: Literal[
            c.Infra.ModFindingOrigin.AST_GREP, c.Infra.ModFindingOrigin.OWNED_PATH
        ] = ...
        native_record: FlextInfraProtocolsScan.ModNativeRecord = ...
        native_receipt: m.Cli.AtomicFileReceipt | None = ...
        source_path: Path | None
        native_artifact: int

    @runtime_checkable
    class ModModuleQuarantine(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        cause: str
        error_code: str | None = ...

    @runtime_checkable
    class ModQuarantineExclusion(Protocol):
        """Structural data contract projected from the owning model."""

        phase: str
        modules: tuple[Path, ...]
        paths: tuple[Path, ...]

    @runtime_checkable
    class ModTextRule(Protocol):
        """Structural data contract projected from the owning model."""

        rule_id: t.NonEmptyStr
        description: str = ...
        include: Sequence[str] = ...
        exclude: Sequence[str] = ...
        distributions: Sequence[str] = ...
        find: t.NonEmptyStr
        replace: str = ...
        flags: Sequence[str] = ...
        capture_equals: Mapping[str, str] = ...
        expected: int | None = ...

    @runtime_checkable
    class ModTextFinding(Protocol):
        """Structural data contract projected from the owning model."""

        rule_id: t.NonEmptyStr
        file: Path
        line: t.NonNegativeInt
        text: str
        replacement: str

    @runtime_checkable
    class ModTextReport(Protocol):
        """Structural data contract projected from the owning model."""

        findings: t.NonNegativeInt
        actionable: t.NonNegativeInt
        files: frozenset[Path]
        entries: tuple[FlextInfraProtocolsScan.ModTextFinding, ...]

    @runtime_checkable
    class ModScanEvidenceReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        sha256: t.NonEmptyStr
        evidence: FlextInfraProtocolsScan.ModScanEvidence


__all__: list[str] = [
    "FlextInfraProtocolsScan",
]
