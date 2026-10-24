"""Target-owned complete CUSTOM requirements survive public generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from flext_infra import config, m
from flext_infra.codegen import FlextInfraCodegenConformExecute
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from tests import c, t, tm, u


class TestsFlextInfraCodegenRuntimeProfiles:
    """Tests for ``FlextInfraCodegenRuntimeProfiles``."""

    @staticmethod
    def _seed_member_workspace(
        tmp_path: Path,
        upstream: str,
        *,
        composed: bool,
    ) -> tuple[Path, Path, Path]:
        """Initialize the governed member (and parent when composed).

        The member manifest carries its own facade contract; a member
        cannot introduce another parent target through its manifest.

        Returns:
            The request root, the member checkout, and the member pyproject.

        """
        fixture = u.Tests.WorktreeFixture
        root = tmp_path / "workspace"
        member = root / "sample-member" if composed else tmp_path / "sample-member"
        if composed:
            fixture.initialize_governed_project(
                root,
                "sample-workspace",
                beads=u.Tests.BeadsIdentity(
                    workspace="sample-workspace",
                    database="sample_workspace",
                    issue_prefix="sample",
                ),
            )
        pyproject = fixture.initialize_governed_project(
            member,
            "sample-member",
            beads=u.Tests.BeadsIdentity(
                workspace="sample-workspace",
                database="sample_workspace",
                issue_prefix="sample",
            ),
        )
        observed = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(member))
        project = u.Tests.project_spec(observed.repository.name).model_copy(
            update={"upstream": upstream},
        )
        manifest = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=observed.repository.name,
            docs_audit=observed.docs_audit,
            repository=observed.repository,
            project=project,
            members=(
                u.Tests.repository_ref(
                    "unselected-project",
                    path=Path("unselected-project"),
                ),
            ),
        )
        manifest_path = member / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME
        tm.ok(u.Cli.yaml_dump(manifest_path, manifest.model_dump(mode="json")))
        if composed:
            fixture.attach_submodule(
                root,
                member,
                distribution="sample-member",
                relative_path="sample-member",
            )
        return root, member, pyproject

    @staticmethod
    def _declare_custom_dependencies(
        pyproject: Path,
        upstream: str,
    ) -> t.VariadicTuple[str]:
        """Author marker variants and a direct source in the target declaration.

        Returns:
            The declared requirement variants and the direct source.

        """
        declared = (
            u.Tests.flext_source(upstream.replace("_", "-")),
            "custom-runtime[feature]>=2; python_version < '3.14'",
            "custom-runtime[feature]>=3; python_version >= '3.14'",
            (
                "custom-artifact[extra] @ https://example.invalid/pkg.whl ;"
                " sys_platform == 'linux'"
            ),
        )
        payload = tm.ok(u.Cli.json_dumps(list(declared)))
        pyproject.write_text(
            "".join(
                f"dependencies = {payload}\n"
                if line.startswith("dependencies = ")
                else line
                for line in pyproject.read_text(encoding="utf-8").splitlines(
                    keepends=True
                )
            ),
            encoding="utf-8",
        )
        return declared

    @staticmethod
    def _protected_state(
        request_root: Path,
        member: Path,
        *,
        composed: bool,
    ) -> tuple[m.Infra.WorkspaceSpec, t.MappingKV[Path, bytes]]:
        """Snapshot the baseline workspace and the bytes conform must preserve.

        Returns:
            The observed workspace and the protected path-to-bytes mapping.

        """
        before = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(request_root))
        protected = {
            path: path.read_bytes()
            for path in (
                member / "config" / c.Infra.WORKSPACE_MANIFEST_FILENAME,
                member / "config" / c.Infra.BEADS_CONFIG_FILENAME,
                *((request_root / c.Infra.GITMODULES,) if composed else ()),
            )
        }
        return before, protected

    @staticmethod
    def _assert_render_retains_requirements(
        rendered: str,
        declared: t.VariadicTuple[str],
    ) -> str:
        """Public generation retains requirement variants, injecting only dev policy.

        Returns:
            The rendered text, returned unchanged once the assertions pass.

        """
        tm.that(
            Counter(
                Requirement(item)
                for item in u.Tests.toml_strings_at(rendered, "project", "dependencies")
            ),
            eq=Counter(Requirement(item) for item in declared),
        )
        tm.that(
            u.Tests.toml_table_at(rendered, "tool", "pyrefly", "errors"),
            eq=dict(config.Infra.tooling.settings["pyrefly.errors"]),
        )
        development = u.Tests.toml_strings_at(rendered, "dependency-groups", "dev")
        dev_names = [
            n for item in development if (n := u.Infra.dep_name(item)) is not None
        ]
        required_names = [
            n
            for item in config.Infra.codegen.scaffold.project.required_flext_dev
            if (n := u.Infra.dep_name(item)) is not None
        ]
        tm.that(
            dev_names,
            has=required_names,
        )
        return rendered

    @pytest.mark.parametrize(
        "upstream",
        tuple(
            base.module for base in config.Infra.codegen.scaffold.project.config_bases
        ),
    )
    @pytest.mark.parametrize("composed", [False, True])
    # Two complete governed pyproject renders per case (tooling context,
    # template, overlay, conform, taplo) over a real git fixture: measured
    # 3.3-4.9s per render under a four-worker phase, so each case exceeds the
    # bounded-phase item budget. Integration-scale, so it runs in the slow
    # phase under its per-item bound (rules/workflow/gate-budget.md), never a
    # raised limit.
    @pytest.mark.slow
    def test_target_requirements_survive_runtime_rendering(
        self,
        tmp_path: Path,
        upstream: str,
        *,
        composed: bool,
    ) -> None:
        """Standalone and parent plans consume the same member-owned requirements."""
        root, member, pyproject = self._seed_member_workspace(
            tmp_path,
            upstream,
            composed=composed,
        )
        declared = self._declare_custom_dependencies(pyproject, upstream)
        request_root = root if composed else member
        before, protected = self._protected_state(
            request_root,
            member,
            composed=composed,
        )
        request = u.Tests.conform_request(
            request_root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=(
                c.Infra.CodegenConformScope.DECLARED
                if composed
                else c.Infra.CodegenConformScope.SELF
            ),
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        service = FlextInfraCodegenConformExecute(
            repository_root=request_root,
            state=m.Infra.CodegenConformState(
                repository_root=request_root,
                request=request,
            ),
        )
        first = tm.ok(service.plan(request))
        rendered = self._assert_render_retains_requirements(
            u.Tests.codegen_file_text(
                next(item for item in first.files if item.path == pyproject),
            ),
            declared,
        )
        tm.that(first.workspace.repository, eq=before.repository)
        tm.that(first.workspace.subprojects, eq=before.subprojects)
        tm.that(first.workspace.beads, eq=before.beads)
        tm.that({item.path for item in first.files}, eq={pyproject})
        pyproject.write_text(rendered, encoding="utf-8")
        second = tm.ok(service.plan(request))
        tm.that(
            u.Tests.codegen_file_text(
                next(item for item in second.files if item.path == pyproject),
            ),
            eq=rendered,
        )
        for path, content in protected.items():
            tm.that(path.read_bytes(), eq=content)

    @staticmethod
    def test_custom_policy_can_be_explicitly_disabled() -> None:
        """An empty preservation policy still elects only the rendered requirements."""
        rendered = '[project]\nname = "sample"\ndependencies = ["owned>=2"]\n'
        live = '[project]\nname = "sample"\ndependencies = ["external[extra]>=1"]\n'
        result = tm.ok(
            u.Infra.overlay_preserved(rendered, live, preserve_project_keys=()),
        )
        tm.that(
            u.Tests.toml_strings_at(result, "project", "dependencies"),
            eq=("owned>=2",),
        )

    @staticmethod
    @pytest.mark.parametrize("invalid", ['["external>=1", 42]', '"external>=1"'])
    def test_invalid_custom_requirements_are_not_discarded(invalid: str) -> None:
        """Composition rejects malformed arrays rather than filtering their entries."""
        rendered = '[project]\nname = "sample"\ndependencies = ["owned>=2"]\n'
        live = f'[project]\nname = "sample"\ndependencies = {invalid}\n'
        tm.fail(
            u.Infra.overlay_preserved(rendered, live),
            has="validate runtime dependencies",
        )
