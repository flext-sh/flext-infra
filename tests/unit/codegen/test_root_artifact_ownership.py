"""Public contract for governed repository-root artifact ownership."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.workspace.sync import FlextInfraSyncService
from flext_tests import tm


class TestsRootArtifactOwnership:
    """Prove codegen config is the sole root-artifact ownership catalog."""

    def test_governed_artifacts_have_one_explicit_policy(self) -> None:
        # Conflict: mro-56qk owns migration of this temporary local expectation
        # into the normative tests.c/t/p/m/u/config/settings fixture architecture.
        expected = {
            ".env.example": "create-only",
            ".envrc": "create-only",
            ".gitignore": "merge",
            ".gitmodules": "full",
            ".mise.toml": "merge",
            ".pre-commit-config.yaml": "full",
            ".python-version": "full",
            ".vscode/settings.json": "merge",
            "LICENSE": "create-only",
            "Makefile": "delegated",
            "README.md": "create-only",
            "base.mk": "delegated",
            "config/workspace.yaml": "manual",
            "custom.mk": "manual",
            "pyproject.toml": "merge",
            "workspace_custom.mk": "manual",
        }

        configured = {
            item.path.as_posix(): item.policy
            for item in config.Infra.codegen.managed_files
        }

        tm.that(configured, eq=expected)

    def test_legacy_sync_uses_one_fixed_point_plan(self, tmp_path: Path) -> None:
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
        tm.ok(u.Cli.run_checked(["git", "init", "-q"], cwd=root))
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed conform project"], cwd=root
            )
        )
        manual = {
            "config/workspace.yaml": (root / "config" / "workspace.yaml").read_bytes(),
            "custom.mk": b"# manual project extension\n",
            "workspace_custom.mk": b"# manual workspace extension\n",
        }
        (root / "custom.mk").write_bytes(manual["custom.mk"])
        (root / "workspace_custom.mk").write_bytes(manual["workspace_custom.mk"])
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Seed manual extensions"], cwd=root
            )
        )
        request = m.Infra.CodegenConformRequest(root=root)
        planned = FlextInfraCodegenConform(workspace_root=root, request=request).plan(
            request
        )
        tm.ok(planned)
        governed = tuple(file for file in planned.value.files if file.policy is not None)
        before = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )

        checked = FlextInfraSyncService(workspace_root=root).execute()
        first = FlextInfraSyncService(
            workspace_root=root, apply_changes=True
        ).execute()
        second = FlextInfraSyncService(
            workspace_root=root, apply_changes=True
        ).execute()

        tm.ok(checked)
        tm.ok(first)
        tm.ok(second)
        tm.that(len(governed), eq=len(config.Infra.codegen.managed_files))
        tm.that(len({file.path for file in governed}), eq=len(governed))
        tm.that(checked.value.files_changed, eq=0)
        tm.that(first.value.files_changed, eq=0)
        tm.that(second.value.files_changed, eq=0)
        after = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )
        tm.that(after, eq=before)
        for relative, expected in manual.items():
            tm.that((root / relative).read_bytes(), eq=expected)


__all__: list[str] = []
