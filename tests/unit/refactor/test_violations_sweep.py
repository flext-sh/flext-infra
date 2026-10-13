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


class TestsFlextInfraRefactorViolationsSweep:
    """Behavior contract for the ``refactor violations-sweep`` verb."""

    @staticmethod
    def _makefile(recipe: str = "", *, first_only: bool = False) -> str:
        """Provide the configured operations without freezing the Make policy."""
        verbs = config.Infra.codegen.make.violations_sweep_repair_verbs
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
        tm.that(list(second.rule_deltas), eq=list(first.rule_deltas))
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
        self._prepare(root, makefile=RECORDING_MAKEFILE, local_rule=True)
        tm.that(
            main([
                c.Infra.CLI_GROUP_REFACTOR,
                c.Infra.VIOLATIONS_SWEEP_ROUTE_NAME,
                "--repository-root",
                str(root),
                "--rules",
                "sweep-growth",
            ]),
            ne=0,
        )
        tm.that((root / "ran.txt").exists(), eq=False)
