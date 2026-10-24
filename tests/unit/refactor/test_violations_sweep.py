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

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, m, tm, u
from tests.unit.refactor.violations_sweep_support import (
    LOCAL_GROWTH_RULE,
    TestsFlextInfraRefactorViolationsSweepSupport,
)


@pytest.mark.slow
class TestsFlextInfraRefactorViolationsSweep(
    TestsFlextInfraRefactorViolationsSweepSupport,
):
    """Behavior contract for the ``refactor violations-sweep`` verb: publication."""

    @staticmethod
    def _assert_quiet_baseline(
        root: Path,
        victim: Path,
        quiet_before: m.Infra.ModScanReport,
    ) -> None:
        """Assert the single-rule baseline scans the victim without reporting it.

        Args:
            root: The sweep workspace root.
            victim: The unrelated scanned source path.
            quiet_before: The single-rule baseline scan report.

        """
        tm.that(
            any(
                entry.file == victim.relative_to(root) for entry in quiet_before.entries
            ),
            eq=False,
        )
        source_states = tm.not_none(quiet_before.source_states)
        tm.that(
            any(state.path == victim for state in source_states),
            eq=True,
        )

    @staticmethod
    def _inject_publication_drift(
        parent: Path,
        sample: Path,
        victim: Path,
        drift: str,
    ) -> None:
        """Corrupt the published source identity for one drift scenario.

        Args:
            parent: The source parent directory of the sample.
            sample: The admitted sample source path.
            victim: The unrelated scanned source path.
            drift: The declared drift scenario identifier.

        """
        if drift == "inode":
            replacement = sample.with_suffix(".replacement")
            tm.ok(
                u.Cli.atomic_write_text_file(
                    replacement, sample.read_text(encoding=c.DEFAULT_ENCODING)
                )
            )
            replacement.replace(sample)
        elif drift == "parent":
            preserved = parent.with_name("preserved-source")
            parent.rename(preserved)
            parent.mkdir()
            for child in preserved.iterdir():
                child.rename(parent / child.name)
            preserved.rmdir()
        elif drift == "removed":
            victim.unlink()

    @staticmethod
    def _assert_drift_rejected(
        root: Path,
        before: m.Infra.ModScanReport,
        chain: list[m.Infra.CodegenStagedFile],
        quiet_before: m.Infra.ModScanReport | None,
    ) -> None:
        """Assert identity drift or unexplained removal rejects the deltas.

        Args:
            root: The sweep workspace root.
            before: The baseline scan report.
            chain: The published staged file chain.
            quiet_before: The single-rule baseline scan, when drift removal.

        """
        changed = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        with pytest.raises(ValueError, match=r"identity drift|unexplained removal"):
            u.Infra.rule_deltas(
                before,
                changed,
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )
        if quiet_before is not None:
            quiet_after = tm.ok(
                FlextInfraModGateEngine.scan(
                    root, fix=False, selection=("repair-marker",)
                )
            )
            with pytest.raises(ValueError, match="unexplained removal"):
                u.Infra.rule_deltas(
                    quiet_before,
                    quiet_after,
                    options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
                )

    @pytest.mark.parametrize("drift", ["none", "inode", "parent", "removed"])
    def test_actual_publication_identity_and_complete_resolution_inventory(
        self, mod_workspace: Path, drift: str
    ) -> None:
        """Real admitted states reject byte-identical drift and unexplained deletion."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=False)
        u.Tests.declare_codemod_rules(
            root,
            {
                "repair-marker": LOCAL_GROWTH_RULE.replace(
                    "sweep-growth", "repair-marker"
                ).replace("tuple()", "()"),
                "resolve-future": (
                    "id: resolve-future\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: marker = ()\nfix: |\n"
                    "  from __future__ import annotations\n\n  marker = []\n"
                ),
                "absent-future": (
                    "id: absent-future\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: module\n  not:\n    has:\n"
                    "      pattern: from __future__ import annotations\n"
                ),
            },
        )
        tm.ok(u.Tests.create_python_environment(root))
        parent = root / "src"
        parent.mkdir(exist_ok=True)
        sample, victim = parent / "accounting.py", root / "victim.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n"))
        tm.ok(u.Cli.atomic_write_text_file(victim, "value = 1\n"))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(sample))
        tm.that(
            m.Cli.AtomicFileState.model_validate_json(state.model_dump_json()), eq=state
        )
        before = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        quiet_before = (
            tm.ok(
                FlextInfraModGateEngine.scan(
                    root, fix=False, selection=("repair-marker",)
                )
            )
            if drift == "removed"
            else None
        )
        if quiet_before is not None:
            self._assert_quiet_baseline(root, victim, quiet_before)
        chain: list[m.Infra.CodegenStagedFile] = []
        observed = before
        for index, rule_id in enumerate(("repair-marker", "resolve-future")):
            tm.ok(
                FlextInfraModGateEngine.apply_report(
                    root,
                    tm.ok(
                        FlextInfraModGateEngine.scan(
                            root, fix=False, selection=(rule_id,)
                        )
                    ),
                    exact_replacements=True,
                    published_plans=chain,
                )
            )
            observed = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
            if index == 0:
                u.Infra.rule_deltas(
                    before,
                    observed,
                    options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
                )
                source_states = tm.not_none(observed.source_states)
                admitted = next(item for item in chain if item.before.path == sample)
                tm.that(
                    admitted.replacement,
                    eq=next(item for item in source_states if item.path == sample),
                )
                self._inject_publication_drift(parent, sample, victim, drift)
                if drift != "none":
                    self._assert_drift_rejected(root, before, chain, quiet_before)
        if drift == "none":
            rows = u.Infra.rule_deltas(
                before,
                observed,
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )
            future = next(row for row in rows if row.rule_id == "absent-future")
            tm.that(future.resolved, eq=1)
            tm.ok(future.semantic_correspondence_proven)
        else:
            with pytest.raises(
                ValueError, match=r"identity continuity|unexplained removal"
            ):
                u.Infra.rule_deltas(
                    before,
                    observed,
                    options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
                )

    def test_native_lint_failure_keeps_independent_scan_evidence(
        self,
        mod_workspace: Path,
    ) -> None:
        """A failed Ruff configuration remains red without erasing AST or text scans."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.ok(u.Cli.atomic_write_text_file(root / "sample.py", "marker = dict()\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "ruff.toml", "line-length = 'invalid'\n"
            )
        )
        tm.that(self._sweep(root, "--audit-rules"), ne=0)
        report = self._receipt(root)
        snapshot = next(
            stage.audit_before
            for stage in report.stages
            if stage.audit_before is not None
        )
        ast_report = tm.not_none(snapshot.ast_report)
        tm.ok(snapshot.text_report is not None)
        tm.that(snapshot.observation_errors, empty=False)
        tm.that("\n".join(snapshot.observation_errors), has="invalid")
        lint = tm.not_none(snapshot.lint)
        receipt = next(
            tools[c.Infra.RUFF]
            for tools in lint.values()
            if tools[c.Infra.RUFF].execution_error is not None
        )
        tm.that(receipt.errors, empty=True)
        output = tm.not_none(receipt.output)
        tm.fail(u.Cli.process_succeeded(output.outcome))
        tm.that(
            any(entry.rule_id == "sweep-growth" for entry in ast_report.entries),
            eq=True,
        )

    @pytest.mark.parametrize("copies", [1, 2])
    @pytest.mark.parametrize("prefix", ["", "\n", "# \u03b1\n"])
    def test_published_module_absence_preserves_locus_not_changed_declarations(
        self, mod_workspace: Path, copies: int, prefix: str
    ) -> None:
        """Real publication preserves root absence, never equal-total call swaps."""
        self._prepare(mod_workspace, makefile=self._makefile(), local_rule=False)
        tm.ok(u.Tests.create_python_environment(mod_workspace))
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                "repair-marker": (
                    "id: repair-marker\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: marker = dict(source)\nfix: marker = "
                    "list(source)\n"
                ),
                "absent-class": (
                    "id: absent-class\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: module\n  not:\n    has:\n"
                    "      kind: class_definition\n"
                ),
                "violating-call": (
                    "id: violating-call\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: call\n  regex: '^(dict|list)\\(source\\)$'\n"
                ),
                "violating-declaration": (
                    "id: violating-declaration\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: expression_statement\n"
                    "  regex: '^marker = (dict|list)\\(source\\)$'\n"
                ),
                "module-with-declaration": (
                    "id: module-with-declaration\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: module\n  has:\n"
                    "    kind: expression_statement\n"
                    "    regex: '^marker = (dict|list)\\(source\\)$'\n"
                ),
            },
        )
        sample = mod_workspace / "accounting.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                sample, prefix + "source = ()\n" + "marker = dict(source)\n" * copies
            )
        )
        before = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        chain: list[m.Infra.CodegenStagedFile] = []
        tm.ok(
            FlextInfraModGateEngine.apply_report(
                mod_workspace,
                tm.ok(
                    FlextInfraModGateEngine.scan(
                        mod_workspace, fix=False, selection=("repair-marker",)
                    )
                ),
                exact_replacements=True,
                published_plans=chain,
            )
        )
        after = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.that(len(chain), eq=1)
        rows = {
            row.rule_id: row
            for row in u.Infra.rule_deltas(
                before,
                after,
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )
        }
        absence = rows["absent-class"]
        tm.that(
            (absence.before, absence.after, absence.introduced),
            eq=(
                sum(entry.rule_id == absence.rule_id for entry in before.entries),
                sum(entry.rule_id == absence.rule_id for entry in after.entries),
                0,
            ),
        )
        tm.ok(absence.semantic_correspondence_proven)
        calls = rows["violating-call"]
        tm.that(
            (calls.before, calls.after, calls.introduced), eq=(copies, copies, copies)
        )
        tm.fail(calls.semantic_correspondence_proven)
        tm.that(rows["violating-declaration"].introduced, eq=copies)
        tm.that(rows["module-with-declaration"].introduced, eq=1)
        tm.that(
            rows["module-with-declaration"].semantic_correspondence_proven, eq=False
        )
        with pytest.raises(ValueError, match="identity continuity broken"):
            u.Infra.rule_deltas(
                before,
                after,
                options=m.Infra.RuleDeltaOptions(publication_chain=(*chain, *chain)),
            )
        duplicated = FlextInfraModGateEngine.recounted(
            (
                *after.entries,
                next(
                    entry for entry in after.entries if entry.rule_id == "absent-class"
                ),
            ),
            source_states=after.source_states,
        )
        duplicate_rows = {
            row.rule_id: row
            for row in u.Infra.rule_deltas(
                before,
                duplicated,
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )
        }
        tm.that(duplicate_rows["absent-class"].introduced, eq=1)
        with pytest.raises(ValueError, match="lacks complete source inventory"):
            u.Infra.rule_deltas(
                before,
                after.model_copy(update={"source_states": None}),
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )
        lexical = {row.rule_id: row for row in u.Infra.rule_deltas(before, after)}
        tm.that(lexical["absent-class"].introduced, eq=1)
        with pytest.raises(ValueError, match="source identity drift"):
            u.Infra.rule_deltas(
                before, after, options=m.Infra.RuleDeltaOptions(publication_chain=())
            )
        drifted = after.model_copy(
            update={
                "entries": tuple(
                    entry.model_copy(
                        update={
                            "source_state": entry.source_state.model_copy(
                                update={"content": b"marker = tuple()\n"}
                            )
                        }
                    )
                    if entry.file == sample.relative_to(mod_workspace)
                    and entry.module_absence
                    and entry.source_state is not None
                    else entry
                    for entry in after.entries
                )
            }
        )
        with pytest.raises(ValueError, match="differs from complete scan inventory"):
            u.Infra.rule_deltas(
                before,
                drifted,
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )
        changed_catalog = after.model_copy(
            update={
                "entries": tuple(
                    entry.model_copy(update={"catalog_digest": "changed-catalog"})
                    if entry.rule_id == "absent-class"
                    else entry
                    for entry in after.entries
                )
            }
        )
        with pytest.raises(ValueError, match="catalog correspondence changed"):
            u.Infra.rule_deltas(
                before,
                changed_catalog,
                options=m.Infra.RuleDeltaOptions(publication_chain=tuple(chain)),
            )

    @pytest.mark.parametrize("counts", [(2, 0), (2, 1), (1, 2), (0, 0)])
    def test_public_utility_deltas_preserve_native_scan_indexes_and_multiplicity(
        self,
        mod_workspace: Path,
        counts: tuple[int, int],
    ) -> None:
        """The single utility owner retains complete per-rule evidence fields."""
        self._prepare(mod_workspace, makefile=self._makefile(), local_rule=True)
        sample = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n" * counts[0]))
        before = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n" * counts[1]))
        after = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        evidence = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes()
        )
        for classification, field in c.Infra.MOD_SCAN_CLASS_COUNT_FIELDS.items():
            tm.that(
                getattr(evidence, field),
                eq=sum(
                    entry.classification == classification for entry in after.entries
                ),
            )
        with pytest.raises(ValueError, match="deferred differs"):
            m.Infra.ModScanEvidence.model_validate({
                **evidence.model_dump(
                    mode="python", exclude=set(type(evidence).model_computed_fields)
                ),
                "totals_by_class": {
                    **evidence.totals_by_class,
                    c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT: evidence.deferred
                    + 1,
                },
            })
        plan = tm.ok(u.Infra.codemod_rule_plan(mod_workspace))
        inventory = tuple(
            (project.name, rule.id)
            for project in u.Infra.governed_project_roots(mod_workspace)
            for rule in plan.rules
        )
        deltas = u.Infra.rule_deltas(
            before, after, options=m.Infra.RuleDeltaOptions(inventory=inventory)
        )
        tm.that(
            [(row.repository, row.rule_id) for row in deltas], eq=sorted(set(inventory))
        )
        delta = next(row for row in deltas if row.rule_id == "sweep-growth")
        persisted = min(counts)
        tm.that((delta.before, delta.after), eq=counts)
        tm.that(
            (delta.resolved, delta.introduced),
            eq=tuple(count - persisted for count in counts),
        )
        tm.that(delta.persisted, eq=persisted)
        for row in deltas:
            for report, indexes in (
                (before, row.before_entries),
                (after, row.after_entries),
            ):
                tm.that(
                    indexes,
                    eq=tuple(
                        index
                        for index, entry in enumerate(report.entries)
                        if (entry.repository, entry.rule_id)
                        == (row.repository, row.rule_id)
                    ),
                )
        tm.fail(delta.semantic_correspondence_proven)
