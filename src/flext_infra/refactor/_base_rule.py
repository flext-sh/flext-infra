"""Base rule class for flext_infra.refactor.

Provides the foundational rule interface for the refactoring engine.
Rules operate on source text and file paths, using rope for analysis.

This module has no dependencies on any rules/ submodule.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

from flext_infra import FlextInfraChangeTracker, c, t


class FlextInfraRefactorRule:
    """Base class for flext_infra refactor rules.

    Rules receive source text and return (transformed_source, changes).
    The engine handles file I/O and rope project lifecycle.
    """

    def __init__(self, config: Mapping[str, t.Infra.InfraValue]) -> None:
        """Initialize rule metadata from rule config."""
        self.config = dict(config)
        rule_id = self.config.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN)
        self.rule_id = str(rule_id)
        name_raw = self.config.get(c.Infra.NAME, self.rule_id)
        self.name = str(name_raw)
        description_raw = self.config.get("description", "")
        self.description = description_raw if isinstance(description_raw, str) else ""
        enabled_raw = self.config.get(c.Infra.ReportKeys.ENABLED, True)
        self.enabled = bool(enabled_raw)
        severity_raw = self.config.get("severity", c.Infra.Severity.WARNING)
        self.severity = str(severity_raw)

    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        """Apply the rule to source text and return (transformed_source, changes)."""
        return (source, list[str]())

    def _apply_text_transformer(
        self,
        transformer: FlextInfraChangeTracker,
        source: str,
    ) -> t.Infra.TransformResult:
        """Apply a text transformer with apply_to_source and return (source, changes)."""
        apply_fn = getattr(transformer, "apply_to_source", None)
        if apply_fn is not None:
            result = apply_fn(source)
            new_source: str = result[0] if isinstance(result, tuple) else result
            return (new_source, list(transformer.changes))
        return (source, list[str]())


class FlextInfraGenericTransformerRule(FlextInfraRefactorRule):
    """Base for rules that delegate to a single transformer class.

    Subclasses set ``TRANSFORMER_CLASS``. The ``apply()`` method
    instantiates the transformer and delegates to ``_apply_text_transformer``.
    """

    TRANSFORMER_CLASS: type[FlextInfraChangeTracker]
    """The transformer class to instantiate and apply."""

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        """Instantiate TRANSFORMER_CLASS and apply it."""
        transformer = self.TRANSFORMER_CLASS()
        return self._apply_text_transformer(transformer, source)


__all__ = [
    "FlextInfraGenericTransformerRule",
    "FlextInfraRefactorRule",
]
