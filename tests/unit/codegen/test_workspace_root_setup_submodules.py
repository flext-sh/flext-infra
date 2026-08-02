"""Workspace-root setup delegates submodule ownership to the runtime service."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


def _repository(
    name: str, *, role: c.Infra.RepositoryRole, path: Path
) -> m.Infra.RepositoryRef:
    provider = config.Infra.codegen.providers[0]
    return m.Infra.RepositoryRef(
        name=name,
        distribution=name,
        url=f"{provider.base_url}/{name}.git",
        path=path,
        role=role,
        provider=provider.name,
        branch=provider.branch,
        checkout=(
            c.Infra.CheckoutKind.SUBMODULE
            if role is c.Infra.RepositoryRole.WORKSPACE_MEMBER
            else c.Infra.CheckoutKind.ROOT
        ),
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        read_only=False,
    )


class TestsWorkspaceRootSetupSubmodules:
    def test_setup_routes_submodule_reconciliation_through_runtime_owner(
        self, tmp_path: Path
    ) -> None:
        """Generated Make carries metadata; the runtime owns setup behavior."""
        provider = config.Infra.codegen.providers[0]
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="fixture-root",
            repository=_repository(
                "fixture-root", role=c.Infra.RepositoryRole.WORKSPACE_ROOT, path=Path()
            ),
            project=m.Infra.ProjectSpec(
                package_name="fixture_root",
                class_stem="FixtureRoot",
                namespace="FixtureRoot",
                constant_name="fixture-root",
                namespace_attribute="fixture_root",
                alias="fixture_root",
                environment_prefix="FIXTURE_ROOT_",
                description="Fixture workspace root",
                version="0.12.0",
                license="MIT",
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream="flext_cli",
                homepage=f"{provider.base_url}/fixture-root",
                documentation=f"{provider.base_url}/fixture-root",
                workspace_root_rel=".",
                year=2026,
            ),
            members=(
                _repository(
                    "fixture-member",
                    role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                    path=Path("fixture-member"),
                ),
            ),
        )
        root = tmp_path / "fixture-root"
        request = m.Infra.CodegenConformRequest(
            root=root, scope=c.Infra.CodegenConformScope.SELF
        )
        plan: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(
                workspace_root=root,
                request=request,
                initial_workspace=workspace,
                projection_operation="generate",
            ).plan(request)
        )
        engine: m.Infra.CodegenFilePlan = next(
            file
            for file in plan.files
            if file.path == root / config.Infra.codegen.surfaces.make_engine_path
        )
        setup = next(
            verb for verb in config.Infra.codegen.make.verbs if verb.name == "setup"
        )
        operation = next(
            item
            for item in config.Infra.codegen.make.operations
            if item.name == setup.operation
        )

        tm.that(operation.executor, eq="bootstrap")
        tm.that(operation.scope, eq="environment-owner")
        tm.that(operation.requires, has=("managed", "git"))
        tm.that(engine.rendered, has="workspace serialize-make")
        tm.that(
            engine.rendered,
            lacks=[
                "submodule sync --recursive",
                "submodule update --init --recursive",
                "$(UV) sync --project",
            ],
        )
