"""Behavior tests for FlextInfraPytestDiagExtractor."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm
from tests import m, t

from flext_infra import FlextInfraPytestDiagExtractor


def _extractor(
    junit: Path,
    log: Path,
    *,
    failed: Path | None = None,
    errors: Path | None = None,
    warnings: Path | None = None,
    slowest: Path | None = None,
    skips: Path | None = None,
) -> FlextInfraPytestDiagExtractor:
    return FlextInfraPytestDiagExtractor(
        junit=junit,
        log=log,
        failed=failed,
        errors=errors,
        warnings=warnings,
        slowest=slowest,
        skips=skips,
    )


class TestPytestDiagExtractorBehavior:
    def test_extract_valid_junit_xml(self, tmp_path: Path) -> None:
        junit = tmp_path / "junit.xml"
        junit.write_text(
            '<?xml version="1.0"?><testsuites><testsuite name="t" tests="1"'
            ' failures="0" errors="0" skipped="0"></testsuite></testsuites>',
        )
        log = tmp_path / "log.txt"
        log.write_text("")

        report = tm.ok(_extractor(junit, log).extract(junit, log))

        tm.that(report, is_=m.Infra.PytestDiagnostics)
        tm.that(report.failed_count, eq=0)
        tm.that(report.error_count, eq=0)

    def test_extract_falls_back_to_log_when_xml_missing_or_invalid(
        self,
        tmp_path: Path,
    ) -> None:
        log = tmp_path / "log.txt"
        log.write_text("FAILED test_case.py::test_foo")
        missing_xml = tmp_path / "missing.xml"

        missing_report = tm.ok(_extractor(missing_xml, log).extract(missing_xml, log))
        tm.that(missing_report.failed_cases, length_gt=0)

        bad_xml = tmp_path / "bad.xml"
        bad_xml.write_text("invalid xml content")
        invalid_report = tm.ok(_extractor(bad_xml, log).extract(bad_xml, log))
        tm.that(invalid_report.failed_cases, length_gt=0)

    def test_extract_failed_and_error_tests_from_xml(self, tmp_path: Path) -> None:
        log = tmp_path / "log.txt"
        log.write_text("")
        fail_xml = tmp_path / "fail.xml"
        fail_xml.write_text(
            '<?xml version="1.0"?><testsuites><testsuite name="t" tests="1"'
            ' failures="1" errors="0" skipped="0"><testcase name="test_fail"'
            ' classname="TC"><failure message="fail">Traceback</failure>'
            "</testcase></testsuite></testsuites>",
        )

        fail_report = tm.ok(_extractor(fail_xml, log).extract(fail_xml, log))
        tm.that(fail_report.failed_count, eq=1)
        tm.that(fail_report.error_traces, length_gt=0)

        err_xml = tmp_path / "err.xml"
        err_xml.write_text(
            '<?xml version="1.0"?><testsuites><testsuite name="t" tests="1"'
            ' failures="0" errors="1" skipped="0"><testcase name="test_err"'
            ' classname="TC"><error message="err">Trace</error>'
            "</testcase></testsuite></testsuites>",
        )

        err_report = tm.ok(_extractor(err_xml, log).extract(err_xml, log))
        tm.that(err_report.error_count, eq=1)

    def test_extract_skipped_and_slow_tests_from_xml(self, tmp_path: Path) -> None:
        log = tmp_path / "log.txt"
        log.write_text("")
        skip_xml = tmp_path / "skip.xml"
        skip_xml.write_text(
            '<?xml version="1.0"?><testsuites><testsuite name="t" tests="1"'
            ' failures="0" errors="0" skipped="1"><testcase name="test_skip"'
            ' classname="TC"><skipped message="skip"/>'
            "</testcase></testsuite></testsuites>",
        )

        skip_report = tm.ok(_extractor(skip_xml, log).extract(skip_xml, log))
        tm.that(skip_report.skipped_count, eq=1)

        slow_xml = tmp_path / "slow.xml"
        slow_xml.write_text(
            '<?xml version="1.0"?><testsuites><testsuite name="t" tests="2">'
            '<testcase name="fast" time="0.1"/><testcase name="slow" time="5.5"/>'
            "</testsuite></testsuites>",
        )

        slow_report = tm.ok(_extractor(slow_xml, log).extract(slow_xml, log))
        tm.that(slow_report.slow_entries, length_gt=0)

    def test_extract_missing_log_is_graceful(self, tmp_path: Path) -> None:
        junit = tmp_path / "junit.xml"
        junit.write_text(
            '<?xml version="1.0"?><testsuites>'
            '<testsuite name="t" tests="0"/></testsuites>',
        )

        report = tm.ok(
            _extractor(junit, tmp_path / "missing.txt").extract(
                junit,
                tmp_path / "missing.txt",
            ),
        )

        tm.that(report.warning_count, eq=0)

    def test_extract_warnings_and_error_block_from_log(self, tmp_path: Path) -> None:
        junit = tmp_path / "missing.xml"
        log = tmp_path / "log.txt"
        log.write_text(
            "=== FAILURES ===\n"
            "test_case.py::test_foo\n"
            "AssertionError: expected True\n"
            "=== short test summary info ===\n"
            "=== warnings summary ===\n"
            "DeprecationWarning: test warning\n"
            "-- Docs: https://docs.pytest.org/\n",
        )

        report = tm.ok(_extractor(junit, log).extract(junit, log))

        tm.that(report.error_traces, length_gt=0)
        tm.that(report.warning_lines, length_gt=0)

    def test_extract_inline_warning_without_summary(self, tmp_path: Path) -> None:
        junit = tmp_path / "missing.xml"
        log = tmp_path / "log.txt"
        log.write_text("test_case.py:10: DeprecationWarning: test warning")

        report = tm.ok(_extractor(junit, log).extract(junit, log))

        tm.that(report.warning_lines, length_gt=0)

    def test_extract_slow_entries_from_log_when_xml_missing(
        self, tmp_path: Path
    ) -> None:
        junit = tmp_path / "missing.xml"
        log = tmp_path / "log.txt"
        log.write_text(
            "=== slowest durations ===\n"
            "5.50s call     test_case.py::test_slow\n"
            "0.50s call     test_case.py::test_fast\n"
            "=== 2 passed in 6.00s ===\n",
        )

        report = tm.ok(_extractor(junit, log).extract(junit, log))

        tm.that(report.slow_entries, length_gt=0)

    def test_execute_writes_selected_output_files(self, tmp_path: Path) -> None:
        junit = tmp_path / "junit.xml"
        junit.write_text(
            '<?xml version="1.0"?><testsuites><testsuite name="t" tests="2">'
            '<testcase name="test_fail" classname="TC" time="2.5">'
            '<failure message="fail">Traceback</failure></testcase>'
            '<testcase name="test_skip" classname="TC" time="0.1">'
            '<skipped message="skip"/></testcase></testsuite></testsuites>',
        )
        log = tmp_path / "log.txt"
        log.write_text(
            "=== warnings summary ===\n"
            "DeprecationWarning: test warning\n"
            "-- Docs: https://docs.pytest.org/\n",
        )
        extractor = _extractor(
            junit,
            log,
            failed=tmp_path / "failed.txt",
            errors=tmp_path / "errors.txt",
            warnings=tmp_path / "warnings.txt",
            slowest=tmp_path / "slow.txt",
            skips=tmp_path / "skips.txt",
        )

        tm.ok(extractor.execute())

        tm.that((tmp_path / "failed.txt").read_text(), contains="TC::test_fail")
        tm.that((tmp_path / "errors.txt").read_text(), contains="Traceback")
        tm.that((tmp_path / "warnings.txt").read_text(), contains="DeprecationWarning")
        tm.that((tmp_path / "slow.txt").read_text(), contains="TC::test_fail")
        tm.that((tmp_path / "skips.txt").read_text(), contains="TC::test_skip")


__all__: t.StrSequence = []
