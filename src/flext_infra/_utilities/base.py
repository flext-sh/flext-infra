"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from flext_core import u
from flext_infra import m, p, t


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    # ------------------------------------------------------------------
    # Generic validation (SSOT for TypeAdapter-based coercion)
    # ------------------------------------------------------------------

    @staticmethod
    def validate[T](
        adapter: TypeAdapter[T],
        value: object,
        *,
        default: T,
    ) -> T:
        """Validate *value* with any ``TypeAdapter[T]``, returning *default* on failure.

        SSOT for all Pydantic-adapter validation in flext-infra.
        Replaces every try/except ValidationError pattern.

        Example::

            mapping = u.Infra.validate(t.Infra.INFRA_MAPPING_ADAPTER, raw, default={})
            items = u.Infra.validate(t.Infra.INFRA_SEQ_ADAPTER, raw, default=[])
        """
        try:
            return adapter.validate_python(value)
        except (ValidationError, TypeError):
            return default

    # ------------------------------------------------------------------
    # Mapping / list normalization (thin wrappers over validate)
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_str_mapping(
        value: t.Infra.InfraValue | Mapping[str, t.Infra.InfraValue] | None,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Normalize a value to a string-keyed mapping, or ``{}`` on failure."""
        return FlextInfraUtilitiesBase.validate(
            t.Infra.INFRA_MAPPING_ADAPTER,
            value,
            default={},
        )

    @staticmethod
    def normalize_mapping_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Normalize a value to a list of string-keyed mappings."""
        if value is None or not isinstance(value, list):
            return []
        items = FlextInfraUtilitiesBase.validate(
            t.Infra.INFRA_SEQ_ADAPTER,
            value,
            default=[],
        )
        result: list[Mapping[str, t.Infra.InfraValue]] = []
        for item in items:
            validated = FlextInfraUtilitiesBase.validate(
                t.Infra.INFRA_MAPPING_ADAPTER,
                item,
                default={},
            )
            if validated:
                result.append(validated)
        return result

    # ------------------------------------------------------------------
    # Deep path navigation (generic key-path traversal)
    # ------------------------------------------------------------------

    @staticmethod
    def _walk_path(
        data: Mapping[str, t.Infra.InfraValue],
        keys: tuple[str, ...],
    ) -> t.Infra.InfraValue | None:
        """Walk a key path through nested mappings, returning the leaf value."""
        current: Mapping[str, t.Infra.InfraValue] = data
        for key in keys[:-1]:
            raw = current.get(key)
            if raw is None:
                return None
            try:
                current = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
            except ValidationError:
                return None
        return current.get(keys[-1]) if keys else None

    @staticmethod
    def nested_int(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        """Extract a nested int by key path."""
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return u.to_int(raw, default=default) if raw is not None else default

    @staticmethod
    def deep_mapping(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
    ) -> Mapping[str, t.Infra.InfraValue]:
        """Navigate nested dicts by key path → normalized mapping.

        Replaces chains of ``normalize_str_mapping(x.get("key"))``.
        """
        if not keys:
            return FlextInfraUtilitiesBase.normalize_str_mapping(data)
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return FlextInfraUtilitiesBase.normalize_str_mapping(raw)

    @staticmethod
    def deep_list(
        data: Mapping[str, t.Infra.InfraValue],
        *keys: str,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Navigate nested dicts by key path → list of mappings."""
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return FlextInfraUtilitiesBase.normalize_mapping_list(raw)

    # ------------------------------------------------------------------
    # Generic scalar extraction (PEP 695)
    # ------------------------------------------------------------------

    @staticmethod
    def pick[T: (str, int, float, bool)](
        data: Mapping[str, object],
        key: str,
        default: T,
    ) -> T:
        """Extract a typed scalar from a mapping, coercing to match *default*'s type.

        ONE method replaces ``str(x.get(k, ""))``, ``u.to_int(x.get(k))``,
        ``bool(x.get(k, False))``, and ``get_str_key(x, k)``.

        Example::

            name = u.Infra.pick(diag, "file", "?")  # str
            line = u.Infra.pick(diag, "line", 0)  # int
            ok = u.Infra.pick(diag, "passed", False)  # bool
        """
        raw = data.get(key, default)
        if raw is None:
            return default
        if isinstance(default, bool):
            return bool(raw)  # type: ignore[return-value]
        if isinstance(default, int) and not isinstance(default, bool):
            return u.to_int(raw, default=default)  # type: ignore[return-value]
        if isinstance(default, float):
            return u.to_float(raw, default=default)  # type: ignore[return-value]
        # str fallback
        return str(raw).strip() if raw is not None else str(default)  # type: ignore[return-value]

    @staticmethod
    def get_str_key(
        mapping: Mapping[str, t.Infra.InfraValue],
        key: str,
        *,
        default: str = "",
        lower: bool = False,
    ) -> str:
        """Extract and normalize a string key (with optional lowercasing)."""
        raw = FlextInfraUtilitiesBase.pick(mapping, key, default)
        return raw.lower() if lower else raw

    # ------------------------------------------------------------------
    # Scan result builder (PEP 695 inline type parameter)
    # ------------------------------------------------------------------

    @classmethod
    def build_scan_result[V: p.Infra.ViolationWithLine](
        cls,
        *,
        file_path: Path,
        detector_name: str,
        rule_id: str,
        violations: Sequence[V],
        message_builder: Callable[[V], str],
    ) -> m.Infra.ScanResult:
        """Build a standardized scan result from typed violations."""
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=u.Infra.nested_int(violation.model_dump(), "line"),
                    message=message_builder(violation),
                    severity="error",
                    rule_id=rule_id,
                )
                for violation in violations
            ],
            detector_name=detector_name,
        )
