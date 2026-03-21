"""Terminal output utility with ANSI color and structured formatting."""

from __future__ import annotations

import sys
from collections.abc import Mapping
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
            f"\n{c.Infra.Style.BOLD if cls._use_color else ''}{line}\n  {title}\n{line}{c.Infra.Style.RESET if cls._use_color else ''}\n"
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
            f"  {clr}{sym}{c.Infra.Style.RESET if cls._use_color else ''} {verb:<8} {proj:<24} {elapsed:.2f}s\n"
        )

    @classmethod
    def summary(
        cls, verb: str, total: int, ok: int, fail: int, skip: int, elapsed: float
    ) -> None:
        hdr = f"── {verb} summary ──" if cls._use_unicode else f"-- {verb} summary --"
        cls._stream.write(
            f"\n{hdr}\nTotal: {total}  Success: {ok}  Failed: {fail}  Skipped: {skip}  ({elapsed:.2f}s)\n"
        )

    @classmethod
    def gate_result(cls, gate: str, count: int, passed: bool, elapsed: float) -> None:
        sym = (
            (c.Infra.Style.OK if passed else c.Infra.Style.FAIL)
            if cls._use_unicode
            else ("[OK]" if passed else "[FAIL]")
        )
        cls._stream.write(f"    {sym} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n")

    @staticmethod
    def metrics(
        *instances: t.Infra.MetricRecord, **kwargs: t.Infra.MetricValue
    ) -> None:
        for item in list(instances) + [kwargs]:
            for k, v in item.items() if isinstance(item, Mapping) else item:
                if isinstance(v, (*t.PRIMITIVES_TYPES, Path)) or v is None:
                    sys.stdout.write(f"{k}={v}\n")
        sys.stdout.flush()

    @staticmethod
    def render_namespace_enforcement_report(
        report: m.Infra.WorkspaceEnforcementReport,
    ) -> str:
        """Render a human-readable namespace enforcement report."""
        max_loose = c.Infra.NAMESPACE_MAX_RENDERED_LOOSE_OBJECTS
        max_imports = c.Infra.NAMESPACE_MAX_RENDERED_IMPORT_VIOLATIONS
        lines: list[str] = [
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
            if proj.loose_objects:
                lines.append(f"  Loose objects: {len(proj.loose_objects)}")
                lines.extend(
                    f"    {obj.file}:{obj.line} {obj.kind} '{obj.name}' -> {obj.suggestion}"
                    for obj in proj.loose_objects[:max_loose]
                )
                if len(proj.loose_objects) > max_loose:
                    lines.append(
                        f"    ... and {len(proj.loose_objects) - max_loose} more",
                    )
            if proj.import_violations:
                lines.append(f"  Import violations: {len(proj.import_violations)}")
                lines.extend(
                    f"    {iv.file}:{iv.line} {iv.current_import}"
                    for iv in proj.import_violations[:max_imports]
                )
                if len(proj.import_violations) > max_imports:
                    lines.append(
                        f"    ... and {len(proj.import_violations) - max_imports} more",
                    )
            if proj.internal_import_violations:
                lines.append(
                    f"  Internal imports: {len(proj.internal_import_violations)}",
                )
                lines.extend(
                    f"    {iv.file}:{iv.line} {iv.current_import} ({iv.detail})"
                    for iv in proj.internal_import_violations[:max_imports]
                )
                if len(proj.internal_import_violations) > max_imports:
                    lines.append(
                        f"    ... and {len(proj.internal_import_violations) - max_imports} more",
                    )
            if proj.cyclic_imports:
                lines.append(f"  Cyclic imports: {len(proj.cyclic_imports)}")
                lines.extend(
                    f"    Cycle: {' -> '.join(ci.cycle)}" for ci in proj.cyclic_imports
                )
            if proj.runtime_alias_violations:
                lines.append(
                    f"  Runtime alias violations: {len(proj.runtime_alias_violations)}",
                )
                lines.extend(
                    f"    {rv.file} [{rv.kind}] alias='{rv.alias}' {rv.detail}"
                    for rv in proj.runtime_alias_violations
                )
            if proj.future_violations:
                lines.append(
                    f"  Missing __future__ annotations: {len(proj.future_violations)}",
                )
                lines.extend(
                    f"    {fv.file}" for fv in proj.future_violations[:max_loose]
                )
                if len(proj.future_violations) > max_loose:
                    lines.append(
                        f"    ... and {len(proj.future_violations) - max_loose} more",
                    )
            if proj.manual_protocol_violations:
                lines.append(
                    f"  Manual protocols: {len(proj.manual_protocol_violations)}",
                )
                lines.extend(
                    f"    {pv.file}:{pv.line} {pv.name}"
                    for pv in proj.manual_protocol_violations[:max_loose]
                )
                if len(proj.manual_protocol_violations) > max_loose:
                    lines.append(
                        f"    ... and {len(proj.manual_protocol_violations) - max_loose} more",
                    )
            if proj.manual_typing_violations:
                lines.append(
                    f"  Manual typing aliases: {len(proj.manual_typing_violations)}",
                )
                lines.extend(
                    f"    {tv.file}:{tv.line} {tv.name}"
                    for tv in proj.manual_typing_violations[:max_loose]
                )
                if len(proj.manual_typing_violations) > max_loose:
                    lines.append(
                        f"    ... and {len(proj.manual_typing_violations) - max_loose} more",
                    )
            if proj.compatibility_alias_violations:
                lines.append(
                    f"  Compatibility aliases: {len(proj.compatibility_alias_violations)}",
                )
                lines.extend(
                    f"    {cv.file}:{cv.line} {cv.alias_name}={cv.target_name}"
                    for cv in proj.compatibility_alias_violations[:max_loose]
                )
                if len(proj.compatibility_alias_violations) > max_loose:
                    lines.append(
                        f"    ... and {len(proj.compatibility_alias_violations) - max_loose} more",
                    )
            if proj.parse_failures:
                lines.append(f"  Parse failures: {len(proj.parse_failures)}")
                lines.extend(
                    f"    {pf.file} [{pf.stage}] {pf.error_type}: {pf.detail}"
                    for pf in proj.parse_failures[:max_loose]
                )
                if len(proj.parse_failures) > max_loose:
                    lines.append(
                        f"    ... and {len(proj.parse_failures) - max_loose} more",
                    )
            lines.append("")
        return "\n".join(lines) + "\n"

    @staticmethod
    def render_census_report(report: m.Infra.UtilitiesCensusReport) -> str:
        """Render a human-readable census report."""
        sep = "=" * 110
        lines: list[str] = [
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

    def __init__(self, *, use_color: bool, use_unicode: bool, stream: TextIO) -> None:
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
            f"\n{c.Infra.Style.BOLD if self._use_color else ''}{line}\n  {title}\n{line}{c.Infra.Style.RESET if self._use_color else ''}\n"
        )

    def progress(self, idx: int, total: int, proj: str, verb: str) -> None:
        width = len(str(total))
        self._stream.write(f"[{idx:0{width}d}/{total:0{width}d}] {proj} {verb} ...\n")

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
            f"  {color}{symbol}{reset} {verb:<8} {proj:<24} {elapsed:.2f}s\n"
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
            f"── {verb} summary ──" if self._use_unicode else f"-- {verb} summary --"
        )
        self._stream.write(
            f"\n{header}\nTotal: {total}  Success: {success}  Failed: {failed}  Skipped: {skipped}  ({elapsed:.2f}s)\n"
        )

    def gate_result(self, gate: str, count: int, passed: bool, elapsed: float) -> None:
        symbol = (
            (c.Infra.Style.OK if passed else c.Infra.Style.FAIL)
            if self._use_unicode
            else ("[OK]" if passed else "[FAIL]")
        )
        self._stream.write(
            f"    {symbol} {gate:<10} {count:>5} errors  ({elapsed:.2f}s)\n"
        )


# Initialize default state
FlextInfraUtilitiesOutput.setup()
output: Final[type[FlextInfraUtilitiesOutput]] = FlextInfraUtilitiesOutput

__all__ = ["FlextInfraUtilitiesOutput", "OutputBackend", "output"]
