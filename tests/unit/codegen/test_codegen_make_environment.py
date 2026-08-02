"""Generated Make environment isolation contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m, p, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _render_makefile(
        tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> tuple[Path, Path]:
        provider = config.Infra.codegen.providers[0]
        repository = m.Infra.RepositoryRef(
            name="fixture-project",
            distribution="fixture-project",
            url=f"{provider.base_url}/fixture-project.git",
            path=Path(),
            role=c.Infra.RepositoryRole(profile.value),
            provider=provider.name,
            branch=provider.branch,
            checkout=(
                c.Infra.CheckoutKind.ROOT
                if profile is c.Infra.MakeProfile.WORKSPACE_ROOT
                else c.Infra.CheckoutKind.INDEPENDENT
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=False,
            read_only=False,
        )
        project_root = tmp_path / profile.value / "fixture-project"
        workspace_root = project_root
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
            members=(),
        )
        request = m.Infra.CodegenConformRequest(
            root=project_root, scope=c.Infra.CodegenConformScope.SELF
        )
        plan: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(
                workspace_root=workspace_root,
                request=request,
                initial_workspace=workspace,
                projection_operation="generate",
            ).plan(request)
        )
        make_paths = {
            entry.path
            for entry in config.Infra.codegen.surfaces.entries
            if entry.make_role != "none"
        }
        for file in plan.files:
            relative = file.path.relative_to(project_root).as_posix()
            if relative in make_paths:
                file.path.parent.mkdir(parents=True, exist_ok=True)
                tm.ok(u.Cli.atomic_write_text_file(file.path, file.rendered))
        return project_root, workspace_root

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.WORKSPACE_ROOT, c.Infra.MakeProfile.STANDALONE]
    )
    def test_generated_make_uses_profile_runtime_environment(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """The generated engine derives its runtime root from the typed profile."""
        project_root, _workspace_root = self._render_makefile(tmp_path, profile)
        rendered = (
            project_root / config.Infra.codegen.surfaces.make_engine_path
        ).read_text(encoding="utf-8")
        profile_spec = next(
            item for item in config.Infra.codegen.profiles if item.name == profile
        )
        expected_root = (
            "$(WORKSPACE_ROOT)"
            if profile_spec.environment_scope == "root"
            else "$(PROJECT_ROOT)"
        )
        environment_dir = config.Infra.tooling.tools.pyright.path_rules.venv_name
        tm.that(
            rendered,
            has=[
                f"MAKE_PROFILE := {profile.value}",
                f"RUNTIME_ROOT := {expected_root}",
                f"RUNTIME_VENV := $(RUNTIME_ROOT)/{environment_dir}",
                '"$(RUNTIME_PYTHON)" -m flext_infra',
            ],
        )
        tm.that(rendered, lacks="FLEXT_INFRA_PYTHON")

    @pytest.mark.parametrize(
        "profile", [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE_ROOT]
    )
    def test_setup_routes_to_the_bootstrap_environment_operation(
        self, tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> None:
        """Setup is one typed bootstrap operation, not generated shell logic."""
        project_root, _workspace_root = self._render_makefile(tmp_path, profile)
        rendered = (
            project_root / config.Infra.codegen.surfaces.make_engine_path
        ).read_text(encoding="utf-8")
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
        tm.that(operation.mutation, eq="always")
        tm.that(operation.requires, has=("managed", "git"))
        tm.that(rendered, has=["BOOTSTRAP_VERBS :=", "workspace serialize-make"])
        tm.that(rendered, lacks=["uv venv --clear", "uv sync --project"])

    def test_serialized_gate_fails_closed_before_managed_environment_exists(
        self, tmp_path: Path
    ) -> None:
        """A serialized gate preserves the canonical setup-required diagnostic."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )

        process: p.Cli.CommandOutput = tm.ok(
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
