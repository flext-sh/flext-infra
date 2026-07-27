"""Tests for canonical dependency source selection by topology role.

An attached workspace member has exactly one dependency source:
``[tool.uv.sources].<dist> = { workspace = true }``. Emitting a
``git+<url>@<branch>`` specifier for the same distribution creates a second,
contradictory source that ``uv`` silently overrides, so the declared remote
intent is never resolved.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u

_ROLE = c.Infra.RepositoryRole
# mro-o26p: provider identity, branch and base URL come from the config SSOT,
# never from literals repeated in the test.
_PROVIDER_SPEC = config.Infra.codegen.providers[0]
_PROVIDER = _PROVIDER_SPEC.name
_BRANCH = _PROVIDER_SPEC.branch


def _repository(
    distribution: str,
    *,
    role: c.Infra.RepositoryRole,
    path: str,
    checkout: c.Infra.CheckoutKind,
) -> m.Infra.RepositoryRef:
    return m.Infra.RepositoryRef(
        name=distribution,
        distribution=distribution,
        url=f"https://github.com/flext-sh/{distribution}.git",
        branch=_BRANCH,
        path=Path(path),
        role=role,
        provider=_PROVIDER,
        checkout=checkout,
        codegen=c.Infra.CodegenKind.CONFORM,
        package=True,
        editable=True,
        read_only=False,
    )


def _workspace() -> m.Infra.WorkspaceSpec:
    return m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name="workspace-root",
        repository=_repository(
            "workspace-root",
            role=_ROLE.WORKSPACE_ROOT,
            path=".",
            checkout=c.Infra.CheckoutKind.ROOT,
        ),
        members=(
            _repository(
                "flext-core",
                role=_ROLE.WORKSPACE_MEMBER,
                path="flext-core",
                checkout=c.Infra.CheckoutKind.SUBMODULE,
            ),
        ),
        content_only=(),
        exclusions=(),
    )


_PYPROJECT = """[project]
name = "workspace-root"
version = "0.1.0"
dependencies = ["flext-core"]

[dependency-groups]
workspace = ["flext-core"]

[tool.uv.workspace]
members = ["flext-core"]

[tool.uv.sources.flext-core]
workspace = true
"""


class TestsFlextInfraPyprojectConformTopologySources:
    def test_attached_member_never_gets_git_specifier(self) -> None:
        workspace = _workspace()

        result = u.Infra.pyproject_dependencies_conform(
            _PYPROJECT,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        rendered = tm.ok(result)
        document = tomllib.loads(rendered)
        group = document["dependency-groups"]["workspace"]
        runtime = document["project"]["dependencies"]

        tm.that(group, eq=["flext-core"])
        tm.that(runtime, eq=["flext-core"])

    def test_external_consumer_keeps_remote_branch_source(self) -> None:
        workspace = _workspace()
        external = (
            '[project]\nname = "cosmos-main"\nversion = "0.1.0"\n'
            'dependencies = ["flext-core"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            external,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        document = tomllib.loads(tm.ok(result))

        # The expected specifier is derived from the same declared repository
        # contract the generator reads - never a hardcoded URL or branch.
        member = workspace.members[0]
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{member.distribution} @ git+{member.url}@{member.branch}"],
        )

    def test_attached_member_uses_workspace_provenance(self) -> None:
        workspace = _workspace()
        attached = (
            '[project]\nname = "flext-api"\nversion = "0.1.0"\n'
            'dependencies = ["flext-core"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            attached,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        document = tomllib.loads(tm.ok(result))
        tm.that(document["project"]["dependencies"], eq=["flext-core"])

    def test_attached_member_rejects_explicit_source(self) -> None:
        workspace = _workspace()
        member = workspace.members[0]
        attached = (
            '[project]\nname = "flext-api"\nversion = "0.1.0"\n'
            f'dependencies = ["{member.distribution} @ git+{member.url}@{member.branch}"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            attached,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.that(result.failure, eq=True)
        tm.that(
            result.error or "", has="attached workspace dependency declares Git source"
        )

        local_result = u.Infra.pyproject_dependencies_conform(
            attached.replace(
                f"git+{member.url}@{member.branch}",
                "file:///home/marlonsc/flext/flext-core",
            ),
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.that(local_result.failure, eq=True)
        tm.that(
            local_result.error or "",
            has="attached workspace dependency declares Git source",
        )

    def test_standalone_rejects_workspace_source_without_git_requirement(self) -> None:
        workspace = _workspace()

        result = u.Infra.pyproject_dependencies_conform(
            _PYPROJECT,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        rendered = tm.ok(result)
        member = workspace.members[0]
        tm.that(
            rendered,
            has=f"{member.distribution} @ git+{member.url}@{member.branch}",
        )
        tm.that("workspace = true" not in rendered, eq=True)
