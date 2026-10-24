"""Import-law engine: tier letters, layer-zero, and family facade contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import m
from flext_infra.refactor import FlextInfraImportNormalization
from tests import c, tm, u
from tests.unit.refactor.import_normalization_support import (
    TestsFlextInfraRefactorImportNormalizationSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalizationFamilies(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Family, tier, and layer-zero rules observed through ``normalize_source``."""

    @classmethod
    def test_family_keeps_upstream_own_letter(cls, tmp_path: Path) -> None:
        """A family package keeps its own letter from the upstream namespace."""
        project, package = cls._project(tmp_path)
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "_models" / "record.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "from flext_cli import m\n"
                "\n"
                "\n"
                "class DemoRecord(m.ContractModel):\n"
                "    name: str\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    @pytest.mark.parametrize("local_alias", ["tm", "u", "payload_models"])
    @pytest.mark.parametrize("imported_name", ["m", "FlextTestsModels"])
    def test_renamed_model_letter_preserves_public_payload_identity(
        cls,
        tmp_path: Path,
        local_alias: str,
        imported_name: str,
    ) -> None:
        """An imported model alias never becomes the root's unrelated receiver."""
        project, package = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(
            tier,
            {"m": ".models", "tm": "flext_tests", "u": "flext_tests"},
        )
        (tier / "models.py").write_text(
            "from flext_tests import FlextTestsModels\n\n"
            "class TestsLocalModels(FlextTestsModels):\n"
            "    class Tests(FlextTestsModels.Tests):\n"
            "        class User(FlextTestsModels.Tests.User):\n"
            "            local: bool = FlextTestsModels.Field("
            "default=True, description='Local consumer field')\n\n"
            "m = TestsLocalModels\n__all__ = ['TestsLocalModels', 'm']\n",
            encoding="utf-8",
        )
        module = tier / "consumer.py"
        source = (
            "from __future__ import annotations\n"
            "from tests import c, m\n"
            f"from flext_tests import {imported_name} as {local_alias}\n\n"
            "local_models = m\n"
            "class ClassScope:\n    m = 'class-local'\n\n"
            "def local(m: str = 'default-local') -> str:\n    return m\n\n"
            f"def sibling({local_alias}: str) -> str:\n"
            f"    return {local_alias}\n\n"
            f"def build(value: '{local_alias}.Tests.User') "
            f"-> '{local_alias}.Tests.User':\n"
            f"    return {local_alias}.Tests.User.model_validate(value.model_dump())\n"
        )
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source,
            encoding="utf-8",
        )
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from typing import get_type_hints; "
                        "from flext_tests import m, tm; "
                        "from tests import c, m as local_m; "
                        "from tests.consumer import "
                        "ClassScope, build, local, local_models, sibling; "
                        "user = m.Tests.User.model_validate("
                        "{'id': 'user-1', 'name': 'Native User', "
                        "'email': 'native@example.test'}); "
                        "assert type(build(user)) is m.Tests.User; "
                        "assert build(user).model_dump() == user.model_dump(); "
                        "assert get_type_hints(build)['value'] is m.Tests.User; "
                        "assert get_type_hints(build)['return'] is m.Tests.User; "
                        "assert local_models is local_m and local_m is not m; "
                        "assert local_models.Tests.User is not m.Tests.User; "
                        "local_user = local_models.Tests.User.model_validate("
                        "user.model_dump()); "
                        "assert type(local_user) is local_models.Tests.User; "
                        "assert tm is not m; "
                        "assert ClassScope.m == 'class-local'; "
                        "assert local() == 'default-local'; "
                        "assert sibling('sibling-local') == 'sibling-local'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": f"{project}:{package.parent}"},
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(result.outcome))

    @classmethod
    def test_leaf_object_routes_through_lazy_package(cls, tmp_path: Path) -> None:
        """A leaf-module object binds through the package that publishes it."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg._models.record import DemoRecord\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    return DemoRecord\n",
        )

        tm.that(normalized, has="from demo_pkg._models import DemoRecord\n")
        tm.that(normalized, lacks="demo_pkg._models.record")

    @classmethod
    @pytest.mark.parametrize("reexport", [True, False])
    def test_published_package_binding_preserves_provider_identity(
        cls,
        tmp_path: Path,
        *,
        reexport: bool,
    ) -> None:
        """Reexports share identity; independent declarations remain conflicts."""
        project, package = cls._project(tmp_path)
        family = package / "_models"
        cls._lazy_init(family / "parts", {"DemoRecord": ".record"})
        (family / "parts" / "record.py").write_text(
            "class DemoRecord:\n    pass\n\n__all__ = ['DemoRecord']\n",
            encoding="utf-8",
        )
        (family / "record.py").write_text(
            (
                "from demo_pkg._models.parts.record import DemoRecord\n"
                if reexport
                else "class DemoRecord:\n    pass\n"
            )
            + "\n__all__ = ['DemoRecord']\n",
            encoding="utf-8",
        )
        source = "from demo_pkg._models import DemoRecord\n\nvalue = DemoRecord\n"
        if not reexport:
            with pytest.raises(ValueError, match="Ambiguous declared public import"):
                FlextInfraImportNormalization.normalize_source(
                    project_root=project,
                    file_path=package / "consumer.py",
                    source=source,
                )
            return
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "consumer.py",
            source=source,
        )
        tm.that(normalized, eq=None)

        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg._models import DemoRecord; "
                        "from demo_pkg._models.record import DemoRecord as provider; "
                        "assert DemoRecord is provider"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.ok(u.Cli.process_succeeded(result.outcome))

    @classmethod
    @pytest.mark.parametrize("base_binding", ["module", "direct", "alias", "generic"])
    def test_exception_factory_mro_reexports_have_one_terminal_owner(
        cls,
        tmp_path: Path,
        *,
        base_binding: str,
    ) -> None:
        """An explicit MRO chain and its reexport route to one canonical class."""
        project, package = cls._project(tmp_path)
        family = package / "exceptions"
        parts = family / "parts"
        cls._lazy_init(family, {"FlextExceptionsFactories": ".factories"})
        cls._lazy_init(parts, {"FlextExceptionsFactories": ".second"})
        (parts / "first.py").write_text(
            (
                "class FlextExceptionsFactories[T]:\n"
                if base_binding == "generic"
                else "class FlextExceptionsFactories:\n"
            )
            + "    pass\n\n__all__ = ['FlextExceptionsFactories']\n",
            encoding="utf-8",
        )
        (parts / "second.py").write_text(
            (
                "from demo_pkg.exceptions.parts.first import "
                "FlextExceptionsFactories as Previous\n\n"
                "class FlextExceptionsFactories(Previous):\n"
                if base_binding == "direct"
                else "from demo_pkg.exceptions.parts import first\n\n"
                "previous = first\n\n"
                "class FlextExceptionsFactories(previous.FlextExceptionsFactories):\n"
                if base_binding == "alias"
                else "from demo_pkg.exceptions.parts import first\n\n"
                "class FlextExceptionsFactories[T]("
                "first.FlextExceptionsFactories[T]):\n"
                if base_binding == "generic"
                else "from demo_pkg.exceptions.parts import first\n\n"
                "class FlextExceptionsFactories(first.FlextExceptionsFactories):\n"
            )
            + "    pass\n\n__all__ = ['FlextExceptionsFactories']\n",
            encoding="utf-8",
        )
        (family / "factories.py").write_text(
            "from demo_pkg.exceptions.parts import FlextExceptionsFactories\n\n"
            "__all__ = ['FlextExceptionsFactories']\n",
            encoding="utf-8",
        )
        source = (
            "from demo_pkg.exceptions import FlextExceptionsFactories\n\n"
            "value = FlextExceptionsFactories\n"
        )
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=package / "consumer.py",
                source=source,
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize("same_package", [False, True])
    def test_unpublished_name_rejects_competing_descendant_declarations(
        cls,
        tmp_path: Path,
        *,
        same_package: bool,
    ) -> None:
        """Without a package binding, independent public declarations stay ambiguous."""
        project, package = cls._project(tmp_path)
        for child in ("first", "second"):
            directory = (
                package / "services" if same_package else package / "services" / child
            )
            filename = child if same_package else "record"
            cls._lazy_init(directory, {"DemoRecord": f".{filename}"})
            (directory / f"{filename}.py").write_text(
                "class DemoRecord:\n    pass\n\n__all__ = ['DemoRecord']\n",
                encoding="utf-8",
            )
        source = "from demo_pkg.services import DemoRecord\n\nvalue = DemoRecord\n"
        with pytest.raises(ValueError, match="Ambiguous declared public import"):
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=package / "consumer.py",
                source=source,
            )

    @classmethod
    def test_tier_long_letter_forms_collapse_to_tier_root(
        cls,
        tmp_path: Path,
    ) -> None:
        """The operator's flext-auth shape: tier letters and helpers bind lazily."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(
            tier,
            {"c": ".constants", "m": ".models", "u": ".utilities"},
        )
        for letter, name in (("c", "TestsDemoConstants"), ("u", "TestsDemoUtilities")):
            family = u.Infra.facade_families()[letter]
            (tier / f"{family.module}.py").write_text(
                f"class {name}:\n    pass\n{letter} = {name}\n"
                f"__all__ = ['{name}', '{letter}']\n",
                encoding="utf-8",
            )
        (tier / "models.py").write_text(
            "from demo_pkg import m\n__all__ = ['m']\n", encoding="utf-8"
        )
        cls._lazy_init(
            tier / "unit" / "api_cases",
            {"DemoApiTestDataHelper": ".support"},
        )
        normalized = cls._normalize(
            project,
            tier / "unit" / "test_api.py",
            "from __future__ import annotations\n"
            "\n"
            "from tests.constants import TestsDemoConstants as c\n"
            "from tests.unit.api_cases.support import DemoApiTestDataHelper\n"
            "from tests.utilities import TestsDemoUtilities as u\n"
            "from demo_pkg import DemoApi, m\n"
            "\n"
            "\n"
            "def test_api() -> None:\n"
            "    assert DemoApi(c, m, u, DemoApiTestDataHelper)\n",
        )

        tm.that(normalized, has="from tests import c\n")
        tm.that(normalized, has="from tests import c, u\n")
        tm.that(normalized, has="from tests import c, m\n")
        tm.that(normalized, has="from demo_pkg import DemoApi\n")
        tm.that(
            normalized,
            has="from tests.unit.api_cases import DemoApiTestDataHelper\n",
        )
        tm.that(normalized, lacks="TestsDemoConstants")
        tm.that(normalized, lacks="TestsDemoUtilities")

    @classmethod
    @pytest.mark.parametrize("namespace", ["primary_pkg", "secondary_pkg"])
    @pytest.mark.parametrize(
        "relative",
        [
            "consumer.py",
            "_models/record.py",
            "_constants/value.py",
            "constants.py",
            "domain_records.py",
        ],
    )
    @pytest.mark.parametrize("guarded", [False, True])
    def test_native_facade_role_and_identity_are_project_independent(
        cls, tmp_path: Path, namespace: str, relative: str, *, guarded: bool
    ) -> None:
        """Only consumers converge on an identical public alias; producers do not."""
        project = tmp_path / namespace
        package = u.Tests.src_package(
            project,
            namespace,
            pyproject=f"[project]\nname='{namespace}'\nversion='1.0.0'\n",
        )
        parent = package.parent / "ancestor_pkg"
        cls._lazy_init(parent, {"c": ".constants", "r": ".result"})
        (parent / "constants.py").write_text(
            "class AncestorConstants:\n    marker = 'native'\n\n"
            "c = AncestorConstants\n__all__ = ['c']\n",
            encoding="utf-8",
        )
        (parent / "result.py").write_text(
            "class Result:\n    pass\n\nr = Result\n__all__ = ['r']\n",
            encoding="utf-8",
        )
        producer = relative in {
            "_constants/value.py",
            "constants.py",
            "domain_records.py",
        }
        provider = (
            relative[:-3].replace("/", ".")
            if producer and relative != "domain_records.py"
            else "facade"
        )
        cls._lazy_init(package, {"c": f".{provider}", "r": "ancestor_pkg"})
        if not producer:
            (package / "facade.py").write_text(
                "from ancestor_pkg import c\n__all__ = ['c']\n", encoding="utf-8"
            )
        if relative == "domain_records.py":
            (package / "facade.py").write_text(
                f"from {namespace}.domain_records import DomainConstants\n"
                "class PublicConstants(DomainConstants):\n    pass\n"
                "c = PublicConstants\n__all__ = ['c']\n",
                encoding="utf-8",
            )
        module = package / relative
        if module.parent != package:
            cls._lazy_init(module.parent, {})
        statement = (
            f"from {namespace} import c\nfrom ancestor_pkg import c, r\n"
            if producer and relative != "domain_records.py"
            else "from ancestor_pkg import c, r\n"
        )
        source = (
            "from __future__ import annotations\nfrom typing import TYPE_CHECKING\n"
            + (
                "if TYPE_CHECKING:\n"
                + "".join(f"    {line}\n" for line in statement.splitlines())
                if guarded
                else statement
            )
            + (
                "\nclass DomainConstants(c):\n    pass\n__all__ = ['DomainConstants']\n"
                if relative == "domain_records.py"
                else "\nclass LocalConstants(c):\n    pass\nc = LocalConstants\n"
                "__all__ = ['c']\n"
                if producer
                else "\ndef read() -> c:\n    return r\n"
            )
        )
        module.write_text(source, encoding="utf-8")
        normalized = (
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=source
            )
            or source
        )
        module.write_text(normalized, encoding="utf-8")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=normalized
            ),
            eq=None,
        )
        imports = [
            node.module
            for node in ast.walk(ast.parse(normalized))
            if isinstance(node, ast.ImportFrom)
            and any(alias.name == "c" for alias in node.names)
        ]
        tm.that(imports, eq=["ancestor_pkg" if producer else namespace])
        if guarded:
            normalized = normalized.replace("if TYPE_CHECKING:", "if True:")
            module.write_text(normalized, encoding="utf-8")
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {namespace}.{relative[:-3].replace('/', '.')} "
                        "import c, r; "
                        "from ancestor_pkg import c as original_c, r as original_r; "
                        + (
                            "assert c.__bases__[0] is original_c; "
                            if producer and relative != "domain_records.py"
                            else "assert c is original_c; "
                        )
                        + "assert r is original_r"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(outcome.exit_code, eq=0)
        tm.that(outcome.stderr, eq="")

    @classmethod
    @pytest.mark.parametrize("namespace", ["checks", "verification"])
    @pytest.mark.parametrize("distinct", [False, True])
    @pytest.mark.parametrize("guarded", [False, True])
    def test_native_alias_collision_requires_identity_before_effects(
        cls, tmp_path: Path, namespace: str, *, distinct: bool, guarded: bool
    ) -> None:
        """Inherited operational aliases deduplicate; independent classes reject."""
        project = tmp_path / namespace
        application = u.Tests.src_package(
            project,
            "application_pkg",
            pyproject=f"[project]\nname='{namespace}'\nversion='1.0.0'\n",
        )
        package = project / namespace
        parent = application.parent / "ancestor_pkg"
        cls._lazy_init(parent, {"r": ".result"})
        (parent / "result.py").write_text(
            "class Result:\n    pass\n\nr = Result\n__all__ = ['r']\n", encoding="utf-8"
        )
        cls._lazy_init(package, {"r": ".result" if distinct else "ancestor_pkg"})
        if distinct:
            (package / "result.py").write_text(
                "from ancestor_pkg import r\nclass LocalResult(r):\n    pass\n"
                "r = LocalResult\n__all__ = ['r']\n",
                encoding="utf-8",
            )
        module = package / "consumer.py"
        source = (
            "from typing import TYPE_CHECKING\n"
            f"from {namespace} import r\n"
            + (
                "if TYPE_CHECKING:\n    from ancestor_pkg import r\n"
                if guarded
                else "from ancestor_pkg import r\n"
            )
            + "value = r\n"
        )
        module.write_text(source, encoding="utf-8")
        if distinct:
            with pytest.raises(ValueError, match="ambiguous facade binding"):
                FlextInfraImportNormalization.normalize_source(
                    project_root=project, file_path=module, source=source
                )
            tm.that(module.read_text(encoding="utf-8"), eq=source)
            return
        normalized = cls._normalize(project, module, source)
        module.write_text(normalized, encoding="utf-8")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=normalized
            ),
            eq=None,
        )
        tm.that(
            sum(
                alias.name == "r"
                for node in ast.walk(ast.parse(normalized))
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            ),
            eq=1,
        )
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {namespace}.consumer import r, value; "
                        "from ancestor_pkg import r as native; "
                        "assert r is native; assert value is native"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": f"{project}:{application.parent}"}
                ),
            )
        )
        tm.that(outcome.exit_code, eq=0)
        tm.that(outcome.stderr, eq="")

    @classmethod
    def test_settings_config_modules_keep_upstream_contracts(
        cls,
        tmp_path: Path,
    ) -> None:
        """Layer-zero modules retain native/upstream contracts, not own imports."""
        project, package = cls._project(tmp_path)
        source = (
            "from __future__ import annotations\n"
            "from typing import ClassVar\n"
            "from pydantic import JsonValue\n"
            "from flext_core import FlextConfig\n"
            "class DemoConfig(FlextConfig):\n"
            "    CONFIG_FILENAMES: ClassVar[tuple[str, ...]] = ()\n"
            "    value: JsonValue = 'native'\n"
        )
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "_config.py",
            source=source,
        )
        normalized = result if result is not None else source
        tm.that(normalized, has="from flext_core import FlextConfig")
        tm.that(normalized, has="from pydantic import JsonValue")
        tm.that(normalized, lacks="from demo_pkg import")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=package / "_config.py",
                source=normalized,
            ),
            eq=None,
        )
        (package / "_config.py").write_text(normalized, encoding="utf-8")
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg._config import DemoConfig; "
                        "value = DemoConfig(value={'native': [1, 'contract']}); "
                        "assert value.model_dump()['value'] == "
                        "{'native': [1, 'contract']}"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(outcome.exit_code, eq=0)
        tm.that(outcome.stderr, eq="")

    @classmethod
    @pytest.mark.parametrize("role", sorted(c.Infra.IMPORT_LAW_ROOT_SINGLETONS))
    @pytest.mark.parametrize(
        "statement",
        [
            "from demo_pkg import t",
            "from demo_pkg import settings",
            "from demo_pkg import settings as own",
            "from demo_pkg._models.base import DemoModelsBase",
            "from demo_pkg._settings import DemoSettings",
            "from ._settings import DemoSettings",
            "import demo_pkg as own",
        ],
    )
    @pytest.mark.parametrize("guarded", [False, True])
    def test_layer_zero_rejects_all_own_namespace_dependencies(
        cls, tmp_path: Path, role: str, statement: str, *, guarded: bool
    ) -> None:
        """Typing guards and private paths cannot authorize a layer-zero edge."""
        project, package = cls._project(tmp_path)
        source = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING\n"
            + (f"if TYPE_CHECKING:\n    {statement}\n" if guarded else statement + "\n")
        )
        with pytest.raises(ValueError, match="layer-zero module imports its own"):
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=package / f"_{role}.py",
                source=source,
            )

    @classmethod
    @pytest.mark.parametrize("role", sorted(c.Infra.IMPORT_LAW_ROOT_SINGLETONS))
    def test_layer_zero_role_uses_architecture_not_substring(cls, role: str) -> None:
        """A domain configuration name cannot override its enclosing family."""
        tm.that(u.Infra.import_module_role(f"demo_pkg._{role}"), eq="layer0")
        tm.that(u.Infra.import_module_role(f"demo_pkg.{role}_sources"), eq="layer0")
        tm.that(u.Infra.import_module_role(f"demo_pkg.{role}uration"), eq="consumer")
        tm.that(u.Infra.import_module_role(f"demo_pkg.helpers.{role}"), eq="consumer")
        tm.that(u.Infra.import_module_role(f"infra.pulumi.lib.{role}"), eq="consumer")
        for family in u.Infra.facade_families().values():
            tm.that(
                u.Infra.import_module_role(f"demo_pkg.{family.directory}._{role}.base"),
                eq="family",
            )

    @classmethod
    @pytest.mark.parametrize("letter", sorted(u.Infra.facade_families()))
    @pytest.mark.parametrize("guarded", [False, True])
    def test_family_rejects_own_facade_but_preserves_private_assembly(
        cls, tmp_path: Path, letter: str, *, guarded: bool
    ) -> None:
        """Every family retains private MRO sources and rejects its own facade."""
        project, package = cls._project(tmp_path)
        family = u.Infra.facade_families()[letter]
        directory = package / family.directory
        directory.mkdir(exist_ok=True)
        module = directory / "declaration.py"
        source = "from typing import TYPE_CHECKING\n" + (
            f"if TYPE_CHECKING:\n    from demo_pkg import {letter} as own\n"
            if guarded
            else f"from demo_pkg import {letter} as own\n"
        )
        with pytest.raises(ValueError, match="family imports its own facade"):
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=source
            )
        native = f"from demo_pkg.{family.directory}.part import Declaration\n"
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=directory / "base.py", source=native
            ),
            eq=None,
        )
