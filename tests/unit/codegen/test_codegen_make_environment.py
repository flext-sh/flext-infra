"""Generated Make environment isolation contract."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsCodegenMakeEnvironment:
    """Prove generated operations ignore the caller shell environment."""

    @staticmethod
    def _render_makefile(
        tmp_path: Path, profile: c.Infra.MakeProfile
    ) -> tuple[Path, Path]:
        repository = m.Infra.RepositoryRef(
            name="fixture-project",
            distribution="fixture-project",
            url="https://github.com/flext-sh/fixture-project.git",
            branch="0.12.0-dev",
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
                    ".."
                    if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER
                    else "."
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
        planned = FlextInfraCodegenConform(
            workspace_root=workspace_root,
            request=request,
            initial_workspace=workspace,
        ).plan(request)
        plan = tm.ok(planned)
        makefile = next(
            file for file in plan.files if file.path.name == c.Infra.MAKEFILE_FILENAME
        )
        project_root.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(project_root / "Makefile", makefile.rendered))
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
        self,
        tmp_path: Path,
        profile: c.Infra.MakeProfile,
        *,
        attached: bool,
    ) -> None:
        """Every generated shell receives the profile-resolved runtime venv."""
        project_root, workspace_root = self._render_makefile(tmp_path, profile)
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
        probe = (
            "probe:; @printf '%s\\n' "
            "'UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT)' "
            "'VIRTUAL_ENV=$(VIRTUAL_ENV)' "
            "'PATH=$(PATH)'; command -v python"
        )
        process = u.Cli.capture(
            [
                "make",
                "--no-print-directory",
                "--eval",
                probe,
                "probe",
                f"SUPERPROJECT_ROOT={workspace_root if attached else ''}",
            ],
            cwd=project_root,
            env={
                **os.environ,
                "UV_PROJECT_ENVIRONMENT": str(hostile_venv),
                "VIRTUAL_ENV": str(hostile_venv),
                "PATH": f"{hostile_bin}:{os.environ['PATH']}",
            },
        )
        output = tm.ok(process).splitlines()
        tm.that(output[0], eq=f"UV_PROJECT_ENVIRONMENT={runtime_root / '.venv'}")
        tm.that(output[1], eq=f"VIRTUAL_ENV={runtime_root / '.venv'}")
        tm.that(output[2].split(":", maxsplit=1)[0], eq=f"PATH={runtime_bin}")
        tm.that(output[3], eq=str(runtime_python))

    def test_generated_operations_bind_uv_to_runtime_root(self, tmp_path: Path) -> None:
        """All uv command families consume the same generated environment binding."""
        project_root, _workspace_root = self._render_makefile(
            tmp_path, c.Infra.MakeProfile.STANDALONE
        )
        makefile = (project_root / "Makefile").read_text()
        profile_names = {profile.name for profile in config.Infra.codegen.profiles}
        tm.that(profile_names, eq={profile.value for profile in c.Infra.MakeProfile})
        tm.that("override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)" in makefile, eq=True)
        tm.that('UV_RUN := uv run --project "$(RUNTIME_ROOT)" --no-sync' in makefile, eq=True)
        tm.that('uv sync --project "$(PROJECT_ROOT)"' in makefile, eq=True)
        tm.that('uv build --project "$(PROJECT_ROOT)"' in makefile, eq=True)
        tm.that('uv pip install --python "$(RUNTIME_PYTHON)"' in makefile, eq=True)
