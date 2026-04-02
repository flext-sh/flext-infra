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
from dataclasses import dataclass
from pathlib import Path
from typing import override

from flext_core import r, s
from pydantic import Field
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


def _violation(
    *,
    module: str,
    rule: str,
    line: int,
    message: str,
    fixable: bool,
) -> m.Infra.CensusViolation:
    """Create a CensusViolation with standard fields."""
    return m.Infra.CensusViolation(
        module=module,
        rule=rule,
        line=line,
        message=message,
        fixable=fixable,
    )


@dataclass(frozen=True, slots=True)
class _MoveTarget:
    """Configuration for moving AST nodes to a target module."""

    rule: str
    target_filename: str
    target_module: str
    check_first_party: bool = False


class FlextInfraCodegenFixer(s[bool]):
    """AST-based auto-fixer for namespace violations (Rules 1-5)."""

    class _FixContext(m.ArbitraryTypesModel):
        """Mutable accumulation context for fix operations."""

        violations_fixed: MutableSequence[m.Infra.CensusViolation] = Field(
            default_factory=list,
        )
        violations_skipped: MutableSequence[m.Infra.CensusViolation] = Field(
            default_factory=list,
        )
        files_modified: t.Infra.StrSet = Field(default_factory=set)

        def skip(self, *, module: str, rule: str, line: int, message: str) -> None:
            """Record a skipped violation."""
            self.violations_skipped.append(
                _violation(
                    module=module, rule=rule, line=line, message=message, fixable=False
                ),
            )

        def fix(self, *, module: str, rule: str, line: int, message: str) -> None:
            """Record a fixed violation."""
            self.violations_fixed.append(
                _violation(
                    module=module, rule=rule, line=line, message=message, fixable=True
                ),
            )

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
        super().__init__()
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

    @staticmethod
    def _build_result(
        project_name: str,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> m.Infra.AutoFixResult:
        return m.Infra.AutoFixResult(
            project=project_name,
            violations_fixed=ctx.violations_fixed,
            violations_skipped=ctx.violations_skipped,
            files_modified=sorted(ctx.files_modified),
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
        ctx = self._FixContext()
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
            ctx=ctx,
        )
        if self._dry_run or self._rules_only:
            return self._build_result(project_path.name, ctx)
        report = self._apply_project_mro_migrations(
            project_path=project_path,
            ctx=ctx,
        )
        self._record_mro_migration_result(report=report, ctx=ctx)
        self._apply_refactor_engine_pass(project_path=project_path, ctx=ctx)
        self._apply_namespace_enforcement_pass(project_path=project_path, ctx=ctx)
        self._run_lazy_propagation(project_path=project_path, ctx=ctx)
        try:
            self._cleanup_stale_all_entries(ctx)
            self._normalize_rewritten_python_files(ctx)
        except (OSError, UnicodeDecodeError):
            _ = u.Infra.rollback_to_checkpoint(self._workspace_root, stash_ref)
            raise
        return self._build_result(project_path.name, ctx)

    def _apply_ns_rules(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Apply NS-001 and NS-002 rules to all Python files in src_dir."""
        excluded = {"constants.py", "typings.py", c.Infra.Files.INIT_PY}
        for py_file in sorted(src_dir.rglob("*.py")):
            if py_file.name in excluded:
                continue
            if py_file.name.startswith("_"):
                continue
            self._fix_rule1(
                source_file=py_file,
                pkg_dir=pkg_dir,
                ctx=ctx,
            )
            self._fix_rule2(
                source_file=py_file,
                pkg_dir=pkg_dir,
                ctx=ctx,
            )
        self._fix_rule3(
            pkg_dir=pkg_dir,
            ctx=ctx,
        )
        self._fix_rule4(
            src_dir=src_dir,
            pkg_dir=pkg_dir,
            ctx=ctx,
        )
        self._fix_rule5(
            src_dir=src_dir,
            pkg_dir=pkg_dir,
            ctx=ctx,
        )

    def _apply_project_mro_migrations(
        self,
        *,
        project_path: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> m.Infra.MROMigrationReport:
        service = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_path)
        try:
            report: m.Infra.MROMigrationReport = service.run(
                target="all",
                apply=True,
            )
        except (
            SyntaxError,
            ModuleSyntaxError,
            OSError,
            ValueError,
            KeyError,
            AttributeError,
        ):
            return m.Infra.MROMigrationReport(
                workspace=str(project_path),
                target="all",
                dry_run=False,
                files_scanned=0,
                files_with_candidates=0,
                remaining_violations=0,
                mro_failures=0,
                stash_ref="",
                migrations=(),
                rewrites=(),
            )
        ctx.files_modified.update(migration.file for migration in report.migrations)
        ctx.files_modified.update(rewrite.file for rewrite in report.rewrites)
        return report

    _REFACTOR_RULES: Sequence[str] = (
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
    )

    def _apply_refactor_engine_pass(
        self,
        *,
        project_path: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        engine = FlextInfraRefactorEngine()
        config_result = engine.load_config()
        if config_result.is_failure:
            ctx.skip(
                module=str(project_path),
                rule="NS-ENGINE",
                line=1,
                message=config_result.error or "Failed to load refactor engine config",
            )
            return
        engine.set_rule_filters(list(self._REFACTOR_RULES))
        rules_result = engine.load_rules()
        if rules_result.is_failure:
            ctx.skip(
                module=str(project_path),
                rule="NS-ENGINE",
                line=1,
                message=rules_result.error or "Failed to load filtered refactor rules",
            )
            return
        results = engine.refactor_project(
            project_path,
            dry_run=False,
            apply_safety=False,
        )
        ctx.files_modified.update(
            str(result.file_path)
            for result in results
            if result.success and result.modified
        )
        for result in results:
            if not result.success:
                ctx.skip(
                    module=str(result.file_path),
                    rule="NS-ENGINE",
                    line=1,
                    message=result.error or "Refactor engine pass failed",
                )

    def _apply_namespace_enforcement_pass(
        self,
        *,
        project_path: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_path,
            project_roots=[project_path],
            src_dirs=frozenset(c.Infra.MRO_SCAN_DIRECTORIES),
        )
        if py_files_result.is_failure:
            return
        src_files = [
            file_path
            for file_path in py_files_result.value
            if c.Infra.Paths.DEFAULT_SRC_DIR in file_path.parts
        ]
        before_snapshot: t.StrMapping = FlextInfraCodegenSnapshot.snapshot_files(
            file_paths=src_files,
        )
        package_name = FlextInfraNamespaceSourceDetector.discover_project_package_name(
            project_root=project_path,
        )
        u.Infra.rewrite_import_violations(
            py_files=src_files,
            project_package=package_name,
        )
        u.Infra.rewrite_runtime_alias_violations(py_files=src_files)
        u.Infra.rewrite_missing_future_annotations(py_files=src_files)
        changed_paths = FlextInfraCodegenSnapshot.detect_changed_files(
            before_snapshot=before_snapshot,
            file_paths=src_files,
        )
        ctx.files_modified.update(changed_paths)

    @staticmethod
    def _record_mro_migration_result(
        *,
        report: m.Infra.MROMigrationReport,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        for migration in report.migrations:
            for moved_symbol in migration.moved_symbols:
                ctx.fix(
                    module=migration.file,
                    rule="NS-MRO",
                    line=1,
                    message=f"Moved symbol '{moved_symbol}' into namespace class via MRO migration",
                )
        if report.remaining_violations > 0:
            ctx.skip(
                module=report.workspace,
                rule="NS-MRO",
                line=1,
                message=f"MRO migration finished with {report.remaining_violations} remaining violations",
            )
        if report.mro_failures > 0:
            ctx.skip(
                module=report.workspace,
                rule="NS-MRO",
                line=1,
                message=f"MRO validation reported {report.mro_failures} failures",
            )
        for message in [*report.warnings, *report.errors]:
            ctx.skip(
                module=report.workspace,
                rule="NS-MRO",
                line=1,
                message=message,
            )

    @staticmethod
    def _cleanup_stale_all_entries(ctx: FlextInfraCodegenFixer._FixContext) -> None:
        for file_path in sorted(ctx.files_modified):
            path = Path(file_path)
            if not path.exists() or path.suffix != c.Infra.Extensions.PYTHON:
                continue
            if path.name == c.Infra.Files.INIT_PY:
                continue
            if u.Infra.prune_stale_all_assignment(path=path):
                ctx.files_modified.add(str(path))

    @staticmethod
    def _normalize_rewritten_python_files(
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        for file_path in sorted(ctx.files_modified):
            path = Path(file_path)
            if not path.exists() or path.suffix != c.Infra.Extensions.PYTHON:
                continue
            u.Infra.run_ruff_fix(path)

    def _run_lazy_propagation(
        self,
        *,
        project_path: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        before_snapshot: t.StrMapping = FlextInfraCodegenSnapshot.snapshot_init_files(
            project_path=project_path,
        )
        _ = FlextInfraCodegenLazyInit(workspace_root=project_path).run(check_only=False)
        after_snapshot: t.StrMapping = FlextInfraCodegenSnapshot.snapshot_init_files(
            project_path=project_path,
        )
        ctx.files_modified.update(
            path_str
            for path_str, updated in after_snapshot.items()
            if before_snapshot.get(path_str) != updated
        )

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

    @staticmethod
    def _node_kind_label(node: ast.stmt) -> str:
        """Return a human-readable label for an AST assignment node."""
        if isinstance(node, ast.AnnAssign):
            return "Final constant"
        if isinstance(node, ast.Assign):
            return "TypeVar"
        return "TypeAlias"

    def _move_nodes_to_target(
        self,
        *,
        source_file: Path,
        pkg_dir: Path,
        target: _MoveTarget,
        candidates: Sequence[ast.stmt],
        tree: ast.Module,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Move qualifying AST nodes from source to target module."""
        target_path = pkg_dir / target.target_filename
        if not target_path.exists():
            return
        target_tree = u.Infra.parse_module_ast(target_path)
        if target_tree is None:
            return
        module_str = str(source_file)
        public_nodes = self._filter_private_nodes(
            candidates, module_str=module_str, rule=target.rule, ctx=ctx
        )
        if not public_nodes:
            return
        actually_moved, moved_names = self._try_move_nodes(
            nodes=public_nodes,
            tree=tree,
            target_tree=target_tree,
            target=target,
            module_str=module_str,
            ctx=ctx,
        )
        if actually_moved:
            FlextInfraCodegenSnapshot.write_changes(
                source_path=source_file,
                target_path=target_path,
                nodes_moved=actually_moved,
                moved_names=moved_names,
                source_tree=tree,
                pkg_name=pkg_dir.name,
                target_module=target.target_module,
                dry_run=self._dry_run,
            )
            ctx.files_modified.add(module_str)
            ctx.files_modified.add(str(target_path))

    @staticmethod
    def _filter_private_nodes(
        candidates: Sequence[ast.stmt],
        *,
        module_str: str,
        rule: str,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> Sequence[ast.stmt]:
        """Keep only public nodes; record skips for private ones."""
        public: MutableSequence[ast.stmt] = []
        for node in candidates:
            name = u.Infra.get_node_name(node)
            if not name:
                continue
            if name.startswith("_"):
                ctx.skip(
                    module=module_str,
                    rule=rule,
                    line=node.lineno,
                    message=f"'{name}' is private — skipped",
                )
                continue
            public.append(node)
        return public

    def _try_move_nodes(
        self,
        *,
        nodes: Sequence[ast.stmt],
        tree: ast.Module,
        target_tree: ast.Module,
        target: _MoveTarget,
        module_str: str,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> tuple[Sequence[ast.stmt], Sequence[str]]:
        """Attempt to move each node; return (moved_nodes, moved_names)."""
        moved: MutableSequence[ast.stmt] = []
        names: MutableSequence[str] = []
        for node in nodes:
            name = u.Infra.get_node_name(node)
            if not name:
                continue
            skip_reason = self._check_move_blockers(
                node=node,
                name=name,
                tree=tree,
                target_tree=target_tree,
                target=target,
            )
            if skip_reason:
                ctx.skip(
                    module=module_str,
                    rule=target.rule,
                    line=node.lineno,
                    message=skip_reason,
                )
                continue
            insert_idx = u.Infra.find_insert_position(target_tree)
            target_tree.body.insert(insert_idx, node)
            kind = self._node_kind_label(node)
            ctx.fix(
                module=module_str,
                rule=target.rule,
                line=node.lineno,
                message=f"{kind} '{name}' moved to {target.target_filename}",
            )
            moved.append(node)
            names.append(name)
        return moved, names

    @staticmethod
    def _check_move_blockers(
        *,
        node: ast.stmt,
        name: str,
        tree: ast.Module,
        target_tree: ast.Module,
        target: _MoveTarget,
    ) -> str:
        """Return skip reason if node cannot be moved, or empty string."""
        if u.Infra.name_exists_in_module(name, target_tree):
            return f"'{name}' already in {target.target_filename} — skipped"
        if target.check_first_party and u.Infra.needs_first_party_import(
            node, tree, target_tree
        ):
            return f"'{name}' needs first-party import — circular risk, skipped"
        u.Infra.copy_required_imports(node, tree, target_tree)
        if not u.Infra.all_deps_resolvable(node, target_tree):
            return f"'{name}' has unresolvable deps — skipped"
        return ""

    _RULE1_TARGET = _MoveTarget(
        rule="NS-001",
        target_filename="constants.py",
        target_module="constants",
    )
    _RULE2_TARGET = _MoveTarget(
        rule="NS-002",
        target_filename="typings.py",
        target_module=c.Infra.Directories.TYPINGS,
        check_first_party=True,
    )

    def _fix_rule1(
        self,
        *,
        source_file: Path,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
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
            target=self._RULE1_TARGET,
            candidates=finals,
            tree=tree,
            ctx=ctx,
        )

    def _fix_rule2(
        self,
        *,
        source_file: Path,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
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
            target=self._RULE2_TARGET,
            candidates=candidates,
            tree=tree,
            ctx=ctx,
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

    @staticmethod
    def _record_bulk_result(
        *,
        modified: bool,
        file_path: Path,
        items: Sequence[m.Infra.BulkFixItem],
        rule: str,
        fix_message: str,
        skip_message: str,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Record fix/skip violations for a bulk file operation."""
        if modified:
            ctx.files_modified.add(str(file_path))
            for item in items:
                ctx.fix(
                    module=item.file_path,
                    rule=rule,
                    line=item.line,
                    message=fix_message.format(name=item.name),
                )
        else:
            for item in items:
                ctx.skip(
                    module=item.file_path,
                    rule=rule,
                    line=item.line,
                    message=skip_message.format(name=item.name),
                )

    def _fix_rule3(
        self,
        *,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Fix Rule 3 — replace hardcoded canonical constants with parent refs."""
        constants_file = pkg_dir / "constants.py"
        if not constants_file.exists():
            return
        definitions = u.Infra.extract_constant_definitions(
            file_path=constants_file,
            project=pkg_dir.name,
        )
        hardcoded = u.Infra.detect_hardcoded_canonicals(definitions)
        if not hardcoded:
            return
        parent_class = self._resolve_parent_constants_class(constants_file)
        if not parent_class:
            for definition in hardcoded:
                ctx.skip(
                    module=definition.file_path,
                    rule="NS-003",
                    line=definition.line,
                    message=f"Could not resolve parent constants class for '{definition.name}'",
                )
            return
        modified, _ = u.Infra.replace_canonical_values(
            file_path=constants_file,
            parent_class=parent_class,
            definitions=hardcoded,
        )
        self._record_bulk_result(
            modified=modified,
            file_path=constants_file,
            items=hardcoded,
            rule="NS-003",
            fix_message=f"Hardcoded canonical '{{name}}' replaced with {parent_class} reference",
            skip_message="No canonical replacement applied for '{name}'",
            ctx=ctx,
        )

    def _fix_rule4(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Fix Rule 4 — remove unused constants."""
        constants_file = pkg_dir / "constants.py"
        if not constants_file.exists():
            return
        definitions = u.Infra.extract_constant_definitions(
            file_path=constants_file,
            project=pkg_dir.name,
        )
        if not definitions:
            return
        all_used_names = self._collect_used_constant_names(src_dir, pkg_dir)
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
        self._record_bulk_result(
            modified=modified,
            file_path=constants_file,
            items=unused,
            rule="NS-004",
            fix_message="Removed unused constant '{name}'",
            skip_message="Unused constant '{name}' detected but not removed",
            ctx=ctx,
        )

    def _collect_used_constant_names(
        self,
        src_dir: Path,
        pkg_dir: Path,
    ) -> t.Infra.StrSet:
        """Scan all workspace projects (or fallback to src_dir) for used constant names."""
        all_used_names: t.Infra.StrSet = set()
        projects_result = u.Infra.discover_projects(self._workspace_root)
        if projects_result.is_success:
            for project in projects_result.unwrap():
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
        return all_used_names

    def _fix_rule5(
        self,
        *,
        src_dir: Path,
        pkg_dir: Path,
        ctx: FlextInfraCodegenFixer._FixContext,
    ) -> None:
        """Fix Rule 5 — normalize direct constant references to c.* aliases."""
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
                ctx.files_modified.add(str(py_file))
                for ref in direct_refs:
                    ctx.fix(
                        module=ref.file_path,
                        rule="NS-005",
                        line=ref.line,
                        message=f"Direct ref {ref.full_ref} normalized to {ref.alias_ref}",
                    )
            else:
                for ref in direct_refs:
                    ctx.skip(
                        module=ref.file_path,
                        rule="NS-005",
                        line=ref.line,
                        message=f"Direct ref {ref.full_ref} detected but replacement did not apply",
                    )


__all__ = ["FlextInfraCodegenFixer"]
