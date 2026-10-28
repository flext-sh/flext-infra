"""Native Pyright proves exported contracts and rejects private consumers.

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

from typing import TYPE_CHECKING

import pytest

from flext_infra.deps import FlextInfraEnsurePyrightConfigPhase
from flext_infra.gates import FlextInfraPyrightGate
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPyrightPublicContract:
    """Exercise the configured semantic owner with real source and type stubs."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("partially_generated", [False, True])
    def test_generated_facade_letter_remains_a_type_alias(
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
        *,
        partially_generated: bool,
    ) -> None:
        """Upstream imports cannot share the locally published type-alias binding."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        framework = package.parent / "framework"
        framework.mkdir()
        (framework / "__init__.py").write_text(
            "class FrameworkProtocols:\n"
            "    class Sample:\n"
            "        class Item:\n"
            "            label: str\n"
            "p = FrameworkProtocols\n"
            "__all__ = ['FrameworkProtocols', 'p']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        owners = package / "_protocols"
        owners.mkdir()
        (owners / "base.py").write_text(
            "from typing import Protocol\n"
            "class SampleProtocolsBase(Protocol):\n"
            "    def status(self) -> str: ...\n"
            "__all__ = ['SampleProtocolsBase']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (owners / "__init__.py").write_text(
            "from .base import SampleProtocolsBase\n"
            "__all__ = ['SampleProtocolsBase']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        facade = package / "protocols.py"
        inherited = "framework_p" if partially_generated else "p"
        facade.write_text(
            "from framework import p\n"
            + (
                "from framework import p as framework_p\n"
                if partially_generated
                else ""
            )
            + f"class SampleProtocols({inherited}):\n"
            f"    class Sample({inherited}.Sample):\n"
            "        pass\n"
            "p = SampleProtocols\n"
            "__all__ = ['SampleProtocols', 'p']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.facade_source_project(root) as (project, sources):
            generated = tm.not_none(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                )
            )
        facade.write_text(generated, encoding=c.DEFAULT_ENCODING)
        (package.parent / "consumer.py").write_text(
            f"from {package.name}.protocols import p\n"
            "def identity(value: p.Sample.Item) -> p.Sample.Item:\n"
            "    return value\n",
            encoding=c.DEFAULT_ENCODING,
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        FlextInfraEnsurePyrightConfigPhase(
            tool_config_document,
            codegen=tm.ok(u.Infra.load_codegen_inputs(root)).spec,
        ).apply_payload(
            payload,
            context=m.Infra.PyprojectAnalyzerContext(
                is_root=False,
                project_dir=root,
                declared_python_dirs=(package.parent.relative_to(root).as_posix(),),
                declared_python_dirs_are_complete=True,
            ),
        )
        (root / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding=c.DEFAULT_ENCODING,
        )
        result = FlextInfraPyrightGate(root).check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=root / ".reports"),
        )
        tm.that(result.result.passed, eq=True, msg=result.raw_output)
        tm.that(result.issues, eq=(), msg=result.raw_output)
        with u.Infra.facade_source_project(root) as (project, sources):
            tm.that(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                ),
                eq=generated,
            )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("selected", ["first", "second", "workspace"])
    def test_homonymous_test_facades_resolve_in_their_own_project(
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
        selected: str,
    ) -> None:
        """Identical facade imports resolve distinct inherited member contracts."""
        rules = tool_config_document.tools.pyright.path_rules
        projects = (
            ("first", "int", "7"),
            ("second", "str", "'second'"),
        )
        for name, annotation, value in projects:
            root = tmp_path / name
            tests = root / "tests"
            tests.mkdir(parents=True)
            (root / rules.source_dir).mkdir(parents=True, exist_ok=True)
            (tests / "__init__.py").write_text(
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from tests.constants import c\n",
                encoding="utf-8",
            )
            (tests / "constants.py").write_text(
                "from typing import ClassVar\n"
                "class Rules:\n"
                f"    RULES_CATALOG_BASIC: ClassVar[{annotation}] = {value}\n"
                "class Constants:\n"
                "    class Tests(Rules):\n"
                "        pass\n"
                "c = Constants\n",
                encoding="utf-8",
            )
            (tests / "consumer.py").write_text(
                "from tests import c, r\n"
                f"def catalog() -> {annotation}:\n"
                "    return c.Tests.RULES_CATALOG_BASIC\n",
                encoding="utf-8",
            )
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
            payload["project"] = {"name": name, "version": "0.1.0"}
            FlextInfraEnsurePyrightConfigPhase(
                tool_config_document,
                codegen=u.Infra.load_codegen_inputs(root).unwrap().spec,
            ).apply_payload(
                payload,
                context=m.Infra.PyprojectAnalyzerContext(
                    is_root=False,
                    project_dir=root,
                    declared_python_dirs=(rules.source_dir, "tests"),
                    declared_python_dirs_are_complete=True,
                ),
            )
            (root / c.PYPROJECT_FILENAME).write_text(
                u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
                encoding="utf-8",
            )
        project = tmp_path / selected
        if selected == "workspace":
            project = tmp_path
            u.Tests.declare_workspace_projects(tmp_path, ("first", "second"))
            u.Tests.write_project_beads_config(tmp_path, selected)
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
            payload["project"] = {"name": selected, "version": "0.1.0"}
            FlextInfraEnsurePyrightConfigPhase(
                tool_config_document,
                codegen=u.Infra.load_codegen_inputs(project).unwrap().spec,
            ).apply_payload(
                payload,
                context=m.Infra.PyprojectAnalyzerContext(
                    is_root=True, repository_root=project
                ),
            )
            (project / c.PYPROJECT_FILENAME).write_text(
                u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
                encoding="utf-8",
            )
        context = m.Infra.GateContext(
            repository_root=project,
            reports_dir=project / ".reports",
        )
        result = FlextInfraPyrightGate(project).check(project, context)

        tm.that(result.result.passed, eq=True, msg=result.raw_output)
        tm.that(result.issues, eq=(), msg=result.raw_output)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("consumer", "private"),
        [
            (
                (
                    "import os as operating_system\n"
                    "def exit_child() -> None:\n"
                    "    operating_system._exit(0)\n"
                ),
                False,
            ),
            (
                (
                    "from owner import Owner\n"
                    "def observe(value: Owner) -> int:\n"
                    "    return value._secret\n"
                ),
                True,
            ),
            (
                (
                    "from owner import Owner\n"
                    "def exit_child(os: Owner) -> None:\n"
                    "    os._exit(0)\n"
                ),
                True,
            ),
            (
                (
                    "from owner import _public\n"
                    "def observe() -> int:\n"
                    "    return _public()\n"
                ),
                False,
            ),
        ],
    )
    def test_publicness_uses_resolved_owner(
        tmp_path: Path,
        tool_config_document: m.Infra.ToolConfigDocument,
        consumer: str,
        *,
        private: bool,
    ) -> None:
        """Aliases and explicit exports stay public; shadowed receivers do not."""
        rules = tool_config_document.tools.pyright.path_rules
        roots = tuple(dict.fromkeys((*rules.env_dirs, rules.project_root)))
        for index, root in enumerate(roots):
            directory = tmp_path / root / "fixtures"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"consumer_{index}.py").write_text(consumer, encoding="utf-8")
        (tmp_path / rules.source_dir / "owner.py").write_text(
            '__all__ = ["Owner", "_public"]\n'
            "class Owner:\n"
            "    _secret: int = 1\n"
            "    def _exit(self, code: int) -> None:\n"
            "        self._secret = code\n"
            "def _public() -> int:\n"
            "    return 1\n",
            encoding="utf-8",
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python({})
        FlextInfraEnsurePyrightConfigPhase(
            tool_config_document,
            codegen=u.Infra.load_codegen_inputs(tmp_path).unwrap().spec,
        ).apply_payload(
            payload,
            context=m.Infra.PyprojectAnalyzerContext(
                is_root=False,
                project_dir=tmp_path,
                declared_python_dirs=roots,
                declared_python_dirs_are_complete=True,
            ),
        )
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / ".reports",
        )
        result = FlextInfraPyrightGate(tmp_path).check(tmp_path, context)

        private_issues = tuple(
            issue for issue in result.issues if issue.code == "reportPrivateUsage"
        )
        tm.that(bool(private_issues), eq=private)
        tm.that(result.result.passed, eq=not private, msg=result.raw_output)
        if private:
            tm.that(len(private_issues), eq=len(roots), msg=result.raw_output)
