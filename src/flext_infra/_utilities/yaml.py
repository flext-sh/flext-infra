"""Infra-specific YAML helpers (tool_config.yml caching).

Generic YAML operations live in ``flext_cli._utilities.yaml`` and are
accessible via ``u.Cli.yaml_*``.  This module only contains the
infra-specific ``load_tool_config`` cached accessor.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from pydantic import ValidationError

from flext_cli import FlextCliUtilitiesYaml as _CliYaml
from flext_core import r
from flext_infra import c, m, t


class FlextInfraUtilitiesYaml(_CliYaml):
    """Infra-specific YAML helpers — typed wrappers + tool_config.yml caching."""

    @staticmethod
    def yaml_load_infra_mapping(path: Path) -> t.Infra.ContainerDict:
        """Load YAML → ``Mapping[str, InfraValue]`` (infra-typed).

        Delegates to ``u.Cli.yaml_load_mapping`` and normalizes the result
        to the infra type system via ``normalize_str_mapping``.
        """
        raw = FlextInfraUtilitiesYaml.yaml_load_mapping(path)
        try:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
        except ValidationError:
            return {}

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
                .read_text(encoding=c.Infra.Encoding.DEFAULT)
            )
            parsed = FlextInfraUtilitiesYaml.yaml_parse(raw_text)
            if parsed.is_failure:
                result = r[m.Infra.ToolConfigDocument].fail(
                    parsed.error or "tool_config.yml parse failed",
                )
                FlextInfraUtilitiesYaml._tool_config_cache = result
                return result
            validated = m.Infra.ToolConfigDocument.model_validate(parsed.value)
            result = r[m.Infra.ToolConfigDocument].ok(validated)
            FlextInfraUtilitiesYaml._tool_config_cache = result
            return result
        except (
            FileNotFoundError,
            OSError,
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
