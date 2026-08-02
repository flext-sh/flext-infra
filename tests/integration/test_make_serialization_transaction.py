"""Public process contract for serialized Make transaction inheritance."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [
    pytest.mark.integration,
    pytest.mark.timeout(config.Infra.codegen.make.serialization.timeout_seconds),
]


class TestsMakeSerializationTransaction:
    """Prove real Make children preserve the natural transaction marker."""

    def test_public_make_inherits_absent_and_real_transaction_markers(
        self, infra_git_repo: Path
    ) -> None:
        """Inherit the marker without introducing or removing it."""
        make_config = config.Infra.codegen.make
        verb_spec = next(
            verb
            for verb in make_config.verbs
            if any(handler.mutating for handler in verb.handlers.values())
        )
        mutation_verb = verb_spec.name
        mutation_selector = next(
            selector
            for selector, handler in verb_spec.handlers.items()
            if handler.mutating
        )
        marker = c.Infra.WORKTREE_TRANSACTION_ENV
        marker_active_value = c.Infra.WORKTREE_TRANSACTION_ACTIVE_VALUE
        makefile = infra_git_repo / c.Infra.MAKEFILE_FILENAME
        artifact = infra_git_repo / "transaction-artifact.txt"
        (infra_git_repo / c.Infra.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                f'name = "{config.Infra.name}"\n'
                f'version = "{config.Infra.version}"\n'
            ),
            encoding="utf-8",
        )
        makefile.write_text(
            (
                f".PHONY: {mutation_verb} _serialized_{mutation_verb}\n"
                f"{mutation_verb}:\n"
                f"\t@{sys.executable} -m {c.Infra.PACKAGE_IMPORT_NAME} "
                f"{c.Infra.CLI_GROUP_WORKSPACE} serialize-make "
                f'--workspace "$(CURDIR)" --makefile "$(CURDIR)/'
                f'{c.Infra.MAKEFILE_FILENAME}" '
                f"--verb {mutation_verb} "
                f'--selector-value "$({make_config.selector})" '
                f'--apply-token "$({make_config.apply_variable})"\n'
                f"_serialized_{mutation_verb}:\n"
                f"\t@printf 'transaction-marker=%s\\n' "
                f'"$${{{marker}-<absent>}}"; '
                f'if [ "$${{{marker}-}}" = "{marker_active_value}" ] && '
                f'[ ! -e "{artifact.name}" ]; then '
                f"printf 'generated\\n' > \"{artifact.name}\"; fi\n"
            ),
            encoding="utf-8",
        )
        (infra_git_repo / ".gitignore").write_text(
            f"{make_config.serialization.lock_path.parts[0]}/\n", encoding="utf-8"
        )
        tm.that(u.Cli.process_env().get(marker), eq=None)

        outer_make = tm.ok(
            u.Cli.run_raw(
                (
                    c.Infra.MAKE,
                    "--no-print-directory",
                    mutation_verb,
                    f"{make_config.selector}={mutation_selector}",
                    f"{make_config.apply_variable}={make_config.apply_value}",
                ),
                cwd=infra_git_repo,
            )
        )

        tm.that(outer_make.exit_code, eq=0, msg=outer_make.stderr)
        tm.that(
            outer_make.stdout + outer_make.stderr, has="transaction-marker=<absent>"
        )
        tm.that(artifact.exists(), eq=False)

        request = m.Infra.WorktreeTransactionRequest(
            workspace_root=infra_git_repo,
            command=(
                c.Infra.CLI_GROUP_WORKSPACE,
                "serialize-make",
                "--workspace",
                str(infra_git_repo),
                "--makefile",
                str(makefile),
                "--verb",
                mutation_verb,
                "--selector-value",
                mutation_selector,
                "--apply-token",
                make_config.apply_value,
            ),
            apply_patch=True,
            timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
        )
        first_report = tm.ok(u.Infra.execute_worktree_transaction(request))
        first_rendered = u.Infra.render_worktree_transaction_report(first_report)

        tm.that(first_report.breakage_detected, eq=False, msg=first_rendered)
        tm.that(first_rendered.count("transaction: "), eq=1)
        tm.that(
            first_report.command_output.stdout + first_report.command_output.stderr,
            has=f"transaction-marker={marker_active_value}",
        )
        tm.that(first_report.applied, eq=True)
        tm.that(any(item.patch for item in first_report.repositories), eq=True)
        tm.that(artifact.read_text(encoding="utf-8"), eq="generated\n")

        second_report = tm.ok(u.Infra.execute_worktree_transaction(request))
        second_rendered = u.Infra.render_worktree_transaction_report(second_report)

        tm.that(second_report.breakage_detected, eq=False, msg=second_rendered)
        tm.that(second_rendered.count("transaction: "), eq=1)
        tm.that(
            second_report.command_output.stdout + second_report.command_output.stderr,
            has=f"transaction-marker={marker_active_value}",
        )
        tm.that(second_report.applied, eq=False, msg=second_rendered)
        tm.that(
            any(item.patch for item in second_report.repositories),
            eq=False,
            msg=second_rendered,
        )
        tm.that(artifact.read_text(encoding="utf-8"), eq="generated\n")
