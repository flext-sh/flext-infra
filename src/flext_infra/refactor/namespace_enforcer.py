"""Automated namespace enforcement orchestration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import (
    ClassPlacementDetector,
    CompatibilityAliasDetector,
    CyclicImportDetector,
    FutureAnnotationsDetector,
    ImportAliasDetector,
    InternalImportDetector,
    LooseObjectDetector,
    ManualProtocolDetector,
    ManualTypingAliasDetector,
    MROCompletenessDetector,
    NamespaceFacadeScanner,
    NamespaceSourceDetector,
    RuntimeAliasDetector,
    c,
    m,
    u,
)


class FlextInfraNamespaceEnforcer:
    """Orchestrate namespace enforcement across a workspace."""

    def __init__(self, *, workspace_root: Path) -> None:
        """Initialize with the workspace root path."""
        super().__init__()
        self._workspace_root = workspace_root.resolve()

    def enforce(
        self,
        *,
        apply: bool = False,
    ) -> m.Infra.WorkspaceEnforcementReport:
        """Run namespace enforcement across all projects in the workspace."""
        project_roots = u.Infra.discover_project_roots(
            workspace_root=self._workspace_root,
        )
        project_reports: Sequence[m.Infra.ProjectEnforcementReport] = []
        total_missing = 0
        total_loose = 0
        total_import_v = 0
        total_internal_import_v = 0
        total_cyclic = 0
        total_alias_v = 0
        total_future_v = 0
        total_manual_protocol_v = 0
        total_manual_typing_v = 0
        total_compat_alias_v = 0
        total_class_placement_v = 0
        total_mro_completeness_v = 0
        total_namespace_source_v = 0
        total_parse_failures = 0
        total_files = 0
        for project_root in project_roots:
            project_name = project_root.name
            report = self._enforce_project(
                project_root=project_root,
                project_name=project_name,
                apply=apply,
            )
            project_reports.append(report)
            total_missing += sum(1 for s in report.facade_statuses if not s.exists)
            total_loose += len(report.loose_objects)
            total_import_v += len(report.import_violations)
            total_internal_import_v += len(report.internal_import_violations)
            total_cyclic += len(report.cyclic_imports)
            total_alias_v += len(report.runtime_alias_violations)
            total_future_v += len(report.future_violations)
            total_manual_protocol_v += len(report.manual_protocol_violations)
            total_manual_typing_v += len(report.manual_typing_violations)
            total_compat_alias_v += len(report.compatibility_alias_violations)
            total_class_placement_v += len(report.class_placement_violations)
            total_mro_completeness_v += len(report.mro_completeness_violations)
            total_namespace_source_v += len(report.namespace_source_violations)
            total_parse_failures += len(report.parse_failures)
            total_files += report.files_scanned
        return m.Infra.WorkspaceEnforcementReport.create(
            workspace=str(self._workspace_root),
            projects=project_reports,
            total_facades_missing=total_missing,
            total_loose_objects=total_loose,
            total_import_violations=total_import_v,
            total_namespace_source_violations=total_namespace_source_v,
            total_internal_import_violations=total_internal_import_v,
            total_cyclic_imports=total_cyclic,
            total_runtime_alias_violations=total_alias_v,
            total_future_violations=total_future_v,
            total_manual_protocol_violations=total_manual_protocol_v,
            total_manual_typing_violations=total_manual_typing_v,
            total_compatibility_alias_violations=total_compat_alias_v,
            total_class_placement_violations=total_class_placement_v,
            total_mro_completeness_violations=total_mro_completeness_v,
            total_parse_failures=total_parse_failures,
            total_files_scanned=total_files,
        )

    def _enforce_project(
        self,
        *,
        project_root: Path,
        project_name: str,
        apply: bool,
    ) -> m.Infra.ProjectEnforcementReport:
        parse_failures: Sequence[m.Infra.ParseFailureViolation] = []
        facade_statuses = NamespaceFacadeScanner.scan_project(
            project_root=project_root,
            project_name=project_name,
            parse_failures=parse_failures,
        )
        if apply:
            u.Infra.namespace_ensure_missing_facades(
                project_root=project_root,
                project_name=project_name,
                facade_statuses=facade_statuses,
            )
            facade_statuses = NamespaceFacadeScanner.scan_project(
                project_root=project_root,
                project_name=project_name,
                parse_failures=parse_failures,
            )
        py_files_result = u.Infra.iter_python_files(
            workspace_root=project_root,
            project_roots=[project_root],
            src_dirs=frozenset(c.Infra.MRO_SCAN_DIRECTORIES),
        )
        py_files = [] if py_files_result.is_failure else py_files_result.value
        loose_objects: Sequence[m.Infra.LooseObjectViolation] = []
        for py_file in py_files:
            loose_objects.extend(
                LooseObjectDetector.detect_file(
                    file_path=py_file,
                    project_name=project_name,
                    parse_failures=parse_failures,
                ),
            )
        import_violations: Sequence[m.Infra.ImportAliasViolation] = []
        for py_file in py_files:
            import_violations.extend(
                ImportAliasDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(import_violations) > 0:
            package_name = NamespaceSourceDetector.discover_project_package_name(
                project_root=project_root,
            )
            u.Infra.namespace_rewrite_import_violations(
                py_files=py_files,
                project_package=package_name,
            )
            import_violations = []
            for py_file in py_files:
                import_violations.extend(
                    ImportAliasDetector.detect_file(
                        file_path=py_file,
                        parse_failures=parse_failures,
                    ),
                )
        namespace_source_violations: Sequence[m.Infra.NamespaceSourceViolation] = []
        for py_file in py_files:
            namespace_source_violations.extend(
                NamespaceSourceDetector.detect_file(
                    file_path=py_file,
                    project_name=project_name,
                    project_root=project_root,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(namespace_source_violations) > 0:
            namespace_source_violations = []
            for py_file in py_files:
                namespace_source_violations.extend(
                    NamespaceSourceDetector.detect_file(
                        file_path=py_file,
                        project_name=project_name,
                        project_root=project_root,
                        parse_failures=parse_failures,
                    ),
                )
        cyclic_imports = CyclicImportDetector.scan_project(
            project_root=project_root,
            _parse_failures=parse_failures,
        )
        internal_import_violations: Sequence[m.Infra.InternalImportViolation] = []
        for py_file in py_files:
            internal_import_violations.extend(
                InternalImportDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        runtime_alias_violations: Sequence[m.Infra.RuntimeAliasViolation] = []
        for py_file in py_files:
            runtime_alias_violations.extend(
                RuntimeAliasDetector.detect_file(
                    file_path=py_file,
                    project_name=project_name,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(runtime_alias_violations) > 0:
            u.Infra.namespace_rewrite_runtime_alias_violations(
                py_files=py_files,
            )
            runtime_alias_violations = []
            for py_file in py_files:
                runtime_alias_violations.extend(
                    RuntimeAliasDetector.detect_file(
                        file_path=py_file,
                        project_name=project_name,
                        parse_failures=parse_failures,
                    ),
                )
        future_violations: Sequence[m.Infra.FutureAnnotationsViolation] = []
        for py_file in py_files:
            future_violations.extend(
                FutureAnnotationsDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(future_violations) > 0:
            u.Infra.namespace_rewrite_missing_future_annotations(
                py_files=py_files,
            )
            future_violations = []
            for py_file in py_files:
                future_violations.extend(
                    FutureAnnotationsDetector.detect_file(
                        file_path=py_file,
                        parse_failures=parse_failures,
                    ),
                )
        manual_protocol_violations: Sequence[m.Infra.ManualProtocolViolation] = []
        for py_file in py_files:
            manual_protocol_violations.extend(
                ManualProtocolDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(manual_protocol_violations) > 0:
            u.Infra.namespace_rewrite_manual_protocol_violations(
                project_root=project_root,
                py_files=py_files,
                violations=manual_protocol_violations,
            )
            manual_protocol_violations = []
            for py_file in py_files:
                manual_protocol_violations.extend(
                    ManualProtocolDetector.detect_file(
                        file_path=py_file,
                        parse_failures=parse_failures,
                    ),
                )
        manual_typing_violations: Sequence[m.Infra.ManualTypingAliasViolation] = []
        for py_file in py_files:
            manual_typing_violations.extend(
                ManualTypingAliasDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(manual_typing_violations) > 0:
            u.Infra.namespace_rewrite_manual_typing_alias_violations(
                project_root=project_root,
                violations=manual_typing_violations,
                parse_failures=parse_failures,
            )
            manual_typing_violations = []
            for py_file in py_files:
                manual_typing_violations.extend(
                    ManualTypingAliasDetector.detect_file(
                        file_path=py_file,
                        parse_failures=parse_failures,
                    ),
                )
        compatibility_alias_violations: Sequence[
            m.Infra.CompatibilityAliasViolation
        ] = []
        for py_file in py_files:
            compatibility_alias_violations.extend(
                CompatibilityAliasDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(compatibility_alias_violations) > 0:
            u.Infra.namespace_rewrite_compatibility_alias_violations(
                violations=compatibility_alias_violations,
                parse_failures=parse_failures,
            )
            compatibility_alias_violations = []
            for py_file in py_files:
                compatibility_alias_violations.extend(
                    CompatibilityAliasDetector.detect_file(
                        file_path=py_file,
                        parse_failures=parse_failures,
                    ),
                )
        class_placement_violations: Sequence[m.Infra.ClassPlacementViolation] = []
        for py_file in py_files:
            class_placement_violations.extend(
                ClassPlacementDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        mro_completeness_violations: Sequence[m.Infra.MROCompletenessViolation] = []
        for py_file in py_files:
            mro_completeness_violations.extend(
                MROCompletenessDetector.detect_file(
                    file_path=py_file,
                    parse_failures=parse_failures,
                ),
            )
        if apply and len(mro_completeness_violations) > 0:
            u.Infra.namespace_rewrite_mro_completeness_violations(
                violations=mro_completeness_violations,
                parse_failures=parse_failures,
            )
            mro_completeness_violations = []
            for py_file in py_files:
                mro_completeness_violations.extend(
                    MROCompletenessDetector.detect_file(
                        file_path=py_file,
                        parse_failures=parse_failures,
                    ),
                )
        return m.Infra.ProjectEnforcementReport.create(
            project=project_name,
            project_root=str(project_root),
            facade_statuses=facade_statuses,
            loose_objects=loose_objects,
            import_violations=import_violations,
            namespace_source_violations=namespace_source_violations,
            internal_import_violations=internal_import_violations,
            manual_protocol_violations=manual_protocol_violations,
            cyclic_imports=cyclic_imports,
            runtime_alias_violations=runtime_alias_violations,
            future_violations=future_violations,
            manual_typing_violations=manual_typing_violations,
            compatibility_alias_violations=compatibility_alias_violations,
            class_placement_violations=class_placement_violations,
            mro_completeness_violations=mro_completeness_violations,
            parse_failures=parse_failures,
            files_scanned=len(py_files),
        )

    @staticmethod
    def render_text(
        report: m.Infra.WorkspaceEnforcementReport,
    ) -> str:
        """Render a workspace enforcement report as plain text."""
        return u.Infra.render_namespace_enforcement_report(
            report,
        )


__all__ = ["FlextInfraNamespaceEnforcer"]
