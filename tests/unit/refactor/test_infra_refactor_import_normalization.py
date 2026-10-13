"""Behavior of the FLEXT import-law engine on real package trees.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, m
from flext_infra.refactor import FlextInfraImportNormalization
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalization:
    """Each import-law rule observed through ``normalize_source``."""

    @classmethod
    def test_runtime_promotion_rejects_reverse_namespace_edges(
        cls, tmp_path: Path
    ) -> None:
        """Runtime demand cannot authorize a higher self-namespace dependency."""
        project, package = cls._project(tmp_path)
        module = package / "models.py"
        source = (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            f"    from {package.name} import u\n"
            "value = u()\n"
        )
        module.write_text(source, encoding="utf-8")
        with pytest.raises(ValueError, match="forbidden reverse namespace import"):
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=source
            )
        tm.that(module.read_text(encoding="utf-8"), eq=source)

    @classmethod
    @pytest.mark.parametrize("model", [False, True])
    def test_typing_guard_promotes_real_definition_time_imports(
        cls, tmp_path: Path, *, model: bool
    ) -> None:
        """A fresh consumer resolves evaluated generics and Pydantic annotations."""
        project, package = cls._project(tmp_path)
        module = package / ("models.py" if model else "consumer.py")
        declaration = (
            "from flext_core import m\n"
            "class Record(m.ContractModel):\n"
            "    value: Path = m.Field(description='Consumer path')\n"
            "value = Record(value=Path('consumer')).value\n"
            if model
            else "from flext_core import r\n"
            "value = r[tuple[Path, ...]].ok((Path('consumer'),)).unwrap()[0]\n"
        )
        source = (
            "from __future__ import annotations\n"
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from pathlib import Path, PurePath\n"
            + declaration
            + "def annotate(value: PurePath) -> PurePath:\n"
            "    return value\n"
        )
        normalized = cls._normalize(project, module, source)
        module.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.{module.stem} import value, annotate; "
                        "assert str(value) == 'consumer'; "
                        "assert annotate(value) == value"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=normalized
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
            f"{c.Infra.AUTOGEN_HEADER}\n"
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
            "            local: bool = FlextTestsModels.Field("
            "default=True, description='Local consumer field')\n\n"
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
        tm.that(result, eq=None)
        (package / "_config.py").write_text(source, encoding="utf-8")
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

    @classmethod
    def test_nested_config_models_are_family_sources_not_layer_zero(
        cls, tmp_path: Path
    ) -> None:
        """Domain config MRO assembly remains valid source for generated facets."""
        project, package = cls._project(tmp_path)
        family = u.Infra.facade_families()["m"]
        module = package / family.directory / "_config" / "base.py"
        source = (
            f"from demo_pkg.{family.directory}._config.part import ConfigPart\n"
            "class ConfigModels(ConfigPart):\n    pass\n"
            "__all__ = ['ConfigModels']\n"
        )
        tm.that(
            u.Infra.import_module_role("demo_pkg._models._config.base"), eq="family"
        )
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project, file_path=module, source=source
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize("letter", sorted(u.Infra.facade_families()))
    def test_missing_reverse_runtime_letter_is_not_synthesized(
        cls, tmp_path: Path, letter: str
    ) -> None:
        """A missing higher own alias is a defect, never a new runtime edge."""
        project, package = cls._project(tmp_path)
        families = u.Infra.facade_families()
        higher = [
            name
            for name, family in families.items()
            if u.Infra.module_import_layer(f"demo_pkg.{family.module}")
            > u.Infra.module_import_layer(f"demo_pkg.{families[letter].module}")
        ]
        cls._lazy_init(
            package, {name: f".{family.module}" for name, family in families.items()}
        )
        for name in higher:
            with pytest.raises(ValueError, match="forbidden reverse namespace import"):
                FlextInfraImportNormalization.normalize_source(
                    project_root=project,
                    file_path=package / families[letter].directory / "declaration.py",
                    source=f"value = {name}.Value\n",
                )
            module = package / families[letter].directory / "annotations.py"
            normalized = cls._normalize(
                project,
                module,
                "from __future__ import annotations\n"
                f"def describe(value: {name}.Value) -> str:\n    return 'value'\n",
            )
            tm.that(
                normalized,
                has=f"if TYPE_CHECKING:\n    from demo_pkg import {name}\n",
            )
            tm.that(
                FlextInfraImportNormalization.normalize_source(
                    project_root=project, file_path=module, source=normalized
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
        """A relative own-package import becomes its absolute form."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "_utilities" / "extra.py",
            "from __future__ import annotations\n"
            "\n"
            "from .helper import DemoHelper\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    return DemoHelper\n",
        )

        tm.that(normalized, has="from demo_pkg._utilities import DemoHelper\n")
        tm.that(normalized, lacks="from .helper")

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
        cls._lazy_init(tier, {"c": ".constants", "u": ".utilities"})
        normalized = cls._normalize(
            project,
            tier / "constants.py",
            "from __future__ import annotations\n"
            "\n"
            "from tests import c, u\n"
            "\n"
            "\n"
            "class TestsDemoConstants:\n"
            "    HELPER = u\n"
            "\n"
            "\n"
            "c = TestsDemoConstants\n",
        )

        tm.that(normalized, has="from tests import u\n")
        tm.that(normalized, lacks="from tests import c")
