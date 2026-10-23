"""Semantic model-role admission preserves native behavioral contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraModelRoleAdmission:
    """Exercise the elected rule with real packages, models and project metadata."""

    @staticmethod
    @pytest.mark.parametrize(
        "project_name",
        [
            "flext-core",
            "flext-cli",
            "flext-ldap",
            "flext-ldif",
            "flext-infra",
            "flext-tests",
            "algar-oud-mig",
        ],
    )
    @pytest.mark.parametrize("surface", ["src", "namespace"])
    def test_model_role_follows_payload_identity_not_base_spelling(
        tmp_path: Path,
        project_name: str,
        surface: str,
    ) -> None:
        """Seven fixture profiles preserve payload diagnostics and writer behavior."""
        declaration = u.Tests.project_spec(f"role-{project_name}")
        namespace = f"{declaration.package_name}_operations"
        declaration = declaration.model_copy(
            update={"repository_namespace_packages": (namespace,)}
        )
        root, primary = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name=declaration.constant_name,
            package_name=declaration.package_name,
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / "codegen.yaml",
                {
                    "Infra": {
                        "codegen": {
                            "repository": {
                                "project": declaration.model_dump(mode="json"),
                            }
                        }
                    }
                },
            )
        )
        package = primary if surface == "src" else root / namespace
        package.mkdir(exist_ok=True)
        source = (
            "from __future__ import annotations\n"
            "from io import StringIO\n"
            "from pydantic import BaseModel as PayloadBase\n"
            "from pydantic_settings import BaseSettings\n"
            "from flext_core import m\n"
            "class NamespacePart:\n    pass\n"
            "class Namespace(NamespacePart):\n    pass\n"
            "class Parent[T](PayloadBase):\n    value: T\n"
            "class Aliased(PayloadBase):\n    value: str\n"
            "class Intermediate(Parent[str]):\n    pass\n"
            "class Generic(Parent[list[str]]):\n    pass\n"
            "class PassiveMixin:\n    pass\n"
            "class Composite(m.StrictManagedModel, PassiveMixin):\n"
            "    value: str = m.Field(description='Payload value')\n"
            "class Settings(BaseSettings):\n    value: str = 'settings'\n"
            "class Service(m.StrictManagedModel):\n"
            "    def execute(self) -> str:\n        return 'executed'\n"
            "class Writer(m.StrictManagedModel):\n"
            "    value: str = m.Field(description='Writer input')\n"
            "    def render(self) -> str:\n        return self.value.upper()\n"
            "    def stream(self, target: StringIO) -> None:\n"
            "        target.write(self.render())\n"
        )
        path = package / "role_cases.py"
        path.write_text(source, encoding="utf-8")
        module_name = f"{package.name}.{path.stem}"
        probe = (
            "from io import StringIO\n"
            "from pydantic import BaseModel, ValidationError\n"
            f"from {module_name} import (Aliased, Composite, Generic, "
            "Intermediate, Namespace, Service, Settings, Writer)\n"
            "writer = Writer.model_validate({'value': 'payload'})\n"
            "assert writer.model_dump() == {'value': 'payload'}\n"
            "assert Writer.model_validate_json(writer.model_dump_json()) == writer\n"
            "assert Writer.model_json_schema()['properties']['value']['type'] == "
            "'string'\n"
            "stream = StringIO()\nwriter.stream(stream)\n"
            "assert stream.getvalue() == writer.render() == 'PAYLOAD'\n"
            "try:\n    Writer.model_validate({'value': []})\n"
            "except ValidationError:\n    pass\n"
            "else:\n    raise AssertionError('Writer validation was weakened')\n"
            "assert Aliased(value='payload').model_dump() == {'value': 'payload'}\n"
            "assert Intermediate(value='payload').value == 'payload'\n"
            "assert Generic(value=['payload']).value == ['payload']\n"
            "assert Composite(value='payload').value == 'payload'\n"
            "assert Service().execute() == 'executed'\n"
            "assert Settings().value == 'settings'\n"
            "assert not issubclass(Namespace, BaseModel)\n"
            "print('native-model-contracts-preserved')\n"
        )
        python_paths = (str(primary.parent), str(root))
        before = u.Tests.run_lazy_init_probe(probe, python_paths=python_paths, cwd=root)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                root,
                fix=False,
                selection=("ban-class-wrong-facade-layer",),
                source_files=(path,),
            )
        )
        tm.that(
            {entry.text.split("(", 1)[0] for entry in report.entries},
            eq={
                "class Parent[T]",
                "class Aliased",
                "class Intermediate",
                "class Generic",
                "class Composite",
            },
        )
        tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(
            u.Tests.run_lazy_init_probe(probe, python_paths=python_paths, cwd=root),
            eq=before,
        )
        tm.that(before, eq=["native-model-contracts-preserved"])

    @staticmethod
    def test_model_family_admission_keeps_other_family_diagnostics(
        declaration_workspace: tuple[Path, Path],
    ) -> None:
        """Model placement does not disable enum or utilities family enforcement."""
        root, package = declaration_workspace
        family = package / "_models"
        family.mkdir()
        (family / "__init__.py").write_text("", encoding="utf-8")
        path = family / "declarations.py"
        source = (
            "from enum import StrEnum\n"
            "from pydantic import BaseModel as PayloadBase\n"
            "class Payload(PayloadBase):\n    value: str\n"
            "class Status(StrEnum):\n    READY = 'ready'\n"
            "class SampleUtilities:\n    pass\n"
        )
        path.write_text(source, encoding="utf-8")
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                root,
                fix=False,
                selection=("ban-class-wrong-facade-layer",),
                source_files=(path,),
            )
        )
        tm.that(
            {entry.text.split("(", 1)[0].split(":", 1)[0] for entry in report.entries},
            eq={"class Status", "class SampleUtilities"},
        )
        tm.that(path.read_text(encoding="utf-8"), eq=source)
