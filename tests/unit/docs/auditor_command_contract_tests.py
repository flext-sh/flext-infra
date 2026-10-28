"""Behavior tests for the public documentation command-contract audit.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraAuditorCommandContract:
    """Prove canonical Make, Testmon, and public-test documentation policy."""

    @pytest.fixture
    @staticmethod
    def command_contract_scope(infra_test_workspace: Path) -> m.Infra.DocScope:
        """Declare the same repository identity in Git and the typed topology.

        Returns:
            The resulting ``m.Infra.DocScope``.

        """
        name = "infra-pkg"
        u.Tests.write_project_beads_config(infra_test_workspace, name)
        u.Tests.write_standalone_workspace_manifest(infra_test_workspace, name)
        u.Tests.initialize_git_repo(
            infra_test_workspace,
            origin_url=u.Tests.repository_ref(name).url,
        )
        return m.Infra.DocScope(
            name=name,
            path=infra_test_workspace,
            report_dir=infra_test_workspace / ".reports" / "docs",
            package_name="infra_pkg",
        )

    @staticmethod
    def test_scans_recursive_live_docs_from_typed_scope(
        command_contract_scope: m.Infra.DocScope,
    ) -> None:
        """Test scans recursive live docs from typed scope."""
        infra_test_workspace = command_contract_scope.path
        docs_root = infra_test_workspace / "docs"
        governed = {
            docs_root / "guides" / "nested" / "commands.md": (
                "```bash\nruff check src\n```\n"
            ),
            docs_root / "standards" / "nested" / "commands.md": (
                "```bash\nmake test PROJECT=demo\n```\n"
            ),
        }
        for path, content in governed.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            u.write_file(path, content)
        ungoverned = docs_root / "architecture" / "historical.md"
        ungoverned.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(ungoverned, "```bash\nruff check src\n```\n")
        excluded = docs_root / "standards" / "historical" / "commands.md"
        excluded.parent.mkdir(parents=True, exist_ok=True)
        u.write_file(excluded, "```bash\nruff check src\n```\n")
        u.write_file(
            infra_test_workspace / c.PYPROJECT_FILENAME,
            (
                "[project]\nname='infra-pkg'\nversion='0.0.0'\n\n"
                "[tool.flext.docs]\n"
                'exclude_docs=["standards/historical/**"]\n'
            ),
        )
        issues = u.Infra.docs_command_contract_issues(command_contract_scope)

        tm.that(len(issues), eq=2)
        tm.that(
            {issue.file for issue in issues},
            eq={"docs/guides/nested/commands.md", "docs/standards/nested/commands.md"},
        )

    @staticmethod
    @pytest.mark.parametrize("verb_name", ["publish-preview", "archive-assets"])
    @pytest.mark.parametrize(
        ("declared", "expected"),
        [
            (True, ""),
            (True, "legacy `APPLY` flag is exterminated"),
            (False, "not declared"),
        ],
    )
    def test_audits_repository_declared_verbs(
        command_contract_scope: m.Infra.DocScope,
        verb_name: str,
        *,
        declared: bool,
        expected: str,
    ) -> None:
        """Test audits repository declared verbs."""
        scope = command_contract_scope
        spec = m.Infra.MakeVerbSpec(
            name=verb_name,
            description="Repository-owned operation",
        )
        u.Tests.write_standalone_workspace_manifest(
            scope.path,
            scope.name,
            extra_verbs=(spec,) if declared else (),
        )
        guide = scope.path / "docs/guides/commands.md"
        guide.parent.mkdir(parents=True)
        token = " APPLY=Y" if "APPLY" in expected else ""
        u.write_file(guide, f"```bash\nmake {verb_name}{token}\n```\n")

        issues = u.Infra.docs_command_contract_issues(scope)

        if expected:
            tm.that(len(issues), eq=1)
            tm.that(issues[0].message, has=expected)
        else:
            tm.that(issues, eq=[])

    @staticmethod
    def test_manifest_changes_update_the_live_contract(
        command_contract_scope: m.Infra.DocScope,
    ) -> None:
        """Test manifest changes update the live contract."""
        scope = command_contract_scope
        spec = m.Infra.MakeVerbSpec(
            name="publish-preview",
            description="Repository-owned operation",
        )
        guide = scope.path / "docs/guides/commands.md"
        guide.parent.mkdir(parents=True)
        u.write_file(guide, f"```bash\nmake {spec.name}\n```\n")
        u.Tests.write_standalone_workspace_manifest(
            scope.path,
            scope.name,
            extra_verbs=(spec,),
        )
        tm.that(u.Infra.docs_command_contract_issues(scope), eq=[])

        u.write_file(guide, f"```bash\nmake {spec.name} APPLY=Y\n```\n")
        legacy = u.Infra.docs_command_contract_issues(scope)
        tm.that(len(legacy), eq=1)
        tm.that(legacy[0].message, has="legacy `APPLY` flag is exterminated")

        renamed = m.Infra.MakeVerbSpec(
            name="archive-assets",
            description="Repository-owned operation",
        )
        u.Tests.write_standalone_workspace_manifest(
            scope.path,
            scope.name,
            extra_verbs=(renamed,),
        )
        u.write_file(guide, f"```bash\nmake {renamed.name}\n```\n")
        tm.that(u.Infra.docs_command_contract_issues(scope), eq=[])

    @staticmethod
    @pytest.mark.parametrize("with_guide", [False, True])
    def test_malformed_selected_topology_blocks_with_exact_cause(
        command_contract_scope: m.Infra.DocScope,
        *,
        with_guide: bool,
    ) -> None:
        """Test malformed selected topology blocks with exact cause."""
        scope = command_contract_scope
        if with_guide:
            guide = scope.path / "docs/guides/commands.md"
            guide.parent.mkdir(parents=True)
            spec = config.Infra.codegen.make.verbs[0]
            u.write_file(guide, f"```bash\nmake {spec.name}\n```\n")
        manifest = u.Tests.write_standalone_workspace_manifest(scope.path, scope.name)
        u.write_file(manifest, "version: [\n")
        loaded = u.Infra.load_workspace_manifest(scope.path)
        tm.fail(loaded)
        tm.that(loaded.error, has=str(manifest))

        with pytest.raises(ValueError, match=re.escape(loaded.error or "")) as caught:
            u.Infra.docs_command_contract_issues(scope)

        tm.that(str(caught.value), eq=loaded.error)

    @staticmethod
    def test_guide_projection_resolves_source_repository_contract(
        command_contract_scope: m.Infra.DocScope,
    ) -> None:
        """Test guide projection resolves source repository contract."""
        source_scope = command_contract_scope
        spec = m.Infra.MakeVerbSpec(
            name="publish-preview",
            description="Source repository operation",
        )
        manifest = u.Tests.write_standalone_workspace_manifest(
            source_scope.path,
            source_scope.name,
            extra_verbs=(spec,),
        )
        guide = source_scope.path / "docs/guides/commands.md"
        guide.parent.mkdir(parents=True)
        u.write_file(guide, f"```bash\nmake {spec.name}\n```\n")
        state = u.Cli.atomic_read_binary_file_state(guide, required=True)
        tm.ok(state)
        destination = source_scope.path / "member"
        destination.mkdir()
        scope = m.Infra.DocScope(
            name="member",
            path=destination,
            report_dir=destination / ".reports/docs",
        )

        projected = u.Infra.docs_project_guides_artifacts(
            scope,
            repository_root=source_scope.path,
        )

        tm.ok(projected)
        tm.that(len(projected.value), eq=1)
        tm.that(projected.value[0][1], eq=destination / "docs/guides/commands.md")
        tm.that(projected.value[0][2], has=f"make {spec.name}")

        u.write_file(manifest, "version: [\n")
        loaded = u.Infra.load_workspace_manifest(source_scope.path)
        tm.fail(loaded)
        blocked = u.Infra.docs_project_guides_artifacts(
            scope,
            repository_root=source_scope.path,
        )
        tm.fail(blocked)
        tm.that(blocked.error, eq=loaded.error)

    @staticmethod
    def test_member_guides_resolve_from_the_containing_workspace(
        command_contract_scope: m.Infra.DocScope,
        tmp_path: Path,
    ) -> None:
        """A member-scoped plan projects its containing workspace's guides.

        The workspace and a standalone checkout own their guides, which are
        never their own projections.
        """
        workspace_scope = command_contract_scope
        workspace = workspace_scope.path
        guide = workspace / "docs/guides/using-demo.md"
        guide.parent.mkdir(parents=True)
        u.write_file(guide, "# Using Demo\n\nWorkspace-owned guidance.\n")
        source = tmp_path / "member-source"
        source.mkdir()
        u.Tests.initialize_git_repo(source)
        source_guide = source / "docs/guides/local.md"
        source_guide.parent.mkdir(parents=True)
        u.write_file(source_guide, "# Local\n\nStandalone-owned guidance.\n")
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "--quiet",
                    str(source),
                    "member",
                ],
                cwd=workspace,
            ),
        )
        member = workspace / "member"
        member_scope = m.Infra.DocScope(
            name="member",
            path=member,
            report_dir=member / ".reports/docs",
        )

        attached = u.Infra.docs_project_guides_artifacts(
            member_scope,
            repository_root=member,
        )

        tm.ok(attached)
        tm.that(len(attached.value), eq=1)
        tm.that(attached.value[0][1], eq=member / "docs/guides/using-demo.md")
        tm.that(
            attached.value[0][2],
            eq=u.Infra.docs_sanitize_internal_anchor_links(
                u.Infra.docs_project_guide_content(
                    guide.read_text(encoding=c.DEFAULT_ENCODING),
                    member_scope.name,
                    guide.name,
                ),
            ),
        )
        for scope, root in (
            (workspace_scope, workspace),
            (
                m.Infra.DocScope(
                    name="member-source",
                    path=source,
                    report_dir=source / ".reports/docs",
                ),
                source,
            ),
        ):
            own = u.Infra.docs_project_guides_artifacts(scope, repository_root=root)
            tm.ok(own)
            tm.that(own.value, eq=())
