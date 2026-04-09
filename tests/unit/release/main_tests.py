"""Tests for release CLI argument parsing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm

from tests import t, u


def _parse_args(argv: t.StrSequence | None = None) -> Namespace:
    parser = u.Infra.create_parser(
        prog="release",
        description="Release orchestration",
        flags=u.Infra.SharedFlags(include_apply=True),
    )
    _ = parser.add_argument("--phase", default="all")
    _ = parser.add_argument("--version", default="")
    _ = parser.add_argument("--tag", default="")
    _ = parser.add_argument("--bump", default="")
    _ = parser.add_argument("--interactive", type=int, default=1)
    _ = parser.add_argument("--push", action="store_true", default=False)
    _ = parser.add_argument("--dev-suffix", action="store_true", default=False)
    _ = parser.add_argument("--next-dev", action="store_true", default=False)
    _ = parser.add_argument("--next-bump", default="minor")
    _ = parser.add_argument("--create-branches", type=int, default=1)
    _ = parser.add_argument("--projects", nargs="*", default=[])
    return parser.parse_args(argv)


class TestReleaseMainParsing:
    """Test argument parsing for release CLI."""

    def test_parse_args_defaults(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(str(args.workspace), eq=str(Path.cwd()))
        tm.that(args.phase, eq="all")
        tm.that(args.version, eq="")
        tm.that(args.tag, eq="")
        tm.that(args.interactive, eq=1)
        tm.that(not args.push, eq=True)
        tm.that(not args.dry_run, eq=True)

    def test_parse_args_with_root(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(str(args.workspace), eq="/tmp/workspace")

    def test_parse_args_with_phase(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.phase, eq="validate")

    def test_parse_args_with_version(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.version, eq="1.0.0")

    def test_parse_args_with_tag(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.tag, eq="v1.0.0")

    def test_parse_args_with_bump(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.bump, eq="minor")

    def test_parse_args_with_interactive(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.interactive, eq=0)

    def test_parse_args_with_push(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.push, eq=True)

    def test_parse_args_with_dry_run(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.dry_run, eq=True)

    def test_parse_args_with_dev_suffix(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.dev_suffix, eq=True)

    def test_parse_args_with_next_dev(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.next_dev, eq=True)

    def test_parse_args_with_next_bump(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.next_bump, eq="patch")

    def test_parse_args_with_create_branches(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.create_branches, eq=0)

    def test_parse_args_with_projects(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.projects, eq=["proj1", "proj2"])

    def test_parse_args_projects_empty(self, monkeypatch: MonkeyPatch) -> None:
        args = _parse_args()
        tm.that(args.projects, eq=[])
