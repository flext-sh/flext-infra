"""Focused contract tests for the codegen pipeline toolchain stage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_cli import cli
from flext_core import r
from flext_tests import tm

from flext_infra import c, m, p, t
from flext_infra.codegen._pipeline_stages import (  # noqa: PLC2701
    FlextInfraCodegenPipelineStagesMixin,
)
from flext_infra.codegen.conform import FlextInfraCodegenConform

if TYPE_CHECKING:
    from collections.abc import Callable


class _ToolchainStageHarness(FlextInfraCodegenPipelineStagesMixin):
    def _run_stage[V](
        self, stage_id: str, action: Callable[[], V], emit: Callable[[V], t.JsonMapping]
    ) -> p.Result[m.Cli.PipelineStageResult]:
        return r[m.Cli.PipelineStageResult].create_from_callable(
            lambda: cli.stage_result(stage_id, output=emit(action())),
            error_code=stage_id,
        )


@pytest.mark.parametrize(
    ("dry_run", "expected_mode"),
    [
        (True, c.Infra.CodegenConformMode.CHECK),
        (False, c.Infra.CodegenConformMode.APPLY),
    ],
)
def test_toolchain_stage_builds_full_workspace_conform_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    dry_run: bool,
    expected_mode: c.Infra.CodegenConformMode,
) -> None:
    captured: list[m.Infra.CodegenConformRequest] = []

    def execute_request(
        request: m.Infra.CodegenConformRequest,
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> r[m.Infra.CodegenResult]:
        del initial_workspace
        captured.append(request)
        plan = m.Infra.CodegenPlan.model_construct(
            request=request, repositories=(), files=()
        )
        return r[m.Infra.CodegenResult].ok(m.Infra.CodegenResult(plan=plan))

    monkeypatch.setattr(
        FlextInfraCodegenConform, "execute_request", staticmethod(execute_request)
    )
    pipeline = _ToolchainStageHarness()
    context = cli.stage_context(
        tmp_path, settings={c.Infra.PIPELINE_KEY_DRY_RUN: dry_run}
    )

    result = pipeline._stage_toolchain(context)  # noqa: SLF001

    tm.ok(result)
    tm.that(
        captured,
        eq=[
            m.Infra.CodegenConformRequest(
                root=tmp_path,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.ALL,
                mode=expected_mode,
            )
        ],
    )
    tm.that(result.value.output, eq={"repositories_conformed": 0, "files_written": 0})


def test_toolchain_stage_propagates_conform_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def execute_request(
        request: m.Infra.CodegenConformRequest,
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> r[m.Infra.CodegenResult]:
        del request, initial_workspace
        return r[m.Infra.CodegenResult].fail("codegen drift detected: pyproject.toml")

    monkeypatch.setattr(
        FlextInfraCodegenConform, "execute_request", staticmethod(execute_request)
    )
    pipeline = _ToolchainStageHarness()
    context = cli.stage_context(tmp_path, settings={c.Infra.PIPELINE_KEY_DRY_RUN: True})

    result = pipeline._stage_toolchain(context)  # noqa: SLF001

    tm.fail(result)
    tm.that(result.error or "", has="codegen drift detected: pyproject.toml")


__all__: list[str] = []
