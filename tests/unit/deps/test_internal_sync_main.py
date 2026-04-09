from __future__ import annotations

import argparse
from pathlib import Path

import pytest
from flext_tests import tm

from flext_core import r
from flext_infra import FlextInfraInternalDependencySyncService, u
from tests import t


class TestMain:
    def test_main_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cli_args = u.Infra.CliArgs(workspace=tmp_path)

        def _parse_args(
            _self: argparse.ArgumentParser,
            _args: t.StrSequence | None = None,
            _ns: argparse.Namespace | None = None,
        ) -> argparse.Namespace:
            return argparse.Namespace(workspace=tmp_path)

        def _resolve(_a: argparse.Namespace) -> u.Infra.CliArgs:
            return cli_args

        def _sync(
            _self: FlextInfraInternalDependencySyncService,
            _root: Path,
        ) -> r[int]:
            return r[int].ok(0)

        monkeypatch.setattr(
            FlextInfraInternalDependencySyncService,
            "sync",
            _sync,
        )
        tm.that(FlextInfraInternalDependencySyncService.main(), eq=0)

    def test_main_failure(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cli_args = u.Infra.CliArgs(workspace=tmp_path)

        def _parse_args(
            _self: argparse.ArgumentParser,
            _args: t.StrSequence | None = None,
            _ns: argparse.Namespace | None = None,
        ) -> argparse.Namespace:
            return argparse.Namespace(workspace=tmp_path)

        def _resolve(_a: argparse.Namespace) -> u.Infra.CliArgs:
            return cli_args

        def _sync(
            _self: FlextInfraInternalDependencySyncService,
            _root: Path,
        ) -> r[int]:
            return r[int].fail("sync failed")

        monkeypatch.setattr(
            FlextInfraInternalDependencySyncService,
            "sync",
            _sync,
        )
        tm.that(FlextInfraInternalDependencySyncService.main(), eq=1)
