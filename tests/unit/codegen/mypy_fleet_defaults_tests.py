"""Validate fleet-mandatory Mypy policy through the typed YAML owner.

Pydantic 2 and its plugin remain mandatory. Configuration, not declaration
defaults, owns the selected policy; tests validate its public input contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, deps
from tests import e, m, t, tm, u


class TestsFlextInfraMypyFleetMandatoryDefaults:
    """The selected SSOT policy survives validation and rejects weakening."""

    @staticmethod
    def _document_payload(
        *entries: t.Pair[str, t.JsonValue],
    ) -> t.JsonMapping:
        """Supply native option deltas through the same document production reads.

        Returns:
            The tooling document payload with the given entries appended to the
            native mypy settings.

        """
        payload = config.Infra.tooling.model_dump(
            mode="json", by_alias=True, exclude_computed_fields=True
        )
        settings = payload["settings"]
        return {
            **payload,
            "settings": {
                **settings,
                "mypy": [*settings["mypy"], *map(list, entries)],
            },
        }

    @staticmethod
    def test_selected_policy_round_trips() -> None:
        """The same typed SSOT supplies production and expected policy values."""
        document = config.Infra.tooling
        validated = m.Infra.ToolConfigDocument.model_validate(
            document.model_dump(by_alias=True, exclude_computed_fields=True)
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
        policy = document.tools.mypy.model_dump(
            by_alias=True, exclude_computed_fields=True
        )
        policy[field] = []
        payload = {
            **document.model_dump(by_alias=True, exclude_computed_fields=True),
            "tools": {
                **document.tools.model_dump(
                    by_alias=True, exclude_computed_fields=True
                ),
                "mypy": policy,
            },
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
        value: t.JsonValue,
    ) -> None:
        """Generic options cannot bypass the dedicated plugin and code fields."""
        payload = self._document_payload((option, value))
        with pytest.raises(e.PydanticValidationError, match=r"[Mm]ypy"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @pytest.mark.parametrize("option", ["follow-imports", "follow_imports "])
    def test_generic_options_reject_option_alias_collisions(self, option: str) -> None:
        """An alias cannot shadow the canonical native option from another layer."""
        payload = self._document_payload(
            ("follow_imports", "normal"),
            (option, "error"),
        )
        with pytest.raises(e.PydanticValidationError):
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
        with pytest.raises(e.PydanticValidationError):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        ("option", "value"),
        [
            ("ignore_errors", True),
            ("disable_error_code", ["assignment"]),
        ],
    )
    def test_override_options_cannot_hide_diagnostics(
        option: str,
        value: t.JsonValue,
    ) -> None:
        """Free native override options cannot bypass the diagnostic policy."""
        document = config.Infra.tooling
        mypy = document.tools.mypy.model_dump(
            by_alias=True, exclude_computed_fields=True
        )
        mypy["overrides"] = [
            {
                "modules": ["arbitrary_dependency.*"],
                "settings": [(option, value)],
                "justification": "https://mypy.readthedocs.io/en/stable/config_file.html",
            }
        ]
        payload = {
            **document.model_dump(by_alias=True, exclude_computed_fields=True),
            "tools": {
                **document.tools.model_dump(
                    by_alias=True, exclude_computed_fields=True
                ),
                "mypy": mypy,
            },
        }
        with pytest.raises(e.PydanticValidationError, match=r"[Mm]ypy"):
            m.Infra.ToolConfigDocument.model_validate(payload)

    @staticmethod
    def test_mypy_path_projection_converges_before_path_sync(tmp_path: Path) -> None:
        """The table phase retains elected roots before sync.

        The same roots survive repeated conformance.

        """
        tooling = config.Infra.tooling
        source_dir = tooling.tools.pyrefly.path_rules.source_dir
        package = tmp_path / source_dir / "arbitrary_package"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        path = tmp_path / "pyproject.toml"
        source = (
            '[project]\nname = "arbitrary-project"\ndependencies = []\n'
            '[tool.mypy]\nmypy_path = ["retired-root"]\n'
        )
        path.write_text(source, encoding="utf-8")
        manager = deps.FlextInfraExtraPathsManager(repository_root=tmp_path)
        expected = manager.mypy_search_paths(project_dir=tmp_path, is_root=True)
        topology = m.Infra.PyprojectDeclaredTopology(
            declared_python_dirs=(source_dir,),
            declared_python_dirs_are_complete=True,
        )
        modernizer = deps.FlextInfraPyprojectModernizer(repository_root=tmp_path)
        first = tm.ok(
            modernizer.conform_source(
                source,
                path=path,
                format_source=False,
                topology=topology,
            )
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(first)
        )
        mypy = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["mypy"])
        tm.that(mypy["mypy_path"], eq=list(expected))
        tm.that(
            deps.FlextInfraToolTablesPhase(tooling).apply_payload(
                payload, path=path, mypy_search_paths=expected
            ),
            empty=True,
        )
        tm.that(
            manager.sync_payload(
                payload,
                project_dir=tmp_path,
                is_root=True,
                mypy_search_paths=expected,
            ),
            empty=True,
        )
        tm.that(
            tm.ok(
                modernizer.conform_source(
                    first,
                    path=path,
                    format_source=False,
                    topology=topology,
                )
            ),
            eq=first,
        )
