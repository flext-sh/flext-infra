"""Class nesting leaves an immediate suite reference importable.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

import flext_infra
from flext_infra import config
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, tm, u


class TestsFlextInfraClassNestingSuiteScope:
    """A nested class suite cannot see a sibling while the owner is building."""

    @staticmethod
    def _test_workspace(tmp_path: Path, source: str) -> tuple[Path, Path]:
        """Declare one natively collected test module with governed patterns.

        Returns:
            The workspace root and the declared test module path.

        """
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        native = u.Infra.native_tool_settings(
            config.Infra.tooling, "pytest.ini_options"
        )
        python_files = u.Tests.strings(native["python_files"])
        python_classes = u.Tests.strings(native["python_classes"])
        project = root / c.PYPROJECT_FILENAME
        project.write_text(
            project.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            + "\n[tool.pytest.ini_options]\n"
            + f"python_files = {list(python_files)!r}\n"
            + f"python_classes = {list(python_classes)!r}\n"
            + "python_functions = ['test_*', 'check_*']\n"
            + "asyncio_default_fixture_loop_scope = "
            + f"{native['asyncio_default_fixture_loop_scope']!r}\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        directory = root / c.Infra.DIR_TESTS
        directory.mkdir(exist_ok=True)
        path = directory / python_files[0].replace("*", "native_suite")
        path.write_text(source, encoding=c.Infra.ENCODING_DEFAULT)
        return root, path

    @staticmethod
    def _plan_test(root: Path, path: Path, source: str) -> str:
        """Publish the public planner's proposed bytes and prove its fixed point.

        Returns:
            The published module source.

        """
        with flext_infra.infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources={path: source},
                ),
            )
            published = next(
                edit.updated_source for edit in edits if edit.file_path == path
            )
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                        rope_workspace=rope,
                        sources={path: published},
                    )
                ),
                eq=(),
            )
        path.write_text(published, encoding=c.Infra.ENCODING_DEFAULT)
        return published

    @staticmethod
    def _cold_pytest(root: Path, path: Path, *arguments: str) -> str:
        """Exercise real native collection/execution in a fresh interpreter.

        Returns:
            The cold pytest run's standard output.

        """
        cache = config.Infra.codegen.make.testmon_cache
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-m",
                    "pytest",
                    "-c",
                    str(root / c.PYPROJECT_FILENAME),
                    "-p",
                    "testmon.pytest_testmon",
                    "--testmon",
                    "-p",
                    "pytest_asyncio.plugin",
                    *arguments,
                    str(path),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env=u.Cli.process_env(
                        overrides={
                            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                            "PYTEST_ADDOPTS": "",
                            "PYTEST_PLUGINS": "",
                            cache.database_environment_variable: str(
                                root / cache.database_filename
                            ),
                        }
                    ),
                ),
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )
        return result.stdout

    @staticmethod
    @pytest.mark.parametrize("existing", [False, True])
    def test_native_functions_collect_and_execute_after_nesting(
        tmp_path: Path,
        *,
        existing: bool,
    ) -> None:
        """Decorators, async tests, injection, metadata and helpers survive.

        Cold pytest session behavior is asserted.
        """
        source = (
            "import pytest\n\n"
            "pytestmark = pytest.mark.usefixtures('session_probe')\n\n"
            "pytest_plugins = []\n\n"
            "class _Payload:\n    value = 7\n\n"
            "def _value():\n    return _Payload.value\n\n"
            "@pytest.mark.parametrize(\n"
            "    'value', [7, 8], ids=['first', 'second'],\n"
            ")\n"
            "def test_values(value, injected):\n"
            "    assert value >= _value()\n    assert injected == _value()\n\n"
            "@pytest.mark.asyncio\n"
            "async def test_async(injected):\n    assert injected == _value()\n\n"
            "def check_native(injected):\n    assert injected == _value()\n"
            + (
                "\nclass TestsExisting:\n"
                "    def test_existing(self):\n        assert _value() == 7\n"
                if existing
                else ""
            )
        )
        root, path = TestsFlextInfraClassNestingSuiteScope._test_workspace(
            tmp_path, source
        )
        conftest = path.parent / "conftest.py"
        conftest.write_text(
            "from pathlib import Path\nimport pytest\n\n"
            "@pytest.fixture(scope='session')\n"
            "def session_probe():\n"
            "    path = Path(__file__).with_name('session.log')\n"
            "    with path.open('a') as stream:\n        stream.write('start\\n')\n"
            "    yield\n"
            "    with path.open('a') as stream:\n        stream.write('stop\\n')\n\n"
            "@pytest.fixture\n"
            "def injected():\n    return 7\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        before = TestsFlextInfraClassNestingSuiteScope._cold_pytest(
            root,
            path,
            "--collect-only",
            "-q",
        )
        TestsFlextInfraClassNestingSuiteScope._cold_pytest(root, path, "-q")
        published = TestsFlextInfraClassNestingSuiteScope._plan_test(root, path, source)
        after = TestsFlextInfraClassNestingSuiteScope._cold_pytest(
            root,
            path,
            "--collect-only",
            "-q",
        )
        old_nodes = [line for line in before.splitlines() if "::" in line]
        new_nodes = [line for line in after.splitlines() if "::" in line]
        tm.that(
            [node.rsplit("::", 1)[-1] for node in new_nodes],
            eq=[node.rsplit("::", 1)[-1] for node in old_nodes],
        )
        if existing:
            tm.that(published.count("class TestsExisting:"), eq=1)
            tm.that(
                new_nodes,
                eq=[
                    node
                    if "::TestsExisting::" in node
                    else node.replace("::", "::TestsExisting::", 1)
                    for node in old_nodes
                ],
            )
        else:
            tm.ok(all("::Tests" in node for node in new_nodes))
        tm.ok("\npytestmark =" in published)
        tm.ok("\npytest_plugins =" in published)
        TestsFlextInfraClassNestingSuiteScope._cold_pytest(root, path, "-q")
        tm.that(
            (path.parent / "session.log").read_text().splitlines(),
            eq=["start", "stop"] * 2,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "declaration",
        [
            "@pytest.fixture\ndef injected():\n    return 1\n",
            "from pytest import fixture as fx\n@fx\ndef injected():\n    return 1\n",
            "def pytest_generate_tests(metafunc):\n    pass\n",
            "def setup_function(function):\n    pass\n",
        ],
    )
    def test_unmigrated_framework_registration_fails_loudly(
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Admitting native tests never admits unresolved hooks, fixtures or xunit."""
        source = "import pytest\n\n" + declaration + "\ndef test_native():\n    pass\n"
        root, path = TestsFlextInfraClassNestingSuiteScope._test_workspace(
            tmp_path, source
        )
        with flext_infra.infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="framework registration contract")
        tm.that(path.read_text(encoding=c.Infra.ENCODING_DEFAULT), eq=source)

    @staticmethod
    def test_existing_suite_retains_native_class_fixture_lifecycle(
        tmp_path: Path,
    ) -> None:
        """Helper nesting keeps the actual suite and its class-scoped finalizer."""
        source = (
            "from pathlib import Path\nimport pytest\n\n"
            "class _Payload:\n    value = 7\n\n"
            "class TestsLifecycle:\n"
            "    @pytest.fixture(scope='class')\n"
            "    def payload(self, request):\n"
            "        assert request.cls is TestsLifecycle\n"
            "        path = Path(__file__).with_name('class.log')\n"
            "        with path.open('a') as stream:\n"
            "            stream.write('start\\n')\n"
            "        yield _Payload()\n"
            "        with path.open('a') as stream:\n"
            "            stream.write('stop\\n')\n\n"
            "    @pytest.mark.parametrize('value', [7, 8])\n"
            "    def test_values(self, payload, value):\n"
            "        assert value >= payload.value\n\n"
            "    def test_again(self, payload):\n"
            "        assert payload.value == 7\n"
        )
        root, path = TestsFlextInfraClassNestingSuiteScope._test_workspace(
            tmp_path, source
        )
        before = TestsFlextInfraClassNestingSuiteScope._cold_pytest(
            root,
            path,
            "--collect-only",
            "-q",
        )
        TestsFlextInfraClassNestingSuiteScope._cold_pytest(root, path, "-q")
        published = TestsFlextInfraClassNestingSuiteScope._plan_test(root, path, source)
        after = TestsFlextInfraClassNestingSuiteScope._cold_pytest(
            root,
            path,
            "--collect-only",
            "-q",
        )
        tm.that(
            [line for line in after.splitlines() if "::" in line],
            eq=[line for line in before.splitlines() if "::" in line],
        )
        tm.that(published.count("class TestsLifecycle:"), eq=1)
        TestsFlextInfraClassNestingSuiteScope._cold_pytest(root, path, "-q")
        tm.that(
            (path.parent / "class.log").read_text().splitlines(),
            eq=["start", "stop"] * 2,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "member",
        [
            "    def setup_method(self):\n        pass\n",
            "    pytestmark = pytest.mark.usefixtures('injected')\n",
            (
                "    @pytest.fixture(scope='class')\n"
                "    def injected(self):\n"
                "        return 1\n"
            ),
            "    __test__ = False\n",
        ],
    )
    def test_free_tests_do_not_acquire_existing_suite_registration(
        tmp_path: Path,
        member: str,
    ) -> None:
        """Changed fixture, xunit or mark inheritance fails instead of applying.

        Silent inheritance changes are rejected.
        """
        source = (
            "import pytest\n\nclass TestsExisting:\n"
            + member
            + "\ndef test_native():\n    pass\n"
        )
        root, path = TestsFlextInfraClassNestingSuiteScope._test_workspace(
            tmp_path, source
        )
        with flext_infra.infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="registration or lifecycle would change")

    @staticmethod
    def _models_owner() -> tuple[str, str, str]:
        """Return the models alias, module file name, and owner class.

        Returns:
            The alias, the module stem, and the owner class name.

        """
        alias = next(
            letter
            for letter, family in u.Infra.facade_families().items()
            if family.module == "models"
        )
        module_name = u.Tests.family_public_module(alias)
        owner_name = (
            f"{u.derive_class_stem('flext-test-project')}"
            f"{u.Infra.facade_families()[alias].suffix}"
        )
        return alias, module_name, owner_name

    @classmethod
    def _publish(cls, tmp_path: Path, source: str) -> str:
        """Plan class nesting and return the source a later publish would write.

        Returns:
            The updated source, or ``source`` when the plan moves nothing.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        _alias, module_name, _owner_name = cls._models_owner()
        module_path = package_root / f"{module_name}.py"
        module_path.write_text(source, encoding=c.Infra.ENCODING_DEFAULT)
        with flext_infra.infra.rope_workspace(repository_root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module_path: source},
            )
        edits = tm.ok(planned)
        return edits[0].updated_source if edits else source

    @staticmethod
    def _load(published: str, tmp_path: Path) -> ModuleType:
        """Import published source as a module so a NameError fails the test.

        Returns:
            The loaded module.

        Raises:
            RuntimeError: If the published module has no loader.

        """
        module_path = tmp_path / "published_models.py"
        module_path.write_text(published, encoding=c.Infra.ENCODING_DEFAULT)
        spec = importlib.util.spec_from_file_location("published_models", module_path)
        if spec is None or spec.loader is None:
            msg = "published models module did not load"
            raise RuntimeError(msg)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_immediate_suite_reference_stays_at_module_level(
        self,
        tmp_path: Path,
    ) -> None:
        """A default factory that names a sibling stays a module global."""
        alias, _module_name, owner_name = self._models_owner()
        payload = f"{owner_name}Payload"
        holder = f"{owner_name}Holder"
        source = (
            '"""Models."""\n\n'
            "from __future__ import annotations\n\n"
            f'__all__: list[str] = ["{owner_name}", "{alias}"]\n\n'
            f"class {owner_name}:\n"
            '    """Owner."""\n\n'
            f"{alias} = {owner_name}\n\n"
            f"class {payload}:\n"
            '    """Payload."""\n\n'
            f"class {holder}:\n"
            '    """Holder."""\n\n'
            f"    payload = {payload}\n"
        )
        published = self._publish(tmp_path, source)
        loaded = self._load(published, tmp_path)
        holder_cls = getattr(loaded, holder)
        payload_cls = getattr(loaded, payload)
        tm.ok(isinstance(holder_cls, type))
        tm.ok(isinstance(payload_cls, type))
        tm.that(holder_cls.payload, eq=payload_cls)
        tm.ok(f"\nclass {holder}:" in published)
        tm.ok(f"\nclass {payload}:" in published)

    def test_inherited_siblings_still_nest_and_import(
        self,
        tmp_path: Path,
    ) -> None:
        """A base in the class header still moves under the owner."""
        alias, _module_name, owner_name = self._models_owner()
        base = f"{owner_name}Base"
        child = f"{owner_name}Child"
        source = (
            '"""Models."""\n\n'
            "from __future__ import annotations\n\n"
            f'__all__: list[str] = ["{owner_name}", "{alias}"]\n\n'
            f"class {owner_name}:\n"
            '    """Owner."""\n\n'
            f"{alias} = {owner_name}\n\n"
            f"class {base}:\n"
            '    """Base."""\n\n'
            f"class {child}({base}):\n"
            '    """Child."""\n'
        )
        published = self._publish(tmp_path, source)
        loaded = self._load(published, tmp_path)
        owner = getattr(loaded, owner_name)
        tm.ok(isinstance(owner, type))
        nested_child = getattr(owner, child)
        nested_base = getattr(owner, base)
        tm.ok(issubclass(nested_child, nested_base))

    def test_nested_view_keeps_a_module_level_base_importable(
        self,
        tmp_path: Path,
    ) -> None:
        """A class already inside the owner does not pull its target's base in."""
        alias, _module_name, owner_name = self._models_owner()
        payload = f"{owner_name}Payload"
        holder = f"{owner_name}Holder"
        source = (
            '"""Models."""\n\n'
            "from __future__ import annotations\n\n"
            f'__all__: list[str] = ["{owner_name}", "{alias}"]\n\n'
            f"class {payload}:\n"
            '    """Payload."""\n\n'
            f"class {holder}({payload}):\n"
            '    """Holder."""\n\n'
            f"class {owner_name}:\n"
            '    """Owner."""\n\n'
            "    class View:\n"
            '        """View."""\n\n'
            f"        item = {holder}\n\n"
            f"{alias} = {owner_name}\n"
        )
        published = self._publish(tmp_path, source)
        loaded = self._load(published, tmp_path)
        owner = getattr(loaded, owner_name)
        holder_cls = getattr(loaded, holder)
        payload_cls = getattr(loaded, payload)
        tm.that(owner.View.item, eq=holder_cls)
        tm.ok(issubclass(holder_cls, payload_cls))
        tm.ok(f"\nclass {holder}({payload}):" in published)

    def test_nested_class_decorator_keeps_a_moved_helper_bare(
        self,
        tmp_path: Path,
    ) -> None:
        """A field specifier named by a nested model's decorator stays bare."""
        alias, _module_name, owner_name = self._models_owner()
        source = (
            '"""Models."""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import dataclass_transform\n\n"
            f'__all__: list[str] = ["{owner_name}", "{alias}"]\n\n'
            "def _field(default: int = 0) -> int:\n"
            '    """Field."""\n'
            "    return default\n\n"
            f"class {owner_name}:\n"
            '    """Owner."""\n\n'
            "    @dataclass_transform(field_specifiers=(_field,))\n"
            "    class BaseModel:\n"
            '        """Model."""\n\n'
            f"{alias} = {owner_name}\n"
        )
        published = self._publish(tmp_path, source)
        tm.fail(f"{owner_name}._field" in published)
        tm.that(u.Infra.definition_time_name_errors(published), eq=())
        owner = getattr(self._load(published, tmp_path), owner_name)
        specifiers = owner.BaseModel.__dataclass_transform__["field_specifiers"]
        tm.that(len(specifiers), eq=1)
        tm.ok(specifiers[0] is vars(owner)["_field"])

    def test_method_decorator_reference_stays_at_module_level(
        self,
        tmp_path: Path,
    ) -> None:
        """A sibling suite whose method decorator reads a helper keeps both."""
        alias, _module_name, owner_name = self._models_owner()
        holder = f"{owner_name}Holder"
        source = (
            '"""Models."""\n\n'
            "from __future__ import annotations\n\n"
            "import functools\n\n"
            f'__all__: list[str] = ["{owner_name}", "{alias}"]\n\n'
            "def _size() -> int:\n"
            '    """Size."""\n'
            "    return 2\n\n"
            f"class {owner_name}:\n"
            '    """Owner."""\n\n'
            f"{alias} = {owner_name}\n\n"
            f"class {holder}:\n"
            '    """Holder."""\n\n'
            "    @staticmethod\n"
            "    @functools.lru_cache(maxsize=_size())\n"
            "    def value() -> int:\n"
            '        """Value."""\n'
            "        return 1\n"
        )
        published = self._publish(tmp_path, source)
        tm.that(u.Infra.definition_time_name_errors(published), eq=())
        loaded = self._load(published, tmp_path)
        tm.that(getattr(loaded, holder).value(), eq=1)
        tm.ok(f"\nclass {holder}:" in published)
        tm.ok("\ndef _size() -> int:" in published)

    def test_semantic_apply_refuses_a_plan_that_breaks_import(
        self,
        tmp_path: Path,
    ) -> None:
        """A moved default that reads a later module binding publishes nothing."""
        alias, module_name, owner_name = self._models_owner()
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / f"{module_name}.py"
        source = (
            '"""Models."""\n\n'
            "from __future__ import annotations\n\n"
            f'__all__: list[str] = ["{owner_name}", "{alias}"]\n\n'
            f"class {owner_name}:\n"
            '    """Owner."""\n\n'
            f"{alias} = {owner_name}\n\n"
            "LIMIT = len\n\n"
            "def _helper(measure: object = LIMIT) -> object:\n"
            '    """Helper."""\n'
            "    return measure\n"
        )
        path.write_text(source, encoding=c.Infra.ENCODING_DEFAULT)
        u.Tests.initialize_git_repo(root)
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence] = (
            m.Infra.ModOccurrenceReport(
                files=frozenset(),
                entries=(),
            )
        )
        with flext_infra.infra.rope_workspace(root) as rope:
            applied = FlextInfraCodemodSemanticApply.apply(
                root,
                report,
                rope,
                source_preview=flext_infra.infra.source_preview(root),
                workspace_factory=flext_infra.infra.rope_workspace,
            )
        tm.fail(applied, has=f"{owner_name}: LIMIT")
        tm.that(path.read_text(encoding=c.Infra.ENCODING_DEFAULT), eq=source)

    @staticmethod
    def test_detector_reports_the_owner_named_inside_its_own_suite() -> None:
        """The NameError shape class nesting once published is reported."""
        source = (
            "from typing import dataclass_transform\n\n"
            "class Owner:\n"
            "    @staticmethod\n"
            "    def _field() -> int:\n"
            "        return 0\n\n"
            "    @dataclass_transform(field_specifiers=(Owner._field,))\n"
            "    class BaseModel:\n"
            "        pass\n"
        )
        tm.that(u.Infra.definition_time_name_errors(source), eq=("Owner: Owner",))

    @staticmethod
    def test_detector_reports_an_enclosing_class_binding() -> None:
        """A nested suite cannot read a binding of the class around it."""
        source = (
            "class Owner:\n"
            "    _CASES = (1, 2)\n\n"
            "    class Inner:\n"
            "        size = len(_CASES)\n"
        )
        tm.that(
            u.Infra.definition_time_name_errors(source),
            eq=("Owner.Inner: _CASES",),
        )

    @staticmethod
    def test_detector_accepts_deferred_and_module_bound_loads() -> None:
        """Function bodies, lambdas, type aliases and module globals resolve."""
        source = (
            "from typing import ClassVar\n\n"
            "LIMIT = 3\n\n"
            "class Owner[T]:\n"
            "    items: ClassVar[tuple[int, ...]] = tuple(range(LIMIT))\n"
            "    squares = {item: item * item for item in items}\n"
            "    type Alias = Owner[T]\n"
            "    factory = staticmethod(lambda: Owner)\n\n"
            "    def method(self) -> type[Owner[T]]:\n"
            "        return Owner\n\n"
            "    @staticmethod\n"
            "    def labels(names: tuple[str, ...] = tuple(n for n in 'ab')) -> int:\n"
            "        return len(names)\n\n"
            "    class Inner:\n"
            "        limit = LIMIT\n\n"
            "    class Box[V](list[V]):\n"
            "        pass\n"
        )
        tm.that(u.Infra.definition_time_name_errors(source), eq=())
