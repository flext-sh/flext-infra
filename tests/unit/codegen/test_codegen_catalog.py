"""Typed codegen catalog contract tests."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_cli import u
from flext_infra import m


def test_codegen_catalog_is_tracked_typed_and_accepts_cosmos_workspace() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    catalog_path = repository_root / "config" / "codegen.yaml"

    tracked = u.Cli.run_raw(
        ["git", "ls-files", "--error-unmatch", "config/codegen.yaml"],
        cwd=repository_root,
    )
    assert tracked.success
    assert tracked.value.exit_code == 0
    assert tracked.value.stdout.strip() == "config/codegen.yaml"

    payload = u.Cli.yaml_load_mapping(catalog_path)
    infra = payload["Infra"]
    assert isinstance(infra, Mapping)
    catalog = infra["codegen"]
    assert isinstance(catalog, Mapping)
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

    assert tuple(
        repository.model_dump(mode="json") for repository in workspace_repositories
    ) == tuple(repository.model_dump(mode="json") for repository in cosmos)
