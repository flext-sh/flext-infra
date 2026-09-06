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
        generated_hook = mod_workspace / ".agents/aihub-hooks/session.py"
        tm.ok(u.Cli.ensure_dir(generated_hook.parent))
        tm.ok(u.Cli.atomic_write_text_file(generated_hook, "value = 1\n"))

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
        tm.that(
            any(
                entry.file == generated_hook.relative_to(mod_workspace)
                for entry in first_evidence.entries
            ),
            eq=False,
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

    def test_apply_validates_rewrites_before_reporting_detection_only_findings(
        self, mod_workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reject an unformatted rewrite before the later findings-only result."""
        actionable_path = mod_workspace / "actionable.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                actionable_path, "publication=m.Infra.MiseToolchainPublication\n"
            )
        )

        exit_code = infra_main([
            "refactor",
            "mod",
            "--workspace",
            str(mod_workspace),
            "--apply",
        ])
        console_capture = capsys.readouterr()
        console = console_capture.out + console_capture.err
        updated = tm.not_none(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(actionable_path, required=True)
            ).content
        ).decode(c.Cli.ENCODING_DEFAULT)

        tm.that(exit_code, ne=0)
        tm.that(updated, has="m.Cli.AtomicFilePublication")
        tm.that(updated, lacks="m.Infra.MiseToolchainPublication")
        tm.that(console, has="Would reformat")
        tm.that(console, has=str(actionable_path))

    def test_scan_keeps_prefix_rule_ids_exact(self, mod_workspace: Path) -> None:
        config_path = mod_workspace / c.Infra.CODEMOD_CONFIG_FILENAME
        rules_root = (
            mod_workspace / c.Infra.CODEMOD_RESOURCE_DIRNAME / c.Cli.RULES_DIR_NAME
        )
        first_rule = rules_root / "rewire-first.yml"
        second_rule = rules_root / "rewire-first-message.yml"

        tm.ok(u.Cli.ensure_dir(rules_root))
        tm.ok(u.Cli.atomic_write_text_file(config_path, "ruleDirs:\n  - rules\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                first_rule,
                (
                    "id: rewire-first\n"
                    "language: Python\n"
                    "rule:\n"
                    "  pattern: |\n"
                    "    value = dict(\n"
                    "      $ARGS\n"
                    "    )\n"
                    "fix: |\n"
                    "  value = {\n"
                    "    $ARGS\n"
                    "  }\n"
                    "severity: warning\n"
                ),
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                second_rule,
                (
                    "id: rewire-first-message\n"
                    "language: Python\n"
                    "rule:\n"
                    "  pattern: |\n"
                    "    value = dict(\n"
                    "      $ARGS\n"
                    "    )\n"
                    "severity: warning\n"
                ),
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / "sample.py", "value = dict(\n    a=1,\n)\n"
            )
        )

        exit_code = infra_main(["refactor", "mod", "--workspace", str(mod_workspace)])
        report_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH, required=True
            )
        )
        report = m.Infra.ModScanEvidence.model_validate_json(
            tm.not_none(report_state.content)
        )

        tm.that(exit_code, ne=0)
        tm.that(report.findings, eq=2)
        tm.that(report.actionable, eq=1)
        tm.that(report.detection_only, eq=1)
        tm.that(
            {entry.rule_id: entry.rule_file for entry in report.entries},
            eq={
                "rewire-first": str(first_rule.resolve()),
                "rewire-first-message": str(second_rule.resolve()),
            },
        )

    def test_scan_aggregates_every_composed_provider_and_accepts_hint(
        self, mod_workspace: Path
    ) -> None:
        """Execute each elected provider config and retain its exact rule owner."""
        expected_rule_files: dict[str, str] = {}
        source_lines: list[str] = []
        for package, rule_id, severity in (
            ("first_provider", "first-provider-finding", "warning"),
            ("second_provider", "second-provider-finding", "hint"),
        ):
            config_root = mod_workspace / "src" / package / "codemod"
            rules_root = config_root / c.Cli.RULES_DIR_NAME
            rule_path = rules_root / f"{rule_id}.yml"
            statement = f"{package}_value = 1"
            tm.ok(u.Cli.ensure_dir(rules_root))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    config_root / c.Infra.CODEMOD_CONFIG_FILENAME,
                    (
                        f"{c.Infra.CODEMOD_SCOPE_KEY}: "
                        f"{c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n"
                        f"{c.Infra.CODEMOD_RULE_DIRS_KEY}:\n"
                        f"  - {c.Cli.RULES_DIR_NAME}\n"
                    ),
                )
            )
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rule_path,
                    (
                        f"id: {rule_id}\n"
                        "language: Python\n"
                        f"severity: {severity}\n"
                        "rule:\n"
                        f"  pattern: {statement}\n"
                    ),
                )
            )
            expected_rule_files[rule_id] = str(rule_path.resolve())
            source_lines.append(statement)
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / "sample.py", "\n".join(source_lines) + "\n"
            )
        )

        exit_code = infra_main(["refactor", "mod", "--workspace", str(mod_workspace)])
        report_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH, required=True
            )
        )
        report = m.Infra.ModScanEvidence.model_validate_json(
            tm.not_none(report_state.content)
        )
        provider_entries = {
            entry.rule_id: entry
            for entry in report.entries
            if entry.rule_id in expected_rule_files
        }

        tm.that(exit_code, ne=0)
        tm.that(
            {rule_id: entry.rule_file for rule_id, entry in provider_entries.items()},
            eq=expected_rule_files,
        )
        tm.that(
            {str(entry.payload["severity"]) for entry in provider_entries.values()},
            eq={"warning", "hint"},
        )

    def test_scan_rejects_byte_identical_declared_fix(
        self, mod_workspace: Path
    ) -> None:
        """Keep a declared fix that changes no bytes in the fixed-point residue."""
        config_path = mod_workspace / c.Infra.CODEMOD_CONFIG_FILENAME
        rules_root = (
            mod_workspace / c.Infra.CODEMOD_RESOURCE_DIRNAME / c.Cli.RULES_DIR_NAME
        )
        rule_path = rules_root / "identity-fix.yml"
        statement = "identity_fix_value = 1"
        tm.ok(u.Cli.ensure_dir(rules_root))
        tm.ok(
            u.Cli.atomic_write_text_file(
                config_path,
                f"{c.Infra.CODEMOD_RULE_DIRS_KEY}:\n  - {c.Cli.RULES_DIR_NAME}\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule_path,
                (
                    "id: identity-fix\n"
                    "language: Python\n"
                    "severity: hint\n"
                    "rule:\n"
                    f"  pattern: {statement}\n"
                    f"fix: {statement}\n"
                ),
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(mod_workspace / "sample.py", f"{statement}\n")
        )

        exit_code = infra_main(["refactor", "mod", "--workspace", str(mod_workspace)])
        report_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(
                mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH, required=True
            )
        )
        report = m.Infra.ModScanEvidence.model_validate_json(
            tm.not_none(report_state.content)
        )
        matches = [entry for entry in report.entries if entry.rule_id == "identity-fix"]
        tm.that(matches, len=1)
        identity_finding = matches[0]

        tm.that(exit_code, ne=0)
        tm.that(identity_finding.actionable, eq=False)
        tm.that(
            identity_finding.classification,
            eq=c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX,
        )
        tm.that(report.non_actionable_with_fix, gte=1)
