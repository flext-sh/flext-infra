"""Readonly namespace identities do not grant name-wide lint exemptions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config, gates
from tests import c, m, tm, u

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
        occurrence = m.Infra.RuffReadonlyNamespaceOccurrence.model_validate(payload)
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
            m.Infra.RuffReadonlyNamespaceOccurrence.model_validate({
                "path": path,
                "qualname": "ExampleProtocols.Settings.Branch",
                "role": "protocol-instance-readonly-namespace",
                "return-type-owner": "example.Branch",
                "producer-qualname": "example.ExampleSettings.Branch",
            })

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
            m.Infra.RuffReadonlyNamespaceOccurrence.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        ("name", "producer"),
        [("branch", "branch"), ("BRANCH", "BRANCH"), ("Branch", "OtherBranch")],
    )
    def test_producer_member_is_paired(name: str, producer: str) -> None:
        """A declaration cannot authorize an unrelated producer member."""
        with pytest.raises(ValueError, match="paired PascalCase producer member"):
            m.Infra.RuffReadonlyNamespaceOccurrence.model_validate({
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
            m.Infra.RuffReadonlyNamespaceOccurrence.model_validate({
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
        gate = gates.FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        tm.that(
            gate.readonly_namespace_sources(project, context, targets=(".",)),
            eq=tuple(
                sorted(project / name for name in (*relative, c.PYPROJECT_FILENAME))
            ),
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
        gate = gates.FlextInfraRuffLintGate(tmp_path)
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
            gates.FlextInfraRuffLintGate(tmp_path).readonly_namespace_sources(
                project, context, targets=(".",)
            )

    @staticmethod
    def _semantic_project(
        tmp_path: Path,
    ) -> tuple[Path, m.Infra.RuffReadonlyNamespaceOccurrence]:
        project = u.Tests.mk_project(
            tmp_path,
            "semantic-readonly",
            pyproject=(
                '[project]\nname = "semantic-readonly"\nversion = "0.0.0"\n'
                '[tool.ruff.lint]\nselect = ["N"]\n'
                '[tool.ruff.lint.pep8-naming]\nignore-names = ["Branch", "setUp"]\n'
                'extend-ignore-names = ["legacyName"]\n'
                '[tool.pyrefly]\nproject-includes = ["src/**/*.py"]\n'
                'search-path = ["src"]\npython-version = "3.13"\n'
            ),
        )
        package = project / "src" / "sample"
        package.mkdir(parents=True, exist_ok=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "contracts.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol, runtime_checkable\n\n"
            "class Contracts:\n"
            "    @runtime_checkable\n"
            "    class BranchSettings(Protocol):\n"
            "        @property\n"
            "        def encoding(self) -> str: ...\n\n"
            "    class Settings(Protocol):\n"
            "        @property\n"
            "        def Branch(self) -> Contracts.BranchSettings: ...\n",
            encoding="utf-8",
        )
        (package / "settings.py").write_text(
            "from typing import Annotated\n"
            "from pydantic import BaseModel, Field\n\n"
            "class RuntimeSettings(BaseModel):\n"
            "    class BranchSettings(BaseModel):\n"
            "        encoding: Annotated[str, Field(description='Encoding')]"
            " = 'utf-8'\n\n"
            "    Branch: BranchSettings = Field(default_factory=BranchSettings)\n",
            encoding="utf-8",
        )
        occurrence = m.Infra.RuffReadonlyNamespaceOccurrence.model_validate({
            "path": "src/sample/contracts.py",
            "qualname": "Contracts.Settings.Branch",
            "role": "protocol-instance-readonly-namespace",
            "return-type-owner": "sample.contracts.Contracts.BranchSettings",
            "producer-qualname": "sample.settings.RuntimeSettings.Branch",
        })
        return project, occurrence

    @staticmethod
    def test_semantic_getter_authentication_is_a_separate_auditable_probe(
        tmp_path: Path,
    ) -> None:
        """Account exactly one getter; preserve other configured name exceptions."""
        project, occurrence = (
            TestsFlextInfraReadonlyNamespaceContract._semantic_project(tmp_path)
        )
        (project / "src" / "sample" / "legacy.py").write_text(
            "def setUp() -> None: ...\ndef legacyName() -> None: ...\n",
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        gate = gates.FlextInfraRuffLintGate(tmp_path)
        primary_context = context.model_copy(
            update={
                "reports_dir": context.reports_dir / "primary",
            }
        )
        before = gate.check(project, primary_context)
        result = gate.check_readonly_namespaces(project, context, (occurrence,))
        after = gate.check(project, primary_context)
        tm.that(before.raw_output, eq=after.raw_output)
        tm.that(before.result.passed, eq=after.result.passed)
        tm.that(result.result.passed, eq=True)
        tm.that(result.issues, eq=())
        tm.that(result.raw_receipt is not None, eq=True)
        tm.that("readonly-namespace-probe" in str(result.raw_receipt), eq=True)
        tm.that('"N802"' in result.raw_output, eq=True)
        tm.that((context.reports_dir / "lint.raw.log").exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize(
        "mutation",
        [
            "no-property",
            "async",
            "extra-argument",
            "setter",
            "deleter",
            "property-shadow",
            "decorator-alias",
            "false-protocol",
            "return-owner",
            "producer-removed",
            "producer-type",
            "stale-file",
            "other-class",
            "rebinding",
            "masked-baseline",
            "duplicate-registry",
            "producer-no-model",
            "field-shadow",
            "factory-mismatch",
            "protocol-shadow",
            "ambiguous-module",
            "empty-registry",
            "non-protocol-base",
        ],
    )
    def test_semantic_invalid_occurrences_fail_closed(
        tmp_path: Path, mutation: str
    ) -> None:
        """No source-invalid, stale, ambiguous, or masked registry is admitted."""
        project, occurrence = (
            TestsFlextInfraReadonlyNamespaceContract._semantic_project(tmp_path)
        )
        source = project / occurrence.path
        text = source.read_text(encoding="utf-8")
        replacements = {
            "no-property": (
                "        @property\n        def Branch",
                "        def Branch",
            ),
            "async": ("def Branch(self)", "async def Branch(self)"),
            "extra-argument": ("def Branch(self)", "def Branch(self, extra: int)"),
            "property-shadow": (
                "class Contracts:",
                "property = lambda value: value\nclass Contracts:",
            ),
            "decorator-alias": (
                "        @property\n        def Branch",
                "        @alias\n        def Branch",
            ),
            "false-protocol": ("class Settings(Protocol):", "class Settings:"),
            "non-protocol-base": (
                "class Settings(Protocol):",
                "class Settings(object, Protocol):",
            ),
            "protocol-shadow": (
                "class Contracts:",
                "Protocol = object\nclass Contracts:",
            ),
            "return-owner": ("-> Contracts.BranchSettings:", "-> int:"),
            "other-class": (
                "class Settings(Protocol):",
                "class OtherSettings(Protocol):",
            ),
        }
        if mutation in replacements:
            before, after = replacements[mutation]
            text = text.replace(before, after)
        if mutation in {"setter", "deleter"}:
            text += (
                f"        @Branch.{mutation}\n        def Branch(self) -> None: ...\n"
            )
        if mutation == "rebinding":
            text += "\nContracts.Settings.Branch = property(lambda self: None)\n"
        source.write_text(text, encoding="utf-8")
        producer = project / "src" / "sample" / "settings.py"
        producer_replacements = {
            "producer-removed": (
                (
                    "    Branch: BranchSettings = "
                    "Field(default_factory=BranchSettings)\n"
                ),
                "",
            ),
            "producer-type": ("Annotated[str,", "Annotated[int,"),
            "producer-no-model": (
                "RuntimeSettings(BaseModel)",
                "RuntimeSettings(object)",
            ),
            "factory-mismatch": (
                "default_factory=BranchSettings",
                "default_factory=dict",
            ),
            "field-shadow": (
                "class RuntimeSettings",
                "def Field(**kwargs: object) -> None: ...\n\nclass RuntimeSettings",
            ),
        }
        if mutation in producer_replacements:
            before, after = producer_replacements[mutation]
            producer.write_text(
                producer.read_text(encoding="utf-8").replace(before, after),
                encoding="utf-8",
            )
        if mutation == "ambiguous-module":
            source.with_suffix(".pyi").write_text(text, encoding="utf-8")
        if mutation == "stale-file":
            occurrence = m.Infra.RuffReadonlyNamespaceOccurrence.model_validate({
                **occurrence.model_dump(by_alias=True),
                "path": "src/sample/missing.py",
            })
        if mutation == "masked-baseline":
            policy = project / c.PYPROJECT_FILENAME
            policy.write_text(
                policy.read_text(encoding="utf-8").replace(
                    '["Branch", "setUp"]', '["Branch", "setUp", "B*"]'
                ),
                encoding="utf-8",
            )
        occurrences = {
            "duplicate-registry": (occurrence, occurrence),
            "empty-registry": (),
        }.get(mutation, (occurrence,))
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        with pytest.raises((ValueError, TypeError), match=r"(?i)(readonly|registered)"):
            gates.FlextInfraRuffLintGate(tmp_path).check_readonly_namespaces(
                project, context, occurrences
            )

    @staticmethod
    @pytest.mark.parametrize(
        ("filename", "source", "rule"),
        [
            ("other.py", "def Branch() -> None: ...\n", "N802"),
            ("other.py", "async def Branch() -> None: ...\n", "N802"),
            (
                "other.py",
                "class Other:\n    def Branch(self) -> None: ...\n",
                "N802",
            ),
            ("other.pyi", "def Branch() -> None: ...\n", "N802"),
            (
                "other.py",
                "def consume(Branch: int) -> None: ...\n",
                "N803",
            ),
            (
                "other.py",
                "def consume() -> None:\n    Branch = 1\n",
                "N806",
            ),
            (
                "other.py",
                "class Branch(Exception): ...\n",
                "N818",
            ),
            (
                "other.py",
                "def OtherBrokenName() -> None: ...\n",
                "N802",
            ),
        ],
    )
    def test_native_oracle_keeps_every_other_naming_binding_hard(
        tmp_path: Path, filename: str, source: str, rule: str
    ) -> None:
        """Native rule coverage is retained, including stubs and future N rules."""
        project, occurrence = (
            TestsFlextInfraReadonlyNamespaceContract._semantic_project(tmp_path)
        )
        (project / "src" / "sample" / filename).write_text(source, encoding="utf-8")
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        result = gates.FlextInfraRuffLintGate(tmp_path).check_readonly_namespaces(
            project, context, (occurrence,)
        )
        tm.that(result.result.passed, eq=False)
        tm.that(tuple(issue.code for issue in result.issues), has=rule)

    @staticmethod
    def test_real_checker_proves_producer_compatibility_and_readonly_assignment(
        tmp_path: Path,
    ) -> None:
        """A real checker proves structural return typing and prohibits writes."""
        project, _ = TestsFlextInfraReadonlyNamespaceContract._semantic_project(
            tmp_path
        )
        proof = project / "src" / "sample" / "proof.py"
        proof.write_text(
            "from sample.contracts import Contracts\n"
            "from sample.settings import RuntimeSettings\n\n"
            "def compatible(value: RuntimeSettings) -> Contracts.BranchSettings:\n"
            "    return value.Branch\n",
            encoding="utf-8",
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path, reports_dir=tmp_path / "reports"
        )
        checker = gates.FlextInfraPyreflyGate(tmp_path)
        accepted = checker.check_files((proof,), project, context)
        tm.that(accepted.result.passed, eq=True, msg=accepted.raw_output)
        proof.write_text(
            proof.read_text(encoding="utf-8") + "\ndef forbidden(\n"
            "    value: Contracts.Settings, branch: Contracts.BranchSettings\n"
            ") -> None:\n"
            "    value.Branch = branch\n",
            encoding="utf-8",
        )
        rejected = checker.check_files((proof,), project, context)
        tm.that(rejected.result.passed, eq=False)
        tm.that(
            any("read-only" in issue.message.lower() for issue in rejected.issues),
            eq=True,
        )
