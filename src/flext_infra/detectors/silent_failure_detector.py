"""Detect silent failure sentinels via Rope-backed source scanning."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import FlextInfraScanFileMixin, c, m, p, u


class FlextInfraSilentFailureDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect branches that hide failures behind generic sentinel returns."""

    _rule_id: ClassVar[str] = "silent_failure"
    _MESSAGE_TEMPLATE: ClassVar[str] = "{message}"

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.Issue]:
        file_path = ctx.file_path
        if file_path.suffix != c.Infra.Extensions.PYTHON:
            return []
        source = cls._get_source_or_empty(ctx.rope_project, file_path)
        if source is None or not source.strip():
            return []
        display_path = file_path
        if ctx.project_root is not None:
            try:
                display_path = file_path.relative_to(ctx.project_root)
            except ValueError:
                display_path = file_path
        return [
            m.Infra.Issue(
                file=str(display_path),
                line=line,
                column=column,
                code=code,
                message=message,
            )
            for line, column, code, message, _change in (
                u.Infra.collect_silent_failure_findings(source)
            )
        ]

    @override
    def _build_message(self, violation: BaseModel) -> str:
        if isinstance(violation, m.Infra.Issue):
            return violation.message
        return super()._build_message(violation)


__all__ = ["FlextInfraSilentFailureDetector"]
