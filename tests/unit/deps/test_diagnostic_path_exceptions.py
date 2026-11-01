"""Authorized diagnostic path exceptions render both type checkers from one entry.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_infra.deps.phases import (
    FlextInfraEnsurePyreflyConfigPhase,
    FlextInfraEnsurePyrightConfigPhase,
)
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsDiagnosticPathExceptions:
    """One SSOT entry scopes Pyright and Pyrefly rule levels to its root."""

    @staticmethod
    def _entry(root: str) -> t.JsonDict:
        """Declare one authorized exception changing rules of both checkers.

        Returns:
            The YAML-shaped declaration of the exception.

        """
        return {
            "root": root,
            "rationale": "Third-party base class redeclares the attribute.",
            "authorization": {
                "operator-words": "Approve exception",
                "date": "2026-11-01",
                "channel": "Claude Code chat",
            },
            "changes": [
                {
                    "checker": c.Infra.PYRIGHT,
                    "rule": "reportAssignmentType",
                    "old": "error",
                    "new": "none",
                },
                {
                    "checker": c.Infra.PYRIGHT,
                    "rule": "reportIncompatibleVariableOverride",
                    "old": "error",
                    "new": "none",
                },
                {
                    "checker": c.Infra.PYREFLY,
                    "rule": "bad-override",
                    "old": "error",
                    "new": "ignore",
                },
            ],
        }

    @staticmethod
    def _document(
        tool_config_document: m.Infra.ToolConfigDocument,
        entry: t.JsonDict,
    ) -> m.Infra.ToolConfigDocument:
        """Validate the canonical document carrying one declared exception.

        Returns:
            The validated tooling document.

        """
        payload = tool_config_document.model_dump(
            by_alias=True, exclude_computed_fields=True
        )
        tools = u.Tests.toml_mapping(payload["tools"])
        pyright = u.Tests.toml_mapping(tools[c.Infra.PYRIGHT])
        rules = u.Tests.toml_mapping(pyright["path-rules"])
        return m.Infra.ToolConfigDocument.model_validate({
            **payload,
            "tools": {
                **tools,
                c.Infra.PYRIGHT: {
                    **pyright,
                    "path-rules": {**rules, "diagnostic-path-exceptions": [entry]},
                },
            },
        })

    @staticmethod
    def _project(tmp_path: Path, root: str) -> Path:
        """Create one governed project whose exception root exists on disk.

        Returns:
            The project directory.

        """
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        project = tmp_path / "flext-sample"
        target = project / root
        target.parent.mkdir(parents=True)
        target.write_text("VALUE = 1\n", encoding="utf-8")
        (project / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname='flext-sample'\nversion='0.1.0'\n",
            encoding="utf-8",
        )
        u.Tests.write_project_beads_config(project, "flext-sample")
        u.Tests.initialize_git_repo(project)
        return project

    @staticmethod
    def _tool_table(payload: t.MutableJsonMapping, tool: str) -> t.JsonMapping:
        """Read one rendered native tool table.

        Returns:
            The rendered ``[tool.<tool>]`` mapping.

        """
        return u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])[tool])

    def test_exception_without_authorization_fails_validation(
        self,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """No declaration is admitted without its tracker key or operator words."""
        entry = self._entry("src/flext_sample/models.py")
        unauthorized = {
            key: value for key, value in entry.items() if key != "authorization"
        }
        with u.Tests.raises(m.ValidationError, match="authorization"):
            self._document(tool_config_document, unauthorized)

    def test_absent_root_fails_loud(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """A declared root missing from the project stops rendering."""
        project = self._project(tmp_path, "src/flext_sample/__init__.py")
        document = self._document(
            tool_config_document, self._entry("src/flext_sample/absent.py")
        )
        context = m.Infra.PyprojectAnalyzerContext(is_root=False, project_dir=project)
        for phase in (
            FlextInfraEnsurePyrightConfigPhase(document, codegen=config.Infra.codegen),
            FlextInfraEnsurePyreflyConfigPhase(document, codegen=config.Infra.codegen),
        ):
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
            with u.Tests.raises(FileNotFoundError, match="absent.py"):
                phase.apply_payload(payload, context=context)

    def test_one_entry_renders_both_checkers(
        self,
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
    ) -> None:
        """The same entry yields the Pyright environment and the Pyrefly sub-config."""
        root = "src/flext_sample/models.py"
        project = self._project(tmp_path, root)
        document = self._document(tool_config_document, self._entry(root))
        rules = document.tools.pyright.path_rules
        context = m.Infra.PyprojectAnalyzerContext(is_root=False, project_dir=project)

        pyright_payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        FlextInfraEnsurePyrightConfigPhase(
            document, codegen=config.Infra.codegen
        ).apply_payload(pyright_payload, context=context)
        environments = [
            u.Tests.toml_mapping(item)
            for item in u.Tests.toml_list(
                self._tool_table(pyright_payload, c.Infra.PYRIGHT)[
                    "executionEnvironments"
                ]
            )
        ]
        source = next(env for env in environments if env["root"] == rules.source_dir)
        tm.that(
            environments[0],
            eq={
                "root": root,
                c.Infra.REPORT_PRIVATE_USAGE: rules.source_report_private_usage,
                c.Infra.EXTRA_PATHS: source[c.Infra.EXTRA_PATHS],
                "reportAssignmentType": "none",
                "reportIncompatibleVariableOverride": "none",
            },
        )

        pyrefly_payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        FlextInfraEnsurePyreflyConfigPhase(
            document, codegen=config.Infra.codegen
        ).apply_payload(pyrefly_payload, context=context)
        tm.that(
            self._tool_table(pyrefly_payload, c.Infra.PYREFLY)[c.Infra.SUB_CONFIG],
            eq=[
                {
                    c.Infra.SUB_CONFIG_MATCHES: root,
                    c.Infra.SUB_CONFIG_ERRORS: {"bad-override": "ignore"},
                }
            ],
        )


__all__: list[str] = ["TestsFlextInfraDepsDiagnosticPathExceptions"]
