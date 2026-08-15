"""Consolidation phase tests for deps modernizer."""

from __future__ import annotations

from flext_infra.deps.phases.consolidate_groups import FlextInfraConsolidateGroupsPhase
from flext_tests import tm
from tests import u


class TestsFlextInfraDepsModernizerConsolidate:
    """Tests consolidate groups phase behavior."""

    def test_consolidate_groups_creates_dev_group(self) -> None:
        """Verify consolidate groups creates dev group."""
        doc = u.Cli.toml_document()
        project = u.Cli.toml_table()
        optional = u.Cli.toml_table()
        project["optional-dependencies"] = optional
        doc["project"] = project
        changes = FlextInfraConsolidateGroupsPhase().apply(doc, [])
        tm.that(changes, empty=False)

    def test_consolidate_groups_removes_old_groups(self) -> None:
        """Verify consolidate groups removes old groups."""
        doc = u.Tests.toml_doc(
            "[project.optional-dependencies]\n"
            'dev = ["pytest"]\n'
            'docs = ["sphinx"]\n'
            'test = ["coverage"]\n'
        )
        changes = FlextInfraConsolidateGroupsPhase().apply(doc, ["pytest"])
        tm.that(any("removed" in change for change in changes), eq=True)

    def test_consolidate_groups_merges_poetry_groups(self) -> None:
        """Verify consolidate groups merges poetry groups."""
        doc = u.Cli.toml_document()
        project = u.Cli.toml_table()
        optional = u.Cli.toml_table()
        project["optional-dependencies"] = optional
        doc["project"] = project
        group = u.Cli.toml_table()
        group["dev"] = {"dependencies": {"pytest": "^7.0"}}
        group["docs"] = {"dependencies": {"sphinx": "^4.0"}}
        poetry = u.Cli.toml_table()
        poetry["group"] = group
        tool = u.Cli.toml_table()
        tool["poetry"] = poetry
        doc["tool"] = tool
        changes = FlextInfraConsolidateGroupsPhase().apply(doc, [])
        tm.that(changes, empty=False)

    def test_consolidate_groups_sets_deptry_config(self) -> None:
        """Verify consolidate groups sets deptry config."""
        doc = u.Cli.toml_document()
        project = u.Cli.toml_table()
        project["optional-dependencies"] = u.Cli.toml_table()
        doc["project"] = project
        doc["tool"] = u.Cli.toml_table()
        changes = FlextInfraConsolidateGroupsPhase().apply(doc, [])
        tm.that(any("deptry" in change for change in changes), eq=True)

    def test_consolidate_groups_handles_missing_tables(self) -> None:
        """Verify consolidate groups handles missing tables."""
        changes = FlextInfraConsolidateGroupsPhase().apply(u.Cli.toml_document(), [])
        tm.that(changes, empty=False)

    def test_consolidate_groups_phase_apply_removes_old_groups(self) -> None:
        """Verify consolidate groups phase apply removes old groups."""
        doc = u.Cli.toml_document()
        project = u.Cli.toml_table()
        optional = u.Cli.toml_table()
        optional["dev"] = ["pytest"]
        optional["docs"] = ["sphinx"]
        optional["test"] = ["coverage"]
        project["optional-dependencies"] = optional
        doc["project"] = project
        changes = FlextInfraConsolidateGroupsPhase().apply(doc, [])
        tm.that(
            any("optional-dependencies.docs removed" in c for c in changes), eq=True
        )
        tm.that(
            any("optional-dependencies.test removed" in c for c in changes), eq=True
        )

    def test_consolidate_groups_phase_apply_with_empty_poetry_group(self) -> None:
        """Verify consolidate groups phase apply with empty poetry group."""
        doc = u.Cli.toml_document()
        project = u.Cli.toml_table()
        project["optional-dependencies"] = u.Cli.toml_table()
        doc["project"] = project
        docs_group = u.Cli.toml_table()
        docs_group["dependencies"] = u.Cli.toml_table()
        group = u.Cli.toml_table()
        group["docs"] = docs_group
        poetry = u.Cli.toml_table()
        poetry["group"] = group
        tool = u.Cli.toml_table()
        tool["poetry"] = poetry
        doc["tool"] = tool
        changes = FlextInfraConsolidateGroupsPhase().apply(doc, [])
        tm.that(changes, empty=False)
