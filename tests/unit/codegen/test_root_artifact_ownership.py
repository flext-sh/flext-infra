"""Public contract for governed repository-root artifact ownership."""

from __future__ import annotations

from pathlib import Path

import pytest

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
        github_templates = {
            Path(entry.destination)
            for entry in config.Infra.codegen.templates.entries
            if Path(entry.destination).parts[:1] == (".github",)
        }
        github_managed = {
            item.path: item
            for item in configured
            if item.path.parts[:1] == (".github",)
        }
        tm.that(set(github_managed), eq=github_templates)
        tm.that(github_templates, empty=False)
        for owned in github_managed.values():
            tm.that(owned.policy, eq="full")

    def test_every_packaged_github_template_is_declared(self) -> None:
        """Keep the packaged GitHub tree and typed render manifest bijective."""
        template_root = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
        )
        physical = {
            path.relative_to(template_root).as_posix().removesuffix(".j2")
            for path in (template_root / ".github").rglob("*.j2")
        }
        declared = {
            entry.destination
            for entry in config.Infra.codegen.templates.entries
            if Path(entry.destination).parts[:1] == (".github",)
        }

        tm.that(physical, eq=declared)

    def test_github_template_without_managed_owner_is_rejected(self) -> None:
        """Reject any config where a GitHub projection escapes full ownership."""
        codegen_type = type(config.Infra.codegen)
        payload = config.Infra.codegen.model_dump(mode="python")
        github_managed = tuple(
            item
            for item in config.Infra.codegen.managed_files
            if item.path.parts[:1] == (".github",)
        )
        target = github_managed[0]
        payload["managed_files"] = tuple(
            item
            for item in config.Infra.codegen.managed_files
            if item.path != target.path
        )

        with pytest.raises(ValueError, match="ownership mismatch"):
            codegen_type.model_validate(payload)

    def test_github_managed_owner_must_be_full(self) -> None:
        """Reject weaker policies for every config-declared GitHub artifact."""
        codegen_type = type(config.Infra.codegen)
        payload = config.Infra.codegen.model_dump(mode="python")
        target = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.path.parts[:1] == (".github",)
        )
        payload["managed_files"] = tuple(
            item.model_copy(update={"policy": "merge"})
            if item.path == target.path
            else item
            for item in config.Infra.codegen.managed_files
        )

        with pytest.raises(ValueError, match="must be full-managed"):
            codegen_type.model_validate(payload)

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

        tm.ok(checked)
        tm.ok(first)
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
