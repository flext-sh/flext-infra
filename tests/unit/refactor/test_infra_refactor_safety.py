"""Runtime tests for fail-fast refactor semantic validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.refactor import FlextInfraRefactorSafetyManager
from flext_tests import tm
from tests import c

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorSafety:
    """Exercise the public safety facade against the real language server."""

    def test_semantic_validation_accepts_clean_python(
        self, infra_test_workspace: Path
    ) -> None:
        source = infra_test_workspace / "clean.py"
        source.write_text(
            '"""Clean LSP fixture."""\n\nvalue: int = 1\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )

        result = FlextInfraRefactorSafetyManager.run_semantic_validation(
            infra_test_workspace, (source,)
        )

        tm.ok(result)


__all__: tuple[str, ...] = ()
