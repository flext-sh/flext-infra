"""Readonly namespace identities do not grant name-wide lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra._models.deps_tool_config_linters import (
    FlextInfraModelsDepsToolConfigLinters,
)
from flext_infra.gates import FlextInfraRuffLintGate
from tests import m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraReadonlyNamespaceContract:
    """Validate exact declarations independently of any project's spelling."""

    @staticmethod
    @pytest.mark.parametrize("name", ["Branch", "SettingsBranch", "Domain2"])
    @pytest.mark.parametrize("extension", [".py", ".pyi"])
    def test_identity_round_trip(name: str, extension: str) -> None:
        """Arbitrary valid namespaces retain every declared identity field."""
        payload = {
            "path": f"src/example/_protocols/base{extension}",
            "qualname": f"ExampleProtocols.Settings.{name}",
            "role": "protocol-instance-readonly-namespace",
            "return-type-owner": "example._protocols.base.ExampleProtocols.Branch",
            "producer-qualname": f"example._settings.ExampleSettings.{name}",
        }
        occurrence = FlextInfraModelsDepsToolConfigLinters.RuffReadonlyNamespaceOccurrence.model_validate(
            payload
        )
        tm.that(occurrence.model_dump(by_alias=True), eq=payload)

    @staticmethod
    @pytest.mark.parametrize(
        "path",
        [
            "/src/example.py",
            "../example.py",
            "src/../example.py",
            "./src/example.py",
            "src//example.py",
            "src/example.py/",
            "src/**/*.py",
            "src/example?.py",
            "src/[example].py",
            "src/{example}.py",
            "src\\example.py",
            "C:/src/example.py",
            "src/example.ipynb",
            "src/example.py\x00",
            "src/example\n.py",
        ],
    )
    def test_path_is_exact_and_project_relative(path: str) -> None:
        """Aliases, escaping paths, globs, and unsupported formats fail closed."""
        with pytest.raises(ValueError, match="exact project-relative Python path"):
            FlextInfraModelsDepsToolConfigLinters.RuffReadonlyNamespaceOccurrence(
                path=path,
                qualname="ExampleProtocols.Settings.Branch",
                role="protocol-instance-readonly-namespace",
                return_type_owner="example.Branch",
                producer_qualname="example.ExampleSettings.Branch",
            )

    @staticmethod
    @pytest.mark.parametrize(
        "field", ["qualname", "return-type-owner", "producer-qualname"]
    )
    @pytest.mark.parametrize(
        "identity",
        ["Branch", "example.*", "example..Branch", "example.Branch()", "example.class"],
    )
    def test_declaration_identity_rejects_patterns_and_expressions(
        field: str, identity: str
    ) -> None:
        """No identity field can become a pattern or executable expression."""
        payload = {
            "path": "src/example/_protocols/base.py",
            "qualname": "ExampleProtocols.Settings.Branch",
            "role": "protocol-instance-readonly-namespace",
            "return-type-owner": "example.Branch",
            "producer-qualname": "example.ExampleSettings.Branch",
        }
        payload[field] = identity
        with pytest.raises(ValueError, match="qualified declaration identity"):
            FlextInfraModelsDepsToolConfigLinters.RuffReadonlyNamespaceOccurrence.model_validate(
                payload
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("name", "producer"),
        [("branch", "branch"), ("BRANCH", "BRANCH"), ("Branch", "OtherBranch")],
    )
    def test_producer_member_is_paired(name: str, producer: str) -> None:
        """A declaration cannot authorize an unrelated producer member."""
        with pytest.raises(ValueError, match="paired PascalCase producer member"):
            contract = (
                FlextInfraModelsDepsToolConfigLinters.RuffReadonlyNamespaceOccurrence
            )
            contract.model_validate({
                "path": "src/example/_protocols/base.py",
                "qualname": f"ExampleProtocols.Settings.{name}",
                "role": "protocol-instance-readonly-namespace",
                "return-type-owner": "example.Branch",
                "producer-qualname": f"example.ExampleSettings.{producer}",
            })

    @staticmethod
    @pytest.mark.parametrize("role", ["method", "property", "class", "*"])
    def test_role_is_not_an_open_exemption(role: str) -> None:
        """Only the selected readonly Protocol occurrence role is representable."""
        with pytest.raises(ValueError, match="protocol-instance-readonly-namespace"):
            FlextInfraModelsDepsToolConfigLinters.RuffReadonlyNamespaceOccurrence.model_validate({
                "path": "src/example/_protocols/base.py",
                "qualname": "ExampleProtocols.Settings.Branch",
                "role": role,
                "return-type-owner": "example.Branch",
                "producer-qualname": "example.ExampleSettings.Branch",
            })

    @staticmethod
    def test_native_manifest_retains_stub_and_codemod_ignored_inputs(
        tmp_path: Path,
    ) -> None:
        """Ruff, not a second directory walk, elects complete naming inputs."""
        project = u.Tests.mk_project(
            tmp_path,
            "native-manifest",
            pyproject=(
                '[project]\nname = "native-manifest"\nversion = "0.0.0"\n'
                "[tool.ruff]\nexclude = []\nrespect-gitignore = false\n"
            ),
        )
        ignored = next(iter(config.Infra.codegen.source_scan_ignored))
        relative = ("src/plain.py", "src/contracts.pyi", f"{ignored}/selected.py")
        for name in relative:
            path = project / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("def BrokenName() -> None: ...\n", encoding="utf-8")
        gate = FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        tm.that(
            gate.readonly_namespace_sources(project, context, targets=(".",)),
            eq=tuple(sorted(project / name for name in (*relative, "pyproject.toml"))),
        )
        tm.that(
            gate.readonly_namespace_sources(
                project, context, targets=("src/contracts.pyi",)
            ),
            eq=(project / "src/contracts.pyi",),
        )

    @staticmethod
    def test_native_notebook_is_not_silently_removed(tmp_path: Path) -> None:
        """An unsupported native format blocks naming adaptation, not its lint."""
        project = u.Tests.mk_project(
            tmp_path,
            "notebook-manifest",
            pyproject=(
                '[project]\nname = "notebook-manifest"\nversion = "0.0.0"\n'
                '[tool.ruff]\ninclude = ["*.py", "*.pyi", "*.ipynb"]\n'
            ),
        )
        notebook = project / "selected.ipynb"
        notebook.write_text(
            '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}\n',
            encoding="utf-8",
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        tm.that(gate.source_manifest(project, context, targets=(".",)), has=notebook)
        with pytest.raises(
            ValueError, match=r"coverage is unavailable for: selected\.ipynb"
        ):
            gate.readonly_namespace_sources(project, context, targets=(".",))

    @staticmethod
    def test_unavailable_manifest_does_not_authorize_adaptation(tmp_path: Path) -> None:
        """A malformed native policy retains its blocking discovery failure."""
        project = u.Tests.mk_project(
            tmp_path,
            "invalid-manifest",
            pyproject=(
                '[project]\nname = "invalid-manifest"\nversion = "0.0.0"\n'
                "[tool.ruff]\nunknown-manifest-setting = true\n"
            ),
        )
        (project / "selected.py").write_text("pass\n", encoding="utf-8")
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        with pytest.raises(ValueError, match="Ruff source manifest is unavailable"):
            FlextInfraRuffLintGate(tmp_path).readonly_namespace_sources(
                project, context, targets=(".",)
            )
