"""Guard 8 — metadata-discipline validator.

Enforces that pyproject metadata parsing is centralized. Runtime imports of
``tomllib`` are forbidden outside allowlisted metadata readers/writers.

This validator is ROPE-backed (no raw AST/CST parsing) and plugs into the
existing ``flext-infra validate`` command hierarchy.
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import override

from flext_infra import c, m, p, r, s, t, u


class FlextInfraValidateMetadataDiscipline(s[bool]):
    """Detect rogue ``tomllib`` imports outside canonical metadata modules."""

    def build_report(
        self,
        workspace_root: Path,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Scan workspace for metadata-discipline violations."""
        try:
            violations = self._collect_violations(workspace_root)
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail(
                f"metadata-discipline scan failed: {exc}",
            )
        passed = not violations
        summary = (
            "metadata-discipline respected (tomllib imports centralized)"
            if passed
            else f"{len(violations)} metadata-discipline violation(s)"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=list(violations),
                summary=summary,
            ),
        )

    def _collect_violations(
        self,
        workspace_root: Path,
    ) -> Sequence[str]:
        """Traverse one rope project and accumulate rogue tomllib imports."""
        violations: MutableSequence[str] = []
        with u.Infra.open_project(workspace_root) as project:
            for resource in u.Infra.python_resources(project):
                file_path = u.Infra.resource_file_path(
                    project,
                    resource,
                )
                if (
                    file_path is None
                    or not self._is_target_scope(file_path)
                    or self._is_allowlisted(file_path)
                ):
                    continue
                module_imports = u.Infra.get_module_imports(
                    project,
                    resource,
                )
                if module_imports is None:
                    continue
                violations.extend(
                    self._violations_for_module(file_path, module_imports),
                )
        return tuple(violations)

    def _is_allowlisted(self, file_path: Path) -> bool:
        """Return True when file path is in canonical metadata reader set."""
        posix = file_path.as_posix()
        return any(
            marker in posix for marker in c.Infra.METADATA_ALLOWLIST_PATH_MARKERS
        )

    def _is_target_scope(self, file_path: Path) -> bool:
        """Return True when path belongs to metadata-discipline enforcement scope."""
        posix = file_path.as_posix()
        return any(marker in posix for marker in c.Infra.METADATA_TARGET_SCOPE_MARKERS)

    def _violations_for_module(
        self,
        file_path: Path,
        module_imports: t.Infra.RopeModuleImports,
    ) -> Sequence[str]:
        """Return violation strings for one module import set via Rope boundary types."""
        out: MutableSequence[str] = []
        for import_statement in u.Infra.import_statements(module_imports):
            module_name = u.Infra.import_statement_module_name(import_statement)
            if module_name is not None:
                imported = module_name.split(".", maxsplit=1)[0] if module_name else ""
                if imported in c.Infra.METADATA_TOMLLIB_MODULES:
                    out.append(
                        f"{file_path}: direct metadata parser import {module_name!r} "
                        "— route pyproject reads through canonical metadata utilities"
                    )
                continue
            for imported_name, _alias in u.Infra.import_statement_names_and_aliases(
                import_statement,
            ):
                imported = imported_name.split(".", maxsplit=1)[0]
                if imported in c.Infra.METADATA_TOMLLIB_MODULES:
                    out.append(
                        f"{file_path}: direct metadata parser import {imported_name!r} "
                        "— route pyproject reads through canonical metadata utilities"
                    )
        return tuple(out)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute metadata-discipline validation using service workspace root."""
        report_result = self.build_report(self.workspace_root)
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "metadata-discipline validation failed",
            )
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)


__all__: t.StrSequence = ["FlextInfraValidateMetadataDiscipline"]
