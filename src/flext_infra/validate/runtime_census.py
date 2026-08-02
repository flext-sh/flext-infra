"""Runtime Beartype census validator.

Imports every ``flext_*`` module in selected projects and runs
``u.check()`` against every locally-defined class.
Aggregates violations by rule/project into the standard validation report.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Annotated, override

from flext_infra import c, config, m, p, r, s, t, u


class FlextInfraRuntimeCensusValidator(s[bool]):
    """Post-import runtime enforcement census across workspace projects."""

    project_filter: Annotated[
        str | None, m.Field(description="Project filter (comma-separated)")
    ] = None

    def _selected_projects(
        self, projects: t.SequenceOf[p.Infra.ProjectInfo]
    ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
        """Resolve every requested project name against discovered projects."""
        if self.project_filter is None:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(tuple(projects))
        selected = {
            item.strip() for item in self.project_filter.split(",") if item.strip()
        }
        discovered_names = {project.name for project in projects}
        missing = sorted(selected - discovered_names)
        if missing:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].fail(
                f"unknown runtime census projects: {', '.join(missing)}"
            )
        return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(
            tuple(project for project in projects if project.name in selected)
        )

    @staticmethod
    def _package_name_for_project(project: p.Infra.ProjectInfo) -> p.Result[str]:
        """Return the package identity already owned by project discovery."""
        if not project.package_name:
            return r[str].fail(
                f"project discovery produced no package identity: {project.name}"
            )
        return r[str].ok(project.package_name)

    @staticmethod
    def _is_local_class(klass: type, module_name: str) -> bool:
        """Return True when ``klass`` is defined in ``module_name`` (not imported)."""
        return getattr(klass, "__module__", "") == module_name

    @staticmethod
    def _walk_modules(package_name: str) -> p.Result[t.SequenceOf[str]]:
        """Return every importable module or one typed discovery failure."""
        try:
            package = importlib.import_module(package_name)
        except Exception as exc:
            return r[t.SequenceOf[str]].fail_op(
                f"import runtime package {package_name}", exc
            )
        prefix = package.__name__ + "."
        modules: list[str] = [package.__name__]
        walk_failures: list[str] = []
        try:
            for _, modname, _ in pkgutil.walk_packages(
                package.__path__, prefix=prefix, onerror=walk_failures.append
            ):
                modules.append(modname)
        except Exception as exc:
            return r[t.SequenceOf[str]].fail_op(
                f"walk runtime package {package_name}", exc
            )
        if walk_failures:
            return r[t.SequenceOf[str]].fail(
                f"runtime package discovery failed: {', '.join(walk_failures)}"
            )
        return r[t.SequenceOf[str]].ok(tuple(modules))

    def _check_module(self, module_name: str) -> p.Result[m.Infra.ValidationReport]:
        """Import one module and run runtime enforcement on its local classes."""
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            return r[m.Infra.ValidationReport].fail_op(
                f"import runtime module {module_name}", exc
            )
        violations: list[str] = []
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if not self._is_local_class(obj, module.__name__):
                continue
            try:
                report = u.check(obj)
            except Exception as exc:
                violations.append(
                    f"{module_name}:{obj.__qualname__}: check raised: {exc}"
                )
                continue
            for violation in report.violations:
                file_part = f"{violation.file_path}:" if violation.file_path else ""
                line_part = f"{violation.line_number}:" if violation.line_number else ""
                rule_part = f" [{violation.rule_id}]" if violation.rule_id else ""
                violations.append(
                    f"{file_part}{line_part}{obj.__qualname__}{rule_part}: "
                    f"{violation.message}"
                )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=not violations,
                violations=tuple(violations),
                summary=(
                    f"{module_name}: {len(violations)} runtime violation(s)"
                    if violations
                    else f"{module_name}: clean"
                ),
            )
        )

    def _project_report(self, project: p.Infra.ProjectInfo) -> m.Infra.ValidationReport:
        """Run the runtime census for one project and return a merged report."""
        package_result = self._package_name_for_project(project)
        if package_result.failure:
            error = package_result.error or f"{project.name}: package identity failed"
            return m.Infra.ValidationReport(
                passed=False,
                violations=(error,),
                summary=f"{project.name}: package identity failed",
            )
        package_name = package_result.value
        module_names_result = self._walk_modules(package_name)
        if module_names_result.failure:
            error = module_names_result.error or (
                f"{project.name}: runtime module discovery failed"
            )
            return m.Infra.ValidationReport(
                passed=False,
                violations=(error,),
                summary=f"{project.name}: runtime module discovery failed",
            )
        real_modules = list(module_names_result.value)
        if self.target_module is not None:
            real_modules = [
                name
                for name in real_modules
                if name == self.target_module
                or name.startswith(self.target_module + ".")
            ]
            if not real_modules:
                return m.Infra.ValidationReport(
                    passed=False,
                    violations=(
                        f"{project.name}: unknown runtime target module "
                        f"{self.target_module}",
                    ),
                    summary=f"{project.name}: runtime target module not found",
                )
        real_modules = [
            name
            for name in real_modules
            if not frozenset(config.Infra.codegen.source_scan_ignored).intersection(
                name.split(".")
            )
        ]
        if not real_modules:
            reason = (
                f"{project.name}: runtime target module {self.target_module} "
                "is excluded by source scan policy"
                if self.target_module is not None
                else f"{project.name}: runtime module selection is empty after source scan policy"
            )
            return m.Infra.ValidationReport(
                passed=False,
                violations=(reason,),
                summary=f"{project.name}: no governed runtime modules",
            )
        all_reports: list[m.Infra.ValidationReport] = []
        for module_name in real_modules:
            checked = self._check_module(module_name)
            if checked.failure:
                error = checked.error or f"{module_name}: runtime check failed"
                all_reports.append(
                    m.Infra.ValidationReport(
                        passed=False,
                        violations=(error,),
                        summary=f"{module_name}: runtime check failed",
                    )
                )
                continue
            all_reports.append(checked.value)
        merged_violations = tuple(
            violation for report in all_reports for violation in report.violations
        )
        passed = not merged_violations
        summary = (
            f"{project.name}: {len(merged_violations)} runtime violation(s)"
            if not passed
            else f"{project.name}: runtime census passed ({len(real_modules)} module(s))"
        )
        return m.Infra.ValidationReport(
            passed=passed, violations=merged_violations, summary=summary
        )

    def build_report(self) -> p.Result[m.Infra.ValidationReport]:
        """Build one validation report for the selected workspace projects."""
        projects_result = u.Infra.projects(self.workspace_root)
        if projects_result.failure:
            return r[m.Infra.ValidationReport].fail(
                projects_result.error or "project discovery failed"
            )
        selected_result = self._selected_projects(projects_result.value)
        if selected_result.failure:
            return r[m.Infra.ValidationReport].fail(
                selected_result.error or "runtime census project selection failed"
            )
        projects = selected_result.value
        if not projects:
            return r[m.Infra.ValidationReport].fail(
                "runtime census project selection is empty"
            )
        merged_violations: list[str] = []
        for project in projects:
            report = self._project_report(project)
            merged_violations.extend(report.violations)
        passed = not merged_violations
        summary = (
            "runtime census passed"
            if passed
            else f"runtime census found {len(merged_violations)} violation(s)"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed, violations=tuple(merged_violations), summary=summary
            )
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute runtime census and collapse the report to ``r[bool]``."""
        report_result = self.build_report()
        if report_result.failure:
            return r[bool].fail(report_result.error or "runtime census failed")
        report = report_result.value
        if report.passed:
            return r[bool].ok(True)
        details = (
            report.model_dump_json()
            if self.output_format == c.Cli.OutputFormats.JSON
            else "\n".join([report.summary, *report.violations])
        )
        return r[bool].fail(details)


__all__: list[str] = ["FlextInfraRuntimeCensusValidator"]
