"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from importlib.resources import files
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from flext_cli import FlextCliUtilitiesYaml as _CliYaml
from flext_core import r, u
from flext_infra import (
    FlextInfraConstantsBase,
    FlextInfraModelsDepsToolConfig,
    FlextInfraModelsScan,
    FlextInfraProtocolsBase,
    FlextInfraTypes,
    FlextInfraTypesAdapters,
    FlextInfraTypesBase,
)


class FlextInfraUtilitiesBase(_CliYaml):
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    _tool_config_cache: r[FlextInfraModelsDepsToolConfig.ToolConfigDocument] | None = (
        None
    )

    # ------------------------------------------------------------------
    # Generic validation (SSOT for TypeAdapter-based coercion)
    # ------------------------------------------------------------------

    @staticmethod
    def validate[T](
        adapter: TypeAdapter[T],
        value: FlextInfraTypes.ValueOrModel,
        *,
        default: T,
    ) -> T:
        """Validate *value* with any ``TypeAdapter[T]``, returning *default* on failure.

        SSOT for all Pydantic-adapter validation in flext-infra.
        Replaces every try/except ValidationError pattern.

        Example::

            mapping = u.Infra.validate(
                FlextInfraTypesAdapters.INFRA_MAPPING_ADAPTER,
                raw,
                default={},
            )
            items = u.Infra.validate(
                FlextInfraTypesAdapters.INFRA_SEQ_ADAPTER,
                raw,
                default=[],
            )
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
        value: FlextInfraTypes.ValueOrModel | None,
    ) -> Mapping[str, FlextInfraTypesBase.InfraValue]:
        """Normalize a value to a string-keyed mapping, or ``{}`` on failure."""
        return FlextInfraUtilitiesBase.validate(
            FlextInfraTypesAdapters.INFRA_MAPPING_ADAPTER,
            value,
            default={},
        )

    @staticmethod
    def normalize_mapping_list(
        value: FlextInfraTypesBase.InfraValue | None,
    ) -> Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]]:
        """Normalize a value to a list of string-keyed mappings."""
        if value is None or not isinstance(value, list):
            return []
        items = FlextInfraUtilitiesBase.validate(
            FlextInfraTypesAdapters.INFRA_SEQ_ADAPTER,
            value,
            default=[],
        )
        result: list[Mapping[str, FlextInfraTypesBase.InfraValue]] = []
        for item in items:
            validated = FlextInfraUtilitiesBase.validate(
                FlextInfraTypesAdapters.INFRA_MAPPING_ADAPTER,
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
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        keys: tuple[str, ...],
    ) -> FlextInfraTypesBase.InfraValue | None:
        """Walk a key path through nested mappings, returning the leaf value."""
        current: Mapping[str, FlextInfraTypesBase.InfraValue] = data
        for key in keys[:-1]:
            raw = current.get(key)
            if raw is None:
                return None
            try:
                current = FlextInfraTypesAdapters.INFRA_MAPPING_ADAPTER.validate_python(
                    raw
                )
            except ValidationError:
                return None
        return current.get(keys[-1]) if keys else None

    @staticmethod
    def nested_int(
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        *keys: str,
        default: int = 0,
    ) -> int:
        """Extract a nested int by key path."""
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return u.to_int(raw, default=default) if raw is not None else default

    @staticmethod
    def deep_mapping(
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        *keys: str,
    ) -> Mapping[str, FlextInfraTypesBase.InfraValue]:
        """Navigate nested dicts by key path → normalized mapping.

        Replaces chains of ``normalize_str_mapping(x.get("key"))``.
        """
        if not keys:
            return FlextInfraUtilitiesBase.normalize_str_mapping(data)
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return FlextInfraUtilitiesBase.normalize_str_mapping(raw)

    @staticmethod
    def deep_list(
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        *keys: str,
    ) -> Sequence[Mapping[str, FlextInfraTypesBase.InfraValue]]:
        """Navigate nested dicts by key path → list of mappings."""
        raw = FlextInfraUtilitiesBase._walk_path(data, keys)
        return FlextInfraUtilitiesBase.normalize_mapping_list(raw)

    # ------------------------------------------------------------------
    # Generic scalar extraction (PEP 695)
    # ------------------------------------------------------------------

    @staticmethod
    def pick_str(
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        key: str,
        default: str = "",
    ) -> str:
        """Extract a string from mapping, coercing if needed."""
        raw = data.get(key, default)
        return str(raw).strip() if raw is not None else default

    @staticmethod
    def pick_int(
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        key: str,
        default: int = 0,
    ) -> int:
        """Extract an int from mapping, coercing if needed."""
        raw = data.get(key, default)
        if raw is None:
            return default
        if isinstance(raw, int):
            return raw
        if isinstance(raw, (str, float, bool)):
            return u.to_int(raw, default=default)
        return default

    @staticmethod
    def pick_bool(
        data: Mapping[str, FlextInfraTypesBase.InfraValue],
        key: str,
        *,
        default: bool = False,
    ) -> bool:
        """Extract a bool from mapping."""
        raw = data.get(key)
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            normalized = raw.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        if isinstance(raw, int | float):
            return raw != 0
        return default

    @staticmethod
    def get_str_key(
        mapping: Mapping[str, FlextInfraTypesBase.InfraValue],
        key: str,
        *,
        default: str = "",
        case: str | None = None,
    ) -> str:
        """Extract and normalize a string key with optional case conversion."""
        raw = FlextInfraUtilitiesBase.pick_str(mapping, key, default)
        return u.normalize(raw, case=case)

    @staticmethod
    def _load_tool_config_cached() -> r[
        FlextInfraModelsDepsToolConfig.ToolConfigDocument
    ]:
        """Load, validate, and cache ``tool_config.yml`` for dependency tooling."""
        cached = FlextInfraUtilitiesBase._tool_config_cache
        if cached is not None:
            return cached
        try:
            raw_text = (
                files("flext_infra.deps")
                .joinpath("tool_config.yml")
                .read_text(encoding=FlextInfraConstantsBase.Encoding.DEFAULT)
            )
            parsed = FlextInfraUtilitiesBase.yaml_parse(raw_text)
            if parsed.is_failure:
                result = r[FlextInfraModelsDepsToolConfig.ToolConfigDocument].fail(
                    parsed.error or "tool_config.yml parse failed",
                )
                FlextInfraUtilitiesBase._tool_config_cache = result
                return result
            validated = (
                FlextInfraModelsDepsToolConfig.ToolConfigDocument.model_validate(
                    parsed.value
                )
            )
            result = r[FlextInfraModelsDepsToolConfig.ToolConfigDocument].ok(validated)
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValidationError,
            ValueError,
        ) as exc:
            result = r[FlextInfraModelsDepsToolConfig.ToolConfigDocument].fail(
                f"failed to load tool_config.yml: {exc}",
            )
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result

    @staticmethod
    def load_tool_config() -> r[FlextInfraModelsDepsToolConfig.ToolConfigDocument]:
        """Return cached dependency tool configuration."""
        return FlextInfraUtilitiesBase._load_tool_config_cached()

    # ------------------------------------------------------------------
    # Scan result builder (PEP 695 inline type parameter)
    # ------------------------------------------------------------------

    @classmethod
    def build_scan_result[V: FlextInfraProtocolsBase.ViolationWithLine](
        cls,
        *,
        file_path: Path,
        detector_name: str,
        rule_id: str,
        violations: Sequence[V],
        message_builder: Callable[[V], str],
    ) -> FlextInfraModelsScan.ScanResult:
        """Build a standardized scan result from typed violations."""
        return FlextInfraModelsScan.ScanResult(
            file_path=file_path,
            violations=[
                FlextInfraModelsScan.ScanViolation(
                    line=FlextInfraUtilitiesBase.pick_int(
                        violation.model_dump(), "line"
                    ),
                    message=message_builder(violation),
                    severity="error",
                    rule_id=rule_id,
                )
                for violation in violations
            ],
            detector_name=detector_name,
        )
