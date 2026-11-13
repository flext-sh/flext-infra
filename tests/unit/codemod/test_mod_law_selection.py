"""Theme selection contract of ``refactor mod`` (ADR-028 Decision 18 item 2).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraCli
from flext_infra.codemod import FlextInfraModGateEngine, FlextInfraModTextGateEngine
from tests import c, t, tm, u


@c.Tests.MARK.slow
class TestsFlextInfraModLawSelection:
    """Drive the public ``refactor mod`` route and law expansion facade.

    Every expected rule id and law is derived from the repository's own plan
    and the derived enforcement catalog, never from a hand-kept list.
    """

    @staticmethod
    def _run(root: Path, *arguments: str) -> int:
        return FlextInfraCli.infra_main([
            "refactor",
            "mod",
            "--repository-root",
            str(root),
            *arguments,
        ])

    @staticmethod
    def _plan_laws(root: Path) -> tuple[frozenset[str], dict[str, frozenset[str]]]:
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            plan = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        claims = {rule.id: frozenset(rule.enforce) for rule in plan.rules}
        return frozenset().union(*claims.values()), claims

    @staticmethod
    def test_unselected_run_is_refused(
        mod_workspace: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """A run without a theme is a global make and fails before any scan."""
        source = mod_workspace / "unselected.py"
        tm.ok(u.Cli.atomic_write_text_file(source, 'value = "before"\n'))
        original = source.read_bytes()
        exit_code = TestsFlextInfraModLawSelection._run(mod_workspace)
        console = capsys.readouterr()
        tm.that(exit_code, ne=0)
        tm.that(console.out + console.err, has="ADR-028 Decision 18 item 2")
        tm.that(source.read_bytes(), eq=original)

    @staticmethod
    def test_unknown_law_fails_loud(
        mod_workspace: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """A law no active owner claims fails once, before any repository runs."""
        catalog = tm.ok(u.Infra.enforcement_catalog())
        claimed = frozenset(claim.id for claim in catalog.claims if claim.active)
        unknown = next(
            law
            for number in range(1000)
            if (law := f"ENFORCE-{number:03d}") not in claimed
        )
        exit_code = TestsFlextInfraModLawSelection._run(
            mod_workspace, "--check", "--laws", unknown
        )
        console = capsys.readouterr()
        tm.that(exit_code, ne=0)
        tm.that(console.out + console.err, has=unknown)
        tm.that(console.out + console.err, has="no active owner claims")

    @staticmethod
    def test_laws_expand_to_every_planned_rule_claiming_them(
        mod_workspace: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """The repository plan's static and generated rules of the law are selected."""
        planned, claims = TestsFlextInfraModLawSelection._plan_laws(mod_workspace)
        tm.that(planned, ne=frozenset())
        law = min(planned)
        expected = frozenset(rule for rule, laws in claims.items() if law in laws)
        with u.Infra.codemod_workspace_snapshot(mod_workspace) as snapshot:
            expanded = tm.ok(u.Infra.codemod_law_rule_ids(snapshot, frozenset({law})))
        tm.that(frozenset(expanded), eq=expected)
        tm.that(len(expanded), eq=len(expected))
        TestsFlextInfraModLawSelection._run(mod_workspace, "--check", "--laws", law)
        console = capsys.readouterr()
        tm.that(
            console.out + console.err,
            has=f"laws expand to {len(expected)} rule(s)",
        )

    @staticmethod
    def test_repository_without_the_law_gets_an_empty_plan(
        mod_workspace: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """A catalog law no planned rule of this repository claims checks nothing."""
        planned, _claims = TestsFlextInfraModLawSelection._plan_laws(mod_workspace)
        catalog = tm.ok(u.Infra.enforcement_catalog())
        absent = sorted(
            frozenset(claim.id for claim in catalog.claims if claim.active) - planned
        )
        tm.that(absent, ne=[])
        law = absent[0]
        with u.Infra.codemod_workspace_snapshot(mod_workspace) as snapshot:
            expanded = tm.ok(u.Infra.codemod_law_rule_ids(snapshot, frozenset({law})))
        tm.that(expanded, eq=())
        exit_code = TestsFlextInfraModLawSelection._run(
            mod_workspace, "--check", "--laws", law
        )
        console = capsys.readouterr()
        tm.that(exit_code, eq=0, msg=console.out + console.err)
        tm.that(console.out + console.err, has="no planned rule")

    @staticmethod
    def test_unselected_verdict_does_not_fail_a_selected_run(
        mod_workspace: Path,
        capsys: t.Tests.CaptureFixture[str],
    ) -> None:
        """A selected theme owns no text verdict: an unrelated finding stays out."""
        target = mod_workspace / "selected.py"
        source = 'from __future__ import annotations\n\nvalue = "stable"\n'
        tm.ok(u.Cli.atomic_write_text_file(target, source))
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: unselected-detection\n"
                "    include: ['selected.py']\n"
                "    find: 'stable'\n"
                "    replace: 'stable'\n",
            ),
        )
        pending = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False))
        tm.that(pending.findings, ne=0)
        selected = TestsFlextInfraModLawSelection._run(
            mod_workspace, "--rule-ids", "require-future-annotations"
        )
        console = capsys.readouterr()
        tm.that(selected, eq=0, msg=console.out + console.err)
        tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def test_selected_scan_binds_other_rules_only_where_the_selection_matches(
        mod_workspace: Path,
    ) -> None:
        """A focused scan locates its selection, then scans only those files."""
        rule_id = "require-future-annotations"
        matched = mod_workspace / "matched.py"
        clean = mod_workspace / "clean.py"
        tm.ok(u.Cli.atomic_write_text_file(matched, 'value = "before"\n'))
        tm.ok(
            u.Cli.atomic_write_text_file(
                clean, 'from __future__ import annotations\n\nvalue = "kept"\n'
            )
        )
        with u.Infra.codemod_workspace_snapshot(mod_workspace) as snapshot:
            complete = tm.ok(u.Infra.codemod_rule_plan(snapshot))
            focused = tm.ok(u.Infra.codemod_rule_plan(snapshot, rule_ids=(rule_id,)))
        tm.that(complete.selected_rule_ids, none=True)
        tm.that(focused.selected_rule_ids, eq=(rule_id,))
        binding = frozenset(rule.id for rule in focused.rules) - {rule_id}
        header = f"{c.Infra.CODEMOD_IMPORT_HEADER_SHAPE}"
        tm.that(all(rule.startswith(header) for rule in binding), eq=True)
        tm.that(
            binding,
            eq=frozenset(
                rule.id for rule in complete.rules if rule.id.startswith(header)
            ),
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(mod_workspace, fix=False, selection=focused)
        )
        tm.that(report.source_files, eq=(matched.resolve(),))
        tm.that(
            {mod_workspace.resolve() / path for path in report.files},
            eq={matched.resolve()},
        )
        tm.that({entry.rule_id for entry in report.entries} >= {rule_id}, eq=True)
        tm.that(report.rule_plan, eq=focused)

    @staticmethod
    def test_selected_rule_keeps_the_generated_utilities_it_references(
        mod_workspace: Path,
    ) -> None:
        """A selected catalog rule calling a generated utility still scans."""
        rule_id = "rewire-collapsed-family-package"
        with u.Infra.codemod_workspace_snapshot(mod_workspace) as snapshot:
            focused = tm.ok(u.Infra.codemod_rule_plan(snapshot, rule_ids=(rule_id,)))
        tm.that(c.Infra.CODEMOD_GENERATED_PROVIDER in focused.provider_order, eq=True)
        tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False, selection=focused))
