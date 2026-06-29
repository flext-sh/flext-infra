"""Per-project namespace enforcement — extracted concern of the namespace enforcer."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

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
    FlextInfraNamespaceSourceDetector,
    FlextInfraRuntimeAliasDetector,
    m,
    t,
    u,
)


class FlextInfraNamespaceEnforcerProjectMixin:
    """Run every detector over one project and build its enforcement report.

    Composed alongside the phases/orchestration mixins into the concrete
    enforcer; ``self`` provides facade scan / file-collection / detect-apply
    helpers through the concrete's MRO.
    """

    if TYPE_CHECKING:
        _workspace_root: Path

        def _detect_and_apply[V](
            self,
            *,
            py_files: t.SequenceOf[Path],
            detect_fn: Callable[[Path], t.SequenceOf[V]],
            rewrite_fn: Callable[[t.MutableSequenceOf[V]], None] | None,
            apply: bool,
        ) -> t.MutableSequenceOf[V]: ...

        @staticmethod
        def _scan_facades(
            *,
            project: tuple[Path, str],
            rope_project: t.Infra.RopeProject,
            apply: bool,
            workspace_root: Path,
        ) -> t.SequenceOf[m.Infra.FacadeStatus]: ...

        @staticmethod
        def _collect_py_files(*, project_root: Path) -> t.SequenceOf[Path]: ...

    def _enforce_project(
        self,
        *,
        project_root: Path,
        project_name: str,
        apply: bool,
        gates: t.StrSequence | None = None,
    ) -> m.Infra.ProjectEnforcementReport:
        """Enforce project."""
        with u.Infra.open_project(project_root) as rope_project:
            return self._enforce_project_with_rope(
                project_root=project_root,
                project_name=project_name,
                apply=apply,
                gates=gates,
                rope_project=rope_project,
            )

    @staticmethod
    def _detector_context(
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation],
        project_name: str = "",
        project_root: Path | None = None,
    ) -> m.Infra.DetectorContext:
        """Build the canonical detector context for one file."""
        return m.Infra.DetectorContext(
            file_path=file_path,
            rope_project=rope_project,
            parse_failures=parse_failures,
            project_name=project_name,
            project_root=project_root,
        )

    def _enforce_project_with_rope(
        self,
        *,
        project_root: Path,
        project_name: str,
        apply: bool,
        gates: t.StrSequence | None,
        rope_project: t.Infra.RopeProject,
    ) -> m.Infra.ProjectEnforcementReport:
        """Enforce project using the Rope project scoped to ``project_root``."""
        parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation] = []
        facade_statuses = self._scan_facades(
            project=(project_root, project_name),
            rope_project=rope_project,
            apply=apply,
            workspace_root=self._workspace_root,
        )
        py_files = self._collect_py_files(project_root=project_root)
        project_layout = u.Infra.layout(project_root)
        package_name = project_layout.package_name if project_layout is not None else ""

        loose_objects = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraLooseObjectDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_name=project_name,
                ),
            ),
            rewrite_fn=None,
            apply=apply,
        )
        import_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraImportAliasDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
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
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_name=project_name,
                    project_root=project_root,
                ),
            ),
            rewrite_fn=lambda _vs: None,
            apply=apply,
        )
        cyclic_imports = FlextInfraCyclicImportDetector.scan_project(
            project_root=project_root,
            rope_project=rope_project,
            _parse_failures=parse_failures,
        )
        internal_import_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraInternalImportDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=None,
            apply=apply,
        )
        runtime_alias_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraRuntimeAliasDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                    project_name=project_name,
                ),
            ),
            rewrite_fn=lambda _vs: u.Infra.rewrite_runtime_alias_violations(
                py_files=py_files,
                gates=gates,
            ),
            apply=apply,
        )
        future_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraFutureAnnotationsDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
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
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda vs: u.Infra.rewrite_manual_protocol_violations(
                project_root=project_root,
                py_files=py_files,
                violations=vs,
                gates=gates,
            ),
            apply=apply,
        )
        manual_typing_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraManualTypingAliasDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
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
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=lambda vs: u.Infra.rewrite_compatibility_alias_violations(
                violations=vs,
                parse_failures=parse_failures,
                gates=gates,
            ),
            apply=apply,
        )
        class_placement_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraClassPlacementDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
                ),
            ),
            rewrite_fn=None,
            apply=apply,
        )
        mro_completeness_violations = self._detect_and_apply(
            py_files=py_files,
            detect_fn=lambda f: FlextInfraMROCompletenessDetector.detect_file(
                self._detector_context(
                    file_path=f,
                    rope_project=rope_project,
                    parse_failures=parse_failures,
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


__all__: list[str] = ["FlextInfraNamespaceEnforcerProjectMixin"]
