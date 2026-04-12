"""TOML utility helpers for flext-infra.

Provides infra-specific TOML operations with validation via INFRA adapters.
Pure TOML operations are available directly via ``u.Cli.toml_*``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence

from pydantic import ValidationError

from flext_cli import FlextCliUtilities
from flext_infra import t


class FlextInfraUtilitiesToml:
    """Infra-specific TOML helpers — validation via INFRA adapters.

    For pure TOML operations use ``u.Cli.toml_*`` directly::

        doc = u.Cli.toml_read(some_path)
        table = u.Cli.toml_ensure_table(parent, key)
    """

    @staticmethod
    def as_toml_mapping(value: t.Infra.InfraValue) -> t.Infra.ContainerDict | None:
        """Check if value is a MutableMapping and return it typed, otherwise None."""
        normalized_value = FlextCliUtilities.Cli.toml_as_mapping(value)
        if normalized_value is None:
            return None
        try:
            validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                normalized_value,
            )
        except ValidationError:
            return None
        result: t.Infra.ContainerDict = {str(key): validated[key] for key in validated}
        return result

    @staticmethod
    def unwrap_item(
        value: t.Infra.InfraValue
        | t.Cli.TomlItem
        | t.Cli.TomlDocument
        | Mapping[str, t.Infra.InfraValue]
        | None,
    ) -> t.Infra.InfraValue | None:
        """Unwrap TOML items/documents to a concrete Python value.

        SSOT for TOML value normalization — replaces ``normalize_container_value``.
        """
        normalized = FlextCliUtilities.Cli.toml_unwrap_item(value)
        if normalized is None or isinstance(normalized, (str, int, float, bool)):
            return normalized
        if isinstance(normalized, Mapping):
            try:
                return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(normalized)
            except ValidationError:
                return None
        if isinstance(normalized, (list, tuple)):
            try:
                return t.Infra.INFRA_SEQ_ADAPTER.validate_python(normalized)
            except ValidationError:
                return None
        return None

    @staticmethod
    def get(
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        key: t.Infra.InfraValue,
    ) -> t.Infra.InfraValue | None:
        """Retrieve and normalize a value from a TOML container by key."""
        if not isinstance(key, str):
            return None
        return FlextInfraUtilitiesToml.unwrap_item(
            FlextCliUtilities.Cli.toml_value(container, key),
        )

    @staticmethod
    def sync_value(
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        key: str,
        expected: t.Infra.InfraValue,
        changes: MutableSequence[str],
        change_message: str,
    ) -> bool:
        """Synchronize a scalar TOML value when it differs."""
        current = FlextInfraUtilitiesToml.unwrap_item(
            FlextCliUtilities.Cli.toml_value(container, key)
        )
        if current == expected:
            return False
        container[key] = expected
        changes.append(change_message)
        return True


__all__: list[str] = ["FlextInfraUtilitiesToml"]
