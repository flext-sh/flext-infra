"""Pytest diagnostics extraction service.

Extracts robust pytest diagnostics from JUnit XML and log outputs,
producing structured failure/error/warning/skip/slow-test reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, ClassVar, override

from defusedxml import ElementTree as DefusedET

from flext_infra import c, m, p, r, s, t, u


class _DiagResult:
    """Internal container for extracted diagnostics."""

    __slots__: ClassVar[t.Quint[str, str, str, str, str]] = (
        "error_traces",
        "failed_cases",
        "skip_cases",
        "slow_entries",
        "warning_lines",
    )

    def __init__(self) -> None:
        self.failed_cases: t.MutableSequenceOf[str] = []
        self.error_traces: t.MutableSequenceOf[str] = []
        self.skip_cases: t.MutableSequenceOf[str] = []
        self.warning_lines: t.MutableSequenceOf[str] = []
        self.slow_entries: t.MutableSequenceOf[str] = []


class FlextInfraPytestDiagExtractor(s[bool]):
    """Extracts pytest diagnostics from JUnit XML and log files.

    Parses JUnit XML for structured failure/error/skip/timing data
    and uses regex-based log parsing when XML is unavailable.
    """

    junit: Annotated[Path, m.Field(description="JUnit XML path")]
    log_path: Annotated[
        Path,
        m.Field(alias="log", description="Pytest log path"),
    ]
    failed: Annotated[
        Path | None, m.Field(description="Path to write failed cases")
    ] = None
    errors: Annotated[
        Path | None, m.Field(description="Path to write error traces")
    ] = None
    warnings: Annotated[Path | None, m.Field(description="Path to write warnings")] = (
        None
    )
    slowest: Annotated[
        Path | None, m.Field(description="Path to write slowest entries")
    ] = None
    skips: Annotated[
        Path | None, m.Field(description="Path to write skipped cases")
    ] = None

    @staticmethod
    def _extract_slow_from_log(lines: t.StrSequence, diag: _DiagResult) -> None:
        """Extract slow test durations from log when XML unavailable."""
        capture_slow = False
        for line in lines:
            if c.Infra.PYTEST_SLOWEST_HEADER_RE.match(line):
                capture_slow = True
                continue
            if capture_slow and c.Infra.PYTEST_SECTION_DIVIDER_RE.match(line):
                break
            if capture_slow and line.strip():
                diag.slow_entries.append(line)

    @staticmethod
    def _extract_warnings(lines: t.StrSequence, diag: _DiagResult) -> None:
        """Extract warning lines from pytest log."""
        capture_warn = False
        for line in lines:
            if c.Infra.PYTEST_WARNINGS_HEADER_RE.match(line):
                capture_warn = True
            if capture_warn:
                diag.warning_lines.append(line)
                if c.Infra.PYTEST_DOCS_FOOTER_RE.match(line):
                    break
        if not diag.warning_lines:
            diag.warning_lines = [
                line for line in lines if c.Infra.PYTEST_KNOWN_WARNINGS_RE.search(line)
            ]

    @staticmethod
    def _parse_log_into_diag(lines: t.StrSequence, diag: _DiagResult) -> None:
        """Parse pytest log output for failures/skips when XML unavailable."""
        diag.failed_cases = [
            line for line in lines if c.Infra.PYTEST_FAILED_LINE_RE.search(line)
        ]
        diag.skip_cases = [
            line for line in lines if c.Infra.PYTEST_SKIPPED_LINE_RE.search(line)
        ]
        capture = False
        block: t.MutableSequenceOf[str] = []
        for line in lines:
            if c.Infra.PYTEST_FAILURES_OR_ERRORS_RE.match(line):
                capture = True
            if capture:
                block.append(line)
                if c.Infra.PYTEST_BLOCK_END_RE.match(line):
                    break
        diag.error_traces = block

    @staticmethod
    def _as_xml_element(
        value: p.Infra.XmlElementLike | t.JsonValue,
    ) -> p.Infra.XmlElementLike | None:
        """Normalize dynamic defusedxml nodes to the typed stdlib element API."""
        return value if isinstance(value, p.Infra.XmlElementLike) else None

    @staticmethod
    def _build_trace_chunk(
        heading: str, label: str, element: p.Infra.XmlElementLike
    ) -> str:
        """Build an error/failure trace chunk from a JUnit XML element."""
        msg = (element.attrib.get(c.Infra.RK_MESSAGE) or "").strip()
        trace = (element.text or "").strip()
        chunk: t.MutableSequenceOf[str] = [f"=== {heading}: {label} ==="]
        if msg:
            chunk.append(msg)
        if trace:
            chunk.append(trace)
        return "\n".join(chunk)

    @staticmethod
    def _process_testcase(
        case: p.Infra.XmlElementLike,
        diag: _DiagResult,
    ) -> t.Pair[float, str]:
        """Process a single testcase element; returns (seconds, label)."""
        classname = case.attrib.get("classname", "")
        name = case.attrib.get(c.Infra.NAME, "")
        label = f"{classname}::{name}" if classname else name
        try:
            secs = float(case.attrib.get("time", "0") or 0.0)
        except ValueError:
            secs = 0.0
        if (failure := case.find("failure")) is not None:
            diag.failed_cases.append(label)
            diag.error_traces.append(
                FlextInfraPytestDiagExtractor._build_trace_chunk(
                    "FAILURE", label, failure
                ),
            )
        if (error := case.find(c.Infra.ERROR)) is not None:
            diag.error_traces.append(
                FlextInfraPytestDiagExtractor._build_trace_chunk("ERROR", label, error),
            )
        if (skipped := case.find("skipped")) is not None:
            reason = (
                skipped.attrib.get(c.Infra.RK_MESSAGE) or skipped.text or ""
            ).strip()
            diag.skip_cases.append(f"{label} | {reason}" if reason else label)
        return secs, label

    @staticmethod
    def _parse_xml(junit_path: Path, diag: _DiagResult) -> bool:
        """Parse JUnit XML and populate diagnostics. Returns True on success."""
        if not junit_path.exists():
            return False
        try:
            root_raw = DefusedET.parse(junit_path).getroot()
        except DefusedET.ParseError:
            return False
        if root_raw is None:
            return False
        root = FlextInfraPytestDiagExtractor._as_xml_element(root_raw)
        if root is None:
            return False
        slow_rows: t.MutableSequenceOf[t.Pair[float, str]] = []
        for case_raw in root.iter("testcase"):
            if case_raw is None:
                continue
            case = FlextInfraPytestDiagExtractor._as_xml_element(case_raw)
            if case is None:
                continue
            slow_rows.append(
                FlextInfraPytestDiagExtractor._process_testcase(case, diag),
            )
        if slow_rows:
            diag.slow_entries = [
                f"{secs:.6f}s | {label}"
                for secs, label in sorted(slow_rows, reverse=True)
            ]
        return True

    def extract(
        self,
        junit_path: Path,
        log_path: Path,
    ) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract diagnostics from JUnit XML and pytest log.

        Args:
            junit_path: Path to JUnit XML result file.
            log_path: Path to raw pytest log output.

        Returns:
            r with diagnostics dict containing counts and entries.

        """
        try:
            log_text = (
                log_path.read_text(encoding=c.Cli.ENCODING_DEFAULT, errors="replace")
                if log_path.exists()
                else ""
            )
            lines = log_text.splitlines()
            diag = _DiagResult()
            xml_parsed = self._parse_xml(junit_path, diag)
            if not xml_parsed:
                self._parse_log_into_diag(lines, diag)
            self._extract_warnings(lines, diag)
            if not diag.slow_entries:
                self._extract_slow_from_log(lines, diag)
            result = m.Infra.PytestDiagnostics(
                failed_count=len(diag.failed_cases),
                error_count=len(diag.error_traces),
                warning_count=len(diag.warning_lines),
                skipped_count=len(diag.skip_cases),
                failed_cases=diag.failed_cases,
                error_traces=diag.error_traces,
                warning_lines=diag.warning_lines,
                skip_cases=diag.skip_cases,
                slow_entries=diag.slow_entries,
            )
            return r[m.Infra.PytestDiagnostics].ok(result)
        except c.EXC_OS_TYPE_VALUE as exc:
            return r[m.Infra.PytestDiagnostics].fail_op(
                "pytest diagnostics extraction", exc
            )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the pytest diagnostics CLI flow."""
        result = self.extract(self.junit, self.log_path)
        if result.failure:
            return r[bool].fail(result.error or "extraction failed")
        for output_path, attr_name, separator in [
            (self.failed, "failed_cases", "\n\n"),
            (self.errors, "error_traces", "\n\n"),
            (self.warnings, "warning_lines", "\n"),
            (self.slowest, "slow_entries", "\n"),
            (self.skips, "skip_cases", "\n"),
        ]:
            if output_path is None:
                continue
            items = [
                value
                for value in getattr(result.value, attr_name, [])
                if isinstance(value, str)
            ]
            u.write_file(
                output_path,
                separator.join(items) + "\n",
                encoding=c.Cli.ENCODING_DEFAULT,
            )
        sys.stdout.write(
            f"failed_count={result.value.failed_count}\n"
            f"error_count={result.value.error_count}\n"
            f"warning_count={result.value.warning_count}\n"
            f"skipped_count={result.value.skipped_count}\n",
        )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPytestDiagExtractor"]
