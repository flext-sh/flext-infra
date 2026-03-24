"""Base rule class for flext_infra.refactor.

Extracted to break circular import chain:
rule.py -> class_nesting.py -> class_reconstructor.py -> rule.py

This module has no dependencies on any rules/ submodule.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import libcst as cst

from flext_infra import c, t


class FlextInfraRefactorRule:
    """Base class for flext_infra refactor rules."""

    def __init__(self, config: Mapping[str, t.Infra.InfraValue]) -> None:
        """Initialize rule metadata from rule config."""
        self.config = dict(config.items())
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
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Apply the rule to a CST module and return transformed tree plus changes."""
        return (tree, [])

    def _apply_transformer(
        self,
        transformer: cst.CSTTransformer,
        tree: cst.Module,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Apply a single transformer and return (tree, changes)."""
        new_tree = tree.visit(transformer)
        changes: t.StrSequence = getattr(transformer, "changes", [])
        return (new_tree, changes)


__all__ = ["FlextInfraRefactorRule"]
