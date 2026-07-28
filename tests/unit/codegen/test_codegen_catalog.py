"""Validate the typed repository catalog through its public configuration file."""

from __future__ import annotations

from pathlib import Path

import pytest
from packaging.requirements import Requirement

from flext_cli import u
from flext_infra import config, m, t
from flext_tests import tm


def test_codegen_catalog_is_tracked_typed_and_accepts_external_workspace() -> None:
    """Keep the engine catalog owned while accepting consumer-declared topology."""
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
    workspace = m.Infra.WorkspaceSpec.model_validate({
        "version": 2,
        "name": "consumer-root",
        "repository": {
            "name": "consumer-root",
            "distribution": "consumer-root",
            "provider": "consumer-owned",
            "url": "https://example.invalid/consumer/root.git",
            "branch": "dev",
            "path": ".",
            "role": "workspace-root",
            "state": "active",
            "profile": "workspace-root",
            "checkout": "root",
            "codegen": "conform",
            "package": False,
            "editable": False,
            "read_only": False,
        },
        "members": (
            {
                "name": "consumer-member",
                "distribution": "consumer-member",
                "provider": "consumer-owned",
                "url": "https://example.invalid/consumer/member.git",
                "branch": "dev",
                "path": "apps/member",
                "role": "workspace-member",
                "state": "active",
                "profile": "workspace-member",
                "checkout": "submodule",
                "codegen": "conform",
                "package": True,
                "editable": True,
                "read_only": False,
            },
        ),
        "exclusions": (),
    })

    tm.that(repositories, empty=False)
    tm.that(workspace.repository.provider, eq="consumer-owned")
    tm.that(tuple(member.name for member in workspace.members), eq=("consumer-member",))


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
        *project.dev,
        *(
            requirement
            for profile in project.dependency_profiles
            for requirement in (*profile.runtime, *profile.codegen)
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
