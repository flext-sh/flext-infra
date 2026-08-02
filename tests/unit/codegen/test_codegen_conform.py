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
from flext_infra import main as infra_main
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.codegen.publisher import FlextInfraCodegenPublisher
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.services.cli_routes_codegen import CodegenRoutes
from flext_tests import tm
from tests import u as test_u


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
        governed_branch_patterns=(config.Infra.codegen.governed_branch_patterns),
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
        make_engine_plan = next(
            item
            for item in first.value.plan.files
            if item.path.relative_to(root).as_posix()
            == config.Infra.codegen.surfaces.make_engine_path
        )
        tm.that(
            make_engine_plan.rendered,
            has=f"MAKE_PROFILE := {c.Infra.MakeProfile.STANDALONE.value}",
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
        request = m.Infra.CodegenConformRequest(
            root=existing_root, scope=c.Infra.CodegenConformScope.SELF
        )
        planner = FlextInfraCodegenConform(
            workspace_root=existing_root, projection_operation="generate"
        )
        plan: m.Infra.CodegenPlan = tm.ok(planner.plan(request))
        tm.ok(planner.validate_plan(plan, allow_missing_beads=True))
        tm.ok(FlextInfraCodegenPublisher.apply(plan))
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
            root=root, scope=c.Infra.CodegenConformScope.SELF
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
                workspace_root=tmp_path
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
            make=tm.ok(
                u.Infra.repository_make_spec(config.Infra.codegen.make, repository)
            ),
            tooling_runtime=tooling_runtime,
        )
        rendered: m.Infra.MakeRenderContext = tm.ok(context)
        tm.that(isinstance(rendered, m.Infra.MakeRenderContext), eq=True)
        tm.that(isinstance(rendered, m.Infra.ProjectRenderContext), eq=False)
        tm.that(rendered.workspace_root_rel, eq=".")
        # A standalone consumer declares no flext-infra member, so the
        # reference is derived from the provider contract. The generated
        # Makefile consumes exactly the distribution and the URL (the
        # bootstrap requirement), which is what this asserts; the topology
        # role of a derived reference is not part of that contract.
        tm.that(rendered.infra_repository.distribution, eq=config.Infra.name)
        tm.that(
            rendered.infra_repository.url,
            eq=f"{config.Infra.codegen.providers[0].base_url.rstrip('/')}"
            f"/{config.Infra.name}.git",
        )
        tm.that(rendered.infra_source_root_rel, eq=None)

    def test_make_context_resolves_attached_infra_member_from_workspace(
        self, tmp_path: Path
    ) -> None:
        """An attached member bootstraps from its declared local checkout."""
        workspace_repository = test_u.Tests.repository_ref("workspace-root-fixture")
        infra_repository = test_u.Tests.repository_ref(
            config.Infra.name,
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            path=Path(config.Infra.name),
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=workspace_repository.name,
            repository=workspace_repository,
            members=(infra_repository,),
        )
        target = _conform_target(
            tmp_path,
            workspace_repository,
            make_profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
        )
        tooling_runtime: m.Infra.ToolingRuntimeContext = tm.ok(
            FlextInfraPyprojectModernizer(
                workspace_root=tmp_path
            ).resolve_tooling_context(
                project_name=infra_repository.distribution,
                package_name=infra_repository.distribution.replace("-", "_"),
                path=tmp_path / infra_repository.path / "pyproject.toml",
                declared_python_dirs=("src",),
            )
        )

        rendered: m.Infra.MakeRenderContext = tm.ok(
            FlextInfraCodegenConform.make_render_context(
                workspace_repository,
                target,
                workspace,
                config.Infra.codegen,
                make=tm.ok(
                    u.Infra.repository_make_spec(
                        config.Infra.codegen.make, workspace_repository
                    )
                ),
                tooling_runtime=tooling_runtime,
            )
        )

        tm.that(rendered.infra_source_root_rel, eq=infra_repository.path.as_posix())

    def test_public_cli_routes_read_only_conform_handler(
        self, infra_git_repo: Path
    ) -> None:
        """The public conform route checks without changing a conform tree."""
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
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.ALL,
            scope=c.Infra.CodegenConformScope.SELF,
        )
        tm.ok(route.handler(request))
        after: m.Infra.WorkspaceFingerprint = tm.ok(
            u.Infra.workspace_fingerprint(root, excluded_paths=snapshot_excludes)
        )
        tm.that(after.digest, eq=before.digest)
        tm.that(u.Infra.workspace_fingerprint_changes(before, after), eq=())

    def test_dependency_surface_excludes_unowned_surfaces(
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
        )
        planned: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(workspace_root=root, request=request).plan(request)
        )
        tm.that(tuple(file.path.name for file in planned.files), eq=("pyproject.toml",))
        exit_code = infra_main([
            "codegen",
            "conform",
            "--root",
            str(root),
            "--what",
            "dependencies",
            "--scope",
            "self",
        ])
        tm.that(exit_code, eq=0)


class TestScriptDispatchMakefile:
    """Prove per-repository script verbs extend the typed Make handler graph."""

    @staticmethod
    def _render_root_makefile(
        tmp_path: Path,
        *,
        extra_verb_names: tuple[str, ...],
        script_dispatch: m.Infra.ScriptDispatchSpec | None,
    ) -> str:
        # mro-4gbp: the engine is consumer-agnostic, so this fixture models a
        # neutral downstream root and takes its provider from the engine's own
        # configured provider catalog instead of naming a real consumer.
        provider = config.Infra.codegen.providers[0]
        script_operation = next(
            operation
            for operation in config.Infra.codegen.make.operations
            if operation.executor == "script"
        )
        script_handler = (
            m.Infra.MakeHandlerSpec(
                what="all", default=True, apply_policy="required", apply_default=True
            )
            if script_operation.mutation == "apply"
            else m.Infra.MakeHandlerSpec(what="all", default=True)
        )
        extra_verbs = tuple(
            m.Infra.MakeVerbSpec(
                name=name, operation=script_operation.name, handlers=(script_handler,)
            )
            for name in extra_verb_names
        )
        root_repository = m.Infra.RepositoryRef(
            name="demo-root",
            distribution="demo-root",
            url=f"{provider.base_url}/demo-root.git",
            path=Path(),
            # Script dispatch is a generic capability: exercise it on standalone.
            role=c.Infra.RepositoryRole.STANDALONE,
            provider=provider.name,
            branch=provider.branch,
            checkout=c.Infra.CheckoutKind.INDEPENDENT,
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
            root=root, scope=c.Infra.CodegenConformScope.SELF
        )
        planned = FlextInfraCodegenConform(
            workspace_root=root,
            request=request,
            initial_workspace=workspace,
            projection_operation="generate",
        ).plan(request)
        plan: m.Infra.CodegenPlan = tm.ok(planned)
        makefile = next(
            file
            for file in plan.files
            if file.path.relative_to(root).as_posix()
            == config.Infra.codegen.surfaces.make_engine_path
        )
        rendered: str = makefile.rendered
        return rendered

    def test_script_dispatch_repo_routes_extra_verbs_through_handler_graph(
        self, tmp_path: Path
    ) -> None:
        """Extra verbs join the sole public runtime-dispatched Make graph."""
        extra_verb_names = ("incident", "charts")
        rendered = self._render_root_makefile(
            tmp_path,
            extra_verb_names=extra_verb_names,
            script_dispatch=m.Infra.ScriptDispatchSpec(
                dispatcher="scripts/dispatch.py",
                roots=("scripts", "apps/demo-app/scripts"),
            ),
        )
        public_line = next(
            line for line in rendered.splitlines() if line.startswith("PUBLIC_VERBS :=")
        )
        tm.that(public_line, has=extra_verb_names)
        tm.that(rendered.count("workspace serialize-make"), eq=1)
        tm.that(rendered, lacks="scripts/dispatch.py")

    def test_repo_without_script_dispatch_omits_script_routing(
        self, tmp_path: Path
    ) -> None:
        """A repo with no script dispatch omits every script-routing projection."""
        rendered = self._render_root_makefile(
            tmp_path, extra_verb_names=(), script_dispatch=None
        )
        expected = " ".join(verb.name for verb in config.Infra.codegen.make.verbs)
        tm.that(rendered, has=f"PUBLIC_VERBS := {expected}")
        tm.that(rendered, lacks="scripts/dispatch.py")


__all__: list[str] = []
