"""Public CLI evidence contract for the batch ast-grep ``mod`` verb."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, main as infra_main, u
from flext_tests import tm

if TYPE_CHECKING:
    import pytest


class TestsFlextInfraModCliRoute:
    """Exercise reporter behavior only through exported CLI and utility facades."""

    def test_receipt_is_complete_and_replaced_by_zero_scan(
        self, mod_workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        report_path = mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH
        sample_path = mod_workspace / "sample.py"

        first_exit = infra_main(["refactor", "mod", "--workspace", str(mod_workspace)])
        first_console_capture = capsys.readouterr()
        first_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(report_path, required=True)
        )
        first_bytes = tm.not_none(first_state.content)
        first_evidence = m.Infra.ModScanEvidence.model_validate_json(first_bytes)
        first_digest = u.Cli.sha256_bytes(first_bytes)
        first_console = first_console_capture.out + first_console_capture.err

        tm.that(first_exit, ne=0)
        tm.that(
            first_evidence.schema_version, eq=c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION
        )
        tm.that(first_evidence.command, eq=c.Infra.ModScanCommand.SCAN)
        tm.that(first_evidence.root, eq=mod_workspace.resolve())
        tm.that(first_evidence.findings, gte=1)
        tm.that(
            first_evidence.actionable
            + first_evidence.detection_only
            + first_evidence.non_actionable_with_fix,
            eq=first_evidence.findings,
        )
        tm.that(
            first_evidence.totals_by_class[c.Infra.ModScanFindingClass.DETECTION_ONLY],
            eq=first_evidence.detection_only,
        )
        tm.that(
            any(entry.file == Path("sample.py") for entry in first_evidence.entries),
            eq=True,
        )
        tm.that(first_console, has=str(report_path))
        tm.that(first_console, has=first_digest)
        tm.that(first_console, lacks='"ruleId"')

        tm.ok(u.Cli.atomic_write_text_file(sample_path, "value = 1\n"))
        second_exit = infra_main(["refactor", "mod", "--workspace", str(mod_workspace)])
        second_console_capture = capsys.readouterr()
        second_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(report_path, required=True)
        )
        second_bytes = tm.not_none(second_state.content)
        second_evidence = m.Infra.ModScanEvidence.model_validate_json(second_bytes)
        second_digest = u.Cli.sha256_bytes(second_bytes)
        second_console = second_console_capture.out + second_console_capture.err

        tm.that(second_exit, eq=0)
        tm.that(second_evidence.findings, eq=0)
        tm.that(second_evidence.actionable, eq=0)
        tm.that(second_evidence.detection_only, eq=0)
        tm.that(second_evidence.non_actionable_with_fix, eq=0)
        tm.that(second_evidence.entries, empty=True)
        tm.that(tuple(second_evidence.totals_by_repository), empty=True)
        tm.that(tuple(second_evidence.totals_by_rule), empty=True)
        tm.that(second_digest, ne=first_digest)
        tm.that(second_console, has=str(report_path))
        tm.that(second_console, has=second_digest)
        tm.that(second_console, lacks=first_digest)

    def test_apply_executes_safe_rewrites_before_reporting_detection_only_findings(
        self, mod_workspace: Path
    ) -> None:
        """Keep automated fixes independent from semantic findings needing rewire."""
        actionable_path = mod_workspace / "actionable.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                actionable_path,
                "publication = m.Infra.MiseToolchainPublication\n",
            )
        )

        exit_code = infra_main([
            "refactor",
            "mod",
            "--workspace",
            str(mod_workspace),
            "--apply",
        ])
        updated = tm.not_none(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    actionable_path, required=True
                )
            ).content
        ).decode(c.Cli.ENCODING_DEFAULT)

        tm.that(exit_code, ne=0)
        tm.that(updated, has="m.Cli.AtomicFilePublication")
        tm.that(updated, lacks="m.Infra.MiseToolchainPublication")
