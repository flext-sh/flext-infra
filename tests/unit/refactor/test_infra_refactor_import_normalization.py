"""Behavior of the FLEXT import-law engine on real package trees.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import m, refactor, transformers
from tests import c, tm, u
from tests.unit.refactor.import_normalization_support import (
    TestsFlextInfraRefactorImportNormalizationSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalization(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Each import-law rule observed through ``normalize_source``."""

    @classmethod
    @pytest.mark.parametrize("consumer", [False, True])
    def test_function_publication_never_routes_initializer_to_itself(
        cls, tmp_path: Path, *, consumer: bool
    ) -> None:
        """Static function exports keep their native owner inside its initializer."""
        project, package = cls._project(tmp_path)
        owner = package / "_utilities"
        cls._lazy_init(owner, {"inspect_value": ".inspection"})
        (owner / "inspection.py").write_text(
            "def inspect_value(value: str) -> str:\n    return value\n"
            "__all__ = ['inspect_value']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = package / "consumer.py" if consumer else owner / c.Infra.INIT_PY
        before = (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from demo_pkg._utilities.inspection import inspect_value\n"
        )
        normalized = refactor.FlextInfraImportNormalization.normalize_source(
            project_root=project, file_path=target, source=before
        )
        if consumer:
            tm.that(normalized, has="from demo_pkg._utilities import inspect_value")
        else:
            tm.that(normalized, eq=None)
            tm.that(
                refactor.FlextInfraImportNormalization.normalize_source(
                    project_root=project, file_path=target, source=before
                ),
                eq=None,
            )

    @classmethod
    def test_import_plan_uses_working_sources_without_replacing_original_receipts(
        cls,
        tmp_path: Path,
    ) -> None:
        """Working imports and lazy exports remain separate from physical sources."""
        project, package = cls._project(tmp_path)
        helper = package / "_utilities" / "helper.py"
        helper.write_text(
            "class DemoHelper:\n    marker = 'published'\n__all__ = ['DemoHelper']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = package / "consumer.py"
        target.write_text("value = 'original'\n", encoding=c.DEFAULT_ENCODING)
        paths = tm.ok(
            u.Infra.iter_python_files(
                m.Infra.SourceScanRequest(project_roots=(project,)),
            )
        )
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in paths
        )
        sources = {
            state.path: tm.not_none(state.content).decode(c.DEFAULT_ENCODING)
            for state in states
        }
        working = {
            **sources,
            target: (
                "from demo_pkg._utilities import DemoHelper as imported\n"
                "value = imported.marker\n"
            ),
        }
        frozen = dict(working)
        with u.Infra.open_project(project) as rope:
            analysis = tm.ok(
                refactor.FlextInfraImportNormalization.plan_files(
                    project,
                    (target,),
                    sources=working,
                    receipt=m.Infra.CodegenPhaseAnalysis(
                        phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                        inputs=states,
                        files=(),
                    ),
                    rope_project=rope,
                )
            )
        tm.that(analysis.files, length=1)
        plan = analysis.files[0]
        tm.that(plan.before, eq=next(state for state in states if state.path == target))
        desired = tm.not_none(plan.desired_content).decode(c.DEFAULT_ENCODING)
        tm.that(desired, has="value = DemoHelper.marker")
        tm.that(desired, lacks="as imported")
        tm.that(working, eq=frozen)
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)

    @classmethod
    def test_own_import_alias_rewrites_only_bound_references(
        cls, tmp_path: Path
    ) -> None:
        """The published name replaces the alias without changing homonyms or data."""
        project, package = cls._project(tmp_path)
        helper = package / "_utilities" / "helper.py"
        helper.write_text(
            "class DemoHelper:\n    marker = 'published'\n__all__ = ['DemoHelper']\n",
            encoding="utf-8",
        )
        target = package / "consumer.py"
        normalized = cls._normalize(
            project,
            target,
            "from demo_pkg._utilities import DemoHelper as files\n"
            "value = files.marker\n"
            "literal = 'files'\n"
            "def sibling(files: str) -> str:\n    return files\n",
        )
        tm.that(normalized, lacks="as files")
        tm.that(normalized, has="value = DemoHelper.marker")
        tm.that(normalized, has="return files")
        tm.that(normalized, has="literal = 'files'")
        target.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg.consumer import value, sibling, literal; "
                        "assert value == 'published'; assert sibling('local') == "
                        "'local'; "
                        "assert literal == 'files'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.ok(u.Cli.process_succeeded(result.outcome))
        tm.that(
            refactor.FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )

    @classmethod
    def test_own_import_alias_rejects_destination_capture(cls, tmp_path: Path) -> None:
        """A local canonical-name parameter cannot capture an imported reference."""
        project, package = cls._project(tmp_path)
        target = package / "consumer.py"
        source = (
            "from demo_pkg._utilities import DemoHelper as files\n"
            "def consumer(DemoHelper: str) -> str:\n    return files.marker\n"
        )
        target.write_text(source, encoding="utf-8")
        with pytest.raises(ValueError, match="destination is occupied"):
            refactor.FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=target,
                source=source,
            )
        tm.that(target.read_text(encoding="utf-8"), eq=source)

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
            refactor.FlextInfraImportNormalization.normalize_source(
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
        tm.ok(u.Cli.process_succeeded(result.outcome))
        tm.that(
            refactor.FlextInfraImportNormalization.normalize_source(
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
            refactor.FlextInfraImportNormalization.normalize_source(
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
        u.Tests.run_native_callable(
            cls.scenario_declared_destination, tmp_path, destination
        )

    @classmethod
    def scenario_declared_destination(
        cls,
        tmp_path: Path,
        destination: str,
    ) -> None:
        """Exercise publication in the real native runner without pytest hooks."""
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
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=project,
                options=m.Infra.SemanticPublicationOptions(projection_roots=(project,)),
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
        tm.ok(u.Cli.process_succeeded(result.outcome))

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
        normalized = refactor.FlextInfraImportNormalization.normalize_source(
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
        tm.ok(u.Cli.process_succeeded(result.outcome))

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
        normalized = refactor.FlextInfraImportNormalization.normalize_source(
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
        tm.ok(u.Cli.process_succeeded(result.outcome))

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
        normalized = refactor.FlextInfraImportNormalization.normalize_source(
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
        tm.ok(u.Cli.process_succeeded(result.outcome))

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
        tm.ok(u.Cli.process_succeeded(result.outcome))

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
        result = refactor.FlextInfraImportNormalization.normalize_source(
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
