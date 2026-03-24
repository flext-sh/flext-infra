"""I/O helper functions for infrastructure file operations.

Centralizes JSON I/O operations with r-wrapped APIs for explicit error handling.
Merged from json_io.py and _utilities/io.py.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar

from flext_core import r
from pydantic import BaseModel, JsonValue, TypeAdapter, ValidationError

from flext_infra import c, t


class FlextInfraUtilitiesIo:
    """I/O convenience helpers for JSON file operations.

    Provides r-wrapped APIs (read, write, parse, serialize) for explicit
    error handling. All methods are static and do not require instantiation.

    Usage via namespace::

        from flext_infra import u

        result = u.Infra.read_json(path)
    """

    _json_value_adapter: ClassVar[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)
    _json_dict_adapter: ClassVar[TypeAdapter[Mapping[str, JsonValue]]] = TypeAdapter(
        Mapping[str, JsonValue],
    )
    _json_list_adapter: ClassVar[TypeAdapter[Sequence[JsonValue]]] = TypeAdapter(
        Sequence[JsonValue],
    )

    @staticmethod
    def read_json(path: Path) -> r[Mapping[str, JsonValue]]:
        """Read and parse a JSON file.

        Args:
            path: Source file path.

        Returns:
            r with parsed JSON data. Returns empty mapping if file absent.

        """
        if not path.exists():
            return r[Mapping[str, JsonValue]].ok({})
        try:
            raw_content = path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            loaded_obj: JsonValue = (
                FlextInfraUtilitiesIo._json_value_adapter.validate_json(raw_content)
            )
        except (ValidationError, OSError) as exc:
            return r[Mapping[str, JsonValue]].fail(f"JSON read error: {exc}")
        if not isinstance(loaded_obj, dict):
            return r[Mapping[str, JsonValue]].fail(
                "JSON root must be t.NormalizedValue",
            )
        try:
            data = FlextInfraUtilitiesIo._json_dict_adapter.validate_python(loaded_obj)
            return r[Mapping[str, JsonValue]].ok(data)
        except ValidationError as exc:
            return r[Mapping[str, JsonValue]].fail(
                f"JSON t.NormalizedValue validation error: {exc}",
            )

    @staticmethod
    def write_json(
        path: Path,
        payload: JsonValue
        | BaseModel
        | Mapping[str, JsonValue]
        | Sequence[JsonValue]
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
            if isinstance(payload, BaseModel):
                materialized = payload.model_dump()
            elif isinstance(payload, Mapping):
                materialized = dict(payload)
            elif isinstance(payload, Sequence) and not isinstance(payload, str):
                materialized = list(payload)
            else:
                materialized = payload
            validated_payload: JsonValue = (
                FlextInfraUtilitiesIo._json_value_adapter.validate_python(materialized)
            )
            normalized_payload: JsonValue = (
                FlextInfraUtilitiesIo._sort_json_keys(validated_payload)
                if sort_keys
                else validated_payload
            )
            content = (
                FlextInfraUtilitiesIo._json_value_adapter.dump_json(
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
    def _sort_json_keys(data: JsonValue) -> JsonValue:
        if isinstance(data, dict):
            mapped_data = FlextInfraUtilitiesIo._json_dict_adapter.validate_python(data)
            sorted_items: Sequence[tuple[str, JsonValue]] = sorted(
                mapped_data.items(),
                key=operator.itemgetter(0),
            )
            return {
                key: FlextInfraUtilitiesIo._sort_json_keys(value)
                for key, value in sorted_items
            }
        if isinstance(data, list):
            items = FlextInfraUtilitiesIo._json_list_adapter.validate_python(data)
            return [FlextInfraUtilitiesIo._sort_json_keys(item) for item in items]
        return data

    @staticmethod
    def parse(text: str) -> r[JsonValue]:
        """Parse a JSON string.

        Args:
            text: Raw JSON string.

        Returns:
            r with parsed JSON value.

        """
        try:
            parsed: JsonValue = FlextInfraUtilitiesIo._json_value_adapter.validate_json(
                text
            )
            return r[JsonValue].ok(parsed)
        except (ValidationError, ValueError) as exc:
            return r[JsonValue].fail(f"JSON parse error: {exc}")

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
                data.model_dump() if isinstance(data, BaseModel) else data
            )
            validated_data: JsonValue = (
                FlextInfraUtilitiesIo._json_value_adapter.validate_python(raw_data)
            )
            normalized_data: JsonValue = (
                FlextInfraUtilitiesIo._sort_json_keys(validated_data)
                if sort_keys
                else validated_data
            )
            serialized = FlextInfraUtilitiesIo._json_value_adapter.dump_json(
                normalized_data,
                indent=indent,
                ensure_ascii=ensure_ascii,
            ).decode(c.Infra.Encoding.DEFAULT)
            return r[str].ok(serialized)
        except (TypeError, ValueError, ValidationError) as exc:
            return r[str].fail(f"JSON serialize error: {exc}")


__all__ = ["FlextInfraUtilitiesIo"]
