"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u

pytestmark = pytest.mark.slow


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _render_makefile(tmp_path: Path) -> tuple[Path, Path]:
        provider = config.Infra.codegen.providers[0]
        repository = m.Infra.RepositoryRef(
            name="fixture-project",
            distribution="fixture-project",
            url=f"{provider.base_url}/fixture-project.git",
            path=Path(),
            provider=provider.name,
        )
        project_root = tmp_path / "fixture-project"
        workspace_root = project_root
        workspace = m.Infra.WorkspaceSpec(
            repository=repository,
            project=m.Infra.ProjectSpec(
                package_name="fixture_project",
                class_stem="FixtureProject",
                namespace="FixtureProject",
                constant_name="fixture-project",
                namespace_attribute="fixture_project",
                alias="fixture_project",
                environment_prefix="FIXTURE_PROJECT_",
                description="Fixture project",
                version="0.12.0",
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_cli",
                homepage="https://github.com/flext-sh/fixture-project",
                documentation="https://github.com/flext-sh/fixture-project",
                year=2026,
            ),
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
        project_root.mkdir(parents=True)
        for file in plan.files:
            tm.ok(u.Cli.atomic_write_text_file(file.path, file.rendered))
        (project_root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        (project_root / "mise.lock").write_text("[tools]\n", encoding="utf-8")
        return project_root, workspace_root

    def test_generated_make_uses_project_runtime_venv_under_hostile_env(
        self, tmp_path: Path
    ) -> None:
        """Every generated shell receives the project-owned runtime venv."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
        runtime_root = project_root
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
        handler = project_root / "scripts" / "status" / "probe.sh"
        handler.parent.mkdir(parents=True)
        handler.write_text(
            "#!/bin/sh\n"
            "printf '%s\\n' "
            '"FLEXT_INFRA_PYTHON=$FLEXT_INFRA_PYTHON" '
            '"UV_PROJECT_ENVIRONMENT=$UV_PROJECT_ENVIRONMENT" '
            '"VIRTUAL_ENV=$VIRTUAL_ENV" '
            '"PATH=$PATH"\n'
            "command -v python\n",
            encoding="utf-8",
        )
        handler.chmod(0o755)
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

    def test_setup_provisions_environment_before_project_runtime(
        self, tmp_path: Path
    ) -> None:
        """Setup creates the venv and syncs dependencies before any runtime use."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
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
            '  mkdir -p "$2/bin"\n'
            "  printf '#!/bin/sh\\nexit 0\\n' > \"$2/bin/python\"\n"
            '  chmod +x "$2/bin/python"\n'
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        provisioned_uv.chmod(0o755)
        test_u.Tests.write_mise_stub(project_root / "bin" / "mise")
        (project_root / "pyproject.toml").write_text(
            "[project]\nname='fixture'\n", encoding="utf-8"
        )
        (project_root / "uv.lock").write_text("version = 1\n", encoding="utf-8")

        clean_env = {
            **{
                key: value
                for key, value in os.environ.items()
                if key not in {"MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"}
            },
            "PATH": f"{hostile_bin}:{provisioned_bin}:{os.environ['PATH']}",
            "VIRTUAL_ENV": str(hostile_venv),
            "GITHUB_TOKEN": "fixture-token",
        }
        result = u.Cli.run_raw(
            [c.Infra.MAKE, "--no-print-directory", "setup"],
            cwd=project_root,
            env=clean_env,
            remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
        )

        process = tm.ok(result)
        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        tm.that(commands[0], has="venv ")
        tm.that(commands[1], has="export --quiet --project")
        tm.that(commands[1], has=["--locked", "--no-emit-project"])
        tm.that(
            commands[2],
            has=[
                "pip install --python",
                "--exact --no-deps --requirements",
                "--editable",
            ],
        )
        tm.that(commands[3], has="pip check --python")

    def test_setup_fails_before_the_tracked_mise_launcher_exists(
        self, tmp_path: Path
    ) -> None:
        """Never substitute a system Mise for the generated launcher owner."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
        (project_root / "mise.lock").write_text("[tools]\n", encoding="utf-8")
        result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "setup"],
                cwd=project_root,
                env={"GITHUB_TOKEN": "fixture-token", "PATH": os.environ["PATH"]},
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
            )
        )

        tm.that(result.exit_code, ne=0)
        tm.that(result.stderr, has="missing generated mise launcher")

    def test_dispatched_runner_preserves_provisioned_external_tools(
        self, tmp_path: Path
    ) -> None:
        """Keep managed tools reachable while removing the hostile active venv."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
        hostile_venv = tmp_path / "hostile" / ".venv"
        hostile_bin = hostile_venv / "bin"
        hostile_bin.mkdir(parents=True)
        provisioned_bin = tmp_path / "provisioned" / "bin"
        provisioned_bin.mkdir(parents=True)
        fixture_tool = "managed-tool"
        for bin_root in (hostile_bin, provisioned_bin):
            for tool in (fixture_tool, "uv"):
                test_u.Tests.write_executable(
                    bin_root / tool, f"#!/bin/sh\nprintf '%s\\n' '{bin_root / tool}'\n"
                )
        runtime_python = project_root / ".venv" / "bin" / "python"
        tool_log = tmp_path / "tools.log"
        test_u.Tests.write_executable(
            runtime_python,
            (
                "#!/bin/sh\n"
                f"command -v uv > '{tool_log}'\n"
                f"command -v {fixture_tool} >> '{tool_log}'\n"
            ),
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
        """All generated uv operations use the project-owned environment."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
        makefile = (project_root / "Makefile").read_text()

        tm.that(makefile, lacks="FLEXT_INFRA_BOOTSTRAP = $(PROJECT_FLEXT_INFRA)")
        tm.that(makefile, has='--with "$(FLEXT_INFRA_BOOTSTRAP_REQUIREMENT)"')
        tm.that(
            "override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)" in makefile, eq=True
        )
        tm.that("UV ?= uv" in makefile, eq=True)
        tm.that(
            (
                "UV_RUN := env -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT "
                "-u UV_PROJECT_ENVIRONMENT "
                'PATH="$(RUNTIME_BIN)$(CALLER_PATH_SEPARATOR)'
                '$(SANITIZED_CALLER_PATH)" '
                'PYTHONPATH="$(PROJECT_ROOT)/src"'
            )
            in makefile,
            eq=True,
        )
        tm.that("CHECK_GATES_ALLOWED :=" in makefile, eq=True)
        tm.that("$(PROJECT_FLEXT_INFRA) check run" in makefile, eq=True)
        tm.that("$(UV_RUN) actionlint" in makefile, eq=False)
        tm.that('$(UV) sync --project "$(PROJECT_ROOT)"' in makefile, eq=False)
        tm.that('$(UV) build --project "$(PROJECT_ROOT)"' in makefile, eq=True)

    def test_dependency_upgrade_selects_only_one_distribution(
        self, tmp_path: Path
    ) -> None:
        """Refresh one Git dependency without globally upgrading the lock."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
        runtime_python = project_root / ".venv" / "bin" / "python"
        test_u.Tests.write_executable(runtime_python, "#!/bin/sh\nexit 0\n")
        (project_root / "pyproject.toml").write_text(
            "[project]\nname='fixture'\n", encoding="utf-8"
        )
        (project_root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
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
        upgrade = next(line for line in commands if "--upgrade-package" in line)
        tm.that(upgrade, has="lock --project")
        tm.that(upgrade, has="--upgrade-package flext-cli")
        tm.that(upgrade, lacks=f"--project {project_root} ")
        tm.that(any(" --upgrade " in f" {line} " for line in commands), eq=False)

    def test_dependency_upgrade_rejects_non_distribution_selector(
        self, tmp_path: Path
    ) -> None:
        """Fail before uv when the dependency selector is not one package name."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
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
        project_root, _workspace_root = self._render_makefile(tmp_path)

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
        project_root, _workspace_root = self._render_makefile(tmp_path)
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        for required in (
            "UV ?= uv",
            '$(UV) venv "$(RUNTIME_VENV)"',
            '$(UV) export --quiet --project "$(SETUP_MANIFEST_ROOT)"',
            '$(UV) pip install --python "$(RUNTIME_VENV)"',
            '--exact --no-deps --requirements "$(SETUP_REQUIREMENTS)"',
            '--editable "$(PROJECT_ROOT)"',
            '--link-mode "$(UV_LINK_MODE)"',
        ):
            tm.that(makefile, has=required)
        for forbidden in (
            "mise exec -- uv",
            "uv@",
            "define _setup_submodules",
            "SETUP_BRANCH :=",
            "--no-install-project",
            "--all-packages",
        ):
            tm.that(makefile, lacks=forbidden)

    def test_generated_dependency_upgrade_projects_lock_floors(
        self, tmp_path: Path
    ) -> None:
        """Make owns lock upgrade, open-floor projection, and final resolution."""
        project_root, _workspace_root = self._render_makefile(tmp_path)
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile, has="deps modernize")
        tm.that(makefile, has="--rewrite-constraints")
        tm.that(makefile, lacks="--constraint-policy")
