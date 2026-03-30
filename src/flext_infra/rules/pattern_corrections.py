"""Pattern correction rules for high-volume violations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import INFRA_MAPPING_ADAPTER, FlextInfraRefactorRule, c, t, u
from flext_infra.transformers.dict_to_mapping import FlextInfraDictToMappingTransformer
from flext_infra.transformers.redundant_cast_remover import (
    FlextInfraRedundantCastRemover,
)


class FlextInfraRefactorPatternCorrectionsRule(FlextInfraRefactorRule):
    """Apply corrective refactors for high-volume pattern violations."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        fix_action = (
            str(self.config.get(c.Infra.ReportKeys.FIX_ACTION, "")).strip().lower()
        )
        if fix_action == "convert_dict_to_mapping_annotations":
            include_returns = bool(self.config.get("include_return_annotations", False))
            return self._apply_transformer(
                FlextInfraDictToMappingTransformer(
                    include_return_annotations=include_returns,
                ),
                tree,
            )
        if fix_action == "remove_redundant_casts":
            typed_cfg: Mapping[str, t.Infra.InfraValue] = (
                INFRA_MAPPING_ADAPTER.validate_python(self.config)
            )
            raw_types = typed_cfg.get("redundant_type_targets", [])
            removable_types = set(u.Infra.string_list(raw_types))
            return self._apply_transformer(
                FlextInfraRedundantCastRemover(removable_types=removable_types),
                tree,
            )
        return (tree, [])


__all__ = ["FlextInfraRefactorPatternCorrectionsRule"]
