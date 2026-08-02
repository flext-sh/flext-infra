"""Typed workspace-root Make operations delegate member fan-out at runtime."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm
from tests import u as test_u


class TestsCodegenWorkspaceRootFanout:
    def test_surface_catalog_declares_workspace_root_make_wrapper(self) -> None:
        """The sole Make wrapper entry supports the workspace-root profile."""
        makefile_entries = tuple(
            entry
            for entry in config.Infra.codegen.surfaces.entries
            if entry.path == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(makefile_entries, len=1)
        tm.that(makefile_entries[0].profiles, has=c.Infra.MakeProfile.WORKSPACE_ROOT)

    def test_workspace_root_gate_verbs_fan_out_via_orchestrator(
        self, tmp_path: Path
    ) -> None:
        """Workspace gates select the governed repository set at runtime."""
        rendered = _render_root_makefile(tmp_path)
        make = config.Infra.codegen.make
        for name in ("check", "test"):
            verb = next(item for item in make.verbs if item.name == name)
            operation = next(
                item for item in make.operations if item.name == verb.operation
            )
            tm.that(operation.scope, eq="governed-selection")
        tm.that(rendered, has="MAKE_PROFILE := workspace-root")
        tm.that(rendered, has="workspace serialize-make")


def _render_root_makefile(tmp_path: Path) -> str:
    """Render the Make engine from a typed workspace-root fixture."""
    repository = test_u.Tests.repository_ref("workspace-root-fixture")
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repository.name,
        repository=repository,
        project=m.Infra.ProjectSpec(
            package_name=repository.distribution.replace("-", "_"),
            class_stem="FixtureWorkspace",
            namespace="FixtureWorkspace",
            constant_name=repository.name,
            namespace_attribute="fixture_workspace",
            alias="fixture_workspace",
            environment_prefix="FIXTURE_WORKSPACE_",
            description="Fixture workspace",
            version="0.12.0.dev0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage=repository.url.removesuffix(".git"),
            documentation=repository.url.removesuffix(".git"),
            workspace_root_rel=".",
            year=2026,
        ),
    )
    workspace_root = tmp_path / "workspace"
    request = m.Infra.CodegenConformRequest(
        root=workspace_root,
        what=c.Infra.CodegenConformSurface.ALL,
        scope=c.Infra.CodegenConformScope.SELF,
    )
    plan: m.Infra.CodegenPlan = tm.ok(
        FlextInfraCodegenConform(
            workspace_root=workspace_root,
            request=request,
            initial_workspace=workspace,
            projection_operation="generate",
        ).plan(request)
    )
    makefile_plans = tuple(
        file
        for file in plan.files
        if file.path.relative_to(workspace_root).as_posix()
        == config.Infra.codegen.surfaces.make_engine_path
    )
    tm.that(makefile_plans, len=1)
    rendered: str = makefile_plans[0].rendered
    return rendered


__all__: tuple[str, ...] = ()
