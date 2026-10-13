"""Failed codemod passes retain accepted writes for fix-forward.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import main
from flext_infra.codemod import FlextInfraCodemodAstScan, FlextInfraCodemodSemanticApply
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import c, m, tm, u


class TestsFlextInfraFailedInvocationProgress:
    """Failures preserve accepted progress and newer independent source states."""

    @staticmethod
    @pytest.mark.slow
    def test_ast_scan_selects_two_exact_ids_without_prefix_matches(
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """CSV selection elects exact rules, not regex or prefix neighbours."""
        selected = ("selection.first", "selection.second")
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                name: (
                    f"id: {name}\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: value = dict()\n"
                )
                for name in (*selected, "selection.first-extra", "selectionXfirst")
            },
        )
        source = "value = dict()\n"
        sample = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, source))
        plan = tm.ok(u.Infra.codemod_rule_plan(mod_workspace, rule_ids=selected))
        tm.that(tuple(rule.id for rule in plan.rules), eq=selected)
        tm.that(
            tuple(rule_id for ruleset in plan.rulesets for rule_id in ruleset.rule_ids),
            eq=selected,
        )
        exit_code = main([
            "refactor",
            "ast",
            "--repository-root",
            str(mod_workspace),
            "--rules",
            ",".join(selected),
        ])
        capture = capsys.readouterr()
        console = capture.out + capture.err
        report = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(exit_code, ne=0)
        tm.that(report.findings, eq=len(selected))
        tm.that(set(report.totals_by_rule), eq=set(selected))
        tm.that(console, has="text phases=0 semantic callbacks=0; corpus=full")
        tm.that(console, lacks="selection.first-extra")
        tm.that(console, lacks="selectionXfirst")
        tm.that(sample.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("selection", "diagnostic"),
        [
            ("missing-rule-id", "unknown codemod rule IDs"),
            ("", "non-empty exact rule IDs"),
            ("known,", "non-empty exact rule IDs"),
            ("known,known", "duplicate codemod rule IDs"),
        ],
    )
    def test_ast_invalid_selection_fails_before_scan_or_effects(
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
        selection: str,
        diagnostic: str,
    ) -> None:
        """Invalid selections neither publish scan evidence nor rewrite source."""
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {"known": "id: known\nlanguage: Python\nrule:\n  pattern: dict()\n"},
        )
        sample = mod_workspace / "sample.py"
        before = sample.read_bytes()
        exit_code = main([
            "refactor",
            "ast",
            "--repository-root",
            str(mod_workspace),
            "--rules",
            selection,
            "--apply",
        ])
        capture = capsys.readouterr()
        console = capture.out + capture.err
        tm.that(exit_code, ne=0)
        tm.that(console, has=diagnostic)
        tm.that(console, lacks="mod: start")
        tm.that(console, lacks="validate ast-grep rule fixtures")
        tm.that(sample.read_bytes(), eq=before)
        tm.that(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).exists(),
            eq=False,
        )

    @staticmethod
    @pytest.mark.slow
    def test_ast_selected_apply_preserves_unmatched_ast_and_text_sources(
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Selected authenticated fixes do not execute other rules or callbacks."""
        tm.ok(u.Tests.create_python_environment(mod_workspace))
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                name: (
                    f"id: {name}\nlanguage: Python\nseverity: warning\n"
                    f'rule:\n  pattern: {name} = "before"\n'
                    f'fix: {name} = "after"\n'
                )
                for name in ("selected", "unselected")
            },
        )
        sample = mod_workspace / "selection.py"
        stem = u.derive_class_stem(mod_workspace.name.replace("_", "-"))
        source = (
            '"""Selection fixture."""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n    pass\n\n\n"
            f"class {stem}Selection:\n"
            '    """Independent rule targets."""\n\n'
            '    selected = "before"\n'
            '    unselected = "before"\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(sample, source))
        untouched = mod_workspace / "sample.py"
        untouched_before = untouched.read_bytes()
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n  - id: text-sentinel\n"
                "    include: ['selection.py']\n"
                "    find: 'before'\n    replace: 'text-phase-ran'\n",
            )
        )
        exit_code = main([
            "refactor",
            "ast",
            "--repository-root",
            str(mod_workspace),
            "--rules",
            "selected",
            "--apply",
        ])
        capture = capsys.readouterr()
        console = capture.out + capture.err
        tm.that(exit_code, eq=0, msg=console)
        tm.that(
            sample.read_text(encoding=c.DEFAULT_ENCODING),
            eq=source.replace('selected = "before"', 'selected = "after"', 1),
        )
        tm.that(untouched.read_bytes(), eq=untouched_before)
        tm.that(console, has="whole-catalog before=")
        tm.that(console, has="text phases=0 semantic callbacks=0; corpus=full")
        tm.that(console, lacks="apply sed-by-list cascade")
        tm.that(console, lacks="mod: phase ")
        report = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(report.totals_by_rule.get("unselected"), eq=1)
        tm.that(report.totals_by_rule.get("selected", 0), eq=0)
        destination = mod_workspace / c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        before_paths = tuple(
            (destination.parent / destination.stem).glob("*/before.json")
        )
        tm.that(len(before_paths), eq=1)
        before_evidence = m.Infra.ModScanEvidence.model_validate_json(
            before_paths[0].read_bytes(),
        )
        after_evidence = m.Infra.ModScanEvidence.model_validate_json(
            before_paths[0].with_name("after.json").read_bytes(),
        )
        tm.that(before_evidence.totals_by_rule.get("selected"), eq=1)
        tm.that(after_evidence.totals_by_rule.get("selected", 0), eq=0)
        tm.that(after_evidence.totals_by_rule.get("unselected"), eq=1)
        runtime = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "import runpy, sys; namespace = runpy.run_path(sys.argv[1]); "
                        "consumer = namespace[sys.argv[2]]; "
                        "print(consumer.selected, consumer.unselected)"
                    ),
                    str(sample),
                    f"{stem}Selection",
                ),
                cwd=mod_workspace,
            )
        )
        tm.that(runtime.outcome.raw_return_code, eq=0)
        tm.that(runtime.stdout.strip(), eq="after before")
        tm.that(runtime.stderr, eq="")

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("apply", [False, True])
    def test_default_ast_scan_and_apply_reject_warning_findings_without_fix(
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
        *,
        apply: bool,
    ) -> None:
        """Mechanical quiescence cannot accept a warning-level no-fix finding."""
        rule_id = "no-fix-warning"
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                rule_id: (
                    f"id: {rule_id}\nlanguage: Python\nseverity: warning\n"
                    'rule:\n  pattern: value = "unresolved"\n'
                ),
            },
        )
        sample = mod_workspace / "sample.py"
        stem = u.derive_class_stem(mod_workspace.name.replace("_", "-"))
        source = (
            '"""Warning-only fixture."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"class {stem}Sample:\n"
            '    """A deliberately unresolved native finding."""\n\n'
            '    value = "unresolved"\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(sample, source))
        exit_code = main([
            "refactor",
            "ast",
            "--repository-root",
            str(mod_workspace),
            *(["--apply"] if apply else []),
        ])
        capture = capsys.readouterr()
        tm.that(exit_code, ne=0, msg=capture.out + capture.err)
        tm.that(capture.out + capture.err, lacks="mechanical fixed point verified")
        evidence = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        entries = tuple(entry for entry in evidence.entries if entry.rule_id == rule_id)
        tm.that(len(entries), eq=1)
        tm.that(entries[0].actionable, eq=False)
        tm.that(
            entries[0].classification, eq=c.Infra.ModScanFindingClass.DETECTION_ONLY
        )
        tm.that(entries[0].payload["severity"], eq="warning")
        tm.that(sample.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    @pytest.mark.slow
    def test_failed_selected_apply_keeps_native_cause_when_after_scan_fails(
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A real receipt rejection retains accepted bytes and its primary cause."""
        tm.ok(u.Tests.create_python_environment(mod_workspace))
        rule_id = "selected-receipt"
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                rule_id: (
                    f"id: {rule_id}\nlanguage: Python\nseverity: warning\n"
                    'rule:\n  pattern: selected = "before"\n'
                    'fix: selected = "after"\n'
                    "metadata:\n  expected: 1\n"
                ),
            },
        )
        sample = mod_workspace / "receipt.py"
        stem = u.derive_class_stem(mod_workspace.name.replace("_", "-"))
        source = (
            '"""Selected receipt consumer."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"class {stem}Receipt:\n"
            '    """A native selected-rule target."""\n\n'
            '    selected = "before"\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(sample, source))
        result = FlextInfraCodemodAstScan(
            repository_root=mod_workspace,
            rules=rule_id,
            apply_changes=True,
        ).execute()
        expected = f"ast-grep rule {rule_id} declares 1 finding(s), scan produced 0"
        tm.fail(result, has=expected)
        tm.that(result.error, eq=expected)
        capture = capsys.readouterr()
        tm.that(capture.err, has="secondary whole-catalog after scan failure")
        tm.that(capture.err, has=expected)
        tm.that(capture.err, has="accepted writes retained; no rollback performed")
        tm.that(
            sample.read_text(encoding=c.DEFAULT_ENCODING),
            eq=source.replace('selected = "before"', 'selected = "after"'),
        )
        destination = mod_workspace / c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        before_paths = tuple(
            (destination.parent / destination.stem).glob("*/before.json")
        )
        tm.that(len(before_paths), eq=1)
        before = m.Infra.ModScanEvidence.model_validate_json(
            before_paths[0].read_bytes()
        )
        tm.that(before.totals_by_rule.get(rule_id), eq=1)
        tm.that(before_paths[0].with_name("after.json").exists(), eq=False)

    @staticmethod
    @pytest.mark.slow
    def test_failed_mechanical_cycle_retains_accepted_rewrite(
        mod_workspace: Path,
    ) -> None:
        """A real syntax cycle fails without restoring its initial source."""
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                name: (
                    f"id: {name}\nlanguage: Python\nseverity: warning\n"
                    "rule:\n"
                    f"  pattern: value = {before}()\n"
                    f"fix: value = {after}()\n"
                )
                for name, before, after in (
                    ("start", "dict", "list"),
                    ("forward", "list", "tuple"),
                    ("cycle", "tuple", "list"),
                )
            },
        )
        module = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(module, "value = dict()\n"))

        outcome = FlextInfraCodemodAstScan(
            repository_root=mod_workspace,
            apply_changes=True,
        ).execute()

        tm.fail(outcome, has="made no progress")
        retained = module.read_text(encoding="utf-8")
        tm.that(retained, lacks="value = dict()")
        tm.that(retained, has="value = list()")

    @staticmethod
    def test_failed_publication_preserves_progress_and_newer_source(
        mod_workspace: Path,
    ) -> None:
        """A stale next batch cannot undo an accepted batch or a newer edit."""
        accepted = mod_workspace / "accepted.py"
        unrelated = mod_workspace / "unrelated.py"
        for path in (accepted, unrelated):
            tm.ok(u.Cli.atomic_write_text_file(path, 'value = "original"\n'))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(accepted, required=True))
        stale = tm.ok(u.Cli.atomic_read_binary_file_state(unrelated, required=True))
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (
                    m.Infra.SemanticFilePlan(
                        project=mod_workspace,
                        path=accepted,
                        before=before,
                        desired_content=b'value = "accepted"\n',
                        desired_mode=before.mode,
                    ),
                ),
                repository_root=mod_workspace,
            ),
        )
        newer = 'value = "newer independent edit"\n'
        tm.ok(u.Cli.atomic_write_text_file(unrelated, newer))
        published = accepted.read_bytes()
        next_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(accepted, required=True),
        )

        outcome = FlextInfraSemanticPublication.publish_semantic_file_plans(
            (
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=accepted,
                    before=next_before,
                    desired_content=b'value = "next pass"\n',
                    desired_mode=next_before.mode,
                ),
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=unrelated,
                    before=stale,
                    desired_content=b'value = "stale replacement"\n',
                    desired_mode=stale.mode,
                ),
            ),
            repository_root=mod_workspace,
        )

        tm.fail(outcome)
        tm.that(accepted.read_bytes(), eq=published)
        tm.that(unrelated.read_text(encoding="utf-8"), eq=newer)

    @staticmethod
    def test_formatter_exception_preserves_preexisting_accepted_progress(
        mod_workspace: Path,
    ) -> None:
        """A later formatter failure leaves accepted and unrelated files intact."""
        accepted = mod_workspace / "accepted.py"
        unrelated = mod_workspace / "unrelated.py"
        source = 'value = "accepted"\n'
        newer = 'value = "newer independent edit"\n'
        tm.ok(u.Cli.atomic_write_text_file(accepted, source))
        tm.ok(u.Cli.atomic_write_text_file(unrelated, newer))

        with pytest.raises(RuntimeError, match="failed"):
            FlextInfraCodemodSemanticApply.apply_transaction_paths(
                mod_workspace,
                (
                    m.Infra.SemanticMigrationEdit(
                        file_path=accepted,
                        original_source=source,
                        updated_source="value = (\n",
                        changes=("real formatter rejection",),
                    ),
                ),
            )

        tm.that(accepted.read_text(encoding="utf-8"), eq=source)
        tm.that(unrelated.read_text(encoding="utf-8"), eq=newer)
