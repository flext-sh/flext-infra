"""Enforcement phase methods for namespace enforcer."""

from __future__ import annotations

import difflib
from collections.abc import Callable, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraClassPlacementDetector,
    FlextInfraCompatibilityAliasDetector,
    FlextInfraCyclicImportDetector,
    FlextInfraFutureAnnotationsDetector,
    FlextInfraImportAliasDetector,
    FlextInfraInternalImportDetector,
    FlextInfraLooseObjectDetector,
    FlextInfraManualProtocolDetector,
    FlextInfraManualTypingAliasDetector,
    FlextInfraMROCompletenessDetector,
    FlextInfraNamespaceFacadeScanner,
    FlextInfraNamespaceSourceDetector,
    FlextInfraRuntimeAliasDetector,
    c,
    m,
    t,
    u,
)


class FlextInfraNamespaceEnforcerPhasesMixin:
    """Project enforcement and diff methods for namespace enforcer."""

    _workspace_root: Path
    _rope_project: t.Infra.RopeProject

    def _resolve_project_roots(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> Sequence[Path]:
        msg = "_resolve_project_roots must be provided by the concrete enforcer"
        raise NotImplementedError(msg)

    def _detect_and_apply[V](
        self,
        *,
        py_files: Sequence[Path],
        detect_fn: Callable[[Path], Sequence[V]],
        rewrite_fn: Callable[[MutableSequence[V]], None] | None,
        apply: bool,
    ) -> MutableSequence[V]:
        _ = self, py_files, detect_fn, rewrite_fn, apply
        msg = "_detect_and_apply must be provided by the concrete enforcer"
        raise NotImplementedError(msg)

    def enforce(
        self,
        *,
        apply: bool = False,
        project_names: t.StrSequence | None = None,
    ) -> m.Infra.WorkspaceEnforcementReport:
        _ = apply, project_names
        msg = "enforce must be provided by the concrete enforcer"
        raise NotImplementedError(msg)

    def _enforce_project(
        self,
        *,
        project_root: Path,
        project_name: str,
        apply: bool,
    ) -> m.Infra.ProjectEnforcementReport:
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] = []
        facade_statuses = self._scan_facades(
            project_root=project_root,
            project_name=project_name,
            rope_project=self._rope_project,
            parse_failures=parse_failures,
            apply=apply,
            workspace_root=self._workspace_root,
        )
        py_files = self._collect_py_files(project_root=project_root)
        package_name = u.Infra.discover_project_package_name(project_root=project_root)
        loose_objects = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraLooseObjectDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    project_name=project_name,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=None,
            apply=apply,
        )
        import_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraImportAliasDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda _vs: u.Infra.rewrite_import_violations(
                py_files=py_files,
                project_package=package_name,
            ),
            apply=apply,
        )
        namespace_source_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraNamespaceSourceDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    project_name=project_name,
                    project_root=project_root,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda _vs: None,
            apply=apply,
        )
        cyclic_imports = FlextInfraCyclicImportDetector.scan_project(
            project_root=project_root,
            rope_project=self._rope_project,
            _parse_failures=parse_failures,
        )
        internal_import_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraInternalImportDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=None,
            apply=apply,
        )
        runtime_alias_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraRuntimeAliasDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    project_name=project_name,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda _vs: u.Infra.rewrite_runtime_alias_violations(
                py_files=py_files,
            ),
            apply=apply,
        )
        future_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraFutureAnnotationsDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda _vs: u.Infra.rewrite_missing_future_annotations(
                py_files=py_files,
            ),
            apply=apply,
        )
        manual_protocol_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraManualProtocolDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda vs: u.Infra.rewrite_manual_protocol_violations(
                project_root=project_root,
                py_files=py_files,
                violations=vs,
            ),
            apply=apply,
        )
        manual_typing_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraManualTypingAliasDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda vs: u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                violations=vs,
                parse_failures=parse_failures,
            ),
            apply=apply,
        )
        compatibility_alias_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraCompatibilityAliasDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda vs: u.Infra.rewrite_compatibility_alias_violations(
                violations=vs,
                parse_failures=parse_failures,
            ),
            apply=apply,
        )
        class_placement_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraClassPlacementDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    rope_project=self._rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=None,
            apply=apply,
        )
        mro_completeness_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraMROCompletenessDetector.detect_file(
                m.Infra.DetectorContext(
                    file_path=f,
                    parse_failures=parse_failures,
                    rope_project=self._rope_project,
                ),
            ),
            rewrite_fn=lambda vs: u.Infra.rewrite_mro_completeness_violations(
                violations=vs,
                parse_failures=parse_failures,
            ),
            apply=apply,
        )
        return m.Infra.ProjectEnforcementReport(
            project=project_name,
            project_root=str(project_root),
            facade_statuses=facade_statuses,
            loose_objects=list(loose_objects),
            import_violations=list(import_violations),
            namespace_source_violations=list(namespace_source_violations),
            internal_import_violations=list(internal_import_violations),
            manual_protocol_violations=list(manual_protocol_violations),
            cyclic_imports=list(cyclic_imports),
            runtime_alias_violations=list(runtime_alias_violations),
            future_violations=list(future_violations),
            manual_typing_violations=list(manual_typing_violations),
            compatibility_alias_violations=list(compatibility_alias_violations),
            class_placement_violations=list(class_placement_violations),
            mro_completeness_violations=list(mro_completeness_violations),
            parse_failures=list(parse_failures),
            files_scanned=len(py_files),
        )

    @staticmethod
    def _scan_facades(
        *,
        project_root: Path,
        project_name: str,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation],
        apply: bool,
        workspace_root: Path,
    ) -> Sequence[m.Infra.FacadeStatus]:
        """Scan facades and optionally create missing ones."""
        facade_statuses = FlextInfraNamespaceFacadeScanner.scan_project(
            project_root=project_root,
            project_name=project_name,
            rope_project=rope_project,
            parse_failures=parse_failures,
        )
        if not apply:
            return facade_statuses
        u.Infra.ensure_missing_facades(
            project_root=project_root,
            project_name=project_name,
            facade_statuses=facade_statuses,
            workspace_root=workspace_root,
        )
        return FlextInfraNamespaceFacadeScanner.scan_project(
            project_root=project_root,
            project_name=project_name,
            rope_project=rope_project,
            parse_failures=parse_failures,
        )

    @staticmethod
    def _collect_py_files(*, project_root: Path) -> Sequence[Path]:
        """Collect Python files for scanning."""
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_root,
            project_roots=[project_root],
            include_dynamic_dirs=u.Infra.namespace_include_dynamic_dirs(project_root),
            src_dirs=u.Infra.namespace_scan_dirs(project_root),
        )
        if py_files_result.is_failure:
            return []
        return py_files_result.value

    def diff(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> str:
        """Run enforce with apply in diff mode: apply, capture diff, restore originals.

        Returns:
            Unified diff string showing all changes that --apply would make.

        """
        project_roots = self._resolve_project_roots(project_names=project_names)
        all_py_files: MutableSequence[Path] = []
        for project_root in project_roots:
            all_py_files.extend(self._collect_py_files(project_root=project_root))
        snapshots: MutableMapping[Path, str] = {}
        for py_file in all_py_files:
            if py_file.is_file():
                snapshots[py_file] = py_file.read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
        try:
            self.enforce(apply=True, project_names=project_names)
        finally:
            diff_lines: MutableSequence[str] = []
            for py_file, original in snapshots.items():
                if not py_file.is_file():
                    continue
                modified = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
                if modified != original:
                    rel = py_file.relative_to(self._workspace_root)
                    diff_lines.extend(
                        difflib.unified_diff(
                            original.splitlines(keepends=True),
                            modified.splitlines(keepends=True),
                            fromfile=f"a/{rel}",
                            tofile=f"b/{rel}",
                        ),
                    )
                _ = py_file.write_text(original, encoding=c.Infra.Encoding.DEFAULT)
            for project_root in project_roots:
                for py_file in self._collect_py_files(project_root=project_root):
                    if py_file not in snapshots and py_file.is_file():
                        rel = py_file.relative_to(self._workspace_root)
                        content = py_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
                        diff_lines.extend(
                            difflib.unified_diff(
                                [],
                                content.splitlines(keepends=True),
                                fromfile="/dev/null",
                                tofile=f"b/{rel}",
                            ),
                        )
                        py_file.unlink()
        return "".join(diff_lines)


__all__ = ["FlextInfraNamespaceEnforcerPhasesMixin"]
