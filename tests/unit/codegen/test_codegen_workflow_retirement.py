"""Public conformance preserves authored workflows and release capability.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, codegen, config, infra, m, main, workspace
from tests import c, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport


class TestsFlextInfraCodegenWorkflowRetirement:
    """Exercise scaffold and existing-tree conformance through the public facade."""

    pytestmark = pytest.mark.slow

    @staticmethod
    def _declared_workspace(
        root: Path,
        *,
        publishes_release: bool,
    ) -> m.Infra.WorkspaceSpec:
        """Declare release capability through the real repository manifest.

        Returns:
            The resulting ``m.Infra.WorkspaceSpec``.

        """
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        manifest_path = u.Tests.write_standalone_workspace_manifest(
            root,
            config.Infra.name,
        )
        manifest = m.Infra.WorkspaceManifestSpec.model_validate(
            tm.ok(u.Cli.config_load(manifest_path)).data,
        )
        manifest = manifest.model_copy(
            update={
                "repository": manifest.repository.model_copy(
                    update={"publishes_release": publishes_release},
                ),
            },
        )
        tm.ok(u.Cli.yaml_dump(manifest_path, manifest.model_dump(mode="json")))
        declaration = m.Infra.RepositoryDeltaSpec(
            publishes_release=publishes_release,
            project=manifest.project,
        )
        tm.ok(
            u.Cli.yaml_dump(
                manifest_path.with_name(c.Infra.CODEGEN_CONFIG_FILENAME),
                {
                    "Infra": {
                        "codegen": {
                            "repository": declaration.model_dump(
                                mode="json",
                                exclude_unset=True,
                            ),
                        },
                    },
                },
            ),
        )
        return tm.ok(workspace.FlextInfraWorkspaceDetector.load_workspace_spec(root))

    @staticmethod
    @pytest.mark.parametrize("declared_release", [False, True])
    @pytest.mark.parametrize("marker", [None, *c.Infra.TEMPLATE_GENERATED_MARKERS])
    def test_retirement_requires_both_exclusion_and_codegen_authorship(
        infra_git_repo: Path,
        *,
        declared_release: bool,
        marker: str | None,
    ) -> None:
        """Effective target policy and current markers determine desired presence."""
        root = infra_git_repo
        spec = TestsFlextInfraCodegenWorkflowRetirement._declared_workspace(
            root,
            publishes_release=declared_release,
        )
        target = tm.ok(workspace.FlextInfraWorkspaceDetector.conform_target(root, spec))
        tm.that(target.publishes_release, eq=declared_release)
        catalog = config.Infra.codegen
        managed = {item.path.as_posix() for item in catalog.managed_files}
        workflows = tuple(
            entry
            for entry in catalog.templates.entries
            if entry.delegate == "render"
            and entry.destination in managed
            and Path(entry.destination).parts[:2] == (".github", "workflows")
        )
        content = "name: Repository workflow\non: workflow_dispatch\njobs: {}\n"
        if marker is not None:
            content = f"# {marker}\n{content}"
        for entry in workflows:
            workflow = root / entry.destination
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text(content, encoding=c.DEFAULT_ENCODING)

        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.WORKFLOWS,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        plan = tm.ok(
            codegen.FlextInfraCodegenConform(repository_root=root).plan(request),
        )

        workflow_paths = {root / entry.destination for entry in workflows}
        retired = {
            file.path
            for file in plan.files
            if file.path in workflow_paths and file.desired_content is None
        }
        expected = {
            root / entry.destination
            for entry in workflows
            if marker is not None
            and (
                target.make_profile not in entry.profiles
                or (entry.requires_release_protocol and not target.publishes_release)
            )
        }
        tm.that(retired, eq=expected)
        for path in workflow_paths:
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=content)

    @staticmethod
    @pytest.mark.parametrize("declared_release", [False, True])
    def test_release_workflows_converge_for_effective_repository_policy(
        infra_git_repo: Path,
        *,
        declared_release: bool,
    ) -> None:
        """The public workflow command converges for both repository policies."""
        root = infra_git_repo
        TestsFlextInfraCodegenWorkflowRetirement._declared_workspace(
            root,
            publishes_release=declared_release,
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.WORKFLOWS,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.that(
            main(
                [
                    "codegen",
                    "generate",
                    "--root",
                    str(root),
                    "--what",
                    request.what.value,
                    "--scope",
                    request.scope.value,
                ],
            ),
            eq=0,
        )
        target = tm.ok(workspace.FlextInfraWorkspaceDetector.conform_target(root))
        tm.that(target.publishes_release, eq=declared_release)
        releases = tuple(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.delegate == "render"
            and Path(entry.destination).parts[:2] == (".github", "workflows")
        )
        for entry in releases:
            tm.that(
                (root / entry.destination).is_file(),
                eq=target.make_profile in entry.profiles
                and (not entry.requires_release_protocol or declared_release),
            )
        scaffold_content = {
            root / entry.destination: (root / entry.destination).read_bytes()
            for entry in releases
            if (root / entry.destination).is_file()
        }

        conformed = tm.ok(infra.codegen_conform(request))

        release_paths = {root / entry.destination for entry in releases}
        tm.that(release_paths.intersection(conformed.written_files), empty=True)
        for path in release_paths:
            if path in scaffold_content:
                tm.that(path.read_bytes(), eq=scaffold_content[path])
            else:
                tm.fail(path.exists())
