"""Contract tests for the make-managed development-lane verb."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_tests import tm
from tests import u as test_u


class TestsCodegenWorktreeVerb:
    """The `worktree` verb is part of the canonical public Make surface."""

    def _verb(self, name: str) -> m.Infra.MakeVerbSpec:
        matches = tuple(
            verb for verb in config.Infra.codegen.make.verbs if verb.name == name
        )
        tm.that(matches, len=1)
        return matches[0]

    def test_worktree_is_a_canonical_public_verb(self) -> None:
        """Every generated project receives the governed worktree route.

        Declaring it in `extra_verbs` would make it repository-local, which
        would defeat the purpose: every project must expose the same lane
        surface.
        """
        tm.that(self._verb("worktree").name, eq="worktree")

    def test_worktree_defaults_to_the_aggregate_contract(self) -> None:
        """Every public verb shares the selector-free aggregate default."""
        verb = self._verb("worktree")
        tm.that(verb.default_what, eq="all")

    def test_mutating_operations_own_the_apply_guard(self) -> None:
        """Read-only list remains usable without granting mutation authority.

        Guarding at verb level would force `APPLY=Y` onto `list`. The mutating
        selectors enforce the guard individually in their own recipes instead.
        """
        verb = self._verb("worktree")
        tm.that(verb.handlers["list"].mutating, eq=False)
        tm.that(verb.handlers["add"].mutating, eq=True)

    @pytest.mark.parametrize("operation", ["add", "update", "remove"])
    def test_public_make_guards_each_worktree_handler(
        self, tmp_path: Path, operation: str
    ) -> None:
        """Real Make dispatch keeps list read-only and guards each mutation."""
        make = config.Infra.codegen.make
        makefile = tm.ok(u.Cli.files_read_text(Path(c.Infra.MAKEFILE_FILENAME)))
        (tmp_path / c.Infra.MAKEFILE_FILENAME).write_text(makefile, encoding="utf-8")
        invocation_log = tmp_path / "worktree-invocations.log"
        test_u.Tests.write_executable(
            tmp_path / c.Infra.VENV_BIN_REL / "python",
            (
                "#!/bin/sh\n"
                "verb=''\nselector=''\napply=''\nmakefile=''\nprevious=''\n"
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--verb" ]; then verb="$argument"; fi\n'
                '  if [ "$previous" = "--selector-value" ]; then selector="$argument"; fi\n'
                '  if [ "$previous" = "--apply-token" ]; then apply="$argument"; fi\n'
                '  if [ "$previous" = "--makefile" ]; then makefile="$argument"; fi\n'
                '  previous="$argument"\n'
                "done\n"
                'if [ -n "$verb" ]; then\n'
                '  exec make --no-print-directory -f "$makefile" '
                '"_serialized_${verb}" '
                f'"{make.selector}=$selector" "{make.apply_variable}=$apply"\n'
                "fi\n"
                f'printf "%s\\n" "$*" >> "{invocation_log}"\n'
            ),
        )
        fake_uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(fake_uv, "#!/bin/sh\nexit 0\n")

        list_result = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "worktree",
                    f"{make.selector}=list",
                    f"UV={fake_uv}",
                ],
                cwd=tmp_path,
            )
        )
        tm.that(
            list_result.exit_code, eq=0, msg=list_result.stdout + list_result.stderr
        )
        list_with_apply = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "worktree",
                    f"{make.selector}=list",
                    f"{make.apply_variable}={make.apply_value}",
                    f"UV={fake_uv}",
                ],
                cwd=tmp_path,
            )
        )
        tm.that(list_with_apply.exit_code, ne=0)
        tm.that(list_with_apply.stdout + list_with_apply.stderr, has="read-only")

        mutation_arguments = [
            "--no-print-directory",
            "worktree",
            f"{make.selector}={operation}",
            "BASE=origin/main",
            "BRANCH=feature/probe",
            f"UV={fake_uv}",
        ]
        guarded = tm.ok(
            test_u.Tests.run_isolated_make(mutation_arguments, cwd=tmp_path)
        )
        tm.that(guarded.exit_code, ne=0)
        tm.that(
            guarded.stdout + guarded.stderr,
            has=f"requires {make.apply_variable}={make.apply_value}",
        )
        applied = tm.ok(
            test_u.Tests.run_isolated_make(
                [*mutation_arguments, f"{make.apply_variable}={make.apply_value}"],
                cwd=tmp_path,
            )
        )
        tm.that(applied.exit_code, eq=0, msg=applied.stdout + applied.stderr)
        tm.that(
            invocation_log.read_text(encoding="utf-8"),
            has=["--operation list", f"--operation {operation}"],
        )

    def test_public_make_add_reaches_setup_without_inherited_apply(
        self, tmp_path: Path
    ) -> None:
        """A real public add creates its lane and completes child setup."""
        make = config.Infra.codegen.make
        repository = tmp_path / "repository"
        repository.mkdir()
        makefile = Path(c.Infra.MAKEFILE_FILENAME).resolve()
        (repository / c.Infra.MAKEFILE_FILENAME).write_text(
            tm.ok(u.Cli.files_read_text(makefile)), encoding="utf-8"
        )
        (repository / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "worktree-runtime-probe"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        (repository / c.Infra.GITIGNORE).write_text(
            f"{Path(c.Infra.VENV_BIN_REL).parts[0]}/\n", encoding="utf-8"
        )
        test_u.Tests.initialize_git_repo(repository)
        tm.ok(
            u.Cli.ensure_symlink(
                repository / Path(c.Infra.VENV_BIN_REL).parts[0], Path(sys.prefix)
            )
        )
        setup_log = tmp_path / "setup.log"
        fake_uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(
            fake_uv, f'#!/bin/sh\nprintf "%s\\t%s\\n" "$PWD" "$*" >> "{setup_log}"\n'
        )
        branch = "feature/public-setup"
        common_arguments = [
            "--no-print-directory",
            "worktree",
            f"UV={fake_uv}",
            f"BRANCH={branch}",
            f"{make.apply_variable}={make.apply_value}",
        ]
        added = tm.ok(
            test_u.Tests.run_isolated_make(
                [*common_arguments, f"{make.selector}=add", "BASE=HEAD"], cwd=repository
            )
        )
        tm.that(added.exit_code, eq=0, msg=added.stdout + added.stderr)
        setup_output = setup_log.read_text(encoding="utf-8")
        lane = Path(setup_output.split("\t", 1)[0])
        tm.that(lane.is_dir(), where=bool)
        tm.that(setup_output, has=["venv --clear", "sync --project"])
        tm.that(added.stdout + added.stderr, lacks="read-only")

        tm.ok(u.Infra.git_remove_clean_worktree(repository, lane))
        tm.that(lane.exists(), eq=False)
