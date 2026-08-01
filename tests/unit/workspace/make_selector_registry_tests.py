"""Tests for selector ownership in the typed Make registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraCli, c, config, m
from flext_tests import tm
from tests import u as test_u

if TYPE_CHECKING:
    from tests import t


class TestsRegistrySelectors:
    def test_defaults_and_mutation_intent_resolve_from_handlers(self) -> None:
        """Every default and mutation selector resolves in its owning verb."""
        make_config = config.Infra.codegen.make

        for verb in make_config.verbs:
            default_handler = verb.handlers[verb.default_what]
            tm.that(default_handler.target, empty=False)
            for selector, handler in verb.handlers.items():
                tm.that(selector, empty=False)
                tm.that(handler.target, empty=False)
                if handler.mutating:
                    tm.that(verb.name in make_config.mutation_verbs, eq=True)

    def test_cli_preserves_workspace_route_owned_what(self) -> None:
        """Workspace orchestration receives its own typed test selector untouched."""
        cli = FlextInfraCli()
        args = ("orchestrate", "--verb", "test", "--what", "unit")

        tm.that(
            c.Infra.CLI_GROUP_WORKSPACE in c.Infra.CLI_GROUPS_TRANSLATING_WHAT, eq=False
        )
        tm.that(
            tm.ok(cli.translate_what(c.Infra.CLI_GROUP_WORKSPACE, args)), eq=list(args)
        )

    def test_apply_tokens_are_distinct_and_shell_safe(self) -> None:
        """Typed config accepts generic safe tokens and rejects ambiguous intent."""
        payload = config.Infra.codegen.make.model_dump(
            mode="python", exclude_computed_fields=True
        )
        payload.update({"apply_value": "ENABLE_2", "apply_absent_value": "DISABLED-2"})

        validated = m.Infra.MakeSpec.model_validate(payload)

        tm.that(validated.apply_value, eq="ENABLE_2")
        tm.that(validated.apply_absent_value, eq="DISABLED-2")
        payload["apply_absent_value"] = payload["apply_value"]
        with pytest.raises(ValueError, match="tokens must be distinct"):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.parametrize(
        ("field", "value"), [("apply_value", "$Y"), ("apply_absent_value", "N#")]
    )
    def test_apply_tokens_reject_make_and_shell_metacharacters(
        self, field: str, value: str
    ) -> None:
        """Generated Make and shell interpolation only receives safe token atoms."""
        payload = config.Infra.codegen.make.model_dump(
            mode="python", exclude_computed_fields=True
        )
        payload[field] = value

        with pytest.raises(ValueError, match="string_pattern_mismatch"):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.parametrize(
        ("field", "value"), [("selector", "WHAT VALUE"), ("apply_variable", "APPLY$")]
    )
    def test_make_variables_reject_invalid_identifiers(
        self, field: str, value: str
    ) -> None:
        """Make variable names remain valid at their generated consumer boundary."""
        payload = config.Infra.codegen.make.model_dump(
            mode="python", exclude_computed_fields=True
        )
        payload[field] = value

        with pytest.raises(ValueError, match="string_pattern_mismatch"):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.parametrize("collision", ["selector", "apply_variable"])
    def test_ci_variable_is_distinct_from_public_make_variables(
        self, collision: str
    ) -> None:
        """Generated automation and dispatch variables cannot alias each other."""
        make_config = config.Infra.codegen.make
        payload = make_config.model_dump(mode="python", exclude_computed_fields=True)
        ci = dict(payload["ci"])
        ci["variable"] = payload[collision]
        payload["ci"] = ci

        with pytest.raises(ValueError, match="variables must be distinct"):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.parametrize("disabled", ["0", "false"])
    def test_ci_value_rejects_disabled_normalization_tokens(
        self, disabled: str
    ) -> None:
        """The configured enabled state cannot normalize to automation off."""
        payload = config.Infra.codegen.make.model_dump(
            mode="python", exclude_computed_fields=True
        )
        ci = dict(payload["ci"])
        ci["value"] = disabled
        payload["ci"] = ci

        with pytest.raises(ValueError, match="enabled automation state"):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.parametrize("location", ["name", "default", "key", "target"])
    def test_handler_registry_rejects_invalid_dispatch_atoms(
        self, location: str
    ) -> None:
        """Every value interpolated into targets and maps is a safe lowercase atom."""
        verb = config.Infra.codegen.make.verbs[0]
        payload = verb.model_dump(mode="python")
        if location == "name":
            payload["name"] = "bad verb"
        elif location == "default":
            payload["default_what"] = "bad selector"
        elif location == "key":
            payload["handlers"] = {
                "bad selector": next(iter(verb.handlers.values())).model_dump(
                    mode="python"
                )
            }
        else:
            handlers = dict(payload["handlers"])
            default_handler = dict(handlers[verb.default_what])
            default_handler["target"] = "bad target"
            handlers[verb.default_what] = default_handler
            payload["handlers"] = handlers

        with pytest.raises(ValueError, match="string_pattern_mismatch"):
            m.Infra.MakeVerbSpec.model_validate(payload)

    def test_docs_registry_owner_is_required_before_computed_access(self) -> None:
        """A missing docs owner fails with the intentional registry invariant."""
        make_config = config.Infra.codegen.make
        payload = make_config.model_dump(mode="python", exclude_computed_fields=True)
        payload["verbs"] = tuple(
            verb.model_dump(mode="python")
            for verb in make_config.verbs
            if verb.name != "docs"
        )

        with pytest.raises(ValueError, match="docs verb must be declared"):
            m.Infra.MakeSpec.model_validate(payload)

    def test_automated_workflow_rejects_project_custom_hooks(self) -> None:
        """CI and pre-commit cannot execute repository-defined hook side effects."""
        make_config = config.Infra.codegen.make
        payload = make_config.model_dump(mode="python", exclude_computed_fields=True)
        automation_verb = next(
            step.verb
            for step in make_config.workflow
            if set(step.contexts) & {"ci", "pre_commit"}
        )
        payload["verbs"] = tuple(
            {
                **verb.model_dump(mode="python"),
                "automation_hooks": verb.name == automation_verb,
            }
            for verb in make_config.verbs
        )

        with pytest.raises(
            ValueError, match="automated workflow verbs must disable custom hooks"
        ):
            m.Infra.MakeSpec.model_validate(payload)

    @pytest.mark.parametrize(
        "unsupported",
        ["missing-dispatcher", "builtin", "serialized", "orchestrated", "mutating"],
    )
    def test_repository_extra_verbs_reject_unimplemented_semantics(
        self, unsupported: str
    ) -> None:
        """Repository extensions expose only the implemented read-only script lane."""
        payload = test_u.Tests.repository_ref("fixture-repository").model_dump(
            mode="python"
        )
        verb = m.Infra.MakeVerbSpec(
            name="fixture-action",
            default_what="all",
            dispatch="builtin" if unsupported == "builtin" else "script",
            handlers={"all": {"target": "all", "mutating": unsupported == "mutating"}},
            serialized=unsupported == "serialized",
            orchestrated=unsupported == "orchestrated",
        )
        payload["extra_verbs"] = (verb.model_dump(mode="python"),)
        if unsupported != "missing-dispatcher":
            payload["script_dispatch"] = {
                "dispatcher": "scripts/dispatch.py",
                "roots": ("scripts",),
            }

        with pytest.raises(
            ValueError,
            match=(
                "require script_dispatch"
                if unsupported == "missing-dispatcher"
                else "support only read-only, non-serialized script dispatch"
            ),
        ):
            m.Infra.RepositoryRef.model_validate(payload)

    def test_repository_extra_verb_names_are_unique(self) -> None:
        """Duplicate public extension names fail before Makefile rendering."""
        payload = test_u.Tests.repository_ref("fixture-repository").model_dump(
            mode="python"
        )
        verb = m.Infra.MakeVerbSpec(
            name="fixture-action",
            default_what="all",
            dispatch="script",
            handlers={"all": {"target": "all"}},
        )
        payload["extra_verbs"] = (
            verb.model_dump(mode="python"),
            verb.model_dump(mode="python"),
        )
        payload["script_dispatch"] = {
            "dispatcher": "scripts/dispatch.py",
            "roots": ("scripts",),
        }

        with pytest.raises(ValueError, match="extra Make verb names must be unique"):
            m.Infra.RepositoryRef.model_validate(payload)


__all__: t.StrSequence = []
