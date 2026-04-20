"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib.resources import files

from flext_cli import u

from flext_infra import (
    c,
    m,
    p,
    r,
)


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    _tool_config_cache: p.Result[m.Infra.ToolConfigDocument] | None = None

    @staticmethod
    def _load_tool_config_cached() -> p.Result[m.Infra.ToolConfigDocument]:
        """Load, validate, and cache ``tool_config.yml`` for dependency tooling."""
        cached = FlextInfraUtilitiesBase._tool_config_cache
        if cached is not None:
            return cached
        try:
            raw_text = (
                files("flext_infra.deps")
                .joinpath("tool_config.yml")
                .read_text(encoding=c.Infra.ENCODING_DEFAULT)
            )
            parsed = u.Cli.yaml_parse(raw_text)
            if parsed.failure:
                result = r[m.Infra.ToolConfigDocument].fail(
                    parsed.error or "tool_config.yml parse failed",
                )
                FlextInfraUtilitiesBase._tool_config_cache = result
                return result
            validated = m.Infra.ToolConfigDocument.model_validate(parsed.value)
            result = r[m.Infra.ToolConfigDocument].ok(validated)
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            c.ValidationError,
            ValueError,
        ) as exc:
            result = r[m.Infra.ToolConfigDocument].fail(
                f"failed to load tool_config.yml: {exc}",
            )
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result

    @staticmethod
    def load_tool_config() -> p.Result[m.Infra.ToolConfigDocument]:
        """Return cached dependency tool configuration."""
        return FlextInfraUtilitiesBase._load_tool_config_cached()


__all__: list[str] = ["FlextInfraUtilitiesBase"]
