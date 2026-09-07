"""Public beads-workspace environment sync behavior through the facade."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, infra, m
from flext_tests import tm
from tests import TestsFlextInfraUtilities as u


def make_request(
    root: Path, *, apply: bool = True, force: bool = False, allow_direnv: bool = True
) -> m.Infra.WorkspaceEnvironmentSyncRequest:
    """Build one canonical beads-workspace sync request."""
    return m.Infra.WorkspaceEnvironmentSyncRequest(
        workspace_root=root,
        apply=apply,
        force=force,
        beads=m.Infra.BeadsWorkspaceEnvironmentSpec(),
        allow_direnv=allow_direnv,
    )


class TestsBeadsEnvironmentSync:
    """Behavior contract for the generated beads-workspace activation."""

    def test_sync_writes_generated_envrc_and_allows(self, tmp_path: Path) -> None:
        """An applied sync projects the canonical file and re-allows direnv."""
        result = infra.sync_environment_files(
            make_request(tmp_path), runner=u.Tests.command_runner(returncode=0)
        )
        tm.ok(result)
        envrc = tmp_path / c.Infra.ENVRC_FILENAME
        content = envrc.read_text(encoding="utf-8")
        marker = c.Infra.WORKSPACE_ENV_GENERATED_MARKERS[1]
        tm.that(marker in content, eq=True)
        tm.that('checkout_root="$(pwd -P)"' in content, eq=True)
        tm.that("$DIRENV_DIR" in content, eq=False)
        tm.that(
            ': "${AGENTS_GAS_CITY_ROOT:?AGENTS_GAS_CITY_ROOT must name' in content,
            eq=True,
        )
        tm.that("BEADS_DOLT_SERVER_PORT" in content, eq=True)
        tm.that(
            'gas_city_root="$(cd "${AGENTS_GAS_CITY_ROOT}" && pwd -P)"' in content,
            eq=True,
        )
        tm.that("dolt-state.json" in content, eq=True)

    def test_sync_without_allow_consumes_no_runner(self, tmp_path: Path) -> None:
        """allow_direnv=False never invokes a runner."""
        result = infra.sync_environment_files(
            make_request(tmp_path, allow_direnv=False)
        )
        tm.ok(result)
        tm.that((tmp_path / c.Infra.ENVRC_FILENAME).is_file(), eq=True)

    def test_report_mode_writes_nothing(self, tmp_path: Path) -> None:
        """apply=False is read-only and consumes no runner."""
        result = infra.sync_environment_files(make_request(tmp_path, apply=False))
        tm.ok(result)
        tm.that((tmp_path / c.Infra.ENVRC_FILENAME).exists(), eq=False)

    def test_custom_envrc_preserved_without_force(self, tmp_path: Path) -> None:
        """Custom content is never clobbered; direnv allow still heals."""
        custom = tmp_path / c.Infra.ENVRC_FILENAME
        _ = custom.write_text("PATH_add bin\n", encoding="utf-8")
        result = infra.sync_environment_files(
            make_request(tmp_path), runner=u.Tests.command_runner(returncode=0)
        )
        tm.ok(result)
        tm.that(custom.read_text(encoding="utf-8"), eq="PATH_add bin\n")

    def test_force_converts_custom_envrc_to_generated(self, tmp_path: Path) -> None:
        """force=True replaces custom content with the canonical projection."""
        custom = tmp_path / c.Infra.ENVRC_FILENAME
        _ = custom.write_text('checkout_root="${DIRENV_DIR#-}"\n', encoding="utf-8")
        result = infra.sync_environment_files(
            make_request(tmp_path, force=True),
            runner=u.Tests.command_runner(returncode=0),
        )
        tm.ok(result)
        content = custom.read_text(encoding="utf-8")
        tm.that("$DIRENV_DIR" in content, eq=False)
        tm.that("pwd -P" in content, eq=True)

    def test_failed_allow_fails_loud(self, tmp_path: Path) -> None:
        """A direnv allow failure fails the whole sync."""
        result = infra.sync_environment_files(
            make_request(tmp_path),
            runner=u.Tests.command_runner(returncode=1, stderr="blocked"),
        )
        tm.fail(result)
        tm.that("direnv allow failed" in (result.error or ""), eq=True)
