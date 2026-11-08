"""Verify ci.yml and docs.yml grant packages: read only to declared consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tests import c, t, tm, u


class TestsFlextInfraCiPackageRegistryRead:
    """A GitHub Packages consumer reads its registry; nobody else can."""

    workflows = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows"
    )

    @classmethod
    def _job_permissions(
        cls, *, packages_read: bool, template: str = "ci.yml.j2"
    ) -> Mapping[str, t.JsonValue]:
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="fixture-registry-consumer",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="develop",
            ci_trigger_branches=("develop", "main"),
            overrides=u.CodegenTestSupport.Ci.WorkflowRenderOverrides(
                packages_read=packages_read,
            ),
        )
        rendered = tm.ok(u.Cli.template_render(cls.workflows / template, spec))
        adapter = u.Cli.JSON_MAPPING_ADAPTER
        document = adapter.validate_python(tm.ok(u.Cli.yaml_parse(rendered)))
        permissions: t.MutableJsonMapping = {}
        for name, job in adapter.validate_python(document["jobs"]).items():
            permissions[name] = adapter.validate_python(job)["permissions"]
        return permissions

    def test_declared_consumer_ci_job_reads_packages(self) -> None:
        """Test declared consumer ci job reads packages."""
        permissions = self._job_permissions(packages_read=True)

        tm.that(permissions["ci"], eq={"contents": "read", "packages": "read"})

    def test_undeclared_consumer_stays_contents_only(self) -> None:
        """Test undeclared consumer stays contents only."""
        permissions = self._job_permissions(packages_read=False)

        for job_permissions in permissions.values():
            tm.that(job_permissions, eq={"contents": "read"})

    def test_declared_consumer_docs_jobs_read_packages(self) -> None:
        """Docs generation resolves the same packages as the ci gates."""
        declared = self._job_permissions(packages_read=True, template="docs.yml.j2")
        undeclared = self._job_permissions(packages_read=False, template="docs.yml.j2")

        for job in ("docs-quality", "build"):
            tm.that(
                u.Cli.JSON_MAPPING_ADAPTER.validate_python(declared[job]).get(
                    "packages"
                ),
                eq="read",
            )
            tm.that(
                u.Cli.JSON_MAPPING_ADAPTER.validate_python(undeclared[job]).get(
                    "packages"
                ),
                eq=None,
            )
