"""Refactor violations-sweep: repair through the canonical verbs, prove reduction.

Cases drive the public ``refactor violations-sweep`` CLI or service over the real
mod-workspace fixture with a recording Makefile standing in for the repair
verbs, so the sweep's own scans, receipt, and always-reducing verdict are the
behavior under test.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, main, u
from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.refactor import FlextInfraRefactorViolationsSweep
from tests import tm

if TYPE_CHECKING:
    from collections.abc import Iterator


LOCAL_RULE_CATALOG = "ruleDirs:\n  - rules\ntestConfigs: []\n"

LOCAL_GROWTH_RULE = (
    "id: sweep-growth\n"
    "language: Python\n"
    "rule:\n"
    "  pattern: marker = dict()\n"
    "fix: marker = tuple()\n"
    "severity: warning\n"
)


@pytest.mark.slow
class TestsFlextInfraRefactorViolationsSweep:
    """Behavior contract for the ``refactor violations-sweep`` verb."""

    def test_public_utility_deltas_preserve_native_scan_indexes_and_multiplicity(
        self,
        mod_workspace: Path,
    ) -> None:
        """The single utility owner retains complete per-rule evidence fields."""
        self._prepare(mod_workspace, makefile=self._makefile(), local_rule=True)
        sample = mod_workspace / "sample.py"
        tm.ok(
            u.Cli.atomic_write_text_file(sample, "marker = dict()\nmarker = dict()\n")
        )
        before = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = tuple()\n"))
        after = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        plan = tm.ok(u.Infra.codemod_rule_plan(mod_workspace))
        inventory = tuple(
            (project.name, rule.id)
            for project in u.Infra.governed_project_roots(mod_workspace)
            for rule in plan.rules
        )
        deltas = u.Infra.rule_deltas(before, after, inventory=inventory)
        tm.that({(row.repository, row.rule_id) for row in deltas}, eq=set(inventory))
        delta = next(row for row in deltas if row.rule_id == "sweep-growth")
        tm.that((delta.before, delta.after, delta.resolved), eq=(2, 0, 2))
        tm.that((delta.persisted, delta.introduced), eq=(0, 0))
        tm.that(
            delta.before_entries,
            eq=tuple(
                index
                for index, entry in enumerate(before.entries)
                if entry.rule_id == delta.rule_id
            ),
        )
        tm.that(delta.after_entries, eq=())
        tm.that(delta.semantic_correspondence_proven, eq=False)

    @staticmethod
    def _makefile(recipe: str = "", *, first_only: bool = False) -> str:
        """Provide the configured operations without freezing the Make policy.

        Returns:
            An executable Makefile derived from the current canonical verb policy.
        """
        verbs = tuple(
            dict.fromkeys(config.Infra.codegen.make.violations_sweep_repair_verbs)
        )
        names = " ".join(verbs)
        recording = "\t@printf '%s\\n' '$@' >> ran.txt\n"
        if first_only:
            return f".PHONY: {names}\n{verbs[0]}:\n{recording}{recipe}" + (
                f"{' '.join(verbs[1:])}:\n\t@true\n" if len(verbs) > 1 else ""
            )
        return f".PHONY: {names}\n{names}:\n{recording}{recipe}"

    @staticmethod
    def _prepare(root: Path, *, makefile: str, local_rule: bool) -> None:
        """Install the recording repair surface and the optional growth rule."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.MAKEFILE_FILENAME,
                makefile,
            ),
        )
        if local_rule:
            config_path = root / c.Infra.CODEMOD_CONFIG_RELPATH
            rules = config_path.parent / c.Cli.RULES_DIR_NAME
            tm.ok(u.Cli.ensure_dir(rules))
            tm.ok(u.Cli.atomic_write_text_file(config_path, LOCAL_RULE_CATALOG))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rules / "sweep.yml",
                    LOCAL_GROWTH_RULE,
                ),
            )

    @staticmethod
    def _sweep(root: Path, *options: str) -> int:
        """Run the public violations-sweep CLI once.

        Returns:
            The resulting ``int``.

        """
        return main([
            c.Infra.CLI_GROUP_REFACTOR,
            c.Infra.VIOLATIONS_SWEEP_ROUTE_NAME,
            "--repository-root",
            str(root),
            *options,
        ])

    @staticmethod
    def _receipt(root: Path) -> m.Infra.ViolationsSweepReport:
        """Load the typed receipt the verb publishes.

        Returns:
            The resulting ``m.Infra.ViolationsSweepReport``.

        """
        path = root / c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        return m.Infra.ViolationsSweepReport.model_validate_json(
            path.read_bytes(),
        )

    @staticmethod
    def _verbs_ran(root: Path) -> Iterator[str]:
        """Yield the repair verbs the recording Makefile observed.

        Yields:
            Each recorded verb name.

        """
        lines = (root / "ran.txt").read_text(encoding="utf-8").splitlines()
        yield from (line for line in lines if line)

    def test_clean_tree_is_a_no_op_success_with_zero_delta(
        self,
        mod_workspace: Path,
    ) -> None:
        """The canonical sequence runs in order and no total moves."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=False)

        tm.that(self._sweep(root), eq=0)

        tm.that(
            list(self._verbs_ran(root)),
            eq=list(config.Infra.codegen.make.violations_sweep_repair_verbs),
        )
        report = self._receipt(root)
        tm.that(
            report.schema_version,
            eq=c.Infra.VIOLATIONS_SWEEP_REPORT_SCHEMA_VERSION,
        )
        tm.that(report.before, eq=report.after)
        tm.that(report.increased_totals, eq=())
        for field in ("before_source_sha256", "after_source_sha256"):
            with pytest.raises(ValueError, match=field):
                m.Infra.ViolationsSweepReport.model_validate(
                    report.model_dump(exclude={field}),
                )

    def test_rerun_preserves_prior_evidence_with_identical_counts(
        self,
        mod_workspace: Path,
    ) -> None:
        """A second sweep preserves the first invocation's authenticated snapshots."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=False)
        tm.that(self._sweep(root), eq=0)
        first = self._receipt(root)
        assert first.before_evidence is not None
        assert first.after_evidence is not None
        before_bytes = first.before_evidence.path.read_bytes()
        after_bytes = first.after_evidence.path.read_bytes()

        tm.that(self._sweep(root), eq=0)

        second = self._receipt(root)
        assert second.before_evidence is not None
        assert second.after_evidence is not None
        tm.that(second.before, eq=first.before)
        tm.that(
            [
                row.model_dump_json(exclude={"before_entries", "after_entries"})
                for row in second.rule_deltas
            ],
            eq=[
                row.model_dump_json(exclude={"before_entries", "after_entries"})
                for row in first.rule_deltas
            ],
        )
        tm.that(second.before_evidence.path, ne=first.before_evidence.path)
        tm.that(first.before_evidence.path.read_bytes(), eq=before_bytes)
        tm.that(first.after_evidence.path.read_bytes(), eq=after_bytes)
        tm.that(u.Cli.sha256_bytes(before_bytes), eq=first.before_evidence.sha256)
        tm.that(u.Cli.sha256_bytes(after_bytes), eq=first.after_evidence.sha256)

    def test_growing_total_fails_and_still_publishes_the_receipt(
        self,
        mod_workspace: Path,
    ) -> None:
        """A repair verb that adds a violation fails the command.

        The planted ``violating.py`` trips the local growth rule and the
        catalog's own detection rules, so the exact class mix is the
        catalog's; the law under test is that every total only moves down.
        """
        root = mod_workspace
        self._prepare(
            root,
            makefile=self._makefile("\t@printf 'marker = dict()\\n' > violating.py\n"),
            local_rule=True,
        )

        tm.that(self._sweep(root), ne=0)

        report = self._receipt(root)
        tm.that(
            "findings" in report.increased_totals,
            eq=True,
        )
        tm.that(
            report.after.findings > report.before.findings,
            eq=True,
        )

    @pytest.mark.parametrize("original_count", [1, 2])
    def test_equal_or_lower_total_cannot_hide_introduced_occurrences(
        self,
        mod_workspace: Path,
        original_count: int,
    ) -> None:
        """Replacing old findings with a new file is not monotonic reduction."""
        root = mod_workspace
        self._prepare(
            root,
            makefile=self._makefile(
                "\t@rm original*.py\n\t@printf 'marker = dict()\\n' > introduced.py\n",
                first_only=True,
            ),
            local_rule=True,
        )
        for index in range(original_count):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    root / f"original{index}.py",
                    "marker = dict()\n",
                )
            )
        tm.that(self._sweep(root), ne=0)
        report = self._receipt(root)
        delta = next(row for row in report.rule_deltas if row.rule_id == "sweep-growth")
        tm.that(delta.before, eq=original_count)
        tm.that(delta.after, eq=1)
        tm.that(delta.resolved, eq=original_count)
        tm.that(delta.introduced, eq=1)

    def test_failed_repair_publishes_partial_after_evidence(
        self,
        mod_workspace: Path,
    ) -> None:
        """A failed verb stops repairs but does not erase its source effects."""
        root = mod_workspace
        self._prepare(
            root,
            makefile=self._makefile(
                "\t@printf 'marker = dict()\\n' > introduced.py\n\t@false\n",
                first_only=True,
            ),
            local_rule=True,
        )
        tm.that(self._sweep(root), ne=0)
        report = self._receipt(root)
        tm.that(
            report.failed_verb,
            eq=config.Infra.codegen.make.violations_sweep_repair_verbs[0],
        )
        tm.that(report.completed_verbs, eq=())
        tm.that(bool(report.repair_error), eq=True)
        delta = next(row for row in report.rule_deltas if row.rule_id == "sweep-growth")
        tm.that(delta.introduced, eq=1)
        assert report.before_evidence is not None
        assert report.after_evidence is not None
        assert report.after_source_sha256 is not None
        tm.that(delta.semantic_correspondence_proven, eq=False)
        tm.that(len(delta.before_entries), eq=delta.before)
        tm.that(len(delta.after_entries), eq=delta.after)
        for index in delta.after_entries:
            entry = report.after_evidence.evidence.entries[index]
            tm.that(entry.rule_id, eq=delta.rule_id)
            tm.that(bool(entry.range), eq=True)
            assert entry.source_state is not None
            assert entry.source_state.content is not None
            tm.that(
                report.after_source_sha256[str(entry.source_state.path)],
                eq=u.Cli.sha256_bytes(entry.source_state.content),
            )

    def test_clean_local_rule_retains_zero_inventory_and_provider_identity(
        self,
        mod_workspace: Path,
    ) -> None:
        """An elected rule and governed project remain visible with no findings."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.that(self._sweep(root), eq=0)
        report = self._receipt(root)
        assert report.before_evidence is not None
        assert report.before_plan is not None
        rows = {(row.repository, row.rule_id) for row in report.rule_deltas}
        expected = {
            (project.name, rule.id)
            for project in u.Infra.governed_project_roots(root)
            for rule in report.before_plan.rules
        }
        tm.that(rows, eq=expected)
        delta = next(row for row in report.rule_deltas if row.rule_id == "sweep-growth")
        tm.that((delta.before, delta.after, delta.introduced), eq=(0, 0, 0))
        rule = next(
            rule for rule in report.before_plan.rules if rule.id == delta.rule_id
        )
        tm.that(bool(rule.digest), eq=True)
        tm.that(
            report.before_source_sha256[str(rule.resource.resolve())],
            eq=u.Cli.sha256_bytes(rule.resource.read_bytes()),
        )
        tm.that(bool(rule.provider), eq=True)

    @pytest.mark.parametrize("secondary", ["scan", "publication"])
    def test_first_repair_failure_survives_secondary_failure(
        self,
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
        secondary: str,
    ) -> None:
        """Real filesystem failures must not replace the first Make diagnostic."""
        root = mod_workspace
        broken = (
            root / c.Infra.CODEMOD_CONFIG_RELPATH
            if secondary == "scan"
            else root / c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        )
        sabotage = (
            f"\t@printf 'invalid: [\\n' > '{broken}'\n"
            if secondary == "scan"
            else f"\t@mkdir -p '{broken}'\n"
        )
        self._prepare(
            root,
            makefile=self._makefile(
                sabotage + "\t@printf 'original-repair-failure\\n' >&2\n\t@false\n",
                first_only=True,
            ),
            local_rule=True,
        )
        result = FlextInfraRefactorViolationsSweep(repository_root=root).execute()
        tm.fail(result, has="original-repair-failure")
        captured = capsys.readouterr()
        tm.that("secondary" in captured.err, eq=True)
        tm.that(
            list(self._verbs_ran(root)),
            eq=[config.Infra.codegen.make.violations_sweep_repair_verbs[0]],
        )
        if secondary == "scan":
            report = self._receipt(root)
            tm.that("original-repair-failure" in (report.repair_error or ""), eq=True)
            tm.that(bool(report.after_scan_error), eq=True)
            tm.that(report.after_evidence, eq=None)
            tm.that(report.after_source_sha256, eq=None)
            with pytest.raises(
                ValueError, match="requires an authenticated after scan"
            ):
                _ = report.increased_totals

    def test_detection_only_occurrences_persist_without_false_resolution(
        self,
        mod_workspace: Path,
    ) -> None:
        """Repeated unchanged detect-only matches remain separate occurrences."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root
                / c.Infra.CODEMOD_CONFIG_RELPATH.parent
                / c.Cli.RULES_DIR_NAME
                / "sweep.yml",
                LOCAL_GROWTH_RULE.replace("fix: marker = tuple()\n", ""),
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "unchanged.py",
                "marker = dict()\nmarker = dict()\n",
            )
        )
        tm.that(self._sweep(root), eq=0)
        delta = next(
            row
            for row in self._receipt(root).rule_deltas
            if row.rule_id == "sweep-growth"
        )
        tm.that(delta.before, eq=2)
        tm.that(delta.persisted, eq=2)
        tm.that(delta.resolved, eq=0)
        tm.that(delta.introduced, eq=0)

    def test_selected_rule_cannot_invoke_unfiltered_repairs(
        self,
        mod_workspace: Path,
    ) -> None:
        """An unsupported isolation request fails before any Make side effect."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.that(
            main([
                c.Infra.CLI_GROUP_REFACTOR,
                c.Infra.VIOLATIONS_SWEEP_ROUTE_NAME,
                "--repository-root",
                str(root),
                "--rules",
                "sweep-growth",
                "--repair-verbs",
                "gen",
            ]),
            ne=0,
        )
        tm.that((root / "ran.txt").exists(), eq=False)

    def test_native_rule_audit_never_invokes_make_and_keeps_collateral(
        self,
        mod_workspace: Path,
    ) -> None:
        """Read-only audit observes every elected rule, plus real Ruff and text."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.ok(u.Cli.atomic_write_text_file(root / "sample.py", "marker = dict()\n"))
        tm.that(self._sweep(root, "--audit-rules", "--rules", "sweep-growth"), eq=0)
        tm.that((root / "ran.txt").exists(), eq=False)
        report = self._receipt(root)
        stage = report.stages[0]
        tm.that(stage.verb, eq="audit-rules")
        tm.that(stage.outcome, eq=None)
        tm.that(stage.source_inventory_unchanged, eq=True)
        assert stage.audit_before is not None
        assert stage.audit_after is not None
        tm.that(stage.audit_before.text_report is not None, eq=True)
        tm.that(stage.audit_after.text_report is not None, eq=True)
        tm.that(stage.audit_before.lint is not None, eq=True)
        tm.that(stage.audit_after.lint is not None, eq=True)
        tm.that(any((stage.introduced_lint or {}).values()), eq=False)
        tm.that(stage.introduced_text, eq=())
        row = next(
            row for row in stage.rule_evaluations if row.rule_id == "sweep-growth"
        )
        tm.that(row.status, eq="observed")
        assert row.delta is not None
        tm.that(row.delta.persisted, eq=1)
        tm.that(row.delta.resolved, eq=0)
        tm.that(row.delta.introduced, eq=0)

    def test_public_sequence_records_each_canonical_operation(
        self,
        mod_workspace: Path,
    ) -> None:
        """Generation, namespace repair and audit have separate process receipts."""
        root = mod_workspace
        verbs = ("gen", "fix-namespace", "audit")
        names = " ".join(verbs)
        self._prepare(
            root,
            makefile=f".PHONY: {names}\n{names}:\n\t@printf '%s\\n' '$@' >> ran.txt\n",
            local_rule=True,
        )
        tm.that(self._sweep(root, "--repair-verbs", ",".join(verbs)), eq=0)
        report = self._receipt(root)
        tm.that(list(report.repair_verbs), eq=list(verbs))
        tm.that(list(self._verbs_ran(root)), eq=list(verbs))
        for stage in report.stages:
            tm.that(stage.cwd, eq=root.resolve())
            tm.that(stage.invoked, eq=True)
            assert stage.outcome is not None
            tm.that(u.Cli.process_succeeded(stage.outcome), eq=True)
            tm.that(stage.outcome.timed_out, eq=False)
            tm.that(stage.duration >= 0, eq=True)
        audit = report.stages[-1]
        tm.that(audit.source_inventory_unchanged, eq=True)
        assert audit.audit_before is not None
        assert audit.audit_after is not None
        tm.that(audit.audit_before.sha256, eq=audit.audit_after.sha256)

    @pytest.mark.parametrize(
        ("option", "value"),
        [
            ("--rules", "unknown-sweep-rule"),
            ("--repair-verbs", "gen; printf bypass"),
            ("--repair-verbs", ""),
            ("--repair-verbs", "test-file"),
        ],
    )
    def test_invalid_selection_fails_before_make(
        self,
        mod_workspace: Path,
        option: str,
        value: str,
    ) -> None:
        """Undeclared rules, shell payloads and argument-bearing verbs never run."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.that(self._sweep(root, option, value), ne=0)
        tm.that((root / "ran.txt").exists(), eq=False)

    @pytest.mark.parametrize("fail", [False, True])
    @pytest.mark.parametrize("mutation", ["introduce", "resolve"])
    def test_audit_focus_keeps_cross_rule_and_mutation_failures(
        self,
        mod_workspace: Path,
        fail: bool,
        mutation: str,
    ) -> None:
        """Audit cannot rewrite sources or hide findings outside the focus."""
        root = mod_workspace
        replacement = "dict" if mutation == "introduce" else "tuple"
        self._prepare(
            root,
            makefile=(
                ".PHONY: audit\naudit:\n"
                f"\t@printf 'marker = {replacement}()\\n' > changed.py\n"
                + (
                    "\t@printf 'original-audit-failure\\n' >&2\n\t@false\n"
                    if fail
                    else ""
                )
            ),
            local_rule=True,
        )
        if mutation == "resolve":
            tm.ok(
                u.Cli.atomic_write_text_file(root / "changed.py", "marker = dict()\n")
            )
        plan = tm.ok(u.Infra.codemod_rule_plan(root))
        focus = next(rule.id for rule in plan.rules if rule.id != "sweep-growth")
        result = FlextInfraRefactorViolationsSweep(
            repository_root=root,
            repair_verbs="audit",
            rules=focus,
        ).execute()
        tm.fail(result, has="original-audit-failure" if fail else "audit changed")
        report = self._receipt(root)
        tm.that(list(report.focused_rule_ids), eq=[focus])
        stage = report.stages[0]
        tm.that(stage.source_inventory_unchanged, eq=False)
        tm.that(bool(stage.inspection_error), eq=True)
        assert stage.audit_after is not None
        assert report.after_evidence is not None
        tm.that(
            {row.rule_id for row in report.rule_deltas},
            eq={rule.id for rule in plan.rules},
        )
        row = next(row for row in report.rule_deltas if row.rule_id == "sweep-growth")
        tm.that(row.introduced if mutation == "introduce" else row.resolved, eq=1)

    def test_audit_verdicts_are_independent_for_discovered_members(
        self,
        mod_workspace: Path,
    ) -> None:
        """Root success cannot hide a member failure or prevent later audits."""
        root = mod_workspace
        self._prepare(
            root, makefile=".PHONY: audit\naudit:\n\t@true\n", local_rule=True
        )
        members = (root / "member-fails", root / "member-passes")
        layout = u.Infra.layout(root)
        assert layout is not None
        declarations: list[str] = []
        for member in members:
            tm.ok(u.Cli.ensure_dir(member / c.Infra.DEFAULT_SRC_DIR))
            package = member / c.Infra.DEFAULT_SRC_DIR / layout.package_name
            tm.ok(u.Cli.ensure_dir(package))
            tm.ok(u.Cli.atomic_write_text_file(package / "__init__.py", ""))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    member / c.PYPROJECT_FILENAME,
                    (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                )
            )
            tm.ok(
                u.Cli.atomic_write_text_file(
                    member / c.Infra.DEFAULT_SRC_DIR / "sample.py",
                    "marker = tuple()\n",
                )
            )
            recipe = (
                "\t@printf 'member-audit-failure\\n' >&2\n\t@false\n"
                if member == members[0]
                else "\t@true\n"
            )
            tm.ok(
                u.Cli.atomic_write_text_file(
                    member / c.Infra.MAKEFILE_FILENAME,
                    ".PHONY: audit\naudit:\n" + recipe,
                )
            )
            declarations.append(
                f'[submodule "{member.name}"]\n\tpath = {member.name}\n'
                f"\turl = https://example.com/{member.name}.git\n"
            )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.GITMODULES, "".join(declarations)
            )
        )
        discovered = tuple(u.Infra.governed_project_roots(root))
        tm.that(
            set(discovered),
            eq={root.resolve(), *(member.resolve() for member in members)},
        )
        result = FlextInfraRefactorViolationsSweep(
            repository_root=root,
            repair_verbs="audit,gen",
        ).execute()
        tm.fail(result, has="member-audit-failure")
        report = self._receipt(root)
        tm.that(list(report.repository_roots), eq=list(discovered))
        audits = [stage for stage in report.stages if stage.verb == "audit"]
        tm.that([stage.repository_root for stage in audits], eq=list(discovered))
        for stage in audits:
            tm.that(stage.invoked, eq=True)
            tm.that(stage.source_inventory_unchanged, eq=True)
            assert stage.outcome is not None
            tm.that(
                stage.outcome.raw_return_code == 0,
                eq=stage.repository_root != members[0],
            )
        tm.that(report.stages[-1].invoked, eq=False)
        tm.that(report.stages[-1].outcome, eq=None)
