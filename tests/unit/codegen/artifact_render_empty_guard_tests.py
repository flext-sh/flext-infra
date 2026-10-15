"""Contract tests for the empty-render publication guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraConfig, c
from flext_infra.codegen import FlextInfraCodegenConform
from tests import tm, u

if TYPE_CHECKING:
    from tests import m, p


class TestsFlextInfraArtifactRenderEmptyGuard:
    """A managed render that produced no content must fail loud, never publish.

    A workflow fragment gated on an undeclared capability layer (the
    ``private_dependency_auth`` incident, bead cosmos-dxtk7) rendered 0 bytes
    and was emitted verbatim: consumers inspected the directory, saw the
    artifact present, and concluded the capability was delivered while every
    step it owns was silently absent. The render funnel owns the refusal:
    empty render in, typed planning issue out, naming the template, the
    destination, and the declaration cause.
    """

    @staticmethod
    def _plan_render(
        tmp_path: Path,
        content: str,
    ) -> tuple[p.Result[m.Infra.CodegenPlan], Path, Path]:
        """Plan a template declared through the target's repository-local config.

        Returns:
            The planning result, template source path, and destination path.

        """
        root = tmp_path / "project"
        root.mkdir()
        codegen = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        entry = next(
            entry
            for entry in codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        source = tm.not_none(entry.source)
        templates = tmp_path / "templates"
        shutil.copytree(u.Infra.codegen_templates_root(codegen), templates)
        # A nonempty conditional source renders exactly the supplied test content.
        (templates / source).write_text(
            "{% if false %}undeclared capability{% endif %}" + content,
            encoding="utf-8",
        )
        _, _, local_config = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        local_config.parent.mkdir()
        tm.ok(
            u.Cli.yaml_dump(
                local_config,
                {"Infra": {"codegen": {"templates": {"root": str(templates)}}}},
            ),
        )
        effective = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        tm.that(u.Infra.codegen_templates_root(effective), eq=templates)
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.initialize_git_repo(root)
        repository = u.Tests.repository_ref("fixture-project")
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        planned = FlextInfraCodegenConform(
            repository_root=root,
            initial_workspace=workspace,
        ).plan(request)
        return planned, source, root / entry.destination

    @staticmethod
    def test_empty_render_fails_loud_naming_template_and_cause(
        tmp_path: Path,
    ) -> None:
        """A 0-byte render produces a planning issue naming template and cause."""
        refused, source, destination = (
            TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
                tmp_path,
                "",
            )
        )
        plan = tm.ok(refused)
        tm.that(bool(plan.issues), eq=True)
        diagnostic = "\n".join(issue.message for issue in plan.issues)
        tm.that(
            diagnostic,
            has=str(source),
        )
        tm.that(
            diagnostic,
            has=destination.name,
        )
        tm.that(diagnostic, has="render produced no content")
        tm.that(diagnostic, has="consumer declaration error")
        tm.that(any(file.path == destination for file in plan.files), eq=False)
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_whitespace_render_fails_loud_with_template_stage_prefix(
        tmp_path: Path,
    ) -> None:
        """A whitespace-only render is refused and carries the planner banner."""
        refused, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            "  \n\t\n",
        )
        plan = tm.ok(refused)
        tm.that(bool(plan.issues), eq=True)
        diagnostic = "\n".join(issue.message for issue in plan.issues)
        tm.that(diagnostic, has="stage=templates ")
        tm.that(diagnostic, has="repository=")
        tm.that(diagnostic, has="publishing a 0-byte artifact is forbidden")
        tm.that(any(file.path == destination for file in plan.files), eq=False)
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_rendered_content_passes_through_verbatim(
        tmp_path: Path,
    ) -> None:
        """A render with real content passes through byte-exact."""
        content = "ready:\n\t@echo ready\n"
        kept, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            content,
        )
        tm.that(kept.failure, eq=False)
        plan = tm.ok(kept)
        tm.that(bool(plan.issues), eq=False)
        tm.that(u.Tests.planned_text(plan, destination.name), eq=content)
        tm.that(destination.exists(), eq=False)
