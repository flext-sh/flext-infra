"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


def _fake_uv_body(setup_log: Path) -> str:
    return f"#!/bin/sh\nprintf 'uv|%s\\n' \"$*\" >> '{setup_log}'\nexit 0\n"


def _fake_mise_body(setup_log: Path, fake_uv: Path, version: str) -> str:
    return (
        "#!/bin/sh\n"
        'case "${1:-}" in\n'
        "  --version)\n"
        f'    echo "{version} linux-x64 (fake)"\n'
        "    ;;\n"
        "  install)\n"
        f"    printf 'mise|%s\\n' \"$*\" >> '{setup_log}'\n"
        '    mkdir -p "${MISE_DATA_DIR:?}/shims"\n'
        f'    cp "{fake_uv}" "${{MISE_DATA_DIR}}/shims/uv"\n'
        '    chmod +x "${MISE_DATA_DIR}/shims/uv"\n'
        "    ;;\n"
        "esac\n"
        "exit 0\n"
    )


def _write_fake_curl(fake_bin: Path, curl_log: Path, fake_mise_source: Path) -> None:
    """Plant a curl that logs the URL and serves the fake mise binary."""
    fake_bin.mkdir(parents=True, exist_ok=True)
    curl_path = fake_bin / "curl"
    curl_path.write_text(
        "#!/bin/sh\n"
        "out=''; url=''; prev=''\n"
        'for arg in "$@"; do\n'
        '  case "$arg" in http*) url="$arg" ;; esac\n'
        '  if [ "$prev" = "-o" ]; then out="$arg"; fi\n'
        '  prev="$arg"\n'
        "done\n"
        f"printf 'curl|%s\\n' \"$url\" >> '{curl_log}'\n"
        f"cp '{fake_mise_source}' \"$out\"\n"
        'chmod +x "$out"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    curl_path.chmod(0o755)


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
        infra_repositories = tuple(
            item
            for item in config.Infra.codegen.repositories
            if item.distribution == config.Infra.name
        )
        tm.that(len(infra_repositories), eq=1)
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
                workspace_root_rel=(
                    ".." if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else "."
                ),
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
        tm.that(
            output[3],
            has=(
                f"PATH={runtime_bin}:{runtime_root}/.bin:{runtime_root}/.tools/shims:"
            ),
        )
        tm.that(output[4], eq=str(runtime_python))

    @pytest.mark.parametrize(
        ("profile", "local_infra"),
        [
            (c.Infra.MakeProfile.STANDALONE, False),
            (c.Infra.MakeProfile.WORKSPACE_ROOT, True),
        ],
    )
    def test_setup_bootstraps_configured_engine_before_project_environment(
        self, tmp_path: Path, profile: c.Infra.MakeProfile, *, local_infra: bool
    ) -> None:
        """Setup conforms stale metadata before project-owned uv reads it."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, profile, local_infra=local_infra
        )
        hostile_bin = tmp_path / "hostile" / "bin"
        hostile_bin.mkdir(parents=True)
        hostile_uv = hostile_bin / "uv"
        hostile_uv.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        hostile_uv.chmod(0o755)
        hostile_mise = hostile_bin / "mise"
        hostile_mise.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        hostile_mise.chmod(0o755)
        fake_bin = tmp_path / "fake" / "bin"
        setup_log = tmp_path / "setup.log"
        curl_log = tmp_path / "curl.log"
        fake_uv = tmp_path / "fake-uv"
        fake_uv.write_text(_fake_uv_body(setup_log), encoding="utf-8")
        fake_mise_source = tmp_path / "fake-mise"
        fake_mise_source.write_text(
            _fake_mise_body(
                setup_log, fake_uv, config.Infra.codegen.toolchain.mise_version
            ),
            encoding="utf-8",
        )
        _write_fake_curl(fake_bin, curl_log, fake_mise_source)

        clean_env = {
            **{
                key: value
                for key, value in os.environ.items()
                if key not in {"MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"}
            },
            "PATH": f"{hostile_bin}:{fake_bin}:/usr/bin:/bin",
            "SETUP_LOG": str(setup_log),
        }
        result = u.Cli.run_raw(
            [c.Infra.MAKE, "--no-print-directory", "setup"],
            cwd=project_root,
            env=clean_env,
            remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
        )

        process = tm.ok(result)
        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(
            curl_log.read_text(encoding="utf-8"),
            has=(
                "github.com/jdx/mise/releases/download/v"
                f"{config.Infra.codegen.toolchain.mise_version}"
            ),
        )
        commands = setup_log.read_text(encoding="utf-8").splitlines()
        conform = next(line for line in commands if "codegen conform" in line)
        if local_infra:
            tm.that(conform, has=f"--with-editable {project_root / 'infra-engine'}")
            tm.that(conform, lacks="git+")
        else:
            infra_repository = next(
                item
                for item in config.Infra.codegen.repositories
                if item.distribution == config.Infra.name
            )
            tm.that(
                conform,
                has=(
                    f"--with {infra_repository.distribution} @ "
                    f"git+{infra_repository.url}@{infra_repository.branch}"
                ),
            )
        log_text = "\n".join(commands)
        tm.that(log_text, has="mise|install --yes uv@")
        tm.that(log_text, has="uv|sync --project")
        tm.that(log_text, lacks="venv --clear")
        tm.that(log_text, lacks="uv|venv")
        uv_install_at = next(
            index
            for index, line in enumerate(commands)
            if line.startswith("mise|install --yes uv@")
        )
        first_conform_at = next(
            index for index, line in enumerate(commands) if "codegen conform" in line
        )
        last_conform_at = max(
            index for index, line in enumerate(commands) if "codegen conform" in line
        )
        full_install_at = commands.index("mise|install --yes")
        sync_at = next(
            index
            for index, line in enumerate(commands)
            if line.startswith("uv|sync --project")
        )
        tm.that(uv_install_at < first_conform_at, eq=True)
        tm.that(last_conform_at < full_install_at < sync_at, eq=True)

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
        shims_bin = project_root / ".tools" / "shims"
        shims_bin.mkdir(parents=True)
        fixture_tool = "managed-tool"
        for tool in (fixture_tool, "uv"):
            test_u.Tests.write_executable(
                hostile_bin / tool,
                f"#!/bin/sh\nprintf '%s\\n' '{hostile_bin / tool}'\n",
            )
            test_u.Tests.write_executable(
                shims_bin / tool, f"#!/bin/sh\nprintf '%s\\n' '{shims_bin / tool}'\n"
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
            "PATH": f"{hostile_bin}:{os.environ['PATH']}",
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
        tm.that(tools, eq=[str(shims_bin / "uv"), str(shims_bin / fixture_tool)])

    def test_generated_operations_bind_uv_to_runtime_root(self, tmp_path: Path) -> None:
        """All generated uv operations use the profile-owned environment."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text()

        tm.that(
            "override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)" in makefile, eq=True
        )
        tm.that("UV := $(MISE_SHIMS)/uv" in makefile, eq=True)
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
            "TOOLS_BIN := $(PROJECT_ROOT)/.bin",
            "MISE_DATA_DIR := $(PROJECT_ROOT)/.tools",
            "MISE ?= $(TOOLS_BIN)/mise",
            "UV := $(MISE_SHIMS)/uv",
            "_builtin_setup_tools:",
            "github.com/jdx/mise/releases/download",
            "_builtin_setup_conform: _builtin_setup_tools _builtin_setup_submodules",
            '$(MISE) install --yes "uv@$$uv_version"',
            "$(MISE) install --yes",
            '$(UV) sync --project "$(PROJECT_ROOT)"',
            '--link-mode "$(UV_LINK_MODE)"',
            'git -C "$$superproject" submodule update --init -- "$$child_path"',
            "refs/heads/$$branch",
        ):
            tm.that(makefile, has=required)
        for forbidden in (
            "Required uv executable not found",
            "RESOLVED_UV",
            "mise exec -- uv",
            "define _setup_submodules",
            "SETUP_BRANCH :=",
            "--no-install-project",
            '--editable "$(PROJECT_ROOT)"',
            "venv --clear",
            "pip install",
        ):
            tm.that(makefile, lacks=forbidden)

        tm.that(makefile, has="_builtin_setup_mise: _builtin_setup_conform")
        tm.that(makefile, has="_builtin_setup_environment: _builtin_setup_mise")

    def test_workspace_root_setup_orders_topology_conform_before_gitlinks(
        self, tmp_path: Path
    ) -> None:
        """Conform the root topology before selecting managed Gitlinks."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.WORKSPACE_ROOT
        )
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        for required in (
            "_builtin_setup_tools:",
            "_builtin_setup_topology: _builtin_setup_tools",
            "_builtin_setup_conform: _builtin_setup_topology _builtin_setup_submodules",
            "_builtin_setup_mise: _builtin_setup_conform",
            "_builtin_setup_environment: _builtin_setup_mise",
            'codegen conform --root "$(PROJECT_ROOT)" --scope "self" --mode apply',
            "$(MISE) install --yes",
        ):
            tm.that(makefile, has=required)
        tm.that(makefile, lacks="venv --clear")

    def test_setup_rerun_repairs_without_recreating_environment(
        self, tmp_path: Path
    ) -> None:
        """A healthy rerun never clears the venv or reinstalls packages."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        setup_log = tmp_path / "setup.log"
        curl_log = tmp_path / "curl.log"
        fake_uv = tmp_path / "fake-uv"
        fake_uv.write_text(_fake_uv_body(setup_log), encoding="utf-8")
        fake_mise_source = tmp_path / "fake-mise"
        fake_mise_source.write_text(
            _fake_mise_body(
                setup_log, fake_uv, config.Infra.codegen.toolchain.mise_version
            ),
            encoding="utf-8",
        )
        tools_bin = project_root / ".bin"
        tools_bin.mkdir()
        seeded_mise = tools_bin / "mise"
        seeded_mise.write_text(
            fake_mise_source.read_text(encoding="utf-8"), encoding="utf-8"
        )
        seeded_mise.chmod(0o755)
        fake_bin = tmp_path / "fake" / "bin"
        _write_fake_curl(fake_bin, curl_log, fake_mise_source)
        clean_env = {
            **{
                key: value
                for key, value in os.environ.items()
                if key not in {"MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"}
            },
            "PATH": f"{fake_bin}:/usr/bin:/bin",
            "SETUP_LOG": str(setup_log),
        }
        for _run in range(2):
            result = u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "setup"],
                cwd=project_root,
                env=clean_env,
                remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
            )
            process = tm.ok(result)
            tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)

        tm.that(curl_log.exists(), eq=False)
        commands = setup_log.read_text(encoding="utf-8").splitlines()
        log_text = "\n".join(commands)
        tm.that(log_text, lacks="venv --clear")
        tm.that(log_text, lacks="uv|venv")
        tm.that(commands.count("mise|install --yes"), eq=2)
        tm.that(
            sum(1 for line in commands if line.startswith("uv|sync --project")), eq=2
        )

    def test_setup_updates_outdated_bootstrap_mise(self, tmp_path: Path) -> None:
        """A drifted bootstrap binary is updated, never a hard failure."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        setup_log = tmp_path / "setup.log"
        curl_log = tmp_path / "curl.log"
        fake_uv = tmp_path / "fake-uv"
        fake_uv.write_text(_fake_uv_body(setup_log), encoding="utf-8")
        fake_mise_source = tmp_path / "fake-mise"
        fake_mise_source.write_text(
            _fake_mise_body(
                setup_log, fake_uv, config.Infra.codegen.toolchain.mise_version
            ),
            encoding="utf-8",
        )
        tools_bin = project_root / ".bin"
        tools_bin.mkdir()
        outdated_mise = tools_bin / "mise"
        outdated_mise.write_text(
            _fake_mise_body(setup_log, fake_uv, "0.0.1"), encoding="utf-8"
        )
        outdated_mise.chmod(0o755)
        fake_bin = tmp_path / "fake" / "bin"
        _write_fake_curl(fake_bin, curl_log, fake_mise_source)
        clean_env = {
            **{
                key: value
                for key, value in os.environ.items()
                if key not in {"MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"}
            },
            "PATH": f"{fake_bin}:/usr/bin:/bin",
            "SETUP_LOG": str(setup_log),
        }
        result = u.Cli.run_raw(
            [c.Infra.MAKE, "--no-print-directory", "setup"],
            cwd=project_root,
            env=clean_env,
            remove_env_keys=("MAKEFLAGS", "MAKEOVERRIDES", "MFLAGS", "UV"),
        )
        process = tm.ok(result)
        tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
        tm.that(
            curl_log.read_text(encoding="utf-8"),
            has=(
                "github.com/jdx/mise/releases/download/v"
                f"{config.Infra.codegen.toolchain.mise_version}"
            ),
        )

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
