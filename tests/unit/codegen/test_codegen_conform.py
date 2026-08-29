"""Public functional contract for new and existing project conformance.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

import pytest
from flext_infra import config, main
from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenProjectNew
from flext_infra.deps import FlextInfraPyprojectModernizer
from flext_infra.services.cli_routes_codegen import CodegenRoutes
from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_tests import tm

from tests import c, m, p, r, u

pytestmark = pytest.mark.slow


def _standalone_workspace(root: Path) -> m.Infra.WorkspaceSpec:
    """Build the smallest repository-local conformance context."""
    del root
    return m.Infra.WorkspaceSpec(
        repository=u.Tests.repository_ref("flext-demo"),
        project=m.Infra.ProjectSpec(
            package_name="flext_demo",
            class_stem="FlextDemo",
            namespace="Demo",
            constant_name="flext-demo",
            namespace_attribute="demo",
            alias="demo",
            environment_prefix="FLEXT_DEMO_",
            description="FLEXT demo",
            version="0.1.0",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            homepage="https://github.com/flext-sh/flext-demo",
            documentation="https://github.com/flext-sh/flext-demo",
            year=2026,
        ),
    )


def _apply_conform_surface(
    root: Path, workspace: m.Infra.WorkspaceSpec, surface: c.Infra.CodegenConformSurface
) -> None:
    """Materialize one exact public conform surface for a focused test."""
    tm.ok(
        FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=surface,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
            initial_workspace=workspace,
        )
    )


def _project_tree(root: Path) -> tuple[tuple[str, bytes], ...]:
    """Return the versionable project tree independently of Git test fixtures."""
    return tuple(
        sorted(
            (path.relative_to(root).as_posix(), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
            and ".git" not in path.relative_to(root).parts
            and ".infra-baseline" not in path.relative_to(root).parts
        )
    )


def _seed_infra_package_tree(root: Path) -> None:
    """Seed the minimal flext-infra tree (pyproject, src package, tests package).

    The conform templates materialize tests/fixtures/ci/docker/*, and the
    existing-tree tooling render discovers python roots from directories that
    exist on disk (env_dirs). Seeding tests/ makes the first render match the
    post-apply fixed point.
    """
    dist = u.Tests.repository_ref(config.Infra.name).distribution
    tm.ok(
        u.Cli.atomic_write_text_file(
            root / "pyproject.toml",
            f'[project]\nname = "{dist}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n',
        )
    )
    package_init = root / "src" / "flext_infra" / "__init__.py"
    package_init.parent.mkdir(parents=True, exist_ok=True)
    tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
    tests_init = root / "tests" / "__init__.py"
    tests_init.parent.mkdir(parents=True, exist_ok=True)
    tm.ok(u.Cli.atomic_write_text_file(tests_init, ""))


class TestCodegenConform:
    """Prove one SSOT for project creation and existing-tree conformance."""

    def _conform_with_rendered_makefile(
        self, root: Path, monkeypatch: pytest.MonkeyPatch, suffix: str
    ) -> p.Result[m.Infra.CodegenResult]:
        """Apply conform with ``suffix`` appended to the rendered Makefile."""
        distribution = u.Tests.repository_ref(config.Infra.name).distribution
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n',
            encoding="utf-8",
        )
        package_init = root / "src" / distribution.replace("-", "_") / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        package_init.write_text("", encoding="utf-8")
        original_render = u.Cli.template_render

        def _render(path: Path, context: p.Model) -> p.Result[str]:
            rendered = original_render(path, context)
            if rendered.failure or path.name != f"{c.Infra.MAKEFILE_FILENAME}.j2":
                return rendered
            return r[str].ok(f"{rendered.value}{suffix}")

        monkeypatch.setattr(u.Cli, "template_render", _render)
        return FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

    @pytest.mark.slow
    def test_rendered_conflict_marker_is_rejected_before_target_changes(
        self, infra_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = infra_git_repo
        target = root / c.Infra.MAKEFILE_FILENAME
        original = "existing generated makefile\n"
        target.write_text(original, encoding="utf-8")

        rejected = self._conform_with_rendered_makefile(
            root, monkeypatch, "\n<<<<<<< incoming\n"
        )

        tm.fail(rejected)
        tm.that(rejected.error, has="base/Makefile.j2")
        tm.that(rejected.error, has=str(target))
        tm.that(rejected.error, has=str(root))
        tm.that(target.read_text(encoding="utf-8"), eq=original)

        monkeypatch.undo()
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        applied = FlextInfraCodegenConform.execute_request(request)
        tm.ok(applied)
        tm.that(target.read_text(encoding="utf-8"), lacks="<<<<<<< ")
        fixed_point = FlextInfraCodegenConform.execute_request(
            request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK})
        )
        tm.ok(fixed_point)
        tm.that(fixed_point.value.written_files, eq=())

    @pytest.mark.slow
    def test_setext_underline_is_accepted_as_ordinary_content(
        self, infra_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A Markdown Setext underline is content, so conform must not reject it."""
        applied = self._conform_with_rendered_makefile(
            infra_git_repo, monkeypatch, "\n# Title\n=======\n"
        )

        tm.ok(applied)

    def test_diff3_ancestor_fence_is_rejected_before_target_changes(
        self, infra_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A diff3 merge leaves an ancestor fence that must stop the plan."""
        target = infra_git_repo / c.Infra.MAKEFILE_FILENAME
        original = "existing generated makefile\n"
        target.write_text(original, encoding="utf-8")

        rejected = self._conform_with_rendered_makefile(
            infra_git_repo, monkeypatch, "\n||||||| base\nancestor\n"
        )

        tm.fail(rejected)
        tm.that(rejected.error, has="||||||| base")
        tm.that(target.read_text(encoding="utf-8"), eq=original)

    @pytest.mark.slow
    def test_apply_recovers_declared_managed_pyproject_conflict(
        self, infra_git_repo: Path
    ) -> None:
        """Repair a committed managed block through the normal apply plan."""
        root = infra_git_repo
        distribution = u.Tests.repository_ref(config.Infra.name).distribution
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "\n"
            "[tool.pytest.ini_options]\n"
            'addopts = ["--timeout=10"]\n',
            encoding="utf-8",
        )
        package_init = root / "src" / distribution.replace("-", "_") / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        package_init.write_text("", encoding="utf-8")

        applied = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.PYPROJECT,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.ok(applied)
        rendered = (root / "pyproject.toml").read_text(encoding="utf-8")
        tm.that(rendered, lacks="<<<<<<<")
        payload = tomllib.loads(rendered)
        addopts = payload["tool"]["pytest"]["ini_options"]["addopts"]
        tm.that(
            addopts,
            has=f"--timeout={config.Infra.tooling.tools.pytest.case_timeout_seconds}",
        )

    # This end-to-end scenario scaffolds a project and runs its console entry
    # point in a fresh interpreter. The slow marker opts into the single
    # config-owned slow-item budget; tests must not restate that policy locally.
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("kind", "name"),
        [
            (c.Infra.ProjectKind.EXTERNAL, "flext-demo"),
            (c.Infra.ProjectKind.INTERNAL, "flext-internal-demo"),
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
        first_result = tm.ok(first)
        tm.that(bool(first_result.written_files), eq=True)
        tm.that(
            tuple(file.path for file in first_result.plan.files if file.changed), eq=()
        )
        makefile_plan = next(
            item
            for item in first_result.plan.files
            if item.path.name == c.Infra.MAKEFILE_FILENAME
        )
        tm.that(makefile_plan.rendered, lacks="MAKE_PROFILE")
        tm.that(first_result.plan.request.root, eq=root.resolve())
        tm.that((root / "config" / "workspace.yaml").is_file(), eq=False)
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

    @pytest.mark.slow
    def test_generated_make_uses_unpinned_environment_uv(
        self, infra_git_repo: Path
    ) -> None:
        """Generated Make delegates uv selection to the caller environment."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.MAKEFILE)
        selected = u.Cli.run_raw(
            ["make", "-C", str(root), "--dry-run", "_builtin_status_diagnostics"],
            remove_env_keys=("MAKEFLAGS",),
        )

        selected_process = tm.ok(selected)
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

    @pytest.mark.slow
    def test_existing_manifest_converges_to_identical_tree(
        self, infra_git_repo: Path
    ) -> None:
        existing_root = infra_git_repo
        created = FlextInfraCodegenProjectNew(
            name="flext-demo",
            kind=c.Infra.ProjectKind.EXTERNAL,
            output_root=existing_root,
            provider="flext-sh",
            license="MIT",
            author_name="FLEXT Team",
            author_email="team@flext.dev",
            upstream="flext_cli",
            year=2026,
            apply_changes=True,
        ).execute()
        tm.ok(created)
        expected_tree = _project_tree(existing_root)
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
                ["git", "commit", "-q", "--no-verify", "-m", "Seed committed drift"],
                cwd=existing_root,
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
        tm.that(_project_tree(existing_root), eq=expected_tree)

    @pytest.mark.slow
    def test_python_root_outside_env_dirs_still_reaches_a_fixed_point(
        self, infra_git_repo: Path
    ) -> None:
        """The gen verb converges for a Python root beyond declarative env_dirs.

        Two derivations used to select the pyright execution environments: the
        dependency command discovered roots ON DISK, while conform planned them
        from declarative ``env_dirs``. A project owning a Python directory
        outside that list therefore oscillated between two writers. Conform is
        the sole generation owner, so it must discover and preserve the extra
        root by itself and immediately reach a fixed point.
        """
        root = infra_git_repo
        _seed_infra_package_tree(root)
        # The defect needs a Python root the declarative env_dirs never lists.
        extra_root = "tools"
        module = root / extra_root / "maintenance.py"
        module.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(module, "VALUE = 1\n"))
        tm.that(extra_root in u.Infra.discover_python_dirs(root), eq=True)
        tm.that(
            extra_root in config.Infra.tooling.tools.pyright.path_rules.env_dirs,
            eq=False,
        )
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed python root beyond env_dirs"],
                cwd=root,
            )
        )

        applied = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )
        tm.ok(applied)

        fixed_point = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )
        tm.ok(fixed_point)
        tm.that(fixed_point.value.written_files, eq=())

    @pytest.mark.slow
    def test_declared_root_namespace_is_analyzed_before_content(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        _seed_infra_package_tree(root)
        (root / "scripts").mkdir()

        result = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.ok(result)
        payload = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        tm.that(payload["tool"]["pyrefly"]["project-includes"], has="scripts/**/*.py*")
        tm.that(payload["tool"]["pyright"]["include"], has="scripts")

    # Why (suite budget): two conform apply cycles plus a check over a full
    # managed tree on a real git repo; the per-case wall only holds idle.
    @pytest.mark.slow
    def test_existing_root_derives_project_spec_from_pep621(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        repository = u.Tests.repository_ref(config.Infra.name)
        local_repository = repository.model_copy(update={"path": Path()})
        create_only = {
            "LICENSE": "existing license\n",
            "README.md": "# Existing repository\n",
            "OWNERS.txt": "repository-owned\n",
        }
        _seed_infra_package_tree(root)
        for relative, content in create_only.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed manifest-less tree"],
                cwd=root,
            )
        )

        derived = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(derived.repository, eq=local_repository)
        tm.that(
            derived.project.package_name, eq=repository.distribution.replace("-", "_")
        )

        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        initial_plan = tm.ok(
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

    def test_make_context_accepts_manifest_without_project_metadata(
        self, tmp_path: Path
    ) -> None:
        """Build Make context from repository and tooling owners alone."""
        repository = u.Tests.repository_ref("consumer")
        tooling_runtime = tm.ok(
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
            repository, config.Infra.codegen, tooling_runtime=tooling_runtime
        )
        rendered = tm.ok(context)
        tm.that(isinstance(rendered, m.Infra.MakeRenderContext), eq=True)
        tm.that(isinstance(rendered, m.Infra.ProjectRenderContext), eq=False)
        tm.that("workspace_root_rel" in type(rendered).model_fields, eq=False)
        tm.that("infra_source_root_rel" in type(rendered).model_fields, eq=False)
        tm.that(rendered.infra_repository.distribution, eq=config.Infra.name)
        tm.that(
            rendered.infra_repository.url,
            eq=f"{config.Infra.codegen.providers[0].base_url.rstrip('/')}"
            f"/{config.Infra.name}.git",
        )

    # Why (suite budget): parametrized over both conform modes, each running a
    # full plan/apply cycle on a real git repo; 10s only holds on an idle CPU.
    @pytest.mark.slow
    @pytest.mark.parametrize("mode", tuple(c.Infra.CodegenConformMode))
    def test_public_cli_routes_check_and_apply_to_one_handler(
        self, infra_git_repo: Path, mode: c.Infra.CodegenConformMode
    ) -> None:
        """Execute one public mode without changing an already conform tree."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.PYPROJECT)
        _apply_conform_surface(root, workspace, c.Infra.CodegenConformSurface.MAKEFILE)
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed generated project"],
                cwd=root,
            )
        )
        route = next(
            route
            for route in CodegenRoutes.codegen_routes[c.Infra.CLI_GROUP_CODEGEN]
            if route.name == "conform"
        )
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
        )
        tm.ok(route.handler(request))
        status = tm.ok(u.Cli.capture(["git", "status", "--porcelain"], cwd=root))
        tm.that(status, eq="")

    # Why (suite budget): dependencies-only apply+check runs two full conform
    # cycles on a real git repo; the per-case wall only holds on an idle CPU.
    @pytest.mark.slow
    def test_dependency_surface_excludes_unowned_managed_files(
        self, infra_git_repo: Path
    ) -> None:
        """Plan only dependency metadata when another managed surface is invalid."""
        root = infra_git_repo
        workspace = _standalone_workspace(root)
        _apply_conform_surface(
            root, workspace, c.Infra.CodegenConformSurface.DEPENDENCIES
        )
        tm.ok(u.Cli.atomic_write_text_file(root / "OWNERS.txt", "repository-owned\n"))
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed generated project"],
                cwd=root,
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
        exit_code = main([
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


__all__: list[str] = []
