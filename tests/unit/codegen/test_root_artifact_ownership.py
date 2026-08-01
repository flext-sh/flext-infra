"""Public contract for governed repository-root artifact ownership."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config
from flext_infra.codegen.project_new import FlextInfraCodegenProjectNew
from flext_tests import tm


class TestsRootArtifactOwnership:
    """Prove codegen config is the sole root-artifact ownership catalog."""

    def test_envrc_template_covers_every_repository_profile(self) -> None:
        """Every generated repository owns the same direnv activation contract."""
        entry = next(
            item
            for item in config.Infra.codegen.templates.entries
            if item.destination == c.Infra.ENVRC_FILENAME
        )

        tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))

    def test_every_template_profile_is_registered(self) -> None:
        """Every profile used by a template resolves through the typed registry."""
        registered = {profile.name for profile in config.Infra.codegen.profiles}
        mapped = {
            profile
            for entry in config.Infra.codegen.templates.entries
            for profile in entry.profiles
        }

        tm.that(registered, eq=set(c.Infra.MakeProfile))
        tm.that(mapped - registered, eq=set())

    def test_workspace_member_consumes_the_standalone_template_baseline(self) -> None:
        """Workspace members receive every template consumed by a standalone."""
        for entry in config.Infra.codegen.templates.entries:
            if c.Infra.MakeProfile.STANDALONE in entry.profiles:
                tm.that(
                    c.Infra.MakeProfile.WORKSPACE_MEMBER in entry.profiles,
                    eq=True,
                    msg=entry.destination,
                )

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
        spec = config.Infra.codegen
        github_managed = tuple(
            item for item in spec.managed_files if item.path.parts[:1] == (".github",)
        )
        target = github_managed[0]
        mutated = spec.model_copy(
            update={
                "managed_files": tuple(
                    item for item in spec.managed_files if item.path != target.path
                )
            }
        )

        with pytest.raises(ValueError, match="ownership mismatch"):
            type(spec).model_validate(mutated)

    def test_github_managed_owner_must_be_full(self) -> None:
        """Reject weaker policies for every config-declared GitHub artifact."""
        spec = config.Infra.codegen
        target = next(
            item for item in spec.managed_files if item.path.parts[:1] == (".github",)
        )
        mutated = spec.model_copy(
            update={
                "managed_files": tuple(
                    item.model_copy(update={"policy": "merge"})
                    if item.path == target.path
                    else item
                    for item in spec.managed_files
                )
            }
        )

        with pytest.raises(ValueError, match="must be full-managed"):
            type(spec).model_validate(mutated)

    def test_project_new_returns_one_verified_owned_plan(self, tmp_path: Path) -> None:
        """Return the verified conform plan instead of planning the project again."""
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
        configured_policies = {
            item.path.as_posix(): item.policy
            for item in config.Infra.codegen.managed_files
        }
        governed = tuple(
            file for file in created.value.plan.files if file.policy is not None
        )
        tm.that(governed, empty=False)
        tm.that(created.value.written_files, empty=False)
        tm.that(tuple(file for file in created.value.plan.files if file.changed), eq=())
        tm.that(
            len({file.path for file in governed}),
            eq=len(governed),
            msg=str(tuple(file.path.relative_to(root).as_posix() for file in governed)),
        )
        for file in governed:
            relative = file.path.relative_to(root).as_posix()
            tm.that(file.policy, eq=configured_policies[relative])


__all__: list[str] = []
