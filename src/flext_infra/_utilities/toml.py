"""TOML utility helpers for flext-infra.

Provides type-safe TOML operations: normalization, reading, table manipulation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence
from pathlib import Path

from pydantic import BaseModel, ValidationError
from tomlkit.items import Item, Table
from tomlkit.toml_document import TOMLDocument

from flext_core import r
from flext_infra import t, u


class FlextInfraUtilitiesToml:
    """TOML utility helpers — normalization, reading, table manipulation.

    Usage::

        from flext_infra import u

        result = u.Infra.as_toml_mapping(value)
        doc = u.Cli.toml_read(some_path)
    """

    @staticmethod
    def as_toml_mapping(value: t.Infra.InfraValue) -> t.Infra.ContainerDict | None:
        """Check if value is a MutableMapping and return it typed, otherwise None."""
        normalized_value = u.Cli.toml_as_mapping(value)
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
        | Item
        | TOMLDocument
        | Mapping[str, t.Infra.InfraValue]
        | None,
    ) -> t.Infra.InfraValue | None:
        """Unwrap TOML items/documents to a concrete Python value.

        SSOT for TOML value normalization — replaces ``normalize_container_value``.
        """
        normalized = u.Cli.toml_unwrap_item(value)
        if normalized is None or isinstance(normalized, (str, int, float, bool)):
            return normalized
        if u.is_mapping(normalized):
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
    def as_string_list(value: t.Infra.InfraValue | Item | None) -> t.StrSequence:
        """Convert TOML value to list of strings."""
        return u.Cli.toml_as_string_list(value)

    @staticmethod
    def array(items: t.StrSequence) -> t.Cli.TomlArray:
        """Create multiline TOML array from string items."""
        return u.Cli.toml_array(items)

    @staticmethod
    def get_table(container: TOMLDocument | Table, key: str) -> Table | None:
        """Get a sub-table from a TOML container, or None if missing/not a Table."""
        return u.Cli.toml_get_table(container, key)

    @staticmethod
    def get_item(container: TOMLDocument | Table, key: str) -> Item | None:
        """Get a raw TOML Item from a container, or None if missing."""
        return u.Cli.toml_get_item(container, key)

    @staticmethod
    def ensure_table(parent: Table | TOMLDocument, key: str) -> Table:
        """Get or create a TOML table in parent.

        When the key already exists as a dotted-key implicit ("super") table,
        promote it to an explicit table so that tomlkit serializes sub-tables
        under the correct parent path instead of creating bare top-level sections.
        """
        return u.Cli.toml_ensure_table(parent, key)

    @staticmethod
    def get(
        container: TOMLDocument | Table,
        key: t.Infra.InfraValue,
    ) -> t.Infra.InfraValue | None:
        """Retrieve and normalize a value from a TOML container by key."""
        if not isinstance(key, str):
            return None
        raw_value = u.Cli.toml_get(container, key)
        if raw_value is None:
            return None
        if isinstance(
            raw_value,
            (str, int, float, bool, type(None), BaseModel, Path),
        ):
            return raw_value
        if u.is_mapping(raw_value):
            try:
                return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                    raw_value,
                )
            except ValidationError:
                return None
        try:
            return t.Cli.JSON_LIST_ADAPTER.validate_python(
                raw_value,
            )
        except ValidationError:
            return None

    @staticmethod
    def table_string_keys(table: Table) -> t.StrSequence:
        """Return table keys as strings."""
        return u.Cli.toml_table_string_keys(table)

    @staticmethod
    def sync_value(
        container: TOMLDocument | Table,
        key: str,
        expected: t.Infra.InfraValue,
        changes: MutableSequence[str],
        change_message: str,
    ) -> bool:
        """Synchronize a scalar TOML value when it differs."""
        current = FlextInfraUtilitiesToml.unwrap_item(u.Cli.toml_get(container, key))
        if current == expected:
            return False
        container[key] = expected
        changes.append(change_message)
        return True

    @staticmethod
    def sync_string_list(
        container: TOMLDocument | Table,
        key: str,
        expected: t.StrSequence,
        changes: MutableSequence[str],
        change_message: str,
        *,
        sort_values: bool = False,
    ) -> bool:
        """Synchronize a string-array TOML value when it differs."""
        return u.Cli.toml_sync_string_list(
            container,
            key,
            expected,
            changes,
            change_message,
            sort_values=sort_values,
        )

    @staticmethod
    def read(path: Path) -> TOMLDocument | None:
        """Read and parse TOML document from file.

        Returns None when the file does not exist or is invalid TOML.
        Prefer ``read_document`` for r-wrapped semantics.
        """
        return u.Cli.toml_read(path)

    @staticmethod
    def read_document(path: Path) -> r[TOMLDocument]:
        """Read and parse a TOML document, returning r.

        Args:
            path: Path to the TOML file.

        Returns:
            r[TOMLDocument] with parsed document on success,
            or failure with descriptive error.

        """
        return u.Cli.toml_read_document(path)

    @staticmethod
    def write_document(path: Path, doc: TOMLDocument) -> r[bool]:
        """Write a TOML document to file.

        Creates parent directories as needed.

        Args:
            path: Destination file path.
            doc: TOML document to serialize.

        Returns:
            r[bool] with True on success.

        """
        return u.Cli.toml_write_document(path, doc)


__all__ = ["FlextInfraUtilitiesToml"]
