"""Detect silent failure sentinels via Rope-backed source scanning."""

from __future__ import annotations

from collections.abc import (
    Sequence,
)

from flext_infra import m, u


class FlextInfraSilentFailureDetector:
    """Detect branches that hide failures behind generic sentinel returns."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.Issue]:
        """Detect silent-failure findings in one Python file."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return []
        file_path = ctx.file_path
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


__all__: list[str] = ["FlextInfraSilentFailureDetector"]
