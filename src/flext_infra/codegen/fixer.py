"""Auto-fix engine for namespace violations.

AST-based auto-fixer that moves standalone Final constants to constants.py
and standalone TypeVar/TypeAlias definitions to typings.py.

Uses text-based line operations for file writes (format-preserving),
following the pattern from refactor/analysis.py rewrite_source/insert_import.
AST is used only for detection and dependency analysis (business logic).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

from flext_core import r, s
from rope.base.exceptions import ModuleSyntaxError

from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenSnapshot,
    FlextInfraNamespaceSourceDetector,
    FlextInfraNamespaceValidator,
    FlextInfraRefactorEngine,
    FlextInfraRefactorMigrateToClassMRO,
    c,
    m,
    t,
    u,
)


class FlextInfraCodegenFixer(s[bool]):
    """AST-based auto-fixer for namespace violations (Rules 1-2)."""

    _workspace_root: Path
    _dry_run: bool
    _rules_only: bool

    def __init__(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        rules_only: bool = False,
    ) -> None:
        """Initialize codegen fixer with workspace root."""
        super().__init__(
            config_type=None,
            config_overrides=None,
            initial_context=None,
            subproject=None,
            services=None,
            factories=None,
            resources=None,
            container_overrides=None,
            wire_modules=None,
            wire_packages=None,
            wire_classes=None,
        )
        self._workspace_root = workspace_root
        self._dry_run = dry_run
        self._rules_only = rules_only

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    @override
    def execute(self) -> r[bool]:
        return r[bool].fail("Use run() directly")

    @staticmethod
    def _empty_result(project_name: str) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=[],
            violations_skipped=[],
            files_modified=[],
        )

    def fix_project(self, project_path: Path) -> m.Infra.AutoFixResult:
        """Auto-fix namespace violations in a single project.

        Each rule parses the source file fresh so that line numbers stay
        accurate after a preceding rule modifies the file on disk.
        """
        prefix = FlextInfraNamespaceValidator.derive_prefix(project_path)
        if not prefix:
            return self._empty_result(project_path.name)
        pkg_dir = FlextInfraCodegenSnapshot.find_package_dir(project_path)
        if pkg_dir is None:
            return self._empty_result(project_path.name)
        violations_fixed: MutableSequence[m.Infra.CensusViolation] = []
        violations_skipped: MutableSequence[m.Infra.CensusViolation] = []
        files_modified: t.Infra.StrSet = set()
        src_dir = project_path / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return self._empty_result(project_path.name)
        checkpoint_result = u.Infra.create_checkpoint(
            self._workspace_root,
            label=f"codegen-fix:{project_path.name}",
        )
        stash_ref = checkpoint_result.value if checkpoint_result.is_success else ""
        self._apply_ns_rules(
            src_dir=src_dir,
            pkg_dir=pkg_dir,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=files_modified,
        )
        if self._dry_run or self._rules_only:
            return m.Infra.AutoFixResult(
                project=project_path.name,
                violations_fixed=violations_fixed,
                violations_skipped=violations_skipped,
                files_modified=sorted(files_modified),
            )
        report = self._apply_project_mro_migrations(
            project_path=project_path,
            files_modified=files_modified,
        )
        self._record_mro_migration_result(
            report=report,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
        )
        self._apply_refactor_engine_pass(
            project_path=project_path,
            files_modified=files_modified,
            violations_skipped=violations_skipped,
        )
        self._apply_namespace_enforcement_pass(
            project_path=project_path,
            files_modified=files_modified,
        )
        self._run_lazy_propagation(
            project_path=project_path,
            files_modified=files_modified,
        )
        try:
            self._cleanup_stale_all_entries(files_modified=files_modified)
            self._normalize_rewritten_python_files(files_modified=files_modified)
        except (OSError, UnicodeDecodeError):
            _ = u.Infra.rollback_to_checkpoint(self._workspace_root, stash_ref)
            raise
        return m.Infra.AutoFixResult(
            project=project_path.name,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=sorted(files_modified),
        )

    def _apply_ns_rules(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
    ) -> None:
        """Apply NS-001 and NS-002 rules to all Python files in src_dir."""
        excluded = {"constants.py", "typings.py", "__init__.py"}
        for py_file in sorted(src_dir.rglob("*.py")):
            if py_file.name in excluded:
                continue
            if py_file.name.startswith("_"):
                continue
            self._fix_rule1(
                source_file=py_file,
                pkg_dir=pkg_dir,
                violations_fixed=violations_fixed,
                violations_skipped=violations_skipped,
                files_modified=files_modified,
            )
            self._fix_rule2(
                source_file=py_file,
                pkg_dir=pkg_dir,
                violations_fixed=violations_fixed,
                violations_skipped=violations_skipped,
                files_modified=files_modified,
            )
        self._fix_rule3(
            pkg_dir=pkg_dir,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=files_modified,
        )
        self._fix_rule4(
            src_dir=src_dir,
            pkg_dir=pkg_dir,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=files_modified,
        )
        self._fix_rule5(
            src_dir=src_dir,
            pkg_dir=pkg_dir,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=files_modified,
        )

    def _apply_project_mro_migrations(
        self,
        *,
        project_path: Path,
        files_modified: t.Infra.StrSet,
    ) -> m.Infra.MROMigrationReport:
        service = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_path)
        try:
            report: m.Infra.MROMigrationReport = service.run(
                target="all",
                apply=True,
            )
        except (SyntaxError, ModuleSyntaxError, OSError, ValueError, KeyError, AttributeError):
            return m.Infra.MROMigrationReport(
                workspace=str(project_path),
                target="all",
                dry_run=False,
                files_scanned=0,
                files_with_candidates=0,
                remaining_violations=0,
                mro_failures=0,
                migrations=[],
                rewrites=[],
            )
        files_modified.update(migration.file for migration in report.migrations)
        files_modified.update(rewrite.file for rewrite in report.rewrites)
        return report

    def _apply_refactor_engine_pass(
        self,
        *,
        project_path: Path,
        files_modified: t.Infra.StrSet,
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
    ) -> None:
        engine = FlextInfraRefactorEngine()
        config_result = engine.load_config()
        if config_result.is_failure:
            message = config_result.error or "Failed to load refactor engine config"
            violations_skipped.append(
                m.Infra.CensusViolation(
                    module=str(project_path),
                    rule="NS-ENGINE",
                    line=1,
                    message=message,
                    fixable=False,
                ),
            )
            return
        engine.set_rule_filters(
            [
                "modernize-constants-import",
                "modernize-models-import",
                "modernize-result-import",
                "ban-lazy-imports",
                "ensure-future-annotations",
                "remove-compatibility-aliases",
                "remove-wrapper-functions",
                "remove-deprecated-classes",
                "remove-import-bypasses",
                "fix-container-invariance-annotations",
                "remove-validated-redundant-casts",
            ],
        )
        rules_result = engine.load_rules()
        if rules_result.is_failure:
            message = rules_result.error or "Failed to load filtered refactor rules"
            violations_skipped.append(
                m.Infra.CensusViolation(
                    module=str(project_path),
                    rule="NS-ENGINE",
                    line=1,
                    message=message,
                    fixable=False,
                ),
            )
            return
        results = engine.refactor_project(
            project_path,
            dry_run=False,
            apply_safety=False,
        )
        files_modified.update(
            str(result.file_path)
            for result in results
            if result.success and result.modified
        )
        violations_skipped.extend(
            m.Infra.CensusViolation(
                module=str(result.file_path),
                rule="NS-ENGINE",
                line=1,
                message=result.error or "Refactor engine pass failed",
                fixable=False,
            )
            for result in results
            if not result.success
        )

    def _apply_namespace_enforcement_pass(
        self,
        *,
        project_path: Path,
        files_modified: t.Infra.StrSet,
    ) -> None:
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_path,
            project_roots=[project_path],
            src_dirs=frozenset(c.Infra.MRO_SCAN_DIRECTORIES),
        )
        if py_files_result.is_failure:
            return
        py_files = py_files_result.value
        src_files = [
            file_path
            for file_path in py_files
            if c.Infra.Paths.DEFAULT_SRC_DIR in file_path.parts
        ]
        before_snapshot: t.StrMapping = FlextInfraCodegenSnapshot.snapshot_files(
            file_paths=src_files,
        )
        package_name = FlextInfraNamespaceSourceDetector.discover_project_package_name(
            project_root=project_path,
        )
        u.Infra.namespace_rewrite_import_violations(
            py_files=src_files,
            project_package=package_name,
        )
        u.Infra.namespace_rewrite_runtime_alias_violations(
            py_files=src_files,
        )
        u.Infra.namespace_rewrite_missing_future_annotations(
            py_files=src_files,
        )
        changed_paths: t.Infra.StrSet = FlextInfraCodegenSnapshot.detect_changed_files(
            before_snapshot=before_snapshot,
            file_paths=src_files,
        )
        files_modified.update(changed_paths)

    @staticmethod
    def _record_mro_migration_result(
        *,
        report: m.Infra.MROMigrationReport,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
    ) -> None:
        for migration in report.migrations:
            violations_fixed.extend(
                m.Infra.CensusViolation(
                    module=migration.file,
                    rule="NS-MRO",
                    line=1,
                    message=(
                        "Moved symbol "
                        f"'{moved_symbol}' into namespace class via MRO migration"
                    ),
                    fixable=True,
                )
                for moved_symbol in migration.moved_symbols
            )
        if report.remaining_violations > 0:
            violations_skipped.append(
                m.Infra.CensusViolation(
                    module=report.workspace,
                    rule="NS-MRO",
                    line=1,
                    message=(
                        "MRO migration finished with "
                        f"{report.remaining_violations} remaining violations"
                    ),
                    fixable=False,
                ),
            )
        if report.mro_failures > 0:
            violations_skipped.append(
                m.Infra.CensusViolation(
                    module=report.workspace,
                    rule="NS-MRO",
                    line=1,
                    message=f"MRO validation reported {report.mro_failures} failures",
                    fixable=False,
                ),
            )
        violations_skipped.extend(
            m.Infra.CensusViolation(
                module=report.workspace,
                rule="NS-MRO",
                line=1,
                message=warning,
                fixable=False,
            )
            for warning in report.warnings
        )
        violations_skipped.extend(
            m.Infra.CensusViolation(
                module=report.workspace,
                rule="NS-MRO",
                line=1,
                message=error,
                fixable=False,
            )
            for error in report.errors
        )

    def _cleanup_stale_all_entries(self, *, files_modified: t.Infra.StrSet) -> None:
        for file_path in sorted(files_modified):
            path = Path(file_path)
            if not path.exists() or path.suffix != c.Infra.Extensions.PYTHON:
                continue
            if path.name == c.Infra.Files.INIT_PY:
                continue
            if u.Infra.prune_stale_all_assignment(path=path):
                files_modified.add(str(path))

    def _normalize_rewritten_python_files(
        self, *, files_modified: t.Infra.StrSet
    ) -> None:
        for file_path in sorted(files_modified):
            path = Path(file_path)
            if not path.exists() or path.suffix != c.Infra.Extensions.PYTHON:
                continue
            u.Infra.run_ruff_fix(path)

    def _run_lazy_propagation(
        self,
        *,
        project_path: Path,
        files_modified: t.Infra.StrSet,
    ) -> None:
        before_snapshot: t.StrMapping = FlextInfraCodegenSnapshot.snapshot_init_files(
            project_path=project_path,
        )
        _ = FlextInfraCodegenLazyInit(workspace_root=project_path).run(check_only=False)
        after_snapshot: t.StrMapping = FlextInfraCodegenSnapshot.snapshot_init_files(
            project_path=project_path,
        )
        for path_str, updated in after_snapshot.items():
            previous = before_snapshot.get(path_str)
            if previous == updated:
                continue
            files_modified.add(path_str)

    def run(self) -> Sequence[m.Infra.AutoFixResult]:
        """Run auto-fix on all projects in workspace.

        Returns:
            List of AutoFixResult models, one per project.

        """
        projects_result = u.Infra.discover_projects(self._workspace_root)
        if not projects_result.is_success:
            return []
        results: MutableSequence[m.Infra.AutoFixResult] = []
        discovered: Sequence[m.Infra.ProjectInfo] = projects_result.unwrap()
        for project in discovered:
            if project.name in c.Infra.EXCLUDED_PROJECTS:
                continue
            if (project.path / c.Infra.Files.GO_MOD).exists():
                continue
            result = self.fix_project(project.path)
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Rule implementations (parse fresh, text-based writes)
    # ------------------------------------------------------------------

    def _move_nodes_to_target(
        self,
        *,
        source_file: Path,
        pkg_dir: Path,
        rule: str,
        target_filename: str,
        target_module: str,
        candidates: Sequence[ast.stmt],
        tree: ast.Module,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
        check_first_party: bool = False,
    ) -> None:
        """Shared logic for moving nodes from source to target module."""
        target_path = pkg_dir / target_filename
        if not target_path.exists():
            return
        target_tree = u.Infra.parse_module_ast(target_path)
        if target_tree is None:
            return
        # Filter private names
        nodes_to_move: MutableSequence[ast.stmt] = []
        for node in candidates:
            name = u.Infra.get_node_name(node)
            if (
                not name
                and isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
            ):
                name = node.target.id
            if not name:
                continue
            if name.startswith("_"):
                violations_skipped.append(
                    m.Infra.CensusViolation(
                        module=str(source_file),
                        rule=rule,
                        line=node.lineno,
                        message=f"'{name}' is private — skipped",
                        fixable=False,
                    ),
                )
                continue
            nodes_to_move.append(node)
        if not nodes_to_move:
            return
        actually_moved: MutableSequence[ast.stmt] = []
        moved_names: MutableSequence[str] = []
        for node in nodes_to_move:
            name = u.Infra.get_node_name(node)
            if (
                not name
                and isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
            ):
                name = node.target.id
            if not name:
                continue
            if u.Infra.name_exists_in_module(name, target_tree):
                violations_skipped.append(
                    m.Infra.CensusViolation(
                        module=str(source_file),
                        rule=rule,
                        line=node.lineno,
                        message=f"'{name}' already in {target_filename} — skipped",
                        fixable=False,
                    ),
                )
                continue
            if check_first_party and u.Infra.needs_first_party_import(
                node, tree, target_tree
            ):
                violations_skipped.append(
                    m.Infra.CensusViolation(
                        module=str(source_file),
                        rule=rule,
                        line=node.lineno,
                        message=f"'{name}' needs first-party import — circular risk, skipped",
                        fixable=False,
                    ),
                )
                continue
            u.Infra.copy_required_imports(node, tree, target_tree)
            if not u.Infra.all_deps_resolvable(node, target_tree):
                violations_skipped.append(
                    m.Infra.CensusViolation(
                        module=str(source_file),
                        rule=rule,
                        line=node.lineno,
                        message=f"'{name}' has unresolvable deps — skipped",
                        fixable=False,
                    ),
                )
                continue
            insert_idx = u.Infra.find_insert_position(target_tree)
            target_tree.body.insert(insert_idx, node)
            kind = ""
            if isinstance(node, ast.AnnAssign):
                kind = "Final constant "
            elif isinstance(node, ast.Assign):
                kind = "TypeVar "
            else:
                kind = "TypeAlias "
            violations_fixed.append(
                m.Infra.CensusViolation(
                    module=str(source_file),
                    rule=rule,
                    line=node.lineno,
                    message=f"{kind}'{name}' moved to {target_filename}",
                    fixable=True,
                ),
            )
            actually_moved.append(node)
            moved_names.append(name)
        if actually_moved:
            FlextInfraCodegenSnapshot.write_changes(
                source_path=source_file,
                target_path=target_path,
                nodes_moved=actually_moved,
                moved_names=moved_names,
                source_tree=tree,
                pkg_name=pkg_dir.name,
                target_module=target_module,
                dry_run=self._dry_run,
            )
            files_modified.add(str(source_file))
            files_modified.add(str(target_path))

    def _fix_rule1(
        self,
        *,
        source_file: Path,
        pkg_dir: Path,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
    ) -> None:
        """Fix Rule 1 — move loose Final constants to constants.py."""
        tree = u.Infra.parse_module_ast(source_file)
        if tree is None:
            return
        finals = u.Infra.find_standalone_finals(tree)
        if not finals:
            return
        self._move_nodes_to_target(
            source_file=source_file,
            pkg_dir=pkg_dir,
            rule="NS-001",
            target_filename="constants.py",
            target_module="constants",
            candidates=finals,
            tree=tree,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=files_modified,
        )

    def _fix_rule2(
        self,
        *,
        source_file: Path,
        pkg_dir: Path,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
    ) -> None:
        """Fix Rule 2 — move loose TypeVars/TypeAliases to typings.py."""
        tree = u.Infra.parse_module_ast(source_file)
        if tree is None:
            return
        typevars = u.Infra.find_standalone_typevars(tree)
        typealiases = u.Infra.find_standalone_typealiases(tree)
        candidates: MutableSequence[ast.stmt] = [*typevars, *typealiases]
        if not candidates:
            return
        self._move_nodes_to_target(
            source_file=source_file,
            pkg_dir=pkg_dir,
            rule="NS-002",
            target_filename="typings.py",
            target_module=c.Infra.Directories.TYPINGS,
            candidates=candidates,
            tree=tree,
            violations_fixed=violations_fixed,
            violations_skipped=violations_skipped,
            files_modified=files_modified,
            check_first_party=True,
        )

    @staticmethod
    def _resolve_parent_constants_class(constants_file: Path) -> str:
        tree = u.Infra.parse_module_ast(constants_file)
        if tree is None:
            return ""
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.bases:
                return ""
            return ast.unparse(node.bases[0])
        return ""

    def _fix_rule3(
        self,
        *,
        pkg_dir: Path,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
    ) -> None:
        constants_file = pkg_dir / "constants.py"
        if not constants_file.exists():
            return
        definitions = u.Infra.extract_constant_definitions(
            file_path=constants_file,
            project=pkg_dir.name,
        )
        hardcoded = u.Infra.detect_hardcoded_canonicals(
            definitions,
        )
        if not hardcoded:
            return
        parent_class = self._resolve_parent_constants_class(constants_file)
        if not parent_class:
            violations_skipped.extend(
                m.Infra.CensusViolation(
                    module=definition.file_path,
                    rule="NS-003",
                    line=definition.line,
                    message=(
                        f"Could not resolve parent constants class for '{definition.name}'"
                    ),
                    fixable=False,
                )
                for definition in hardcoded
            )
            return
        modified, _ = u.Infra.replace_canonical_values(
            file_path=constants_file,
            parent_class=parent_class,
            definitions=hardcoded,
        )
        if modified:
            files_modified.add(str(constants_file))
            violations_fixed.extend(
                m.Infra.CensusViolation(
                    module=definition.file_path,
                    rule="NS-003",
                    line=definition.line,
                    message=(
                        f"Hardcoded canonical '{definition.name}' replaced with {parent_class} reference"
                    ),
                    fixable=True,
                )
                for definition in hardcoded
            )
            return
        violations_skipped.extend(
            m.Infra.CensusViolation(
                module=definition.file_path,
                rule="NS-003",
                line=definition.line,
                message=f"No canonical replacement applied for '{definition.name}'",
                fixable=False,
            )
            for definition in hardcoded
        )

    def _fix_rule4(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
    ) -> None:
        constants_file = pkg_dir / "constants.py"
        if not constants_file.exists():
            return
        definitions = u.Infra.extract_constant_definitions(
            file_path=constants_file,
            project=pkg_dir.name,
        )
        if not definitions:
            return

        all_used_names: t.Infra.StrSet = set()
        projects_result = u.Infra.discover_projects(self._workspace_root)
        if projects_result.is_success:
            discovered_projects: Sequence[m.Infra.ProjectInfo] = (
                projects_result.unwrap()
            )
            for project in discovered_projects:
                discovered_src = project.path / c.Infra.Paths.DEFAULT_SRC_DIR
                if not discovered_src.is_dir():
                    continue
                for py_file in sorted(discovered_src.rglob("*.py")):
                    used_names, _, _ = u.Infra.scan_constant_usages(
                        file_path=py_file,
                        project=project.name,
                    )
                    all_used_names.update(used_names)
        else:
            for py_file in sorted(src_dir.rglob("*.py")):
                used_names, _, _ = u.Infra.scan_constant_usages(
                    file_path=py_file,
                    project=pkg_dir.name,
                )
                all_used_names.update(used_names)

        unused = u.Infra.detect_unused_constants(
            definitions=definitions,
            all_used_names=all_used_names,
        )
        if not unused:
            return
        modified, _ = u.Infra.remove_unused_constants(
            file_path=constants_file,
            unused=unused,
        )
        if modified:
            files_modified.add(str(constants_file))
            violations_fixed.extend(
                m.Infra.CensusViolation(
                    module=item.file_path,
                    rule="NS-004",
                    line=item.line,
                    message=f"Removed unused constant '{item.name}'",
                    fixable=True,
                )
                for item in unused
            )
            return
        violations_skipped.extend(
            m.Infra.CensusViolation(
                module=item.file_path,
                rule="NS-004",
                line=item.line,
                message=f"Unused constant '{item.name}' detected but not removed",
                fixable=False,
            )
            for item in unused
        )

    def _fix_rule5(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        violations_fixed: MutableSequence[m.Infra.CensusViolation],
        violations_skipped: MutableSequence[m.Infra.CensusViolation],
        files_modified: t.Infra.StrSet,
    ) -> None:
        project_import = f"from {pkg_dir.name} import c"
        for py_file in sorted(src_dir.rglob("*.py")):
            if py_file.name == "constants.py":
                continue
            _, direct_refs, _ = u.Infra.scan_constant_usages(
                file_path=py_file,
                project=pkg_dir.name,
            )
            if not direct_refs:
                continue
            modified, _ = u.Infra.normalize_constant_aliases(
                file_path=py_file,
                project_import=project_import,
            )
            if modified:
                files_modified.add(str(py_file))
                violations_fixed.extend(
                    m.Infra.CensusViolation(
                        module=ref.file_path,
                        rule="NS-005",
                        line=ref.line,
                        message=(
                            f"Direct ref {ref.full_ref} normalized to {ref.alias_ref}"
                        ),
                        fixable=True,
                    )
                    for ref in direct_refs
                )
                continue
            violations_skipped.extend(
                m.Infra.CensusViolation(
                    module=ref.file_path,
                    rule="NS-005",
                    line=ref.line,
                    message=(
                        f"Direct ref {ref.full_ref} detected but replacement did not apply"
                    ),
                    fixable=False,
                )
                for ref in direct_refs
            )


__all__ = ["FlextInfraCodegenFixer"]
