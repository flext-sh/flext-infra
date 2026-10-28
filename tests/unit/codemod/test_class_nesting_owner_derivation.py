"""Class nesting derives one owner for a module of loose members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import MutableMapping
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from tests import c, t, tm, u
from tests.unit.codemod.class_nesting_owner_support import (
    TestsFlextInfraClassNestingSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraClassNestingOwnerDerivation(TestsFlextInfraClassNestingSupport):
    """Modules elect one owner and their consumers follow the moved identities."""

    @pytest.mark.parametrize(
        ("stem", "source", "expected"),
        [
            pytest.param(
                "atomic_thing",
                TestsFlextInfraClassNestingSupport.LOOSE_MODULE,
                (
                    'class {owner}:\n    """Loose helpers of one family module."""',
                    "    @staticmethod\n    def write(",
                    "    @staticmethod\n    def _helper(",
                    "    class _Marker:",
                    "return {owner}._helper(path) + {owner}._MODE",
                    "    # Owner-only permission bits.",
                ),
                id="loose-members",
            ),
            pytest.param(
                "atomic_thing",
                TestsFlextInfraClassNestingSupport.LOOSE_MODULE,
                (
                    "from typing import ClassVar",
                    "    _MODE: ClassVar[int] = 0o600",
                    "    LIMIT: ClassVar[int] = 3",
                    "    _SENTINEL = _Marker()",
                ),
                id="class-variables",
            ),
            pytest.param(
                "pair_helpers",
                '"""Two private helpers."""\n\n'
                "from __future__ import annotations\n\n\n"
                "class _First:\n    pass\n\n\n"
                "class _Second(_First):\n    pass\n",
                ("    class _First:", "    class _Second(_First):"),
                id="private-classes",
            ),
            pytest.param(
                "mode_helpers",
                '"""Sentinel and helper."""\n\n'
                "from __future__ import annotations\n\n\n"
                "class {helper}:\n    pass\n\n\n"
                "NO_PRECONDITION = {helper}()\n\n\n"
                "def check(value: int) -> int:\n    return value\n\n\n"
                '__all__: list[str] = ["{helper}", "NO_PRECONDITION", "check"]\n',
                ("    class {helper}:",),
                id="published-record",
            ),
            pytest.param(
                "step_helpers",
                '"""Declared owner and loose helpers."""\n\n'
                "from __future__ import annotations\n\n\n"
                "def _strip(value: str) -> str:\n    return value.strip()\n\n\n"
                "class {owner}:\n"
                '    """Step helpers."""\n\n'
                "    @staticmethod\n"
                "    def clean(value: str) -> str:\n"
                '        """Return the stripped value."""\n'
                "        return _strip(value)\n\n\n"
                '__all__: list[str] = ["{owner}"]\n',
                ("    @staticmethod\n    def _strip(",),
                id="declared-owner",
            ),
            pytest.param(
                "registry_helpers",
                '"""Registry annotations."""\n\n'
                "from __future__ import annotations\n\n"
                "from typing import ClassVar\n\n\n"
                "class _Handler:\n"
                "    @staticmethod\n"
                "    def current() -> _Registry:\n"
                "        return _Registry.current()\n\n\n"
                "class _Registry:\n"
                "    _current: ClassVar[_Registry | None] = None\n\n"
                "    @classmethod\n"
                "    def start(cls) -> _Registry:\n"
                "        return cls()\n\n"
                "    @classmethod\n"
                "    def current(cls) -> _Registry:\n"
                "        return cls()\n",
                (
                    "def current() -> {owner}._Registry:",
                    "return {owner}._Registry.current()",
                    "_current: ClassVar[{owner}._Registry | None] = None",
                    "def start(cls) -> {owner}._Registry:",
                    "def current(cls) -> {owner}._Registry:",
                ),
                id="nested-annotations",
            ),
        ],
    )
    def test_family_members_nest_under_one_owner(
        self,
        tmp_path: Path,
        stem: str,
        source: str,
        expected: t.StrTuple,
    ) -> None:
        """Family declarations share one owner without losing their member contracts."""
        root, module = self._family_module(tmp_path, stem, "")
        owner = self._derived_owner(root, stem)
        helper = f"{u.derive_class_stem(root.name)}NoPrecondition"
        source = source.replace("{owner}", owner).replace("{helper}", helper)
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        tm.that(self._top_level(nested), eq=(owner, "__all__"))
        exports = tm.instance(ast.parse(nested).body[-1], ast.AnnAssign)
        tm.that(ast.unparse(exports.annotation), eq="list[str]")
        tm.that(
            u.Infra.module_assignment_strings_source(nested, c.Infra.DUNDER_ALL),
            eq=(owner,),
        )
        for fragment in expected:
            tm.that(
                nested,
                has=fragment.replace("{owner}", owner).replace("{helper}", helper),
            )
        tm.that(nested, lacks="Canonical namespace owner")
        tm.that(residue, eq={})
        compile(nested, str(module), "exec")

    def test_strict_test_prefix_renames_nested_and_function_local_consumers(
        self,
        tmp_path: Path,
    ) -> None:
        """Native Rope rewires imported identities without touching string payloads."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = root / "tests"
        tm.ok(u.Cli.ensure_dir(directory))
        tm.ok(u.Cli.atomic_write_text_file(directory / "__init__.py", ""))
        module = directory / "test_semantic.py"
        consumer = root / "consumer.py"
        source = (
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n    from pathlib import Path\n\n"
            "__all__: list[str] = ['TestBehavior']\n"
            "class TestBehavior:\n"
            "    class Nested:\n        value = 7\n"
            "    @staticmethod\n"
            "    def test_identity():\n"
            "        class Local:\n            value = 11\n"
            "        return Local.value + TestBehavior.Nested.value\n"
        )
        reader = (
            "from tests.test_semantic import TestBehavior as Subject\n"
            "class Consumer:\n"
            "    @staticmethod\n"
            "    def run():\n        return Subject.test_identity()\n"
            "    @staticmethod\n"
            "    def echo(value: ('Sub' 'ject.Nested')) -> 'Subject.Nested':\n"
            "        return value\n"
            "    payload = 'TestBehavior.Nested'\n"
        )
        for path, text in ((module, source), (consumer, reader)):
            tm.ok(u.Cli.atomic_write_text_file(path, text))
        updated, residue = self._plan(root, {module: source, consumer: reader})
        with infra.rope_workspace(root) as rope:
            prefix = rope.convention(module).module_policy.project_prefix
        tree = ast.parse(updated[module])
        classes = tuple(
            node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
        )
        tm.that(
            len([node for node in tree.body if isinstance(node, ast.ClassDef)]), eq=1
        )
        tm.ok(all(node.name.startswith(prefix) for node in classes))
        root_owner = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        exports = next(
            node
            for node in root_owner.body
            if isinstance(node, c.Infra.AST_ASSIGNMENT_TYPES)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        )
        tm.that(u.Infra.literal_string_sequence(exports.value), eq=(root_owner.name,))
        tm.that(self._top_level(updated[module]), eq=(root_owner.name,))
        tm.that(updated[consumer], has="payload = 'TestBehavior.Nested'")
        tm.that(updated[consumer], lacks="import TestBehavior as Subject")
        for path, text in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, text))
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from consumer import Consumer\n"
                "from typing import get_type_hints\n"
                "hints = get_type_hints(Consumer.echo)\n"
                "assert hints['value'] is hints['return']\n"
                "print(Consumer.run())",
                python_paths=(),
                cwd=root,
            ),
            eq=["18"],
        )
        tm.that(residue, eq={})

    @pytest.mark.parametrize(
        ("relative_module", "source", "errors"),
        [
            pytest.param(
                "tests/test_guard.py",
                "from typing import TYPE_CHECKING\n"
                f"if TYPE_CHECKING:\n    {statement}\n"
                "class Guard:\n    value = 1\n",
                ("unsupported module statements: If",),
                id=f"typing-guard-{index}",
            )
            for index, statement in enumerate((
                "VALUE = 1",
                "def helper():\n        return 1",
            ))
        ]
        + [
            pytest.param(
                "processor.py",
                '"""Competing owners."""\n'
                "class First:\n    pass\nclass Second:\n    pass\n",
                ("requires exactly one declared module owner",),
                id="competing-owners",
            ),
            pytest.param(
                "processor.py",
                '"""Immediate suite dependencies."""\n'
                "class Processor:\n    pass\n\n"
                "class _Payload:\n    pass\n\n"
                "class _Holder:\n    payload = _Payload\n",
                ("definition-time dependencies pin",),
                id="suite-dependencies",
            ),
            pytest.param(
                "{family}/rival_owners.py",
                '"""Two candidate owners."""\n\n'
                "from __future__ import annotations\n\n\n"
                "class {owner}Alpha:\n    pass\n\n\n"
                "class {owner}Beta:\n    pass\n\n\n"
                '__all__: list[str] = ["{owner}Alpha", "{owner}Beta"]\n',
                ("requires exactly one declared module owner", "rival_owners"),
                id="rival-stems",
            ),
        ],
    )
    def test_invalid_module_ownership_fails_before_edits(
        self,
        tmp_path: Path,
        relative_module: str,
        source: str,
        errors: t.StrTuple,
    ) -> None:
        """Invalid ownership or declaration timing refuses the untouched source."""
        if relative_module.startswith("{family}/"):
            root, module = self._family_module(
                tmp_path, relative_module.rsplit("/", 1)[1].removesuffix(".py"), ""
            )
        else:
            root, package = u.Tests.create_lazy_init_workspace(tmp_path)
            parent = root if relative_module.startswith("tests/") else package
            module = parent / relative_module
        source = source.replace("{owner}", self._derived_owner(root, module.stem))
        tm.ok(u.Cli.ensure_dir(module.parent))
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )
        for error in errors:
            tm.fail(result, has=error)
        tm.that(module.read_text(), eq=source)

    def test_strict_conftest_preserves_directory_scope_hooks_and_generator_teardown(
        self,
        tmp_path: Path,
    ) -> None:
        """Original conftest registration retains scoped fixtures and hook wrappers."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        first, second = root / "tests" / "first", root / "tests" / "second"
        for directory in (first, second):
            tm.ok(u.Cli.ensure_dir(directory))
        conftest = first / "conftest.py"
        events = root / "events.txt"
        source = (
            "from pathlib import Path\n"
            "from collections.abc import Iterator\n"
            "import pytest\n"
            f"EVENTS = Path({str(events)!r})\n"
            "def record(value: str) -> None:\n"
            "    with EVENTS.open('a') as stream:\n"
            "        stream.write(value + '\\n')\n"
            "@pytest.fixture(scope='module')\n"
            "def scoped_resource() -> Iterator[int]:\n"
            "    record('setup')\n    yield 7\n    record('teardown')\n"
            "@pytest.hookimpl(wrapper=True)\n"
            "def pytest_runtest_call(item) -> Iterator[None]:\n"
            "    record('before')\n    yield\n    record('after')\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(conftest, source))
        tm.ok(
            u.Cli.atomic_write_text_file(
                first / "test_first.py",
                "def test_one(scoped_resource):\n    assert scoped_resource == 7\n"
                "def test_two(scoped_resource):\n    assert scoped_resource == 7\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                second / "test_second.py",
                "import pytest\n"
                "def test_isolation(request):\n"
                "    with pytest.raises(pytest.FixtureLookupError):\n"
                "        request.getfixturevalue('scoped_resource')\n",
            )
        )
        probe = (
            "import os, contextlib, io\n"
            "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'\n"
            "import pytest\n"
            "with contextlib.redirect_stdout(io.StringIO()):\n"
            "    result = pytest.main(\n"
            "        ['tests', '--tb=short', '-p', 'no:cacheprovider'],\n"
            "    )\n"
            "assert result == 0, result\n"
            f"from pathlib import Path\n"
            f"print(Path({str(events)!r}).read_text().strip())\n"
        )
        before = u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root)
        tm.ok(u.Cli.atomic_write_text_file(events, ""))
        updated, residue = self._plan(root, {conftest: source})
        nested = updated[conftest]
        tree = ast.parse(nested)
        tm.that(
            len([node for node in tree.body if isinstance(node, ast.ClassDef)]), eq=1
        )
        tm.that(
            any(
                isinstance(node, ast.FunctionDef | ast.Assign | ast.AnnAssign)
                for node in tree.body
            ),
            eq=False,
        )
        tm.that(nested, has="@staticmethod\n    @pytest.fixture")
        tm.that(nested, has="'scoped_resource': scoped_resource.__func__")
        tm.that(nested, has="'pytest_runtest_call': pytest_runtest_call.__func__")
        tm.ok(u.Cli.atomic_write_text_file(conftest, nested))
        tm.that(
            u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root), eq=before
        )
        tm.that(before, eq=["setup", "before", "after", "before", "after", "teardown"])
        tm.that(residue, eq={})

    def test_strict_free_tests_collect_with_module_marks_and_xunit_teardown(
        self,
        tmp_path: Path,
    ) -> None:
        """Class collection preserves module marks, module fixture caching and xunit."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = root / "tests"
        tm.ok(u.Cli.ensure_dir(directory))
        module = directory / "test_free.py"
        source = (
            '"""Free test module with native lifecycle."""\n'
            "from collections.abc import Iterator\n"
            "import pytest\n"
            "pytestmark = pytest.mark.usefixtures('token')\n"
            "_EVENTS: list[str] = []\n"
            "@pytest.fixture(scope='module')\n"
            "def token() -> Iterator[str]:\n"
            "    _EVENTS.append('setup')\n"
            "    yield 'ready'\n"
            "    _EVENTS.append('stop')\n"
            "def teardown_module() -> None:\n"
            "    assert _EVENTS == ['setup', 'one', 'two', 'stop']\n"
            "def test_one(token: str) -> None:\n"
            "    assert token == 'ready'\n    _EVENTS.append('one')\n"
            "def test_two(token: str) -> None:\n"
            "    assert token == 'ready'\n    _EVENTS.append('two')\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        probe = (
            "import os, contextlib, io\n"
            "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'\n"
            "import pytest\n"
            "stream = io.StringIO()\n"
            "with contextlib.redirect_stdout(stream):\n"
            "    result = pytest.main(\n"
            "        ['tests', '--tb=short', '-p', 'no:cacheprovider'],\n"
            "    )\n"
            "assert result == 0, stream.getvalue()\n"
            "print('2 passed' in stream.getvalue())\n"
        )
        before = u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root)
        updated, residue = self._plan(root, {module: source})
        nested = updated[module]
        tree = ast.parse(nested)
        tm.that(
            all(
                isinstance(node, c.Infra.AST_IMPORT_OR_CLASS_TYPES)
                for node in tree.body
            ),
            eq=True,
        )
        tm.that(
            len([node for node in tree.body if isinstance(node, ast.ClassDef)]), eq=1
        )
        tm.that(nested, has="del pytestmark")
        tm.ok(u.Cli.atomic_write_text_file(module, nested))
        tm.that(
            u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root), eq=before
        )
        tm.that(before, eq=["True"])
        tm.that(residue, eq={})

    def test_strict_existing_instance_fixture_keeps_its_class_visibility(
        self,
        tmp_path: Path,
    ) -> None:
        """Existing instance fixtures are not republished as module fixtures."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = root / "tests"
        tm.ok(u.Cli.ensure_dir(directory))
        module = directory / "test_existing.py"
        source = (
            "import pytest\n"
            "LABEL: str = 'ready'\n"
            "class TestExisting:\n"
            "    @pytest.fixture\n"
            "    def local(self) -> str:\n        return LABEL\n"
            "    def test_one(self, local: str) -> None:\n"
            "        assert local == 'ready'\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        probe = (
            "import os, contextlib, io\n"
            "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'\n"
            "import pytest\n"
            "stream = io.StringIO()\n"
            "with contextlib.redirect_stdout(stream):\n"
            "    result = pytest.main(\n"
            "        ['tests', '--tb=short', '-p', 'no:cacheprovider'],\n"
            "    )\n"
            "assert result == 0, stream.getvalue()\n"
            "print('1 passed' in stream.getvalue())\n"
        )
        before = u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root)
        updated, residue = self._plan(root, {module: source})
        tm.that(updated[module], lacks="FlextTestsConftestPlugin")
        tm.that(updated[module], has="@pytest.fixture\n    def local(self)")
        tm.ok(u.Cli.atomic_write_text_file(module, updated[module]))
        tm.that(
            u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root), eq=before
        )
        tm.that(before, eq=["True"])
        tm.that(residue, eq={})

    @pytest.mark.parametrize("suppressed", [False, True])
    def test_strict_helper_prefix_does_not_invent_pytest_suites(
        self,
        tmp_path: Path,
        *,
        suppressed: bool,
    ) -> None:
        """Constructor-bearing helpers require an existing non-suite contract."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = root / "tests"
        tm.ok(u.Cli.ensure_dir(directory))
        module = directory / "test_helper.py"
        marker = "        __test__ = False\n" if suppressed else ""
        source = (
            "class TestBehavior:\n"
            "    class Helper:\n"
            f"{marker}"
            "        def __init__(self):\n            self.value = 7\n"
            "    def test_owner(self):\n        assert self.Helper().value == 7\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        if not suppressed:
            with (
                infra.rope_workspace(root) as rope,
                pytest.raises(ValueError, match="newly collect helper"),
            ):
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources={module: source},
                )
            tm.that(module.read_text(), eq=source)
            return
        updated, residue = self._plan(root, {module: source})
        tm.ok(u.Cli.atomic_write_text_file(module, updated[module]))
        probe = (
            "import os, contextlib, io\n"
            "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'\n"
            "import pytest\n"
            "stream = io.StringIO()\n"
            "with contextlib.redirect_stdout(stream):\n"
            "    result = pytest.main(\n"
            "        [\n"
            "            'tests',\n"
            "            '--tb=short',\n"
            "            '-p',\n"
            "            'no:cacheprovider',\n"
            "            '-W',\n"
            "            'error',\n"
            "        ],\n"
            "    )\n"
            "assert result == 0, stream.getvalue()\n"
            "print('1 passed' in stream.getvalue())\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root), eq=["True"]
        )
        tm.that(residue, eq={})

    @pytest.mark.parametrize("directory", ["", "scripts", "examples", "tests", "src"])
    @pytest.mark.parametrize("stem", ["worker", "__main__"])
    def test_ordinary_entry_points_keep_runtime_behavior(
        self,
        tmp_path: Path,
        directory: str,
        stem: str,
    ) -> None:
        """Executable roots preserve behavior; tests reject module execution guards."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="sample-engine",
            package_name="sample_engine",
        )
        parent = package if directory == "src" else root / directory
        tm.ok(u.Cli.ensure_dir(parent))
        module = parent / f"{stem}.py"
        source = (
            "LIMIT = 3\n\n"
            "def helper(value: int) -> int:\n    return value + LIMIT\n\n"
            "async def async_helper(value: int) -> int:\n    return helper(value)\n\n"
            "def main() -> None:\n    print(helper(4))\n\n"
            'if __name__ == "__main__":\n    main()\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        probe = (
            "import asyncio, runpy\n"
            f"namespace = runpy.run_path({str(module)!r})\n"
            f"runpy.run_path({str(module)!r}, run_name='__main__')\n"
        )
        before = u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root)

        if directory == "tests":
            with infra.rope_workspace(root) as rope:
                planned = u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                    rope_workspace=rope,
                    sources={module: source},
                )
            tm.fail(planned, has="unsupported module statements: If")
            tm.that(module.read_text(), eq=source)
            return
        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        owners = [
            node.name
            for node in ast.parse(nested).body
            if isinstance(node, ast.ClassDef)
        ]
        tm.that(len(owners), eq=1)
        owner = owners[0]
        tm.that(self._top_level(nested), eq=(owner, "__all__"))
        tm.that(nested, has="    @staticmethod\n    def main(")
        tm.that(nested, has=f"    {owner}.main()")
        tm.ok(u.Cli.atomic_write_text_file(module, nested))
        after = u.Tests.run_lazy_init_probe(
            probe + f"print(asyncio.run(namespace[{owner!r}].async_helper(4)))\n",
            python_paths=(),
            cwd=root,
        )
        tm.that(after, eq=[*before, *before])
        tm.that(residue, eq={})

    @pytest.mark.parametrize("extra_class", ["", "\nclass _Record:\n    pass\n"])
    def test_ordinary_unique_owner_is_not_wrapped(
        self,
        tmp_path: Path,
        extra_class: str,
    ) -> None:
        """One declared service absorbs helpers without an organizational wrapper."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "processor.py"
        source = (
            '"""Processing behavior."""\n\n'
            "def clean(value: str) -> str:\n    return value.strip()\n\n"
            "class Processor:\n"
            "    @staticmethod\n"
            "    def run(value: str) -> str:\n        return clean(value)\n"
        ) + extra_class
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        tm.that(self._top_level(nested), eq=("Processor", "__all__"))
        tm.that(nested, has="return Processor.clean(value)")
        tm.ok(u.Cli.atomic_write_text_file(module, nested))
        lines = u.Tests.run_lazy_init_probe(
            f"import runpy\nnamespace = runpy.run_path({str(module)!r})\n"
            "print(namespace['Processor'].run(' value '))\n",
            python_paths=(),
            cwd=root,
        )
        tm.that(lines, eq=["value"])
        tm.that(residue, eq={})

    def test_root_modules_keep_distinct_native_binding_identities(
        self,
        tmp_path: Path,
    ) -> None:
        """Same-named functions in independent root modules rewire independently."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        helper = "def compute(value: int) -> int:\n    return value + 1\n"
        consumer = (
            "from alpha import compute as left\n"
            "from beta import compute as right\n\n"
            "class Consumer:\n"
            "    @staticmethod\n"
            "    def run() -> int:\n        return left(1) + right(2)\n"
        )
        sources = {
            root / "alpha.py": helper,
            root / "beta.py": helper,
            root / "reader.py": consumer,
        }
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        probe = "import reader\nprint(reader.Consumer.run())\n"
        before = u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root)

        updated, residue = self._plan(root, sources)

        for path, source in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        after = u.Tests.run_lazy_init_probe(probe, python_paths=(), cwd=root)
        tm.that(after, eq=before)
        tm.that(residue, eq={})

    @pytest.mark.parametrize("wildcard", [False, True])
    def test_native_alias_identity_survives_shadowing_and_same_leaf_modules(
        self,
        tmp_path: Path,
        *,
        wildcard: bool,
    ) -> None:
        """Cold imports preserve lexical shadows, wildcard identities and payloads."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        source_root = root / c.Infra.DEFAULT_SRC_DIR
        sources: MutableMapping[Path, str] = {}
        for package, owner, value in (("left", "Left", 11), ("right", "Right", 29)):
            directory = source_root / package
            tm.ok(u.Cli.ensure_dir(directory))
            tm.ok(u.Cli.atomic_write_text_file(directory / "__init__.py", ""))
            sources[directory / "shared.py"] = (
                f"class {owner}:\n    pass\n\n"
                "type Token = int\n\n"
                f"def compute() -> int:\n    return {value}\n"
            )
        sources[source_root / "left" / "exports.py"] = (
            "from .shared import Left, compute as operation, Token as PublicToken\n"
            "__all__ = ['Left', 'operation', 'PublicToken']\n"
        )
        sources[source_root / "left" / "__init__.py"] = (
            "from .exports import Left, operation, PublicToken\n"
            "__all__ = ['Left', 'operation', 'PublicToken']\n"
        )
        selected = "compute" if wildcard else "thing.compute"
        importing = (
            "from left.shared import *\n"
            if wildcard
            else "import left.shared as thing\n"
        )
        consumer = source_root / "reader.py"
        sources[consumer] = (
            "from typing import Annotated, Literal\n"
            + importing
            + "from left.shared import Token as ImportedToken\n"
            + "from left import operation as public_compute, PublicToken\n"
            + "import right.shared as other\n\n"
            "class Consumer:\n"
            "    class Local:\n"
            "        @staticmethod\n"
            "        def compute() -> int:\n            return 7\n\n"
            "    @staticmethod\n"
            "    def parameter(thing) -> int:\n        return thing.compute()\n\n"
            "    @staticmethod\n"
            "    def local() -> int:\n"
            "        thing = Consumer.Local\n        return thing.compute()\n\n"
            "    @staticmethod\n"
            "    def left_scoped() -> int:\n"
            "        import left.shared as thing\n        return thing.compute()\n\n"
            "    @staticmethod\n"
            "    def right_scoped() -> int:\n"
            "        import right.shared as thing\n        return thing.compute()\n\n"
            "    @staticmethod\n"
            "    def run() -> Annotated[int, 'thing.compute']:\n"
            f"        return {selected}() + other.compute()\n\n"
            "    @staticmethod\n"
            "    def literal() -> Literal['thing.compute']:\n"
            "        return 'thing.compute'\n\n"
            "    @staticmethod\n"
            "    def echo(value: ('Imported' 'Token')) -> '''\nImportedToken\n''':\n"
            "        return value\n\n"
            "    @staticmethod\n"
            "    def public_echo(value: 'list[PublicToken]') -> 'list[PublicToken]':\n"
            "        return value\n\n"
            "    @staticmethod\n"
            "    def public_run() -> int:\n        return public_compute()\n"
        )
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        probe = (
            "from reader import Consumer\n"
            "from typing import get_args, get_type_hints\n"
            "assert Consumer.parameter(Consumer.Local) == Consumer.local() == 7\n"
            "assert (\n"
            "    Consumer.left_scoped()\n"
            "    + Consumer.right_scoped()\n"
            ") == Consumer.run()\n"
            "assert get_args(\n"
            "    get_type_hints(Consumer.run, include_extras=True)['return']\n"
            ")"
            " == (int, 'thing.compute')\n"
            "assert get_args(get_type_hints(Consumer.literal)['return'])"
            " == ('thing.compute',)\n"
            "assert Consumer.literal() == 'thing.compute'\n"
            "hints = get_type_hints(Consumer.echo)\n"
            "assert hints['value'] is hints['return']\n"
            "assert Consumer.echo(1) == 1\n"
            "assert get_type_hints(\n"
            "    Consumer.public_echo\n"
            ")['value'] == list[hints['value']]\n"
            "assert Consumer.public_run() == Consumer.left_scoped()\n"
            "print(Consumer.run())\n"
        )
        paths = (str(source_root),)
        before = u.Tests.run_lazy_init_probe(probe, python_paths=paths, cwd=root)
        updated, residue = self._plan(root, sources)
        for path, source in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        tm.that(
            u.Tests.run_lazy_init_probe(probe, python_paths=paths, cwd=root), eq=before
        )
        tm.that(residue, eq={})

    @pytest.mark.parametrize(
        ("consumer_source", "error"),
        [
            (
                (
                    "import behavior as thing\n"
                    "class Consumer:\n"
                    "    @staticmethod\n"
                    "    def run(flag):\n"
                    "        import behavior as thing\n"
                    "        if flag:\n            thing = None\n"
                    "        return thing.compute()\n"
                ),
                "native nesting alias",
            ),
            (
                (
                    "import behavior as thing\nfrom behavior import compute\n"
                    "class Consumer:\n"
                    "    @staticmethod\n"
                    "    def run(_DESTINATION_):\n        return compute()\n"
                ),
                "shadowed quoted type destination",
            ),
            (
                (
                    "from public import compute\n"
                    "class Consumer:\n"
                    "    @staticmethod\n"
                    "    def run():\n        return compute()\n"
                ),
                "no native public owner exposure",
            ),
        ],
    )
    @staticmethod
    def test_native_nesting_rejects_unproven_binding_or_exposure(
        tmp_path: Path,
        consumer_source: str,
        error: str,
    ) -> None:
        """Rejected original graphs remain untouched, never partially rewired."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = package / "_behavior.py"
        public = package / "public.py"
        consumer = package / "reader.py"
        # Use the package's actual module identity for every import in the graph.
        namespace = package.name
        sources = {
            provider: "class Owner:\n    pass\n\ndef compute():\n    return 1\n",
            public: (
                f"from {namespace}._behavior import compute\n__all__ = ['compute']\n"
            ),
            consumer: consumer_source
            .replace("from behavior", f"from {namespace}._behavior")
            .replace("import behavior as", f"import {namespace}._behavior as")
            .replace("from public", f"from {namespace}.public"),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        if "_DESTINATION_" in sources[consumer]:
            with infra.rope_workspace(root) as rope:
                resource = rope.resource(consumer)
                tm.that(resource, none=False)
                _, binding = u.Infra.import_binding(
                    rope.rope_project,
                    u.Infra.resolve_pymodule(
                        rope.rope_project,
                        u.Infra.require_file_resource(resource, consumer),
                    ),
                    rope.convention(provider).module_name,
                    "Owner",
                )
            primary = ast.parse(binding, mode="eval").body
            while isinstance(primary, ast.Attribute):
                primary = primary.value
            sources[consumer] = sources[consumer].replace(
                "_DESTINATION_", tm.instance(primary, ast.Name).id
            )
            tm.ok(u.Cli.atomic_write_text_file(consumer, sources[consumer]))
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(planned, has=error)
        for path, source in sources.items():
            tm.that(path.read_text(), eq=source)

    def test_initializer_remains_the_only_module_exemption(
        self,
        tmp_path: Path,
    ) -> None:
        """Package initialization is not rewritten as an ordinary namespace."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "__init__.py"
        source = '"""Initialization."""\ndef main() -> int:\n    return 1\n'
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        tm.that(updated[module.resolve()], eq=source)
        tm.that(residue, eq={})
