"""Runtime contracts for in-process refactor postchecks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, t
from flext_infra.refactor.file_executor import FlextInfraClassNestingPostCheckGate
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsRefactorFileExecutor:
    """Validate the exact transformed artifact before it is written."""

    def test_postcheck_rejects_invalid_transformed_source(
        self, tmp_path: Path
    ) -> None:
        """Compile the pending source instead of the old file on disk."""
        file_path = tmp_path / "sample.py"
        file_path.write_text("value = 1\n", encoding=c.Cli.ENCODING_DEFAULT)
        result = m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=True,
            changes=(),
            refactored_code="def invalid(:\n",
        )
        expected = t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
            c.Infra.RK_POST_CHECKS: (),
            c.Infra.RK_QUALITY_GATES: (c.Infra.RK_LSP_DIAGNOSTICS_CLEAN,),
        })

        accepted, errors = FlextInfraClassNestingPostCheckGate().validate(
            result, expected
        )

        tm.that(accepted, eq=False)
        tm.that(len(errors), eq=1)


__all__: list[str] = []
