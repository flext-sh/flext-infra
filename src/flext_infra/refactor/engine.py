"""Refactor engine and CLI for flext_infra.refactor."""

from __future__ import annotations

import argparse
import fnmatch
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
from libcst.metadata import MetadataWrapper
from pydantic import TypeAdapter, ValidationError

from flext_infra import (
    CONTAINER_DICT_SEQ_ADAPTER,
    INFRA_MAPPING_ADAPTER,
    STR_MAPPING_ADAPTER,
    FlextInfraClassNestingRefactorRule,
    FlextInfraGenericTransformerRule,
    FlextInfraRefactorClassReconstructor,
    FlextInfraRefactorEnsureFutureAnnotationsRule,
    FlextInfraRefactorImportModernizerRule,
    FlextInfraRefactorLegacyRemovalRule,
    FlextInfraRefactorMROClassMigrationRule,
    FlextInfraRefactorMRORemover,
    FlextInfraRefactorPatternCorrectionsRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorRuleDefinitionValidator,
    FlextInfraRefactorRuleLoader,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorSignaturePropagator,
    FlextInfraRefactorSymbolPropagator,
    FlextInfraRefactorTypingUnifier,
    FlextInfraRefactorViolationAnalyzer,
    FlextInfraTransformerTier0ImportFixer,
    FlextInfraTypingAnnotationReplacer,
    c,
    m,
    r,
    t,
    u,
)

_SIG_MIGRATION_SEQ_ADAPTER: TypeAdapter[Sequence[m.Infra.SignatureMigration]] = (
    TypeAdapter(Sequence[m.Infra.SignatureMigration])
)


class FlextInfraRefactorMRORedundancyChecker(FlextInfraGenericTransformerRule):
    """Detect and fix nested classes inheriting from their parent namespace."""

    TRANSFORMER_CLASS: type[cst.CSTTransformer] = FlextInfraRefactorMRORemover


class FlextInfraRefactorTypingUnificationRule(FlextInfraRefactorRule):
    """Unify duplicate type alias definitions into canonical t.* contracts."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        return self._apply_transformer(
            FlextInfraRefactorTypingUnifier(
                canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
                file_path=_file_path,
            ),
            tree,
        )


class FlextInfraRefactorTypingAnnotationFixRule(FlextInfraRefactorRule):
    """Replace legacy typing annotations with canonical t.* contracts."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        fix_action = u.Infra.get_str_key(
            self.config, c.Infra.ReportKeys.FIX_ACTION, lower=True
        )
        if fix_action == "replace_object_annotations":
            return self._apply_transformer(
                FlextInfraTypingAnnotationReplacer(),
                tree,
            )
        return (tree, [])


class FlextInfraRefactorTier0ImportFixRule(FlextInfraRefactorRule):
    """Enforce tier-0 import conventions via CST transformation.

    Inlined from rules/tier0_import_fix.py — config extraction + direct
    transformer instantiation.
    """

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, Sequence[str]]:
        if _file_path is None:
            return (tree, [])
        analyzer = FlextInfraTransformerTier0ImportFixer.Analyzer(
            file_path=_file_path,
            tier0_modules=self._tier0_modules(),
            core_aliases=self._core_aliases(),
        )
        tree.visit(analyzer)
        analysis = analyzer.build_analysis()
        if not analysis.has_violations:
            return (tree, [])

        project_root = u.Infra.discover_project_root_from_file(_file_path)
        core_package = (
            u.Infra.discover_core_package(project_root)
            if project_root
            else self._core_package()
        )

        fixer = FlextInfraTransformerTier0ImportFixer.Transformer(
            analysis=analysis,
            alias_to_submodule=self._alias_to_submodule(),
            core_package=core_package,
        )
        updated = tree.visit(fixer)
        return (updated, fixer.changes)

    def _tier0_modules(self) -> tuple[str, ...]:
        value = self.config.get("tier0_modules", [])
        if not isinstance(value, list):
            return ("constants.py", "typings.py", "protocols.py")
        return tuple(str(item) for item in value)

    def _core_aliases(self) -> tuple[str, ...]:
        value = self.config.get("core_aliases", [])
        if not isinstance(value, list):
            return tuple(c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES)
        return tuple(str(item) for item in value)

    def _core_package(self) -> str:
        return str(self.config.get("core_package", "flext_core"))

    def _alias_to_submodule(self) -> t.StrMapping:
        value = self.config.get("alias_to_submodule", {})
        if not u.is_mapping(value):
            return {}
        return {str(key): str(item) for key, item in value.items()}


class FlextInfraRefactorSymbolPropagationRule(FlextInfraRefactorRule):
    """Apply declarative module/symbol renames for workspace-wide propagation.

    Inlined from rules/symbol_propagation.py — config extraction + direct
    FlextInfraRefactorSymbolPropagator usage.
    """

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        typed_cfg: Mapping[str, t.Infra.InfraValue] = (
            INFRA_MAPPING_ADAPTER.validate_python(self.config)
        )
        target_modules_raw = typed_cfg.get("target_modules", [])
        module_renames_raw = typed_cfg.get("module_renames", {})
        symbol_renames_raw = typed_cfg.get("import_symbol_renames", {})
        target_modules = set(u.Infra.string_list(target_modules_raw))
        try:
            module_renames: Mapping[str, str] = STR_MAPPING_ADAPTER.validate_python(
                module_renames_raw,
            )
        except ValidationError:
            module_renames = {}
        try:
            symbol_renames: Mapping[str, str] = STR_MAPPING_ADAPTER.validate_python(
                symbol_renames_raw,
            )
        except ValidationError:
            symbol_renames = {}
        if not target_modules and (not module_renames) and (not symbol_renames):
            return (tree, [])
        transformer = FlextInfraRefactorSymbolPropagator(
            target_modules=target_modules,
            module_renames=module_renames,
            import_symbol_renames=symbol_renames,
        )
        return (tree.visit(transformer), transformer.changes)


class FlextInfraRefactorSignaturePropagationRule(FlextInfraRefactorRule):
    """Apply declarative signature migrations in a generic, workspace-safe way.

    Inlined from rules/symbol_propagation.py — config extraction + direct
    FlextInfraRefactorSignaturePropagator usage.
    """

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        migrations_raw = self.config.get("signature_migrations", [])
        try:
            parsed: Sequence[m.Infra.SignatureMigration] = (
                _SIG_MIGRATION_SEQ_ADAPTER.validate_python(migrations_raw)
            )
        except ValidationError:
            return (tree, [])
        migrations = [item for item in parsed if item.enabled]
        if not migrations:
            return (tree, [])
        transformer = FlextInfraRefactorSignaturePropagator(migrations=migrations)
        wrapper = MetadataWrapper(tree)
        return (wrapper.visit(transformer), transformer.changes)


class FlextInfraRefactorClassReconstructorRule(FlextInfraRefactorRule):
    """Apply class method ordering reconstruction to matching class nodes.

    Inlined from rules/class_reconstructor.py — config extraction + direct
    FlextInfraRefactorClassReconstructor usage.
    """

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Apply method reordering transformer when order config is available."""
        order_config_raw = self.config.get("method_order") or self.config.get(
            "order",
            [],
        )
        try:
            order_config: Sequence[t.Infra.ContainerDict] = (
                CONTAINER_DICT_SEQ_ADAPTER.validate_python(order_config_raw)
            )
        except ValidationError:
            return (tree, [])
        if not order_config:
            return (tree, [])
        return self._apply_transformer(
            FlextInfraRefactorClassReconstructor(order_config=order_config),
            tree,
        )


class FlextInfraRefactorEngine:
    """Engine de refatoracao que orquestra regras declarativas."""

    _RULE_ACTION_REGISTRY: ClassVar[
        Sequence[tuple[frozenset[str], type[FlextInfraRefactorRule]]]
    ] = [
        (
            c.Infra.FUTURE_FIX_ACTIONS | c.Infra.FUTURE_CHECKS,
            FlextInfraRefactorEnsureFutureAnnotationsRule,
        ),
        (c.Infra.LEGACY_FIX_ACTIONS, FlextInfraRefactorLegacyRemovalRule),
        (c.Infra.IMPORT_FIX_ACTIONS, FlextInfraRefactorImportModernizerRule),
        (c.Infra.CLASS_FIX_ACTIONS, FlextInfraRefactorClassReconstructorRule),
        (c.Infra.PATTERN_FIX_ACTIONS, FlextInfraRefactorPatternCorrectionsRule),
        (c.Infra.TYPE_ALIAS_FIX_ACTIONS, FlextInfraRefactorTypingUnificationRule),
        (c.Infra.TYPING_FIX_ACTIONS, FlextInfraRefactorTypingAnnotationFixRule),
        (c.Infra.TIER0_FIX_ACTIONS, FlextInfraRefactorTier0ImportFixRule),
        (
            frozenset({"migrate_to_class_mro"}),
            FlextInfraRefactorMROClassMigrationRule,
        ),
        (
            frozenset({"propagate_signature_migrations"}),
            FlextInfraRefactorSignaturePropagationRule,
        ),
        (c.Infra.PROPAGATION_FIX_ACTIONS, FlextInfraRefactorSymbolPropagationRule),
        (c.Infra.MRO_FIX_ACTIONS, FlextInfraRefactorMRORedundancyChecker),
    ]

    _RULE_ID_FALLBACKS: ClassVar[
        Sequence[tuple[frozenset[str], type[FlextInfraRefactorRule]]]
    ] = [
        (
            frozenset({"ensure-future", "future-annotations"}),
            FlextInfraRefactorEnsureFutureAnnotationsRule,
        ),
        (
            frozenset({"legacy", "alias", "deprecated", "wrapper", "bypass"}),
            FlextInfraRefactorLegacyRemovalRule,
        ),
        (frozenset({"import", "modernize"}), FlextInfraRefactorImportModernizerRule),
        (
            frozenset({"class", "reorder", "method"}),
            FlextInfraRefactorClassReconstructorRule,
        ),
        (
            frozenset({"redundant-cast", "dict-to-mapping", "container-invariance"}),
            FlextInfraRefactorPatternCorrectionsRule,
        ),
        (
            frozenset({"migrate-to-class-mro"}),
            FlextInfraRefactorMROClassMigrationRule,
        ),
        (frozenset({"mro"}), FlextInfraRefactorMRORedundancyChecker),
        (
            frozenset({"propagate", "symbol-rename", "rename"}),
            FlextInfraRefactorSymbolPropagationRule,
        ),
    ]

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize engine state and config file path."""
        self.config_path = config_path or self._default_config_path()
        config_map: Mapping[str, t.Infra.InfraValue] = {}
        self.config: t.Infra.InfraValue = config_map
        self.rules: MutableSequence[FlextInfraRefactorRule] = []
        self.file_rules: MutableSequence[FlextInfraClassNestingRefactorRule] = []
        self.rule_filters: MutableSequence[str] = []
        self.rule_loader = FlextInfraRefactorRuleLoader(self.config_path)
        self.rule_validator = FlextInfraRefactorRuleDefinitionValidator()
        self.safety_manager = FlextInfraRefactorSafetyManager()

    @staticmethod
    def _error_result(
        file_path: Path,
        error: str,
    ) -> m.Infra.Result:
        """Build a failure result with no modifications."""
        return m.Infra.Result(
            file_path=file_path,
            success=False,
            modified=False,
            error=error,
            changes=[],
            refactored_code=None,
        )

    @staticmethod
    def _skip_result(file_path: Path) -> m.Infra.Result:
        """Build a success result for skipped non-Python files."""
        return m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=False,
            changes=["Skipped non-Python file"],
            refactored_code=None,
        )

    def _try_safety_stash(
        self,
        target_path: Path,
        *,
        apply_safety: bool,
        dry_run: bool,
    ) -> t.Infra.Pair[str, Sequence[m.Infra.Result] | None]:
        """Attempt to create a safety stash before transformations.

        Returns (stash_ref, None) on success or ("", error_results) on failure.
        """
        if not apply_safety or dry_run:
            return "", None
        stash_ref_result = self._prepare_safety_stash(target_path)
        if stash_ref_result.is_failure:
            error_msg = stash_ref_result.error or "pre-transformation stash failed"
            return "", [self._error_result(target_path, error_msg)]
        return stash_ref_result.value, None

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """Build the CLI argument parser."""
        parser = argparse.ArgumentParser(
            description="Flext Refactor Engine - Declarative code transformation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        mode_group = parser.add_mutually_exclusive_group(required=True)
        _ = mode_group.add_argument("--project", "-p", type=Path)
        _ = mode_group.add_argument("--workspace", "-w", type=Path)
        _ = mode_group.add_argument("--file", "-f", type=Path)
        _ = mode_group.add_argument("--files", nargs="+", type=Path)
        _ = mode_group.add_argument("--list-rules", "-l", action="store_true")
        _ = parser.add_argument("--rules", "-r", type=str)
        _ = parser.add_argument("--pattern", default=c.Infra.Extensions.PYTHON_GLOB)
        _ = parser.add_argument("--dry-run", "-n", action="store_true")
        _ = parser.add_argument("--show-diff", "-d", action="store_true")
        _ = parser.add_argument("--impact-map-output", type=Path)
        _ = parser.add_argument("--analyze-violations", action="store_true")
        _ = parser.add_argument("--analysis-output", type=Path)
        _ = parser.add_argument("--config", "-c", type=Path)
        return parser

    @staticmethod
    def _init_engine(
        args: argparse.Namespace,
    ) -> tuple[FlextInfraRefactorEngine, int] | tuple[FlextInfraRefactorEngine, None]:
        """Create engine, load config and rules. Returns (engine, error_code) or (engine, None)."""
        engine = FlextInfraRefactorEngine(config_path=args.config)
        config_result = engine.load_config()
        if not config_result.is_success:
            u.Infra.refactor_error(f"Config error: {config_result.error}")
            return engine, 1
        if args.rules:
            rule_filters = [
                item.strip() for item in args.rules.split(",") if item.strip()
            ]
            engine.set_rule_filters(rule_filters)
        rules_result = engine.load_rules()
        if not rules_result.is_success:
            u.Infra.refactor_error(f"Rules error: {rules_result.error}")
            return engine, 1
        return engine, None

    @staticmethod
    def main() -> int:
        """Run the refactor CLI entrypoint and exit with the status code."""
        args = FlextInfraRefactorEngine._build_parser().parse_args()
        engine, init_error = FlextInfraRefactorEngine._init_engine(args)
        if init_error is not None:
            return init_error
        if args.list_rules:
            u.Infra.print_rules_table(engine.list_rules())
            return 0
        return engine.run_cli_mode(args)

    def run_cli_mode(self, args: argparse.Namespace) -> int:
        """Dispatch to analyze-violations or refactor based on CLI args."""
        if args.analyze_violations:
            return self._run_analyze_violations(args)
        return self._run_refactor(args)

    def _run_analyze_violations(self, args: argparse.Namespace) -> int:
        """Execute the --analyze-violations branch of the CLI."""
        files_to_analyze = self._collect_files_for_analysis(args)
        if files_to_analyze is None:
            return 1
        analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(files_to_analyze)
        u.Infra.print_violation_summary(analysis)
        if args.analysis_output is not None:
            _ = u.Infra.write_json(
                args.analysis_output,
                analysis.model_dump(mode="json"),
                ensure_ascii=True,
            )
            u.Infra.refactor_info(
                f"Analysis report written: {args.analysis_output}",
            )
        return 0

    def _collect_files_for_analysis(
        self,
        args: argparse.Namespace,
    ) -> MutableSequence[Path] | None:
        """Collect files for violation analysis. Returns None on error."""
        if args.project:
            return self._collect_project_files_for_analysis(args)
        if args.workspace:
            return list(
                self.collect_workspace_files(args.workspace, pattern=args.pattern),
            )
        return self._collect_explicit_files(args)

    def _collect_project_files_for_analysis(
        self,
        args: argparse.Namespace,
    ) -> MutableSequence[Path] | None:
        """Collect project files for violation analysis. Returns None on error."""
        return self._collect_project_files(args.project, pattern=args.pattern)

    @staticmethod
    def _collect_explicit_files(
        args: argparse.Namespace,
    ) -> MutableSequence[Path] | None:
        """Resolve --file or --files args to a path list. Returns None on error."""
        if args.file:
            if not args.file.exists():
                u.Infra.refactor_error(f"File not found: {args.file}")
                return None
            return [args.file]
        if args.files:
            return [item for item in args.files if item.exists()]
        return []

    def _collect_project_files(
        self,
        project_path: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> MutableSequence[Path] | None:
        """Iterate and filter Python files under a project. Returns None on error."""
        scan_dirs = frozenset(
            self.rule_loader.extract_project_scan_dirs(self.config),
        )
        iter_result = u.Infra.iter_python_files(
            workspace_root=project_path,
            project_roots=[project_path],
            include_tests=c.Infra.Directories.TESTS in scan_dirs,
            include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
            include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
            src_dirs=scan_dirs or None,
        )
        if iter_result.is_failure:
            u.Infra.refactor_error(
                iter_result.error or f"File iteration failed for {project_path}",
            )
            return None
        ignore_items, extension_items = self.rule_loader.extract_engine_file_filters(
            self.config,
        )
        return list(
            self._filter_files(
                iter_result.value,
                base_path=project_path,
                pattern=pattern,
                ignore_patterns={str(item) for item in ignore_items},
                allowed_extensions={str(item) for item in extension_items},
            ),
        )

    def _run_refactor(self, args: argparse.Namespace) -> int:
        """Execute the refactoring branch of the CLI."""
        results = self._collect_refactor_results(args)
        if results is None:
            return 1
        u.Infra.print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = u.Infra.write_impact_map(results, args.impact_map_output)
        failed = u.count(results, lambda item: not item.success)
        return 0 if failed == 0 else 1

    def _collect_refactor_results(
        self,
        args: argparse.Namespace,
    ) -> MutableSequence[m.Infra.Result] | None:
        """Collect refactoring results based on CLI mode. Returns None on error."""
        if args.project:
            return list(
                self.refactor_project(
                    args.project,
                    dry_run=args.dry_run,
                    pattern=args.pattern,
                ),
            )
        if args.workspace:
            return list(
                self.refactor_workspace(
                    args.workspace,
                    dry_run=args.dry_run,
                    pattern=args.pattern,
                ),
            )
        return self._refactor_explicit_files(args)

    def _refactor_explicit_files(
        self,
        args: argparse.Namespace,
    ) -> MutableSequence[m.Infra.Result] | None:
        """Refactor --file or --files from CLI args. Returns None on error."""
        if args.file:
            return self._refactor_single_file(args)
        if args.files:
            existing = [item for item in args.files if item.exists()]
            missing = [item for item in args.files if not item.exists()]
            for file_path in missing:
                u.Infra.refactor_error(f"File not found: {file_path}")
            return list(self.refactor_files(existing, dry_run=args.dry_run))
        return []

    def _refactor_single_file(
        self,
        args: argparse.Namespace,
    ) -> MutableSequence[m.Infra.Result] | None:
        """Refactor a single file from CLI args. Returns None if file not found."""
        if not args.file.exists():
            u.Infra.refactor_error(f"File not found: {args.file}")
            return None
        original_code = args.file.read_text(encoding=c.Infra.Encoding.DEFAULT)
        result_single = self.refactor_file(args.file, dry_run=args.dry_run)
        if args.show_diff and result_single.modified:
            refactored_code = result_single.refactored_code or original_code
            u.Infra.print_diff(original_code, refactored_code, args.file)
        return [result_single]

    @staticmethod
    def _matches_pattern(file: Path, base_path: Path, pattern: str) -> bool:
        """Return True when file matches the glob pattern."""
        rel = str(file.relative_to(base_path))
        return fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(file.name, pattern)

    @staticmethod
    def _is_ignored(file: Path, base_path: Path, ignore_patterns: set[str]) -> bool:
        """Return True when file or any parent dir matches ignore patterns."""
        if file.name in ignore_patterns:
            return True
        rel_path = file.relative_to(base_path)
        if any(part in ignore_patterns for part in rel_path.parts):
            return True
        return any(fnmatch.fnmatch(str(rel_path), ip) for ip in ignore_patterns)

    @staticmethod
    def _filter_files(
        candidates: Sequence[Path],
        *,
        base_path: Path,
        pattern: str,
        ignore_patterns: set[str],
        allowed_extensions: set[str],
    ) -> Sequence[Path]:
        """Filter candidate files by pattern, extensions, and ignore rules."""
        return [
            f
            for f in candidates
            if FlextInfraRefactorEngine._matches_pattern(f, base_path, pattern)
            and (not allowed_extensions or f.suffix in allowed_extensions)
            and not FlextInfraRefactorEngine._is_ignored(f, base_path, ignore_patterns)
        ]

    def collect_workspace_files(
        self,
        workspace_root: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> Sequence[Path]:
        """Collect all candidate files under workspace projects."""
        root = workspace_root.resolve()
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        project_paths = u.Infra.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        ignore_items, extension_items = self.rule_loader.extract_engine_file_filters(
            self.config,
        )
        ignore_patterns = {str(item) for item in ignore_items}
        allowed_extensions = {str(item) for item in extension_items}
        all_files: MutableSequence[Path] = []
        for project in project_paths:
            iter_result = u.Infra.iter_python_files(
                workspace_root=root,
                project_roots=[project],
                include_tests=c.Infra.Directories.TESTS in scan_dirs,
                include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
                include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
                src_dirs=scan_dirs or None,
            )
            if iter_result.is_failure:
                u.Infra.refactor_error(
                    iter_result.error or f"File iteration failed for {project}",
                )
                continue
            all_files.extend(
                self._filter_files(
                    iter_result.value,
                    base_path=project,
                    pattern=pattern,
                    ignore_patterns=ignore_patterns,
                    allowed_extensions=allowed_extensions,
                ),
            )
        return all_files

    def list_rules(self) -> Sequence[t.FeatureFlagMapping]:
        """Return loaded rules metadata for listing."""
        return [
            {
                c.Infra.ReportKeys.ID: rule.rule_id,
                c.Infra.NAME: rule.name,
                "description": rule.description,
                c.Infra.ReportKeys.ENABLED: rule.enabled,
                "severity": rule.severity,
            }
            for rule in self.rules
        ]

    def load_config(self) -> r[Mapping[str, t.Infra.InfraValue]]:
        """Load YAML configuration for this engine instance."""
        result = self.rule_loader.load_config()
        if result.is_success:
            config_dict: Mapping[str, t.Infra.InfraValue] = TypeAdapter(
                Mapping[str, t.Infra.InfraValue],
            ).validate_python(dict(result.value))
            self.config = config_dict
            u.Infra.refactor_info(f"Loaded config from {self.config_path}")
        return result

    def load_rules(self) -> r[Sequence[FlextInfraRefactorRule]]:
        """Load and instantiate enabled rules from rules directory."""
        rules_result = self.rule_loader.load_rules(
            self.rule_filters,
            self.rule_validator,
            self._build_rule,
            self._build_file_rules,
        )
        if rules_result.is_failure:
            return r[Sequence[FlextInfraRefactorRule]].fail(rules_result.error or "")
        loaded_rules, loaded_file_rules = rules_result.value
        self.rules = list(loaded_rules)
        self.file_rules = list(loaded_file_rules)
        u.Infra.refactor_info(f"Loaded {len(self.rules)} rules")
        if self.file_rules:
            u.Infra.refactor_info(
                f"Loaded {len(self.file_rules)} file rules",
            )
        if self.rule_filters:
            u.Infra.refactor_info(
                f"Active filters: {', '.join(self.rule_filters)}",
            )
        return r[Sequence[FlextInfraRefactorRule]].ok(loaded_rules)

    def _apply_file_rules(
        self,
        file_path: Path,
        source: str,
    ) -> m.Infra.Result | t.Infra.Pair[str, t.StrSequence]:
        """Apply file-level rules, returning error Result or (updated_source, changes)."""
        current = source
        all_changes: MutableSequence[str] = []
        for file_rule in self.file_rules:
            file_rule_result = file_rule.apply(file_path, dry_run=True)
            if not file_rule_result.success:
                return m.Infra.Result(
                    file_path=file_path,
                    success=False,
                    modified=False,
                    error=file_rule_result.error,
                    changes=file_rule_result.changes,
                    refactored_code=None,
                )
            if file_rule_result.modified and file_rule_result.refactored_code:
                current = file_rule_result.refactored_code
            all_changes.extend(file_rule_result.changes)
        return (current, list(all_changes))

    def _apply_cst_rules(
        self,
        file_path: Path,
        source: str,
    ) -> m.Infra.Result | t.Infra.Pair[str, t.StrSequence]:
        """Parse and apply CST rules, returning error Result or (code, changes)."""
        tree = u.Infra.parse_cst_from_source(source)
        if tree is None:
            return self._error_result(file_path, "parse_failed")
        all_changes: MutableSequence[str] = []
        for rule in self.rules:
            if rule.enabled:
                tree, changes = rule.apply(tree, file_path)
                all_changes.extend(changes)
        return (tree.code, list(all_changes))

    def refactor_file(
        self,
        file_path: Path,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Refactor one file with currently loaded rules."""
        try:
            if file_path.suffix != c.Infra.Extensions.PYTHON:
                return self._skip_result(file_path)
            original_source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            file_result = self._apply_file_rules(file_path, original_source)
            if isinstance(file_result, m.Infra.Result):
                return file_result
            source_after_file_rules, file_changes = file_result
            cst_result = self._apply_cst_rules(file_path, source_after_file_rules)
            if isinstance(cst_result, m.Infra.Result):
                return cst_result
            result_code, cst_changes = cst_result
            all_changes = [*file_changes, *cst_changes]
            modified = result_code != original_source
            if not dry_run and modified:
                u.write_file(file_path, result_code, encoding=c.Infra.Encoding.DEFAULT)
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=all_changes,
                refactored_code=result_code,
            )
        except Exception as exc:
            return self._error_result(file_path, str(exc))

    def refactor_files(
        self,
        file_paths: Sequence[Path],
        *,
        dry_run: bool = False,
    ) -> Sequence[m.Infra.Result]:
        """Refactor many files and collect individual results."""
        results: MutableSequence[m.Infra.Result] = []
        for file_path in file_paths:
            result = self.refactor_file(file_path, dry_run=dry_run)
            results.append(result)
            if result.success:
                if result.modified:
                    u.Infra.refactor_info(
                        f"{('[DRY-RUN] ' if dry_run else '')}Modified: {file_path.name}",
                    )
                    for change in result.changes:
                        u.Infra.refactor_info(f"  - {change}")
                else:
                    u.Infra.refactor_debug(f"Unchanged: {file_path.name}")
            else:
                u.Infra.refactor_error(
                    f"Failed: {file_path.name} - {result.error}",
                )
        return results

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor files under configured project directories matching the pattern."""
        stash_ref, stash_error = self._try_safety_stash(
            project_path,
            apply_safety=apply_safety,
            dry_run=dry_run,
        )
        if stash_error is not None:
            return stash_error
        collected = self._collect_project_files(project_path, pattern=pattern)
        if collected is None:
            return [
                self._error_result(
                    project_path,
                    f"File iteration failed for {project_path}",
                ),
            ]
        files = collected
        u.Infra.refactor_info(f"Found {len(files)} files to process")
        results: MutableSequence[m.Infra.Result] = list(
            u.Infra.run_rope_pre_hooks(project_path, dry_run=dry_run),
        )
        results.extend(self.refactor_files(files, dry_run=dry_run))
        results.extend(u.Infra.run_rope_post_hooks(project_path, dry_run=dry_run))
        if apply_safety and (not dry_run):
            checkpoint_result = self.safety_manager.save_checkpoint_state(
                project_path,
                status="transformed",
                stash_ref=stash_ref,
                processed_targets=[str(file_path) for file_path in files],
            )
            if checkpoint_result.is_failure:
                u.Infra.refactor_error(
                    checkpoint_result.error or "checkpoint save failed",
                )
            self._run_safety_validation_and_finalize(
                target_path=project_path,
                stash_ref=stash_ref,
                results=results,
            )
        return results

    def refactor_workspace(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor all discoverable workspace projects with one command."""
        root = workspace_root.resolve()
        if not root.exists() or not root.is_dir():
            u.Infra.refactor_error(
                f"Invalid workspace root: {workspace_root}",
            )
            return []
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        project_paths = u.Infra.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        if not project_paths:
            u.Infra.refactor_error(
                f"No projects discovered under workspace root: {workspace_root}",
            )
            return []
        u.Infra.refactor_info(
            f"Discovered {len(project_paths)} projects in workspace",
        )
        results: MutableSequence[m.Infra.Result] = []
        processed_targets: MutableSequence[str] = []
        stash_ref, stash_error = self._try_safety_stash(
            root,
            apply_safety=apply_safety,
            dry_run=dry_run,
        )
        if stash_error is not None:
            return stash_error
        results.extend(u.Infra.run_rope_pre_hooks(root, dry_run=dry_run))
        for project in project_paths:
            if apply_safety and self.safety_manager.is_emergency_stop_requested():
                break
            u.Infra.refactor_header(f"Project: {project}")
            project_results = self.refactor_project(
                project,
                dry_run=dry_run,
                pattern=pattern,
                apply_safety=False,
            )
            results.extend(project_results)
            if apply_safety and (not dry_run):
                processed_targets.append(str(project))
                checkpoint_result = self.safety_manager.save_checkpoint_state(
                    root,
                    status="running",
                    stash_ref=stash_ref,
                    processed_targets=list(processed_targets),
                )
                if checkpoint_result.is_failure:
                    u.Infra.refactor_error(
                        checkpoint_result.error or "checkpoint save failed",
                    )
        results.extend(u.Infra.run_rope_post_hooks(root, dry_run=dry_run))
        if apply_safety and (not dry_run):
            self._run_safety_validation_and_finalize(
                target_path=root,
                stash_ref=stash_ref,
                results=results,
            )
        return results

    def _run_safety_validation_and_finalize(
        self,
        *,
        target_path: Path,
        stash_ref: str,
        results: MutableSequence[m.Infra.Result],
    ) -> None:
        validation_result = self.safety_manager.run_semantic_validation(target_path)
        if validation_result.is_failure:
            error_msg = validation_result.error or "semantic validation failed"
            self.safety_manager.request_emergency_stop(error_msg)
            u.Infra.refactor_error(error_msg)
            rollback_result = self.safety_manager.rollback(target_path, stash_ref)
            if rollback_result.is_failure:
                u.Infra.refactor_error(
                    rollback_result.error or "rollback failed",
                )
            results.append(self._error_result(target_path, error_msg))
            return

        clear_result = self.safety_manager.clear_checkpoint()
        if clear_result.is_failure:
            u.Infra.refactor_error(
                clear_result.error or "checkpoint clear failed",
            )

    def _prepare_safety_stash(self, target_path: Path) -> r[str]:
        stash_result = self.safety_manager.create_pre_transformation_stash(target_path)
        if stash_result.is_failure:
            error_msg = stash_result.error or "pre-transformation stash failed"
            u.Infra.refactor_error(error_msg)
            return r[str].fail(error_msg)
        return r[str].ok(stash_result.value)

    def set_rule_filters(self, filters: t.StrSequence) -> None:
        """Set active rule filters using normalized lowercase rule ids."""
        self.rule_filters = [item.lower() for item in filters]

    def _build_file_rules(self) -> Sequence[FlextInfraClassNestingRefactorRule]:
        return [FlextInfraClassNestingRefactorRule()]

    def _build_rule(
        self,
        rule_def: Mapping[str, t.Infra.InfraValue],
    ) -> FlextInfraRefactorRule | None:
        rule_id = str(rule_def.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN))
        fix_action = u.Infra.get_str_key(
            rule_def,
            c.Infra.ReportKeys.FIX_ACTION,
            default=u.Infra.get_str_key(rule_def, c.Infra.ReportKeys.ACTION),
            lower=True,
        )
        check = u.Infra.get_str_key(rule_def, c.Infra.Verbs.CHECK, lower=True)
        return self._resolve_by_action(
            fix_action,
            check,
            rule_def,
        ) or self._resolve_by_rule_id(rule_id.lower(), rule_def)

    def _resolve_by_action(
        self,
        fix_action: str,
        check: str,
        rule_def: Mapping[str, t.Infra.InfraValue],
    ) -> FlextInfraRefactorRule | None:
        """Resolve rule via unified action registry lookup."""
        for action_set, rule_class in self._RULE_ACTION_REGISTRY:
            if fix_action in action_set or check in action_set:
                return rule_class(rule_def)
        return None

    def _resolve_by_rule_id(
        self,
        rule_id_lower: str,
        rule_def: Mapping[str, t.Infra.InfraValue],
    ) -> FlextInfraRefactorRule | None:
        """Resolve rule via rule_id keyword heuristics."""
        if "signature" in rule_id_lower and any(
            kw in rule_id_lower for kw in ("propagate", "rename")
        ):
            return FlextInfraRefactorSignaturePropagationRule(rule_def)
        for keywords, rule_class in self._RULE_ID_FALLBACKS:
            if any(kw in rule_id_lower for kw in keywords):
                return rule_class(rule_def)
        return None

    def _default_config_path(self) -> Path:
        return Path(__file__).parent / "config.yml"


__all__ = [
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorTier0ImportFixRule",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
]
