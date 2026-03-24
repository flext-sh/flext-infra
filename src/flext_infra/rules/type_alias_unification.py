"""Rule implementation for TypeAlias and inline-union unification."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import FlextInfraRefactorRule, FlextInfraRefactorTypingUnifier, c, t


class FlextInfraRefactorTypingUnificationRule(FlextInfraRefactorRule):
    """Unify duplicate type alias definitions into canonical t.* contracts."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        return self._apply_transformer(
            FlextInfraRefactorTypingUnifier(
                canonical_map=c.Infra.TYPING_INLINE_UNION_CANONICAL_MAP,
                file_path=_file_path,
            ),
            tree,
        )


__all__ = ["FlextInfraRefactorTypingUnificationRule"]
