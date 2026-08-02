"""Verify generated workspace-root Make behavior across orchestration seams."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.orchestrator import FlextInfraOrchestratorService
from flext_tests import tm
from tests import u as test_u

if TYPE_CHECKING:
    from flext_cli import p as cli_p
    from flext_infra import p


def _write_workspace(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    # The fixture declares the synthetic topology it needs; flext-infra owns
    # no catalog of real projects to borrow rows from.
    root_repository = test_u.Tests.repository_ref("fixture-workspace")
    members = tuple(
        test_u.Tests.repository_ref(
            name, path=Path(name), role=c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        for name in ("fixture-member-one", "fixture-member-two")
    )
    project_names = tuple(member.path.as_posix() for member in members)
    root_package = (
        workspace_root / "src" / root_repository.distribution.replace("-", "_")
    )
    root_package.mkdir(parents=True)
    (root_package / "__init__.py").write_text("", encoding="utf-8")
    (workspace_root / "pyproject.toml").write_text(
        f"[project]\nname = '{root_repository.distribution}'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    manifest = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=root_repository.name,
        repository=root_repository,
        members=members,
    )
    tm.ok(
        u.Cli.yaml_dump(
            workspace_root / "config" / "workspace.yaml",
            manifest.model_dump(mode="json", exclude_none=True),
        )
    )
    for project_name in project_names:
        project_root = workspace_root / project_name
        project_root.mkdir(parents=True)
        package_root = project_root / "src" / project_name.replace("-", "_")
        package_root.mkdir(parents=True)
        (package_root / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "pyproject.toml").write_text(
            f"[project]\nname = '{project_name}'\nversion = '0.1.0'\n", encoding="utf-8"
        )
    # Seed the declared provider URL as origin so workspace discovery resolves
    # this fixture as a provider-governed checkout; the helper owns the fake
    # baseline ref, and real ancestry is exercised elsewhere.
    test_u.Tests.initialize_git_repo(workspace_root, origin_url=root_repository.url)
    # mro-z89e.2.2: seed a minimal .gitmodules so the conform detector sees the
    # declared members as governed submodules; the real setup/Gitlink lifecycle is
    # covered by tests/unit/codegen/test_workspace_root_setup_submodules.py.
    gitmodules_path = workspace_root / ".gitmodules"
    provider = config.Infra.codegen.providers[0]
    gitmodules_lines = []
    for member in members:
        section_name = member.name.replace("-", "_")
        gitmodules_lines.extend([
            f'[submodule "{section_name}"]\n',
            f"\tpath = {member.path.as_posix()}\n",
            f"\turl = {member.url}\n",
            f"\tbranch = {provider.branch}\n",
        ])
    gitmodules_path.write_text("".join(gitmodules_lines), encoding="utf-8")
    tm.ok(u.Cli.run_checked(["git", "add", ".gitmodules"], cwd=workspace_root))
    tm.ok(
        u.Cli.run_checked(
            ["git", "commit", "-m", "seed fixture gitmodules"], cwd=workspace_root
        )
    )
    # These tests assert what the GENERATED Makefile contains, so only the
    # rendered artifacts are needed. Running the apply path additionally drove
    # the Beads lifecycle, which inspects a live Dolt tracker: a unit test then
    # depended on an external service and failed on any machine without it.
    # Planning renders the same files and touches no tracker.
    planned = tm.ok(
        FlextInfraCodegenConform().plan(
            m.Infra.CodegenConformRequest(
                root=workspace_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
    )
    for planned_file in planned.files:
        planned_file.path.parent.mkdir(parents=True, exist_ok=True)
        planned_file.path.write_text(planned_file.rendered, encoding="utf-8")
    # mro-z89e.2.2: this fixture validates the environment/toolchain contract,
    # not Gitlink reconciliation. The generated .gitmodules would classify the
    # plain member directories as managed submodules and fail the setup
    # preflight; Gitlink behavior is covered by
    # tests/unit/codegen/test_workspace_root_setup_submodules.py.
    (workspace_root / ".gitmodules").unlink(missing_ok=True)
    for project_name in project_names:
        _write_child_makefile(workspace_root / project_name, exit_code=0)
    return workspace_root, project_names


def _render_standalone_hook_installer(tmp_path: Path) -> str:
    """Render the real universal installer with Beads ownership disabled."""
    project_root = tmp_path / "standalone-hook-render"
    repository = test_u.Tests.repository_ref(
        "standalone-hook-render", path=Path(), role=c.Infra.RepositoryRole.STANDALONE
    )
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repository.name,
        repository=repository,
        project=m.Infra.ProjectSpec(
            package_name="standalone_hook_render",
            class_stem="StandaloneHookRender",
            namespace="StandaloneHookRender",
            constant_name="standalone-hook-render",
            namespace_attribute="standalone_hook_render",
            alias="standalone_hook_render",
            environment_prefix="STANDALONE_HOOK_RENDER_",
            description="Standalone hook render fixture",
            version="0.12.0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage="https://github.com/flext-sh/standalone-hook-render",
            documentation="https://github.com/flext-sh/standalone-hook-render",
            workspace_root_rel=".",
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
            workspace_root=project_root, request=request, initial_workspace=workspace
        ).plan(request)
    )
    installer = config.Infra.codegen.make.git_hooks.installer
    rendered = next(
        planned_file.rendered
        for planned_file in plan.files
        if planned_file.path.relative_to(project_root) == installer
    )
    if not u.string_non_empty(rendered):
        msg = "generated hook installer must be a non-empty string"
        raise TypeError(msg)
    return rendered


def _write_child_makefile(project_root: Path, *, exit_code: int) -> None:
    (project_root / "Makefile").write_text(
        "SHELL := /bin/sh\n"
        ".PHONY: setup check test\n"
        "setup:\n"
        "\t@true\n"
        "check test:\n"
        "\t@printf 'project=%s verb=%s gates=%s uv_project=%s uv_env=%s "
        "venv=%s fail_fast=%s\\n' '$(notdir $(CURDIR))' '$@' "
        "'$(CHECK_GATES)' '$(UV_PROJECT)' '$(UV_PROJECT_ENVIRONMENT)' "
        "'$(VIRTUAL_ENV)' '$(FAIL_FAST)'\n"
        f"\t@exit {exit_code}\n",
        encoding="utf-8",
    )


class TestsWorkspaceRootMakeContract:
    def test_workspace_root_make_template_is_owned_by_typed_config(self) -> None:
        make_entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )

        tm.that(make_entries, len=1)
        tm.that(make_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_git_hook_installer_is_generated_for_every_repository_profile(self) -> None:
        """Keep one config-owned installer path across all generated profiles."""
        hook_policy = config.Infra.codegen.make.git_hooks
        entries = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if Path(entry.destination) == hook_policy.installer
        )

        tm.that(entries, len=1)
        tm.that(set(entries[0].profiles), eq=set(c.Infra.MakeProfile))
        tm.that(hook_policy.pre_commit_config, eq=Path(".pre-commit-config.yaml"))

    def test_generated_make_exposes_only_public_conform(self, tmp_path: Path) -> None:
        """Route the sole public conformance verb to the internal CLI.

        Which verb carries conformance is config-owned: it is declared in
        make.verbs and is `gen` today. The contract is that the declared verb
        reaches `codegen conform`, and that no second public entry point does.
        """
        workspace_root, _ = _write_workspace(tmp_path)
        declared = {verb.name for verb in config.Infra.codegen.make.verbs}
        tm.that(declared, has="gen")

        generated: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "gen", "WHAT=check"],
                cwd=workspace_root,
            )
        )
        retired: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "codegen"], cwd=workspace_root
            )
        )
        output = generated.stdout + generated.stderr

        tm.that(generated.exit_code, eq=0, msg=output)
        tm.that(output, has='--verb "gen"')
        tm.that(declared, lacks="codegen")
        tm.that(retired.exit_code, ne=0)

    def test_generated_setup_runs_its_lifecycle_hooks(self, tmp_path: Path) -> None:
        """``setup`` must fire pre-/post-setup like every other public verb.

        The generated ``setup`` short-circuited straight to
        ``_builtin_setup_environment``, bypassing ``_dispatch`` — so a project
        declaring ``post-setup`` in ``custom.mk`` (the only sanctioned extension
        surface) had that hook silently never execute.
        """
        workspace_root, _project_names = _write_workspace(tmp_path)
        (workspace_root / c.Infra.CUSTOM_MAKE_FILENAME).write_text(
            ".PHONY: post-setup\npost-setup:\n\t@echo POST_SETUP_HOOK_RAN\n",
            encoding="utf-8",
        )

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "setup"], cwd=workspace_root
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="post-setup", msg=output)

    def test_generated_make_selects_manifest_projects_and_forwards_gates(
        self, tmp_path: Path
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_check_all",
                    f"PROJECT={project_names[0]}",
                    "CHECK_GATES=lint,pyrefly",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has=f"--projects {project_names[0]}")
        tm.that(output, has='--make-arg "CHECK_GATES=lint,pyrefly"')
        tm.that(output, lacks=f"--projects {project_names[1]}")

    def test_generated_make_routes_fmt_apply_to_selected_project(
        self, tmp_path: Path
    ) -> None:
        """Apply formatting only in the selected workspace member."""
        workspace_root, project_names = _write_workspace(tmp_path)
        make_config = config.Infra.codegen.make
        fmt_spec = next(verb for verb in make_config.verbs if verb.name == "fmt")

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    f"_builtin_fmt_{fmt_spec.apply_what}",
                    f"PROJECT={project_names[0]}",
                    f"{make_config.selector}={fmt_spec.apply_what}",
                    f"{make_config.apply_variable}={make_config.apply_value}",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="--verb fmt")
        tm.that(output, has=f"--projects {project_names[0]}")
        tm.that(
            output, has=f'--make-arg "{make_config.selector}={fmt_spec.apply_what}"'
        )
        tm.that(
            output,
            has=(
                f'--make-arg "{make_config.apply_variable}={make_config.apply_value}"'
            ),
        )
        tm.that(output, lacks=f"--projects {project_names[1]}")
        tm.that(output, lacks="ruff check --fix")

    def test_generated_make_routes_file_and_match_only_to_owning_project(
        self, tmp_path: Path
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        owner = project_names[0]
        selected = f"{owner}/tests/unit/test_selected.py"

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_test_all",
                    f"FILE={selected}",
                    "MATCH=selected_case",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, has="--projects .")
        for project_name in project_names:
            tm.that(output, has=f"--projects {project_name}")
        tm.that(output, has="--file")
        tm.that(output, has="--match")
        tm.that(output, lacks="flext_infra._pytest_entry")

    def test_generated_make_routes_root_file_only_to_workspace_root(
        self, tmp_path: Path
    ) -> None:
        """Keep provider-owned root tests in the root project execution lane."""
        workspace_root, _ = _write_workspace(tmp_path)
        selected = "tests/unit/test_provider_contract.py"

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_test_all",
                    f"FILE={selected}",
                ],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        # The canonical orchestrator owns FILE resolution and reaches the root
        # through its private post-lock target, so public Make never recurses.
        tm.that(output, has="workspace orchestrate")
        tm.that(output, has="--projects .")
        tm.that(output, lacks="flext_infra._pytest_entry")
        tm.that(output, has="--file")

    def test_generated_make_default_test_includes_root_and_every_member(
        self, tmp_path: Path
    ) -> None:
        """Run provider root tests alongside every configured workspace member."""
        workspace_root, project_names = _write_workspace(tmp_path)

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "--dry-run", "_builtin_test_all"],
                cwd=workspace_root,
            )
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0, msg=output)
        tm.that(output, lacks="flext_infra._pytest_entry")
        tm.that(output, has="--projects .")
        for project_name in project_names:
            tm.that(output, has=f"--projects {project_name}")

    def test_workspace_root_ci_runs_each_gate_locally_once(
        self, tmp_path: Path
    ) -> None:
        """Keep CI self-only when submodules are intentionally not checked out."""
        workspace_root, project_names = _write_workspace(tmp_path)
        make_config = config.Infra.codegen.make
        ci_token = f"{make_config.ci.variable}={make_config.ci.value}"
        apply_token = f"{make_config.apply_variable}={make_config.apply_value}"
        probes = {
            "_builtin_build_artifacts": "build --project",
            "_builtin_check_all": "check run --workspace",
            "_builtin_test_all": "flext_infra._pytest_entry",
            "_builtin_fmt_all": "ruff format",
            "_builtin_fix_all": "ruff check --fix",
        }

        for target, local_command in probes.items():
            command = ["-C", str(workspace_root), "--dry-run", target, ci_token]
            if target in {"_builtin_fmt_all", "_builtin_fix_all"}:
                command.append(apply_token)
            process = tm.ok(test_u.Tests.run_isolated_make(command, cwd=workspace_root))
            output = process.stdout + process.stderr

            tm.that(process.exit_code, eq=0, msg=output)
            tm.that(output, has=local_command)
            tm.that(output, lacks="workspace orchestrate")
            for project_name in project_names:
                tm.that(output, lacks=f"--projects {project_name}")

    def test_generated_make_exposes_typed_docs_lifecycle(self, tmp_path: Path) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        make_config = config.Infra.codegen.make
        docs = make_config.docs
        docs_spec = next(verb for verb in make_config.verbs if verb.name == "docs")
        docs_actions = make_config.handler_whats["docs"]
        docs_default = docs_spec.default_what
        invocation_log = workspace_root / "docs.log"
        test_u.Tests.write_executable(
            workspace_root / ".venv" / "bin" / "python",
            (
                "#!/bin/sh\n"
                "verb=''\n"
                "previous=''\n"
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--verb" ]; then verb="$argument"; fi\n'
                '  previous="$argument"\n'
                "done\n"
                'if [ -n "$verb" ]; then exec make --no-print-directory "_serialized_${verb}"; fi\n'
                f'printf "%s\\n" "$*" >> "{invocation_log}"\n'
            ),
        )
        uv = workspace_root / "bin" / "uv"
        test_u.Tests.write_executable(uv, "#!/bin/sh\nexit 0\n")

        for action in docs_actions:
            invocation_log.write_text("", encoding="utf-8")
            process: cli_p.Cli.CommandOutput = tm.ok(
                test_u.Tests.run_isolated_make(
                    [
                        "-C",
                        str(workspace_root),
                        "docs",
                        f"{make_config.selector}={action}",
                        f"PROJECTS={project_names[0]}",
                        f"UV={uv}",
                    ],
                    cwd=workspace_root,
                )
            )
            tm.that(process.exit_code, eq=0, msg=process.stdout + process.stderr)
            output = invocation_log.read_text(encoding="utf-8")
            expected_actions = (
                tuple(item for item in docs_actions if item != docs_default)
                if action == docs_default
                else (action,)
            )
            for expected_action in expected_actions:
                tm.that(output, has=f"docs {expected_action}")
            tm.that(output, has=f"--output-dir {workspace_root / docs.reports_dir}")
            tm.that(output, has=f"--projects {project_names[0]}")
            tm.that(output, lacks=f"--projects {project_names[1]}")
            if action in docs_spec.optional_apply_whats:
                tm.that(output, has="--check")
                tm.that(output, lacks="--apply")
                invocation_log.write_text("", encoding="utf-8")
                applied = tm.ok(
                    test_u.Tests.run_isolated_make(
                        [
                            "-C",
                            str(workspace_root),
                            "docs",
                            f"{make_config.selector}={action}",
                            (f"{make_config.apply_variable}={make_config.apply_value}"),
                            f"PROJECTS={project_names[0]}",
                            f"UV={uv}",
                        ],
                        cwd=workspace_root,
                    )
                )
                tm.that(applied.exit_code, eq=0, msg=applied.stdout + applied.stderr)
                applied_output = invocation_log.read_text(encoding="utf-8")
                tm.that(applied_output, has="--apply")
                tm.that(applied_output, lacks="--check")
            elif action != docs_default:
                tm.that(output, lacks="--apply")
                tm.that(output, lacks="--check")

        invalid = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "docs",
                    f"{make_config.selector}=not-a-docs-action",
                ],
                cwd=workspace_root,
            )
        )
        tm.that(invalid.exit_code, ne=0)

    def test_workspace_root_setup_owns_environment_and_uses_venv_directory(
        self, tmp_path: Path
    ) -> None:
        """Setup provisions the root environment through the caller's uv.

        Setup is provision-only: it creates the workspace venv and syncs
        dependencies with the uv the caller already has on PATH. The previous
        expectation (curl-downloaded mise, then `mise install uv@`, then a
        conform pass, then sync) modelled a bootstrap pipeline the setup
        cutover removed, and it drove real network and real builds from a unit
        test. A fake uv records the invocation, so the contract is observed
        without provisioning anything.
        """
        workspace_root, _ = _write_workspace(tmp_path)
        setup_log = tmp_path / "setup.log"
        fake_bin = tmp_path / "fake" / "bin"
        fake_bin.mkdir(parents=True)
        fake_uv = fake_bin / "uv"
        fake_uv.write_text(
            "#!/bin/sh\n"
            'printf "uv|%s|%s|%s|%s\\n" "${UV_PROJECT:-}" '
            '"${UV_PROJECT_ENVIRONMENT:-}" "${VIRTUAL_ENV:-}" "$*" '
            f">> '{setup_log}'\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)

        process: cli_p.Cli.CommandOutput = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "--dry-run",
                    "_builtin_setup_environment",
                    f"UV={fake_uv}",
                ],
                cwd=workspace_root,
            )
        )

        output = process.stdout + process.stderr
        tm.that(process.exit_code, eq=0, msg=output)
        expected_environment = str(workspace_root / ".venv")
        # The root owns its own environment: the venv lives beside it and the
        # sync targets the workspace root, never an ambient caller project.
        tm.that(output, has=f'venv --clear "{expected_environment}"')
        tm.that(output, has=f'sync --project "{workspace_root}"')
        tm.that(output, has=f'pip check --python "{expected_environment}"')

    def test_setup_installs_root_and_member_hooks_serially_and_skips_ci(
        self, tmp_path: Path
    ) -> None:
        """Run the one generated installer for every config-scoped repository."""
        workspace_root, project_names = _write_workspace(tmp_path)
        hook_policy = config.Infra.codegen.make.git_hooks
        repository_roots = (
            workspace_root,
            *(workspace_root / project_name for project_name in project_names),
        )
        installer = _render_standalone_hook_installer(tmp_path)
        config_template = (
            "repos:\n"
            "  - repo: local\n"
            "    hooks:\n"
            "      - id: setup-fanout-marker\n"
            "        name: setup fanout marker\n"
            "        entry: sh -c 'printf __MARKER__ > __MARKER__.log'\n"
            "        language: system\n"
            "        pass_filenames: false\n"
            "        always_run: true\n"
        )
        for index, repository_root in enumerate(repository_roots):
            if index:
                test_u.Tests.initialize_git_repo(repository_root)
            installer_path = repository_root / hook_policy.installer
            installer_path.parent.mkdir(parents=True, exist_ok=True)
            installer_path.write_text(installer, encoding="utf-8")
            marker = f"repository-{index}"
            (repository_root / hook_policy.pre_commit_config).write_text(
                config_template.replace("__MARKER__", marker), encoding="utf-8"
            )
            tm.ok(
                u.Infra.git_capture(
                    repository_root,
                    (
                        "add",
                        hook_policy.installer.as_posix(),
                        hook_policy.pre_commit_config.as_posix(),
                    ),
                )
            )
            tm.ok(
                u.Infra.git_capture(
                    repository_root,
                    ("commit", "-q", "-m", f"configure repository {index}"),
                )
            )
            runtime = repository_root / c.Infra.VENV_BIN_REL / c.Infra.PYTHON
            runtime.parents[1].symlink_to(Path(sys.prefix), target_is_directory=True)

        ci_policy = config.Infra.codegen.make.ci
        ci = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "-C",
                    str(workspace_root),
                    "_builtin_setup_hooks",
                    f"{ci_policy.variable}={ci_policy.value}",
                ],
                cwd=workspace_root,
            )
        )
        tm.that(ci.exit_code, eq=0, msg=ci.stdout + ci.stderr)
        hook_paths: list[Path] = []
        for repository_root in repository_roots:
            hook_path = Path(
                tm.ok(
                    u.Infra.git_capture(
                        repository_root, ("rev-parse", "--git-path", "hooks/pre-commit")
                    )
                )
            )
            if not hook_path.is_absolute():
                hook_path = repository_root / hook_path
            hook_paths.append(hook_path)
            tm.that(hook_path.exists(), eq=False)

        local = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "_builtin_setup_hooks"], cwd=workspace_root
            )
        )
        output = local.stdout + local.stderr
        tm.that(local.exit_code, eq=0, msg=output)
        tm.that(
            [line for line in output.splitlines() if "action=install" in line],
            eq=[
                f"setup hooks repository={repository_root} action=install"
                for repository_root in repository_roots
            ],
        )
        for index, (repository_root, hook_path) in enumerate(
            zip(repository_roots, hook_paths, strict=True)
        ):
            tm.that(hook_path.exists(), eq=True)
            tm.ok(u.Cli.run_checked([str(hook_path)], cwd=repository_root))
            marker = f"repository-{index}"
            tm.that((repository_root / f"{marker}.log").read_text(), eq=marker)

        preserved_member = repository_roots[1]
        preserved_hook = hook_paths[1].read_text(encoding="utf-8")
        tm.ok(
            u.Infra.git_capture(
                preserved_member, ("config", "core.hooksPath", ".operator-hooks")
            )
        )
        preserved = tm.ok(
            test_u.Tests.run_isolated_make(
                ["-C", str(workspace_root), "_builtin_setup_hooks"], cwd=workspace_root
            )
        )
        tm.that(preserved.exit_code, eq=0, msg=preserved.stdout + preserved.stderr)
        tm.that(preserved.stdout + preserved.stderr, has=str(preserved_member))
        tm.that(hook_paths[1].read_text(encoding="utf-8"), eq=preserved_hook)
        tm.that(
            preserved.stdout + preserved.stderr, has="action=skip reason=core.hooksPath"
        )

    def test_orchestrator_sanitizes_child_env_and_forwards_gates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        for project_name in project_names:
            _write_child_makefile(workspace_root / project_name, exit_code=0)
        hostile_root = tmp_path / "hostile-worktree"
        hostile_venv = hostile_root / ".venv"
        monkeypatch.chdir(workspace_root)
        monkeypatch.setenv("UV_PROJECT", str(hostile_root))
        monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(hostile_venv))
        monkeypatch.setenv("VIRTUAL_ENV", str(hostile_venv))
        monkeypatch.setenv("PYTHONPATH", str(hostile_root / "src"))

        result = FlextInfraOrchestratorService(verb="check").orchestrate(
            project_names, "check", make_args=("CHECK_GATES=lint,pyrefly",)
        )

        tm.ok(result, len=2)
        outputs: tuple[p.Cli.CommandOutput, ...] = tuple(result.unwrap())
        for output in outputs:
            child_log = Path(output.stdout).read_text(encoding="utf-8")
            tm.that(child_log, has="gates=lint,pyrefly")
            tm.that(child_log, lacks=str(hostile_root))

    def test_orchestrator_fail_fast_preserves_child_exit_and_skips_remaining(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        workspace_root, project_names = _write_workspace(tmp_path)
        _write_child_makefile(workspace_root / project_names[0], exit_code=23)
        _write_child_makefile(workspace_root / project_names[1], exit_code=0)
        monkeypatch.chdir(workspace_root)

        result = FlextInfraOrchestratorService(verb="test").orchestrate(
            project_names, "test", fail_fast=True
        )

        tm.fail(result, has="orchestration completed with failures: 1")
        first_log = (
            workspace_root
            / ".reports"
            / "workspace"
            / "test"
            / f"{project_names[0]}.log"
        )
        second_log = first_log.with_name(f"{project_names[1]}.log")
        tm.that(first_log.read_text(encoding="utf-8"), has="fail_fast=1")
        tm.that(second_log.exists(), eq=False)
