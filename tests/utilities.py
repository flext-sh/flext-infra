"""Test utilities for flext-infra."""

from __future__ import annotations

from flext_infra import u as flext_infra_u
from flext_tests import FlextTestsUtilities
from tests import m
from tests.utilities_codegen import TestsFlextInfraUtilitiesCodegenMixin
from tests.utilities_deps import TestsFlextInfraUtilitiesDepsMixin
from tests.utilities_fixture_docs import TestsFlextInfraUtilitiesDocsFixtureMixin
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin
from tests.utilities_fixture_tooling import TestsFlextInfraUtilitiesToolingFixtureMixin
from tests.utilities_fixture_workspace import (
    TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
)
from tests.utilities_gates import TestsFlextInfraUtilitiesGatesMixin
from tests.utilities_git import TestsFlextInfraUtilitiesGitMixin
from tests.utilities_release import TestsFlextInfraUtilitiesReleaseMixin
from tests.utilities_replay import TestsFlextInfraUtilitiesReplayRunnerMixin
from tests.utilities_replay_sequence import TestsFlextInfraUtilitiesReplaySequenceMixin
from tests.utilities_toml import TestsFlextInfraUtilitiesTomlMixin
from tests.utilities_workspace_env import TestsFlextInfraUtilitiesWorkspaceEnvMixin


class TestsFlextInfraUtilities(FlextTestsUtilities, flext_infra_u):
    """Typed test utilities for flext-infra."""

    class Tests(
        TestsFlextInfraUtilitiesTomlMixin,
        TestsFlextInfraUtilitiesReplayRunnerMixin,
        TestsFlextInfraUtilitiesReplaySequenceMixin,
        TestsFlextInfraUtilitiesProjectFixtureMixin,
        TestsFlextInfraUtilitiesWorkspaceFixtureMixin,
        TestsFlextInfraUtilitiesToolingFixtureMixin,
        TestsFlextInfraUtilitiesDocsFixtureMixin,
        TestsFlextInfraUtilitiesReleaseMixin,
        TestsFlextInfraUtilitiesGitMixin,
        TestsFlextInfraUtilitiesGatesMixin,
        TestsFlextInfraUtilitiesCodegenMixin,
        TestsFlextInfraUtilitiesDepsMixin,
        TestsFlextInfraUtilitiesWorkspaceEnvMixin,
        FlextTestsUtilities.Tests,
    ):
        """Canonical test helper namespace."""

        @staticmethod
        def enforcement_rule(rule_id: str) -> m.EnforcementRuleSpec:
            """Resolve one enabled rule from the canonical enforcement catalog."""
            catalog = u.build_canonical_catalog()
            rule: m.EnforcementRuleSpec = next(
                rule for rule in catalog.enabled_rules() if rule.id == rule_id
            )
            return rule


u = TestsFlextInfraUtilities

__all__: list[str] = ["TestsFlextInfraUtilities", "u"]
