"""An attached member renders the workspace profile from every scope.

Operator decision on cosmos-8fmi7.1.9.5: a superproject gitlink renders the
WORKSPACE profile whether the superproject or the member runs generation, and
the workspace runtime provides the tools its attached members declare.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, t, tm, u

pytestmark = c.Tests.MARK.slow


class TestsFlextInfraCodegenAttachedWorkspaceProfile:
    """Root-scope and member-scope generation agree on an attached member."""

    SURFACES = (
        c.Infra.CodegenConformSurface.MAKEFILE,
        c.Infra.CodegenConformSurface.PYPROJECT,
        c.Infra.CodegenConformSurface.GITIGNORE,
    )

    @staticmethod
    def _attached_workspace(tmp_path: Path) -> tuple[Path, Path]:
        """Initialize a governed superproject with one attached member.

        Returns:
            The superproject root and the attached member checkout.

        """
        fixture = u.Tests.WorktreeFixture
        root = tmp_path / "workspace"
        member = root / "sample-member"
        beads = u.Tests.BeadsIdentity(
            workspace="sample-workspace",
            database="sample_workspace",
            issue_prefix="sample",
        )
        fixture.initialize_governed_project(root, "sample-workspace", beads=beads)
        fixture.initialize_governed_project(member, "sample-member", beads=beads)
        fixture.attach_submodule(
            root,
            member,
            distribution="sample-member",
            relative_path="sample-member",
        )
        return root, member

    @staticmethod
    def _declare_tool(project: Path, name: str, version: str) -> None:
        """Layer one toolchain tool over the project's codegen declaration."""
        path = project / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
        document = u.Cli.yaml_load_mapping(path) if path.exists() else {}
        infra = u.Cli.json_as_mapping(document.get("Infra", {}))
        codegen = u.Cli.json_as_mapping(infra.get("codegen", {}))
        tool: t.JsonDict = {"name": name, "version": version}
        tm.ok(
            u.Cli.yaml_dump(
                path,
                {
                    **document,
                    "Infra": {
                        **infra,
                        "codegen": {**codegen, "toolchain": {"tools": [tool]}},
                    },
                },
            )
        )

    @staticmethod
    def _plan(
        request_root: Path,
        surface: c.Infra.CodegenConformSurface,
        scope: c.Infra.CodegenConformScope,
    ) -> p.Result[p.Infra.CodegenPlan]:
        """Plan one surface from one scope without writing.

        Returns:
            The generation plan, or its failure.

        """
        request = u.Tests.conform_request(
            request_root,
            what=surface,
            scope=scope,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        return FlextInfraCodegenConform.Generate(
            repository_root=request_root,
            state=m.Infra.CodegenConformState(
                repository_root=request_root,
                request=request,
            ),
        ).plan(request)

    @classmethod
    def _member_files(
        cls,
        request_root: Path,
        member: Path,
        scope: c.Infra.CodegenConformScope,
    ) -> t.MutableMappingKV[Path, str]:
        """Collect the member's planned bytes for every compared surface.

        Returns:
            The member-relative path to rendered text mapping.

        """
        files: t.MutableMappingKV[Path, str] = {}
        for surface in cls.SURFACES:
            plan = tm.ok(cls._plan(request_root, surface, scope))
            files.update({
                item.path.relative_to(member): u.Tests.codegen_file_text(item)
                for item in plan.files
                if item.path.is_relative_to(member)
            })
        return files

    def test_attached_member_renders_identically_from_both_scopes(
        self, tmp_path: Path
    ) -> None:
        """The superproject and the member render the same member bytes."""
        root, member = self._attached_workspace(tmp_path)
        from_root = self._member_files(
            root, member, c.Infra.CodegenConformScope.DECLARED
        )
        from_member = self._member_files(
            member, member, c.Infra.CodegenConformScope.SELF
        )
        tm.that(set(from_root), has=Path(c.Infra.MAKEFILE_FILENAME))
        tm.that(from_member, eq=from_root)

    def test_workspace_runtime_provides_attached_member_tools(
        self, tmp_path: Path
    ) -> None:
        """A tool declared only by the member reaches the workspace runtime."""
        root, member = self._attached_workspace(tmp_path)
        self._declare_tool(member, "terraform", "1.9.8")
        plan = tm.ok(
            self._plan(
                root,
                c.Infra.CodegenConformSurface.MISE_CONFIG,
                c.Infra.CodegenConformScope.SELF,
            )
        )
        mise = next(
            item for item in plan.files if item.path == root / ".mise.toml"
        )
        tm.that(u.Tests.codegen_file_text(mise), has='"terraform" = "1.9.8"')

    def test_conflicting_member_tool_version_fails_loud(
        self, tmp_path: Path
    ) -> None:
        """Two effective versions of one tool name both declarations."""
        root, member = self._attached_workspace(tmp_path)
        self._declare_tool(root, "terraform", "1.9.7")
        self._declare_tool(member, "terraform", "1.9.8")
        tm.fail(
            self._plan(
                root,
                c.Infra.CodegenConformSurface.MISE_CONFIG,
                c.Infra.CodegenConformScope.SELF,
            ),
            has="workspace toolchain conflict for terraform",
        )
