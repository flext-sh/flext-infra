"""Report rendering mixins for output utility."""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from operator import itemgetter

from flext_infra import c, m


class FlextInfraUtilitiesOutputReporting:
    """Mixin for structured report rendering (namespace enforcement, census)."""

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
        max_loose = c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS
        max_imports = c.Infra.NAMESPACE_MAX_RENDERED_IMPORT_VIOLATIONS
        no_limit = c.Infra.NAMESPACE_NO_RENDER_LIMIT
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
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.import_violations,
                "Import violations",
                lambda iv: f"    {iv.file}:{iv.line} {iv.current_import}",
                max_imports,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.internal_import_violations,
                "Internal imports",
                lambda iv: f"    {iv.file}:{iv.line} {iv.current_import} ({iv.detail})",
                max_imports,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.cyclic_imports,
                "Cyclic imports",
                lambda ci: f"    Cycle: {' -> '.join(ci.cycle)}",
                no_limit,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.runtime_alias_violations,
                "Runtime alias violations",
                lambda rv: f"    {rv.file} [{rv.kind}] alias='{rv.alias}' {rv.detail}",
                no_limit,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.future_violations,
                "Missing __future__ annotations",
                lambda fv: f"    {fv.file}",
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.manual_protocol_violations,
                "Manual protocols",
                lambda pv: f"    {pv.file}:{pv.line} {pv.name}",
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.manual_typing_violations,
                "Manual typing aliases",
                lambda tv: f"    {tv.file}:{tv.line} {tv.name}",
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.compatibility_alias_violations,
                "Compatibility aliases",
                lambda cv: f"    {cv.file}:{cv.line} {cv.alias_name}={cv.target_name}",
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.class_placement_violations,
                "Class placement violations",
                lambda cpv: f"    {cpv.file}:{cpv.line} {cpv.name} -> {cpv.suggestion}",
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.mro_completeness_violations,
                "MRO completeness violations",
                lambda mv: (
                    f"    {mv.file}:{mv.line} '{mv.facade_class}'"
                    f" missing base '{mv.missing_base}' (family={mv.family})"
                ),
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.namespace_source_violations,
                "Namespace source violations",
                lambda nsv: (
                    f"    {nsv.file}:{nsv.line} alias='{nsv.alias}'"
                    f" {nsv.current_source} -> {nsv.correct_source}"
                ),
                max_loose,
            )
            FlextInfraUtilitiesOutputReporting._add_violation_section(
                lines,
                proj.parse_failures,
                "Parse failures",
                lambda pf: f"    {pf.file} [{pf.stage}] {pf.error_type}: {pf.detail}",
                max_loose,
            )
            lines.append("")
        return "\n".join(lines) + "\n"

    @staticmethod
    def render_census_report(report: m.Infra.UtilitiesCensusReport) -> str:
        """Render a human-readable census report."""
        sep = "=" * 110
        lines: MutableSequence[str] = [
            sep,
            "FLEXT MRO Family Method Usage Census",
            "Engine: libcst + stdlib ast | Infrastructure: flext_infra",
            sep,
            (
                f"\nClasses: {report.total_classes} | Methods: {report.total_methods}"
                f" | Usages: {report.total_usages} | Unused: {report.total_unused}"
                f" | Files: {report.files_scanned} | Parse errors: {report.parse_errors}"
            ),
            "",
            f"{'CLASS':<40} {'METHOD':<30} {'flat':<8} {'NS':<8} {'Direct':<8} {'Total':<8}",
            sep,
        ]

        grand_af = grand_an = grand_dr = 0
        for cs in report.classes:
            for ms in cs.methods:
                grand_af += ms.alias_flat
                grand_an += ms.alias_namespaced
                grand_dr += ms.direct
                marker = "  " if ms.total > 0 else "\u26a0\ufe0f"
                lines.append(
                    f"{marker} {cs.class_name:<38} {ms.name:<30}"
                    f" {ms.alias_flat:<8} {ms.alias_namespaced:<8}"
                    f" {ms.direct:<8} {ms.total:<8}",
                )
            lines.append("-" * 110)

        grand_total = grand_af + grand_an + grand_dr
        lines.append(
            f"\n{'GRAND TOTAL':<71} {grand_af:<8} {grand_an:<8} {grand_dr:<8} {grand_total:<8}",
        )

        lines.extend([f"\n\n{sep}", "PER-PROJECT BREAKDOWN", sep])
        for ps in report.projects:
            alias_total = sum(
                pu.count
                for pu in ps.usages
                if pu.access_mode != c.Infra.Census.MODE_DIRECT
            )
            direct_total = sum(
                pu.count
                for pu in ps.usages
                if pu.access_mode == c.Infra.Census.MODE_DIRECT
            )
            lines.append(
                f"\n\U0001f4e6 {ps.project_name}"
                f" (alias: {alias_total}, direct: {direct_total}, total: {ps.total})",
            )
            lines.extend(
                f"  {pu.class_name}.{pu.method_name}: {pu.access_mode}={pu.count}"
                for pu in ps.usages
            )

        lines.extend([f"\n\n{sep}", "UNUSED PUBLIC METHODS", sep])
        current_cls = ""
        for cs in report.classes:
            unused = [ms for ms in cs.methods if ms.total == 0]
            if unused:
                if cs.class_name != current_cls:
                    lines.append(f"\n  {cs.class_name} ({cs.source_file}):")
                    current_cls = cs.class_name
                lines.extend(f"    - {ms.name}" for ms in unused)
        lines.append(f"\n  Total unused: {report.total_unused}/{report.total_methods}")

        lines.extend([f"\n\n{sep}", "TOP 20 MOST USED METHODS", sep])
        all_methods = [
            (cs.class_name, ms.name, ms.total)
            for cs in report.classes
            for ms in cs.methods
        ]
        lines.extend(
            f"  {total:>5}x  {cls}.{method}"
            for cls, method, total in sorted(
                all_methods,
                key=itemgetter(2),
                reverse=True,
            )[:20]
        )

        return "\n".join(lines)


__all__ = [
    "FlextInfraUtilitiesOutputReporting",
]
