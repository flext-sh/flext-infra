"""Raw-hard duplication evidence controls without scanner or network dependence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.gates.duplication_evidence import FlextInfraDuplicationEvidence
from tests import m, tm


class TestsFlextInfraDuplicationEvidence:
    """Keep candidates and independent oracles even when classification is uncertain."""

    @staticmethod
    def _report(
        root: Path,
        source: str,
        *,
        format_name: str = "python",
        mirror: bool = False,
    ) -> m.Infra.JscpdReport:
        files = (root / "first.py", root / "second.py")
        for path in files:
            path.write_text(source, encoding="utf-8")
        lines = source.splitlines()
        sides = [
            {
                "name": str(path),
                "start": 1,
                "end": len(lines),
                "startLoc": {"line": 1, "column": 0, "position": 0},
                "endLoc": {
                    "line": len(lines),
                    "column": len(lines[-1].encode()),
                    "position": len(source.rstrip().encode()),
                },
            }
            for path in files
        ]
        duplicate = {
            "firstFile": sides[0],
            "secondFile": sides[1],
            "fragment": source.rstrip(),
            "format": format_name,
            "lines": len(lines),
            "tokens": 100,
        }
        duplicates = [duplicate]
        if mirror:
            duplicates.append({
                **duplicate,
                "firstFile": sides[1],
                "secondFile": sides[0],
            })
        summary = {
            "clones": len(duplicates),
            "sources": len(files),
            "lines": len(lines) * len(files),
            "tokens": 200,
            "duplicatedLines": len(lines),
            "duplicatedTokens": 100,
            "newClones": 0,
            "newDuplicatedLines": 0,
            "percentage": 50,
            "percentageTokens": 50,
        }
        return m.Infra.JscpdReport.model_validate({
            "duplicates": duplicates,
            "statistics": {
                "detectionDate": "2026-10-23",
                "formats": {format_name: summary},
                "total": summary,
            },
        })

    @staticmethod
    def _assess(
        root: Path,
        report: m.Infra.JscpdReport,
    ) -> m.Infra.DuplicationAssessment:
        return FlextInfraDuplicationEvidence().assess(
            report,
            root,
            m.Infra.ProjectDuplicationOverrides(),
            raw_receipt=report.model_dump_json(),
            execution="offline contract fixture",
        )

    def test_mirrors_preserve_inventory_and_raw_hard(self, tmp_path: Path) -> None:
        """A mirror has its own reason but links back to the original candidate."""
        report = self._report(tmp_path, "value = calculate()\n", mirror=True)
        assessment = self._assess(tmp_path, report)
        tm.that(len(assessment.candidates), eq=len(report.duplicates))
        tm.that(assessment.candidates[1].canonical_index, eq=0)
        tm.that(assessment.counts["mirror"], eq=1)
        tm.that(assessment.counts["raw_hard"], eq=1)

    def test_body_floor_uses_selected_config(self, tmp_path: Path) -> None:
        """A real cloned body at the configured floor remains a behavioral candidate."""
        config = m.Infra.ProjectDuplicationOverrides()
        source = "def test_real_body():\n" + "".join(
            f"    value_{index} = calculate({index}, strict=True)\n"
            for index in range(max(config.min_lines, config.min_tokens))
        )
        assessment = self._assess(tmp_path, self._report(tmp_path, source))
        tm.that(assessment.candidates[0].disposition, eq="behavioral_candidate")
        tm.that(assessment.counts["raw_hard"], eq=1)

    def test_padding_does_not_raise_body_measure(self, tmp_path: Path) -> None:
        """Copyright and a long docstring cannot promote a short body above floor."""
        config = m.Infra.ProjectDuplicationOverrides()
        source = '"""\n' + "boilerplate\n" * config.min_lines + '"""\n'
        source += "def action():\n    return calculate()\n"
        assessment = self._assess(tmp_path, self._report(tmp_path, source))
        item = assessment.candidates[0]
        tm.that(item.disposition, eq="below_existing_behavior_floor")
        tm.that(item.measures[0].lines, eq=1)
        tm.that(assessment.counts["raw_hard"], eq=1)

    def test_import_only_has_no_authority_exemption(self, tmp_path: Path) -> None:
        """Imports are not bodies but their activation effects remain unresolved."""
        assessment = self._assess(
            tmp_path, self._report(tmp_path, "import activates_plugin\n")
        )
        tm.that(assessment.candidates[0].measures[0].tokens, eq=0)
        tm.that(assessment.candidates[0].disposition, eq="unresolved")

    def test_future_and_docstring_only_is_structural(self, tmp_path: Path) -> None:
        """Removing syntax from measurement never removes its raw-hard finding."""
        assessment = self._assess(
            tmp_path,
            self._report(
                tmp_path, '"""Notice."""\nfrom __future__ import annotations\n'
            ),
        )
        tm.that(assessment.candidates[0].disposition, eq="non_behavioral_only")
        tm.that(assessment.counts["raw_hard"], eq=1)

    def test_definition_time_effects_are_retained(self, tmp_path: Path) -> None:
        """Decorator registration and default factories must not disappear."""
        source = "@register()\ndef action(value=calculate()):\n    return value\n"
        assessment = self._assess(tmp_path, self._report(tmp_path, source))
        tm.that(assessment.candidates[0].measures[0].lines, eq=3)
        tm.ok(assessment.candidates[0].measures[0].tokens > 0)

    @pytest.mark.parametrize("format_name", ["txt", "yaml", "json"])
    def test_data_never_gets_generic_exemption(
        self, tmp_path: Path, format_name: str
    ) -> None:
        """No path, hash, golden spelling or data format proves independence."""
        source = (
            '{"command": "run_real_operation"}\n'
            if format_name == "json"
            else "command: run_real_operation\n"
        )
        report = self._report(tmp_path, source, format_name=format_name)
        assessment = self._assess(tmp_path, report)
        expected = "unresolved" if format_name == "txt" else "authority_data_candidate"
        tm.that(assessment.candidates[0].disposition, eq=expected)
        tm.that(assessment.counts["raw_hard"], eq=1)

    @pytest.mark.parametrize("failure", ["missing", "syntax", "encoding", "span"])
    def test_unreadable_or_unparseable_source_fails_closed(
        self, tmp_path: Path, failure: str
    ) -> None:
        """Each failed candidate remains present with its causal error."""
        report = self._report(tmp_path, "value = calculate()\n")
        path = tmp_path / "second.py"
        if failure == "missing":
            path.unlink()
        elif failure == "encoding":
            path.write_bytes(b"\xff")
        elif failure == "syntax":
            path.write_text("not valid python here!\n", encoding="utf-8")
        else:
            path.write_text("x\n", encoding="utf-8")
        assessment = self._assess(tmp_path, report)
        tm.that(assessment.candidates[0].disposition, eq="analysis_error")
        tm.that(assessment.counts["raw_hard"], eq=1)

    def test_raw_trailer_preserved_and_second_document_rejected(
        self, tmp_path: Path
    ) -> None:
        """Console output is retained separately, not mistaken for another report."""
        report = self._report(tmp_path, "value = calculate()\n")
        raw = report.model_dump_json()
        parsed = FlextInfraDuplicationEvidence.parse(
            raw + "\nERROR: jscpd threshold exceeded\n"
        )
        tm.that(parsed, eq=report)
        with pytest.raises(ValueError, match="second JSON"):
            FlextInfraDuplicationEvidence.parse(raw + "\n{}")

    def test_invalid_report_is_not_an_empty_success(self, tmp_path: Path) -> None:
        """Missing statistics or mismatched inventory cannot authorize green."""
        with pytest.raises(ValueError, match="statistics"):
            FlextInfraDuplicationEvidence.parse('{"duplicates": []}')
        report = self._report(tmp_path, "value = calculate()\n")
        malformed = report.model_dump_json().replace('"clones":1', '"clones":2')
        with pytest.raises(ValueError, match="clone total"):
            FlextInfraDuplicationEvidence.parse(malformed)

    @pytest.mark.parametrize("format_name", ["yaml", "json", "markdown"])
    def test_invalid_data_or_unmapped_format_fails_closed(
        self,
        tmp_path: Path,
        format_name: str,
    ) -> None:
        """A data parser failure is not a harmless data-role classification."""
        report = self._report(tmp_path, "{broken: [\n", format_name=format_name)
        assessment = self._assess(tmp_path, report)
        tm.that(assessment.candidates[0].disposition, eq="analysis_error")

    def test_first_fragment_drift_is_not_reclassified(self, tmp_path: Path) -> None:
        """A parseable changed source still fails its historical fragment binding."""
        report = self._report(tmp_path, "value = calculate()\n")
        (tmp_path / "first.py").write_text("value = different()\n", encoding="utf-8")
        assessment = self._assess(tmp_path, report)
        tm.that(assessment.candidates[0].disposition, eq="analysis_error")
        tm.that(assessment.candidates[0].reason, has="no longer matches")

    def test_disjoint_bodies_do_not_form_one_large_run(self, tmp_path: Path) -> None:
        """Comments cannot join physically separate regions to reach a floor."""
        config = m.Infra.ProjectDuplicationOverrides()
        source = (
            "def action():\n"
            + "\n# separate region\n".join(
                f"    value_{index} = calculate({index}, strict=True)"
                for index in range(max(config.min_lines, config.min_tokens))
            )
            + "\n"
        )
        assessment = self._assess(tmp_path, self._report(tmp_path, source))
        tm.that(
            assessment.candidates[0].disposition, eq="below_existing_behavior_floor"
        )
        tm.ok(
            all(
                end == start
                for start, end, _ in assessment.candidates[0].measures[0].runs
            )
        )

    def test_unknown_trailer_is_not_a_valid_scan(self, tmp_path: Path) -> None:
        """Unrecognized tool output requires an explicit parser contract change."""
        report = self._report(tmp_path, "value = calculate()\n")
        with pytest.raises(ValueError, match="unrecognized console"):
            FlextInfraDuplicationEvidence.parse(
                report.model_dump_json() + "\nunknown output"
            )

    def test_scanner_byte_columns_bind_unicode_sources(self, tmp_path: Path) -> None:
        """Real scanner byte columns must not become false source-drift failures."""
        report = self._report(tmp_path, "value = 'a\u00e7\u00e3o'\n")
        assessment = self._assess(tmp_path, report)
        tm.that(
            assessment.candidates[0].disposition, eq="below_existing_behavior_floor"
        )
        tm.ok(assessment.candidates[0].measures[0].tokens > 0)
