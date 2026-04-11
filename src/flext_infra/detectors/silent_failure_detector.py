"""Detect silent failure sentinels via Rope-backed source scanning."""

from __future__ import annotations

from collections.abc import Sequence

from flext_infra import c, m, u


class FlextInfraSilentFailureDetector:
    """Detect branches that hide failures behind generic sentinel returns."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.Issue]:
        """Detect silent-failure findings in one Python file."""
        file_path = ctx.file_path
        if file_path.suffix != c.Infra.EXT_PYTHON:
            return []
        resource = u.Infra.get_resource_from_path(ctx.rope_project, file_path)
        if resource is None:
            return []
        source = resource.read()
        if not source.strip():
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


__all__ = ["FlextInfraSilentFailureDetector"]
