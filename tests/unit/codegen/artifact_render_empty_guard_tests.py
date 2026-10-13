"""Contract tests for the empty-render publication guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraConfig, c, config
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
    empty render in, typed failure out, naming the template, the
    destination, and the declaration cause.
    """

    @staticmethod
    def _plan_render(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        content: str,
    ) -> tuple[p.Result[m.Infra.CodegenPlan], Path, Path]:
        """Plan a real declared template with isolated config and source inputs."""
        entry = next(
            entry
            for entry in config.Infra.codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        source = entry.source
        if source is None:
            pytest.fail("the declared Makefile renderer must have a template source")
        templates = tmp_path / "templates"
        shutil.copytree(u.Infra.codegen_templates_root(config.Infra.codegen), templates)
        # A nonempty conditional source renders exactly the supplied test content.
        (templates / source).write_text(
            "{% if false %}undeclared capability{% endif %}" + content,
            encoding="utf-8",
        )
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        for path in FlextInfraConfig.ssot_config_dir().glob("*.yaml"):
            shutil.copyfile(path, config_dir / path.name)
        tm.ok(
            u.Cli.yaml_dump(
                config_dir / c.Infra.CODEGEN_LOCAL_OVERRIDES_FILENAME,
                {"Infra": {"codegen": {"templates": {"root": str(templates)}}}},
            ),
        )
        root = tmp_path / "project"
        root.mkdir()
        u.Tests.copy_tracked_mise_seeds(root)
        repository = u.Tests.repository_ref("fixture-project")
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        with monkeypatch.context() as environment:
            environment.setenv("FLEXT_INFRA_CONFIG_DIR", str(config_dir))
            FlextInfraConfig.reset_for_testing()
            try:
                planned = FlextInfraCodegenConform(
                    repository_root=root,
                    initial_workspace=workspace,
                ).plan(request)
            finally:
                FlextInfraConfig.reset_for_testing()
        return planned, source, root / entry.destination

    @staticmethod
    def test_empty_render_fails_loud_naming_template_and_cause(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A 0-byte render is a typed failure naming template and cause."""
        refused, source, destination = (
            TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
                tmp_path,
                monkeypatch,
                "",
            )
        )
        tm.that(refused.failure, eq=True)
        tm.that(
            refused.error,
            has=str(source),
        )
        tm.that(
            refused.error,
            has=destination.name,
        )
        tm.that(refused.error, has="render produced no content")
        tm.that(refused.error, has="consumer declaration error")
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_whitespace_render_fails_loud_with_template_stage_prefix(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A whitespace-only render is refused and carries the planner banner."""
        refused, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            monkeypatch,
            "  \n\t\n",
        )
        tm.that(refused.failure, eq=True)
        tm.that(refused.error, has="stage=templates ")
        tm.that(refused.error, has="repository=")
        tm.that(refused.error, has="publishing a 0-byte artifact is forbidden")
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_rendered_content_passes_through_verbatim(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A render with real content passes through byte-exact."""
        content = "ready:\n\t@echo ready\n"
        kept, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            monkeypatch,
            content,
        )
        tm.that(kept.failure, eq=False)
        plan = tm.ok(kept)
        tm.that(u.Tests.planned_text(plan, destination.name), eq=content)
        tm.that(destination.exists(), eq=False)
