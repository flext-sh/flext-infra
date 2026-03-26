"""Base rule class for flext_infra.refactor.

Extracted to break circular import chain:
rule.py -> class_nesting.py -> class_reconstructor.py -> rule.py

This module has no dependencies on any rules/ submodule.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import Protocol, override, runtime_checkable

import libcst as cst
from pydantic import TypeAdapter

from flext_infra import c, t

# ── Shared TypeAdapter constants ──────────────────────────────────────
# Defined once here; imported by rules/ modules that need them.

INFRA_MAPPING_ADAPTER: TypeAdapter[Mapping[str, t.Infra.InfraValue]] = TypeAdapter(
    Mapping[str, t.Infra.InfraValue],
)
CONTAINER_DICT_SEQ_ADAPTER: TypeAdapter[Sequence[t.Infra.ContainerDict]] = TypeAdapter(
    Sequence[t.Infra.ContainerDict],
)
STR_MAPPING_ADAPTER: TypeAdapter[Mapping[str, str]] = TypeAdapter(Mapping[str, str])
INFRA_SEQ_ADAPTER: TypeAdapter[Sequence[t.Infra.InfraValue]] = TypeAdapter(
    Sequence[t.Infra.InfraValue],
)


@runtime_checkable
class FlextInfraChangeTracker(Protocol):
    """Protocol for objects that track applied changes."""

    changes: MutableSequence[str]


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
        changes: Sequence[str] = (
            transformer.changes
            if isinstance(transformer, FlextInfraChangeTracker)
            else []
        )
        return (new_tree, changes)


class FlextInfraGenericTransformerRule(FlextInfraRefactorRule):
    """Base for rules that simply delegate to a single transformer class.

    Subclasses set ``TRANSFORMER_CLASS`` and optionally ``CONFIG_KEY``.
    The ``apply()`` method instantiates the transformer (no args) and
    delegates to ``_apply_transformer``.
    """

    TRANSFORMER_CLASS: type[cst.CSTTransformer]
    """The transformer class to instantiate and apply."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Instantiate TRANSFORMER_CLASS and apply it."""
        return self._apply_transformer(self.TRANSFORMER_CLASS(), tree)


__all__ = [
    "CONTAINER_DICT_SEQ_ADAPTER",
    "INFRA_MAPPING_ADAPTER",
    "INFRA_SEQ_ADAPTER",
    "STR_MAPPING_ADAPTER",
    "FlextInfraChangeTracker",
    "FlextInfraGenericTransformerRule",
    "FlextInfraRefactorRule",
]
