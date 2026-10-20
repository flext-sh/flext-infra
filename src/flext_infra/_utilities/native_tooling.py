"""Validate and compose the declared native tool-option catalog.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from copy import deepcopy

from flext_cli import u
from typing_extensions import TypeForm

from flext_infra import m, t


class FlextInfraUtilitiesNativeTooling:
    """Own native option values without file-discovery or projection behavior."""

    @staticmethod
    def configuration_pairs(
        entries: t.SequenceOf[t.Pair[str, t.JsonValue]],
    ) -> t.JsonDict:
        """Elect ordered pairs and isolate their mutable values from consumers.

        Returns:
            The last declared value per key, preserving nested array order.

        """
        return deepcopy(dict(entries))

    @staticmethod
    def native_tool_settings(
        document: m.Infra.ToolConfigDocument, table: str
    ) -> t.JsonDict:
        """Read a declared native table without inventing an absent configuration.

        Returns:
            The elected JSON-compatible options for the declared table.

        """
        return FlextInfraUtilitiesNativeTooling.configuration_pairs(
            document.settings[table]
        )

    @staticmethod
    def native_tool_configuration(
        document: m.Infra.ToolConfigDocument, root: str
    ) -> t.JsonDict:
        """Compose a declared native root and its nested option tables.

        Returns:
            The elected tool configuration with native nested table structure.

        Raises:
            KeyError: If the requested root has no declared option tables.

        """
        result: t.JsonDict = {}
        selected = False
        for table, entries in sorted(document.settings.items()):
            owner, separator, nested = table.partition(".")
            if owner != root:
                continue
            selected = True
            target = u.Cli.toml_mapping_ensure_path(
                result, nested.split(".") if separator else ()
            )
            target.update(FlextInfraUtilitiesNativeTooling.configuration_pairs(entries))
        if not selected:
            raise KeyError(root)
        return result

    @staticmethod
    def native_tool_setting[TValue](
        document: m.Infra.ToolConfigDocument,
        table: str,
        key: str,
        target: TypeForm[TValue],
    ) -> TValue:
        """Validate one native option, preserving lookup and validation failures.

        Returns:
            The configured value validated against the consumer's type.

        """
        options = FlextInfraUtilitiesNativeTooling.native_tool_settings(document, table)
        return u.type_adapter(target).validate_python(options[key], strict=True)


__all__ = ["FlextInfraUtilitiesNativeTooling"]
