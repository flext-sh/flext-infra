"""Behavior contract for the FLEXT workspace manifest v2 cutover.

Proves the atomic v1->v2 evolution:
  S1  schema version const == 2 (a version:1 document is rejected)
  S2  RepositoryRef carries checkout/codegen/package/editable/read_only;
      WorkspaceSpec.version rejects 1 (hard cutover, no v1 acceptance)
  S3  a fully-specified v2 workspace document validates

The schema, model, and closed vocabularies form one atomic public contract.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra
from flext_infra import c, m, t


class TestsWorkspaceManifestV2Contract:
    """Prove the hard v1-to-v2 workspace-manifest cutover."""

    @staticmethod
    def _schema_path() -> Path:
        """Return the packaged workspace schema path."""
        root = Path(flext_infra.__file__).resolve().parent
        return root / "schemas" / "workspace.schema.json"

    @staticmethod
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
    ) -> t.MutableMappingKV[str, t.JsonValue]:
        """Build one complete v2 repository payload."""
        return {
            "name": name,
            "distribution": name,
            "provider": "flext-sh",
            "url": f"https://github.com/flext-sh/{name}.git",
            "branch": "0.20.0-dev",
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

    @classmethod
    def _v2_workspace(cls) -> t.MutableMappingKV[str, t.JsonValue]:
        """Build one complete v2 workspace payload."""
        root = cls._v2_repository(
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
        member = cls._v2_repository(
            "flext-core",
            path="flext-core",
            checkout="submodule",
            codegen="conform",
            package=True,
            editable=True,
            read_only=False,
        )
        return {
            "version": c.Infra.WORKSPACE_MANIFEST_VERSION,
            "name": "flext",
            "repository": root,
            "members": [member],
            "content_only": [],
            "exclusions": [],
        }

    def test_schema_pins_version_const_2(self) -> None:
        """Pin the JSON schema version to the canonical v2 constant."""
        schema = json.loads(self._schema_path().read_text(encoding="utf-8"))
        tm.that(
            schema["properties"]["version"]["const"],
            eq=c.Infra.WORKSPACE_MANIFEST_VERSION,
        )

    def test_schema_requires_v2_repository_fields(self) -> None:
        """Require every v2 topology and mutability field in repository entries."""
        schema = json.loads(self._schema_path().read_text(encoding="utf-8"))
        required = schema["$defs"]["repository"]["required"]
        for field in ("checkout", "codegen", "package", "editable", "read_only"):
            tm.that(required, has=field)

    def test_checkout_and_codegen_enums_exist(self) -> None:
        """Expose closed typed vocabularies for checkout and codegen."""
        tm.that(
            frozenset(member.value for member in c.Infra.CheckoutKind),
            eq=frozenset({"root", "submodule", "independent"}),
        )
        tm.that(
            frozenset(member.value for member in c.Infra.CodegenKind),
            eq=frozenset({"conform", "python", "none"}),
        )

    def test_repository_ref_accepts_v2_fields(self) -> None:
        """Validate all five v2 fields into their canonical typed contract."""
        ref = m.Infra.RepositoryRef.model_validate(
            self._v2_repository(
                "flext-core",
                path="flext-core",
                checkout="independent",
                codegen="python",
                package=True,
                editable=True,
                read_only=False,
            )
        )
        tm.that(ref.checkout, eq=c.Infra.CheckoutKind.INDEPENDENT)
        tm.that(ref.codegen, eq=c.Infra.CodegenKind.PYTHON)
        tm.that(ref.package, eq=True)
        tm.that(ref.editable, eq=True)
        tm.that(ref.read_only, eq=False)

    def test_workspace_spec_rejects_version_1(self) -> None:
        """Reject a v1 workspace after the hard cutover."""
        doc = self._v2_workspace()
        doc["version"] = c.Infra.WORKSPACE_MANIFEST_VERSION - 1
        with pytest.raises(c.ValidationError):
            m.Infra.WorkspaceSpec.model_validate(doc)

    def test_workspace_spec_accepts_v2_document(self) -> None:
        """Validate a complete v2 document into typed repository contracts."""
        spec = m.Infra.WorkspaceSpec.model_validate(self._v2_workspace())
        tm.that(spec.version, eq=c.Infra.WORKSPACE_MANIFEST_VERSION)
        tm.that(spec.repository.checkout, eq=c.Infra.CheckoutKind.ROOT)
        tm.that(spec.members[0].checkout, eq=c.Infra.CheckoutKind.SUBMODULE)
