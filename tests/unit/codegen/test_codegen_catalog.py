"""Validate the typed repository catalog through its public configuration file."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_cli import u
from flext_tests import tm
from packaging.requirements import Requirement

from flext_infra import config, m, t


def test_codegen_catalog_is_tracked_typed_and_accepts_cosmos_workspace() -> None:
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
    repositories = m.TypeAdapter(tuple[m.Infra.RepositoryRef, ...]).validate_python(
        catalog["repositories"]
    )
    by_name = {repository.name: repository for repository in repositories}
    cosmos_names = (
        "cosmos-main",
        "cosmos-charts",
        "cosmos-gitops",
        "cosmos-inventory",
        "cosmos-automation",
        "cosmos-frontend",
        "cosmos-observability",
        "cosmos-templates",
        "cosmos-zabbix",
        "cosmos-monitoring",
        "cosmos-hook",
        "cosmosec-backend",
        "cosmosec-frontend",
    )
    cosmos = tuple(by_name[name] for name in cosmos_names)

    workspace = m.Infra.WorkspaceSpec.model_validate({
        "version": 2,
        "name": "cosmos-main",
        "repository": cosmos[0],
        "members": cosmos[1:3],
        "content_only": cosmos[3:],
        "exclusions": (),
    })
    workspace_repositories = (
        workspace.repository,
        *workspace.members,
        *workspace.content_only,
    )

    tm.that(
        tuple(
            repository.model_dump(mode="json") for repository in workspace_repositories
        ),
        eq=tuple(repository.model_dump(mode="json") for repository in cosmos),
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
        ),
    ]
    forbidden = {"<", "<=", "==", "===", "~="}

    for raw_requirement in requirements:
        parsed = Requirement(raw_requirement)
        tm.that(
            forbidden.isdisjoint(specifier.operator for specifier in parsed.specifier),
            eq=True,
            msg=raw_requirement,
        )
