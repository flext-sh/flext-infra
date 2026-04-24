"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from flext_cli import u

from flext_infra import (
    FlextInfraModelsDepsToolSettings as mdts,
    c,
    p,
    r,
    t,
)


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    Generic ``validate`` and ``deep`` methods use PEP 695 type parameters
    so callers can validate ANY shape with a single SSOT helper.
    """

    _tool_config_cache: p.Result[mdts.ToolConfigDocument] | None = None

    @staticmethod
    def _load_tool_config_cached() -> p.Result[mdts.ToolConfigDocument]:
        """Load, validate, and cache ``tool_config.yml`` for dependency tooling."""
        cached = FlextInfraUtilitiesBase._tool_config_cache
        if cached is not None:
            return cached
        try:
            raw_text = (
                files("flext_infra.deps")
                .joinpath("tool_config.yml")
                .read_text(encoding=c.Cli.ENCODING_DEFAULT)
            )
            parsed = u.Cli.yaml_parse(raw_text)
            if parsed.failure:
                result = r[mdts.ToolConfigDocument].fail(
                    parsed.error or "tool_config.yml parse failed",
                )
                FlextInfraUtilitiesBase._tool_config_cache = result
                return result
            validated = mdts.ToolConfigDocument.model_validate(parsed.value)
            result = r[mdts.ToolConfigDocument].ok(validated)
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            c.ValidationError,
            ValueError,
        ) as exc:
            result = r[mdts.ToolConfigDocument].fail(
                f"failed to load tool_config.yml: {exc}",
            )
            FlextInfraUtilitiesBase._tool_config_cache = result
            return result

    @staticmethod
    def load_tool_config() -> p.Result[mdts.ToolConfigDocument]:
        """Return cached dependency tool configuration."""
        return FlextInfraUtilitiesBase._load_tool_config_cached()

    @staticmethod
    def resolve_workspace_root_or_cwd(workspace_root: Path | None = None) -> Path:
        """Resolve workspace root from explicit value or current working directory."""
        target = workspace_root or Path.cwd()
        if target.is_file():
            target = target.parent
        return target.resolve()

    @staticmethod
    def normalize_optional_path(value: str | Path | None) -> Path | None:
        """Resolve one optional path-like value when present."""
        if value is None:
            return None
        path = value if isinstance(value, Path) else Path(value)
        return path.resolve()

    @staticmethod
    def normalize_cli_values(*values: str | None) -> t.StrSequence:
        """Normalize comma-separated or whitespace-separated CLI selectors."""
        return tuple(
            item.strip()
            for value in values
            for group in (value or "").split(",")
            for item in group.split()
            if item.strip()
        )

    @staticmethod
    def normalize_sequence_values(values: t.StrSequence | None) -> t.StrSequence | None:
        """Normalize repeated CLI sequence fields into a compact selector list."""
        names = FlextInfraUtilitiesBase.normalize_cli_values(*(values or ()))
        return names or None

    @staticmethod
    def normalize_make_args(values: t.StrSequence) -> t.StrSequence:
        """Return trimmed make arguments without blank entries."""
        return tuple(item.strip() for item in values if item.strip())


__all__: list[str] = ["FlextInfraUtilitiesBase"]
