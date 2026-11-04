"""Render the canonical Markdown tool configuration from its typed policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from flext_cli import u

from flext_infra import p, t
from flext_infra._utilities.base import FlextInfraUtilitiesBase


class FlextInfraUtilitiesMarkdownTooling(FlextInfraUtilitiesBase):
    """Project one typed Markdown policy into its native tool dialects."""

    @staticmethod
    def markdown_native_configuration(
        markdown: p.Infra.MarkdownConfig,
        excludes: Sequence[str],
    ) -> str:
        """Render canonical rumdl TOML from the common policy and overrides.

        Returns:
            Native TOML consumed by lint, repair, formatting and the editor.

        """
        rules = FlextInfraUtilitiesBase.configuration_pairs(markdown.rules)
        for name, value in markdown.native_rules:
            common = rules.get(name)
            rules[name] = (
                {**common, **value}
                if isinstance(common, Mapping) and isinstance(value, Mapping)
                else value
            )
        native_settings = FlextInfraUtilitiesBase.configuration_pairs(
            markdown.native_settings
        )
        disabled: list[t.JsonValue] = [
            *sorted(name for name, value in rules.items() if value is False)
        ]
        enabled: list[t.JsonValue] = (
            []
            if markdown.default_enabled
            else [*sorted(name for name, value in rules.items() if value is not False)]
        )
        exclude: list[t.JsonValue] = [*sorted(dict.fromkeys(excludes))]
        global_options: t.JsonDict = {"exclude": exclude, "disable": disabled}
        if markdown.extend_enable:
            extend: list[t.JsonValue] = [*sorted(markdown.extend_enable)]
            global_options["extend-enable"] = extend
        if enabled:
            global_options["enable"] = enabled
        document: t.JsonDict = {"global": global_options}
        for name in sorted(native_settings):
            document[name] = native_settings[name]
        for name in sorted(rules):
            value = rules[name]
            if isinstance(value, Mapping):
                document[name] = value
        return u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(document))

    @staticmethod
    def markdown_editor_configuration(markdown: p.Infra.MarkdownConfig) -> t.JsonDict:
        """Elect the editor-compatible policy from the common Markdown rules.

        Native rumdl rules and tables (``native_rules``/``native_settings``)
        stay execution-tool-only: the editor projection reads the common
        ``MD*`` rules exactly as declared, so one SSOT policy owns both tool
        dialects without copying the native surface.

        Returns:
            The JSON mapping consumed by the settings projection.

        """
        editor: t.JsonDict = {"default": markdown.default_enabled}
        editor.update(FlextInfraUtilitiesBase.configuration_pairs(markdown.rules))
        return editor


__all__: list[str] = ["FlextInfraUtilitiesMarkdownTooling"]
