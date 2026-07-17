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

    # mro-qc84 (fix-forward): protocol-of-model contracts for every detector
    # violation record (m.Infra.*Violation), consumed at runtime by the
    # detectors/refactor services. Generated to mirror the model fields.
    @runtime_checkable
    class ClassNestingViolation(p.BaseModel, Protocol):
        """Normalized class-nesting violation with rewrite metadata."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def rewrite_scope(self) -> str: ...

        @property
        def confidence(self) -> str: ...

        @property
        def class_name(self) -> str: ...

        @property
        def target_namespace(self) -> str: ...

    @runtime_checkable
    class ClassPlacementViolation(p.BaseModel, Protocol):
        """Class placement violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def base_class(self) -> str: ...

        @property
        def suggestion(self) -> str: ...

        @property
        def action(self) -> str: ...

        @property
        def fixable(self) -> bool: ...

        @property
        def target_facade(self) -> str: ...

        @property
        def family(self) -> str: ...

    @runtime_checkable
    class CompatibilityAliasViolation(p.BaseModel, Protocol):
        """Compatibility alias violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def alias_name(self) -> str: ...

        @property
        def target_name(self) -> str: ...

        @property
        def module_name(self) -> str: ...

    @runtime_checkable
    class CyclicImportViolation(p.BaseModel, Protocol):
        """Cyclic import violation."""

        @property
        def cycle(self) -> t.SequenceOf[str]: ...

        @property
        def files(self) -> t.SequenceOf[str]: ...

    @runtime_checkable
    class FutureAnnotationsViolation(p.BaseModel, Protocol):
        """Future annotations violation."""

        @property
        def file(self) -> str: ...

    @runtime_checkable
    class ImportAliasViolation(p.BaseModel, Protocol):
        """Import alias violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def current_import(self) -> str: ...

        @property
        def suggested_import(self) -> str: ...

    @runtime_checkable
    class InlineImportViolation(p.BaseModel, Protocol):
        """Inline or lazy import declared inside a function body."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def current_import(self) -> str: ...

        @property
        def detail(self) -> str: ...

        @property
        def module_name(self) -> str: ...

        @property
        def imported_symbols(self) -> t.StrSequence: ...

        @property
        def is_importlib(self) -> bool: ...

    @runtime_checkable
    class InternalImportViolation(p.BaseModel, Protocol):
        """Internal import violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def current_import(self) -> str: ...

        @property
        def detail(self) -> str: ...

    @runtime_checkable
    class LooseClassViolation(p.BaseModel, Protocol):
        """A detected loose-class naming violation with confidence."""

        @property
        def file(self) -> str: ...

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def class_name(self) -> str: ...

        @property
        def expected_prefix(self) -> str: ...

        @property
        def rule(self) -> str: ...

        @property
        def reason(self) -> str: ...

        @property
        def confidence(self) -> str: ...

        @property
        def score(self) -> float: ...

    @runtime_checkable
    class LooseObjectViolation(p.BaseModel, Protocol):
        """Loose object violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def kind(self) -> str: ...

        @property
        def suggestion(self) -> str: ...

    @runtime_checkable
    class LooseTestFunctionViolation(p.BaseModel, Protocol):
        """A module-level ``test_*`` function outside a ``Tests*`` class."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def suggestion(self) -> str: ...

    @runtime_checkable
    class MROCompletenessViolation(p.BaseModel, Protocol):
        """M r o completeness violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def family(self) -> str: ...

        @property
        def facade_class(self) -> str: ...

        @property
        def missing_base(self) -> str: ...

        @property
        def suggestion(self) -> str: ...

    @runtime_checkable
    class MROShapeViolation(p.BaseModel, Protocol):
        """MRO shape violation (ENFORCE-046/047/049/051)."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def class_name(self) -> str: ...

        @property
        def rule_id(self) -> str: ...

        @property
        def detail(self) -> str: ...

        @property
        def first_base(self) -> str: ...

        @property
        def expected_base(self) -> str: ...

        @property
        def fix_action(self) -> str: ...

        @property
        def fixable(self) -> bool: ...

    @runtime_checkable
    class ManualProtocolViolation(p.BaseModel, Protocol):
        """Manual protocol violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def suggestion(self) -> str: ...

    @runtime_checkable
    class ManualTypingAliasViolation(p.BaseModel, Protocol):
        """Manual typing alias violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def detail(self) -> str: ...

        @property
        def name(self) -> str: ...

    @runtime_checkable
    class NamespaceSourceViolation(p.BaseModel, Protocol):
        """Namespace source violation."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def alias(self) -> str: ...

        @property
        def current_source(self) -> str: ...

        @property
        def correct_source(self) -> str: ...

        @property
        def current_import(self) -> str: ...

        @property
        def suggested_import(self) -> str: ...

    @runtime_checkable
    class ParseFailureViolation(p.BaseModel, Protocol):
        """Parse failure violation."""

        @property
        def detail(self) -> str: ...

        @property
        def file(self) -> str: ...

        @property
        def stage(self) -> str: ...

        @property
        def error_type(self) -> str: ...

    @runtime_checkable
    class PatternSmellViolation(p.BaseModel, Protocol):
        """Generic rope-detected pattern smell (ENFORCE-026..033)."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def kind(self) -> str: ...

        @property
        def detail(self) -> str: ...

    @runtime_checkable
    class PrivateImportBypassViolation(p.BaseModel, Protocol):
        """Semantically proven package-root config/settings import bypass."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def current_import(self) -> str: ...

        @property
        def detail(self) -> str: ...

        @property
        def kind(self) -> str: ...

        @property
        def private_module(self) -> str: ...

        @property
        def imported_symbol(self) -> str: ...

        @property
        def bound_name(self) -> str: ...

        @property
        def target_file(self) -> str: ...

        @property
        def canonical_singleton(self) -> str: ...

        @property
        def owner_project(self) -> str: ...

        @property
        def surface(self) -> str: ...

        @property
        def type_checking_guarded(self) -> bool: ...

    @runtime_checkable
    class RuntimeAliasViolation(p.BaseModel, Protocol):
        """Runtime alias violation."""

        @property
        def detail(self) -> str: ...

        @property
        def line(self) -> int: ...

        @property
        def file(self) -> str: ...

        @property
        def kind(self) -> str: ...

        @property
        def alias(self) -> str: ...

    @runtime_checkable
    class SilentFailureViolation(p.BaseModel, Protocol):
        """Exception-handling construct that silences failures."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def file(self) -> str: ...

        @property
        def kind(self) -> str: ...

        @property
        def detail(self) -> str: ...

        @property
        def fix_action(self) -> str: ...


__all__: list[str] = ["FlextInfraProtocolsValidate"]
