"""The parsed rule catalog is cached by content and never served stale.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, p, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRuleCatalogCache:
    """Drive the public rule plan against a real local provider."""

    @staticmethod
    def _apply_catalog(project: Path, generated: Path | None = None) -> None:
        """Apply the public composed native stage to the project's source files."""
        plan = tm.ok(
            u.Infra.codemod_compose_rule_plan(
                project,
                {
                    project.resolve(): (
                        (c.Infra.CODEMOD_GENERATED_PROVIDER, generated)
                        if generated is not None
                        else None
                    )
                },
                rule_ids=("cache-only",),
            )
        )
        staged = u.Infra.codemod_stage_scan_ruleset(
            plan, project.parent / "native-stage"
        )
        tm.ok(
            u.Cli.capture([
                c.Infra.SG,
                "scan",
                "-c",
                str(staged.config),
                "--update-all",
                str(project / "src"),
            ])
        )

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
        rule.write_text(
            "id: cache-only\nlanguage: Python\nseverity: error\n"
            f"message: '{message}'\nrule:\n  pattern: only($VALUE)\n",
            encoding="utf-8",
        )
        return project, rule

    def test_unchanged_catalog_preserves_the_public_plan(
        self,
        tmp_path: Path,
    ) -> None:
        """Repeated planning preserves every rule's authenticated identity."""
        project, _ = self._project(tmp_path, "first")

        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            first = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            again = tm.ok(u.Infra.codemod_rule_plan(snapshot))

        tm.that(
            tuple(rule.model_dump(mode="json") for rule in again.rules),
            eq=tuple(rule.model_dump(mode="json") for rule in first.rules),
        )

    def test_an_edited_rule_is_a_new_key_never_the_stale_rule(
        self,
        tmp_path: Path,
    ) -> None:
        """Changing a rule's text re-parses it under a new content key."""
        project, rule = self._project(tmp_path, "before")
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            first = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        rule.write_text(
            rule.read_text(encoding="utf-8").replace("before", "after"),
            encoding="utf-8",
        )
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            second = tm.ok(u.Infra.codemod_rule_plan(snapshot))

        local = {rule.id: rule.digest for rule in first.rules}
        edited = {rule.id: rule.digest for rule in second.rules}
        tm.that(edited["cache-only"], ne=local["cache-only"])

    def test_utility_only_generated_provider_drives_catalog_scope(
        self, tmp_path: Path
    ) -> None:
        """A catalog rewrite consumes generated utilities and the declared scope."""
        project, rule = self._project(tmp_path, "generated facts")
        selected = project / "src" / "selected.py"
        excluded = project / "src" / "excluded.py"
        for source in (selected, excluded):
            source.write_text("only(7)\n", encoding=c.DEFAULT_ENCODING)
        generated_root = (
            project
            / c.Infra.MOD_NATIVE_STAGE_RELATIVE_PATH
            / c.Infra.CODEMOD_GENERATED_PROVIDER
            / "utility-only"
        )
        (generated_root / "rules").mkdir(parents=True)
        (generated_root / "utils").mkdir()
        generated = generated_root / c.Infra.CODEMOD_CONFIG_FILENAME
        u.Infra.codemod_write_native_documents(
            generated,
            ({"ruleDirs": ["rules"], "utilDirs": ["utils"]},),
        )
        u.Infra.codemod_write_native_documents(
            generated_root / c.Infra.CODEMOD_SCOPES_FILENAME,
            ({"selected-source": [selected.relative_to(project).as_posix()]},),
        )
        u.Infra.codemod_write_native_documents(
            generated_root / "utils" / "selected-call.yml",
            (
                {
                    "id": "selected-call",
                    "language": "Python",
                    "rule": {"pattern": "only($VALUE)"},
                },
            ),
        )
        u.Infra.codemod_write_native_documents(
            rule,
            (
                {
                    "id": "cache-only",
                    "language": "Python",
                    "severity": "error",
                    "message": "Rewrite the selected source",
                    "metadata": {"scope": {"in": ["selected-source"]}},
                    "rule": {"matches": "selected-call"},
                    "fix": "owned($VALUE)",
                },
            ),
        )

        self._apply_catalog(project, generated)

        tm.that(selected.read_text(encoding=c.DEFAULT_ENCODING), eq="owned(7)\n")
        tm.that(excluded.read_text(encoding=c.DEFAULT_ENCODING), eq="only(7)\n")

    def test_parameterized_utility_keeps_argument_captures_and_formal_shadow(
        self, tmp_path: Path
    ) -> None:
        """Native arguments export their capture instead of a homonymous utility."""
        project, rule = self._project(tmp_path, "parameterized utility")
        consumer = project / "src" / "consumer.py"
        consumer.write_text("only(7)\nwrong(8)\n", encoding=c.DEFAULT_ENCODING)
        catalog = rule.parent.parent
        utilities = catalog / "utils"
        utilities.mkdir()
        u.Infra.codemod_write_native_documents(
            catalog / c.Infra.CODEMOD_CONFIG_FILENAME,
            ({"ruleDirs": ["rules"], "utilDirs": ["utils"]},),
        )
        documents: tuple[t.JsonMapping, ...] = (
            {
                "id": "BODY",
                "language": "Python",
                "rule": {"pattern": "wrong($VALUE)"},
            },
            {
                "id": "supplied-call",
                "language": "Python",
                "rule": {"pattern": "only($VALUE)"},
            },
            {
                "id": "captured-call",
                "language": "Python",
                "arguments": ["BODY"],
                "rule": {"matches": "BODY"},
            },
        )
        for document in documents:
            u.Infra.codemod_write_native_documents(
                utilities / f"{document['id']}.yml", (document,)
            )
        u.Infra.codemod_write_native_documents(
            rule,
            (
                {
                    "id": "cache-only",
                    "language": "Python",
                    "severity": "error",
                    "message": "Preserve the supplied native capture",
                    "rule": {
                        "matches": {
                            "captured-call": {"BODY": {"matches": "supplied-call"}}
                        }
                    },
                    "fix": "owned($VALUE)",
                },
            ),
        )

        self._apply_catalog(project)

        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            eq="owned(7)\nwrong(8)\n",
        )

    def test_a_fresh_consumer_builds_the_same_typed_rules(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """A fresh process derives the same public plan from authored sources."""
        project, rule_path = self._project(tmp_path, "native")
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            plan = tm.ok(u.Infra.codemod_rule_plan(snapshot))
        expected = next(rule for rule in plan.rules if rule.resource == rule_path)
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
with u.Infra.codemod_workspace_snapshot(Path(sys.argv[1])) as snapshot:
    plan = u.Infra.codemod_rule_plan(snapshot).unwrap()
observed = next(
    rule for rule in plan.rules
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
