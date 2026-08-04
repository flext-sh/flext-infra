"""Workspace conform progress feedback contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_tests import tm


class TestsFlextInfraCodegenConformProgress:
    """Prove conform emits stage and template progress on stdout."""

    def test_plan_emits_stage_and_repository_progress(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check-mode conform must report stage and per-repository progress."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        _ = capsys.readouterr()
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
            what=c.Infra.CodegenConformSurface.ALL,
        )
        _ = FlextInfraCodegenConform.execute_request(request)
        captured = capsys.readouterr().out
        tm.that("Codegen Conform" in captured, where=bool, msg=captured[-3000:])
        tm.that("stage=plan" in captured, where=bool, msg=captured[-3000:])
        tm.that(
            "stage=plan repositories=" in captured, where=bool, msg=captured[-3000:]
        )
        tm.that(
            "[1/" in captured and "conform" in captured,
            where=bool,
            msg=captured[-3000:],
        )
        tm.that(
            "stage=pyproject" in captured or "stage=templates" in captured,
            where=bool,
            msg=captured[-3000:],
        )
        tm.that(" template " in captured, where=bool, msg=captured[-3000:])
