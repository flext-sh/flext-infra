"""YAML loading and config normalization helpers for infrastructure.

Centralizes YAML-related helpers previously defined as module-level
functions in ``flext_infra.validate.skill_validator``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

from flext_core import r
from pydantic import TypeAdapter, ValidationError
from yaml import YAMLError, safe_load

from flext_infra import c, m, t


class FlextInfraUtilitiesYaml:
    """YAML loading and validation helpers.

    Usage via namespace::

        from flext_infra import u

        data = u.Infra.safe_load_yaml(path)
    """

    _MAPPING_ADAPTER: TypeAdapter[dict[str, t.Infra.InfraValue]] | None = None

    @staticmethod
    def _get_mapping_adapter() -> TypeAdapter[dict[str, t.Infra.InfraValue]]:
        if FlextInfraUtilitiesYaml._MAPPING_ADAPTER is None:
            FlextInfraUtilitiesYaml._MAPPING_ADAPTER = TypeAdapter(
                dict[str, t.Infra.InfraValue],
            )
        return FlextInfraUtilitiesYaml._MAPPING_ADAPTER

    @staticmethod
    def safe_load_yaml(path: Path) -> Mapping[str, t.Infra.InfraValue]:
        """Load YAML file safely, returning empty mapping on missing/invalid.

        Args:
            path: Path to the YAML file to load.

        Returns:
            Parsed YAML data as a mapping, or empty dict on missing/invalid.

        Raises:
            TypeError: If the parsed content is not a mapping.

        """
        raw = path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        parsed: t.Infra.InfraValue | None = safe_load(raw)
        if parsed is None:
            return {}
        if not isinstance(parsed, Mapping):
            msg = f"rules.yml must be a mapping: {path}"
            raise TypeError(msg)
        try:
            return FlextInfraUtilitiesYaml._get_mapping_adapter().validate_python(
                parsed,
            )
        except ValidationError as exc:
            msg = f"rules.yml must be a mapping: {path}: {exc}"
            raise TypeError(msg) from exc

    _tool_config_cache: r[m.Infra.ToolConfigDocument] | None = None

    @staticmethod
    def _load_tool_config_cached() -> r[m.Infra.ToolConfigDocument]:
        """Load, validate, and cache tool_config.yml."""
        if FlextInfraUtilitiesYaml._tool_config_cache is not None:
            return FlextInfraUtilitiesYaml._tool_config_cache
        try:
            raw_text = (
                files("flext_infra.deps")
                .joinpath("tool_config.yml")
                .read_text(
                    encoding=c.Infra.Encoding.DEFAULT,
                )
            )
            parsed_raw: t.Infra.TomlValue | None = safe_load(raw_text)
            if not isinstance(parsed_raw, Mapping):
                result = r[m.Infra.ToolConfigDocument].fail(
                    "tool_config.yml must contain a top-level mapping",
                )
                FlextInfraUtilitiesYaml._tool_config_cache = result
                return result
            payload: t.Infra.TomlConfig = dict(parsed_raw.items())
            validated = m.Infra.ToolConfigDocument.model_validate(payload)
            result = r[m.Infra.ToolConfigDocument].ok(validated)
            FlextInfraUtilitiesYaml._tool_config_cache = result
            return result
        except (
            FileNotFoundError,
            OSError,
            YAMLError,
            ValidationError,
            TypeError,
        ) as exc:
            result = r[m.Infra.ToolConfigDocument].fail(
                f"failed to load tool_config.yml: {exc}",
            )
            FlextInfraUtilitiesYaml._tool_config_cache = result
            return result

    @staticmethod
    def load_tool_config() -> r[m.Infra.ToolConfigDocument]:
        """Public cached accessor for tool_config.yml."""
        return FlextInfraUtilitiesYaml._load_tool_config_cached()


__all__ = ["FlextInfraUtilitiesYaml"]
