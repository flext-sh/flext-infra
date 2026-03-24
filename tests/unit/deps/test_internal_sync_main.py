from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_core import r
from flext_tests import tm

from flext_infra import FlextInfraInternalDependencySyncService
from flext_infra.deps import internal_sync
from tests import u


class TestMain:
    def test_main_success(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        cli_args = u.Infra.CliArgs(workspace=tmp_path)

        def _parse_args(
            _self: argparse.ArgumentParser,
            _args: Sequence[str] | None = None,
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

        monkeypatch.setattr(argparse.ArgumentParser, "parse_args", _parse_args)
        monkeypatch.setattr(u.Infra, "resolve", staticmethod(_resolve))
        monkeypatch.setattr(
            internal_sync.FlextInfraInternalDependencySyncService,
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
            _args: Sequence[str] | None = None,
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

        monkeypatch.setattr(argparse.ArgumentParser, "parse_args", _parse_args)
        monkeypatch.setattr(u.Infra, "resolve", staticmethod(_resolve))
        monkeypatch.setattr(
            internal_sync.FlextInfraInternalDependencySyncService,
            "sync",
            _sync,
        )
        tm.that(FlextInfraInternalDependencySyncService.main(), eq=1)
