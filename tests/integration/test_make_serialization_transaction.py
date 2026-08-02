"""Public process contract for serialized Make transaction inheritance."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

from flext_infra import c, config, m, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm

pytestmark = [
    pytest.mark.integration,
    pytest.mark.timeout(config.Infra.codegen.make.serialization.timeout_seconds),
]


class TestsMakeSerializationTransaction:
    """Prove real Make children preserve the natural transaction marker."""

    def test_public_gen_applies_one_atomic_plan_and_rejects_foreign_dirty_bytes(
        self, infra_git_repo: Path
    ) -> None:
        """Accept only an exact canonical dirty fixed point on the second run."""
        target = infra_git_repo
        distribution = config.Infra.name
        package_name = distribution.replace("-", "_")
        pyproject = target / c.Infra.PYPROJECT_FILENAME
        pyproject.write_text(
            (
                "[project]\n"
                f'name = "{distribution}"\n'
                f'version = "{config.Infra.version}"\n'
                "requires-python = "
                f'"{config.Infra.codegen.toolchain.python_required_version}"\n'
            ),
            encoding="utf-8",
        )
        package_init = target / c.Infra.DEFAULT_SRC_DIR / package_name / c.Infra.INIT_PY
        package_init.parent.mkdir(parents=True)
        package_init.write_text("", encoding="utf-8")
        managed = target / c.Infra.MAKEFILE_FILENAME
        managed.write_text("# committed managed drift\n", encoding="utf-8")
        baseline = managed.read_bytes()
        canonical_line_length = config.Infra.tooling.tools.ruff.line_length
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "add", "-A"], cwd=target))
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "commit", "-q", "-m", "Seed committed drift"], cwd=target
            )
        )
        make_config = config.Infra.codegen.make
        gen_spec = next(verb for verb in make_config.verbs if verb.name == "gen")
        tm.that(gen_spec.apply_what in gen_spec.apply_whats, where=bool)
        command = (
            c.Infra.MAKE,
            "--no-print-directory",
            "gen",
            f"{make_config.apply_variable}={make_config.apply_value}",
            f"WORKSPACE={target}",
        )
        engine_root = Path(__file__).parents[2]

        first = tm.ok(u.Cli.run_raw(command, cwd=engine_root))
        first_output = first.stdout + first.stderr
        first_bytes = managed.read_bytes()
        first_status = tm.ok(
            u.Infra.git_capture_bytes(target, ("status", "--porcelain=v1", "-z"))
        )

        tm.that(first.exit_code, eq=0, msg=first_output)
        tm.that(first_output.count("transaction: "), eq=1)
        tm.that(first_output, has="applied=yes")
        tm.that(first_bytes, ne=baseline)
        first_pyproject = t.Cli.JSON_MAPPING_ADAPTER.validate_python(
            tomllib.loads(pyproject.read_text(encoding="utf-8"))
        )
        tooling = t.Cli.JSON_MAPPING_ADAPTER.validate_python(first_pyproject["tool"])
        ruff = t.Cli.JSON_MAPPING_ADAPTER.validate_python(tooling["ruff"])
        tm.that(ruff["line-length"], eq=canonical_line_length)

        second = tm.ok(u.Cli.run_raw(command, cwd=engine_root))
        second_output = second.stdout + second.stderr
        tm.that(second.exit_code, eq=0, msg=second_output)
        tm.that(second_output.count("transaction: "), eq=1)
        tm.that(second_output, has="applied=no")
        tm.that(managed.read_bytes(), eq=first_bytes)
        tm.that(
            tm.ok(
                u.Infra.git_capture_bytes(target, ("status", "--porcelain=v1", "-z"))
            ),
            eq=first_status,
        )

        foreign = first_bytes + b"# foreign delta\n"
        managed.write_bytes(foreign)
        rejected = tm.ok(u.Cli.run_raw(command, cwd=engine_root))
        rejected_output = rejected.stdout + rejected.stderr

        tm.that(rejected.exit_code, ne=0)
        tm.that(rejected_output, has="uncommitted WIP in managed file")
        tm.that(managed.read_bytes(), eq=foreign)
        direct = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=target,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.fail(direct, has="uncommitted WIP in managed file")
        tm.that(managed.read_bytes(), eq=foreign)

    def test_public_make_inherits_absent_and_real_transaction_markers(
        self, infra_git_repo: Path
    ) -> None:
        """Inherit the marker without introducing or removing it."""
        make_config = config.Infra.codegen.make
        mutation_verb = make_config.mutable_verbs[0]
        verb_spec = next(
            verb for verb in make_config.verbs if verb.name == mutation_verb
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
                    f"{make_config.selector}={verb_spec.apply_what}",
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
                verb_spec.apply_what,
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
