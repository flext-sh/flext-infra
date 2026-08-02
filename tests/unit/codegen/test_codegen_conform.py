"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.17 / agent: codex): this suite exercises only the
# public services and emitted artifacts; the former private catalog golden is gone.
from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from tests import u as test_u
from flext_infra import main as infra_main
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.services.cli_routes_codegen import CodegenRoutes
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm


def _conform_target(
    root: Path, repository: m.Infra.RepositoryRef, *, make_profile: c.Infra.MakeProfile
) -> m.Infra.RepositoryConformTarget:
    """Build a typed rendering target from the same provider SSOT as production."""
    provider: m.Infra.ProviderSpec = tm.ok(
        u.Infra.repository_provider(repository, config.Infra.codegen.providers)
    )
    return m.Infra.RepositoryConformTarget(
        repository=repository,
        root=root,
        make_profile=make_profile,
        beads_enabled=make_profile is c.Infra.MakeProfile.WORKSPACE_ROOT,
        canonical_project_name=repository.distribution,
        baseline_branch=provider.branch,
        ci_enabled=True,
        technical_branch_patterns=(
            config.Infra.codegen.branch_policy.technical_branch_patterns
        ),
        governed_branch_patterns=(
            config.Infra.codegen.branch_policy.governed_branch_patterns
        ),
    )


class TestCodegenConform:
    """Prove one SSOT for project creation and existing-tree conformance."""

    @pytest.mark.parametrize(
        ("kind", "name"),
        [
            (c.Infra.ProjectKind.EXTERNAL, "flext-demo"),
            (c.Infra.ProjectKind.INTERNAL, "flext-member"),
        ],
    )
    def test_new_project_is_complete_and_idempotent(
        self, tmp_path: Path, kind: c.Infra.ProjectKind, name: str
    ) -> None:
        root = tmp_path / kind.value
        service = FlextInfraCodegenProjectNew(
            name=name,
            kind=kind,
            output_root=root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        )
        first = service.execute()
        tm.ok(first)
        second = service.execute()
        tm.ok(second)
        tm.that(bool(first.value.written_files), eq=True)
        tm.that(second.value.written_files, eq=())
        makefile_plan = next(
            item
            for item in first.value.plan.files
            if item.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(
            makefile_plan.rendered,
            has=(
                f"{c.Infra.MakeProfile.WORKSPACE_MEMBER.value},"
                f"{c.Infra.MakeProfile.STANDALONE.value})"
            ),
        )
        tm.that(first.value.plan.request.root, eq=root.resolve())
        tm.that((root / "config" / "workspace.yaml").is_file(), eq=True)
        tm.that((root / "pyproject.toml").is_file(), eq=True)
        tm.that((root / ".env.example").is_file(), eq=True)
        package_name = name.replace("-", "_")
        pythonpath = os.pathsep.join(
            part
            for part in (str(root / "src"), os.environ.get("PYTHONPATH", ""))
            if part
        )
        process = u.Cli.capture(
            [sys.executable, "-m", package_name, "ping"],
            cwd=root,
            env={**os.environ, "PYTHONPATH": pythonpath},
            timeout=c.Infra.TIMEOUT_DEFAULT,
        )
        tm.ok(process)
        tm.that(process.value, eq="✅ pong")

    def test_generated_make_uses_unpinned_environment_uv(self, tmp_path: Path) -> None:
        """Generated Make delegates uv selection to the caller environment."""
        root = tmp_path / "flext-demo"
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        selected = u.Cli.run_raw(
            ["make", "-C", str(root), "--dry-run", "_builtin_status_diagnostics"],
            remove_env_keys=("MAKEFLAGS",),
        )

        selected_process: m.Cli.CommandOutput = tm.ok(selected)
        selected_output = selected_process.stdout + selected_process.stderr
        tm.that(selected_process.exit_code, eq=0)
        tm.that(selected_output, has="uv --version")
        tm.that(selected_output, lacks="uv@")
        tm.that(selected_output, lacks="UV_VERSION")
        makefile = (root / "Makefile").read_text(encoding="utf-8")
        tm.that(makefile, has="UV ?= uv")
        tm.that(makefile, lacks="UV_VERSION")
        tm.that(makefile, lacks="uv@")
        tm.that(makefile, lacks="mise exec")

    def test_existing_manifest_converges_to_identical_tree(
        self, tmp_path: Path, infra_git_repo: Path
    ) -> None:
        new_root = tmp_path / "new" / "flext-demo"
        existing_root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=new_root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        copied = u.Cli.files_copy_directory(new_root, existing_root, dirs_exist_ok=True)
        tm.ok(copied)
        tm.ok(
            u.Cli.atomic_write_text_file(
                existing_root / ".gitignore", "# committed managed drift\n"
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                existing_root / "Makefile", "# committed managed drift\n"
            )
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=existing_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed committed drift"], cwd=existing_root
            )
        )
        migrated = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=existing_root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.ok(migrated)
        new_tree = tuple(
            sorted(
                (path.relative_to(new_root).as_posix(), path.read_bytes())
                for path in new_root.rglob("*")
                if path.is_file()
            )
        )
        existing_tree = tuple(
            sorted(
                (path.relative_to(existing_root).as_posix(), path.read_bytes())
                for path in existing_root.rglob("*")
                if path.is_file()
                and ".git" not in path.relative_to(existing_root).parts
                and ".infra-baseline" not in path.relative_to(existing_root).parts
            )
        )
        tm.that(existing_tree, eq=new_tree)

    def test_manifestless_existing_root_plans_artifacts_without_project_spec(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        repository = test_u.Tests.repository_ref(config.Infra.name)
        local_repository = repository.model_copy(update={"path": Path()})
        dist = repository.distribution
        create_only = {
            "LICENSE": "existing license\n",
            "README.md": "# Existing repository\n",
            "custom.mk": "_custom_status_diagnostics:\n\t@true\n",
        }
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "pyproject.toml",
                f'[project]\nname = "{dist}"\nversion = "0.12.0.dev0"\n'
                'requires-python = ">=3.13,<3.14"\n',
            )
        )
        package_init = root / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        for relative, content in create_only.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed manifest-less tree"], cwd=root
            )
        )

        derived: m.Infra.WorkspaceSpec = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root)
        )
        tm.that(derived.repository, eq=local_repository)
        tm.that(derived.project, eq=None)

        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        initial_plan: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(workspace_root=root).plan(request)
        )
        plans = {
            file.path.relative_to(root).as_posix(): file for file in initial_plan.files
        }
        env_plan = plans[".env.example"]
        tm.that(env_plan.owner, eq="codegen")
        tm.that(env_plan.policy, eq="create-only")
        tm.that(env_plan.changed, eq=False)
        tm.that(env_plan.blocked, eq=False)
        tm.that(env_plan.current_sha256, eq="")
        tm.that((root / ".env.example").exists(), eq=False)
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.that(plans[required].changed, eq=True)

        applied = FlextInfraCodegenConform.execute_request(request)
        tm.ok(applied)
        for relative, content in create_only.items():
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        tm.that((root / "Makefile").is_file(), eq=True)
        tm.that((root / ".mise.toml").is_file(), eq=True)
        tm.that((root / ".python-version").is_file(), eq=True)
        tm.that((root / ".gitignore").is_file(), eq=True)
        tm.that((root / ".env.example").exists(), eq=False)
        tm.that(root / ".env.example" in applied.value.written_files, eq=False)

        fixed_point = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(fixed_point)
        tm.that(fixed_point.value.written_files, eq=())

    def test_workspace_uv_plan_owns_root_lock_and_editable_repositories(
        self, tmp_path: Path
    ) -> None:
        """Keep workspace setup data complete without Make-side re-derivation."""
        root_repository = test_u.Tests.repository_ref("flext")
        member = test_u.Tests.repository_ref(
            "flext-core", role=c.Infra.RepositoryRole.WORKSPACE_MEMBER
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="flext",
            repository=root_repository,
            project=m.Infra.ProjectSpec(
                package_name="flext",
                class_stem="Flext",
                namespace="Flext",
                constant_name="flext",
                namespace_attribute="flext",
                alias="flext",
                environment_prefix="FLEXT_",
                description="FLEXT workspace",
                version="0.12.0.dev0",
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_cli",
                homepage="https://github.com/flext-sh/flext",
                documentation="https://github.com/flext-sh/flext",
                workspace_root_rel=".",
                year=2026,
            ),
            members=(member,),
        )
        root = tmp_path / "flext"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(
            workspace_root=root, request=request, initial_workspace=workspace
        ).plan(request)
        tm.ok(planned)
        environment = planned.value.uv_environments[0]
        tm.that(environment.environment_root, eq=root.resolve())
        tm.that(environment.lock_path, eq=root.resolve() / "uv.lock")
        tm.that(environment.groups, eq=("dev", "codegen", "workspace"))
        tm.that(
            tuple(item.name for item in environment.editable_repositories),
            eq=("flext-core",),
        )

    def test_workspace_root_catalog_profile_preserves_platform_coverage(
        self, tmp_path: Path
    ) -> None:
        """Route an arbitrary workspace root through its typed catalog profile."""
        provider = config.Infra.codegen.providers[0]
        repository = test_u.Tests.repository_ref("arbitrary-root").model_copy(
            update={
                "name": "arbitrary-root",
                "distribution": "arbitrary-root",
                "url": f"{provider.base_url}/arbitrary-root.git",
                "path": Path(),
                "role": c.Infra.RepositoryRole.WORKSPACE_ROOT,
                "profile": c.Infra.MakeProfile.WORKSPACE_ROOT,
                "package": False,
                "editable": False,
            }
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="arbitrary-root",
            repository=repository,
            project=m.Infra.ProjectSpec(
                package_name="arbitrary_root",
                class_stem="ArbitraryRoot",
                namespace="ArbitraryRoot",
                constant_name="arbitrary-root",
                namespace_attribute="arbitrary_root",
                alias="arbitrary_root",
                environment_prefix="ARBITRARY_ROOT_",
                description="Arbitrary workspace root",
                version="0.1.0",
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_cli",
                homepage=f"{provider.base_url}/arbitrary-root",
                documentation=f"{provider.base_url}/arbitrary-root",
                workspace_root_rel=".",
                year=2026,
            ),
        )
        root = tmp_path / "arbitrary-root"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConform(
            workspace_root=root, request=request, initial_workspace=workspace
        )

        first: m.Infra.CodegenPlan = tm.ok(service.plan(request))
        second: m.Infra.CodegenPlan = tm.ok(service.plan(request))
        first_pyproject = next(
            item for item in first.files if item.path.name == c.Infra.PYPROJECT_FILENAME
        )
        second_pyproject = next(
            item
            for item in second.files
            if item.path.name == c.Infra.PYPROJECT_FILENAME
        )
        rendered_tooling = tomllib.loads(first_pyproject.rendered)["tool"]
        report = rendered_tooling["coverage"]["report"]
        addopts = set(rendered_tooling["pytest"]["ini_options"]["addopts"])
        pytest_policy = config.Infra.tooling.tools.pytest

        tm.that(second_pyproject.rendered, eq=first_pyproject.rendered)
        tm.that(addopts, has=f"--timeout={pytest_policy.case_timeout_seconds}")
        tm.that(addopts, lacks="--session-timeout")
        tm.that(addopts >= set(pytest_policy.standard_addopts), eq=True)
        tm.that(
            report["fail_under"],
            eq=config.Infra.tooling.tools.coverage.fail_under.platform,
        )

    def test_make_context_accepts_manifest_without_project_metadata(
        self, tmp_path: Path
    ) -> None:
        """Build Make context from repository-owned data alone."""
        repository = test_u.Tests.repository_ref("consumer")
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="consumer",
            repository=repository,
        )
        target = _conform_target(
            tmp_path, repository, make_profile=c.Infra.MakeProfile.STANDALONE
        )
        tooling_runtime: m.Infra.ToolingRuntimeContext = tm.ok(
            FlextInfraPyprojectModernizer(
                workspace_root=tmp_path, skip_check=True
            ).resolve_tooling_context(
                project_name=repository.distribution,
                package_name=repository.distribution.replace("-", "_"),
                path=tmp_path / "pyproject.toml",
                declared_python_dirs=("src",),
            )
        )
        context = FlextInfraCodegenConform.make_render_context(
            repository,
            target,
            workspace,
            config.Infra.codegen,
            tooling_runtime=tooling_runtime,
        )
        rendered: m.Infra.MakeRenderContext = tm.ok(context)
        tm.that(isinstance(rendered, m.Infra.ProjectRenderContext), eq=False)
        tm.that(rendered.workspace_root_rel, eq=".")
        tm.that(rendered.make, eq=config.Infra.codegen.make)

    def test_make_context_round_trips_mutated_dispatch_environment(
        self, tmp_path: Path
    ) -> None:
        """Rendering and Make execution consume arbitrary valid registry tokens."""
        make_payload = config.Infra.codegen.make.model_dump(
            mode="python", exclude_computed_fields=True
        )
        make_payload.update({
            "selector": "ACTION",
            "apply_variable": "WRITE",
            "apply_value": "ENABLE",
            "apply_absent_value": "DISABLED",
            "ci": {"variable": "AUTOMATION", "value": "ON"},
        })
        make = m.Infra.MakeSpec.model_validate(make_payload)
        codegen = config.Infra.codegen.model_copy(update={"make": make})
        root = tmp_path / "workspace"
        root.mkdir()
        repository = test_u.Tests.repository_ref(
            "fixture-workspace", role=c.Infra.RepositoryRole.WORKSPACE_ROOT
        )
        member = test_u.Tests.repository_ref(
            "fixture-member",
            path=Path("fixture-member"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            members=(member,),
        )
        tooling_runtime = tm.ok(
            FlextInfraPyprojectModernizer(
                workspace_root=root, skip_check=True
            ).resolve_tooling_context(
                project_name=repository.distribution,
                package_name=repository.distribution.replace("-", "_"),
                path=root / c.Infra.PYPROJECT_FILENAME,
                declared_python_dirs=(
                    config.Infra.tooling.tools.pyrefly.path_rules.source_dir,
                ),
            )
        )
        context = tm.ok(
            FlextInfraCodegenConform.make_render_context(
                repository,
                _conform_target(
                    root, repository, make_profile=c.Infra.MakeProfile.WORKSPACE_ROOT
                ),
                workspace,
                codegen,
                tooling_runtime=tooling_runtime,
            )
        )
        render_context = m.Infra.MakefileRenderSpec(
            pytest=context.pytest,
            dist=context.dist,
            infra_cli=context.infra_cli,
            make_profile=context.make_profile,
            setup_scope=context.setup_scope,
            workspace_members=context.workspace_members,
            workspace_repositories=context.workspace_repositories,
            workspace_gitlinks=context.workspace_gitlinks,
            uv_link_mode=context.uv_link_mode,
            make=context.make,
            extra_verbs=context.extra_verbs,
            script_dispatch=context.script_dispatch,
            makefile_custom_include=context.makefile_custom_include,
            workspace_cli_group=context.workspace_cli_group,
            project_selection_conflict_error=context.project_selection_conflict_error,
            mypy_memory_limit_mb=context.mypy_memory_limit_mb,
            mypy_timeout_seconds=context.mypy_timeout_seconds,
            mypy_timeout_exit_code=context.mypy_timeout_exit_code,
            mypy_signal_exit_offset=context.mypy_signal_exit_offset,
            prlimit_command=context.prlimit_command,
            prlimit_address_space_option=context.prlimit_address_space_option,
            timeout_command=context.timeout_command,
            timeout_kill_after_seconds=context.timeout_kill_after_seconds,
            pytest_process_timeout_seconds=(
                config.Infra.tooling.tools.pytest.process_timeout_seconds
            ),
        )
        templates = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
        )
        rendered = tm.ok(
            u.Cli.template_render(templates / "Makefile.j2", render_context)
        )
        (root / c.Infra.MAKEFILE_FILENAME).write_text(rendered, encoding="utf-8")

        help_process = tm.ok(test_u.Tests.run_isolated_make(["help"], cwd=root))
        tm.that(
            help_process.exit_code, eq=0, msg=help_process.stdout + help_process.stderr
        )
        tm.that(help_process.stdout, has=f"{make.apply_variable}={make.apply_value}")
        tm.that(
            help_process.stdout,
            lacks=(
                f"{config.Infra.codegen.make.apply_variable}="
                f"{config.Infra.codegen.make.apply_value}"
            ),
        )

        invocation_log = root / "public-dispatch.log"
        test_u.Tests.write_executable(
            root / c.Infra.VENV_BIN_REL / c.Infra.PYTHON,
            (
                "#!/bin/sh\n"
                "verb=''\nselector=''\napply=''\nmakefile=''\nprevious=''\n"
                'for argument in "$@"; do\n'
                '  if [ "$previous" = "--verb" ]; then verb="$argument"; fi\n'
                '  if [ "$previous" = "--selector-value" ]; then '
                'selector="$argument"; fi\n'
                '  if [ "$previous" = "--apply-token" ]; then '
                'apply="$argument"; fi\n'
                '  if [ "$previous" = "--makefile" ]; then makefile="$argument"; fi\n'
                '  previous="$argument"\n'
                "done\n"
                'if [ -n "$verb" ]; then\n'
                '  exec make --no-print-directory -f "$makefile" '
                '"_serialized_${verb}" '
                f'"{make.selector}=$selector" "{make.apply_variable}=$apply"\n'
                "fi\n"
                f'printf "%s\\n" "$*" >> "{invocation_log}"\n'
            ),
        )
        fake_uv = root / "bin" / "uv"
        test_u.Tests.write_executable(fake_uv, "#!/bin/sh\nexit 0\n")
        public_dispatch = tm.ok(
            test_u.Tests.run_isolated_make(
                [
                    "--no-print-directory",
                    "worktree",
                    f"{make.selector}=list",
                    f"UV={fake_uv}",
                ],
                cwd=root,
            )
        )
        tm.that(
            public_dispatch.exit_code,
            eq=0,
            msg=public_dispatch.stdout + public_dispatch.stderr,
        )
        tm.that(
            invocation_log.read_text(encoding="utf-8"),
            has=["workspace worktree", "--operation list"],
        )

        pre_commit = tm.ok(
            u.Cli.template_render(
                templates / ".pre-commit-config.yaml.j2", render_context
            )
        )
        entry = pre_commit.split("'", 2)[1]
        expected_commands = [
            f"make {step.verb}"
            + (f" {make.apply_variable}={make.apply_value}" if step.apply else "")
            for step in make.workflow
            if "pre_commit" in step.contexts
        ]
        tm.that(entry.split(" && "), eq=expected_commands)
        tm.that(entry, lacks=f"{make.ci.variable}={make.ci.value}")
        tm.that(entry, lacks=["make gen", "conform"])

        context_payload = render_context.model_dump(
            mode="python", exclude_computed_fields=True
        )
        context_payload["pytest"] = render_context.pytest.model_dump(
            mode="python", by_alias=True
        )
        context_payload["extra_verbs"] = (
            make
            .verbs[0]
            .model_copy(update={"dispatch": "script"})
            .model_dump(mode="python"),
        )
        context_payload["script_dispatch"] = {
            "dispatcher": "scripts/dispatch.py",
            "roots": ("scripts",),
        }
        with pytest.raises(ValueError, match="collide with canonical verbs"):
            m.Infra.MakefileRenderSpec.model_validate(context_payload)

    def test_public_cli_routes_check_and_apply_to_one_handler(
        self, infra_git_repo: Path
    ) -> None:
        """Execute each public mode without changing an already conform tree."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed generated project"], cwd=root
            )
        )
        snapshot_excludes = config.Infra.codegen.make.serialization.snapshot_excludes
        before: m.Infra.WorkspaceFingerprint = tm.ok(
            u.Infra.workspace_fingerprint(root, excluded_paths=snapshot_excludes)
        )
        route = next(
            route
            for route in CodegenRoutes.codegen_routes[c.Infra.CLI_GROUP_CODEGEN]
            if route.name == "conform"
        )
        for mode in c.Infra.CodegenConformMode:
            request = m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=mode,
            )
            tm.ok(route.handler(request))
        after: m.Infra.WorkspaceFingerprint = tm.ok(
            u.Infra.workspace_fingerprint(root, excluded_paths=snapshot_excludes)
        )
        tm.that(after.digest, eq=before.digest)
        tm.that(u.Infra.workspace_fingerprint_changes(before, after), eq=())

    def test_dependency_surface_excludes_unowned_managed_files(
        self, infra_git_repo: Path
    ) -> None:
        """Plan only dependency metadata when another managed surface is invalid."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk", ".PHONY: public-handler\npublic-handler:\n\t@true\n"
            )
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed generated project"], cwd=root
            )
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.DEPENDENCIES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(workspace_root=root, request=request).plan(
            request
        )
        tm.ok(planned)
        tm.that(
            tuple(file.path.name for file in planned.value.files),
            eq=("pyproject.toml",),
        )
        exit_code = infra_main([
            "codegen",
            "conform",
            "--root",
            str(root),
            "--what",
            "dependencies",
            "--scope",
            "self",
            "--mode",
            "check",
        ])
        tm.that(exit_code, eq=0)

    def test_invalid_public_custom_make_fails_without_side_effects(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        content = ".PHONY: public-handler\npublic-handler:\n\t@true\n"
        tm.ok(u.Cli.atomic_write_text_file(custom, content))
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.fail(result)
        rejection = Path(f"{custom}.rej")
        tm.that(
            result.error or "", has="custom.mk line 1 is not a private custom handler"
        )
        tm.that(rejection.exists(), eq=False)
        tm.that(custom.read_text(encoding="utf-8"), eq=content)

    def test_valid_private_custom_make_has_no_rejection(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        tm.ok(
            u.Cli.atomic_write_text_file(
                custom,
                (
                    ".PHONY: \\\n"
                    "\tpre-check-demo \\\n"
                    "\tpost-run-demo\n"
                    "pre-check-demo:\n\t@true\n"
                    "post-run-demo:\n\t@true\n"
                ),
            )
        )
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(result)
        tm.that("WARN:" in capsys.readouterr().out, eq=False)
        tm.that(Path(f"{custom}.rej").exists(), eq=False)

    def test_custom_make_rejects_unterminated_phony_continuation(self) -> None:
        """Fail closed when a multiline private-handler declaration is truncated."""
        policy = config.Infra.codegen.make.custom_handler_policies[
            c.Infra.MakeProfile.STANDALONE
        ]

        result = FlextInfraCodegenConform.validate_custom_make(
            ".PHONY: \\\n\tpre-check-demo \\",
            policy,
            allowed_verbs=tuple(verb.name for verb in config.Infra.codegen.make.verbs),
        )

        tm.fail(result, has="unterminated .PHONY continuation")

    def test_scaffold_make_help_documents_and_lists_custom_hooks(
        self, infra_git_repo: Path
    ) -> None:
        """Scaffold help documents the hook contract and lists custom.mk hooks."""
        root = infra_git_repo
        tm.ok(
            FlextInfraCodegenProjectNew(
                name="flext-demo",
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
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: pre-check post-test-all _custom_check_myscan\n"
                "pre-check:\n\t@true\n"
                "post-test-all:\n\t@true\n"
                "_custom_check_myscan:\n\t@true\n",
            )
        )
        outcome = u.Cli.run_raw(["make", "-C", str(root), "help"])
        output: m.Cli.CommandOutput = tm.ok(outcome)
        tm.that(output.exit_code, eq=0)
        tm.that(
            output.stdout,
            has=[
                "Custom hooks (custom.mk):",
                "pre-<verb>",
                "pre-check",
                "post-test-all",
                "_custom_check_myscan",
            ],
        )

    def test_scaffold_make_runs_pre_and_post_verb_hooks_in_order(
        self, infra_git_repo: Path
    ) -> None:
        """Generated _dispatch runs pre-<verb>, handler, post-<verb> in order."""
        root = infra_git_repo
        tm.ok(
            FlextInfraCodegenProjectNew(
                name="flext-demo",
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
        )
        # The private target is the dispatcher entry point invoked while the
        # public verb holds the serialization lock. Exercising it directly
        # keeps this test focused on hook ordering and independent of bootstrap.
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: pre-check post-check _custom_check_probe\n"
                "pre-check:\n\t@echo HOOK_PRE\n"
                "_custom_check_probe:\n\t@echo HANDLER_BODY\n"
                "post-check:\n\t@echo HOOK_POST\n",
            )
        )
        outcome = u.Cli.run_raw([
            "make",
            "-C",
            str(root),
            "_serialized_check",
            f"{config.Infra.codegen.make.selector}=probe",
        ])
        output: m.Cli.CommandOutput = tm.ok(outcome)
        tm.that(output.exit_code, eq=0)
        combined = output.stdout + output.stderr
        pre_at = combined.find("HOOK_PRE")
        body_at = combined.find("HANDLER_BODY")
        post_at = combined.find("HOOK_POST")
        tm.that(pre_at >= 0 and body_at >= 0 and post_at >= 0, eq=True)
        tm.that(pre_at < body_at, eq=True)
        tm.that(body_at < post_at, eq=True)

    def test_custom_make_accepts_pre_post_verb_hooks(
        self, infra_git_repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """custom.mk may append pre/post verb hooks (verb-wide and WHAT-scoped)."""
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        tm.ok(
            u.Cli.atomic_write_text_file(
                custom,
                ".PHONY: pre-check post-check pre-test-all post-test-all\n"
                "pre-check:\n\t@true\n"
                "post-check:\n\t@true\n"
                "pre-test-all:\n\t@true\n"
                "post-test-all:\n\t@true\n",
            )
        )
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(result)
        tm.that("WARN:" in capsys.readouterr().out, eq=False)
        tm.that(Path(f"{custom}.rej").exists(), eq=False)

    def test_non_regular_custom_make_remains_fatal(self, infra_git_repo: Path) -> None:
        root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
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
        tm.ok(u.Cli.files_delete(root / "custom.mk"))
        (root / "custom.mk").mkdir()
        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.fail(result)
        tm.that(result.error, has="not a regular file")
        tm.that(result.error, has=str(root / "custom.mk"))


class TestScriptDispatchMakefile:
    """Prove per-repo extra verbs and script-dispatch WHAT normalization."""

    @staticmethod
    def _render_root_makefile(
        tmp_path: Path,
        *,
        extra_verbs: tuple[m.Infra.MakeVerbSpec, ...],
        script_dispatch: m.Infra.ScriptDispatchSpec | None,
    ) -> str:
        # mro-4gbp: the engine is consumer-agnostic, so this fixture models a
        # neutral downstream root and takes its provider from the engine's own
        # configured provider catalog instead of naming a real consumer.
        provider = config.Infra.codegen.providers[0]
        root_repository = m.Infra.RepositoryRef(
            name="demo-root",
            distribution="demo-root",
            url=f"{provider.base_url}/demo-root.git",
            path=Path(),
            # Script dispatch is a generic capability: exercise it on standalone.
            role=c.Infra.RepositoryRole.STANDALONE,
            provider=provider.name,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
            extra_verbs=extra_verbs,
            script_dispatch=script_dispatch,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="demo-root",
            repository=root_repository,
            project=m.Infra.ProjectSpec(
                package_name="demo_root",
                class_stem="DemoRoot",
                namespace="DemoRoot",
                constant_name="demo-root",
                namespace_attribute="demo_root",
                alias="demo_root",
                environment_prefix="DEMO_",
                description="Demo workspace",
                version="0.2.0",
                license="MIT",
                author_name="Demo",
                author_email="devops@example.com",
                upstream="flext_cli",
                homepage=f"{provider.base_url}/demo-root",
                documentation=f"{provider.base_url}/demo-root",
                workspace_root_rel=".",
                year=2026,
            ),
            members=(),
        )
        root = tmp_path / "demo-root"
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(
            workspace_root=root, request=request, initial_workspace=workspace
        ).plan(request)
        plan: m.Infra.CodegenPlan = tm.ok(planned)
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        rendered: str = makefile.rendered
        return rendered

    def test_script_dispatch_repo_routes_extra_verbs_and_normalizes_what(
        self, tmp_path: Path
    ) -> None:
        """Extra verbs join PUBLIC_VERBS and WHAT hyphens map to script stems."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="incidente",
                    default_what="all",
                    dispatch="script",
                    handlers={"all": {"target": "all"}},
                ),
                m.Infra.MakeVerbSpec(
                    name="charts",
                    default_what="all",
                    dispatch="script",
                    handlers={"all": {"target": "all"}},
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
        )
        # Extra verbs are public targets the dispatcher can reach.
        tm.that("incidente" in rendered, eq=True)
        tm.that("charts" in rendered, eq=True)
        # The generated dispatch normalizes hyphenated WHAT to the module stem.
        tm.that("tr '-' '_'" in rendered, eq=True)
        # It forwards to the declared dispatcher through uv, not a raw builtin.
        tm.that("scripts/dispatch.py" in rendered, eq=True)
        # Existence check spans every declared script root.
        tm.that("apps/demo-app/scripts" in rendered, eq=True)
        # REGRESSION (fork-bomb): every line of the single-recipe _dispatch shell
        # command must continue with a trailing backslash. A blank/unterminated
        # line splits the recipe, drops $$what/$$builtin, and recurses into the
        # default goal. Verify continuity across the whole define body.
        body = rendered.split("define _dispatch", 1)[1].split("endef", 1)[0]
        recipe = [ln for ln in body.splitlines() if ln.startswith("\t")]
        broken = [ln for ln in recipe[:-1] if not ln.rstrip().endswith("\\")]
        tm.that(broken, eq=[])

    def test_repo_without_script_dispatch_omits_script_routing(
        self, tmp_path: Path
    ) -> None:
        """A repo with no script dispatch omits every script-routing projection."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        # No script routing leaks into non-opted-in repositories.
        tm.that("tr '-' '_'" in rendered, eq=False)
        tm.that("scripts/dispatch.py" in rendered, eq=False)

    def test_gen_replaces_codegen_as_the_single_conform_verb(
        self, tmp_path: Path
    ) -> None:
        """``make gen`` is THE conform verb; ``codegen`` no longer exists.

        The convergence spine (mro-e9j0.6 C7) fuses codegen+conform under the
        single short ``gen`` verb: one verb, one meaning. The old ``codegen``
        Make verb is fully replaced — config, serialization, fixed points,
        rendered handlers, and the regeneration header all speak ``gen``.
        """
        make_config = config.Infra.codegen.make
        verb_names = {verb.name for verb in make_config.verbs}
        tm.that("gen" in verb_names, eq=True)
        tm.that("codegen" in verb_names, eq=False)
        gen = next(verb for verb in make_config.verbs if verb.name == "gen")
        tm.that(gen.default_what, eq="all")
        tm.that(gen.handlers["all"].mutating, eq=True)
        # Serialization follows the rename: gen is serialized, codegen gone.
        tm.that("gen" in make_config.serialized_verbs, eq=True)
        tm.that("codegen" in make_config.serialized_verbs, eq=False)
        tm.that("gen" in make_config.mutation_verbs, eq=True)
        tm.that("codegen" in make_config.mutation_verbs, eq=False)
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(" gen" in public_line, eq=True)
        tm.that(" codegen" in public_line, eq=False)
        tm.that("_DEFAULT_gen := all" in rendered, eq=True)
        tm.that("_builtin_gen_check:" in rendered, eq=True)
        tm.that("_builtin_gen_apply:" in rendered, eq=True)
        tm.that("_builtin_codegen_check" in rendered, eq=False)
        tm.that("_builtin_codegen_apply" in rendered, eq=False)
        tm.that("_BUILTIN_HANDLERS" in rendered, eq=False)
        tm.that(
            "_HANDLER_MAP_gen := all:all check:check apply:apply" in rendered, eq=True
        )
        # Both handlers drive the conform engine (CLI namespace is unchanged).
        gen_check_body = rendered.split("_builtin_gen_check:", 1)[1].split("\n\n", 1)[0]
        tm.that("codegen conform" in gen_check_body, eq=True)
        tm.that("--mode check" in gen_check_body, eq=True)
        tm.that(gen_check_body.count("deps modernize"), eq=1)
        tm.that(gen_check_body.count("codegen conform"), eq=1)
        tm.that(
            gen_check_body.index("deps modernize")
            < gen_check_body.index("codegen conform"),
            eq=True,
        )
        tm.that(gen_check_body, lacks="deps extra-paths")
        gen_apply_body = rendered.split("_builtin_gen_apply:", 1)[1].split("\n\n", 1)[0]
        tm.that("codegen conform" in gen_apply_body, eq=True)
        tm.that("--mode apply" in gen_apply_body, eq=True)
        tm.that("_require_apply" in gen_apply_body, eq=True)
        tm.that(gen_apply_body.count("deps modernize"), eq=1)
        tm.that(gen_apply_body.count("codegen conform"), eq=1)
        tm.that(
            gen_apply_body.index("deps modernize")
            < gen_apply_body.index("codegen conform"),
            eq=True,
        )
        tm.that(gen_apply_body, lacks="deps extra-paths")
        # The regeneration contract published on every projection speaks gen.
        make = config.Infra.codegen.make
        tm.that(
            (f"# @flext-regenerate: make gen {make.apply_variable}={make.apply_value}")
            in rendered,
            eq=True,
        )
        # The handwritten surface only wraps registry-owned handlers.
        for policy in config.Infra.codegen.make.custom_handler_policies.values():
            tm.that(policy.allow_public_targets, eq=False)

    # NOTE (mro-4gbp): a test asserting a downstream consumer's verbs from this
    # engine's catalog was removed. The engine is consumer-agnostic: a consumer
    # declares extra_verbs/script_dispatch in its OWN config/workspace.yaml. The
    # generic capability stays covered by the fixture-driven cases below.
    def test_script_dispatch_adds_scripts_to_lint_and_type_paths(
        self, tmp_path: Path
    ) -> None:
        """Opted-in repos scan scripts alongside src and tests."""
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verbs=(
                m.Infra.MakeVerbSpec(
                    name="charts",
                    default_what="all",
                    dispatch="script",
                    handlers={"all": {"target": "all"}},
                ),
                m.Infra.MakeVerbSpec(
                    name="chart-release",
                    default_what="all",
                    dispatch="script",
                    handlers={"all": {"target": "all"}},
                ),
                m.Infra.MakeVerbSpec(
                    name="bead",
                    default_what="all",
                    dispatch="script",
                    handlers={"all": {"target": "all"}},
                ),
            ),
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py", roots=("scripts",)
            ),
        )
        tm.that(
            "RUFF_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests $(PROJECT_ROOT)/scripts"
            in rendered,
            eq=True,
        )
        tm.that(
            "MYPY_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests $(PROJECT_ROOT)/scripts"
            in rendered,
            eq=True,
        )

    def test_repo_without_script_dispatch_retains_canonical_lint_and_type_paths(
        self, tmp_path: Path
    ) -> None:
        """A repo without script dispatch keeps src/tests paths and excludes scripts."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verbs=(), script_dispatch=None
        )
        tm.that(
            "RUFF_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests" in rendered,
            eq=True,
        )
        tm.that(
            "MYPY_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests" in rendered,
            eq=True,
        )
        tm.that("$(PROJECT_ROOT)/scripts" in rendered, eq=False)


__all__: list[str] = []
