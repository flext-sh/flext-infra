"""Terminal output utility with ANSI color and structured formatting."""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, MutableSequence, Sequence
from operator import itemgetter
from pathlib import Path
from typing import Final, TextIO

from flext_infra import FlextInfraUtilitiesTerminal, c, m, t


class FlextInfraUtilitiesOutput:
    """Terminal output formatter with color and unicode support."""

    _stream: TextIO = sys.stderr
    _use_color: bool = False
    _use_unicode: bool = False

    @classmethod
    def setup(
        cls,
        *,
        color: bool | None = None,
        unicode: bool | None = None,
        stream: TextIO | None = None,
    ) -> None:
        """Initialize output settings."""
        cls._use_color = (
            FlextInfraUtilitiesTerminal.terminal_should_use_color()
            if color is None
            else color
        )
        cls._use_unicode = (
            FlextInfraUtilitiesTerminal.terminal_should_use_unicode()
            if unicode is None
            else unicode
        )
        if stream:
            cls._stream = stream

    @classmethod
    def _fmt(cls, level: str, color: str, message: str) -> None:
        reset = c.Infra.Style.RESET if cls._use_color else ""
        clr = color if cls._use_color else ""
        cls._stream.write(f"{clr}{level}{reset}: {message}\n")
        cls._stream.flush()

    @classmethod
    def info(cls, msg: str) -> None:
        cls._fmt("INFO", c.Infra.Style.BLUE, msg)

    @classmethod
    def error(cls, msg: str, detail: str | None = None) -> None:
        cls._fmt("ERROR", c.Infra.Style.RED, msg)
        if detail:
            cls._stream.write(f"  {detail}\n")

    @classmethod
    def warning(cls, msg: str) -> None:
        cls._fmt("WARN", c.Infra.Style.YELLOW, msg)

    @classmethod
    def debug(cls, msg: str) -> None:
        cls._fmt("DEBUG", c.Infra.Style.GREEN, msg)

    @classmethod
    def header(cls, title: str) -> None:
        sep = "═" if cls._use_unicode else "="
        line = sep * 60
        cls._stream.write(
            f"\n{c.Infra.Style.BOLD if cls._use_color else ''}{line}\n  {title}\n{line}{c.Infra.Style.RESET if cls._use_color else ''}\n",
        )

    @classmethod
    def progress(cls, idx: int, total: int, proj: str, verb: str) -> None:
        w = len(str(total))
        cls._stream.write(f"[{idx:0{w}d}/{total:0{w}d}] {proj} {verb} ...\n")

    @classmethod
    def status(cls, verb: str, proj: str, result: bool, elapsed: float) -> None:
        sym = (
            (c.Infra.Style.OK if cls._use_unicode else "[OK]")
            if result
            else (c.Infra.Style.FAIL if cls._use_unicode else "[FAIL]")
        )
        clr = (
            (c.Infra.Style.GREEN if result else c.Infra.Style.RED)
            if cls._use_color
            else ""
        )
        cls._stream.write(
            f"  {clr}{sym}{c.Infra.Style.RESET if cls._use_color else ''} {verb:<8} {proj:<24} {elapsed:.2f}s\n",
        )

    @classmethod
    def write(cls, text: str) -> None:
        """Write raw text to output stream."""
        cls._stream.write(text)
        cls._stream.flush()

    @classmethod
    def summary(
        cls,
        verb: str,
        total: int,
        ok: int,
        fail: int,
        skip: int,
        elapsed: float,
    ) -> None:
        hdr = f"── {verb} summary ──" if cls._use_unicode else f"-- {verb} summary --"
        cls._stream.write(
            f"\n{hdr}\nTotal: {total}  Success: {ok}  Failed: {fail}  Skipped: {skip}  ({elapsed:.2f}s)\n",
        )

    @classmethod
    def gate_result(cls, gate: str, count: int, passed: bool, elapsed: float) -> None:
        sym = (
            (c.Infra.Style.OK if passed else c.Infra.Style.FAIL)
            if cls._use_unicode
            else ("[OK]" if passed else "[FAIL]")
        )
        cls._stream.write(f"    {sym} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n")

    @classmethod
    def project_failure(
        cls,
        project: str,
        elapsed: float,
        log_path: Path,
        error_count: int,
        errors: t.StrSequence,
        *,
        max_show: int = 3,
    ) -> None:
        """Show failed project with error excerpt."""
        clr = c.Infra.Style.RED if cls._use_color else ""
        reset = c.Infra.Style.RESET if cls._use_color else ""
        fail_sym = c.Infra.Style.FAIL if cls._use_unicode else "[FAIL]"
        count_label = f"  [{error_count} errors]" if error_count > 0 else ""
        cls._stream.write(
            f"  {clr}{fail_sym}{reset} {project} completed in {int(elapsed)}s"
            f"{count_label}  ({log_path})\n",
        )
        for line in errors[:max_show]:
            cls._stream.write(f"      {line}\n")
        remaining = error_count - max_show
        if remaining > 0:
            cls._stream.write(f"      ... and {remaining} more (see log)\n")
        cls._stream.flush()

    @classmethod
    def failure_summary(
        cls,
        verb: str,
        failures: Sequence[tuple[str, int, Path]],
    ) -> None:
        """Show end-of-run failure summary block."""
        if not failures:
            return
        hdr = (
            f"── {verb} failed projects ──"
            if cls._use_unicode
            else f"-- {verb} failed projects --"
        )
        clr = c.Infra.Style.RED if cls._use_color else ""
        reset = c.Infra.Style.RESET if cls._use_color else ""
        fail_sym = c.Infra.Style.FAIL if cls._use_unicode else "[FAIL]"
        cls._stream.write(f"\n{hdr}\n")
        for project, error_count, log_path in failures:
            count_label = f"{error_count} errors" if error_count > 0 else "failed"
            cls._stream.write(
                f"{clr}{fail_sym}{reset} {project:<20} {count_label}  ({log_path})\n",
            )
        cls._stream.flush()

    @staticmethod
    def metrics(
        *instances: t.Infra.MetricRecord,
        **kwargs: t.Infra.MetricValue,
    ) -> None:
        for item in list(instances) + [kwargs]:
            for k, v in item.items() if isinstance(item, Mapping) else item:
                if isinstance(v, (*t.PRIMITIVES_TYPES, Path)) or v is None:
                    sys.stdout.write(f"{k}={v}\n")
        sys.stdout.flush()

    @staticmethod
    def _render_violation_section[V](
        *,
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
        no_limit = 10_000
        render = FlextInfraUtilitiesOutput._render_violation_section
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
            missing = [s for s in proj.facade_statuses if not s.exists]
            has_violations = (
                missing
                or proj.loose_objects
                or proj.import_violations
                or proj.internal_import_violations
                or proj.runtime_alias_violations
                or proj.future_violations
                or proj.manual_protocol_violations
                or proj.manual_typing_violations
                or proj.compatibility_alias_violations
                or proj.class_placement_violations
                or proj.mro_completeness_violations
                or proj.namespace_source_violations
                or proj.parse_failures
            )
            if not has_violations:
                continue
            lines.append(f"--- {proj.project} ---")
            if missing:
                lines.append(
                    "  Missing facades: "
                    + ", ".join(
                        f"{s.family} ({c.Infra.FAMILY_SUFFIXES[s.family]})"
                        for s in missing
                    ),
                )
            render(
                lines=lines,
                violations=proj.loose_objects,
                label="Loose objects",
                formatter=lambda obj: (
                    f"    {obj.file}:{obj.line} {obj.kind} '{obj.name}' -> {obj.suggestion}"
                ),
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.import_violations,
                label="Import violations",
                formatter=lambda iv: f"    {iv.file}:{iv.line} {iv.current_import}",
                max_items=max_imports,
            )
            render(
                lines=lines,
                violations=proj.internal_import_violations,
                label="Internal imports",
                formatter=lambda iv: (
                    f"    {iv.file}:{iv.line} {iv.current_import} ({iv.detail})"
                ),
                max_items=max_imports,
            )
            render(
                lines=lines,
                violations=proj.cyclic_imports,
                label="Cyclic imports",
                formatter=lambda ci: f"    Cycle: {' -> '.join(ci.cycle)}",
                max_items=no_limit,
            )
            render(
                lines=lines,
                violations=proj.runtime_alias_violations,
                label="Runtime alias violations",
                formatter=lambda rv: (
                    f"    {rv.file} [{rv.kind}] alias='{rv.alias}' {rv.detail}"
                ),
                max_items=no_limit,
            )
            render(
                lines=lines,
                violations=proj.future_violations,
                label="Missing __future__ annotations",
                formatter=lambda fv: f"    {fv.file}",
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.manual_protocol_violations,
                label="Manual protocols",
                formatter=lambda pv: f"    {pv.file}:{pv.line} {pv.name}",
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.manual_typing_violations,
                label="Manual typing aliases",
                formatter=lambda tv: f"    {tv.file}:{tv.line} {tv.name}",
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.compatibility_alias_violations,
                label="Compatibility aliases",
                formatter=lambda cv: (
                    f"    {cv.file}:{cv.line} {cv.alias_name}={cv.target_name}"
                ),
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.class_placement_violations,
                label="Class placement violations",
                formatter=lambda cpv: (
                    f"    {cpv.file}:{cpv.line} {cpv.name} -> {cpv.suggestion}"
                ),
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.mro_completeness_violations,
                label="MRO completeness violations",
                formatter=lambda mv: (
                    f"    {mv.file}:{mv.line} '{mv.facade_class}'"
                    f" missing base '{mv.missing_base}' (family={mv.family})"
                ),
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.namespace_source_violations,
                label="Namespace source violations",
                formatter=lambda nsv: (
                    f"    {nsv.file}:{nsv.line} alias='{nsv.alias}'"
                    f" {nsv.current_source} -> {nsv.correct_source}"
                ),
                max_items=max_loose,
            )
            render(
                lines=lines,
                violations=proj.parse_failures,
                label="Parse failures",
                formatter=lambda pf: (
                    f"    {pf.file} [{pf.stage}] {pf.error_type}: {pf.detail}"
                ),
                max_items=max_loose,
            )
            lines.append("")
        return "\n".join(lines) + "\n"

    class OutputBackend:
        """Instance-based terminal output formatter with stateful configuration.

        Similar to FlextInfraUtilitiesOutput but uses instance state rather than class state.
        Allows multiple independent OutputBackend instances with different color/unicode
        settings and output streams, useful for tests or multi-threaded contexts.

        Instance state:
            _use_color: Whether to emit ANSI color codes.
            _use_unicode: Whether to use unicode symbols (✓/✗ vs [OK]/[FAIL]).
            _stream: TextIO stream for output (typically stderr).

        Comparison:
            FlextInfraUtilitiesOutput: Global singleton-like state via class methods.
            OutputBackend: Per-instance configurable state via instance methods.

        Attributes:
            None (all state is private: _use_color, _use_unicode, _stream).

        """

        def __init__(
            self,
            *,
            use_color: bool,
            use_unicode: bool,
            stream: TextIO,
        ) -> None:
            """Initialize output backend with terminal capabilities and stream.

            Args:
                use_color: Emit ANSI color codes (e.g., for terminal with color support).
                use_unicode: Use unicode box-drawing and status symbols vs ASCII fallbacks.
                stream: TextIO stream for output (typically sys.stderr or sys.stdout).

            """
            self._use_color = use_color
            self._use_unicode = use_unicode
            self._stream = stream

        def _fmt(self, level: str, color: str, message: str) -> None:
            reset = c.Infra.Style.RESET if self._use_color else ""
            clr = color if self._use_color else ""
            self._stream.write(f"{clr}{level}{reset}: {message}\n")

        def info(self, msg: str) -> None:
            self._fmt("INFO", c.Infra.Style.BLUE, msg)

        def error(self, msg: str, detail: str | None = None) -> None:
            self._fmt("ERROR", c.Infra.Style.RED, msg)
            if detail:
                self._stream.write(f"  {detail}\n")

        def warning(self, msg: str) -> None:
            self._fmt("WARN", c.Infra.Style.YELLOW, msg)

        def debug(self, msg: str) -> None:
            self._fmt("DEBUG", c.Infra.Style.GREEN, msg)

        def header(self, title: str) -> None:
            sep = "═" if self._use_unicode else "="
            line = sep * 60
            self._stream.write(
                f"\n{c.Infra.Style.BOLD if self._use_color else ''}{line}\n  {title}\n{line}{c.Infra.Style.RESET if self._use_color else ''}\n",
            )

        def progress(self, idx: int, total: int, proj: str, verb: str) -> None:
            width = len(str(total))
            self._stream.write(
                f"[{idx:0{width}d}/{total:0{width}d}] {proj} {verb} ...\n",
            )

        def status(self, verb: str, proj: str, result: bool, elapsed: float) -> None:
            symbol = (
                (c.Infra.Style.OK if (result and self._use_unicode) else "[OK]")
                if result
                else (c.Infra.Style.FAIL if self._use_unicode else "[FAIL]")
            )
            color = (
                (c.Infra.Style.GREEN if result else c.Infra.Style.RED)
                if self._use_color
                else ""
            )
            reset = c.Infra.Style.RESET if self._use_color else ""
            self._stream.write(
                f"  {color}{symbol}{reset} {verb:<8} {proj:<24} {elapsed:.2f}s\n",
            )

        def summary(
            self,
            verb: str,
            total: int,
            success: int,
            failed: int,
            skipped: int,
            elapsed: float,
        ) -> None:
            header = (
                f"── {verb} summary ──"
                if self._use_unicode
                else f"-- {verb} summary --"
            )
            self._stream.write(
                f"\n{header}\nTotal: {total}  Success: {success}  Failed: {failed}  Skipped: {skipped}  ({elapsed:.2f}s)\n",
            )

        def gate_result(
            self,
            gate: str,
            count: int,
            passed: bool,
            elapsed: float,
        ) -> None:
            symbol = (
                (c.Infra.Style.OK if passed else c.Infra.Style.FAIL)
                if self._use_unicode
                else ("[OK]" if passed else "[FAIL]")
            )
            self._stream.write(
                f"    {symbol} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n",
            )

        def project_failure(
            self,
            project: str,
            elapsed: float,
            log_path: Path,
            error_count: int,
            errors: t.StrSequence,
            *,
            max_show: int = 3,
        ) -> None:
            """Show failed project with error excerpt."""
            clr = c.Infra.Style.RED if self._use_color else ""
            reset = c.Infra.Style.RESET if self._use_color else ""
            fail_sym = c.Infra.Style.FAIL if self._use_unicode else "[FAIL]"
            count_label = f"  [{error_count} errors]" if error_count > 0 else ""
            self._stream.write(
                f"  {clr}{fail_sym}{reset} {project} completed in {int(elapsed)}s"
                f"{count_label}  ({log_path})\n",
            )
            for line in errors[:max_show]:
                self._stream.write(f"      {line}\n")
            remaining = error_count - max_show
            if remaining > 0:
                self._stream.write(f"      ... and {remaining} more (see log)\n")

        def failure_summary(
            self,
            verb: str,
            failures: Sequence[tuple[str, int, Path]],
        ) -> None:
            """Show end-of-run failure summary block."""
            if not failures:
                return
            hdr = (
                f"── {verb} failed projects ──"
                if self._use_unicode
                else f"-- {verb} failed projects --"
            )
            clr = c.Infra.Style.RED if self._use_color else ""
            reset = c.Infra.Style.RESET if self._use_color else ""
            fail_sym = c.Infra.Style.FAIL if self._use_unicode else "[FAIL]"
            self._stream.write(f"\n{hdr}\n")
            for project, error_count, log_path in failures:
                count_label = f"{error_count} errors" if error_count > 0 else "failed"
                self._stream.write(
                    f"{clr}{fail_sym}{reset} {project:<20} {count_label}  ({log_path})\n",
                )

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


# Initialize default state
FlextInfraUtilitiesOutput.setup()
output: Final[type[FlextInfraUtilitiesOutput]] = FlextInfraUtilitiesOutput
__all__ = ["FlextInfraUtilitiesOutput", "output"]
