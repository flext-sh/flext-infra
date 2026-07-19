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

    from flext_infra import p as ip, t


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

    # mro-qc84 (fix-forward): protocols-of-models closure for the remaining
    # runtime-referenced infra models (tooling config, reports, render
    # contexts) so codegen conform/deps/github/grpc contracts resolve.
    @runtime_checkable
    class AccessorMigrationRule(p.BaseModel, Protocol):
        """Declarative symbol-rename rule for accessor migration."""

        @property
        def source_name(self) -> str: ...

        @property
        def replacement_name(self) -> str: ...

        @property
        def reason(self) -> str: ...

        @property
        def origin(self) -> str: ...

    @runtime_checkable
    class AuditScopeParams(p.BaseModel, Protocol):
        """Bundled parameters for a single audit scope run."""

        @property
        def check(self) -> str: ...

        @property
        def strict(self) -> bool: ...

        @property
        def docstring_min(self) -> float | None: ...

        @property
        def budgets(self) -> t.JsonValue | None: ...

    @runtime_checkable
    class CheckProjectTarget(p.BaseModel, Protocol):
        """Resolved project target for workspace gate execution."""

        @property
        def name(self) -> str: ...

        @property
        def path(self) -> Path: ...

    @runtime_checkable
    class CodespellConfig(Protocol):
        """Codespell settings loaded from YAML."""

        @property
        def check_filenames(self) -> bool: ...

        @property
        def ignore_words_list(self) -> str: ...

    @runtime_checkable
    class CoverageConfig(Protocol):
        """Coverage baseline settings loaded from YAML."""

        @property
        def source(self) -> t.JsonValue: ...

        @property
        def fail_under(self) -> FlextInfraProtocolsValidate.CoverageFailUnderConfig: ...

        @property
        def show_missing(self) -> bool: ...

        @property
        def skip_covered(self) -> bool: ...

        @property
        def precision(self) -> int: ...

        @property
        def exclude_also(self) -> t.JsonValue: ...

        @property
        def omit(self) -> t.JsonValue: ...

    @runtime_checkable
    class CoverageFailUnderConfig(Protocol):
        """Coverage fail-under thresholds by layer."""

        @property
        def core(self) -> int: ...

        @property
        def domain(self) -> int: ...

        @property
        def platform(self) -> int: ...

        @property
        def integration(self) -> int: ...

        @property
        def app(self) -> int: ...

    @runtime_checkable
    class DeptryConfig(Protocol):
        """Deptry namespace and dependency-group policy."""

        @property
        def known_first_party(self) -> t.SequenceOf[str]: ...

        @property
        def pep621_dev_dependency_groups(self) -> t.SequenceOf[str]: ...

    @runtime_checkable
    class DocScope(p.BaseModel, Protocol):
        """Documentation scope targeting a project or workspace root."""

        @property
        def name(self) -> str: ...

        @property
        def path(self) -> t.JsonValue: ...

        @property
        def report_dir(self) -> t.JsonValue: ...

        @property
        def project_class(self) -> str: ...

        @property
        def package_name(self) -> str: ...

    @runtime_checkable
    class DocsPhaseItemModel(p.BaseModel, Protocol):
        """Unified item payload for docs phase reports."""

        @property
        def phase(self) -> str: ...

        @property
        def file(self) -> str: ...

        @property
        def issue_type(self) -> str: ...

        @property
        def severity(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def links(self) -> int: ...

        @property
        def toc(self) -> int: ...

        @property
        def codeblocks(self) -> int: ...

        @property
        def path(self) -> str: ...

        @property
        def written(self) -> bool: ...

    @runtime_checkable
    class DocsPhaseReport(p.BaseModel, Protocol):
        """Unified report payload for docs phases (declaration only)."""

        @property
        def phase(self) -> str: ...

        @property
        def scope(self) -> str: ...

        @property
        def result(self) -> str: ...

        @property
        def reason(self) -> str: ...

        @property
        def message(self) -> str: ...

        @property
        def site_dir(self) -> str: ...

        @property
        def checks(self) -> t.StrSequence: ...

        @property
        def strict(self) -> bool: ...

        @property
        def passed(self) -> bool: ...

        @property
        def changed_files(self) -> int: ...

        @property
        def applied(self) -> bool: ...

        @property
        def generated(self) -> int: ...

        @property
        def source(self) -> str: ...

        @property
        def missing_adr_skills(self) -> t.StrSequence: ...

        @property
        def todo_written(self) -> bool: ...

        @property
        def items(self) -> FlextInfraProtocolsValidate.DocsPhaseItemModel: ...

    @runtime_checkable
    class FacadeStatus(p.BaseModel, Protocol):
        """Facade status."""

        @property
        def family(self) -> str: ...

        @property
        def exists(self) -> bool: ...

        @property
        def class_name(self) -> str: ...

        @property
        def file(self) -> str: ...

        @property
        def symbol_count(self) -> int: ...

    @runtime_checkable
    class GithubPullRequestOutcome(p.BaseModel, Protocol):
        """Outcome of a single pull-request command on one repository."""

        @property
        def display(self) -> str: ...

        @property
        def status(self) -> str: ...

        @property
        def elapsed(self) -> int: ...

        @property
        def exit_code(self) -> int: ...

        @property
        def log_path(self) -> str | None: ...

    @runtime_checkable
    class GithubPullRequestWorkspaceReport(p.BaseModel, Protocol):
        """Aggregated report for workspace-wide pull-request execution."""

        @property
        def total(self) -> int: ...

        @property
        def success(self) -> int: ...

        @property
        def fail(self) -> int: ...

        @property
        def outcomes(self) -> FlextInfraProtocolsValidate.GithubPullRequestOutcome: ...

    @runtime_checkable
    class GithubWorkflowLintOutcome(p.BaseModel, Protocol):
        """Outcome payload for workflow lint execution."""

        @property
        def status(self) -> str: ...

        @property
        def reason(self) -> str | None: ...

        @property
        def detail(self) -> str | None: ...

        @property
        def exit_code(self) -> int | None: ...

        @property
        def stdout(self) -> str | None: ...

        @property
        def stderr(self) -> str | None: ...

    @runtime_checkable
    class GithubWorkflowSyncOperation(p.BaseModel, Protocol):
        """Describe one workflow synchronization operation."""

        @property
        def project(self) -> str: ...

        @property
        def path(self) -> str: ...

        @property
        def action(self) -> str: ...

        @property
        def reason(self) -> str: ...

    @runtime_checkable
    class GithubWorkflowSyncReport(p.BaseModel, Protocol):
        """Structured report for a workflow synchronization request."""

        @property
        def mode(self) -> str: ...

        @property
        def summary(self) -> t.JsonMapping: ...

        @property
        def operations(
            self,
        ) -> FlextInfraProtocolsValidate.GithubWorkflowSyncOperation: ...

    @runtime_checkable
    class GrpcGeneratedArtifact(p.BaseModel, Protocol):
        """One normalized compiler-owned Python file."""

        @property
        def target(self) -> t.JsonValue: ...

        @property
        def content(self) -> str: ...

    @runtime_checkable
    class GrpcProjectRender(p.BaseModel, Protocol):
        """Complete compiler artifact set for one project."""

        @property
        def schemas(self) -> int: ...

        @property
        def artifacts(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.GrpcGeneratedArtifact]: ...

    @runtime_checkable
    class HatchConfig(Protocol):
        """Hatch metadata policy."""

        @property
        def allow_direct_references(self) -> bool: ...

        @property
        def packaged_data_dirs(self) -> t.JsonValue: ...

    @runtime_checkable
    class InventoryReport(p.BaseModel, Protocol):
        """Summary of written inventory report artifacts."""

        @property
        def total_scripts(self) -> int: ...

        @property
        def reports_written(self) -> t.JsonValue: ...

    @runtime_checkable
    class MROFileMigration(p.BaseModel, Protocol):
        """Migration summary for one transformed file."""

        @property
        def file(self) -> str: ...

        @property
        def module(self) -> str: ...

        @property
        def moved_symbols(self) -> t.JsonValue: ...

        @property
        def created_classes(self) -> t.JsonValue: ...

    @runtime_checkable
    class MROMigrationReport(p.BaseModel, Protocol):
        """End-to-end report for migrate-to-mro command execution."""

        @property
        def checkpoint_ref(self) -> str: ...

        @property
        def workspace(self) -> str: ...

        @property
        def target(self) -> str: ...

        @property
        def selected_projects(self) -> t.JsonValue: ...

        @property
        def dry_run(self) -> bool: ...

        @property
        def validation_mode(self) -> str: ...

        @property
        def files_scanned(self) -> int: ...

        @property
        def files_with_candidates(self) -> int: ...

        @property
        def migrations(self) -> FlextInfraProtocolsValidate.MROFileMigration: ...

        @property
        def rewrites(self) -> FlextInfraProtocolsValidate.MRORewriteResult: ...

        @property
        def remaining_violations(self) -> int: ...

        @property
        def mro_failures(self) -> int: ...

        @property
        def scan_duration_seconds(self) -> float: ...

        @property
        def rewrite_duration_seconds(self) -> float: ...

        @property
        def validation_duration_seconds(self) -> float: ...

        @property
        def total_duration_seconds(self) -> float: ...

        @property
        def warnings(self) -> t.JsonValue: ...

        @property
        def errors(self) -> t.JsonValue: ...

    @runtime_checkable
    class MRORewriteResult(p.BaseModel, Protocol):
        """Reference rewrite summary for one file."""

        @property
        def file(self) -> str: ...

        @property
        def replacements(self) -> int: ...

    @runtime_checkable
    class MypyConfig(p.BaseModel, Protocol):
        """Mypy baseline settings loaded from YAML."""

        @property
        def plugins(self) -> t.StrSequence: ...

        @property
        def exclude(self) -> str: ...

        @property
        def disabled_error_codes(self) -> t.StrMapping: ...

        @property
        def boolean_settings(self) -> t.MappingKV[str, bool]: ...

        @property
        def string_settings(self) -> t.StrMapping: ...

        @property
        def overrides(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.MypyOverrideConfig]: ...

    @runtime_checkable
    class MypyOverrideConfig(p.BaseModel, Protocol):
        """Single [[tool.mypy.overrides]] entry."""

        @property
        def modules(self) -> t.StrSequence: ...

        @property
        def disable_error_codes(self) -> t.StrSequence: ...

        @property
        def justification(self) -> str: ...

    @runtime_checkable
    class ProjectEnforcementReport(p.BaseModel, Protocol):
        """Project enforcement report."""

        @property
        def project(self) -> str: ...

        @property
        def project_root(self) -> str: ...

        @property
        def facade_statuses(self) -> FlextInfraProtocolsValidate.FacadeStatus: ...

        @property
        def loose_objects(self) -> FlextInfraProtocolsValidate.LooseObjectViolation: ...

        @property
        def import_violations(
            self,
        ) -> FlextInfraProtocolsValidate.ImportAliasViolation: ...

        @property
        def namespace_source_violations(
            self,
        ) -> FlextInfraProtocolsValidate.NamespaceSourceViolation: ...

        @property
        def internal_import_violations(
            self,
        ) -> FlextInfraProtocolsValidate.InternalImportViolation: ...

        @property
        def private_import_bypass_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PrivateImportBypassViolation: ...

        @property
        def manual_protocol_violations(
            self,
        ) -> FlextInfraProtocolsValidate.ManualProtocolViolation: ...

        @property
        def cyclic_imports(
            self,
        ) -> FlextInfraProtocolsValidate.CyclicImportViolation: ...

        @property
        def runtime_alias_violations(
            self,
        ) -> FlextInfraProtocolsValidate.RuntimeAliasViolation: ...

        @property
        def future_violations(
            self,
        ) -> FlextInfraProtocolsValidate.FutureAnnotationsViolation: ...

        @property
        def manual_typing_violations(
            self,
        ) -> FlextInfraProtocolsValidate.ManualTypingAliasViolation: ...

        @property
        def compatibility_alias_violations(
            self,
        ) -> FlextInfraProtocolsValidate.CompatibilityAliasViolation: ...

        @property
        def foreign_canonical_alias_violations(
            self,
        ) -> FlextInfraProtocolsValidate.CompatibilityAliasViolation: ...

        @property
        def class_placement_violations(
            self,
        ) -> FlextInfraProtocolsValidate.ClassPlacementViolation: ...

        @property
        def mro_completeness_violations(
            self,
        ) -> FlextInfraProtocolsValidate.MROCompletenessViolation: ...

        @property
        def bare_except_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def print_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def breakpoint_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def open_encoding_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def dict_annotation_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def typing_dict_attr_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def typing_dict_import_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def hardcoded_version_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def type_ignore_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def noqa_violations(
            self,
        ) -> FlextInfraProtocolsValidate.PatternSmellViolation: ...

        @property
        def inline_import_violations(
            self,
        ) -> FlextInfraProtocolsValidate.InlineImportViolation: ...

        @property
        def silent_failure_violations(
            self,
        ) -> FlextInfraProtocolsValidate.SilentFailureViolation: ...

        @property
        def parse_failures(
            self,
        ) -> FlextInfraProtocolsValidate.ParseFailureViolation: ...

        @property
        def files_scanned(self) -> int: ...

    @runtime_checkable
    class ProjectRenderContext(p.BaseModel, Protocol):
        """Complete typed input consumed by the universal project templates."""

        @property
        def scaffold(self) -> FlextInfraProtocolsValidate.ScaffoldSpec: ...

        @property
        def dependency_profile(
            self,
        ) -> FlextInfraProtocolsValidate.ScaffoldDependencyProfileSpec: ...

        @property
        def make(self) -> ip.Infra.MakeSpec: ...

        @property
        def tooling_runtime(
            self,
        ) -> FlextInfraProtocolsValidate.ToolingRuntimeContext: ...

        @property
        def dist(self) -> str: ...

        @property
        def const_name(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def packaged_data_dirs(self) -> t.StrSequence: ...

        @property
        def class_stem(self) -> str: ...

        @property
        def ns(self) -> str: ...

        @property
        def ns_attr(self) -> str: ...

        @property
        def alias(self) -> str: ...

        @property
        def env_prefix(self) -> str: ...

        @property
        def upstream(self) -> str: ...

        @property
        def description(self) -> str: ...

        @property
        def version(self) -> str: ...

        @property
        def license(self) -> str: ...

        @property
        def python_version(self) -> str: ...

        @property
        def python_toolchain_version(self) -> str: ...

        @property
        def python_required_version(self) -> str: ...

        @property
        def uv_version(self) -> str: ...

        @property
        def uv_required_version(self) -> str: ...

        @property
        def uv_link_mode(self) -> str: ...

        @property
        def author_name(self) -> str: ...

        @property
        def author_email(self) -> str: ...

        @property
        def repository(self) -> str: ...

        @property
        def homepage(self) -> str: ...

        @property
        def documentation(self) -> str: ...

        @property
        def flext_git_base_url(self) -> str: ...

        @property
        def flext_git_branch(self) -> str: ...

        @property
        def make_profile(self) -> t.JsonValue: ...

        @property
        def workspace_root_rel(self) -> str: ...

        @property
        def repository_provider(self) -> str: ...

        @property
        def repository_git_url(self) -> str: ...

        @property
        def repository_branch(self) -> str: ...

        @property
        def year(self) -> int: ...

        @property
        def project_resources(self) -> t.SequenceOf[ip.Infra.ResourceSpec]: ...

        @property
        def workspace_members(self) -> t.SequenceOf[str]: ...

        @property
        def workspace_repositories(self) -> t.SequenceOf[ip.Infra.RepositoryRef]: ...

        @property
        def workspace_content_only(self) -> t.SequenceOf[ip.Infra.RepositoryRef]: ...

        @property
        def workspace_exclusions(self) -> t.SequenceOf[p.BaseModel]: ...

    @runtime_checkable
    class ProjectTypeOverrideConfig(Protocol):
        """Per-project-type override settings."""

        @property
        def pyright(self) -> t.JsonValue: ...

    @runtime_checkable
    class ProjectTypeOverridesConfig(Protocol):
        """Project-type-specific override matrix from ``config/tooling.yaml``."""

        @property
        def core(self) -> FlextInfraProtocolsValidate.ProjectTypeOverrideConfig: ...

        @property
        def domain(self) -> FlextInfraProtocolsValidate.ProjectTypeOverrideConfig: ...

        @property
        def platform(self) -> FlextInfraProtocolsValidate.ProjectTypeOverrideConfig: ...

        @property
        def integration(
            self,
        ) -> FlextInfraProtocolsValidate.ProjectTypeOverrideConfig: ...

        @property
        def app(self) -> FlextInfraProtocolsValidate.ProjectTypeOverrideConfig: ...

    @runtime_checkable
    class PydanticMypyConfig(p.BaseModel, Protocol):
        """Pydantic mypy plugin settings loaded from YAML."""

        @property
        def init_forbid_extra(self) -> bool: ...

        @property
        def init_typed(self) -> bool: ...

        @property
        def warn_required_dynamic_aliases(self) -> bool: ...

        @property
        def warn_untyped_fields(self) -> bool: ...

    @runtime_checkable
    class PyprojectDocumentState(p.BaseModel, Protocol):
        """Centralized normalized TOML state reused across deps workflows."""

        pyproject_path: Path
        original_rendered: str
        rendered: str
        payload: t.MutableJsonMapping

    @runtime_checkable
    class PyreflyConfig(Protocol):
        """Pyrefly strict settings loaded from YAML."""

        @property
        def python_version(self) -> str: ...

        @property
        def ignore_errors_in_generated_code(self) -> bool: ...

        @property
        def disable_project_excludes_heuristics(self) -> bool: ...

        @property
        def use_ignore_files(self) -> bool: ...

        @property
        def strict_errors(self) -> t.JsonValue: ...

        @property
        def disabled_errors(self) -> t.JsonValue: ...

        @property
        def project_exclude_globs(self) -> t.JsonValue: ...

        @property
        def path_rules(self) -> t.JsonValue: ...

    @runtime_checkable
    class PyrightConfig(Protocol):
        """Pyright strict settings loaded from YAML."""

        @property
        def strict_settings(self) -> t.JsonValue: ...

        @property
        def extended_settings(self) -> t.JsonValue: ...

        @property
        def lazy_import_suppressions(self) -> t.JsonValue: ...

        @property
        def global_suppression_rationales(self) -> t.JsonValue: ...

        @property
        def source_env_suppressions(self) -> t.JsonValue: ...

        @property
        def test_like_env_suppressions(self) -> t.JsonValue: ...

        @property
        def path_rules(self) -> t.JsonValue: ...

    @runtime_checkable
    class PytestConfig(p.BaseModel, Protocol):
        """Pytest baseline settings loaded from YAML."""

        @property
        def min_version(self) -> str: ...

        @property
        def python_classes(self) -> t.SequenceOf[str]: ...

        @property
        def python_files(self) -> t.SequenceOf[str]: ...

        @property
        def test_paths(self) -> t.SequenceOf[str]: ...

        @property
        def filter_warnings(self) -> t.SequenceOf[str]: ...

        @property
        def standard_markers(self) -> t.StrSequence: ...

        @property
        def standard_addopts(self) -> t.StrSequence: ...

    @runtime_checkable
    class PytestDiagnostics(p.BaseModel, Protocol):
        """Extracted diagnostics summary from junit XML and pytest logs."""

        @property
        def failed_count(self) -> int: ...

        @property
        def error_count(self) -> int: ...

        @property
        def warning_count(self) -> int: ...

        @property
        def skipped_count(self) -> int: ...

        @property
        def failed_cases(self) -> t.StrSequence: ...

        @property
        def error_traces(self) -> t.StrSequence: ...

        @property
        def warning_lines(self) -> t.StrSequence: ...

        @property
        def skip_cases(self) -> t.StrSequence: ...

        @property
        def slow_entries(self) -> t.StrSequence: ...

    @runtime_checkable
    class RuffConfig(Protocol):
        """Ruff top-level settings loaded from YAML."""

        @property
        def exclude(self) -> t.StrSequence: ...

        @property
        def namespace_packages(self) -> t.StrSequence: ...

        @property
        def fix(self) -> bool: ...

        @property
        def line_length(self) -> int: ...

        @property
        def preview(self) -> bool: ...

        @property
        def respect_gitignore(self) -> bool: ...

        @property
        def show_fixes(self) -> bool: ...

        @property
        def src(self) -> t.StrSequence: ...

        @property
        def target_version(self) -> str: ...

        @property
        def format(self) -> FlextInfraProtocolsValidate.RuffFormatConfig: ...

        @property
        def lint(self) -> FlextInfraProtocolsValidate.RuffLintConfig: ...

    @runtime_checkable
    class RuffFormatConfig(Protocol):
        """Ruff format settings loaded from YAML."""

        @property
        def docstring_code_format(self) -> bool: ...

        @property
        def indent_style(self) -> str: ...

        @property
        def line_ending(self) -> str: ...

        @property
        def quote_style(self) -> str: ...

        @property
        def skip_magic_trailing_comma(self) -> bool: ...

    @runtime_checkable
    class RuffIsortConfig(Protocol):
        """Ruff isort settings loaded from YAML."""

        @property
        def combine_as_imports(self) -> bool: ...

        @property
        def force_single_line(self) -> bool: ...

        @property
        def split_on_trailing_comma(self) -> bool: ...

    @runtime_checkable
    class RuffLintConfig(Protocol):
        """Ruff lint settings loaded from YAML."""

        @property
        def select(self) -> t.StrSequence: ...

        @property
        def ignore(self) -> t.StrSequence: ...

        @property
        def ignored_rule_rationales(self) -> t.StrMapping: ...

        @property
        def banned_api(self) -> t.StrMapping: ...

        @property
        def isort(self) -> FlextInfraProtocolsValidate.RuffIsortConfig: ...

        @property
        def pydoclint(self) -> FlextInfraProtocolsValidate.RuffPydoclintConfig: ...

        @property
        def pydocstyle(self) -> FlextInfraProtocolsValidate.RuffPydocstyleConfig: ...

        @property
        def per_file_ignores(self) -> t.StrSequenceMapping: ...

    @runtime_checkable
    class RuffPydoclintConfig(Protocol):
        """Ruff pydoclint settings loaded from YAML."""

        @property
        def ignore_one_line_docstrings(self) -> bool: ...

    @runtime_checkable
    class RuffPydocstyleConfig(Protocol):
        """Ruff pydocstyle settings loaded from YAML."""

        @property
        def convention(self) -> t.JsonValue: ...

    @runtime_checkable
    class ScaffoldDependencyProfileSpec(p.BaseModel, Protocol):
        """Dependencies selected by the declared upstream FLEXT facade."""

        @property
        def upstream(self) -> str: ...

        @property
        def runtime(self) -> t.SequenceOf[str]: ...

        @property
        def codegen(self) -> t.SequenceOf[str]: ...

        @property
        def dev(self) -> t.SequenceOf[str]: ...

    @runtime_checkable
    class ScaffoldGitignoreSectionSpec(p.BaseModel, Protocol):
        """One configured section of the generated Git ignore policy."""

        @property
        def name(self) -> str: ...

        @property
        def patterns(self) -> t.SequenceOf[str]: ...

    @runtime_checkable
    class ScaffoldPingExampleSpec(p.BaseModel, Protocol):
        """Values for the functional ping example created only by codegen new."""

        @property
        def command_name(self) -> str: ...

        @property
        def help_text(self) -> str: ...

        @property
        def success_message(self) -> str: ...

        @property
        def enabled_default(self) -> bool: ...

        @property
        def reply(self) -> str: ...

        @property
        def disabled_reply(self) -> str: ...

    @runtime_checkable
    class ScaffoldProjectSpec(p.BaseModel, Protocol):
        """Project metadata policy for newly scaffolded distributions."""

        @property
        def readme(self) -> str: ...

        @property
        def supported_licenses(self) -> t.SequenceOf[str]: ...

        @property
        def classifiers(self) -> t.SequenceOf[str]: ...

        @property
        def keywords(self) -> t.SequenceOf[str]: ...

        @property
        def dependency_profiles(
            self,
        ) -> t.SequenceOf[
            FlextInfraProtocolsValidate.ScaffoldDependencyProfileSpec
        ]: ...

    @runtime_checkable
    class ScaffoldSpec(p.BaseModel, Protocol):
        """Complete typed policy consumed only by new-project templates."""

        @property
        def build(self) -> ip.Infra.ScaffoldBuildSpec: ...

        @property
        def project(self) -> FlextInfraProtocolsValidate.ScaffoldProjectSpec: ...

        @property
        def resources(self) -> t.SequenceOf[ip.Infra.ResourceSpec]: ...

        @property
        def ping_example(
            self,
        ) -> FlextInfraProtocolsValidate.ScaffoldPingExampleSpec: ...

        @property
        def gitignore_sections(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.ScaffoldGitignoreSectionSpec]: ...

    @runtime_checkable
    class StubAnalysisReport(p.BaseModel, Protocol):
        """Structured typed-dependency analysis result for a project."""

        @property
        def project(self) -> str: ...

        @property
        def mypy_hints(self) -> t.JsonValue: ...

        @property
        def internal_missing(self) -> t.JsonValue: ...

        @property
        def unresolved_missing(self) -> t.JsonValue: ...

        @property
        def total_missing(self) -> int: ...

    @runtime_checkable
    class TestTreeRulesConfig(p.BaseModel, Protocol):
        """Config-driven parameters for the loose-test-function detector."""

        @property
        def version(self) -> str: ...

        @property
        def test_dir_globs(self) -> t.SequenceOf[str]: ...

        @property
        def test_fn_prefix(self) -> str: ...

        @property
        def required_class_prefix(self) -> str: ...

    @runtime_checkable
    class TomlsortConfig(Protocol):
        """tomlsort baseline settings loaded from YAML."""

        @property
        def all(self) -> bool: ...

        @property
        def in_place(self) -> bool: ...

        @property
        def sort_first(self) -> t.JsonValue: ...

    @runtime_checkable
    class ToolConfigDocument(p.BaseModel, Protocol):
        """Root schema for canonical ``config/tooling.yaml`` policy data."""

        @property
        def tools(self) -> FlextInfraProtocolsValidate.ToolConfigTools: ...

    @runtime_checkable
    class ToolConfigTools(p.BaseModel, Protocol):
        """Tool map loaded from YAML."""

        @property
        def codespell(self) -> FlextInfraProtocolsValidate.CodespellConfig: ...

        @property
        def deptry(self) -> FlextInfraProtocolsValidate.DeptryConfig: ...

        @property
        def hatch(self) -> FlextInfraProtocolsValidate.HatchConfig: ...

        @property
        def ruff(self) -> FlextInfraProtocolsValidate.RuffConfig: ...

        @property
        def mypy(self) -> FlextInfraProtocolsValidate.MypyConfig: ...

        @property
        def pydantic_mypy(self) -> FlextInfraProtocolsValidate.PydanticMypyConfig: ...

        @property
        def pyright(self) -> FlextInfraProtocolsValidate.PyrightConfig: ...

        @property
        def pyrefly(self) -> FlextInfraProtocolsValidate.PyreflyConfig: ...

        @property
        def pytest(self) -> FlextInfraProtocolsValidate.PytestConfig: ...

        @property
        def tomlsort(self) -> FlextInfraProtocolsValidate.TomlsortConfig: ...

        @property
        def vulture(self) -> FlextInfraProtocolsValidate.VultureConfig: ...

        @property
        def yamlfix(self) -> FlextInfraProtocolsValidate.YamlfixConfig: ...

        @property
        def coverage(self) -> FlextInfraProtocolsValidate.CoverageConfig: ...

    @runtime_checkable
    class ToolingPyrightEnvironment(p.BaseModel, Protocol):
        """One resolved Pyright execution environment."""

        @property
        def root(self) -> str: ...

        @property
        def extra_paths(self) -> t.SequenceOf[str]: ...

        @property
        def settings(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.ToolingScalarSetting]: ...

    @runtime_checkable
    class ToolingRuntimeContext(p.BaseModel, Protocol):
        """Resolved project/workspace values consumed by the complete template."""

        @property
        def project_kind(self) -> str: ...

        @property
        def coverage_fail_under(self) -> int: ...

        @property
        def first_party(self) -> t.SequenceOf[str]: ...

        @property
        def mypy_path(self) -> t.SequenceOf[str]: ...

        @property
        def pyrefly_interpreter_path(self) -> str: ...

        @property
        def pyrefly_search_path(self) -> t.SequenceOf[str]: ...

        @property
        def pyrefly_project_includes(self) -> t.SequenceOf[str]: ...

        @property
        def pyright_exclude(self) -> t.SequenceOf[str]: ...

        @property
        def pyright_ignore(self) -> t.SequenceOf[str]: ...

        @property
        def pyright_include(self) -> t.SequenceOf[str]: ...

        @property
        def pyright_extra_paths(self) -> t.SequenceOf[str]: ...

        @property
        def pyright_venv(self) -> str: ...

        @property
        def pyright_venv_path(self) -> str: ...

        @property
        def pyright_settings(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.ToolingScalarSetting]: ...

        @property
        def pyright_execution_environments(
            self,
        ) -> t.SequenceOf[FlextInfraProtocolsValidate.ToolingPyrightEnvironment]: ...

        @property
        def ruff_src(self) -> t.SequenceOf[str]: ...

        @property
        def ruff_ignore(self) -> t.SequenceOf[str]: ...

    @runtime_checkable
    class ToolingScalarSetting(p.BaseModel, Protocol):
        """One validated scalar setting rendered into an explicit TOML table."""

        @property
        def name(self) -> str: ...

        @property
        def value(self) -> str: ...

    @runtime_checkable
    class VultureConfig(p.BaseModel, Protocol):
        """Vulture production-reachability policy loaded from YAML."""

        @property
        def exclude(self) -> t.SequenceOf[str]: ...

        @property
        def min_confidence(self) -> int: ...

        @property
        def paths(self) -> t.SequenceOf[str]: ...

        @property
        def verbose(self) -> bool: ...

    @runtime_checkable
    class WorkspaceEnforcementReport(p.BaseModel, Protocol):
        """Workspace enforcement report."""

        @property
        def workspace(self) -> str: ...

        @property
        def projects(self) -> FlextInfraProtocolsValidate.ProjectEnforcementReport: ...

        @property
        def total_facades_missing(self) -> int: ...

        @property
        def total_loose_objects(self) -> int: ...

        @property
        def total_import_violations(self) -> int: ...

        @property
        def total_namespace_source_violations(self) -> int: ...

        @property
        def total_internal_import_violations(self) -> int: ...

        @property
        def total_private_import_bypass_violations(self) -> int: ...

        @property
        def total_manual_protocol_violations(self) -> int: ...

        @property
        def total_cyclic_imports(self) -> int: ...

        @property
        def total_runtime_alias_violations(self) -> int: ...

        @property
        def total_future_violations(self) -> int: ...

        @property
        def total_manual_typing_violations(self) -> int: ...

        @property
        def total_compatibility_alias_violations(self) -> int: ...

        @property
        def total_foreign_canonical_alias_violations(self) -> int: ...

        @property
        def total_class_placement_violations(self) -> int: ...

        @property
        def total_mro_completeness_violations(self) -> int: ...

        @property
        def total_bare_except_violations(self) -> int: ...

        @property
        def total_print_violations(self) -> int: ...

        @property
        def total_breakpoint_violations(self) -> int: ...

        @property
        def total_open_encoding_violations(self) -> int: ...

        @property
        def total_dict_annotation_violations(self) -> int: ...

        @property
        def total_typing_dict_attr_violations(self) -> int: ...

        @property
        def total_typing_dict_import_violations(self) -> int: ...

        @property
        def total_hardcoded_version_violations(self) -> int: ...

        @property
        def total_type_ignore_violations(self) -> int: ...

        @property
        def total_noqa_violations(self) -> int: ...

        @property
        def total_inline_import_violations(self) -> int: ...

        @property
        def total_silent_failure_violations(self) -> int: ...

        @property
        def total_parse_failures(self) -> int: ...

        @property
        def total_files_scanned(self) -> int: ...

    @runtime_checkable
    class WorkspaceExclusionSpec(Protocol):
        """One explicitly rejected workspace path and its reason."""

        @property
        def path(self) -> t.JsonValue: ...

        @property
        def reason(self) -> str: ...

    @runtime_checkable
    class YamlfixConfig(Protocol):
        """yamlfix baseline settings loaded from YAML."""

        @property
        def line_length(self) -> int: ...

        @property
        def preserve_quotes(self) -> bool: ...

        @property
        def whitelines(self) -> int: ...

        @property
        def section_whitelines(self) -> int: ...

        @property
        def explicit_start(self) -> bool: ...


__all__: list[str] = ["FlextInfraProtocolsValidate"]
