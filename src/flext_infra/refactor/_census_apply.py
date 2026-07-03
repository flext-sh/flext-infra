"""Census fix application + post-apply regeneration — extracted concern."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, p, t, u
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.detectors.compatibility_alias_detector import (
    FlextInfraCompatibilityAliasDetector,
)
from flext_infra.detectors.inline_import_detector import (
    FlextInfraInlineImportDetector,
)
from flext_infra.detectors.manual_typing_alias_detector import (
    FlextInfraManualTypingAliasDetector,
)
from flext_infra.detectors.mro_completeness_detector import (
    FlextInfraMROCompletenessDetector,
)
from flext_infra.detectors.private_import_bypass_detector import (
    FlextInfraPrivateImportBypassDetector,
)
from flext_infra.refactor._census_apply_formatting import (
    FlextInfraRefactorCensusApplyFormattingMixin,
)


class FlextInfraRefactorCensusApplyMixin(
    FlextInfraRefactorCensusApplyFormattingMixin,
):
    """Apply supported auto-fixes + removal candidates, then regenerate inits.

    Composed into FlextInfraRefactorCensus via inheritance; borrows the
    detector-context / fix-key / runtime-alias-rewrite helpers + root +
    dry_run_gate_names from the facade and sibling mixins via MRO.
    """

    if TYPE_CHECKING:

        @property
        def root(self) -> Path: ...

        @property
        def dry_run_gate_names(self) -> t.StrSequence: ...
        @staticmethod
        def _detector_context(
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            convention: m.Infra.RopeModuleConvention | None = None,
            parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation]
            | None = None,
        ) -> m.Infra.DetectorContext: ...
        @staticmethod
        def _fix_key(file_path: Path, object_name: str, action: str = "") -> str: ...
        @staticmethod
        def _rewrite_runtime_alias_source(
            source: str, *, alias: str, target_name: str
        ) -> str: ...

    def _apply_supported_fixes(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        report: m.Infra.Census.WorkspaceReport,
    ) -> frozenset[str]:
        """Apply supported fixes."""
        applied: set[str] = set()
        touched_paths: set[Path] = set()
        requested_fixes: dict[tuple[Path, str], set[str]] = defaultdict(set)
        for project in report.projects:
            for fix in project.fixes:
                requested_fixes[Path(fix.source_file), fix.action].add(fix.object_name)
        for (file_path, action), object_names in requested_fixes.items():
            parse_failures: list[m.Infra.ParseFailureViolation] = []
            ctx = self._detector_context(rope, file_path, parse_failures=parse_failures)
            changed = False
            if action == "rewrite_runtime_alias":
                convention = rope.convention(file_path)
                alias = convention.module_policy.expected_alias or ""
                target_name = next(iter(sorted(object_names)), "")
                if not alias or not target_name:
                    continue
                source = rope.source(file_path)
                updated = self._rewrite_runtime_alias_source(
                    source,
                    alias=alias,
                    target_name=target_name,
                )
                if updated == source:
                    continue
                resource = rope.resource(file_path)
                if resource is None:
                    continue
                resource.write(updated)
                changed = True
            elif action == "rewrite_manual_typing_alias":
                if ctx.project_root is None:
                    continue
                violations = tuple(
                    violation
                    for violation in FlextInfraManualTypingAliasDetector.detect_file(
                        ctx
                    )
                    if violation.name in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_manual_typing_alias_violations(
                    project_root=ctx.project_root,
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_compatibility_alias":
                violations = tuple(
                    violation
                    for violation in FlextInfraCompatibilityAliasDetector.detect_file(
                        ctx,
                    )
                    if violation.alias_name in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_compatibility_alias_violations(
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_private_import_bypass":
                violations = tuple(
                    violation
                    for violation in FlextInfraPrivateImportBypassDetector.detect_file(
                        ctx,
                    )
                    if violation.imported_symbol in object_names
                    and violation.symbol_exported
                )
                if not violations:
                    continue
                u.Infra.rewrite_private_import_bypass_violations(
                    rope_project=ctx.rope_project,
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_mro_completeness":
                violations = tuple(
                    violation
                    for violation in FlextInfraMROCompletenessDetector.detect_file(ctx)
                    if violation.facade_class in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_mro_completeness_violations(
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "hoist_inline_import":
                changed = self._apply_hoist_inline_imports(
                    rope=rope,
                    file_path=file_path,
                    object_names=object_names,
                )
            elif action == "manual":
                pass
            if not changed:
                continue
            touched_paths.add(file_path.resolve())
            applied.update(
                self._fix_key(file_path, object_name, action)
                for object_name in object_names
            )
        for candidate in report.removal_candidates:
            apply_result = u.Infra.apply_simple_removal_candidate(
                rope,
                self.root,
                candidate,
                gates=self.dry_run_gate_names,
            )
            if apply_result.failure:
                msg = apply_result.error or (
                    "simple removal apply failed for "
                    f"{candidate.file_path}:{candidate.line} {candidate.object_name}"
                )
                raise RuntimeError(msg)
            if apply_result.unwrap_or(False):
                applied.add(
                    self._fix_key(Path(candidate.file_path), candidate.object_name)
                )
                touched_paths.add(Path(candidate.file_path).resolve())
                touched_paths.update(
                    Path(site.file_path).resolve()
                    for site in (
                        *candidate.test_reference_sites,
                        *candidate.example_reference_sites,
                        *candidate.script_reference_sites,
                    )
                )
        if applied:
            self._ruff_fix_touched_files(touched_paths)
            self._regenerate_inits_via_codegen()
            rope.reload()
        return frozenset(applied)

    def _apply_hoist_inline_imports(
        self,
        *,
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        object_names: set[str],
    ) -> bool:
        """Hoist safe inline imports to module top using rope + AST offsets.

        Only stdlib imports are eligible (no cycle risk); callers already
        filter via ``FlextInfraInlineImportDetector.fix_action_for``.
        """
        resource = rope.resource(file_path)
        if resource is None:
            return False
        ctx = self._detector_context(rope, file_path)
        violations = [
            violation
            for violation in FlextInfraInlineImportDetector.detect_file(ctx)
            if violation.current_import in object_names
            and FlextInfraInlineImportDetector.fix_action_for(
                module_name=violation.module_name,
                is_importlib=violation.is_importlib,
            )
            == "hoist_inline_import"
        ]
        if not violations:
            return False
        try:
            pymodule = u.Infra.get_pymodule(rope.rope_project, resource)
            tree = pymodule.get_ast()
        except Exception:
            return False
        if not isinstance(tree, ast.Module):
            return False
        source = rope.source(file_path)
        lines = source.splitlines(keepends=True)
        line_ranges_to_remove: list[tuple[int, int]] = []
        imports_to_add: list[tuple[str, tuple[str, ...]]] = []
        for violation in violations:
            target = self._find_inline_import_node(tree, violation.line)
            if target is None:
                continue
            start_line = target.lineno
            end_line = getattr(target, "end_lineno", start_line) or start_line
            line_ranges_to_remove.append((start_line, end_line))
            if isinstance(target, ast.Import):
                imports_to_add.extend(("", (alias.name,)) for alias in target.names)
            elif isinstance(target, ast.ImportFrom):
                module_name = target.module or ""
                imports_to_add.append((
                    module_name,
                    tuple(alias.name for alias in target.names),
                ))
        if not line_ranges_to_remove:
            return False
        updated_lines = self._remove_line_ranges(lines, line_ranges_to_remove)
        new_source = "".join(updated_lines)
        try:
            compile(new_source, str(file_path), "exec")
        except SyntaxError:
            return False
        resource.write(new_source)
        for module_name, names in imports_to_add:
            if module_name:
                u.Infra.add_import(
                    rope.rope_project,
                    resource,
                    module_name,
                    names,
                    apply=True,
                )
            else:
                for name in names:
                    top_module = name.split(".")[0]
                    u.Infra.add_import(
                        rope.rope_project,
                        resource,
                        top_module,
                        (top_module,),
                        apply=True,
                    )
        return True

    @staticmethod
    def _find_inline_import_node(
        tree: ast.Module,
        line: int,
    ) -> ast.Import | ast.ImportFrom | None:
        """Find an Import/ImportFrom node at ``line`` inside a function body."""
        for node in ast.walk(tree):
            if not isinstance(node, ast.Import | ast.ImportFrom):
                continue
            if node.lineno != line:
                continue
            parent = _find_parent(tree, node)
            while parent is not None:
                if isinstance(parent, ast.FunctionDef | ast.AsyncFunctionDef):
                    return node
                parent = _find_parent(tree, parent)
        return None

    @staticmethod
    def _remove_line_ranges(
        lines: list[str],
        ranges: list[tuple[int, int]],
    ) -> list[str]:
        """Remove 1-based inclusive line ranges, returning the updated line list."""
        drop: set[int] = set()
        for start, end in ranges:
            drop.update(range(start, end + 1))
        return [line for index, line in enumerate(lines, start=1) if index not in drop]

    def _regenerate_inits_via_codegen(self) -> None:
        """Regenerate every ``__init__.py`` via the canonical lazy-init service."""
        FlextInfraCodegenLazyInit(workspace=self.root).generate_inits(
            check_only=False,
        )


def _find_parent(tree: ast.AST, target: ast.AST) -> ast.AST | None:
    """Return the parent AST node of ``target`` within ``tree``."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if child is target:
                return parent
    return None


__all__: list[str] = ["FlextInfraRefactorCensusApplyMixin"]
