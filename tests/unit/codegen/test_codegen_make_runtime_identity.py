"""Public Make runtime uses the same locked tool identity as frozen setup.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from flext_infra import config
from tests import c, tm, u

pytestmark = c.Tests.MARK.slow


class TestsFlextInfraCodegenMakeRuntimeIdentity:
    """Host Mise configuration cannot replace a project's resolved executable."""

    @staticmethod
    def test_status_uses_locked_uv_without_loading_host_configuration(
        tmp_path: Path,
    ) -> None:
        """Test status uses locked uv without loading host configuration."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.provision_python_project_environment(root))
        host_config = tmp_path / "host-mise.toml"
        host_config.write_text("invalid-host = [\n", encoding="utf-8")
        lock = root / c.Infra.MISE_LOCK_FILENAME
        lock_before = lock.read_bytes()
        locked_uv = u.Tests.toml_tables_at(
            lock.read_text(encoding="utf-8"),
            "tools",
            "uv",
        )
        tm.that(len(locked_uv), eq=1)
        version = locked_uv[0]["version"]
        tm.ok(isinstance(version, str))
        (root / config.Infra.codegen.make.custom_handler_policy.filename).write_text(
            ".PHONY: post-status\n"
            'post-status:\n\t@test "$$APPLICATION_STATE" = "$(PROJECT_ROOT)"\n'
            "\t@printf 'application-environment-preserved\\n'\n",
            encoding="utf-8",
        )

        result = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "status"],
                cwd=root,
                env={
                    "MISE_GLOBAL_CONFIG_FILE": str(host_config),
                    "APPLICATION_STATE": str(root),
                },
            ),
        )

        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )
        tm.that(result.outcome.raw_return_code, eq=c.Cli.EXIT_CODE_SUCCESS)
        tm.that(result.stdout, has=f"uv {version} ")
        tm.that(result.stdout, has="application-environment-preserved")
        tm.that(result.stderr, lacks="invalid-host")
        tm.that(lock.read_bytes(), eq=lock_before)

    @staticmethod
    @c.Tests.MARK.parametrize(
        "profile",
        [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE],
    )
    def test_rendered_makefile_never_invokes_a_bare_direnv(
        tmp_path: Path,
        profile: c.Infra.MakeProfile,
    ) -> None:
        """Every generated direnv invocation runs the Mise-provisioned executable.

        A bare ``direnv`` resolves through the operator PATH, so a consumer
        without a host direnv could not run any activated verb.
        """
        root, _ = u.Tests.render_make_environment(tmp_path, profile)
        commands = tuple(
            line
            for line in (root / c.Infra.MAKEFILE_FILENAME)
            .read_text(encoding="utf-8")
            .splitlines()
            if not line.lstrip().startswith("#")
        )
        bare = tuple(
            line
            for line in commands
            if re.search(r"(?<![$\w])direnv (?:allow|exec)\b", line)
        )
        tm.that(bare, empty=True)
        tm.that(
            "\n".join(commands),
            has=[
                '$(DIRENV) exec "$(PROJECT_ROOT)" $(SELF_MAKE) _activated-$@',
                '$(DIRENV) allow "$(PROJECT_ROOT)"',
                'which "direnv"',
            ],
        )

    @staticmethod
    def test_activated_verb_never_selects_the_host_direnv(tmp_path: Path) -> None:
        """A public verb activates through the locked direnv, never host PATH."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.provision_python_project_environment(root))
        host_bin = tmp_path / "host-bin"
        u.Tests.write_executable(
            host_bin / "direnv",
            "#!/bin/sh\nprintf 'host-direnv-selected\\n' >&2\nexit 97\n",
        )
        (root / config.Infra.codegen.make.custom_handler_policy.filename).write_text(
            ".PHONY: post-status\n"
            "post-status:\n\t@printf 'locked-direnv-activated\\n'\n",
            encoding="utf-8",
        )

        result = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "status"],
                cwd=root,
                env={"PATH": os.pathsep.join((str(host_bin), os.environ["PATH"]))},
            ),
        )

        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )
        tm.that(result.stderr, lacks="host-direnv-selected")
        tm.that(result.stdout, has="locked-direnv-activated")

    @staticmethod
    def test_status_ignores_a_project_local_mise_override(
        tmp_path: Path,
    ) -> None:
        """A machine-local project override never selects a tool outside the lock."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.provision_python_project_environment(root))
        lock = root / c.Infra.MISE_LOCK_FILENAME
        lock_before = lock.read_bytes()
        locked_uv = u.Tests.toml_tables_at(
            lock.read_text(encoding="utf-8"),
            "tools",
            "uv",
        )
        tm.that(len(locked_uv), eq=1)
        version = locked_uv[0]["version"]
        tm.ok(isinstance(version, str))
        # Mise loads this name from the project directory on its own; the
        # pinned release is absent from the lock, as in the reported override.
        (root / ".mise.local.toml").write_text(
            '[tools]\nuv = "0.0.1"\n', encoding="utf-8"
        )

        result = tm.ok(
            u.Tests.run_isolated_make(["--no-print-directory", "status"], cwd=root)
        )

        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )
        tm.that(result.stdout, has=f"uv {version} ")
        tm.that(result.stderr, lacks="not in the lockfile")
        tm.that(result.stderr, lacks="0.0.1")
        tm.that(lock.read_bytes(), eq=lock_before)

    @staticmethod
    def test_status_reports_the_first_missing_declared_package(
        tmp_path: Path,
    ) -> None:
        """A bare interpreter cannot be reported as a provisioned project."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.create_python_environment(root))
        namespace = u.Infra.project_package_name(root)

        result = tm.ok(u.Tests.run_isolated_make(["status"], cwd=root))

        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=False,
            msg=result.stdout + result.stderr,
        )
        tm.that(result.stdout, has=f"runtime-import-declaration module={namespace!r}")
        tm.that(result.stderr, has=["ModuleNotFoundError", namespace])

    @staticmethod
    @c.Tests.MARK.parametrize(
        (
            "operational_status",
            "fail_preparation_diagnostic",
            "fail_exit_diagnostic",
        ),
        [
            (0, False, False),
            (37, False, False),
            (0, True, False),
            (0, False, True),
            (37, False, True),
        ],
    )
    def test_nested_runtime_preserves_failure_and_cleans_owned_resources(
        tmp_path: Path,
        operational_status: int,
        *,
        fail_preparation_diagnostic: bool,
        fail_exit_diagnostic: bool,
    ) -> None:
        """Nested runtime cleans failed preparation and preserves executed exits."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(u.Tests.create_python_environment(root))
        preserved = {
            c.Infra.MISE_LOCK_FILENAME: (
                root / c.Infra.MISE_LOCK_FILENAME
            ).read_bytes(),
        }
        command = ': >"$(PROJECT_ROOT)/leaf-ran"; '
        if fail_exit_diagnostic:
            command += (
                f"if (exit {operational_status}); then leaf_operation_status=0; "
                "else leaf_operation_status=$$?; fi; "
                'printf "%s\\n" "$$leaf_operation_status" '
                '>"$(PROJECT_ROOT)/leaf-operation-status"; '
                'exec 2>&-; exit "$$leaf_operation_status"'
            )
        else:
            command += f"exit {operational_status}"
        caller = "eval" if fail_exit_diagnostic else "$(SHELL) -c"
        # Closing stderr here fails preparation, before the selected command runs.
        diagnostic_redirect = " 2>&-" if fail_preparation_diagnostic else ""
        (root / config.Infra.codegen.make.custom_handler_policy.filename).write_text(
            ".PHONY: _custom-status post-status\n"
            "_custom-status:\n"
            "\t@if $(PROJECT_TOOL_EXEC) $(SELF_MAKE) post-status; "
            "then status=0; else status=$$?; fi; "
            'printf \'%s\\n\' "$$status" >"$(PROJECT_ROOT)/nested-status"; '
            'exit "$$status"\n'
            "post-status:\n"
            f"\t@if $(PROJECT_TOOL_EXEC) {caller} '{command}'"
            f"{diagnostic_redirect}; "
            "then status=0; else status=$$?; fi; "
            'printf \'%s\\n\' "$$status" >"$(PROJECT_ROOT)/leaf-status"; '
            'exit "$$status"\n',
            encoding="utf-8",
        )

        result = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", "status"],
                cwd=root,
            ),
        )

        leaf_status = int((root / "leaf-status").read_text(encoding="utf-8"))
        tm.that(
            (root / "leaf-ran").exists(),
            eq=not fail_preparation_diagnostic,
        )
        if fail_exit_diagnostic:
            tm.that(
                int((root / "leaf-operation-status").read_text(encoding="utf-8")),
                eq=operational_status,
            )
        failed = (
            operational_status != 0
            or fail_preparation_diagnostic
            or fail_exit_diagnostic
        )
        if operational_status != 0:
            tm.that(leaf_status, eq=operational_status)
        elif failed:
            tm.that(leaf_status, gt=0)
        else:
            tm.that(leaf_status, eq=c.Cli.EXIT_CODE_SUCCESS)
        # GNU Make returns 2 for a failed recipe, regardless of the leaf's exit.
        expected_make_status = 2 if failed else c.Cli.EXIT_CODE_SUCCESS
        tm.that(
            int((root / "nested-status").read_text(encoding="utf-8")),
            eq=expected_make_status,
        )
        tm.that(result.outcome.raw_return_code, eq=expected_make_status)
        tm.fail(result.outcome.timed_out)
        tm.that(result.outcome.forwarded_signal, eq=None)
        for relative, original in preserved.items():
            tm.that((root / relative).read_bytes(), eq=original)
