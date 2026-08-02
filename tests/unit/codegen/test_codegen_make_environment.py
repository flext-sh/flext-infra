"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _write_serializing_runtime(project_root: Path) -> None:
        """Emulate the public serializer while preserving configured tokens."""
        make = config.Infra.codegen.make
        test_u.Tests.write_executable(
            project_root / c.Infra.VENV_BIN_REL / c.Infra.PYTHON,
            (
                "#!/bin/sh\n"
                "verb=''\nselector=''\napply=''\nprevious=''\n"
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--verb" ]; then verb="$argument"; fi\n'
                '  if [ "$previous" = "--selector-value" ]; then '
                'selector="$argument"; fi\n'
                '  if [ "$previous" = "--apply-token" ]; then '
                'apply="$argument"; fi\n'
                '  previous="$argument"\n'
                "done\n"
                'if [ -n "$verb" ]; then\n'
                '  exec make --no-print-directory "_serialized_${verb}" '
                f'"{make.selector}=$selector" "{make.apply_variable}=$apply"\n'
                "fi\n"
                "exit 0\n"
            ),
        )

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
        infra_repositories = (test_u.Tests.repository_ref(config.Infra.name),)
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
            member_source.mkdir(parents=True)
            (member_source / "README.md").write_text(
                "fixture member\n", encoding="utf-8"
            )
            test_u.Tests.initialize_git_repo(member_source)
            workspace_root.mkdir(parents=True)
            (workspace_root / "README.md").write_text(
                "fixture workspace\n", encoding="utf-8"
            )
            test_u.Tests.initialize_git_repo(workspace_root)
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
            test_u.Tests.initialize_git_repo(project_root)
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "--local", "core.hooksPath", ".fixture-hooks"],
                cwd=project_root,
            )
        )
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
        runtime_bin = runtime_root / c.Infra.VENV_BIN_REL
        runtime_bin.mkdir(parents=True)
        runtime_python = runtime_bin / c.Infra.PYTHON
        runtime_python.write_text("#!/bin/sh\nexit 0\n")
        runtime_python.chmod(0o755)
        hostile_bin = tmp_path / "hostile" / c.Infra.VENV_BIN_REL
        hostile_venv = hostile_bin.parent
        hostile_bin.mkdir(parents=True)
        hostile_python = hostile_bin / c.Infra.PYTHON
        hostile_python.write_text("#!/bin/sh\nexit 0\n")
        hostile_python.chmod(0o755)
        (project_root / "custom.mk").write_text(
            ".PHONY: pre-status-all\n"
            "pre-status-all:\n"
            "\t@printf '%s\\n' "
            "'MAKE_PROFILE=$(MAKE_PROFILE)' "
            "'RUNTIME_ROOT=$(RUNTIME_ROOT)'\n"
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
            "WORKSPACE_ROOT": str(tmp_path / "hostile-workspace"),
            "PATH": f"{hostile_bin}:{os.environ['PATH']}",
            "UV": "/bin/true",
        }
        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "status"],
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
        expected_profile = c.Infra.MakeProfile.WORKSPACE_MEMBER if attached else profile
        tm.that(output[0], eq=f"MAKE_PROFILE={expected_profile.value}")
        tm.that(output[1], eq=f"RUNTIME_ROOT={runtime_root}")
        tm.that(output[2], eq=f"FLEXT_INFRA_PYTHON={runtime_python}")
        tm.that(output[3], eq=f"UV_PROJECT_ENVIRONMENT={runtime_bin.parent}")
        tm.that(output[4], eq=f"VIRTUAL_ENV={runtime_bin.parent}")
        tm.that(output[5], eq=f"PATH={runtime_bin}:{os.environ['PATH']}")
        tm.that(output[6], eq=str(runtime_python))

    def test_non_root_make_projection_is_topology_independent(
        self, tmp_path: Path
    ) -> None:
        """Render one byte-identical Make owner for attached and detached use."""
        detached_root, _ = self._render_makefile(
            tmp_path / "detached", c.Infra.MakeProfile.STANDALONE
        )
        attached_root, _ = self._render_makefile(
            tmp_path / "attached", c.Infra.MakeProfile.STANDALONE, attached=True
        )

        tm.that(
            (attached_root / c.Infra.MAKEFILE_FILENAME).read_bytes(),
            eq=(detached_root / c.Infra.MAKEFILE_FILENAME).read_bytes(),
        )

    def test_non_root_projection_is_identical_and_runtime_selects_attachment(
        self, tmp_path: Path
    ) -> None:
        """One non-root Makefile adapts only to its live Git attachment."""
        standalone_root, _ = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        member_root, _ = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.WORKSPACE_MEMBER, attached=True
        )

        standalone = (standalone_root / c.Infra.MAKEFILE_FILENAME).read_text(
            encoding="utf-8"
        )
        member = (member_root / c.Infra.MAKEFILE_FILENAME).read_text(encoding="utf-8")

        tm.that(member, eq=standalone)
        tm.that(standalone, has="git rev-parse --show-superproject-working-tree")
        tm.that(standalone, has="workspace-member,standalone")

    def test_configured_absent_apply_token_remains_read_only_at_dispatch(
        self, tmp_path: Path
    ) -> None:
        """The generated nested dispatcher treats the seeded token as absent."""
        project_root, _ = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )

        process = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "help",
                    (
                        f"{config.Infra.codegen.make.apply_variable}="
                        f"{config.Infra.codegen.make.apply_absent_value}"
                    ),
                ],
                cwd=project_root,
            )
        )

        tm.that(process.exit_code, eq=0, msg=process.stderr or process.stdout)
        tm.that(process.stdout, has=f"{project_root.name} [standalone]")

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
        progress = (
            f"setup profile={profile.value} runtime={project_root} action=provision"
        )
        tm.that((process.stdout + process.stderr).count(progress), eq=1)
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        tm.that(commands[0], has="venv --clear")
        setup = config.Infra.codegen.make.setup
        expected_sync_flags = " ".join((
            *(
                ("--all-packages",)
                if profile == c.Infra.MakeProfile.WORKSPACE_ROOT
                else ()
            ),
            f"--{setup.lock_mode}",
            f"--{setup.extras}-extras",
            f"--{setup.dependency_groups}-groups",
        ))
        tm.that(commands[1], has=f"sync --project {project_root} {expected_sync_flags}")
        if profile == c.Infra.MakeProfile.WORKSPACE_ROOT:
            tm.that(commands[2], has="pip check")

    def test_attached_setup_delegates_once_to_distinct_runtime_owner(
        self, tmp_path: Path
    ) -> None:
        """An attached member reaches one distinct owner without self-recursion."""
        project_root, workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE, attached=True
        )
        owner_progress = (
            f"setup profile={c.Infra.MakeProfile.WORKSPACE_ROOT.value} "
            f"runtime={workspace_root} action=provision"
        )
        (workspace_root / c.Infra.MAKEFILE_FILENAME).write_text(
            (
                ".PHONY: _builtin_setup_environment\n"
                "_builtin_setup_environment:\n"
                f"\t@printf '%s\\n' '{owner_progress}'\n"
            ),
            encoding="utf-8",
        )

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "setup"],
                cwd=project_root,
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS"),
            )
        )
        output = process.stdout + process.stderr
        delegate_progress = (
            f"setup profile={c.Infra.MakeProfile.WORKSPACE_MEMBER.value} "
            f"runtime={workspace_root} action=delegate"
        )

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output.count(delegate_progress), eq=1)
        tm.that(output.count(owner_progress), eq=1)
        tm.that(f"runtime={project_root} action=delegate" in output, eq=False)

    def test_serialized_runner_preserves_provisioned_external_tools(
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
                "UV_RUN := env -u PYTHONPATH -u MYPYPATH "
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
        self._write_serializing_runtime(project_root)
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
                    "DEPENDENCY=flext-cli",
                    (
                        f"{config.Infra.codegen.make.apply_variable}="
                        f"{config.Infra.codegen.make.apply_value}"
                    ),
                ],
                cwd=project_root,
                env={"UV": str(uv), "PATH": f"{uv.parent}:{os.environ['PATH']}"},
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
        self._write_serializing_runtime(project_root)
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
                    (
                        f"{config.Infra.codegen.make.apply_variable}="
                        f"{config.Infra.codegen.make.apply_value}"
                    ),
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

    def test_serialized_gate_fails_closed_before_managed_environment_exists(
        self, tmp_path: Path
    ) -> None:
        """A serialized gate preserves the canonical setup-required diagnostic."""
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
            '$(UV) venv --clear "$(RUNTIME_VENV)"',
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
            "submodule update --init --recursive",
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
