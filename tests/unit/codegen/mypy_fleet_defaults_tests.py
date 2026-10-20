"""Validate fleet-mandatory Mypy policy through the typed YAML owner.

Pydantic 2 and its plugin remain mandatory. Configuration, not declaration
defaults, owns the selected policy; tests validate its public input contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_core import e

from flext_infra import config, m, t
from tests import tm, u


class TestsMypyFleetMandatoryDefaults:
    """The selected SSOT policy survives validation and rejects weakening."""

    @staticmethod
    def _document_payload(
        *entries: t.Pair[str, t.JsonValue],
    ) -> t.JsonMapping:
        """Supply native option deltas through the same document production reads."""
        document = config.Infra.tooling
        return {
            **document.model_dump(by_alias=True),
            "settings": {
                **document.settings,
                "mypy": (*document.settings["mypy"], *entries),
            },
        }

    @staticmethod
    def test_selected_policy_round_trips() -> None:
        """The same typed SSOT supplies production and expected policy values."""
        document = config.Infra.tooling
        validated = m.Infra.ToolConfigDocument.model_validate(
            document.model_dump(by_alias=True)
        )
        tm.that(
            u.Infra.native_tool_settings(validated, "mypy"),
            eq=u.Infra.native_tool_settings(document, "mypy"),
        )

    @staticmethod
    @pytest.mark.parametrize(
        "field", ["disable-error-code", "facade-rebind-error-codes"]
    )
    def test_selected_policy_rejects_retired_suspensions(
        field: str,
    ) -> None:
        """No suppression catalog can return through the owned typed boundary."""
        document = config.Infra.tooling
        policy = document.tools.mypy.model_dump(by_alias=True)
        policy[field] = []
        payload = {
            **document.model_dump(by_alias=True),
            "tools": {**document.tools.model_dump(by_alias=True), "mypy": policy},
        }
        with pytest.raises(e.PydanticValidationError, match=field):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @pytest.mark.parametrize(
        ("option", "value"),
        [
            ("plugins", "pydantic.v1.mypy"),
            ("disable_error_code", "assignment"),
            ("disable-error-code", "assignment"),
            ("plugins ", "pydantic.v1.mypy"),
            ("python_version", "0.0"),
            ("python-version", "0.0"),
            ("mypy_path", "untrusted"),
            ("plugins", False),
            ("disable_error_code", False),
            ("enable_error_code", True),
            ("enable-error-code", True),
            ("overrides", False),
            ("ignore_errors", True),
            ("ignore_errors", "true"),
        ],
    )
    def test_generic_options_cannot_shadow_typed_policy(
        self,
        option: str,
        value: t.Scalar,
    ) -> None:
        """Generic options cannot bypass the dedicated plugin and code fields."""
        payload = self._document_payload((option, value))
        with pytest.raises(e.PydanticValidationError, match="Mypy"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @pytest.mark.parametrize("option", ["follow-imports", "follow_imports "])
    def test_generic_options_reject_option_alias_collisions(
        self, option: str
    ) -> None:
        """An alias cannot shadow the canonical native option from another layer."""
        payload = self._document_payload(
            ("follow_imports", "normal"),
            (option, "error"),
        )
        with pytest.raises(e.PydanticValidationError, match="plain option names"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    def test_generic_option_pairs_elect_the_last_complete_value(self) -> None:
        """Exact repeated keys use the common last-pair-wins configuration contract."""
        payload = self._document_payload(
            ("follow_imports", "silent"),
            ("follow_imports", "normal"),
        )
        validated = m.Infra.ToolConfigDocument.model_validate(payload)
        tm.that(
            u.Infra.native_tool_settings(validated, "mypy")["follow_imports"],
            eq="normal",
        )

    def test_generic_options_allow_enabling_an_unsuspended_error(self) -> None:
        """Valid unrelated diagnostic settings remain supported without masking."""
        payload = self._document_payload(
            ("enable_error_code", "arg-type"),
            ("ignore_errors", False),
        )
        validated = m.Infra.ToolConfigDocument.model_validate(payload)
        options = u.Infra.native_tool_settings(validated, "mypy")
        tm.that(options["enable_error_code"], eq="arg-type")
        tm.that(options["ignore_errors"], eq=False)
        tm.that(
            options["plugins"],
            eq=u.Infra.native_tool_settings(config.Infra.tooling, "mypy")["plugins"],
        )

    def test_generic_options_allow_enabling_formerly_suspended_codes(self) -> None:
        """A stricter native diagnostic selection never suppresses another code."""
        payload = self._document_payload(("enable_error_code", "arg-type, call-arg"))
        validated = m.Infra.ToolConfigDocument.model_validate(payload)
        tm.that(
            u.Infra.native_tool_settings(validated, "mypy")["enable_error_code"],
            eq="arg-type, call-arg",
        )

    @pytest.mark.parametrize(
        "option",
        [
            'enable_error_code = "call-arg"\ncustom_option',
            '"plugins"',
            "follow-imports",
        ],
    )
    def test_generic_options_reject_toml_key_syntax(self, option: str) -> None:
        """A generic key is one option, never a quoted or injected TOML statement."""
        payload = self._document_payload((option, "normal"))
        with pytest.raises(e.PydanticValidationError, match="plain option names"):
            m.Infra.ToolConfigDocument.model_validate(payload)
