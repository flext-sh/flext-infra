"""Tests for canonical dependency source selection by topology role.

The attached root owns the local ``workspace = true`` overlay. Publishable
members retain their catalog Git provenance so the same package metadata works
outside the workspace; uv applies the root overlay when resolving them locally.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, config, m, u
from flext_tests import tm

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


def _workspace_with_consumer() -> m.Infra.WorkspaceSpec:
    workspace = _workspace()
    consumer = _repository(
        "flext-api",
        role=_ROLE.WORKSPACE_MEMBER,
        path="flext-api",
        checkout=c.Infra.CheckoutKind.SUBMODULE,
    )
    return workspace.model_copy(update={"members": (*workspace.members, consumer)})


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
    def test_attached_root_never_gets_git_specifier(self) -> None:
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
            '[project]\nname = "acme-platform"\nversion = "0.1.0"\n'
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

    def test_publishable_member_keeps_catalog_git_provenance(self) -> None:
        workspace = _workspace_with_consumer()
        provider = workspace.members[0]
        publishable_member = (
            f'[project]\nname = "{workspace.members[1].distribution}"\n'
            'version = "0.1.0"\n'
            'dependencies = ["flext-core"]\n'
        )

        result = u.Infra.pyproject_dependencies_conform(
            publishable_member,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{provider.distribution} @ git+{provider.url}@{provider.branch}"],
        )

    def test_attached_root_rejects_explicit_member_source(self) -> None:
        workspace = _workspace()
        member = workspace.members[0]
        attached_root = _PYPROJECT.replace(
            'dependencies = ["flext-core"]',
            (
                f'dependencies = ["{member.distribution} @ '
                f'git+{member.url}@{member.branch}"]'
            ),
            1,
        )

        result = u.Infra.pyproject_dependencies_conform(
            attached_root,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.that(result.failure, eq=True)
        tm.that(
            result.error or "",
            has="attached workspace dependency declares direct source",
        )

        local_result = u.Infra.pyproject_dependencies_conform(
            attached_root.replace(
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
            has="attached workspace dependency declares direct source",
        )

    def test_publishable_member_rejects_unmapped_direct_source(self) -> None:
        """Fail closed when no typed workspace repository owns a direct source."""
        workspace = _workspace_with_consumer()
        consumer = workspace.members[1]
        result = u.Infra.pyproject_dependencies_conform(
            (
                f'[project]\nname = "{consumer.distribution}"\n'
                'version = "0.1.0"\n'
                'dependencies = ["flext-unmapped @ '
                'git+https://github.com/flext-sh/flext-unmapped.git@main"]\n'
            ),
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
        )

        tm.fail(result, has="repository catalog lacks required distribution")

    def test_root_workspace_overlay_resolves_publishable_member_with_uv(
        self, tmp_path: Path
    ) -> None:
        """Prove uv resolves member Git metadata through the root workspace overlay."""
        workspace = _workspace_with_consumer()
        provider, consumer = workspace.members
        root = tmp_path / "workspace-root"
        provider_root = root / provider.path
        consumer_root = root / consumer.path
        provider_root.mkdir(parents=True)
        consumer_root.mkdir(parents=True)
        root_source = f"""[project]
name = "{workspace.repository.distribution}"
version = "0.1.0"
dependencies = ["{provider.distribution}", "{consumer.distribution}"]

[tool.uv]
package = false

[tool.uv.workspace]
members = ["{provider.path.as_posix()}", "{consumer.path.as_posix()}"]

[tool.uv.sources.{provider.distribution}]
workspace = true

[tool.uv.sources.{consumer.distribution}]
workspace = true
"""
        root_rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                root_source,
                repositories=(workspace.repository, *workspace.members),
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
            )
        )
        consumer_rendered = tm.ok(
            u.Infra.pyproject_dependencies_conform(
                (
                    f'[project]\nname = "{consumer.distribution}"\n'
                    'version = "0.1.0"\n'
                    f'dependencies = ["{provider.distribution}"]\n'
                ),
                repositories=(workspace.repository, *workspace.members),
                workspace=workspace,
                workspace_mode=c.Infra.WorkspaceMode.WORKSPACE,
            )
        )
        (root / c.Infra.PYPROJECT_FILENAME).write_text(root_rendered, encoding="utf-8")
        (provider_root / c.Infra.PYPROJECT_FILENAME).write_text(
            (f'[project]\nname = "{provider.distribution}"\nversion = "0.1.0"\n'),
            encoding="utf-8",
        )
        (consumer_root / c.Infra.PYPROJECT_FILENAME).write_text(
            consumer_rendered, encoding="utf-8"
        )

        lock_result = tm.ok(
            u.Cli.run_raw(
                [c.Infra.UV, "lock", "--offline", "--project", str(root)],
                cwd=root,
                timeout=c.DEFAULT_TIMEOUT_SECONDS,
                env={"UV_CACHE_DIR": str(tmp_path / "uv-cache")},
                remove_env_keys=(
                    "MYPYPATH",
                    "PYTHONPATH",
                    "UV_PROJECT",
                    "UV_PROJECT_ENVIRONMENT",
                    "VIRTUAL_ENV",
                ),
            )
        )

        tm.that(lock_result.exit_code, eq=0)
        lock_payload = tomllib.loads(
            (root / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8")
        )
        provider_packages = [
            package
            for package in lock_payload["package"]
            if package["name"] == provider.distribution
        ]
        tm.that(len(provider_packages), eq=1)
        provider_source = provider_packages[0]["source"]
        tm.that(provider_source.get("editable"), eq=provider.path.as_posix())
        tm.that("git" in provider_source, eq=False)

    def test_standalone_replaces_workspace_source_with_git_requirement(self) -> None:
        workspace = _workspace()

        result = u.Infra.pyproject_dependencies_conform(
            _PYPROJECT,
            repositories=(workspace.repository, *workspace.members),
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
        )

        member = workspace.members[0]
        document = tomllib.loads(tm.ok(result))
        tm.that(
            document["project"]["dependencies"],
            eq=[f"{member.distribution} @ git+{member.url}@{member.branch}"],
        )
        uv_config = document.get("tool", {}).get("uv", {})
        tm.that("sources" in uv_config, eq=False)
