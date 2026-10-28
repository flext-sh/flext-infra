"""Real Git and interpreter contracts for generated analyzer environments.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path
from typing import Literal

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.deps import FlextInfraEnsurePyrightConfigPhase
from tests import c, m, t, tm, u


class TestsFlextInfraRuntimeEnvironmentProjection:
    """Exercise projected paths with physical environments and real Git topology."""

    @staticmethod
    def _project(parent: Path, name: str) -> Path:
        """Construct one committed project through the shared fixture owners.

        Returns:
            The real repository containing its declared Python module.

        """
        root = parent / name
        root.mkdir()
        (root / c.PYPROJECT_FILENAME).write_text(
            f"[project]\nname='{name}'\nversion='0.1.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (root / "probe.py").write_text("VALUE: int = 1\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.write_project_beads_config(root, name)
        u.Tests.initialize_git_repo(root)
        return root

    @classmethod
    def _topology(
        cls,
        parent: Path,
        mode: Literal["standalone", "workspace", "member", "nested-member", "worktree"],
    ) -> tuple[Path, Path]:
        """Create the actual attachment or independent checkout under test.

        Returns:
            The selected project and its explicitly constructed environment owner.

        """
        workspace = cls._project(parent, "flext-projection-owner")
        if mode == "standalone":
            return workspace, workspace
        if mode == "worktree":
            lane = u.Tests.git_linked_lane(parent, workspace, "projection-lane")
            return lane, lane
        origin = cls._project(parent, "flext-projection-origin")
        relative = "packages/member" if mode == "nested-member" else "member"
        u.Tests.git_bootstrap(
            workspace,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                str(origin),
                relative,
            ),
        )
        u.Tests.git_bootstrap(
            workspace,
            (
                "config",
                "--file",
                c.Infra.GITMODULES,
                f"submodule.{relative}.branch",
                u.Tests.provider_branch(),
            ),
        )
        selected = workspace if mode == "workspace" else workspace / relative
        return selected, workspace

    @classmethod
    @pytest.mark.parametrize(
        "mode", ["standalone", "workspace", "member", "nested-member", "worktree"]
    )
    def test_editor_and_pyright_select_the_same_physical_environment(
        cls,
        tmp_path: Path,
        mode: Literal["standalone", "workspace", "member", "nested-member", "worktree"],
    ) -> None:
        """Opening a member alone still executes its workspace-owned interpreter."""
        project, owner = cls._topology(tmp_path, mode)
        interpreter = u.Tests.provision_runtime_environment(owner)
        rendered = tm.ok(
            FlextInfraCodegenConform.Generate.render_vscode_settings(
                project, codegen=config.Infra.codegen
            )
        )
        document = u.Tests.json_payload(rendered)
        editor_interpreter = u.type_adapter(str).validate_python(
            document["python.defaultInterpreterPath"]
        )
        selected = Path(editor_interpreter.replace("${workspaceFolder}", str(project)))
        tm.that(selected.parent.resolve(), eq=interpreter.parent.resolve())
        tm.that(selected.name, eq=interpreter.name)
        mypy_interpreters = u.Tests.toml_strings(
            document["mypy-type-checker.interpreter"]
        )
        tm.that(tuple(mypy_interpreters), eq=(editor_interpreter,))
        executed = tm.ok(
            u.Cli.capture(
                (str(selected), "-c", "import sys; print(sys.prefix)"),
                cwd=project,
            )
        ).strip()
        tm.that(
            Path(executed).resolve(),
            eq=(owner / c.Infra.ENVIRONMENT_DIRECTORY).resolve(),
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        phase = FlextInfraEnsurePyrightConfigPhase(
            config.Infra.tooling, codegen=config.Infra.codegen
        )
        context = m.Infra.PyprojectAnalyzerContext(
            is_root=mode == "workspace", repository_root=owner, project_dir=project
        )
        phase.apply_payload(payload, context=context, analysis_exclusions=())
        table = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["pyright"])
        environment_parent = u.type_adapter(str).validate_python(table["venvPath"])
        environment_name = u.type_adapter(str).validate_python(table["venv"])
        tm.that(
            (project / environment_parent / environment_name).resolve(),
            eq=Path(executed).resolve(),
        )
        tm.that(
            phase.apply_payload(payload, context=context, analysis_exclusions=()),
            empty=True,
        )
        settings = project / c.Infra.VSCODE_DIRNAME / c.Infra.VSCODE_SETTINGS_FILENAME
        settings.parent.mkdir(exist_ok=True)
        settings.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        tm.that(
            tm.ok(
                FlextInfraCodegenConform.Generate.render_vscode_settings(
                    project, codegen=config.Infra.codegen
                )
            ),
            eq=rendered,
        )

    @classmethod
    def test_explicit_mypy_command_does_not_borrow_an_installed_checker(
        cls, tmp_path: Path
    ) -> None:
        """A dependency-free selected environment fails rather than using the host."""
        project = cls._project(tmp_path, "flext-projection-isolated")
        u.Tests.provision_runtime_environment(project)
        document = u.Tests.json_payload(
            tm.ok(
                FlextInfraCodegenConform.Generate.render_vscode_settings(
                    project, codegen=config.Infra.codegen
                )
            )
        )
        interpreter = next(
            iter(u.Tests.toml_strings(document["mypy-type-checker.interpreter"]))
        ).replace("${workspaceFolder}", str(project))
        command = tuple(
            argument.replace("${interpreter}", interpreter)
            for argument in u.Tests.toml_strings(document["mypy-type-checker.path"])
        )
        result = tm.ok(u.Cli.run_raw((*command, "--version"), cwd=project))
        tm.that(u.Cli.process_succeeded(result.outcome), eq=False)
        tm.that(result.stderr, has="mypy")
