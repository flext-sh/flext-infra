"""Public regression coverage for manifestless existing repositories."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm


class TestCodegenManifestlessExisting:
    def test_existing_root_uses_pep621_metadata_for_managed_artifacts(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        repository = next(
            item
            for item in config.Infra.codegen.repositories
            if item.distribution == "flext-infra"
        )
        preserved = {
            "LICENSE": "existing license\n",
            "README.md": "# Existing repository\n",
        }
        pyproject_source: str = tm.ok(
            u.Cli.files_read_text(Path.cwd() / "pyproject.toml")
        )
        tm.ok(u.Cli.atomic_write_text_file(root / "pyproject.toml", pyproject_source))
        package_init = root / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        vscode_settings = root / ".vscode" / "settings.json"
        vscode_settings.parent.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                vscode_settings,
                tm.ok(u.Cli.files_read_text(Path.cwd() / ".vscode" / "settings.json")),
            )
        )
        for relative, content in preserved.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed manifestless tree"], cwd=root
            )
        )

        derived: m.Infra.WorkspaceSpec = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root)
        )
        tm.that(derived.repository, eq=repository)
        tm.that(derived.project, eq=None)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(FlextInfraCodegenConform.execute_request(request))
        tm.ok(u.Cli.run_checked(["git", "add", "pyproject.toml"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Conform fixture metadata"], cwd=root
            )
        )
        artifact_request = request.model_copy(
            update={"what": c.Infra.CodegenConformSurface.ALL}
        )
        initial_plan: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(workspace_root=root).plan(artifact_request)
        )
        plans = {
            file.path.relative_to(root).as_posix(): file for file in initial_plan.files
        }
        tm.that(
            sum(file.path == root / "pyproject.toml" for file in initial_plan.files),
            eq=1,
        )
        tm.that(plans["pyproject.toml"].changed, eq=False)

        missing_create_only = plans[".env.example"]
        tm.that(missing_create_only.policy, eq="create-only")
        tm.that(missing_create_only.changed, eq=False)
        tm.that((root / ".env.example").exists(), eq=False)
        for relative, content in preserved.items():
            tm.that(plans[relative].changed, eq=False)
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.that(plans[required].changed, eq=True)

        for file in initial_plan.files:
            if file.changed:
                tm.ok(u.Cli.atomic_write_text_file(file.path, file.rendered))
        tm.that((root / ".env.example").exists(), eq=False)
        for relative, content in preserved.items():
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.that((root / required).is_file(), eq=True)
        fixed_point = FlextInfraCodegenConform(workspace_root=root).plan(
            artifact_request.model_copy(
                update={"mode": c.Infra.CodegenConformMode.CHECK}
            )
        )
        verified: m.Infra.CodegenPlan = tm.ok(fixed_point)
        tm.that(tuple(file.path for file in verified.files if file.changed), eq=())

    def test_existing_root_rejects_non_regular_create_only_destination(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        pyproject_source: str = tm.ok(
            u.Cli.files_read_text(Path.cwd() / "pyproject.toml")
        )
        tm.ok(u.Cli.atomic_write_text_file(root / "pyproject.toml", pyproject_source))
        package_init = root / "src" / "flext_infra" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        (root / ".env.example").mkdir()

        planned = FlextInfraCodegenConform(workspace_root=root).plan(
            m.Infra.CodegenConformRequest(root=root)
        )

        tm.fail(planned)
        tm.that(
            planned.error or "", has="create-only destination is not a regular file"
        )


__all__: list[str] = []
