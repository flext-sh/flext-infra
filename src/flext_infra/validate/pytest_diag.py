"""Pytest diagnostics extraction service.

Extracts robust pytest diagnostics from JUnit XML and log outputs,
producing structured failure/error/warning/skip/slow-test reports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence
from pathlib import Path
from typing import ClassVar

from defusedxml import ElementTree as DefusedET

from flext_infra import c, m, r, t, u


class _DiagResult:
    """Internal container for extracted diagnostics."""

    __slots__: ClassVar[t.Infra.Quint[str, str, str, str, str]] = (
        "error_traces",
        "failed_cases",
        "skip_cases",
        "slow_entries",
        "warning_lines",
    )

    def __init__(self) -> None:
        self.failed_cases: MutableSequence[str] = []
        self.error_traces: MutableSequence[str] = []
        self.skip_cases: MutableSequence[str] = []
        self.warning_lines: MutableSequence[str] = []
        self.slow_entries: MutableSequence[str] = []


class FlextInfraPytestDiagExtractor:
    """Extracts pytest diagnostics from JUnit XML and log files.

    Parses JUnit XML for structured failure/error/skip/timing data
    and uses regex-based log parsing when XML is unavailable.
    """

    _ENCODING: ClassVar[str] = c.Infra.Encoding.DEFAULT

    @staticmethod
    def _extract_slow_from_log(lines: t.StrSequence, diag: _DiagResult) -> None:
        """Extract slow test durations from log when XML unavailable."""
        capture_slow = False
        for line in lines:
            if re.match(r"^=+ slowest durations =+", line):
                capture_slow = True
                continue
            if capture_slow and re.match(r"^=+", line):
                break
            if capture_slow and line.strip():
                diag.slow_entries.append(line)

    @staticmethod
    def _extract_warnings(lines: t.StrSequence, diag: _DiagResult) -> None:
        """Extract warning lines from pytest log."""
        capture_warn = False
        for line in lines:
            if re.match(r"^=+ warnings summary =+", line):
                capture_warn = True
            if capture_warn:
                diag.warning_lines.append(line)
                if re.match(r"^-- Docs: https://docs.pytest.org/", line):
                    break
        if not diag.warning_lines:
            diag.warning_lines = [
                line
                for line in lines
                if re.search(
                    r"CoverageWarning|PytestCollectionWarning|DeprecationWarning|UserWarning|RuntimeWarning",
                    line,
                )
            ]

    @staticmethod
    def _parse_log_into_diag(lines: t.StrSequence, diag: _DiagResult) -> None:
        """Parse pytest log output for failures/skips when XML unavailable."""
        diag.failed_cases = [
            line for line in lines if re.search(r"(^FAILED |::.* FAILED( |$))", line)
        ]
        diag.skip_cases = [
            line for line in lines if re.search(r"(^SKIPPED |::.* SKIPPED( |$))", line)
        ]
        capture = False
        block: MutableSequence[str] = []
        for line in lines:
            if re.match(r"^=+ (FAILURES|ERRORS) =+", line):
                capture = True
            if capture:
                block.append(line)
                if re.match(
                    r"^=+ (short test summary info|warnings summary|.+ in [0-9.]+s) =+",
                    line,
                ):
                    break
        diag.error_traces = block

    @staticmethod
    def _build_trace_chunk(heading: str, label: str, element: DefusedET.Element) -> str:
        """Build an error/failure trace chunk from a JUnit XML element."""
        msg = (element.attrib.get(c.Infra.ReportKeys.MESSAGE) or "").strip()
        trace = (element.text or "").strip()
        chunk: MutableSequence[str] = [f"=== {heading}: {label} ==="]
        if msg:
            chunk.append(msg)
        if trace:
            chunk.append(trace)
        return "\n".join(chunk)

    @staticmethod
    def _process_testcase(
        case: DefusedET.Element,
        diag: _DiagResult,
    ) -> t.Infra.Pair[float, str]:
        """Process a single testcase element; returns (seconds, label)."""
        classname = case.attrib.get("classname", "")
        name = case.attrib.get(c.Infra.NAME, "")
        label = f"{classname}::{name}" if classname else name
        try:
            secs = float(case.attrib.get("time", "0") or 0.0)
        except ValueError:
            secs = 0.0
        failure = case.find("failure")
        error = case.find(c.Infra.ERROR)
        skipped = case.find("skipped")
        if failure is not None:
            diag.failed_cases.append(label)
            diag.error_traces.append(
                FlextInfraPytestDiagExtractor._build_trace_chunk(
                    "FAILURE", label, failure
                ),
            )
        if error is not None:
            diag.error_traces.append(
                FlextInfraPytestDiagExtractor._build_trace_chunk("ERROR", label, error),
            )
        if skipped is not None:
            reason = (
                skipped.attrib.get(c.Infra.ReportKeys.MESSAGE) or skipped.text or ""
            ).strip()
            diag.skip_cases.append(f"{label} | {reason}" if reason else label)
        return secs, label

    @staticmethod
    def _parse_xml(junit_path: Path, diag: _DiagResult) -> bool:
        """Parse JUnit XML and populate diagnostics. Returns True on success."""
        if not junit_path.exists():
            return False
        try:
            root = DefusedET.parse(junit_path).getroot()
        except DefusedET.ParseError:
            return False
        if root is None:
            return False
        slow_rows: MutableSequence[t.Infra.Pair[float, str]] = []
        for case in root.iter("testcase"):
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
    ) -> r[m.Infra.PytestDiagnostics]:
        """Extract diagnostics from JUnit XML and pytest log.

        Args:
            junit_path: Path to JUnit XML result file.
            log_path: Path to raw pytest log output.

        Returns:
            r with diagnostics dict containing counts and entries.

        """
        try:
            log_text = (
                log_path.read_text(encoding=self._ENCODING, errors="replace")
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
        except (OSError, TypeError, ValueError) as exc:
            return r[m.Infra.PytestDiagnostics].fail(
                f"pytest diagnostics extraction failed: {exc}",
            )

    def execute_command(self, params: m.Infra.ValidatePytestDiagInput) -> r[bool]:
        """Execute the pytest diagnostics CLI flow for the input model."""
        result = self.extract(params.junit_path, params.log_path)
        if result.is_failure:
            return r[bool].fail(result.error or "extraction failed")
        for param_name, attr_name, separator in [
            ("failed", "failed_cases", "\n\n"),
            ("errors", "error_traces", "\n\n"),
            ("warnings", "warning_lines", "\n"),
            ("slowest", "slow_entries", "\n"),
            ("skips", "skip_cases", "\n"),
        ]:
            path_str = getattr(params, param_name, None)
            if not path_str:
                continue
            items = [
                value
                for value in getattr(result.value, attr_name, [])
                if isinstance(value, str)
            ]
            u.write_file(
                Path(path_str),
                separator.join(items) + "\n",
                encoding=c.Infra.Encoding.DEFAULT,
            )
        return r[bool].ok(True)


__all__ = ["FlextInfraPytestDiagExtractor"]
