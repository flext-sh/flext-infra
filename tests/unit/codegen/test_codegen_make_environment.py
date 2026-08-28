"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import WorktreeFixture, u as test_u

pytestmark = pytest.mark.slow


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _render_makefile(
        tmp_path: Path, profile: c.Infra.MakeProfile, *, local_infra: bool = False
    ) -> tuple[Path, Path]:
        role = c.Infra.RepositoryRole(profile.value)
        repository = test_u.Tests.repository_ref(
            "fixture-project", role=role
        ).model_copy(update={"editable": True})
        project_root = tmp_path / profile.value / "fixture-project"
        WorktreeFixture.write_python_project(project_root, repository.distribution)
        beads = test_u.Tests.beads_project(repository.distribution)
        test_u.Tests.write_beads_project(
            project_root,
            workspace=beads.workspace,
            database=beads.database,
            issue_prefix=beads.issue_prefix,
        )
        test_u.Tests.initialize_git_repo(project_root, origin_url=repository.url)
        provider = test_u.Tests.provider(repository.provider)
        baseline = tm.ok(u.Cli.capture(["git", "rev-parse", "HEAD"], cwd=project_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "remote.origin.skipDefaultUpdate", "true"],
                cwd=project_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "update-ref",
                    f"refs/remotes/origin/{provider.branch}",
                    baseline,
                ],
                cwd=project_root,
            )
        )
        workspace_root = project_root
        infra_repositories = (test_u.Tests.repository_ref(config.Infra.name),)
        local_subprojects = (
            (infra_repositories[0].model_copy(update={"path": Path("infra-engine")}),)
            if local_infra
            else ()
        )
        workspace = m.Infra.WorkspaceSpec(
            name="fixture-project",
            beads=beads,
            repository=repository,
            project=test_u.Tests.project_spec("fixture-project"),
            subprojects=local_subprojects,
        )
        request = m.Infra.CodegenConformRequest(
            root=project_root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        plan = tm.ok(
            FlextInfraCodegenConform(
                workspace_root=workspace_root,
                request=request,
                initial_workspace=workspace,
            ).plan(request)
        )
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.ok(
            u.Cli.atomic_write_text_file(project_root / "Makefile", makefile.rendered)
        )
        return project_root, workspace_root

    @staticmethod
    def _write_mise_setup_fixture(project_root: Path) -> None:
        toolchain = config.Infra.codegen.toolchain
        test_u.Tests.write_executable(
            project_root / "bin" / "mise",
            (
                "#!/bin/sh\n"
                'if [ "$1" = "--version" ]; then\n'
                f"  printf '%s\\n' '{toolchain.mise_version}'\n"
                "  exit 0\n"
                "fi\n"
                'case "$*" in\n'
                f"  *'exec -- uv --version'*) printf '%s\\n' 'uv {toolchain.uv_version}.0'; exit 0 ;;\n"
                "esac\n"
                'while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do shift; done\n'
                'if [ "$#" -gt 0 ]; then shift; exec "$@"; fi\n'
                "exit 0\n"
            ),
        )
        (project_root / "mise.lock").write_text("[tools]\n", encoding="utf-8")

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE]
    )
    def test_generated_make_uses_profile_runtime_venv_under_hostile_env(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Every generated shell receives the profile-resolved runtime venv."""
        project_root, runtime_root = self._render_makefile(tmp_path, profile)
        runtime_bin = runtime_root / ".venv" / "bin"
        runtime_bin.mkdir(parents=True)
        runtime_python = runtime_bin / "python"
        runtime_python.write_text("#!/bin/sh\nexit 0\n")
        runtime_python.chmod(0o755)
        hostile_venv = tmp_path / "hostile" / ".venv"
        hostile_bin = hostile_venv / "bin"
        hostile_bin.mkdir(parents=True)
        hostile_python = hostile_bin / "python"
        hostile_python.write_text("#!/bin/sh\nexit 0\n")
        hostile_python.chmod(0o755)
        (project_root / "custom.mk").write_text(
            ".PHONY: _custom_status_probe\n"
            "_custom_status_probe:\n"
            "\t@printf '%s\\n' "
            "'FLEXT_INFRA_PYTHON=$(FLEXT_INFRA_PYTHON)' "
            "'UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT)' "
            "'VIRTUAL_ENV=$(VIRTUAL_ENV)' "
            "'PATH=$(PATH)'\n"
            "\t@command -v python\n",
            encoding="utf-8",
        )
        active_env = {
            "FLEXT_INFRA_PYTHON": str(hostile_python),
            "UV_PROJECT_ENVIRONMENT": str(hostile_venv),
            "VIRTUAL_ENV": str(hostile_venv),
            "PATH": f"{hostile_bin}:{os.environ['PATH']}",
        }
        process = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "status",
                    f"{config.Infra.codegen.make.selector}=probe",
                ],
                cwd=project_root,
                env=active_env,
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            )
        )
        tm.that(
            process.exit_code,
            eq=0,
            msg=process.stderr or process.stdout or "make probe failed without output",
        )
        output = process.stdout.strip().splitlines()
        tm.that(output[0], eq=f"FLEXT_INFRA_PYTHON={runtime_python}")
        tm.that(output[1], eq=f"UV_PROJECT_ENVIRONMENT={runtime_root / '.venv'}")
        tm.that(output[2], eq=f"VIRTUAL_ENV={runtime_root / '.venv'}")
        tm.that(output[3], eq=f"PATH={runtime_bin}:{os.environ['PATH']}")
        tm.that(output[4], eq=str(runtime_python))

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE]
    )
    def test_setup_provisions_environment_before_project_runtime(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Setup creates the venv and syncs dependencies before any runtime use."""
        project_root, _workspace_root = self._render_makefile(tmp_path, profile)
        self._write_mise_setup_fixture(project_root)
        hostile_venv = tmp_path / "hostile" / ".venv"
        hostile_bin = hostile_venv / "bin"
        hostile_bin.mkdir(parents=True)
        hostile_uv = hostile_bin / "uv"
        hostile_uv.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        hostile_uv.chmod(0o755)
        provisioned_bin = tmp_path / "provisioned" / "bin"
        provisioned_bin.mkdir(parents=True)
        uv_log = tmp_path / "uv.log"
        provisioned_uv = provisioned_bin / "uv"
        provisioned_uv.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$*\" >> '{uv_log}'\n"
            'if [ "$1" = "venv" ]; then\n'
            '  mkdir -p "$3/bin"\n'
            "  printf '#!/bin/sh\\nexit 0\\n' > \"$3/bin/python\"\n"
            '  chmod +x "$3/bin/python"\n'
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        provisioned_uv.chmod(0o755)
        mise = test_u.Tests.write_mise_stub(tmp_path / "mise")
        (project_root / "mise.lock").touch()

        clean_env = {
            **{
                key: value
                for key, value in os.environ.items()
                if key not in {"MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"}
            },
            "PATH": f"{hostile_bin}:{provisioned_bin}:{os.environ['PATH']}",
            "VIRTUAL_ENV": str(hostile_venv),
        }
        result = u.Cli.run_raw(
            [c.Infra.MAKE, "--no-print-directory", "setup", f"SETUP_MISE={mise}"],
            cwd=project_root,
            env=clean_env,
            remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
        )

        process = tm.ok(result)
        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        tm.that(commands[0], has="venv ")
        tm.that(commands[1], has="sync --project")
        if profile == c.Infra.MakeProfile.WORKSPACE:
            tm.that(commands[2], has="pip check")

    def test_setup_bootstraps_before_the_tracked_mise_launcher_exists(
        self, tmp_path: Path
    ) -> None:
        """Use the exact managed Mise version already available on ``PATH``."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        (project_root / "mise.lock").write_text("[tools]\n", encoding="utf-8")
        tool_bin = tmp_path / "managed-tools" / "bin"
        mise = test_u.Tests.write_mise_stub(tool_bin / "mise")
        uv = tool_bin / "uv"
        test_u.Tests.write_executable(
            uv,
            "#!/bin/sh\n"
            'if [ "$1" = "--version" ]; then '
            f"printf 'uv {config.Infra.codegen.toolchain.uv_version}.0\\n'; exit; fi\n"
            'if [ "$1" = "venv" ]; then\n'
            '  mkdir -p "$2/bin"\n'
            "  printf '#!/bin/sh\\nexit 0\\n' > \"$2/bin/python\"\n"
            '  chmod +x "$2/bin/python"\n'
            "fi\n"
            "exit 0\n",
        )
        env = {"PATH": f"{tool_bin}:{os.environ['PATH']}"}

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "setup"],
                cwd=project_root,
                env=env,
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(mise.is_file(), eq=True)
        tm.that((project_root / ".venv" / "bin" / "python").is_file(), eq=True)

    def test_dispatched_runner_preserves_provisioned_external_tools(
        self, tmp_path: Path
    ) -> None:
        """Keep managed tools reachable while removing the hostile active venv."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        hostile_venv = tmp_path / "hostile" / ".venv"
        hostile_bin = hostile_venv / "bin"
        hostile_bin.mkdir(parents=True)
        provisioned_bin = tmp_path / "provisioned" / "bin"
        provisioned_bin.mkdir(parents=True)
        fixture_tool = "managed-tool"
        runtime_python = project_root / ".venv" / "bin" / "python"
        tool_log = tmp_path / "tools.log"
        for bin_root in (hostile_bin, provisioned_bin):
            test_u.Tests.write_executable(
                bin_root / fixture_tool,
                f"#!/bin/sh\nprintf '%s\\n' '{bin_root / fixture_tool}'\n",
            )
        test_u.Tests.write_executable(hostile_bin / "uv", "#!/bin/sh\nexit 99\n")
        test_u.Tests.write_executable(
            provisioned_bin / "uv", f"#!/bin/sh\nexec '{runtime_python}'\n"
        )
        test_u.Tests.write_executable(
            runtime_python,
            (
                "#!/bin/sh\n"
                f"command -v uv > '{tool_log}'\n"
                f"command -v {fixture_tool} >> '{tool_log}'\n"
            ),
        )
        test_u.Tests.write_executable(
            provisioned_bin / "uv", f"#!/bin/sh\nexec '{runtime_python}'\n"
        )
        active_env = {
            "PATH": f"{hostile_bin}:{provisioned_bin}:{os.environ['PATH']}",
            "VIRTUAL_ENV": str(hostile_venv),
        }

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "test"],
                cwd=project_root,
                env=active_env,
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tools = tool_log.read_text(encoding="utf-8").splitlines()
        tm.that(
            tools, eq=[str(provisioned_bin / "uv"), str(provisioned_bin / fixture_tool)]
        )

    def test_generated_operations_bind_uv_to_runtime_root(self, tmp_path: Path) -> None:
        """All generated uv operations use the profile-owned environment."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text()

        tm.that(
            "override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)" in makefile, eq=True
        )
        tm.that("UV ?= uv" in makefile, eq=True)
        tm.that(
            (
                "UV_RUN := env -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT "
                "-u UV_PROJECT_ENVIRONMENT "
                'PYTHONPATH="$(PROJECT_ROOT)/src" '
                '$(UV) run --project "$(RUNTIME_ROOT)" --no-sync'
            )
            in makefile,
            eq=True,
        )
        tm.that("CHECK_GATES_ALLOWED :=" in makefile, eq=True)
        tm.that("$(PROJECT_FLEXT_INFRA) check run" in makefile, eq=True)
        tm.that("$(UV_RUN) actionlint" in makefile, eq=False)
        tm.that('$(UV) sync --project "$(PROJECT_ROOT)"' in makefile, eq=True)
        tm.that('$(UV) build --project "$(PROJECT_ROOT)"' in makefile, eq=True)

    def test_dependency_upgrade_selects_only_one_distribution(
        self, tmp_path: Path
    ) -> None:
        """Refresh one Git dependency without globally upgrading the lock."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        runtime_python = project_root / ".venv" / "bin" / "python"
        test_u.Tests.write_executable(runtime_python, "#!/bin/sh\nexit 0\n")
        uv_log = tmp_path / "uv.log"
        bin_dir = tmp_path / "bin"
        uv = bin_dir / "uv"
        test_u.Tests.write_executable(
            uv, f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{uv_log}'\nexit 0\n"
        )

        process = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "deps",
                    f"{config.Infra.codegen.make.selector}=upgrade",
                    "DEPENDENCY=flext-cli",
                    "APPLY=Y",
                ],
                cwd=project_root,
                # PATH takes the DIRECTORY holding the stub, never the stub
                # itself: pointing it at the executable makes every lookup miss.
                env={"UV": str(uv), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS"),
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        tm.that(
            commands, has=(f"lock --project {project_root} --upgrade-package flext-cli")
        )
        tm.that(any(" --upgrade " in f" {line} " for line in commands), eq=False)

    def test_dependency_upgrade_rejects_non_distribution_selector(
        self, tmp_path: Path
    ) -> None:
        """Fail before uv when the dependency selector is not one package name."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        runtime_python = project_root / ".venv" / "bin" / "python"
        test_u.Tests.write_executable(runtime_python, "#!/bin/sh\nexit 0\n")
        uv_log = tmp_path / "uv.log"
        uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(
            uv, f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{uv_log}'\nexit 0\n"
        )

        process = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "deps",
                    f"{config.Infra.codegen.make.selector}=upgrade",
                    "DEPENDENCY=flext-cli --all",
                    "APPLY=Y",
                ],
                cwd=project_root,
                env={"UV": str(uv), "PATH": f"{uv.parent}:{os.environ['PATH']}"},
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS"),
            )
        )

        tm.that(process.exit_code, ne=0)
        tm.that(
            process.stdout + process.stderr, has="DEPENDENCY must be one normalized"
        )
        tm.that(uv_log.exists(), eq=False)

    def test_public_gate_fails_closed_before_managed_environment_exists(
        self, tmp_path: Path
    ) -> None:
        """A public gate preserves the canonical setup-required diagnostic."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "test"],
                cwd=project_root,
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS"),
            )
        )

        tm.that(process.exit_code, ne=0)
        tm.that(
            process.stdout + process.stderr,
            has=["missing environment interpreter", "make setup creates it"],
        )

    def test_generated_setup_is_self_contained(self, tmp_path: Path) -> None:
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        for required in (
            "UV ?= uv",
            '$(UV) venv "$(RUNTIME_VENV)"',
            '$(UV) sync --project "$(PROJECT_ROOT)"',
            '--link-mode "$(UV_LINK_MODE)"',
            'git -C "$$superproject" submodule update --init -- "$$child_path"',
            'git -C "$$child_root" branch --show-current',
            'merge-base --is-ancestor "$$gitlink" HEAD',
        ):
            tm.that(makefile, has=required)
        for forbidden in (
            "mise exec -- uv",
            "uv@",
            "define _setup_submodules",
            "SETUP_BRANCH :=",
            "--no-install-project",
            '--editable "$(PROJECT_ROOT)"',
            "pip install",
            "git checkout",
        ):
            tm.that(makefile, lacks=forbidden)

    def test_generated_dependency_upgrade_projects_lock_floors(
        self, tmp_path: Path
    ) -> None:
        """Make owns lock upgrade, open-floor projection, and final resolution."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile, has="deps modernize")
        tm.that(makefile, has="--rewrite-constraints")
        tm.that(makefile, lacks="--constraint-policy")
