"""Post-apply structural validation for refactor census fixes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


class FlextInfraRefactorCensusApplyFormattingMixin:
    """Mixin for validating files touched by census apply operations."""

    @staticmethod
    def _validate_touched_files(paths: Iterable[Path]) -> None:
        """Require every touched Python source to compile in-process."""
        for path in sorted({path.resolve() for path in paths if path.is_file()}):
            source = path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            compile(source, str(path), "exec")


__all__: list[str] = ["FlextInfraRefactorCensusApplyFormattingMixin"]
