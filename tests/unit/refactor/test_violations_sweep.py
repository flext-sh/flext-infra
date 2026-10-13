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

from flext_infra import config, main
from flext_infra.codemod import FlextInfraModGateEngine, FlextInfraModTextGateEngine
from flext_infra.refactor import FlextInfraRefactorViolationsSweep
from tests import c, m, tm, u

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
                ),
                "resolve-future": (
                    "id: resolve-future\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: marker = tuple()\nfix: |\n"
                    "  from __future__ import annotations\n  marker = list()\n"
                ),
            },
        )
        tm.ok(u.Tests.create_python_environment(root))
        parent = root / "src"
        parent.mkdir(exist_ok=True)
        sample, victim = parent / "accounting.py", root / "victim.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n"))
        tm.ok(u.Cli.atomic_write_text_file(victim, "value = 1\n"))
        before = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        quiet_before = (
            tm.ok(
                FlextInfraModGateEngine.scan(
                    root, fix=False, rule_ids=("repair-marker",)
                )
            )
            if drift == "removed"
            else None
        )
        if quiet_before is not None:
            tm.that(
                any(
                    entry.file == victim.relative_to(root)
                    for entry in quiet_before.entries
                ),
                eq=False,
            )
            assert quiet_before.source_states is not None
            tm.that(
                any(state.path == victim for state in quiet_before.source_states),
                eq=True,
            )
        chain: list[m.Infra.CodegenStagedFile] = []
        for index, rule_id in enumerate(("repair-marker", "resolve-future")):
            tm.ok(
                FlextInfraModGateEngine.scan(
                    root, fix=True, rule_ids=(rule_id,), published_plans=chain
                )
            )
            observed = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
            if index == 0:
                u.Infra.rule_deltas(before, observed, publication_chain=tuple(chain))
                assert observed.source_states is not None
                admitted = next(item for item in chain if item.before.path == sample)
                tm.that(
                    admitted.replacement,
                    eq=next(
                        item for item in observed.source_states if item.path == sample
                    ),
                )
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
                if drift != "none":
                    changed = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
                    with pytest.raises(
                        ValueError, match="identity drift|unexplained removal"
                    ):
                        u.Infra.rule_deltas(
                            before, changed, publication_chain=tuple(chain)
                        )
                    if quiet_before is not None:
                        quiet_after = tm.ok(
                            FlextInfraModGateEngine.scan(
                                root, fix=False, rule_ids=("repair-marker",)
                            )
                        )
                        with pytest.raises(ValueError, match="unexplained removal"):
                            u.Infra.rule_deltas(
                                quiet_before,
                                quiet_after,
                                publication_chain=tuple(chain),
                            )
        if drift == "none":
            rows = u.Infra.rule_deltas(before, observed, publication_chain=tuple(chain))
            future = next(
                row for row in rows if row.rule_id == "require-future-annotations"
            )
            tm.that(future.resolved, eq=1)
            tm.that(future.semantic_correspondence_proven, eq=True)
        else:
            with pytest.raises(
                ValueError, match="identity continuity|unexplained removal"
            ):
                u.Infra.rule_deltas(before, observed, publication_chain=tuple(chain))

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
        tm.that(snapshot.ast_report is not None, eq=True)
        tm.that(snapshot.text_report is not None, eq=True)
        tm.that(snapshot.observation_errors, empty=False)
        tm.that("\n".join(snapshot.observation_errors), has="invalid")
        assert snapshot.lint is not None
        receipt = next(
            tools[c.Infra.RUFF]
            for tools in snapshot.lint.values()
            if tools[c.Infra.RUFF].execution_error is not None
        )
        tm.that(receipt.errors, eq=())
        assert receipt.output is not None
        tm.that(u.Cli.process_succeeded(receipt.output.outcome), eq=False)
        assert snapshot.ast_report is not None
        tm.that(
            any(
                entry.rule_id == "sweep-growth" for entry in snapshot.ast_report.entries
            ),
            eq=True,
        )

    @pytest.mark.parametrize("copies", [1, 2])
    def test_published_module_absence_preserves_locus_not_changed_declarations(
        self, mod_workspace: Path, copies: int
    ) -> None:
        """Real publication preserves root absence, never equal-total call swaps."""
        self._prepare(mod_workspace, makefile=self._makefile(), local_rule=False)
        tm.ok(u.Tests.create_python_environment(mod_workspace))
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                "repair-marker": (
                    "id: repair-marker\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: marker = dict()\nfix: marker = list()\n"
                ),
                "absent-class": (
                    "id: absent-class\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: module\n  not:\n    has:\n"
                    "      kind: class_definition\n"
                ),
                "violating-call": (
                    "id: violating-call\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: call\n  regex: '^(dict|list)\\(\\)$'\n"
                ),
                "violating-declaration": (
                    "id: violating-declaration\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: expression_statement\n"
                    "  regex: '^marker = (dict|list)\\(\\)$'\n"
                ),
                "module-with-declaration": (
                    "id: module-with-declaration\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  kind: module\n  has:\n"
                    "    kind: expression_statement\n"
                    "    regex: '^marker = (dict|list)\\(\\)$'\n"
                ),
            },
        )
        sample = mod_workspace / "accounting.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n" * copies))
        before = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        chain: list[m.Infra.CodegenStagedFile] = []
        tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=True,
                rule_ids=("repair-marker",),
                published_plans=chain,
            )
        )
        after = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.that(len(chain), eq=1)
        rows = {
            row.rule_id: row
            for row in u.Infra.rule_deltas(
                before, after, publication_chain=tuple(chain)
            )
        }
        absence = rows["absent-class"]
        tm.that((absence.before, absence.after, absence.introduced), eq=(1, 1, 0))
        tm.that(absence.semantic_correspondence_proven, eq=True)
        calls = rows["violating-call"]
        tm.that(
            (calls.before, calls.after, calls.introduced), eq=(copies, copies, copies)
        )
        tm.that(calls.semantic_correspondence_proven, eq=False)
        tm.that(rows["violating-declaration"].introduced, eq=copies)
        tm.that(rows["module-with-declaration"].introduced, eq=1)
        tm.that(
            rows["module-with-declaration"].semantic_correspondence_proven, eq=False
        )
        with pytest.raises(ValueError, match="identity continuity broken"):
            u.Infra.rule_deltas(before, after, publication_chain=(*chain, *chain))
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
                before, duplicated, publication_chain=tuple(chain)
            )
        }
        tm.that(duplicate_rows["absent-class"].introduced, eq=1)
        with pytest.raises(ValueError, match="lacks complete source inventory"):
            u.Infra.rule_deltas(
                before,
                after.model_copy(update={"source_states": None}),
                publication_chain=tuple(chain),
            )
        lexical = {row.rule_id: row for row in u.Infra.rule_deltas(before, after)}
        tm.that(lexical["absent-class"].introduced, eq=1)
        with pytest.raises(ValueError, match="source identity drift"):
            u.Infra.rule_deltas(before, after, publication_chain=())
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
            u.Infra.rule_deltas(before, drifted, publication_chain=tuple(chain))
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
            u.Infra.rule_deltas(before, changed_catalog, publication_chain=tuple(chain))

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

    @classmethod
    def _declare_members(cls, root: Path, names: tuple[str, ...]) -> tuple[Path, ...]:
        """Declare real member identities through the existing Git manifest owner.

        Returns:
            Fixture members with native project metadata and executable audits.
        """
        distribution, _dependencies = tm.ok(u.Infra.codemod_project_requirements(root))
        document = (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        members = tuple(root / name for name in names)
        for member in members:
            package = member / c.Infra.DEFAULT_SRC_DIR / member.name.replace("-", "_")
            tm.ok(u.Cli.ensure_dir(package))
            tm.ok(u.Cli.atomic_write_text_file(package / "__init__.py", ""))
            tm.ok(
                u.Cli.atomic_write_text_file(
                    member / c.PYPROJECT_FILENAME,
                    document.replace(
                        f'name = "{distribution}"', f'name = "{member.name}"'
                    ),
                )
            )
            cls._prepare(
                member, makefile=".PHONY: audit\naudit:\n\t@true\n", local_rule=True
            )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.Infra.GITMODULES,
                "".join(
                    f'[submodule "{member.name}"]\n\tpath = {member.name}\n'
                    f"\turl = https://example.com/{member.name}.git\n"
                    for member in members
                ),
            )
        )
        return members

    def test_same_total_rule_swap_cannot_offset_native_rule_growth(
        self,
        mod_workspace: Path,
    ) -> None:
        """Each actual native ID keeps its counter even when total count is equal."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        rule_dir = root / c.Infra.CODEMOD_CONFIG_RELPATH.parent / c.Cli.RULES_DIR_NAME
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule_dir / "second.yml",
                LOCAL_GROWTH_RULE.replace("sweep-growth", "sweep-second").replace(
                    "dict()", "list()"
                ),
            )
        )
        sample = root / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n"))
        before = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = list()\n"))
        after = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        rows = {row.rule_id: row for row in u.Infra.rule_deltas(before, after)}
        tm.that(before.findings, eq=after.findings)
        tm.that(rows["sweep-growth"].resolved, eq=1)
        tm.that(rows["sweep-second"].introduced, eq=1)

    def test_project_reduction_cannot_offset_another_project_growth(
        self,
        mod_workspace: Path,
    ) -> None:
        """Two projects with the same native rule retain independent multiplicities."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        first, second = self._declare_members(root, ("member-first", "member-second"))
        first_source = first / "sample.py"
        second_source = second / "sample.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                first_source, "marker = dict()\nmarker = dict()\n"
            )
        )
        tm.ok(u.Cli.atomic_write_text_file(second_source, "marker = tuple()\n"))
        before = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        tm.ok(u.Cli.atomic_write_text_file(first_source, "marker = tuple()\n"))
        tm.ok(u.Cli.atomic_write_text_file(second_source, "marker = dict()\n"))
        after = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        rows = {
            (row.repository, row.rule_id): row
            for row in u.Infra.rule_deltas(before, after)
        }
        tm.that(rows[first.name, "sweep-growth"].resolved, eq=2)
        tm.that(rows[second.name, "sweep-growth"].introduced, eq=1)

    def test_effective_zero_rows_and_not_applicable_retain_catalog_identity(
        self,
        mod_workspace: Path,
    ) -> None:
        """A native owner exclusion is not a successful zero-count scan."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        (member,) = self._declare_members(root, ("member-owner",))
        rule_text = LOCAL_GROWTH_RULE + f"metadata:\n  owner: {member.name}\n"
        for project in (root, member):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    project
                    / c.Infra.CODEMOD_CONFIG_RELPATH.parent
                    / c.Cli.RULES_DIR_NAME
                    / "sweep.yml",
                    rule_text,
                )
            )
        tm.that(self._sweep(root, "--audit-rules"), ne=0)
        report = self._receipt(root)
        rows = {(row.repository, row.rule_id): row for row in report.rule_evaluations}
        scanned = rows[root.name, "sweep-growth"]
        excluded = rows[member.name, "sweep-growth"]
        tm.that(scanned.status, eq="observed")
        assert scanned.delta is not None
        tm.that((scanned.delta.before, scanned.delta.after), eq=(0, 0))
        tm.that(excluded.status, eq="not_applicable")
        tm.that(excluded.delta, eq=None)
        tm.that(excluded.catalog_digest, eq=scanned.catalog_digest)
        tm.that(excluded.provider, eq=scanned.provider)
        tm.that(bool(excluded.error), eq=True)
        tm.that(
            {row.repository for row in report.engine_coverage},
            eq={root.name, member.name},
        )

    def test_native_text_and_ast_homonyms_never_share_a_counter(
        self,
        mod_workspace: Path,
    ) -> None:
        """The native text finding ID is independent of an identically named AST ID."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        text_catalog = root / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        tm.ok(u.Cli.ensure_dir(text_catalog.parent))
        tm.ok(
            u.Cli.atomic_write_text_file(
                text_catalog,
                "rules:\n  - id: sweep-growth\n    include: [sample.py]\n"
                "    find: 'dict'\n    replace: 'tuple'\n",
            )
        )
        sample = root / "sample.py"
        tm.ok(
            u.Cli.atomic_write_text_file(sample, "marker = dict()\nmarker = dict()\n")
        )
        before_ast = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        before_text = tm.ok(FlextInfraModTextGateEngine.scan(root, fix=False))
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n"))
        after_ast = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        after_text = tm.ok(FlextInfraModTextGateEngine.scan(root, fix=False))
        ast_rows = u.Infra.rule_deltas(before_ast, after_ast)
        text_rows = u.Infra.rule_deltas(
            before_text,
            after_text,
            repository_root=root,
            projects=(root.resolve(),),
        )
        rows = {(row.engine, row.rule_id): row for row in (*ast_rows, *text_rows)}
        for engine in ("ast-grep", "text"):
            row = rows[engine, "sweep-growth"]
            tm.that(
                (row.before, row.after, row.persisted, row.resolved), eq=(2, 1, 1, 1)
            )
            tm.that(row.introduced, eq=0)

    def test_failed_text_inventory_preserves_independent_ast_evidence(
        self,
        mod_workspace: Path,
    ) -> None:
        """One failed native engine never erases another engine's measured rows."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.ok(u.Cli.atomic_write_text_file(root / "sample.py", "marker = dict()\n"))
        text_catalog = root / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        tm.ok(u.Cli.ensure_dir(text_catalog.parent))
        tm.ok(u.Cli.atomic_write_text_file(text_catalog, "rules: [invalid\n"))
        tm.that(self._sweep(root, "--audit-rules"), ne=0)
        report = self._receipt(root)
        assert report.before_evidence is not None
        row = next(
            row
            for row in report.rule_evaluations
            if row.engine == "ast-grep" and row.rule_id == "sweep-growth"
        )
        assert row.delta is not None
        tm.that((row.delta.before, row.delta.after, row.delta.persisted), eq=(1, 1, 1))
        text = next(row for row in report.engine_coverage if row.engine == "text")
        tm.that(text.status, eq="NOT_EXECUTED")
        tm.that(bool(report.repair_error), eq=True)
        tm.that((root / "ran.txt").exists(), eq=False)

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

    def test_clean_tree_retains_zero_deltas_without_false_complete_audit(
        self,
        mod_workspace: Path,
    ) -> None:
        """The sequence runs, but missing native rule audits cannot become green."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=False)

        tm.that(self._sweep(root), ne=0)

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
        tm.that(report.repair_error, eq=None)
        tm.that(
            {row.engine: row.status for row in report.engine_coverage},
            eq={
                "ast-grep": "incomplete",
                "text": "incomplete",
                "ruff": "incomplete",
                "census": "NOT_EXECUTED",
            },
        )
        tm.that(
            all(
                row.cause for row in report.engine_coverage if row.status != "observed"
            ),
            eq=True,
        )
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
        tm.that(self._sweep(root), ne=0)
        first = self._receipt(root)
        assert first.before_evidence is not None
        assert first.after_evidence is not None
        before_bytes = first.before_evidence.path.read_bytes()
        after_bytes = first.after_evidence.path.read_bytes()

        tm.that(self._sweep(root), ne=0)

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
        assert report.before is not None
        assert report.after is not None
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
        tm.that(self._sweep(root), ne=0)
        report = self._receipt(root)
        assert report.before_evidence is not None
        assert report.before_plan is not None
        assert report.before_source_sha256 is not None
        tm.that(report.before_evidence.evidence.totals_by_rule["sweep-growth"], eq=0)
        tm.that(
            report.before_evidence.evidence.totals_by_repository[root.name],
            eq=sum(
                entry.repository == root.name
                for entry in report.before_evidence.evidence.entries
            ),
        )
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
        tm.that(self._sweep(root), ne=0)
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
        tm.that(self._sweep(root, "--audit-rules", "--rules", "sweep-growth"), ne=0)
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

    def test_existing_ast_cli_applies_only_the_exact_selected_rule(
        self,
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Reuse the native selected engine, never a sweep-specific rewrite engine."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root
                / c.Infra.CODEMOD_CONFIG_RELPATH.parent
                / c.Cli.RULES_DIR_NAME
                / "sweep.yml",
                LOCAL_GROWTH_RULE.replace("fix: marker = tuple()", "fix: marker = ()"),
            )
        )
        tm.ok(u.Cli.atomic_write_text_file(root / "sample.py", "marker = dict()\n"))
        exit_code = main([
            c.Infra.CLI_GROUP_REFACTOR,
            "ast",
            "--apply",
            "--repository-root",
            str(root),
            "--rules",
            "sweep-growth",
        ])
        captured = capsys.readouterr()
        tm.that(exit_code, eq=0, msg=captured.out + captured.err)
        tm.that((root / "ran.txt").exists(), eq=False)
        tm.that(self._sweep(root, "--audit-rules"), eq=0)
        row = next(
            row
            for row in self._receipt(root).stages[0].rule_evaluations
            if row.rule_id == "sweep-growth"
        )
        assert row.delta is not None
        tm.that(row.delta.before, eq=0)
        tm.that(row.delta.after, eq=0)

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
        tm.that(self._sweep(root, "--repair-verbs", ",".join(verbs)), ne=0)
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

    @pytest.mark.parametrize("mutation", ["change", "add", "remove"])
    def test_audit_authenticates_utility_bytes_and_inventory_without_source_changes(
        self,
        mod_workspace: Path,
        mutation: str,
    ) -> None:
        """Utility-only effects invalidate native evidence and the read-only audit."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        catalog = root / c.Infra.CODEMOD_CONFIG_RELPATH
        utilities = catalog.parent / "utils"
        tm.ok(u.Cli.ensure_dir(utilities))
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalog, LOCAL_RULE_CATALOG + "utilDirs:\n  - utils\n"
            )
        )
        rule_path = catalog.parent / c.Cli.RULES_DIR_NAME / "sweep.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule_path,
                LOCAL_GROWTH_RULE.replace(
                    "  pattern: marker = dict()", "  matches: sweep-match"
                ),
            )
        )
        utility = utilities / "match.yml"
        utility_text = (
            "id: sweep-match\nlanguage: Python\nrule:\n  pattern: marker = tuple()\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(utility, utility_text))
        tm.ok(u.Cli.atomic_write_text_file(root / "sample.py", "marker = dict()\n"))
        changed = utility if mutation == "change" else utilities / "extra.yml"
        extra_text = utility_text.replace("sweep-match", "sweep-extra")
        if mutation == "remove":
            tm.ok(u.Cli.atomic_write_text_file(changed, extra_text))
            recipe = f"\t@rm '{changed}'\n"
        else:
            replacement = (
                utility_text.replace("tuple()", "dict()")
                if mutation == "change"
                else extra_text
            ).replace("\n", "\\n")
            recipe = f"\t@printf '{replacement}' > '{changed}'\n"
        self._prepare(
            root,
            makefile=".PHONY: audit\naudit:\n" + recipe,
            local_rule=False,
        )
        tm.fail(
            FlextInfraRefactorViolationsSweep(
                repository_root=root, repair_verbs="audit"
            ).execute(),
            has="audit changed",
        )
        stage = self._receipt(root).stages[0]
        tm.that(stage.source_inventory_unchanged, eq=False)
        assert stage.audit_before is not None
        assert stage.audit_after is not None
        before = stage.audit_before.sha256
        after = stage.audit_after.sha256
        for unchanged in (catalog, rule_path, root / "sample.py"):
            tm.that(
                before[str(unchanged.resolve())], eq=after[str(unchanged.resolve())]
            )
        tm.that(
            before[str(utility.resolve())], eq=u.Cli.sha256_bytes(utility_text.encode())
        )
        changed_key = str(changed.resolve())
        if mutation == "change":
            tm.that(before[changed_key], ne=after[changed_key])
            row = next(
                row for row in stage.rule_evaluations if row.rule_id == "sweep-growth"
            )
            assert row.delta is not None
            tm.that(
                (row.delta.before, row.delta.after, row.delta.introduced), eq=(0, 1, 1)
            )
        else:
            tm.that(changed_key in before, eq=mutation == "remove")
            tm.that(changed_key in after, eq=mutation == "add")

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
