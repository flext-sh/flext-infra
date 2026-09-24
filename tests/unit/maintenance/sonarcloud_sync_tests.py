"""Public behavior tests for the SonarCloud server-side settings sync.

The sync writes an external web API; these tests exercise everything that
decides what is written and when, without opening a network socket: the
project key derived from a real Git origin, the request plan derived from the
codegen SSOT, the no-op decision against the measured response shape, and the
token preflight that fails before any effect through the public CLI.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import FlextInfraSonarcloudSettingsSync, c, config, m
from tests import u

if TYPE_CHECKING:
    from tests import t

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSonarcloudSettingsSync:
    """Validate the settings sync through its public service contract."""

    _ORGANIZATION = "example-org"
    _REPOSITORY = "example-repo"

    @staticmethod
    def _plan(project_key: str) -> m.Infra.SonarcloudSettingsPlan:
        """Build the plan the SSOT declares for one project key."""
        return tm.ok(
            FlextInfraSonarcloudSettingsSync.settings_plan(
                config.Infra.codegen.sonarcloud, project_key
            )
        )

    @staticmethod
    def _server_payload(pairs: tuple[tuple[str, str], ...]) -> str:
        """Render an ``api/settings/values`` body in the measured shape."""
        settings: list[t.JsonValue] = []
        if pairs:
            field_values: list[t.JsonValue] = [
                {"resourceKey": resource, "ruleKey": rule} for rule, resource in pairs
            ]
            settings.append({
                "key": c.Infra.SONARCLOUD_ISSUE_IGNORE_KEY,
                "fieldValues": field_values,
                "inherited": False,
            })
        return tm.ok(u.Cli.json_dumps({"settings": settings}))

    @staticmethod
    def _ssot_pairs() -> tuple[tuple[str, str], ...]:
        """Return the SSOT exclusions as ``(rule_key, resource_key)`` pairs."""
        return tuple(
            (exclusion.rule_key, exclusion.resource_key)
            for exclusion in config.Infra.codegen.sonarcloud.issue_exclusions
        )

    def _cli(
        self, repository_root: Path, env: t.StrMapping | None = None
    ) -> tuple[int, str]:
        """Run the public CLI route in a child process without SONAR_TOKEN."""
        result = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-m",
                    "flext_infra",
                    c.Infra.CLI_GROUP_MAINTENANCE,
                    c.Infra.VERB_SONARCLOUD_SYNC,
                    "--repository-root",
                    str(repository_root),
                ],
                env={"COLUMNS": "200", **(env or {})},
                remove_env_keys=() if env else ("SONAR_TOKEN",),
            )
        )
        return result.outcome.raw_return_code, result.stdout + result.stderr

    @pytest.mark.parametrize(
        "origin",
        [
            "https://github.com/example-org/example-repo.git",
            "git@github.com:example-org/example-repo.git",
        ],
    )
    def test_project_key_joins_origin_organization_and_repository(
        self, tmp_path: Path, origin: str
    ) -> None:
        """The key is <organization>_<repository> whatever the origin transport."""
        u.Tests.initialize_git_repo(tmp_path, origin_url=origin)

        key = tm.ok(FlextInfraSonarcloudSettingsSync.project_key(tmp_path))

        tm.that(
            key,
            eq=f"{self._ORGANIZATION}{c.Infra.SONARCLOUD_PROJECT_KEY_SEPARATOR}"
            f"{self._REPOSITORY}",
        )

    def test_plan_sends_one_field_value_per_ssot_exclusion(self) -> None:
        """The set request carries the project, the key, and every SSOT entry."""
        plan = self._plan("org_repo")
        form = plan.form_fields()

        tm.that(form[0], eq=("component", "org_repo"))
        tm.that(form[1], eq=("key", c.Infra.SONARCLOUD_ISSUE_IGNORE_KEY))
        sent = tuple(
            (entry.rule_key, entry.resource_key)
            for name, value in form[2:]
            if name == "fieldValues"
            for entry in (m.Infra.SonarcloudIssueFieldValue.model_validate_json(value),)
        )
        tm.that(form[2][1], has='"ruleKey"')
        tm.that(form[2][1], has='"resourceKey"')
        tm.that(len(form), eq=2 + len(sent))
        tm.that(sent, eq=self._ssot_pairs())
        tm.that(plan.api_url, eq=config.Infra.codegen.sonarcloud.api_url)

    def test_plan_is_in_sync_only_when_server_holds_the_ssot(self) -> None:
        """The write is skipped exactly when the server already equals the SSOT."""
        plan = self._plan("org_repo")
        pairs = self._ssot_pairs()
        values = m.Infra.SonarcloudSettingsValues.model_validate_json

        tm.that(plan.in_sync_with(values(self._server_payload(pairs))), eq=True)
        tm.that(
            plan.in_sync_with(values(self._server_payload(tuple(reversed(pairs))))),
            eq=True,
        )
        tm.that(plan.in_sync_with(values(self._server_payload(()))), eq=False)
        tm.that(
            plan.in_sync_with(
                values(self._server_payload((*pairs, ("text:S0000", "x.toml"))))
            ),
            eq=False,
        )

    def test_plan_refuses_empty_and_repeated_exclusions(self) -> None:
        """An SSOT that cannot be written as one property set fails before effects."""
        spec = config.Infra.codegen.sonarcloud
        empty = spec.model_copy(update={"issue_exclusions": ()})
        repeated = spec.model_copy(
            update={"issue_exclusions": (*spec.issue_exclusions,) * 2}
        )

        for invalid, reason in ((empty, "declares no exclusion"), (repeated, "repeats")):
            tm.fail(
                FlextInfraSonarcloudSettingsSync.settings_plan(invalid, "org_repo"),
                has=reason,
            )

    def test_workspace_root_fans_the_verb_out(self) -> None:
        """The workspace orchestrator accepts the verb so the root reaches members."""
        tm.that(c.Infra.ORCHESTRATED_VERBS, has=c.Infra.VERB_SONARCLOUD_SYNC)

    def test_absent_token_fails_before_any_effect(self, tmp_path: Path) -> None:
        """Without SONAR_TOKEN the verb fails first, before reading origin or API."""
        u.Tests.initialize_git_repo(tmp_path)

        code, output = self._cli(tmp_path)

        tm.that(code, ne=0)
        tm.that(output, has="SONAR_TOKEN is required")

    def test_whitespace_token_is_refused(self, tmp_path: Path) -> None:
        """A whitespace-only token is absent, never trimmed into a request."""
        u.Tests.initialize_git_repo(tmp_path)

        code, output = self._cli(tmp_path, env={"SONAR_TOKEN": "   "})

        tm.that(code, ne=0)
        tm.that(output, has="SONAR_TOKEN is required")


__all__: list[str] = ["TestsFlextInfraSonarcloudSettingsSync"]
