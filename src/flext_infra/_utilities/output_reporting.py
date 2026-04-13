"""Report rendering mixins for output utility."""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence

from flext_infra import c, m


class FlextInfraUtilitiesOutputReporting:
    """Mixin for structured report rendering (namespace enforcement, census)."""

    _MAX_RENDERED_CENSUS_VIOLATIONS: int = 10

    @staticmethod
    def _add_violation_section[V](
        lines: MutableSequence[str],
        violations: Sequence[V],
        label: str,
        formatter: Callable[[V], str],
        max_items: int,
    ) -> None:
        """Render a truncated violation section with count header."""
        if not violations:
            return
        lines.append(f"  {label}: {len(violations)}")
        lines.extend(formatter(v) for v in violations[:max_items])
        if len(violations) > max_items:
            lines.append(f"    ... and {len(violations) - max_items} more")

    @staticmethod
    def render_namespace_enforcement_report(
        report: m.Infra.WorkspaceEnforcementReport,
    ) -> str:
        """Render a human-readable namespace enforcement report."""
        lines: MutableSequence[str] = [
            f"Workspace: {report.workspace}",
            f"Projects scanned: {len(report.projects)}",
            f"Files scanned: {report.total_files_scanned}",
            f"Missing facades: {report.total_facades_missing}",
            f"Loose objects: {report.total_loose_objects}",
            f"Import violations: {report.total_import_violations}",
            f"Internal imports: {report.total_internal_import_violations}",
            f"Cyclic imports: {report.total_cyclic_imports}",
            f"Runtime alias violations: {report.total_runtime_alias_violations}",
            f"Missing __future__: {report.total_future_violations}",
            f"Manual protocols: {report.total_manual_protocol_violations}",
            f"Manual typing aliases: {report.total_manual_typing_violations}",
            f"Compatibility aliases: {report.total_compatibility_alias_violations}",
            f"Class placement violations: {report.total_class_placement_violations}",
            f"MRO completeness violations: {report.total_mro_completeness_violations}",
            f"Namespace source violations: {report.total_namespace_source_violations}",
            f"Parse failures: {report.total_parse_failures}",
            "",
        ]
        for proj in report.projects:
            if not proj.has_violations:
                continue
            lines.append(f"--- {proj.project} ---")
            missing = [s for s in proj.facade_statuses if not s.exists]
            if missing:
                lines.append(
                    "  Missing facades: "
                    + ", ".join(
                        f"{s.family} ({c.Infra.FAMILY_SUFFIXES[s.family]})"
                        for s in missing
                    ),
                )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.loose_objects,
                "Loose objects",
                lambda obj: (
                    f"    {obj.file}:{obj.line} {obj.kind} '{obj.name}' -> {obj.suggestion}"
                ),
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.import_violations,
                "Import violations",
                lambda iv: f"    {iv.file}:{iv.line} {iv.current_import}",
                c.Infra.NAMESPACE_MAX_RENDERED_IMPORT_VIOLATIONS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.internal_import_violations,
                "Internal imports",
                lambda iv: f"    {iv.file}:{iv.line} {iv.current_import} ({iv.detail})",
                c.Infra.NAMESPACE_MAX_RENDERED_IMPORT_VIOLATIONS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.cyclic_imports,
                "Cyclic imports",
                lambda ci: f"    Cycle: {' -> '.join(ci.cycle)}",
                c.Infra.NAMESPACE_NO_RENDER_LIMIT,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.runtime_alias_violations,
                "Runtime alias violations",
                lambda rv: f"    {rv.file} [{rv.kind}] alias='{rv.alias}' {rv.detail}",
                c.Infra.NAMESPACE_NO_RENDER_LIMIT,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.future_violations,
                "Missing __future__ annotations",
                lambda fv: f"    {fv.file}",
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.manual_protocol_violations,
                "Manual protocols",
                lambda pv: f"    {pv.file}:{pv.line} {pv.name}",
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.manual_typing_violations,
                "Manual typing aliases",
                lambda tv: f"    {tv.file}:{tv.line} {tv.name}",
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.compatibility_alias_violations,
                "Compatibility aliases",
                lambda cv: f"    {cv.file}:{cv.line} {cv.alias_name}={cv.target_name}",
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.class_placement_violations,
                "Class placement violations",
                lambda cpv: f"    {cpv.file}:{cpv.line} {cpv.name} -> {cpv.suggestion}",
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.mro_completeness_violations,
                "MRO completeness violations",
                lambda mv: (
                    f"    {mv.file}:{mv.line} '{mv.facade_class}'"
                    f" missing base '{mv.missing_base}' (family={mv.family})"
                ),
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.namespace_source_violations,
                "Namespace source violations",
                lambda nsv: (
                    f"    {nsv.file}:{nsv.line} alias='{nsv.alias}'"
                    f" {nsv.current_source} -> {nsv.correct_source}"
                ),
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.parse_failures,
                "Parse failures",
                lambda pf: f"    {pf.file} [{pf.stage}] {pf.error_type}: {pf.detail}",
                c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS,
            )
            lines.append("")
        return "\n".join(lines) + "\n"

    @staticmethod
    def render_census_report(report: m.Infra.Census.WorkspaceReport) -> str:
        """Render a human-readable census report."""
        sep = "=" * 96
        lines: MutableSequence[str] = [
            sep,
            "FLEXT Rope Workspace Census",
            "Engine: rope-only DSL | Contract: m.Infra.Census.WorkspaceReport",
            sep,
            f"Projects: {len(report.projects)} | Objects: {report.total_objects}",
            f"Violations: {report.total_violations} | Fixable: {report.total_fixable}",
            f"Duplicates: {len(report.duplicates)} | Unused: {report.unused_count}",
            f"Fixes: {report.fixes_total} | Parse errors: {report.parse_errors}",
            f"Duration: {report.scan_duration_seconds:.2f}s",
            "",
            sep,
        ]
        for project in report.projects:
            lines.append(
                f"{project.project}: objects={project.objects_total}"
                f" violations={project.violations_total}"
                f" fixes={project.fixes_applied}/{len(project.fixes)}"
            )
            lines.extend(
                f"  {kind}: {count}"
                for kind, count in sorted(project.objects_by_kind.items())
            )
            lines.extend(
                f"  {violation.kind}: {violation.file_path}:{violation.line} {violation.object_name}"
                for violation in project.violations[
                    : FlextInfraUtilitiesOutputReporting._MAX_RENDERED_CENSUS_VIOLATIONS
                ]
            )
            if (
                len(project.violations)
                > FlextInfraUtilitiesOutputReporting._MAX_RENDERED_CENSUS_VIOLATIONS
            ):
                lines.append(
                    "  ... and "
                    f"{len(project.violations) - FlextInfraUtilitiesOutputReporting._MAX_RENDERED_CENSUS_VIOLATIONS} more"
                )
            lines.append("")
        if report.duplicates:
            lines.append("Duplicate groups:")
            lines.extend(
                f"  {group.kind} {group.name} ({len(group.definitions)}) identical={group.value_identical}"
                for group in report.duplicates[:10]
            )
        return "\n".join(lines)


__all__: list[str] = [
    "FlextInfraUtilitiesOutputReporting",
]
