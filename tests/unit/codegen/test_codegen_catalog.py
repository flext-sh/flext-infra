"""Validate the typed repository catalog through its public configuration file."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_cli import u
from flext_tests import tm
from packaging.requirements import Requirement

from flext_infra import c, config, m, t


def test_codegen_catalog_is_tracked_typed_and_models_external_workspace() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    catalog_path = repository_root / "config" / "codegen.yaml"

    tracked = u.Cli.run_raw(
        ["git", "ls-files", "--error-unmatch", "config/codegen.yaml"],
        cwd=repository_root,
    )
    process = tm.ok(tracked)
    tm.that(process.exit_code, eq=0)
    tm.that(process.stdout.strip(), eq="config/codegen.yaml")

    payload = u.Cli.yaml_load_mapping(catalog_path)
    infra = t.Cli.JSON_MAPPING_ADAPTER.validate_python(payload["Infra"])
    catalog = t.Cli.JSON_MAPPING_ADAPTER.validate_python(infra["codegen"])
    provider_payloads = t.Cli.JSON_LIST_ADAPTER.validate_python(catalog["providers"])
    repository_payloads = t.Cli.JSON_LIST_ADAPTER.validate_python(
        catalog["repositories"]
    )
    typed_catalog = m.Infra.CodegenConfigSpec.model_validate(catalog)
    tm.that(typed_catalog.repositories, len=len(repository_payloads))
    provider = m.Infra.ProviderSpec(
        name="consumer",
        organization="consumer",
        base_url="https://github.com/consumer",
        branch="main",
    )
    repositories = (
        m.Infra.RepositoryRef(
            name="consumer-root",
            distribution="consumer-root",
            provider=provider.name,
            url=f"{provider.base_url}/consumer-root.git",
            branch=provider.branch,
            path=Path(),
            role=c.Infra.RepositoryRole.WORKSPACE_ROOT,
            profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
            checkout=c.Infra.CheckoutKind.ROOT,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=False,
            editable=False,
            read_only=False,
        ),
        m.Infra.RepositoryRef(
            name="consumer-member",
            distribution="consumer-member",
            provider=provider.name,
            url=f"{provider.base_url}/consumer-member.git",
            branch=provider.branch,
            path=Path("consumer-member"),
            role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
            profile=c.Infra.MakeProfile.WORKSPACE_MEMBER,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        ),
        m.Infra.RepositoryRef(
            name="consumer-content",
            distribution="consumer-content",
            provider=provider.name,
            url=f"{provider.base_url}/consumer-content.git",
            branch=provider.branch,
            path=Path("consumer-content"),
            role=c.Infra.RepositoryRole.CONTENT_ONLY,
            state=c.Infra.RepositoryState.CONTENT_ONLY,
            profile=None,
            checkout=c.Infra.CheckoutKind.SUBMODULE,
            codegen=c.Infra.CodegenKind.NONE,
            package=False,
            editable=False,
            read_only=True,
        ),
    )
    external_catalog = m.Infra.CodegenConfigSpec.model_validate({
        **catalog,
        "providers": (*provider_payloads, provider.model_dump(mode="json")),
        "repositories": (
            *repository_payloads,
            *(repository.model_dump(mode="json") for repository in repositories),
        ),
    })
    workspace = m.Infra.WorkspaceSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=repositories[0].name,
        repository=repositories[0],
        members=(repositories[1],),
        content_only=(repositories[2],),
    )

    tm.that(external_catalog.repositories[-len(repositories) :], eq=repositories)
    tm.that(
        (workspace.repository, *workspace.members, *workspace.content_only),
        eq=repositories,
    )


def test_toolchain_rejects_exact_patch_selectors() -> None:
    """Keep runtime selectors on compatible major.minor release lines."""
    payload = config.Infra.codegen.toolchain.model_dump()
    payload["python_version"] = "3.13.11"

    with pytest.raises(ValueError, match="python_version"):
        m.Infra.ToolchainSpec.model_validate(payload)


def test_scaffold_dependencies_delegate_upper_bounds_to_uv() -> None:
    """Keep library requirements floor-only and let uv own concrete resolution."""
    project = config.Infra.codegen.scaffold.project
    requirements = [
        *(
            requirement
            for profile in project.dependency_profiles
            for requirement in (*profile.runtime, *profile.codegen, *profile.dev)
        )
    ]
    forbidden = {"<", "<=", "==", "===", "~="}

    for raw_requirement in requirements:
        parsed = Requirement(raw_requirement)
        tm.that(
            forbidden.isdisjoint(specifier.operator for specifier in parsed.specifier),
            eq=True,
            msg=raw_requirement,
        )
