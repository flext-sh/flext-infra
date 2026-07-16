"""RED contract for FLEXT workspace manifest v2 cutover.

Proves the atomic v1->v2 evolution:
  S1  schema version const == 2 (a version:1 document is rejected)
  S2  RepositoryRef carries checkout/codegen/package/editable/read_only;
      WorkspaceSpec.version rejects 1 (hard cutover, no v1 acceptance)
  S3  a fully-specified v2 workspace document validates

These tests fail against the current v1 implementation for the RIGHT reason
(missing fields / version:1 still accepted) and go green only after the
schema + model + enums land together in one atomic change.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from flext_infra import c, m


def _schema_path() -> Path:
    import flext_infra

    root = Path(flext_infra.__file__).resolve().parent
    return root / "schemas" / "workspace.schema.json"


def _v2_repository(
    name: str,
    *,
    path: str,
    checkout: str,
    codegen: str,
    package: bool,
    editable: bool,
    read_only: bool,
    role: str = "workspace-member",
    state: str = "active",
    profile: str | None = "workspace-member",
) -> dict[str, object]:
    return {
        "name": name,
        "distribution": name,
        "provider": "flext-sh",
        "url": f"https://github.com/flext-sh/{name}.git",
        "branch": "0.12.0-dev",
        "path": path,
        "role": role,
        "state": state,
        "profile": profile,
        "checkout": checkout,
        "codegen": codegen,
        "package": package,
        "editable": editable,
        "read_only": read_only,
    }


def _v2_workspace() -> dict[str, object]:
    root = _v2_repository(
        "flext",
        path=".",
        checkout="root",
        codegen="conform",
        package=False,
        editable=False,
        read_only=False,
        role="workspace-root",
        profile="workspace-root",
    )
    member = _v2_repository(
        "flext-core",
        path="flext-core",
        checkout="submodule",
        codegen="conform",
        package=True,
        editable=True,
        read_only=False,
    )
    return {
        "version": 2,
        "name": "flext",
        "repository": root,
        "members": [member],
        "content_only": [],
        "exclusions": [],
    }


def test_schema_pins_version_const_2() -> None:
    """S1: the JSON schema pins manifest version to const 2."""
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    assert schema["properties"]["version"]["const"] == 2


def test_schema_requires_v2_repository_fields() -> None:
    """S1: repository entries must declare the five v2 fields."""
    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    required = schema["$defs"]["repository"]["required"]
    for field in ("checkout", "codegen", "package", "editable", "read_only"):
        assert field in required, f"{field} missing from repository.required"


def test_checkout_and_codegen_enums_exist() -> None:
    """S2: closed vocabularies for checkout and codegen are typed constants."""
    assert {e.value for e in c.Infra.CheckoutKind} == {
        "root",
        "submodule",
        "independent",
    }
    assert {e.value for e in c.Infra.CodegenKind} == {
        "conform",
        "python",
        "none",
    }


def test_repository_ref_accepts_v2_fields() -> None:
    """S2: RepositoryRef validates the five new v2 fields."""
    ref = m.Infra.RepositoryRef.model_validate(
        _v2_repository(
            "flext-core",
            path="flext-core",
            checkout="independent",
            codegen="python",
            package=True,
            editable=True,
            read_only=False,
        )
    )
    assert ref.checkout is c.Infra.CheckoutKind.INDEPENDENT
    assert ref.codegen is c.Infra.CodegenKind.PYTHON
    assert ref.package is True
    assert ref.editable is True
    assert ref.read_only is False


def test_workspace_spec_rejects_version_1() -> None:
    """S2: a version:1 workspace is rejected after the cutover."""
    doc = _v2_workspace()
    doc["version"] = 1
    with pytest.raises(ValidationError):
        m.Infra.WorkspaceSpec.model_validate(doc)


def test_workspace_spec_accepts_v2_document() -> None:
    """S3: a fully specified v2 workspace validates."""
    spec = m.Infra.WorkspaceSpec.model_validate(_v2_workspace())
    assert spec.version == 2
    assert spec.repository.checkout is c.Infra.CheckoutKind.ROOT
    assert spec.members[0].checkout is c.Infra.CheckoutKind.SUBMODULE
