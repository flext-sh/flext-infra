"""The parsed rule catalog is cached by content and never served stale.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config
from tests import m, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p


class TestsFlextInfraRuleCatalogCache:
    """Drive the public rule plan against a real local provider."""

    @staticmethod
    def _project(tmp_path: Path, message: str) -> tuple[Path, Path]:
        project = tmp_path / "catalog-cache"
        config_path = project / c.Infra.CODEMOD_CONFIG_RELPATH
        rules = config_path.parent / c.Cli.RULES_DIR_NAME
        rules.mkdir(parents=True, exist_ok=True)
        (project / "src").mkdir(exist_ok=True)
        (project / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "catalog-cache"\nversion = "1.0.0"\ndependencies = []\n',
            encoding="utf-8",
        )
        config_path.write_text(
            f"ruleDirs: [{c.Cli.RULES_DIR_NAME}]\n",
            encoding="utf-8",
        )
        rule = rules / "only.yml"
        # The cache is the host's persistent store, keyed by content: the
        # run's own tmp path makes the content new to it on every run, so a
        # rerun on the same host still observes its own publication.
        rule.write_text(
            "id: cache-only\nlanguage: Python\nseverity: error\n"
            f"message: '{message} {tmp_path}'\nrule:\n  pattern: only($VALUE)\n",
            encoding="utf-8",
        )
        return project, rule

    @staticmethod
    def _entries() -> frozenset[str]:
        directory = u.Infra.external_cache_directory(
            config.Infra.codegen.make.codemod_rules_cache,
        )
        if not directory.is_dir():
            return frozenset()
        return frozenset(entry.name for entry in directory.glob("*.json"))

    @staticmethod
    def _catalog_entries(project: Path, entries: frozenset[str]) -> frozenset[str]:
        """Select the actual cache records owned by this test's local catalog.

        Args:
            project: The path to the local project containing the catalog.
            entries: The set of cache entry filenames to filter.

        Returns:
            A frozenset of cache entry filenames that are actually owned by the local catalog.

        """
        directory = u.Infra.external_cache_directory(
            config.Infra.codegen.make.codemod_rules_cache,
        )
        adapter = u.type_adapter(tuple[m.Infra.CodemodRule, ...])
        return frozenset(
            name
            for name in entries
            if any(
                rule.resource.is_relative_to(project)
                for rule in adapter.validate_json((directory / name).read_bytes())
            )
        )

    def test_a_plan_publishes_one_entry_per_catalog_content(
        self,
        tmp_path: Path,
    ) -> None:
        """Planning writes the catalog once; the same content adds nothing."""
        project, _ = self._project(tmp_path, "first")
        before = self._entries()

        first = tm.ok(u.Infra.codemod_rule_plan(project))
        published = self._catalog_entries(project, self._entries() - before)
        again = tm.ok(u.Infra.codemod_rule_plan(project))

        tm.that(published, empty=False)
        tm.that(
            self._catalog_entries(project, self._entries() - before),
            eq=published,
        )
        tm.that(
            tuple(rule.digest for rule in again.rules),
            eq=tuple(rule.digest for rule in first.rules),
        )

    def test_an_edited_rule_is_a_new_key_never_the_stale_rule(
        self,
        tmp_path: Path,
    ) -> None:
        """Changing a rule's text re-parses it under a new content key."""
        project, rule = self._project(tmp_path, "before")
        first = tm.ok(u.Infra.codemod_rule_plan(project))
        after_first = self._entries()

        rule.write_text(
            rule.read_text(encoding="utf-8").replace("before", "after"),
            encoding="utf-8",
        )
        second = tm.ok(u.Infra.codemod_rule_plan(project))

        tm.that(
            self._catalog_entries(project, self._entries() - after_first),
            empty=False,
        )
        local = {rule.id: rule.digest for rule in first.rules}
        edited = {rule.id: rule.digest for rule in second.rules}
        tm.that(edited["cache-only"], ne=local["cache-only"])

    def test_a_fresh_consumer_recovers_typed_rules_from_disk(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Persistent JSON retains the exact public plan across native processes."""
        project, rule_path = self._project(tmp_path, "native")
        expected = next(
            rule
            for rule in tm.ok(u.Infra.codemod_rule_plan(project)).rules
            if rule.resource == rule_path
        )
        expected_path = tmp_path / "expected-plan.json"
        tm.ok(
            u.Cli.atomic_write_text_file(expected_path, expected.model_dump_json()),
        )
        native_consumer(
            """
from flext_infra import m, u

expected = m.Infra.CodemodRule.model_validate_json(
    Path(sys.argv[2]).read_text(encoding="utf-8")
)
observed = next(
    rule for rule in u.Infra.codemod_rule_plan(Path(sys.argv[1])).unwrap().rules
    if rule.resource == expected.resource
)
observed_payload = observed.model_dump(mode="json")
expected_payload = expected.model_dump(mode="json")
assert observed_payload == expected_payload, [
    name for name in expected_payload
    if observed_payload[name] != expected_payload[name]
]
""",
            str(project),
            str(expected_path),
        )
