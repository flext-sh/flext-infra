"""Protocols for validated infrastructure reports.

Structural contracts for report models consumed across validation, scanning,
dependency, and namespace-census services. Field-level protocols keep concrete
Pydantic models behind the model facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import p

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


@runtime_checkable
class FlextInfraProtocolsValidate(Protocol):
    """Validated report contracts published through ``p.Infra``."""

    # Keep report shapes in this private facet; the public protocol is MRO-only.

    @runtime_checkable
    class ValidationReport(p.BaseModel, Protocol):
        """Outcome of one validation pass: status, violations, and summary."""

        @property
        def passed(self) -> bool:
            """Whether the validation passed."""
            ...

        @property
        def violations(self) -> t.StrSequence:
            """Collected validation violations."""
            ...

        @property
        def summary(self) -> str:
            """Human-readable validation summary."""
            ...

    @runtime_checkable
    class ScanViolation(p.BaseModel, Protocol):
        """One violation emitted by a file scanner."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def message(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def rule_id(self) -> str | None: ...

    @runtime_checkable
    class ScanResult(p.BaseModel, Protocol):
        """Validated result emitted by one file scanner."""

        @property
        def file_path(self) -> Path: ...

        @property
        def violations(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.ScanViolation]: ...

        @property
        def detector_name(self) -> str: ...

    @runtime_checkable
    class DependencyLimitsInfo(p.BaseModel, Protocol):
        """Resolved dependency-limits metadata."""

        @property
        def python_version(self) -> str | None: ...

        @property
        def limits_path(self) -> str: ...

    @runtime_checkable
    class PipCheckReport(p.BaseModel, Protocol):
        """Status and output lines from pip check."""

        @property
        def ok(self) -> bool: ...

        @property
        def lines(self) -> t.StrSequence: ...

    @runtime_checkable
    class TypingsReport(p.BaseModel, Protocol):
        """Required, current, and delta typing-package report."""

        @property
        def required_packages(self) -> t.StrSequence: ...

        @property
        def hinted(self) -> t.StrSequence: ...

        @property
        def missing_modules(self) -> t.StrSequence: ...

        @property
        def current(self) -> t.StrSequence: ...

        @property
        def to_add(self) -> t.StrSequence: ...

        @property
        def to_remove(self) -> t.StrSequence: ...

        @property
        def limits_applied(self) -> bool: ...

        @property
        def python_version(self) -> str | None: ...

    @runtime_checkable
    class CensusViolation(p.BaseModel, Protocol):
        """One namespace violation emitted by the census service."""

        @property
        def line(self) -> t.NonNegativeInt: ...

        @property
        def module(self) -> t.NonEmptyStr: ...

        @property
        def rule(self) -> t.NonEmptyStr: ...

        @property
        def message(self) -> t.NonEmptyStr: ...

        @property
        def fixable(self) -> bool: ...

    @runtime_checkable
    class CensusReport(p.BaseModel, Protocol):
        """Aggregated namespace census for one project."""

        @property
        def project(self) -> t.NonEmptyStr: ...

        @property
        def violations(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.CensusViolation]: ...

        @property
        def total(self) -> t.NonNegativeInt: ...

        @property
        def fixable(self) -> t.NonNegativeInt: ...


__all__: list[str] = ["FlextInfraProtocolsValidate"]
