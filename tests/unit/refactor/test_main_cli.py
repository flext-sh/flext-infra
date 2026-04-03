from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm
from tests import m, r, t

from flext_infra import FlextInfraCliRefactor, main as infra_main


def refactor_main(argv: list[str] | None = None) -> int:
    args = ["refactor"]
    if argv is not None:
        args.extend(argv)
    return infra_main(args)


def test_refactor_census_rejects_apply_before_subcommand() -> None:
    tm.that(refactor_main(["--apply", "census"]), eq=2)


def test_refactor_centralize_accepts_apply_before_subcommand(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_apply = False
    captured_workspace = Path()
    captured_normalize_remaining = False

    def _mock_handler(
        params: m.Infra.RefactorCentralizeInput,
    ) -> r[t.IntMapping]:
        nonlocal captured_apply, captured_workspace, captured_normalize_remaining
        captured_apply = params.apply
        captured_workspace = Path(params.workspace).resolve()
        captured_normalize_remaining = params.normalize_remaining
        return r[t.IntMapping].ok({"files": 0})

    monkeypatch.setattr(
        FlextInfraCliRefactor,
        "_handle_centralize_pydantic",
        staticmethod(_mock_handler),
    )
    result = refactor_main(
        [
            "centralize-pydantic",
            "--workspace",
            str(tmp_path),
            "--apply",
        ],
    )
    tm.that(result, eq=0)
    tm.that(captured_apply, eq=True)
    tm.that(captured_workspace, eq=tmp_path.resolve())
    tm.that(captured_normalize_remaining, eq=False)


def test_refactor_runtime_alias_imports_accepts_aliases_and_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    captured_apply = False
    captured_aliases = ""
    captured_project = ""
    captured_workspace = Path()

    def _mock_handler(
        params: m.Infra.RefactorMigrateRuntimeAliasImportsInput,
    ) -> r[t.IntMapping]:
        nonlocal captured_apply, captured_aliases, captured_project, captured_workspace
        captured_apply = params.apply
        captured_aliases = params.aliases
        captured_project = params.project or ""
        captured_workspace = Path(params.workspace).resolve()
        return r[t.IntMapping].ok({"files_changed": 1})

    monkeypatch.setattr(
        FlextInfraCliRefactor,
        "_handle_migrate_runtime_alias_imports",
        staticmethod(_mock_handler),
    )
    result = refactor_main(
        [
            "migrate-runtime-alias-imports",
            "--workspace",
            str(tmp_path),
            "--project",
            "flext-infra",
            "--aliases",
            "r,s,u",
            "--apply",
        ],
    )
    tm.that(result, eq=0)
    tm.that(captured_apply, eq=True)
    tm.that(captured_aliases, eq="r,s,u")
    tm.that(captured_project, eq="flext-infra")
    tm.that(captured_workspace, eq=tmp_path.resolve())
