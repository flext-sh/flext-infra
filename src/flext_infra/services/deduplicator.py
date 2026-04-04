"""Direct constant deduplication command service."""

from __future__ import annotations

from typing import Annotated, override

from pydantic import Field

from flext_core import r
from flext_infra import s, u


class FlextInfraCodegenDeduplicator(s[str]):
    """Deduplicate canonical constant definitions from a validated CLI model."""

    class_to_analyze: Annotated[
        str,
        Field(description="Canonical class path to deduplicate"),
    ]

    @override
    def execute(self) -> r[str]:
        """Run constant deduplication with normalized command context."""
        return u.Infra.deduplicate_constants(
            class_path=self.class_to_analyze,
            root_path=self.workspace_root,
            dry_run=self.dry_run or not self.apply_changes,
        ).map(lambda report: report.render_text())


__all__ = ["FlextInfraCodegenDeduplicator"]
