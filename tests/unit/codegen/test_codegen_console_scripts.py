"""Declared console scripts render into the generated [project.scripts] table.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from tests import c, m, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport

pytestmark = [c.Tests.MARK.slow]


class TestsFlextInfraCodegenConsoleScripts:
    """The pyproject surface publishes every declared console script."""

    @staticmethod
    def test_declared_console_scripts_render_beside_the_default_script(
        infra_git_repo: Path,
    ) -> None:
        """A declared script is published, and a second apply is a no-op."""
        root = infra_git_repo
        workspace = m.Infra.WorkspaceSpec.model_validate(
            TestsFlextInfraConformSupport.standalone_workspace(root),
            from_attributes=True,
        )
        project = workspace.project
        tm.that(project, none=False)
        if project is None:
            return
        package = tm.not_none(project.package_name)
        script = m.Infra.ConsoleScriptSpec(
            name=f"{package.replace('_', '-')}-hook",
            target=f"{package}.hook_client:HookClient.main",
        )
        declared = workspace.model_copy(
            update={
                "project": project.model_copy(update={"console_scripts": (script,)}),
            },
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(TestsFlextInfraConformSupport.conform_in_workspace(request, declared))
        published = (root / c.PYPROJECT_FILENAME).read_bytes()
        scripts = u.Tests.toml_mapping(
            tomllib.loads(published.decode(c.DEFAULT_ENCODING))["project"]["scripts"],
        )
        tm.that(scripts.get(script.name), eq=script.target)
        tm.ok(TestsFlextInfraConformSupport.conform_in_workspace(request, declared))
        tm.that((root / c.PYPROJECT_FILENAME).read_bytes(), eq=published)

    @staticmethod
    def test_console_script_target_rejects_a_non_entry_point_reference() -> None:
        """A target without module:attribute shape fails model validation."""
        with u.Tests.raises(m.ValidationError):
            m.Infra.ConsoleScriptSpec.model_validate(
                {"name": "demo-hook", "target": "not an entry point"},
            )
