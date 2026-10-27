"""Repository-local topology and Beads identity contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, tm, u


class TestsFlextInfraRepositoryLocalTopology:
    """Prove each repository owns its topology and typed Beads identity."""

    @pytest.mark.parametrize("uv_package", [None, False, True])
    def test_packaging_ingress_retains_native_declarations_without_exports(
        self,
        tmp_path: Path,
        *,
        uv_package: bool | None,
    ) -> None:
        """Native package flags and build backend remain distinct metadata facts."""
        root = self._self_named_governed_root(tmp_path, "packaging")
        manifest = root / c.PYPROJECT_FILENAME
        payload = u.Tests.toml_payload(manifest.read_text(encoding=c.DEFAULT_ENCODING))
        tool = u.Tests.toml_mapping(payload.get("tool", {}))
        uv = dict(u.Tests.toml_mapping(tool.get("uv", {})))
        if uv_package is None:
            uv.pop("package", None)
        else:
            uv["package"] = uv_package
        tm.ok(
            u.Cli.toml_write_mapping(
                manifest,
                {
                    **payload,
                    "build-system": {
                        "requires": ["hatchling"],
                        "build-backend": "hatchling.build",
                    },
                    "tool": {**tool, "uv": uv},
                },
            ),
        )
        state = tm.ok(u.Infra.read_project_metadata_state(root))
        tm.that(state.packaging.uv_package, eq=uv_package)
        tm.that(state.packaging.build_backend, eq="hatchling.build")
        tm.that(
            u.Infra.project_package_participation(state.packaging),
            eq=True if uv_package is None else uv_package,
        )
        retained = tm.ok(u.Infra.read_project_metadata_result(root))
        tm.that(retained.model_dump(), eq=state.metadata.model_dump())

    def test_repository_identity_does_not_parse_unrelated_invalid_exports(
        self,
        tmp_path: Path,
    ) -> None:
        """Identity survives invalid exports while the layout parser stays red."""
        root = self._self_named_governed_root(tmp_path, "invalid-exports")
        before = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        metadata = tm.ok(u.Infra.read_project_metadata_result(root))
        source = root / "src" / metadata.package_name / "api.py"
        source.write_text(
            '"""unterminated export documentation\n', encoding=c.DEFAULT_ENCODING
        )

        after = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(after.repository.distribution, eq=metadata.project.name)
        tm.that(after.repository.package, eq=before.repository.package)
        tm.that(after.repository.provider, eq=before.repository.provider)
        with pytest.raises(SyntaxError):
            u.Infra.layout(root)

    @staticmethod
    def _self_named_governed_root(tmp_path: Path, directory: str) -> Path:
        """Initialize one governed checkout whose identity derives from its directory.

        Returns:
            The resulting ``Path``.

        """
        name = f"fixture-{directory}"
        return u.Tests.WorktreeFixture.governed_workspace(
            tmp_path,
            directory,
            distribution=name,
            beads=u.Tests.BeadsIdentity(
                workspace=name,
                database=name.replace("-", "_"),
                issue_prefix=name,
            ),
        )

    def test_repository_declaration_owns_repository_policy(
        self,
        tmp_path: Path,
    ) -> None:
        """The repository's own codegen declaration carries its typed policy."""
        root = self._self_named_governed_root(tmp_path, "manifest-policy")
        u.Tests.WorktreeFixture.override_repository_declaration(
            root,
            {
                "kind": c.Infra.ProjectKind.THIRD_PARTY_FORK.value,
                "uv_link_mode": "clone",
            },
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.repository.kind, eq=c.Infra.ProjectKind.THIRD_PARTY_FORK)
        tm.that(workspace.repository.uv_link_mode, eq="clone")

    def test_declared_beads_free_repository_loads_without_ledger(
        self,
        tmp_path: Path,
    ) -> None:
        """An explicit standalone policy needs no Beads or Gas City identity."""
        root = self._self_named_governed_root(tmp_path, "without-beads")
        observed = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        u.Tests.WorktreeFixture.override_repository_declaration(
            root,
            {"beads_enabled": False, "gascity_enabled": False},
        )
        (root / "config" / c.Infra.BEADS_CONFIG_FILENAME).unlink()
        ledger = root / c.Infra.BEADS_DIRNAME
        if ledger.is_dir():
            shutil.rmtree(ledger)
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(workspace.name, eq=observed.name)
        tm.that(workspace.beads, none=True)
        tm.fail(workspace.gascity_enabled)

    def test_overlay_omitting_beads_policy_keeps_beads_enabled(
        self,
        tmp_path: Path,
    ) -> None:
        """A declaration that omits beads_enabled keeps the default participation."""
        root = self._self_named_governed_root(tmp_path, "overlay-default-beads")
        observed = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        u.Tests.WorktreeFixture.override_repository_declaration(
            root,
            {"ci_enabled": False},
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.beads, eq=observed.beads)
        tm.that(workspace.gascity_enabled, eq=observed.gascity_enabled)

    def test_repository_declaration_cannot_declare_identity(
        self,
        tmp_path: Path,
    ) -> None:
        """Git and project metadata own identity; a declared one fails closed."""
        root = self._self_named_governed_root(tmp_path, "manifest-contradiction")
        u.Tests.WorktreeFixture.override_repository_declaration(
            root,
            {"distribution": "different-distribution"},
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="distribution")

    def test_repository_declaration_rejects_unknown_fields(
        self,
        tmp_path: Path,
    ) -> None:
        """Reject an unknown repository declaration field before policy use."""
        root = self._self_named_governed_root(tmp_path, "unknown-field")
        u.Tests.WorktreeFixture.override_repository_declaration(
            root,
            {"unknown_contract": True},
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="unknown_contract")

    @staticmethod
    def test_gitmodules_without_governed_members_remains_standalone(
        tmp_path: Path,
    ) -> None:
        """Vendored or empty Git topology does not create a FLEXT workspace."""
        root = tmp_path / "workspace"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture-database",
                issue_prefix="fixture-prefix",
            ),
        )
        u.Tests.WorktreeFixture.write_gitmodules(root, ())

        mode = tm.ok(FlextInfraWorkspaceDetector().detect(root))
        target = tm.ok(FlextInfraWorkspaceDetector.conform_target(root))

        tm.that(mode, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(target.make_profile, eq=c.Infra.MakeProfile.STANDALONE)

    @staticmethod
    def test_parent_gitmodules_never_classifies_or_governs_a_child(
        tmp_path: Path,
    ) -> None:
        """Ignore every parent input when deriving one child repository."""
        parent = tmp_path / "parent"
        u.Tests.WorktreeFixture.initialize_governed_project(
            parent,
            "parent",
            beads=u.Tests.BeadsIdentity(
                workspace="parent-workspace",
                database="parent-database",
                issue_prefix="parent-prefix",
            ),
        )
        u.Tests.WorktreeFixture.write_gitmodules(parent, ("child",))
        child = parent / "child"
        u.Tests.WorktreeFixture.initialize_governed_project(
            child,
            "child",
            beads=u.Tests.BeadsIdentity(
                workspace="child-workspace",
                database="child-database",
                issue_prefix="child-prefix",
            ),
        )

        mode = tm.ok(FlextInfraWorkspaceDetector().detect(child))
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(child))
        resolved = tm.ok(
            u.Infra.git_show_toplevel(m.Infra.GitRepoRequest(repo_root=child)),
        ).repository_root

        tm.that(mode, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(workspace.repository.name, eq="child")
        tm.that(workspace.name, eq="child-workspace")
        tm.that(u.Tests.required_beads(workspace).workspace, eq="child-workspace")
        tm.that(workspace.subprojects, empty=True)
        tm.that(resolved, eq=child.resolve())

    @staticmethod
    def _attached_member(tmp_path: Path) -> Path:
        """Attach a governed member to a parent workspace and return its path.

        Returns:
            The resulting ``Path``.

        """
        parent = tmp_path / "parent"
        member = u.Tests.WorktreeFixture.copied_member(
            parent,
            "fixture-parent",
            workspace="parent-workspace",
            database="parent-database",
            issue_prefix="parent-prefix",
        )
        # A composed project follows the workspace ledger through its own
        # declared identity. The ``.beads -> ../.beads`` link that used to
        # carry it is prohibited, and both conform and the detector reject it.
        u.Tests.WorktreeFixture.write_beads_project(
            member,
            workspace="parent-workspace",
            database="parent-database",
            issue_prefix="parent-prefix",
        )
        u.Tests.WorktreeFixture.attach_submodule(
            parent,
            member,
            distribution="fixture-member",
            relative_path="apps/member",
        )
        return member

    def test_explicitly_unmanaged_content_member_remains_external(
        self,
        tmp_path: Path,
    ) -> None:
        """The .gitmodules opt-out takes precedence over a cataloged member."""
        member = self._attached_member(tmp_path)
        root = member.parents[1]
        relative = member.relative_to(root).as_posix()
        tm.ok(
            u.Cli.run_checked(
                (
                    c.Infra.GIT,
                    "config",
                    "-f",
                    c.Infra.GITMODULES,
                    # The fixture names the section after the distribution.
                    "submodule.fixture-member.flext-managed",
                    c.ParserBooleanToken.FALSE,
                ),
                cwd=root,
            ),
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(workspace.subprojects, empty=True)
        tm.that(workspace.external_dependency_paths, has=Path(relative))

    def test_member_origin_must_match_its_gitmodules_url(
        self,
        tmp_path: Path,
    ) -> None:
        """Reject a member checkout whose origin differs from .gitmodules."""
        member = self._attached_member(tmp_path)
        root = member.parents[1]
        u.Tests.git_run(
            member,
            "remote",
            "set-url",
            c.Infra.GIT_ORIGIN,
            u.Tests.WorktreeFixture.governed_repository_url("foreign-member"),
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="subproject origin differs from its .gitmodules URL")

    def test_member_checkout_without_pyproject_fails_closed(
        self,
        tmp_path: Path,
    ) -> None:
        """A present member checkout must carry its native project declaration."""
        member = self._attached_member(tmp_path)
        root = member.parents[1]
        (member / c.PYPROJECT_FILENAME).unlink()

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="repository has no pyproject.toml")

    def test_makefile_bootstrap_accepts_unprovisioned_declared_member(
        self,
        tmp_path: Path,
    ) -> None:
        """The setup Makefile renders before a declared member is checked out."""
        member = self._attached_member(tmp_path)
        root = member.parents[1]
        relative = member.relative_to(root).as_posix()
        for command in (
            (c.Infra.GIT, "submodule", "absorbgitdirs", "--", relative),
            (c.Infra.GIT, "submodule", "deinit", "-f", "--", relative),
        ):
            tm.ok(u.Cli.run_checked(command, cwd=root))

        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        plan = tm.ok(
            FlextInfraCodegenConform.Generate(
                repository_root=root,
                state=m.Infra.CodegenConformState(
                    repository_root=root,
                    request=request,
                ),
            ).plan(
                request,
            ),
        )

        planned = tuple(item.path for item in plan.files)
        for destination in c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS:
            tm.that(planned, has=root / destination)
        tm.fail(
            FlextInfraWorkspaceDetector.load_workspace_spec(root),
            has="governed subproject checkout is missing",
        )

    def test_composed_self_load_records_its_workspace_checkout(
        self,
        tmp_path: Path,
    ) -> None:
        """A composed project keeps its own coordinates and the root ledger."""
        member = self._attached_member(tmp_path)

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        # Topology is the declared role alone; being checked out inside a
        # workspace right now is the Git fact carried by ``editable``.
        tm.that(workspace.repository.path, eq=Path())
        tm.that(workspace.repository.role, eq=c.Infra.MakeProfile.STANDALONE)
        tm.ok(workspace.repository.editable)
        tm.that(tm.not_none(workspace.beads).workspace, eq="parent-workspace")

    def test_composed_self_load_accepts_a_self_coordinate_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """One declaration loads standalone and inside a workspace unchanged."""
        member = self._attached_member(tmp_path)
        u.Tests.WorktreeFixture.override_repository_declaration(
            member,
            {"uv_link_mode": "clone"},
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))

        tm.that(workspace.repository.path, eq=Path())
        tm.that(workspace.repository.role, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(workspace.repository.uv_link_mode, eq="clone")

    def test_standalone_rejects_a_manifest_that_claims_the_workspace_role(
        self,
        tmp_path: Path,
    ) -> None:
        """Topology is observed from Git; a declared role fails closed."""
        root = self._self_named_governed_root(tmp_path, "manifest-role-claim")
        u.Tests.WorktreeFixture.override_repository_declaration(
            root,
            {"role": c.Infra.MakeProfile.WORKSPACE.value},
        )

        result = FlextInfraWorkspaceDetector.load_workspace_spec(root)

        tm.fail(result, has="role")

    @staticmethod
    def test_workspace_excludes_governed_non_python_gitlinks_from_codegen(
        tmp_path: Path,
    ) -> None:
        """Keep provider-owned services outside Python conformance ownership."""
        root = tmp_path / "workspace"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            beads=u.Tests.BeadsIdentity(
                workspace="root-workspace",
                database="root-database",
                issue_prefix="root-prefix",
            ),
        )
        python_project = "fixture-python"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root / python_project,
            python_project,
            beads=u.Tests.BeadsIdentity(
                workspace="python-workspace",
                database="python-database",
                issue_prefix="python-prefix",
            ),
            beads_owner=False,
        )
        u.Tests.WorktreeFixture.link_member_beads(
            root / python_project,
            root,
            workspace_name="root-workspace",
            database="root-database",
            issue_prefix="root-prefix",
        )
        service_project = "fixture-service"
        service_root = root / service_project
        service_root.mkdir()
        (service_root / "go.mod").write_text(
            "module github.com/flext-sh/fixture-service\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(
            service_root,
            origin_url=u.Tests.WorktreeFixture.governed_repository_url(service_project),
        )
        u.Tests.WorktreeFixture.write_gitmodules(
            root,
            (python_project, service_project),
        )
        # Participation is declared natively: an absent flag inherits it, so
        # the provider-owned service opts out in its own .gitmodules section.
        tm.ok(
            u.Cli.run_checked(
                (
                    c.Infra.GIT,
                    "config",
                    "-f",
                    c.Infra.GITMODULES,
                    f"submodule.{service_project}.flext-managed",
                    c.ParserBooleanToken.FALSE,
                ),
                cwd=root,
            ),
        )

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            tuple(project.path.as_posix() for project in workspace.subprojects),
            eq=(python_project,),
        )
        tm.that(workspace.external_dependency_paths, eq=(Path(service_project),))
        tm.that(
            FlextInfraWorkspaceDetector.workspace_analysis_exclusion_paths(workspace),
            eq=(Path(service_project),),
        )
