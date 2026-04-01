"""TOML utility helpers for flext-infra.

Provides type-safe TOML operations: normalization, reading, table manipulation.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import tomlkit
from flext_core import FlextLogger, FlextUtilities, r
from pydantic import BaseModel, ValidationError
from tomlkit.items import Array, Item, Table
from tomlkit.toml_document import TOMLDocument

from flext_infra import FlextInfraUtilitiesSubprocess, c, t


class FlextInfraUtilitiesToml:
    """TOML utility helpers — normalization, reading, table manipulation.

    Usage::

        from flext_infra import u

        result = u.Infra.as_toml_mapping(value)
        doc = u.Infra.read(some_path)
    """

    logger = FlextLogger(__name__)

    @staticmethod
    def as_toml_mapping(value: t.Infra.InfraValue) -> t.Infra.ContainerDict | None:
        """Check if value is a MutableMapping and return it typed, otherwise None."""
        if not FlextUtilities.is_mapping(value):
            return None
        try:
            normalized_value = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                value,
            )
        except ValidationError:
            return None
        result: t.Infra.ContainerDict = {
            str(key): normalized_value[key] for key in normalized_value
        }
        return result

    @staticmethod
    def normalize_container_value(
        value: t.Infra.InfraValue
        | Item
        | TOMLDocument
        | Mapping[str, t.Infra.InfraValue]
        | None,
    ) -> t.Infra.InfraValue | None:
        """Normalize TOML items/documents to a concrete container value."""
        normalized: (
            t.Infra.InfraValue | Item | Mapping[str, t.Infra.InfraValue] | None
        ) = value
        if isinstance(value, (TOMLDocument, Item)):
            normalized = value.unwrap()
        if isinstance(normalized, Item):
            return None
        return normalized

    @staticmethod
    def as_container_list(
        value: t.Infra.InfraValue | Item | None,
    ) -> Sequence[t.Infra.InfraValue]:
        """Validate and normalize list-like values to typed container list."""
        normalized = FlextInfraUtilitiesToml.normalize_container_value(value)
        if normalized is None:
            return []
        try:
            return t.Infra.JSON_SEQ_ADAPTER.validate_python(
                normalized,
            )
        except ValidationError:
            return []

    @staticmethod
    def unwrap_item(
        value: t.Infra.InfraValue | Item | None,
    ) -> t.Infra.InfraValue | None:
        """Unwrap a tomlkit Item to get the underlying value."""
        return FlextInfraUtilitiesToml.normalize_container_value(value)

    @staticmethod
    def as_string_list(value: t.Infra.InfraValue | Item | None) -> t.StrSequence:
        """Convert TOML value to list of strings."""
        normalized = FlextInfraUtilitiesToml.normalize_container_value(value)
        if normalized is None or isinstance(normalized, str):
            return []
        if isinstance(normalized, list):
            try:
                typed_items = t.Infra.JSON_SEQ_ADAPTER.validate_python(
                    normalized,
                )
            except ValidationError:
                return []
            return [str(raw) for raw in typed_items]
        return [
            str(raw) for raw in FlextInfraUtilitiesToml.as_container_list(normalized)
        ]

    @staticmethod
    def array(items: t.StrSequence) -> Array:
        """Create multiline TOML array from string items."""
        arr: Array = tomlkit.array()
        for item in items:
            arr.add_line(item)
        return arr.multiline(True)

    @staticmethod
    def ensure_table(parent: Table | TOMLDocument, key: str) -> Table:
        """Get or create a TOML table in parent.

        When the key already exists as a dotted-key implicit ("super") table,
        promote it to an explicit table so that tomlkit serializes sub-tables
        under the correct parent path instead of creating bare top-level sections.
        """
        existing: t.Infra.InfraValue | Item | None = None
        if key in parent:
            existing = parent[key]
        if isinstance(existing, Table):
            if not existing.is_super_table():
                return existing
            del parent[key]
            table = tomlkit.table()
            for k in FlextInfraUtilitiesToml.table_string_keys(existing):
                table[k] = existing[k]
            parent[key] = table
            return table
        table = tomlkit.table()
        parent[key] = table
        return table

    @staticmethod
    def get(
        container: TOMLDocument | Table,
        key: t.Infra.InfraValue,
    ) -> t.Infra.InfraValue | None:
        """Retrieve and normalize a value from a TOML container by key."""
        if not isinstance(key, str):
            return None
        raw_value: t.Infra.InfraValue | None = None
        if key in container:
            raw_value = FlextInfraUtilitiesToml.normalize_container_value(
                container[key],
            )
        if raw_value is None:
            return None
        if isinstance(
            raw_value,
            (str, int, float, bool, type(None), BaseModel, Path),
        ):
            return raw_value
        if FlextUtilities.is_mapping(raw_value):
            try:
                return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                    raw_value,
                )
            except ValidationError:
                return None
        try:
            return t.Infra.JSON_SEQ_ADAPTER.validate_python(
                raw_value,
            )
        except ValidationError:
            return None

    @staticmethod
    def table_string_keys(table: Table) -> t.StrSequence:
        """Return table keys as strings."""
        return list(table)

    @staticmethod
    def read(path: Path) -> TOMLDocument | None:
        """Read and parse TOML document from file.

        Returns None when the file does not exist or is invalid TOML.
        Prefer ``read_document`` for r-wrapped semantics.
        """
        if not path.exists():
            return None
        try:
            return tomlkit.parse(
                path.read_text(encoding=c.Infra.Encoding.DEFAULT),
            )
        except (OSError, ValueError) as exc:
            FlextInfraUtilitiesToml.logger.warning(
                "Failed to read or parse TOML document",
                path=str(path),
                error=exc,
                error_type=type(exc).__name__,
            )
            return None

    @staticmethod
    def read_document(path: Path) -> r[TOMLDocument]:
        """Read and parse a TOML document, returning r.

        Args:
            path: Path to the TOML file.

        Returns:
            r[TOMLDocument] with parsed document on success,
            or failure with descriptive error.

        """
        if not path.exists():
            return r[TOMLDocument].fail(f"failed to read TOML: {path}")
        doc = FlextInfraUtilitiesToml.read(path)
        if doc is None:
            return r[TOMLDocument].fail(f"TOML parse failed: {path}")
        return r[TOMLDocument].ok(doc)

    @staticmethod
    def _resolve_taplo_config(path: Path) -> Path | None:
        """Return the nearest ``.taplo.toml`` config for a managed pyproject."""
        resolved = path.resolve()
        for candidate in (resolved.parent, *resolved.parents):
            config_path = candidate / ".taplo.toml"
            if config_path.is_file():
                return config_path
        return None

    @staticmethod
    def _format_pyproject(path: Path) -> r[bool]:
        """Format generated ``pyproject.toml`` files with taplo."""
        if path.name != c.Infra.Files.PYPROJECT_FILENAME:
            return r[bool].ok(False)
        command: list[str] = ["taplo", "format"]
        config_path = FlextInfraUtilitiesToml._resolve_taplo_config(path)
        if config_path is not None:
            command.extend(["--config", str(config_path)])
        command.append(str(path))
        return FlextInfraUtilitiesSubprocess.run_checked(command, cwd=path.parent)

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
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(
                doc.as_string(),
                encoding=c.Infra.Encoding.DEFAULT,
            )
        except OSError as exc:
            return r[bool].fail(f"TOML write error: {exc}")
        format_result = FlextInfraUtilitiesToml._format_pyproject(path)
        if format_result.is_failure:
            return r[bool].fail(format_result.error or f"taplo format failed: {path}")
        return r[bool].ok(True)


__all__ = ["FlextInfraUtilitiesToml"]
