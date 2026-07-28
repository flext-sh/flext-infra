"""Public contract for governed repository-root artifact ownership."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_infra.workspace.sync import FlextInfraSyncService
from flext_tests import tm
from tests import u


class TestsRootArtifactOwnership:
    """Prove codegen config is the sole root-artifact ownership catalog."""

    def test_governed_artifacts_have_one_explicit_policy(self) -> None:
        configured = config.Infra.codegen.managed_files
        paths = tuple(item.path.as_posix() for item in configured)

        tm.that(len(paths), eq=len(set(paths)))
        for workflow in (".github/workflows/ci.yml", ".github/workflows/ci-matrix.yml"):
            owned = next(
                item for item in configured if item.path.as_posix() == workflow
            )
            tm.that(owned.owner, eq="codegen")
            tm.that(owned.policy, eq="full")

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
        u.Tests.initialize_git_repo(root)
        manual = {
            "config/workspace.yaml": (root / "config" / "workspace.yaml").read_bytes(),
            "custom.mk": b"# manual project extension\n",
        }
        (root / "custom.mk").write_bytes(manual["custom.mk"])
        u.Tests.commit_git_changes(root, "Seed manual extensions")
        request = m.Infra.CodegenConformRequest(root=root)
        planned = FlextInfraCodegenConform(workspace_root=root, request=request).plan(
            request
        )
        tm.ok(planned)
        governed = tuple(
            file for file in planned.value.files if file.policy is not None
        )
        configured_policies = {
            item.path.as_posix(): item.policy
            for item in config.Infra.codegen.managed_files
        }
        before = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )

        checked = FlextInfraSyncService(workspace_root=root).execute()
        first = FlextInfraSyncService(workspace_root=root, apply_changes=True).execute()
        second = FlextInfraSyncService(
            workspace_root=root, apply_changes=True
        ).execute()

        tm.ok(checked)
        tm.ok(first)
        tm.ok(second)
        tm.that(governed, empty=False)
        tm.that(
            len({file.path for file in governed}),
            eq=len(governed),
            msg=str(tuple(file.path.relative_to(root).as_posix() for file in governed)),
        )
        for file in governed:
            relative = file.path.relative_to(root).as_posix()
            tm.that(file.policy, eq=configured_policies[relative])
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
