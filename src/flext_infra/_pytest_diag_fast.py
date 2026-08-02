"""Low-import pytest diagnostic extraction for the generated Make test surface."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Protocol, cast
from xml.etree.ElementTree import Element

from defusedxml import ElementTree as DefusedET
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

_SLOWEST_HEADER = re.compile(r"^=+ slowest durations =+")
_SECTION_DIVIDER = re.compile(r"^=+")
_WARNINGS_HEADER = re.compile(r"^=+ warnings summary =+")
_DOCS_FOOTER = re.compile(r"^-- Docs: https://docs.pytest.org/")
_FAILED_LINE = re.compile(r"(^FAILED |::.* FAILED( |$))")
_ERROR_LINE = re.compile(r"(^ERROR |::.* ERROR( |$))")
_SKIPPED_LINE = re.compile(r"(^SKIPPED |::.* SKIPPED( |$))")
_WARNING_LINE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*Warning\b")
_FAILURES_OR_ERRORS = re.compile(r"^=+ (FAILURES|ERRORS) =+")
_BLOCK_END = re.compile(
    r"^=+ (short test summary info|warnings summary|.+ in [0-9.]+s) =+"
)
_OPTION_FIELDS = {
    "--junit": "junit",
    "--log": "log",
    "--failed": "failed",
    "--errors": "errors",
    "--warnings": "warnings",
    "--slowest": "slowest",
    "--skips": "skips",
}
_COMBINE_JUNIT_OPTION = "--combine-junit"
_COMBINE_JUNIT_OUTPUT_INDEX = 1
_COMBINE_JUNIT_ARGUMENT_START = 2
_USAGE = (
    "usage: flext-infra validate pytest-diag "
    "--junit PATH --log PATH [--junit PATH --log PATH ...] "
    "[--failed PATH] [--errors PATH] [--warnings PATH] "
    "[--slowest PATH] [--skips PATH]\n"
)


class _XmlElement(Protocol):
    """Minimal defusedxml element boundary used by the extractor."""

    attrib: dict[str, str]
    tag: str
    text: str | None

    def __iter__(self) -> Iterator[_XmlElement]:
        """Iterate direct XML children."""

    def find(self, path: str) -> _XmlElement | None:
        """Find a direct child by tag."""

    def iter(self, tag: str) -> Iterator[_XmlElement]:
        """Iterate descendants matching one tag."""


class _CliArgs(BaseModel):
    """Validated low-import command boundary."""

    model_config = ConfigDict(extra="forbid")

    junit: tuple[Path, ...]
    log: tuple[Path, ...]
    failed: Path | None = None
    errors: Path | None = None
    warnings: Path | None = None
    slowest: Path | None = None
    skips: Path | None = None

    @model_validator(mode="after")
    def _validate_pairs(self) -> _CliArgs:
        """Require one log for every JUnit shard."""
        if not self.junit or len(self.junit) != len(self.log):
            msg = "--junit and --log must form one or more matching pairs"
            raise ValueError(msg)
        return self


class PytestDiagnosticsData(BaseModel):
    """Transport-neutral pytest diagnostic payload."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    failed_cases: list[str] = Field(default_factory=list)
    error_cases: list[str] = Field(default_factory=list)
    error_traces: list[str] = Field(default_factory=list)
    warning_lines: list[str] = Field(default_factory=list)
    skip_cases: list[str] = Field(default_factory=list)
    slow_entries: list[str] = Field(default_factory=list)

    @property
    def failed_count(self) -> int:
        """Number of failed test cases."""
        return len(self.failed_cases)

    @property
    def error_count(self) -> int:
        """Number of collection/runtime error cases."""
        return len(self.error_cases)

    @property
    def warning_count(self) -> int:
        """Number of warning lines."""
        return len(self.warning_lines)

    @property
    def skipped_count(self) -> int:
        """Number of skipped test cases."""
        return len(self.skip_cases)


def _trace_chunk(heading: str, label: str, element: _XmlElement) -> str:
    message = (element.attrib.get("message") or "").strip()
    trace = (element.text or "").strip()
    parts = [f"=== {heading}: {label} ==="]
    if message:
        parts.append(message)
    if trace:
        parts.append(trace)
    return "\n".join(parts)


def _process_testcase(
    case: _XmlElement, diagnostics: PytestDiagnosticsData
) -> tuple[float, str]:
    classname = case.attrib.get("classname", "")
    name = case.attrib.get("name", "")
    label = f"{classname}::{name}" if classname else name
    try:
        seconds = float(case.attrib.get("time", "0") or 0.0)
    except ValueError:
        seconds = 0.0
    if (failure := case.find("failure")) is not None:
        diagnostics.failed_cases.append(label)
        diagnostics.error_traces.append(_trace_chunk("FAILURE", label, failure))
    if (error := case.find("error")) is not None:
        diagnostics.error_cases.append(label)
        diagnostics.error_traces.append(_trace_chunk("ERROR", label, error))
    if (skipped := case.find("skipped")) is not None:
        reason = (skipped.attrib.get("message") or skipped.text or "").strip()
        diagnostics.skip_cases.append(f"{label} | {reason}" if reason else label)
    return seconds, label


def _parse_xml(junit_path: Path, diagnostics: PytestDiagnosticsData) -> bool:
    if not junit_path.exists():
        return False
    try:
        root = cast("_XmlElement", DefusedET.parse(junit_path).getroot())
    except (DefusedET.ParseError, OSError, ValueError):
        return False
    slow_rows = [_process_testcase(case, diagnostics) for case in root.iter("testcase")]
    if slow_rows:
        diagnostics.slow_entries = [
            f"{seconds:.6f}s | {label}"
            for seconds, label in sorted(slow_rows, reverse=True)
        ]
    return True


def _parse_log(lines: Sequence[str], diagnostics: PytestDiagnosticsData) -> None:
    diagnostics.failed_cases = [line for line in lines if _FAILED_LINE.search(line)]
    diagnostics.error_cases = [line for line in lines if _ERROR_LINE.search(line)]
    diagnostics.skip_cases = [line for line in lines if _SKIPPED_LINE.search(line)]
    capture = False
    block: list[str] = []
    for line in lines:
        if _FAILURES_OR_ERRORS.match(line):
            capture = True
        if capture:
            block.append(line)
            if _BLOCK_END.match(line):
                break
    diagnostics.error_traces = block


def _extract_warnings(lines: Sequence[str], diagnostics: PytestDiagnosticsData) -> None:
    capture = False
    for line in lines:
        if _WARNINGS_HEADER.match(line):
            capture = True
            continue
        if capture and _DOCS_FOOTER.match(line):
            break
        if capture and _WARNING_LINE.search(line):
            diagnostics.warning_lines.append(line)
    if not diagnostics.warning_lines:
        diagnostics.warning_lines = [
            line for line in lines if _WARNING_LINE.search(line)
        ]


def _extract_slow(lines: Sequence[str], diagnostics: PytestDiagnosticsData) -> None:
    capture = False
    for line in lines:
        if _SLOWEST_HEADER.match(line):
            capture = True
            continue
        if capture and _SECTION_DIVIDER.match(line):
            break
        if capture and line.strip():
            diagnostics.slow_entries.append(line)


def extract_diagnostics(junit_path: Path, log_path: Path) -> PytestDiagnosticsData:
    """Extract diagnostic data from the JUnit artifact and pytest log."""
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    lines = log_text.splitlines()
    diagnostics = PytestDiagnosticsData()
    if not _parse_xml(junit_path, diagnostics):
        _parse_log(lines, diagnostics)
    _extract_warnings(lines, diagnostics)
    if not diagnostics.slow_entries:
        _extract_slow(lines, diagnostics)
    return diagnostics


def extract_diagnostics_many(
    junit_paths: Sequence[Path], log_paths: Sequence[Path]
) -> PytestDiagnosticsData:
    """Aggregate diagnostics from an exact sequence of pytest shard artifacts."""
    if not junit_paths or len(junit_paths) != len(log_paths):
        msg = "pytest diagnostic shard inputs must form matching non-empty pairs"
        raise ValueError(msg)
    combined = PytestDiagnosticsData()
    for junit_path, log_path in zip(junit_paths, log_paths, strict=True):
        diagnostics = extract_diagnostics(junit_path, log_path)
        combined.failed_cases.extend(diagnostics.failed_cases)
        combined.error_cases.extend(diagnostics.error_cases)
        combined.error_traces.extend(diagnostics.error_traces)
        combined.warning_lines.extend(diagnostics.warning_lines)
        combined.skip_cases.extend(diagnostics.skip_cases)
        combined.slow_entries.extend(diagnostics.slow_entries)
    combined.slow_entries.sort(reverse=True)
    return combined


def combine_junit(junit_paths: Sequence[Path], output_path: Path) -> None:
    """Combine valid, nonempty shard JUnit reports into one consumer artifact."""
    if not junit_paths:
        msg = "at least one JUnit shard is required"
        raise ValueError(msg)
    combined = Element("testsuites")
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    duration = Decimal(0)
    for junit_path in junit_paths:
        if not junit_path.is_file() or junit_path.stat().st_size == 0:
            msg = f"JUnit shard is missing or empty: {junit_path}"
            raise ValueError(msg)
        try:
            shard = cast("_XmlElement", DefusedET.parse(junit_path).getroot())
        except (DefusedET.ParseError, OSError, ValueError) as exc:
            msg = f"JUnit shard is invalid: {junit_path}"
            raise ValueError(msg) from exc
        if not tuple(shard.iter("testcase")):
            msg = f"JUnit shard has no test cases: {junit_path}"
            raise ValueError(msg)
        suites = (
            (shard,)
            if shard.tag == "testsuite"
            else tuple(suite for suite in shard if suite.tag == "testsuite")
        )
        if not suites:
            msg = f"JUnit shard has no test suites: {junit_path}"
            raise ValueError(msg)
        for suite in suites:
            for field_name in totals:
                try:
                    totals[field_name] += int(suite.attrib.get(field_name, "0"))
                except ValueError as exc:
                    msg = f"JUnit shard has invalid {field_name} count: {junit_path}"
                    raise ValueError(msg) from exc
            try:
                duration += Decimal(suite.attrib.get("time", "0"))
            except InvalidOperation as exc:
                msg = f"JUnit shard has invalid time: {junit_path}"
                raise ValueError(msg) from exc
            combined.append(
                DefusedET.fromstring(
                    DefusedET.tostring(cast("Element[str]", suite))
                )
            )
    combined.attrib.update(
        {**{field_name: str(value) for field_name, value in totals.items()}, "time": str(duration)}
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        DefusedET.tostring(combined, encoding="utf-8", xml_declaration=True)
    )


def write_diagnostic_files(
    diagnostics: PytestDiagnosticsData,
    *,
    failed: Path | None,
    errors: Path | None,
    warnings: Path | None,
    slowest: Path | None,
    skips: Path | None,
) -> None:
    """Write the optional human-readable report files."""
    outputs = (
        (failed, diagnostics.failed_cases, "\n\n"),
        (errors, diagnostics.error_traces, "\n\n"),
        (warnings, diagnostics.warning_lines, "\n"),
        (slowest, diagnostics.slow_entries, "\n"),
        (skips, diagnostics.skip_cases, "\n"),
    )
    for output_path, items, separator in outputs:
        if output_path is not None:
            output_path.write_text(separator.join(items) + "\n", encoding="utf-8")


def _parse_args(args: Sequence[str]) -> _CliArgs:
    values: dict[str, str | list[str]] = {}
    index = 0
    while index < len(args):
        option = args[index]
        field_name = _OPTION_FIELDS.get(option)
        if field_name is None:
            msg = f"unknown option: {option}"
            raise ValueError(msg)
        if index + 1 >= len(args):
            msg = f"missing value for option: {option}"
            raise ValueError(msg)
        if field_name in {"junit", "log"}:
            current = values.setdefault(field_name, [])
            if not isinstance(current, list):
                msg = f"invalid repeated option state: {option}"
                raise ValueError(msg)
            current.append(args[index + 1])
            index += 2
            continue
        if field_name in values:
            msg = f"duplicate option: {option}"
            raise ValueError(msg)
        values[field_name] = args[index + 1]
        index += 2
    return _CliArgs.model_validate(values)


def _combine_junit_args(args: Sequence[str]) -> tuple[Path, tuple[Path, ...]] | None:
    """Parse the strict JUnit combination mode without accepting diagnostics flags."""
    if not args or args[0] != _COMBINE_JUNIT_OPTION:
        return None
    if len(args) < _COMBINE_JUNIT_ARGUMENT_START:
        msg = "--combine-junit requires an output path and --junit inputs"
        raise ValueError(msg)
    inputs = args[_COMBINE_JUNIT_ARGUMENT_START:]
    if not inputs or len(inputs) % _COMBINE_JUNIT_ARGUMENT_START != 0:
        msg = "--combine-junit requires repeated --junit PATH pairs"
        raise ValueError(msg)
    if any(
        inputs[index] != "--junit"
        for index in range(0, len(inputs), _COMBINE_JUNIT_ARGUMENT_START)
    ):
        msg = "--combine-junit accepts only --junit PATH pairs"
        raise ValueError(msg)
    return (
        Path(args[_COMBINE_JUNIT_OUTPUT_INDEX]),
        tuple(
            Path(inputs[index])
            for index in range(1, len(inputs), _COMBINE_JUNIT_ARGUMENT_START)
        ),
    )


def _run(args: Sequence[str]) -> PytestDiagnosticsData | None:
    """Execute either strict JUnit combination or normal diagnostics extraction."""
    combine_args = _combine_junit_args(args)
    if combine_args is not None:
        combine_junit(combine_args[1], combine_args[0])
        return None
    parsed = _parse_args(args)
    diagnostics = extract_diagnostics_many(parsed.junit, parsed.log)
    write_diagnostic_files(
        diagnostics,
        failed=parsed.failed,
        errors=parsed.errors,
        warnings=parsed.warnings,
        slowest=parsed.slowest,
        skips=parsed.skips,
    )
    return diagnostics


def main(args: Sequence[str] | None = None) -> int:
    """Run the low-import public pytest diagnostic command."""
    cli_args = list(args) if args is not None else sys.argv[1:]
    if any(arg in {"-h", "--help"} for arg in cli_args):
        sys.stdout.write(_USAGE)
        return 0
    try:
        diagnostics = _run(cli_args)
    except (OSError, ValidationError, ValueError) as exc:
        sys.stderr.write(_USAGE)
        sys.stderr.write(f"pytest diagnostics extraction failed: {exc}\n")
        return 2
    if diagnostics is None:
        return 0
    sys.stdout.write(
        f"failed_count={diagnostics.failed_count}\n"
        f"error_count={diagnostics.error_count}\n"
        f"warning_count={diagnostics.warning_count}\n"
        f"skipped_count={diagnostics.skipped_count}\n"
    )
    return 0


__all__ = [
    "PytestDiagnosticsData",
    "combine_junit",
    "extract_diagnostics",
    "extract_diagnostics_many",
    "main",
    "write_diagnostic_files",
]
