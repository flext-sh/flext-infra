"""Behavior of the FLEXT import-law engine on real package trees.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import m
from flext_infra.refactor import FlextInfraImportNormalization
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalization:
    """Each import-law rule observed through ``normalize_source``."""

    @classmethod
    def test_distinct_inline_providers_fail_before_consumer_publication(
        cls,
        tmp_path: Path,
    ) -> None:
        """Refuse a global binding that would change two real local consumers."""
        project, package = cls._project(tmp_path)
        for provider, value in (
            ("first_provider", "first provider"),
            ("second_provider", "second provider"),
        ):
            (package.parent / f"{provider}.py").write_text(
                f"def value() -> str:\n    return {value!r}\n",
                encoding="utf-8",
            )
        consumer = package / "consumer.py"
        consumer.write_text(
            "def first() -> str:\n"
            "    from first_provider import value\n"
            "    return value()\n\n"
            "def second() -> str:\n"
            "    from second_provider import value\n"
            "    return value()\n",
            encoding="utf-8",
        )
        command = (
            sys.executable,
            "-c",
            "from demo_pkg.consumer import first, second; print(first(), second())",
        )
        options = m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)})
        before = tm.ok(u.Cli.run(command, cwd=project, options=options))
        tm.that(u.Cli.process_succeeded(before.outcome), eq=True, msg=before.stderr)
        tm.that(before.stdout.strip(), eq="first provider second provider")
        with pytest.raises(ValueError, match="conflicting inline import providers"):
            FlextInfraImportNormalization.apply_files(project, (consumer,))
        after = tm.ok(u.Cli.run(command, cwd=project, options=options))
        tm.that(u.Cli.process_succeeded(after.outcome), eq=True, msg=after.stderr)
        tm.that(after.stdout, eq=before.stdout)

    @classmethod
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (
                "def read_failure() -> str:\n"
                "    try:\n"
                "        raise ValueError('handler failure')\n"
                "    except ValueError as e:\n"
                "        return str(e)\n"
                "\n"
                "print(read_failure())\n",
                "handler failure",
            ),
            (
                "match 'pattern value':\n    case str() as s:\n        print(s)\n",
                "pattern value",
            ),
            (
                "match ['pattern value']:\n    case [*s]:\n        print(s[0])\n",
                "pattern value",
            ),
            (
                "match {'value': 'pattern value'}:\n"
                "    case {**s}:\n"
                "        print(s['value'])\n",
                "pattern value",
            ),
        ],
    )
    def test_local_bindings_do_not_load_a_facade_provider(
        cls,
        tmp_path: Path,
        source: str,
        expected: str,
    ) -> None:
        """Exception and pattern bindings execute without a facade dependency."""
        project, package = cls._project(tmp_path)
        cls._lazy_init(
            package,
            {"e": ".unavailable_provider", "s": ".unavailable_provider"},
        )
        module = package / "handler.py"
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source,
            encoding="utf-8",
        )
        result = tm.ok(
            u.Cli.run(
                (sys.executable, str(module)),
                cwd=project,
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)
        tm.that(result.stdout.strip(), eq=expected)
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )

    @classmethod
    def test_eager_root_dependencies_preserve_bootstrap_imports(
        cls,
        tmp_path: Path,
    ) -> None:
        """A loader's dependency stays direct before the root publishes exports."""
        project, package = cls._project(tmp_path)
        initializer = package / "__init__.py"
        initializer.write_text(
            "from demo_pkg.loader import install\n"
            + initializer.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (package / "loader.py").write_text(
            "from demo_pkg.bootstrap import Bootstrap\n\ninstall = Bootstrap\n",
            encoding="utf-8",
        )
        source = "from demo_pkg._models.record import DemoRecord\n\n"
        source += "class Bootstrap(DemoRecord):\n    pass\n"
        target = package / "bootstrap.py"
        target.write_text(source, encoding="utf-8")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=target,
                source=source,
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize("destination", ["missing", "stale"])
    def test_declared_destination_precedes_initializer_projection(
        cls,
        tmp_path: Path,
        destination: str,
    ) -> None:
        """Normalize, generate and consume the same declaration without an old ABI."""
        project, package = u.Tests.create_lazy_init_workspace(tmp_path)
        cls._lazy_init(package, {"FlextTestProjectService": ".services.runner"})
        services = package / "services"
        services.mkdir()
        if destination == "stale":
            cls._lazy_init(services, {"OtherService": ".other"})
        declaration = services / "runner.py"
        declaration.write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestProjectService:\n    pass\n\n"
            "__all__ = ['FlextTestProjectService']\n",
            encoding="utf-8",
        )
        module = package / "consumer.py"
        normalized = cls._normalize(
            project,
            module,
            f"from {package.name} import FlextTestProjectService\n\n"
            "instance = FlextTestProjectService()\n",
        )
        module.write_text(normalized, encoding="utf-8")
        tm.ok(
            FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=project,
                projection_roots=(project,),
            ),
        )
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.consumer import instance; "
                        f"from {package.name}.services import FlextTestProjectService; "
                        f"from {package.name}.services.runner import "
                        "FlextTestProjectService as provider; "
                        "assert type(instance) is FlextTestProjectService is provider"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @classmethod
    def test_generic_bound_retains_its_declared_provider(
        cls,
        tmp_path: Path,
    ) -> None:
        """A generic bound resolves through its original public type provider."""
        project, package = cls._project(tmp_path)
        module = package / "generic_boundary.py"
        source = (
            "from flext_core import t\n\nclass Generic[T: t.JsonPayload]:\n    pass\n"
        )
        (package / "typings.py").write_text(
            "class LocalTypes:\n    type JsonPayload = str\n\nt = LocalTypes\n",
            encoding="utf-8",
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
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_core import t; "
                        "from demo_pkg.generic_boundary import Generic; "
                        "assert Generic.__type_params__[0].__bound__ is t.JsonPayload"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @classmethod
    def test_facade_dependency_retains_its_external_provider(
        cls,
        tmp_path: Path,
    ) -> None:
        """The facade still loads a provider imported by one of its MRO parts."""
        project, package = cls._project(tmp_path)
        module = package / "provider_boundary.py"
        source = (
            "from flext_cli import u\n\n"
            "class Provider:\n"
            "    ADAPTER = u.type_adapter(str)\n"
        )
        module.write_text(source, encoding="utf-8")
        (package / "utilities.py").write_text(
            "from demo_pkg.provider_boundary import Provider\n\n"
            "class DemoUtilities(Provider):\n"
            "    pass\n\n"
            "u = DemoUtilities\n"
            "__all__ = ['u']\n",
            encoding="utf-8",
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
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg import u\nassert u.ADAPTER.validate_python('x') "
                        "== "
                        "'x'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @classmethod
    @pytest.mark.parametrize(
        "directory",
        tuple(family.directory for family in u.Infra.facade_families().values()),
    )
    def test_family_retains_external_model_and_utility_providers(
        cls,
        tmp_path: Path,
        directory: str,
    ) -> None:
        """The rewritten family still imports and validates with its real provider."""
        project, package = cls._project(tmp_path)
        family = package / directory
        family.mkdir(exist_ok=True)
        (family / "__init__.py").touch(exist_ok=True)
        module = family / "provider_boundary.py"
        source = (
            "from flext_cli import m, u\n\n"
            "ADAPTER: m.TypeAdapter[str] = u.type_adapter(str)\n"
        )
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source, encoding="utf-8"
        )
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from demo_pkg.{directory}.provider_boundary import ADAPTER; "
                        "assert ADAPTER.validate_python('native-value') == "
                        "'native-value'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    def _lazy_init(package_dir: Path, exports: t.StrMapping) -> None:
        """Write one generated-shape lazy ``__init__`` publishing ``exports``."""
        package_dir.mkdir(parents=True, exist_ok=True)
        entries = "".join(
            f"    {name!r}: {module!r},\n" for name, module in exports.items()
        )
        (package_dir / "__init__.py").write_text(
            "from flext_core.lazy import install_lazy_exports\n"
            "\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    {\n"
            f"{entries}"
            "    },\n"
            ")\n",
            encoding="utf-8",
        )

    @classmethod
    def _project(cls, tmp_path: Path) -> tuple[Path, Path]:
        """Materialize ``demo_pkg`` with a lazy root and lazy family inits.

        Returns:
            The project root and the package directory.

        """
        project = tmp_path / "project"
        package: Path = u.Tests.src_package(
            project,
            "demo_pkg",
            pyproject="[project]\nname='demo'\nversion='1.0.0'\n",
        )
        cls._lazy_init(
            package,
            {
                "c": ".constants",
                "t": ".typings",
                "m": ".models",
                "u": ".utilities",
                "r": "flext_core",
                "DemoApi": ".api",
            },
        )
        cls._lazy_init(package / "_utilities", {"DemoHelper": ".helper"})
        cls._lazy_init(package / "_models", {"DemoRecord": ".record"})
        cls._lazy_init(package / "services", {"DemoRunner": ".runner"})
        return project, package

    @staticmethod
    def _normalize(project: Path, file_path: Path, source: str) -> str:
        """Normalize one module and require a rewrite.

        Returns:
            The rewritten source.

        """
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=file_path,
            source=source,
        )
        tm.that(normalized is not None, eq=True)
        return normalized or ""

    @classmethod
    @pytest.mark.parametrize("stale_root_export", [False, True])
    def test_root_import_selects_declared_subpackage_owner(
        cls,
        tmp_path: Path,
        *,
        stale_root_export: bool,
    ) -> None:
        """A retired root export resolves to its declared public service owner."""
        project, package = cls._project(tmp_path)
        if stale_root_export:
            cls._lazy_init(package, {"DemoRunner": ".services.runner"})
        (package / "services" / "runner.py").write_text(
            "class DemoRunner:\n    pass\n\n__all__ = ['DemoRunner']\n",
            encoding="utf-8",
        )
        module = package / "consumer.py"
        normalized = cls._normalize(
            project,
            module,
            "from demo_pkg import DemoRunner\n\ninstance = DemoRunner()\n",
        )
        module.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg.consumer import instance; "
                        "from demo_pkg.services import DemoRunner; "
                        "assert type(instance) is DemoRunner"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @classmethod
    def test_forward_inline_import_is_hoisted(cls, tmp_path: Path) -> None:
        """A function-body import of a lower layer moves to the module block."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "import json\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    from demo_pkg._utilities import DemoHelper\n"
            "\n"
            "    return json.dumps(DemoHelper())\n",
        )

        tm.that(
            normalized, has="import json\nfrom demo_pkg._utilities import DemoHelper\n"
        )
        tm.that(normalized, lacks="    from demo_pkg._utilities import DemoHelper")

    @classmethod
    def test_reverse_runtime_import_keeps_its_place(cls, tmp_path: Path) -> None:
        """A lower layer reading a higher layer at runtime keeps the import inline."""
        project, package = cls._project(tmp_path)
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=package / "_utilities" / "bridge.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "\n"
                "def run() -> object:\n"
                "    from demo_pkg import DemoApi\n"
                "\n"
                "    return DemoApi()\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    def test_reverse_typing_import_moves_under_type_checking(
        cls,
        tmp_path: Path,
    ) -> None:
        """A reverse import read only in annotations moves under TYPE_CHECKING."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "_models" / "report.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg.services import DemoRunner\n"
            "\n"
            "\n"
            "def describe(runner: DemoRunner) -> str:\n"
            "    return 'runner'\n",
        )

        tm.that(normalized, has="from typing import TYPE_CHECKING\n")
        tm.that(
            normalized,
            has="if TYPE_CHECKING:\n    from demo_pkg.services import DemoRunner\n",
        )

    @classmethod
    def test_foreign_root_alias_binds_through_own_root(cls, tmp_path: Path) -> None:
        """A root alias imported from another namespace binds through its own root."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "from flext_core import r\n"
            "from demo_pkg.typings import t\n"
            "\n"
            "\n"
            "def run(value: t.StrSequence) -> object:\n"
            "    return r.ok(value)\n",
        )

        tm.that(normalized, has="from demo_pkg import r\n")
        tm.that(normalized, has="from demo_pkg import t\n")
        tm.that(normalized, lacks="from flext_core import r")

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
            "class LocalModels(FlextTestsModels):\n"
            "    class Tests(FlextTestsModels.Tests):\n"
            "        class User(FlextTestsModels.Tests.User):\n"
            "            local: bool = True\n\n"
            "m = LocalModels\n__all__ = ['LocalModels', 'm']\n",
            encoding="utf-8",
        )
        module = tier / "consumer.py"
        source = (
            "from __future__ import annotations\n"
            "from tests import m\n"
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
        tm.that(normalized, eq=None)
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from typing import get_type_hints; "
                        "from flext_tests import m, tm; "
                        "from tests import m as local_m; "
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
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

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
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

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
        tm.that(normalized, has="from tests import u\n")
        tm.that(normalized, has="from tests import m\n")
        tm.that(normalized, has="from demo_pkg import DemoApi\n")
        tm.that(
            normalized,
            has="from tests.unit.api_cases import DemoApiTestDataHelper\n",
        )
        tm.that(normalized, lacks="TestsDemoConstants")
        tm.that(normalized, lacks="TestsDemoUtilities")

    @classmethod
    @pytest.mark.parametrize(
        "module_name",
        ("_config", "_settings", "_models/provider"),
    )
    def test_declarations_keep_external_providers(
        cls,
        tmp_path: Path,
        module_name: str,
    ) -> None:
        """Authored declarations instantiate through their real external provider."""
        project, package = cls._project(tmp_path)
        module = package / f"{module_name}.py"
        source = (
            "from flext_core import m\n\n"
            "class DemoConfig(m.BaseModel):\n"
            "    value: str\n\n"
            "print(DemoConfig(value='validated-value').value)\n"
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
        outcome = tm.ok(
            u.Cli.run(
                (sys.executable, str(module)),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True)
        tm.that(outcome.stdout.strip(), eq="validated-value")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize(
        "consumer",
        (
            "def consume():\n    return s()\n",
            "def consume(s=s()):\n    return s\n",
            "@(lambda value: lambda function: function)(s())\n"
            "def consume():\n    return s()\n",
            "VALUES = [s for s in [s()]]\ndef consume():\n    return VALUES[0]\n",
            "def consume():\n    return [s for s in [s()]][0]\n",
        ),
    )
    @pytest.mark.parametrize(
        "local_body",
        (
            "    try:\n"
            "        raise ValueError('local-value')\n"
            "    except ValueError as s:\n"
            "        return str(s)\n",
            "    match 'local-value':\n        case s:\n            return s\n",
        ),
    )
    def test_local_binding_does_not_hide_another_scope_provider(
        cls,
        tmp_path: Path,
        local_body: str,
        consumer: str,
    ) -> None:
        """A local capture and a separate global lazy provider both execute."""
        project, package = cls._project(tmp_path)
        cls._lazy_init(package, {"s": ".provider"})
        (package / "provider.py").write_text(
            "def s():\n    return 'provider-value'\n\n__all__ = ['s']\n",
            encoding="utf-8",
        )
        module = package / "consumer.py"
        source = (
            f"def capture():\n{local_body}\n"
            f"{consumer}\n"
            "print(capture())\nprint(consume())\n"
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
        outcome = tm.ok(
            u.Cli.run(
                (sys.executable, str(module)),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True)
        tm.that(outcome.stdout.splitlines(), eq=["local-value", "provider-value"])
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )

    @classmethod
    def test_internal_tier_alias_binds_through_tier_root(cls, tmp_path: Path) -> None:
        """An internal tier imports root aliases from its own root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"r": "flext_tests", "c": ".constants"})
        normalized = cls._normalize(
            project,
            tier / "unit" / "test_demo.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg import c\n"
            "from flext_tests import r\n"
            "\n"
            "\n"
            "def test_demo() -> None:\n"
            "    assert r.ok(c)\n",
        )

        tm.that(normalized, has="from tests import c\n")
        tm.that(normalized, has="from tests import r\n")

    @classmethod
    def test_relative_import_becomes_absolute(cls, tmp_path: Path) -> None:
        """A service consumes its helper through the absolute lazy package."""
        project, package = cls._project(tmp_path)
        (package / "_utilities" / "helper.py").write_text(
            "class DemoHelper:\n"
            "    @staticmethod\n"
            "    def read(value):\n        return value\n"
            "__all__ = ['DemoHelper']\n",
            encoding="utf-8",
        )
        cls._lazy_init(package / "services", {"run": ".worker"})
        target = package / "services" / "worker.py"
        normalized = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from .._utilities.helper import DemoHelper\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    return DemoHelper.read('lazy-value')\n"
            "__all__ = ['run']\n",
        )
        target.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    "from demo_pkg.services import run; print(run())",
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="lazy-value")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )

    @classmethod
    def test_import_guard_becomes_plain_import(cls, tmp_path: Path) -> None:
        """A ``try/except ImportError`` guard becomes its plain imports."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "try:\n"
            "    import json\n"
            "except ImportError:\n"
            "    json = None\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    return json.dumps({})\n",
        )

        tm.that(normalized, lacks="except ImportError")
        tm.that(normalized, has="\nimport json\n")

    @classmethod
    def test_normalization_is_idempotent(cls, tmp_path: Path) -> None:
        """A second pass over the normalized module changes nothing."""
        project, package = cls._project(tmp_path)
        target = package / "services" / "worker.py"
        first = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from flext_core import r\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    from demo_pkg._models.record import DemoRecord\n"
            "\n"
            "    return r.ok(DemoRecord)\n",
        )

        second = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=target,
            source=first,
        )

        tm.that(second, eq=None)

    @classmethod
    def test_unbound_tier_letters_bind_through_tier_root(
        cls,
        tmp_path: Path,
    ) -> None:
        """A test module reading unbound tier letters imports them from its root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"c": ".constants", "u": ".utilities"})
        target = tier / "unit" / "test_demo.py"
        normalized = cls._normalize(
            project,
            target,
            '"""Demo tests."""\n'
            "\n"
            "from __future__ import annotations\n"
            "\n"
            "\n"
            "def test_demo(value: int) -> None:\n"
            "    assert u.Demo.run(c.Demo.NAME, value)\n",
        )

        tm.that(normalized, has="from tests import c, u\n")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )

    @classmethod
    def test_locally_bound_letter_is_not_imported(cls, tmp_path: Path) -> None:
        """A letter the module binds itself is never imported from its root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"c": ".constants"})
        result = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=tier / "unit" / "test_demo.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "\n"
                "def test_demo(c: int) -> None:\n"
                "    assert c\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    def test_tier_owner_drops_import_of_its_own_definition(
        cls,
        tmp_path: Path,
    ) -> None:
        """A tier facade module never imports the alias it defines from its root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"c": ".constants"})
        target = tier / "constants.py"
        normalized = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from tests import c\n"
            "\n"
            "\n"
            "class TestsDemoConstants:\n"
            "    NAME = 'tier-value'\n"
            "\n"
            "\n"
            "c = TestsDemoConstants\n"
            "__all__ = ['TestsDemoConstants', 'c']\n",
        )
        target.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (sys.executable, "-c", "from tests import c; print(c.NAME)"),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(project)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="tier-value")
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )
