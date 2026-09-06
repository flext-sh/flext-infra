"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u
from tests.unit.workspace import WorktreeFixture

pytestmark = pytest.mark.slow


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _render_makefile(
        tmp_path: Path, profile: c.Infra.MakeProfile, *, local_infra: bool = False
    ) -> tuple[Path, Path]:
        role = c.Infra.MakeProfile(profile.value)
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
        repository_root = project_root
        infra_repositories = (test_u.Tests.repository_ref(config.Infra.name),)
        local_subprojects = (
            (infra_repositories[0].model_copy(update={"path": Path("infra-engine")}),)
            if local_infra
            else ()
        )
        workspace = m.Infra.WorkspaceSpec(
            name="fixture-project",
            beads=test_u.Tests.beads_project("fixture-project"),
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
                repository_root=repository_root,
                request=request,
                initial_workspace=workspace,
            ).plan(request)
        )
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                project_root / "Makefile", test_u.Tests.codegen_file_text(makefile)
            )
        )
        # The generated project environment is owned by two projections, not
        # one: the Makefile owns the runtime binding of every verb, and .envrc
        # owns the interactive shell's view of the same state roots. Writing
        # only the Makefile made an environment guarantee untestable the moment
        # it moved between the two owners.
        envrc = next(file for file in plan.files if file.path.name == ".envrc")
        tm.ok(
            u.Cli.atomic_write_text_file(
                project_root / ".envrc", test_u.Tests.codegen_file_text(envrc)
            )
        )
        return project_root, repository_root

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
            ".PHONY: _custom-status\n"
            "_custom-status:\n"
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
            test_u.Tests.run_isolated_make(
                ["--no-print-directory", "status"], cwd=project_root, env=active_env
            )
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stderr or process.stdout or "make probe failed without output",
        )
        output = process.stdout.strip().splitlines()
        tm.that(output[0], eq=f"FLEXT_INFRA_PYTHON={runtime_python}")
        tm.that(output[1], eq=f"UV_PROJECT_ENVIRONMENT={runtime_root / '.venv'}")
        tm.that(output[2], eq=f"VIRTUAL_ENV={runtime_root / '.venv'}")
        # The generated shell PREPENDS the profile runtime bin and REMOVES the
        # caller's active venv bin, preserving every other caller entry in
        # order. Byte equality with the caller PATH is not the contract and
        # never was: whatever launched make — a tool shim, a wrapper — may
        # legitimately have inserted its own managed bin dir before make read
        # the environment at all, and that entry is not the hostile venv.
        path_entries = output[3].removeprefix("PATH=").split(os.pathsep)
        tm.that(path_entries[0], eq=str(runtime_bin))
        tm.that(str(hostile_bin) in path_entries, eq=False)
        surviving = iter(path_entries[1:])
        tm.that(
            all(
                any(entry == candidate for candidate in surviving)
                for entry in os.environ["PATH"].split(os.pathsep)
            ),
            eq=True,
        )
        tm.that(output[4], eq=str(runtime_python))

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE]
    )
    def test_setup_provisions_environment_before_project_runtime(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Setup creates the venv and syncs dependencies before any runtime use."""
        project_root, _repository_root = self._render_makefile(tmp_path, profile)
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
        test_u.Tests.write_mise_stub(project_root / "bin" / "mise")
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
            [c.Infra.MAKE, "--no-print-directory", "setup"],
            cwd=project_root,
            env=clean_env,
            remove_env_keys=(*c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS, "UV"),
        )

        process = tm.ok(result)
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        tm.that(commands[0], has="venv ")
        tm.that(commands[1], has="sync --frozen --project")
        if profile == c.Infra.MakeProfile.WORKSPACE:
            tm.that(commands[2], has="pip check")

    def test_setup_fails_when_the_tracked_mise_launcher_is_missing(
        self, tmp_path: Path
    ) -> None:
        """Never substitute a system Mise for the generated launcher owner."""
        project_root, _repository_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        (project_root / "mise.lock").write_text("[tools]\n", encoding="utf-8")
        tool_bin = tmp_path / "managed-tools" / "bin"
        mise_log = tmp_path / "mise.log"
        mise = tool_bin / "mise"
        test_u.Tests.write_executable(
            mise, f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> '{mise_log}'\nexit 0\n"
        )

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "setup"],
                cwd=project_root,
                env={"PATH": f"{tool_bin}:{os.environ['PATH']}"},
                remove_env_keys=(*c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS, "UV"),
            )
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        tm.that(process.stdout + process.stderr, has="missing generated mise launcher")
        tm.that(mise.is_file(), eq=True)
        tm.that(mise_log.exists(), eq=False)
        tm.that((project_root / ".venv").exists(), eq=False)

    def test_dispatched_runner_preserves_provisioned_external_tools(
        self, tmp_path: Path
    ) -> None:
        """Keep managed tools reachable while removing the hostile active venv."""
        project_root, _repository_root = self._render_makefile(
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
                'test -z "${PROJECT_ROOT+x}" || exit 98\n'
                f"command -v uv > '{tool_log}'\n"
                f"command -v {fixture_tool} >> '{tool_log}'\n"
            ),
        )
        active_env = {
            "PATH": f"{hostile_bin}:{provisioned_bin}:{os.environ['PATH']}",
            "PROJECT_ROOT": str(tmp_path / "hostile-project-root"),
            "VIRTUAL_ENV": str(hostile_venv),
        }

        # `test` declares requires_apply in the typed Make owner, so the verb
        # only runs once the write-enable token is present.
        apply_variable = config.Infra.codegen.make.apply_variable
        apply_value = config.Infra.codegen.make.apply_value
        process = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "test",
                    f"{apply_variable}={apply_value}",
                ],
                cwd=project_root,
                env=active_env,
                remove_env_keys=(*c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS, "UV"),
            )
        )

        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tools = tool_log.read_text(encoding="utf-8").splitlines()
        tm.that(
            tools, eq=[str(provisioned_bin / "uv"), str(provisioned_bin / fixture_tool)]
        )

    def test_generated_operations_bind_uv_to_runtime_root(self, tmp_path: Path) -> None:
        """All generated uv operations use the profile-owned environment."""
        project_root, _repository_root = self._render_makefile(
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
                '-u PROJECT_ROOT PYTHONPATH="$(PROJECT_ROOT)/src" '
                '$(UV) run --project "$(RUNTIME_ROOT)" --no-sync'
            )
            in makefile,
            eq=True,
        )
        toolchain = config.Infra.codegen.toolchain
        # The state root is a SIBLING of the checkout, never a directory inside
        # it: derived from the Makefile's own PROJECT_ROOT so a verb invoked
        # from a foreign CWD still writes beside the tree that owns the verb.
        tm.that(
            (
                "PROJECT_STATE_ROOT := $(abspath $(PROJECT_ROOT)/../"
                f"{toolchain.state_directory_name}/$(notdir $(PROJECT_ROOT)))"
            )
            in makefile,
            eq=True,
        )
        tm.that(
            f"PROJECT_SCRATCH_ROOT := $(PROJECT_STATE_ROOT)/{toolchain.scratch_namespace}"
            in makefile,
            eq=True,
        )
        tm.that('TMPDIR="$$test_tmp" GOTMPDIR="$$test_tmp"' in makefile, eq=True)
        # Every gate the typed owner schedules by default reaches the runtime in
        # ONE `check run --gates` invocation. The Make layer no longer publishes
        # a per-gate selector, so the gate list itself is the reachability proof.
        gates = ",".join(config.Infra.codegen.make.check_gates_default)
        tm.that(makefile, has=f'gates="{gates}"')
        tm.that(
            '$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" '
            '--gates "$$gates" --projects .' in makefile,
            eq=True,
        )
        tm.that("$(UV_RUN) actionlint" in makefile, eq=False)
        tm.that('$(UV) sync --frozen --project "$(PROJECT_ROOT)"' in makefile, eq=True)
        tm.that('$(UV) build --project "$(PROJECT_ROOT)"' in makefile, eq=True)
        # Bytecode still lands in the project state root and never inside the
        # checkout. The Makefile stopped exporting it because the shell owns
        # the interactive environment now, so the guarantee is proved at .envrc
        # — its current owner — instead of being dropped with the old export.
        envrc = (project_root / ".envrc").read_text(encoding="utf-8")
        tm.that(
            envrc,
            has=(
                "export PYTHONPYCACHEPREFIX="
                f'"${{PROJECT_STATE_ROOT}}/{toolchain.pycache_namespace}"'
            ),
        )

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.WORKSPACE, c.Infra.MakeProfile.STANDALONE]
    )
    def test_every_declared_check_gate_reaches_the_runtime(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Every declared gate is scheduled by the one check handler, both profiles.

        The Make layer no longer publishes a per-gate `WHAT=` selector with a
        `_builtin_check_<gate>` target behind it; the public boundary accepts
        only APPLY. Reachability is therefore proved where it now lives: the
        single generated handler passes the complete declared gate list to the
        typed `check run` owner, so a gate the owner declares cannot be left
        unscheduled by the projection.
        """
        project_root, _workspace_root = self._render_makefile(tmp_path, profile)
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")
        phony_declarations = tuple(
            line.removeprefix(".PHONY:").strip()
            for line in makefile.splitlines()
            if line.startswith(".PHONY:")
        )

        # `check` is phony through the verb vocabulary, and its dispatch target
        # through the generated `_builtin-` prefix expansion of that same list.
        tm.that(
            phony_declarations,
            has="$(PUBLIC_VERBS) $(addprefix _builtin-,$(PUBLIC_VERBS))",
        )
        verbs = tuple(verb.name for verb in config.Infra.codegen.make.verbs)
        tm.that(verbs, has="check")
        # The dispatch chain that carries the declared gate list to the runtime.
        tm.that(makefile, has="_builtin-check: _builtin_check_all")
        tm.that(makefile, has="_builtin_check_all: _builtin_require_environment")
        scheduled = ",".join(config.Infra.codegen.make.check_gates_default)
        tm.that(makefile, has=f'gates="{scheduled}"')
        for gate in config.Infra.codegen.make.check_gates_default:
            tm.that(scheduled.split(","), has=gate)
        tm.that(makefile, has='--gates "$$gates" --projects .')

    def test_standalone_check_executes_its_declared_default_gates(
        self, tmp_path: Path
    ) -> None:
        """Standalone check runs exactly the owner-declared default gate set."""
        project_root, _repository_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        invocation_log = tmp_path / "check-invocation.log"
        runtime_python = project_root / ".venv" / "bin" / "python"
        test_u.Tests.write_executable(
            runtime_python, f"#!/bin/sh\nprintf '%s\\n' \"$*\" > '{invocation_log}'\n"
        )
        uv = tmp_path / "bin" / "uv"
        test_u.Tests.write_executable(uv, "#!/bin/sh\nexit 0\n")

        # APPLY is the ONLY public Make input; the generated boundary rejects
        # every other command-line variable by name, so the uv override that
        # used to ride on the command line is supplied through the environment.
        apply_variable = config.Infra.codegen.make.apply_variable
        apply_value = config.Infra.codegen.make.apply_value
        process = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.MAKE,
                    "--no-print-directory",
                    "check",
                    f"{apply_variable}={apply_value}",
                ],
                cwd=project_root,
                env={"UV": str(uv), "PATH": f"{uv.parent}:{os.environ['PATH']}"},
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            )
        )

        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        gates = ",".join(config.Infra.codegen.make.check_gates_default)
        invocation = invocation_log.read_text(encoding="utf-8")
        tm.that(invocation, has="-m flext_infra check run")
        tm.that(invocation, has=f"--gates {gates} --projects .")

    def test_dependency_upgrade_scopes_to_declared_project_locks(
        self, tmp_path: Path
    ) -> None:
        """Upgrade exactly the declared project locks through the deps verb."""
        project_root, _repository_root = self._render_makefile(
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
                [c.Infra.MAKE, "--no-print-directory", "deps", "APPLY=Y"],
                cwd=project_root,
                # PATH takes the DIRECTORY holding the stub, never the stub
                # itself: pointing it at the executable makes every lookup miss.
                env={"UV": str(uv), "PATH": f"{bin_dir}:{os.environ['PATH']}"},
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            )
        )

        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        commands = uv_log.read_text(encoding="utf-8").splitlines()
        # The upgrade scope is exactly the declared project locks: one pass with
        # the upgrade flag, then one plain lock verification of the same root.
        tm.that(
            [line for line in commands if line.startswith("lock")],
            eq=(
                f"lock --project {project_root} --upgrade",
                f"lock --project {project_root}",
            ),
        )

    def test_dependency_upgrade_requires_the_write_enable_token(
        self, tmp_path: Path
    ) -> None:
        """Fail before uv when the write-enable token is absent."""
        project_root, _repository_root = self._render_makefile(
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
                [c.Infra.MAKE, "--no-print-directory", "deps"],
                cwd=project_root,
                env={"UV": str(uv), "PATH": f"{uv.parent}:{os.environ['PATH']}"},
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            )
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        apply_variable = config.Infra.codegen.make.apply_variable
        apply_value = config.Infra.codegen.make.apply_value
        tm.that(
            process.stdout + process.stderr,
            has=f"this action requires {apply_variable}={apply_value}",
        )
        tm.that(uv_log.exists(), eq=False)

    def test_public_gate_fails_closed_before_managed_environment_exists(
        self, tmp_path: Path
    ) -> None:
        """A public gate preserves the canonical setup-required diagnostic."""
        project_root, _repository_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )

        process = tm.ok(
            u.Cli.run_raw(
                [c.Infra.MAKE, "--no-print-directory", "test"],
                cwd=project_root,
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            )
        )

        tm.that(process.outcome.raw_return_code, ne=0)
        tm.that(
            process.stdout + process.stderr,
            has=["missing environment interpreter", "make setup creates it"],
        )

    def test_generated_setup_is_self_contained(self, tmp_path: Path) -> None:
        project_root, _repository_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        for required in (
            "UV ?= uv",
            "ifneq ($(filter setup,$(MAKECMDGOALS)),)",
            "SETUP_BOOTSTRAP_ONLY := Y",
            'if [ -n "$${GITHUB_PATH:-}" ]; then',
            # Managed tools reach the setup lifecycle by RUNNING it inside the
            # bootstrapped Mise, not by the old inline PATH computation: the
            # toolchain is installed from the committed lock and the lifecycle
            # is executed through `mise exec`, so nothing needs an ambient mise
            # and nothing hand-assembles a managed PATH any more.
            (
                'mise_exec project "$$latest_mise" -C "$$project_root" '
                "install --locked --yes"
            ),
            (
                'mise_checked "$$scratch/lifecycle.log" mise_exec project '
                '"$$latest_mise" -C "$$project_root" exec -- env '
                '"SETUP_DIRENV=$$direnv_executable"'
            ),
            '$(UV) venv "$(RUNTIME_VENV)"',
            '$(UV) sync --frozen --project "$(PROJECT_ROOT)"',
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
        ):
            tm.that(makefile, lacks=forbidden)
        checkout_command = re.search(
            r"(?:^|[;&|]\s*)git(?:\s+-C\s+\S+)?\s+checkout(?:\s|$)",
            makefile,
            flags=re.MULTILINE,
        )
        tm.that(checkout_command is None, eq=True)

    def test_generated_dependency_upgrade_projects_lock_floors(
        self, tmp_path: Path
    ) -> None:
        """Make owns lock upgrade, open-floor projection, and final resolution."""
        project_root, _repository_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile, has="deps modernize")
        tm.that(makefile, has="--rewrite-constraints")
        tm.that(makefile, lacks="--constraint-policy")
