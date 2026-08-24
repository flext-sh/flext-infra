"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Why (hq-36xk): this module uses BOTH production namespaces (c.Infra, m.Infra,
# config.Infra) and test-only helpers (c.Tests, u.Tests, u.Cli). `tests` re-exports
# both; `flext_infra` exposes only the production half, so importing `u` from it
# made every u.Tests/c.Tests access a missing-attribute error.
from flext_infra import config
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import c, m, u
from flext_tests import tm


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _render_makefile(
        tmp_path: Path,
        profile: c.Infra.MakeProfile,
        *,
        attached: bool = False,
        local_infra: bool = False,
    ) -> tuple[Path, Path]:
        provider = config.Infra.codegen.providers[0]
        role = (
            c.Infra.RepositoryRole.WORKSPACE_MEMBER
            if attached
            else c.Infra.RepositoryRole(profile.value)
        )
        repository = m.Infra.RepositoryRef(
            name="fixture-project",
            distribution="fixture-project",
            url=f"{provider.base_url}/fixture-project.git",
            path=Path(),
            role=role,
            provider=provider.name,
            checkout=(
                c.Infra.CheckoutKind.SUBMODULE
                if attached
                else c.Infra.CheckoutKind.ROOT
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        project_root = tmp_path / profile.value / "fixture-project"
        workspace_root = project_root.parent if attached else project_root
        infra_repositories = (u.Tests.repository_ref(config.Infra.name),)
        local_members = (
            (infra_repositories[0].model_copy(update={"path": Path("infra-engine")}),)
            if local_infra
            else ()
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="fixture-project",
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
                workspace_root_rel=".",
                year=2026,
            ),
            members=local_members,
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
        if attached:
            member_source = tmp_path / "member-source"
            member_source.mkdir()
            (member_source / "README.md").write_text(
                "fixture member\n", encoding="utf-8"
            )
            u.Tests.initialize_git_repo(member_source)
            workspace_root.mkdir(parents=True)
            (workspace_root / "README.md").write_text(
                "fixture workspace\n", encoding="utf-8"
            )
            u.Tests.initialize_git_repo(workspace_root)
            tm.ok(
                u.Cli.run_checked(
                    [
                        c.Infra.GIT,
                        "-c",
                        "protocol.file.allow=always",
                        "submodule",
                        "add",
                        "-q",
                        str(member_source),
                        project_root.name,
                    ],
                    cwd=workspace_root,
                )
            )
        else:
            project_root.mkdir(parents=True)
        tm.ok(
            u.Cli.atomic_write_text_file(project_root / "Makefile", makefile.rendered)
        )
        return project_root, workspace_root

    @pytest.mark.parametrize(
        ("profile", "attached"),
        [
            (c.Infra.MakeProfile.WORKSPACE_ROOT, False),
            (c.Infra.MakeProfile.STANDALONE, True),
            (c.Infra.MakeProfile.STANDALONE, False),
        ],
    )
    def test_generated_make_uses_profile_runtime_venv_under_hostile_env(
        self, tmp_path: Path, profile: c.Infra.MakeProfile, *, attached: bool
    ) -> None:
        """Every generated shell receives the profile-resolved runtime venv."""
        project_root, workspace_root = self._render_makefile(
            tmp_path, profile, attached=attached
        )
        runtime_root = workspace_root if attached else project_root
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
        "profile", [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE_ROOT]
    )
    def test_setup_provisions_environment_before_project_runtime(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Setup creates the venv and syncs dependencies before any runtime use."""
        project_root, _workspace_root = self._render_makefile(tmp_path, profile)
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
            [c.Infra.MAKE, "--no-print-directory", "setup"],
            cwd=project_root,
            env=clean_env,
            remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
        )

        process = tm.ok(result)
        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        tm.that(commands[0], has="venv ")
        tm.that(commands[1], has="sync --project")
        if profile == c.Infra.MakeProfile.WORKSPACE_ROOT:
            tm.that(commands[2], has="pip check")

    @pytest.mark.parametrize("ci_enabled", [False, True])
    def test_setup_installs_git_hooks_only_outside_configured_ci(
        self, tmp_path: Path, *, ci_enabled: bool
    ) -> None:
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        bin_root = tmp_path / "bin"
        bin_root.mkdir()
        uv = bin_root / "uv"
        u.Tests.write_executable(
            uv,
            "#!/bin/sh\n"
            'if [ "$1" = "venv" ]; then\n'
            '  mkdir -p "$3/bin"\n'
            "  printf '#!/bin/sh\\nexit 0\\n' > \"$3/bin/python\"\n"
            '  chmod +x "$3/bin/python"\n'
            "fi\n"
            "exit 0\n",
        )
        hook_log = tmp_path / "hook-install.log"
        u.Tests.write_executable(
            project_root / ".github" / "scripts" / "install-git-hooks.sh",
            f"#!/bin/sh\nprintf '%s\\n' installed > '{hook_log}'\n",
        )
        ci = config.Infra.codegen.make.ci
        env = {"PATH": f"{bin_root}:{os.environ['PATH']}"}
        if ci_enabled:
            env[ci.variable] = ci.value

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "setup"],
                cwd=project_root,
                env=env,
                remove_env_keys=(*c.Tests.MAKE_ISOLATION_ENV_KEYS, ci.variable),
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(hook_log.exists(), eq=not ci_enabled)

    def test_setup_probes_before_repairing_environment(self, tmp_path: Path) -> None:
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")
        recipe = makefile.split("SETUP_ENVIRONMENT_RECIPE = ", 1)[1].split("\n\n", 1)[0]

        tm.that(recipe.index("--check"), lt=recipe.rindex(" sync "))

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
        for bin_root in (hostile_bin, provisioned_bin):
            for tool in (fixture_tool, "uv"):
                u.Tests.write_executable(
                    bin_root / tool, f"#!/bin/sh\nprintf '%s\\n' '{bin_root / tool}'\n"
                )
        runtime_python = project_root / ".venv" / "bin" / "python"
        tool_log = tmp_path / "tools.log"
        u.Tests.write_executable(
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
        u.Tests.write_executable(runtime_python, "#!/bin/sh\nexit 0\n")
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
                env={"UV": str(uv), "PATH": str(bin_dir)},
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
        u.Tests.write_executable(runtime_python, "#!/bin/sh\nexit 0\n")
        uv_log = tmp_path / "uv.log"
        uv = tmp_path / "bin" / "uv"
        u.Tests.write_executable(
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
            "refs/heads/$$branch",
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
