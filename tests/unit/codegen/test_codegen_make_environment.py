"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from tests import u as test_u


class TestsCodegenMakeEnvironment:
    def test_generated_make_overrides_inherited_uv_environment(
        self, tmp_path: Path
    ) -> None:
        root = tmp_path / "demo-root"
        created = FlextInfraCodegenProjectNew(
            name="demo-root",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile, has="$(UV_RUN) python -m pytest")
        probe_file = root / "probe.env"
        (root / "custom.mk").write_text(
            "_custom_check_probe:\n"
            "\t@printf '%s\\n%s\\n%s\\n' "
            "'$(UV_PROJECT)' '$(UV_PROJECT_ENVIRONMENT)' '$(VIRTUAL_ENV)' "
            f"> '{probe_file}'\n",
            encoding="utf-8",
        )
        hostile_root = tmp_path / "hostile"
        hostile_venv = hostile_root / ".venv"
        active_env = os.environ.copy()
        active_env.update({
            "UV_PROJECT": str(hostile_root),
            "UV_PROJECT_ENVIRONMENT": str(hostile_venv),
            "VIRTUAL_ENV": str(hostile_venv),
        })

        result = u.Cli.run_raw(
            ["make", "--no-print-directory", "_custom_check_probe"],
            cwd=root,
            env=active_env,
        )

        tm.ok(result)
        output = probe_file.read_text(encoding="utf-8").splitlines()
        tm.that(output, eq=[str(root), str(root / ".venv"), str(root / ".venv")])

    def test_makefile_surface_applies_only_makefile(self, tmp_path: Path) -> None:
        root = tmp_path / "demo-root"
        created = FlextInfraCodegenProjectNew(
            name="demo-root",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        custom = root / "custom.mk"
        custom_content = ".PHONY: public-handler\npublic-handler:\n\t@true\n"
        custom.write_text(custom_content, encoding="utf-8")
        (root / "Makefile").write_text("stale\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "tests@flext.sh"], cwd=root
            )
        )
        tm.ok(
            u.Cli.run_checked(["git", "config", "user.name", "FLEXT Tests"], cwd=root)
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed generated project"], cwd=root
            )
        )

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        applied = tm.ok(result)
        tm.that(tuple(path.name for path in applied.written_files), eq=("Makefile",))
        tm.that(custom.read_text(encoding="utf-8"), eq=custom_content)

    @staticmethod
    def _render_makefile(
        tmp_path: Path, profile: c.Infra.MakeProfile, *, attached: bool = False
    ) -> tuple[Path, Path]:
        repository = m.Infra.RepositoryRef(
            name="fixture-project",
            distribution="fixture-project",
            url="https://github.com/flext-sh/fixture-project.git",
            branch=config.Infra.codegen.providers[0].branch,
            path=Path(),
            role=c.Infra.RepositoryRole(profile.value),
            provider="flext-sh",
            profile=profile,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )
        project_root = tmp_path / profile.value / "fixture-project"
        workspace_root = (
            project_root.parent
            if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER
            else project_root
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
                workspace_root_rel=(
                    ".." if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else "."
                ),
                year=2026,
            ),
            members=(),
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
        tm.ok(
            u.Cli.atomic_write_text_file(project_root / "Makefile", makefile.rendered)
        )
        return project_root, workspace_root

    @pytest.mark.parametrize(
        ("profile", "attached"),
        [
            (c.Infra.MakeProfile.WORKSPACE_ROOT, False),
            (c.Infra.MakeProfile.WORKSPACE_MEMBER, True),
            (c.Infra.MakeProfile.WORKSPACE_MEMBER, False),
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

    def test_setup_preserves_external_uv_and_removes_hostile_venv(
        self, tmp_path: Path
    ) -> None:
        """Clean CI can provision uv on PATH without leaking an active venv."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
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
        commands = uv_log.read_text(encoding="utf-8")
        tm.that(commands, has="venv --clear")
        tm.that(commands, has="sync --project")

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
        profile_names = {profile.name for profile in config.Infra.codegen.profiles}
        tm.that(profile_names, eq={profile.value for profile in c.Infra.MakeProfile})
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
            'git -C "$(PROJECT_ROOT)" submodule update --init --recursive',
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
