"""Typed ACTION registry contract tests for generated Make configuration."""

from __future__ import annotations

import pytest

from flext_infra import c, config, m
from flext_tests import tm


class TestsTypedMakeContract:
    def test_action_requires_unique_non_empty_whats_and_typed_apply_mode(self) -> None:
        action = m.Infra.MakeActionSpec(whats=("all", "docs"), apply_mode="optional")

        tm.that(action.whats, eq=("all", "docs"))
        tm.that(action.apply_mode, eq="optional")
        with pytest.raises(c.ValidationError):
            m.Infra.MakeActionSpec(whats=(), apply_mode="never")
        with pytest.raises(c.ValidationError):
            m.Infra.MakeActionSpec(whats=("all", "all"), apply_mode="required")
        with pytest.raises(c.ValidationError):
            m.Infra.MakeActionSpec.model_validate({
                "whats": ["all"],
                "apply_mode": "sometimes",
            })

    def test_verb_requires_declared_default_action(self) -> None:
        action = m.Infra.MakeActionSpec(whats=("all",), apply_mode="never")

        verb = m.Infra.MakeVerbSpec(
            name="check", default_action="run", actions={"run": action}
        )

        tm.that(verb.default_action, eq="run")
        tm.that(verb.default_apply, eq=False)
        with pytest.raises(c.ValidationError):
            m.Infra.MakeVerbSpec(
                name="check", default_action="missing", actions={"run": action}
            )

    def test_verb_matrix_uses_actions_without_legacy_selector_fields(self) -> None:
        make = config.Infra.codegen.make
        verbs = {verb.name: verb for verb in make.verbs}

        tm.that("docs" in verbs, eq=False)
        tm.that(hasattr(make, "serialization"), eq=False)
        for verb in verbs.values():
            tm.that(hasattr(verb, "default_what"), eq=False)
            tm.that(hasattr(verb, "apply_what"), eq=False)
            tm.that(hasattr(verb, "apply_guarded"), eq=False)
            tm.that(hasattr(verb, "accepts_apply"), eq=False)
        tm.that(verbs["work"].default_action, eq="status")
        tm.that(tuple(verbs["work"].actions), eq=("start", "status", "land", "finish"))
        tm.that(verbs["setup"].default_apply, eq=True)
        tm.that(verbs["clean"].default_apply, eq=True)
        tm.that(verbs["test"].actions["cache-checkpoint"].apply_mode, eq="required")

    def test_docs_are_rehomed_to_standard_verb_scopes(self) -> None:
        verbs = {verb.name: verb for verb in config.Infra.codegen.make.verbs}

        for verb in ("build", "check", "test", "fmt", "fix", "gen"):
            default = verbs[verb].actions[verbs[verb].default_action]
            tm.that("docs" in default.whats, eq=True)

    def test_workflow_step_supports_an_optional_action(self) -> None:
        step = m.Infra.MakeWorkflowStepSpec(
            verb="test", action="full", contexts=("local", "pre_push")
        )

        tm.that(step.action, eq="full")
        tm.that(
            m.Infra.MakeWorkflowStepSpec(
                verb="check", contexts=("local", "ci")
            ).action,
            eq=None,
        )

    def test_ci_rules_are_ternary_and_never_exclude_markdown(self) -> None:
        ci = config.Infra.codegen.make.ci

        tm.that(hasattr(ci, "check_gates_skip"), eq=False)
        tm.that(set(ci.rules), eq={"enabled", "disabled", "absent"})
        tm.that(ci.rules["enabled"].test_mode, eq="skip")
        tm.that(ci.rules["disabled"].test_mode, eq="full")
        tm.that(ci.rules["absent"].test_mode, eq="incremental")
        for rule in ci.rules.values():
            tm.that(rule.check_gate_exclusions, lacks="markdown")
        with pytest.raises(c.ValidationError):
            m.Infra.MakeCiSpec.model_validate({
                "variable": "CI",
                "enabled_value": "Y",
                "disabled_value": "N",
                "rules": {
                    "enabled": {
                        "check_gate_exclusions": ["markdown"],
                        "test_mode": "skip",
                    },
                    "disabled": {
                        "check_gate_exclusions": [],
                        "test_mode": "full",
                    },
                    "absent": {
                        "check_gate_exclusions": [],
                        "test_mode": "incremental",
                    },
                },
            })
