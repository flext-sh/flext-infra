"""OPTIONS=Y displays a built-in verb's contract without effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraCodegenMakeVerbContract:
    """The generated contract mode runs no prerequisite, hook or handler."""

    pytestmark = pytest.mark.slow

    @staticmethod
    def test_catalog_help_and_contracts_preserve_files(
        infra_git_repo: Path,
    ) -> None:
        """Real Make exposes every catalog input without running its handler."""
        root = infra_git_repo
        TestsFlextInfraCodegenMakeVerbContract._scaffold(root)
        verbs = tuple(
            verb
            for verb in config.Infra.codegen.make.verbs
            if c.Infra.MakeProfile.STANDALONE in verb.profiles
        )
        tm.that(bool(verbs), eq=True)
        before = {
            path.relative_to(root): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }
        before_paths = sorted(path.relative_to(root) for path in root.rglob("*"))
        for goals in (
            ["help"],
            [*(verb.name for verb in verbs), "OPTIONS=Y"],
        ):
            output = tm.ok(
                u.Cli.run_raw(
                    ["make", "--no-print-directory", "-C", str(root), *goals],
                    options=m.Cli.ProcessOptions(remove_env_keys=("MAKEFLAGS",)),
                ),
            )
            tm.that(
                u.Cli.process_succeeded(output.outcome),
                eq=True,
                msg=output.stdout + output.stderr,
            )
            lines = output.stdout.splitlines()
            for verb in verbs:
                description = " ".join(verb.description.splitlines()).strip()
                heading = f"  {verb.name:<16} {description}"
                tm.that(lines, has=heading)
                if verb.arguments:
                    tm.that(
                        lines[lines.index(heading) + 1],
                        eq=f"    Inputs: {' '.join(verb.arguments)}",
                    )
            tm.that(
                sorted(path.relative_to(root) for path in root.rglob("*")),
                eq=before_paths,
            )
            tm.that(
                {
                    path.relative_to(root): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                },
                eq=before,
            )

    @staticmethod
    def _scaffold(root: Path) -> None:
        """Materialize the generated Makefile with a hook that marks execution."""
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        metadata = root / c.PYPROJECT_FILENAME
        before = metadata.read_bytes()
        TestsFlextInfraConformSupport.apply_conform_surface(
            root,
            workspace,
            c.Infra.CodegenConformSurface.MAKEFILE,
        )
        tm.that(metadata.read_bytes(), eq=before)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: pre-upg pre-check\n"
                "pre-upg:\n\t@echo HOOK_RAN\n"
                "pre-check:\n\t@echo HOOK_RAN\n",
            ),
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("verb", "selector"),
        [
            ("upg", "OPTIONS=Y"),
            ("upg", "OPTIONS=yes"),
            ("check", "HELP=1"),
            ("profile-mod", "OPTIONS=Y"),
            ("profile-mod-report", "OPTIONS=Y"),
            ("project-new", "OPTIONS=Y"),
        ],
    )
    def test_contract_selector_displays_the_verb_without_effects(
        infra_git_repo: Path,
        verb: str,
        selector: str,
    ) -> None:
        """The verb prints its contract and leaves the tree untouched."""
        root = infra_git_repo
        TestsFlextInfraCodegenMakeVerbContract._scaffold(root)
        before = sorted(path.relative_to(root) for path in root.rglob("*"))
        outcome = u.Cli.run_raw(
            ["make", "-C", str(root), verb, selector],
            options=m.Cli.ProcessOptions(remove_env_keys=("MAKEFLAGS",)),
        )
        output = tm.ok(outcome)
        tm.that(
            u.Cli.process_succeeded(output.outcome),
            eq=True,
            msg=output.stdout + output.stderr,
        )
        tm.that(output.stdout, has=[verb, "displays this contract without effects"])
        tm.that(output.stdout + output.stderr, lacks="HOOK_RAN")
        after = sorted(path.relative_to(root) for path in root.rglob("*"))
        tm.that(after, eq=before)

    @staticmethod
    def test_disabled_selector_keeps_the_verb_executing(infra_git_repo: Path) -> None:
        """A disabled selector still runs the verb's prerequisites.

        The scaffold has no provisioned environment, so the interpreter guard
        that every executing verb requires is the first prerequisite to fail.
        """
        root = infra_git_repo
        TestsFlextInfraCodegenMakeVerbContract._scaffold(root)
        outcome = u.Cli.run_raw(
            ["make", "-C", str(root), "check", "OPTIONS=N"],
            options=m.Cli.ProcessOptions(remove_env_keys=("MAKEFLAGS",)),
        )
        output = tm.ok(outcome)
        tm.fail(u.Cli.process_succeeded(output.outcome))
        tm.that(output.stderr, has="make setup creates it")
        tm.that(output.stdout + output.stderr, lacks="displays this contract")
