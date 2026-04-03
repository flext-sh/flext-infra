"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TypeVar

from pydantic import JsonValue, ValidationError

from flext_core import u
from flext_infra import m, p, t

_V = TypeVar("_V", bound=p.Infra.ViolationWithLine)


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    """

    @staticmethod
    def get_str_key(
        mapping: Mapping[str, t.Infra.InfraValue],
        key: str,
        *,
        default: str = "",
        lower: bool = False,
    ) -> str:
        """Extract and normalize a string key from a config mapping.

        Replaces the repeated ``str(mapping.get(key, "")).strip().lower()`` pattern.

        Args:
            mapping: Source mapping (e.g., rule config dict).
            key: Key to extract.
            default: Default value if key is missing.
            lower: If True, also lowercase the result.

        Returns:
            Stripped (and optionally lowercased) string value.

        """
        raw = str(mapping.get(key, default)).strip()
        return raw.lower() if lower else raw

    @staticmethod
    def _coerce_violation_line(value: JsonValue | None) -> int:
        """Convert a JSON scalar into a scan-result line number."""
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    @classmethod
    def build_scan_result(
        cls,
        *,
        file_path: Path,
        detector_name: str,
        rule_id: str,
        violations: Sequence[_V],
        message_builder: Callable[[_V], str],
    ) -> m.Infra.ScanResult:
        """Build a standardized scan result from typed violations."""
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=cls._coerce_violation_line(
                        violation.model_dump().get("line"),
                    ),
                    message=message_builder(violation),
                    severity="error",
                    rule_id=rule_id,
                )
                for violation in violations
            ],
            detector_name=detector_name,
        )

    @staticmethod
    def normalize_str_mapping(
        value: t.Infra.InfraValue | Mapping[str, t.Infra.InfraValue] | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Normalize a value to a string-keyed mapping, or empty dict on failure."""
        try:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        except ValidationError:
            return {}

    @staticmethod
    def normalize_mapping_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Normalize a value to a list of string-keyed mappings."""
        if value is None or not isinstance(value, list):
            return []
        typed_items: Sequence[t.Infra.InfraValue] = (
            t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
        )
        normalized: list[Mapping[str, t.Infra.InfraValue]] = []
        for raw_item in typed_items:
            try:
                normalized.append(
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw_item),
                )
            except ValidationError:
                continue
        return normalized

    @staticmethod
    def normalize_string_list(value: t.Infra.InfraValue) -> t.StrSequence:
        """Normalize a value to a list of strings."""
        try:
            return t.Infra.STR_SEQ_SIMPLE_ADAPTER.validate_python(value)
        except ValidationError:
            if not isinstance(value, list):
                return []
            raw_items: Sequence[JsonValue] = t.Infra.JSON_SEQ_ADAPTER.validate_python(
                value,
            )
            return [str(item) for item in raw_items]

    @staticmethod
    def as_str(value: t.Infra.InfraValue, default: str = "") -> str:
        """Coerce a value to str with fallback."""
        return value if isinstance(value, str) else default

    @staticmethod
    def nested_int(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        """Extract a nested int from a mapping by key path."""
        current: t.Infra.ContainerDict = {str(k): data[k] for k in data}
        for key in keys[:-1]:
            nested = u.Infra.as_toml_mapping(current.get(key))
            if nested is None:
                return default
            current = nested
        raw: t.Infra.InfraValue = current.get(keys[-1])
        if raw is None:
            return default
        return u.to_int(raw, default=default)
