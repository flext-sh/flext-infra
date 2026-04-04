"""I/O helper functions for infrastructure file operations.

Centralizes JSON I/O operations with r-wrapped APIs for explicit error handling.
Merged from json_io.py and _utilities/io.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import operator
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ValidationError

from flext_core import u
from flext_infra import c, r, t


class FlextInfraUtilitiesIo:
    """I/O convenience helpers for JSON file operations.

    Provides r-wrapped APIs (read, write, parse, serialize) for explicit
    error handling. All methods are static and do not require instantiation.

    Usage via namespace::

        from flext_infra import u

        result = u.Cli.toml_read_json(path)
    """

    @staticmethod
    def read_json(path: Path) -> r[t.Cli.JsonMapping]:
        """Read and parse a JSON file.

        Args:
            path: Source file path.

        Returns:
            r with parsed JSON data. Returns empty mapping if file absent.

        """
        if not path.exists():
            return r[t.Cli.JsonMapping].ok({})
        try:
            raw_content = path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            loaded_obj: t.Cli.JsonValue = t.Cli.JSON_VALUE_ADAPTER.validate_json(
                raw_content
            )
        except (ValidationError, OSError) as exc:
            return r[t.Cli.JsonMapping].fail(f"JSON read error: {exc}")
        if not u.is_mapping(loaded_obj):
            return r[t.Cli.JsonMapping].fail(
                "JSON root must be t.NormalizedValue",
            )
        try:
            data = t.Cli.JSON_MAPPING_ADAPTER.validate_python(loaded_obj)
            return r[t.Cli.JsonMapping].ok(data)
        except ValidationError as exc:
            return r[t.Cli.JsonMapping].fail(
                f"JSON t.NormalizedValue validation error: {exc}",
            )

    @staticmethod
    def write_json(
        path: Path,
        payload: t.Cli.JsonValue
        | BaseModel
        | t.Cli.JsonMapping
        | t.Cli.JsonList
        | Mapping[str, t.Infra.InfraValue],
        *,
        sort_keys: bool = False,
        ensure_ascii: bool = False,
        indent: int = 2,
    ) -> r[bool]:
        """Write a JSON payload to a file.

        Creates parent directories as needed.

        Args:
            path: Destination file path.
            payload: Data to serialize as JSON (Pydantic JsonValue or BaseModel).
            sort_keys: If True, sort dictionary keys alphabetically.
            ensure_ascii: If True, escape non-ASCII characters.
            indent: JSON indentation level (default 2).

        Returns:
            r[bool] with True on success.

        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            materialized: t.Cli.JsonValue | Mapping[str, t.Infra.InfraValue]
            if isinstance(payload, BaseModel):
                materialized = payload.model_dump(mode="json")
            elif isinstance(payload, Mapping):
                materialized = dict(payload)
            elif isinstance(payload, Sequence) and not isinstance(payload, str):
                materialized = list(payload)
            else:
                materialized = payload
            validated_payload: t.Cli.JsonValue = (
                t.Cli.JSON_VALUE_ADAPTER.validate_python(materialized)
            )
            normalized_payload: t.Cli.JsonValue = (
                FlextInfraUtilitiesIo._sort_json_keys(validated_payload)
                if sort_keys
                else validated_payload
            )
            content = (
                t.Cli.JSON_VALUE_ADAPTER.dump_json(
                    normalized_payload,
                    indent=indent,
                    ensure_ascii=ensure_ascii,
                ).decode(c.Infra.Encoding.DEFAULT)
                + "\n"
            )
            _ = path.write_text(content, encoding=c.Infra.Encoding.DEFAULT)
        except (TypeError, ValueError, ValidationError, OSError) as exc:
            return r[bool].fail(f"JSON write error: {exc}")
        return r[bool].ok(True)

    @staticmethod
    def _sort_json_keys(data: t.Cli.JsonValue) -> t.Cli.JsonValue:
        if u.is_mapping(data):
            mapped_data = t.Cli.JSON_MAPPING_ADAPTER.validate_python(data)
            sorted_items: Sequence[t.Infra.Pair[str, t.Cli.JsonValue]] = sorted(
                mapped_data.items(),
                key=operator.itemgetter(0),
            )
            return {
                key: FlextInfraUtilitiesIo._sort_json_keys(value)
                for key, value in sorted_items
            }
        if isinstance(data, list):
            items = t.Cli.JSON_LIST_ADAPTER.validate_python(data)
            return [FlextInfraUtilitiesIo._sort_json_keys(item) for item in items]
        return data

    @staticmethod
    def atomic_write_file(target: Path, content: str) -> r[bool]:
        """Write content to target via atomic temp-file rename.

        Creates parent directories as needed.  Writes to a temporary file in
        the same directory, then atomically replaces the target.

        Args:
            target: Destination file path.
            content: Text content to write.

        Returns:
            r[bool] with True on success.

        """
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=str(target.parent),
                delete=False,
                encoding=c.Infra.Encoding.DEFAULT,
                suffix=".tmp",
            ) as tmp:
                _ = tmp.write(content)
                tmp_path = Path(tmp.name)
            _ = tmp_path.replace(target)
        except OSError as exc:
            return r[bool].fail(f"atomic write failed: {exc}")
        return r[bool].ok(True)

    @staticmethod
    def parse(text: str) -> r[t.Cli.JsonValue]:
        """Parse a JSON string.

        Args:
            text: Raw JSON string.

        Returns:
            r with parsed JSON value.

        """
        try:
            parsed: t.Cli.JsonValue = t.Cli.JSON_VALUE_ADAPTER.validate_json(
                text,
            )
            return r[t.Cli.JsonValue].ok(parsed)
        except (ValidationError, ValueError) as exc:
            return r[t.Cli.JsonValue].fail(f"JSON parse error: {exc}")

    @staticmethod
    def serialize(
        data: t.Infra.InfraValue,
        *,
        sort_keys: bool = False,
        ensure_ascii: bool = False,
        indent: int | None = 2,
    ) -> r[str]:
        """Serialize a Python t.NormalizedValue to a JSON string.

        Args:
            data: JSON-serializable container value.
            sort_keys: If True, sort dictionary keys alphabetically.
            ensure_ascii: If True, escape non-ASCII characters.
            indent: JSON indentation level (None for compact output).

        Returns:
            r with JSON string.

        """
        try:
            raw_data: t.Infra.InfraValue = (
                data.model_dump(mode="json") if isinstance(data, BaseModel) else data
            )
            validated_data: t.Cli.JsonValue = t.Cli.JSON_VALUE_ADAPTER.validate_python(
                raw_data
            )
            normalized_data: t.Cli.JsonValue = (
                FlextInfraUtilitiesIo._sort_json_keys(validated_data)
                if sort_keys
                else validated_data
            )
            serialized = t.Cli.JSON_VALUE_ADAPTER.dump_json(
                normalized_data,
                indent=indent,
                ensure_ascii=ensure_ascii,
            ).decode(c.Infra.Encoding.DEFAULT)
            return r[str].ok(serialized)
        except (TypeError, ValueError, ValidationError) as exc:
            return r[str].fail(f"JSON serialize error: {exc}")

    @staticmethod
    def sha256_content(content: str) -> str:
        """Compute SHA256 hex digest of string content."""
        return hashlib.sha256(content.encode(c.Infra.Encoding.DEFAULT)).hexdigest()

    @staticmethod
    def sha256_file(path: Path) -> str:
        """Compute SHA256 hex digest of a file on disk."""
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


__all__ = ["FlextInfraUtilitiesIo"]
