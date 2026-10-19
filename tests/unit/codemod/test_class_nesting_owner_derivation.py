"""Class nesting derives one owner for a module of loose members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import flext_core
import pytest

from flext_infra import infra
from tests import c, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraClassNestingOwnerDerivation:
    """Modules elect one owner and their consumers follow the moved identities."""

    LOOSE_MODULE = '''"""Loose helpers of one family module."""

from __future__ import annotations

import os

# Owner-only permission bits.
_MODE = 0o600
LIMIT: int = 3


class _Marker:
    """Marker for callers without a precondition."""


_SENTINEL = _Marker()


def write(path: str, marker: _Marker = _SENTINEL) -> int:
    """Return a size derived from ``path`` for an unmarked call."""
    if isinstance(marker, _Marker):
        return _helper(path) + _MODE
    return LIMIT


def _helper(path: str) -> int:
    return len(os.fspath(path))


__all__: list[str] = ["LIMIT", "write"]
'''

    @staticmethod
    def _family_module(tmp_path: Path, stem: str, source: str) -> t.Pair[Path, Path]:
        """Write one module into the utilities family package of a workspace.

        Returns:
            The repository root and the written module path.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        tm.ok(u.Cli.ensure_dir(family))
        tm.ok(u.Cli.atomic_write_text_file(family / "__init__.py", ""))
        module = family / f"{stem}.py"
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        return root, module

    @staticmethod
    def _derived_owner(root: Path, stem: str) -> str:
        """Return the owner the project class stem and family suffix derive.

        Returns:
            The derived owner class name.

        """
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        return (
            f"{u.derive_class_stem(root.name)}{family.suffix}"
            f"{u.derive_class_stem(stem)}"
        )

    @staticmethod
    def _plan(
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[t.MappingKV[Path, str], t.MappingKV[Path, str] | str]:
        """Plan class nesting, then replan the planned sources.

        Returns:
            The planned sources and the replanned residue (or its failure).

        """
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            updated = dict(sources)
            updated.update(
                (edit.file_path, edit.updated_source) for edit in planned.value
            )
            replanned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources=updated,
            )
        residue = (
            replanned.error or ""
            if replanned.failure
            else {edit.file_path: edit.updated_source for edit in replanned.value}
        )
        return updated, residue

    @staticmethod
    def _top_level(source: str) -> t.VariadicTuple[str]:
        """Return the names a module binds at top level, imports excluded.

        Returns:
            The class, function and assignment names in source order.

        """
        names: list[str] = []
        for node in ast.parse(source).body:
            if isinstance(node, ast.ClassDef | ast.FunctionDef):
                names.append(node.name)
            elif isinstance(node, ast.Assign | ast.AnnAssign):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                names.extend(
                    target.id for target in targets if isinstance(target, ast.Name)
                )
        return tuple(names)

    def test_zero_class_module_nests_under_the_derived_owner(
        self,
        tmp_path: Path,
    ) -> None:
        """Functions, constants and helper classes move under one owner."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")

        updated, residue = self._plan(root, {module: self.LOOSE_MODULE})

        source = updated[module.resolve()]
        tm.that(self._top_level(source), eq=(owner, "__all__"))
        tm.that(
            source,
            has=f'class {owner}:\n    """Loose helpers of one family module."""',
        )
        tm.that(source, has=f'__all__: list[str] = ["{owner}"]')
        tm.that(source, has="    @staticmethod\n    def write(")
        tm.that(source, has="    @staticmethod\n    def _helper(")
        tm.that(source, has="    class _Marker:")
        tm.that(source, has=f"return {owner}._helper(path) + {owner}._MODE")
        tm.that(source, has="    # Owner-only permission bits.")
        tm.that(residue, eq={})

    def test_module_constants_become_class_variables(self, tmp_path: Path) -> None:
        """A literal or annotated constant is a ``ClassVar`` of its owner."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)

        updated, _ = self._plan(root, {module: self.LOOSE_MODULE})

        source = updated[module.resolve()]
        tm.that(source, has="from typing import ClassVar")
        tm.that(source, has="    _MODE: ClassVar[int] = 0o600")
        tm.that(source, has="    LIMIT: ClassVar[int] = 3")
        tm.that(source, has="    _SENTINEL = _Marker()")
        compile(source, str(module), "exec")

    def test_private_classes_nest_under_the_derived_owner(
        self,
        tmp_path: Path,
    ) -> None:
        """Several private classes and no owner gain the derived owner."""
        source = (
            '"""Two private helpers."""\n\n'
            "from __future__ import annotations\n\n\n"
            "class _First:\n    pass\n\n\n"
            "class _Second(_First):\n    pass\n"
        )
        root, module = self._family_module(tmp_path, "pair_helpers", source)
        owner = self._derived_owner(root, "pair_helpers")

        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        tm.that(self._top_level(nested), eq=(owner, "__all__"))
        tm.that(nested, has="    class _First:")
        tm.that(nested, has="    class _Second(_First):")
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
        tm.that(all(node.name.startswith(prefix) for node in classes), eq=True)
        root_owner = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        exports = next(
            node
            for node in root_owner.body
            if isinstance(node, ast.Assign | ast.AnnAssign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        )
        tm.that(ast.literal_eval(exports.value), eq=[root_owner.name])
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
        "statement", ["VALUE = 1", "def helper():\n        return 1"]
    )
    def test_strict_type_checking_guard_has_no_declaration_exemption(
        self,
        tmp_path: Path,
        statement: str,
    ) -> None:
        """Only imports are authorized inside the module-level typing guard."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = root / "tests"
        tm.ok(u.Cli.ensure_dir(directory))
        module = directory / "test_guard.py"
        source = (
            "from typing import TYPE_CHECKING\n"
            f"if TYPE_CHECKING:\n    {statement}\n"
            "class Guard:\n    value = 1\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )
        tm.fail(result, has="unsupported module statements: If")
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
                isinstance(node, ast.Import | ast.ImportFrom | ast.ClassDef)
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

    def test_ordinary_competing_owners_fail_before_edits(self, tmp_path: Path) -> None:
        """Unresolved public class ownership is causal, not an empty success."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "processor.py"
        source = (
            '"""Competing owners."""\nclass First:\n    pass\nclass Second:\n    pass\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )

        tm.fail(planned, has="requires exactly one declared module owner")
        tm.that(module.read_text(), eq=source)

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
        sources: t.MutableMappingKV[Path, str] = {}
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
    def test_native_nesting_rejects_unproven_binding_or_exposure(
        self,
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
                assert resource is not None
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
            assert isinstance(primary, ast.Name)
            sources[consumer] = sources[consumer].replace("_DESTINATION_", primary.id)
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

    @pytest.mark.parametrize("module_kind", ["ordinary", "utilities", "typings"])
    def test_pep695_aliases_preserve_lazy_values_and_generic_scope(
        self,
        tmp_path: Path,
        module_kind: str,
    ) -> None:
        """Cold consumers resolve recursive aliases and unshadowed type parameters."""
        source = (
            '"""Recursive and generic payloads."""\n'
            "from __future__ import annotations\n\n"
            "from collections.abc import Callable\n\n"
            "type Leaf = str | int\n"
            "type Payload = Leaf | list[Payload] | dict[str, Payload]\n"
            "type Item = int\n"
            "type Box[Item] = tuple[Item, Payload]\n"
            "type Items[*Item] = tuple[*Item]\n"
            "type Callback[**Item] = Callable[Item, Payload]\n"
            'type Quoted[Item] = tuple["Item", Payload]\n'
            "type Defaults[T: Leaf = str] = tuple[T, Leaf]\n"
            "type Forward = list[Later]\n"
            "type Later = tuple[Forward]\n\n"
            "class _Record:\n    type Field = Payload\n"
            "\ndef echo(value: Payload) -> Payload:\n    return value\n"
        )
        if module_kind == "utilities":
            root, module = self._family_module(tmp_path, "payload", source)
        else:
            root, package = u.Tests.create_lazy_init_workspace(tmp_path)
            module = package / (
                c.Infra.TYPINGS_PY if module_kind == "typings" else "payload.py"
            )
        tm.ok(u.Cli.atomic_write_text_file(module, source))
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer = module.parent / "consumer.py"
        consumer_source = (
            '"""Alias consumer."""\n'
            "from __future__ import annotations\n"
            "from typing import get_args, get_type_hints\n"
            f"from {imported} import (\n"
            "    Payload as Data, Leaf, Item, Box, Items, Callback, Quoted, Defaults,\n"
            "    Forward, Later, _Record, echo,\n)\n\n"
            "class Consumer:\n"
            "    @staticmethod\n"
            "    def run(value: Data) -> Data:\n        return value\n\n"
            "    @staticmethod\n"
            "    def inspect() -> tuple[bool, ...]:\n"
            "        return (\n"
            "            get_args(Data.__value__)[0] is Leaf,\n"
            "            get_args(get_args(Data.__value__)[1])[0] is Data,\n"
            "            Item.__value__ is int,\n"
            "            get_args(Box.__value__)[0] is Box.__type_params__[0],\n"
            "            get_args(Box.__value__)[1] is Data,\n"
            "            get_args(get_args(Items.__value__)[0])[0]\n"
            "            is Items.__type_params__[0],\n"
            "            get_args(Callback.__value__)[0]\n"
            "            is Callback.__type_params__[0],\n"
            '            get_args(Quoted.__value__)[0] == "Item",\n'
            "            Defaults.__type_params__[0].__bound__ is Leaf,\n"
            "            Defaults.__type_params__[0].__default__ is str,\n"
            "            get_args(Forward.__value__)[0] is Later,\n"
            "            get_args(Later.__value__)[0] is Forward,\n"
            "            _Record.Field.__value__ is Data,\n"
            "            get_type_hints(Consumer.run)['return'] is Data,\n"
            "            get_type_hints(echo)['return'] is Data,\n"
            "            echo('value') == 'value',\n"
            "        )\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))
        probe = (
            f"from {imported.rpartition('.')[0]}.consumer import Consumer\n"
            "print(all(Consumer.inspect()))\n"
            "print(Consumer.run({'items': ['value', 1]}))\n"
        )
        paths = (str(root / c.Infra.DEFAULT_SRC_DIR),)
        before = u.Tests.run_lazy_init_probe(probe, python_paths=paths, cwd=root)

        updated, residue = self._plan(
            root,
            {module: source, consumer: consumer_source},
        )

        tm.that(
            any(
                isinstance(node, ast.TypeAlias)
                for node in ast.parse(updated[module]).body
            ),
            eq=False,
        )
        for path, nested in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, nested))
        after = u.Tests.run_lazy_init_probe(probe, python_paths=paths, cwd=root)
        tm.that(before[0], eq="True")
        tm.that(after, eq=before)
        tm.that(residue, eq={})

    @pytest.mark.parametrize(
        ("stem", "declaration"),
        [
            ("conftest", "def configure() -> None:\n    pass\n"),
            ("plugin", "def pytest_configure(config) -> None:\n    pass\n"),
            ("test_behavior", "def test_behavior() -> None:\n    pass\n"),
            ("fixtures", "@pytest.fixture\ndef resource() -> int:\n    return 1\n"),
        ],
    )
    def test_framework_registration_requires_a_coordinated_cutover(
        self,
        tmp_path: Path,
        stem: str,
        declaration: str,
    ) -> None:
        """Implicit module discovery must not silently lose hooks or fixtures."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / f"{stem}.py"
        source = '"""Framework registration."""\nimport pytest\n\n' + declaration
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        if stem == "conftest":
            updated, residue = self._plan(root, {module: source})
            tree = ast.parse(updated[module])
            tm.that(
                all(
                    isinstance(node, ast.Import | ast.ImportFrom | ast.ClassDef)
                    for node in tree.body
                ),
                eq=True,
            )
            tm.that(
                len([node for node in tree.body if isinstance(node, ast.ClassDef)]),
                eq=1,
            )
            tm.that(updated[module], has="@staticmethod\n    def configure(")
            tm.that(residue, eq={})
            return

        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )

        tm.fail(planned, has="framework registration contract must move")
        tm.that(module.read_text(), eq=source)

    def test_ordinary_suite_dependencies_fail_before_partial_nesting(
        self,
        tmp_path: Path,
    ) -> None:
        """An owner's nested suite cannot evaluate a moved sibling too early."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = package / "processor.py"
        source = (
            '"""Immediate suite dependencies."""\n'
            "class Processor:\n    pass\n\n"
            "class _Payload:\n    pass\n\n"
            "class _Holder:\n    payload = _Payload\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )

        tm.fail(planned, has="definition-time dependencies pin")
        tm.that(module.read_text(), eq=source)

    def test_module_alias_consumers_read_the_owner(self, tmp_path: Path) -> None:
        """Module-alias and member imports are rewired to the owner."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")
        package = module.parent
        consumer_owner = self._derived_owner(root, "consumer_thing")
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer_source = (
            '"""Consumer of the loose module."""\n\n'
            "from __future__ import annotations\n\n"
            f"from {imported.rsplit('.', 1)[0]} import atomic_thing as thing\n"
            f"from {imported} import write\n\n\n"
            f"class {consumer_owner}:\n"
            '    """Consumer owner."""\n\n'
            "    @staticmethod\n"
            "    def run() -> int:\n"
            '        return thing.write("x") + write("y") + thing.LIMIT\n\n\n'
            f'__all__: list[str] = ["{consumer_owner}"]\n'
        )
        consumer = package / "consumer_thing.py"
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))

        updated, residue = self._plan(
            root,
            {module: self.LOOSE_MODULE, consumer: consumer_source},
        )

        rewired = updated[consumer.resolve()]
        tm.that(rewired, has=f"from {imported} import {owner}")
        tm.that(rewired, has="import atomic_thing as thing")
        tm.that(rewired, lacks="import write")
        tm.that(
            rewired,
            has=f'thing.{owner}.write("x")',
        )
        tm.that(residue, eq={})

    def test_private_class_cross_module_reference_follows_plain_import(
        self,
        tmp_path: Path,
    ) -> None:
        """A dotted private-class reference through a plain module import rewires."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")
        package = module.parent
        consumer_owner = self._derived_owner(root, "marker_client")
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer_source = (
            '"""Marker client."""\n\n'
            "from __future__ import annotations\n\n"
            f"from {imported.rsplit('.', 1)[0]} import atomic_thing\n\n\n"
            f"class {consumer_owner}:\n"
            '    """Consumer owner."""\n\n'
            "    @staticmethod\n"
            "    def marked(marker: atomic_thing._Marker) -> bool:\n"
            "        return isinstance(marker, atomic_thing._Marker)\n\n\n"
            f'__all__: list[str] = ["{consumer_owner}"]\n'
        )
        consumer = package / "marker_client.py"
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))
        paths = (str(root / c.Infra.DEFAULT_SRC_DIR),)
        before = u.Tests.run_lazy_init_probe(
            f"import {imported} as atomic_thing\n"
            f"from {imported.rpartition('.')[0]}.marker_client import (\n"
            f"    {consumer_owner}\n"
            f")\n"
            f"print({consumer_owner}.marked(atomic_thing._Marker()))\n",
            python_paths=paths,
            cwd=root,
        )

        updated, residue = self._plan(
            root,
            {module: self.LOOSE_MODULE, consumer: consumer_source},
        )

        rewired = updated[consumer.resolve()]
        tm.that(rewired, has=f"{owner}._Marker")
        tm.that(rewired, lacks="atomic_thing._Marker")
        for path, source in updated.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        after = u.Tests.run_lazy_init_probe(
            f"import {imported} as atomic_thing\n"
            f"from {imported.rpartition('.')[0]}.marker_client import (\n"
            f"    {consumer_owner}\n"
            f")\n"
            f"print({consumer_owner}.marked(atomic_thing.{owner}._Marker()))\n",
            python_paths=paths,
            cwd=root,
        )
        tm.that(before, eq=["True"])
        tm.that(after, eq=before)
        tm.that(residue, eq={})

    def test_module_constant_from_import_survives_nesting(
        self,
        tmp_path: Path,
    ) -> None:
        """A consumer from-import of a call-free constant follows its owner."""
        root, module = self._family_module(tmp_path, "atomic_thing", self.LOOSE_MODULE)
        owner = self._derived_owner(root, "atomic_thing")
        package = module.parent
        consumer_owner = self._derived_owner(root, "limit_client")
        imported = ".".join(
            module.relative_to(root / c.Infra.DEFAULT_SRC_DIR).with_suffix("").parts,
        )
        consumer_source = (
            '"""Limit client."""\n\n'
            "from __future__ import annotations\n\n"
            f"from {imported} import LIMIT\n\n\n"
            f"class {consumer_owner}:\n"
            '    """Consumer owner."""\n\n'
            "    @staticmethod\n"
            "    def bounded(value: int) -> int:\n"
            "        return min(value, LIMIT)\n\n\n"
            f'__all__: list[str] = ["{consumer_owner}"]\n'
        )
        consumer = package / "limit_client.py"
        tm.ok(u.Cli.atomic_write_text_file(consumer, consumer_source))

        updated, residue = self._plan(
            root,
            {module: self.LOOSE_MODULE, consumer: consumer_source},
        )

        rewired = updated[consumer.resolve()]
        tm.that(rewired, has=f"from {imported} import {owner}")
        tm.that(rewired, has=f"return min(value, {owner}.LIMIT)")
        tm.that(rewired, lacks="import LIMIT")
        tm.that(residue, eq={})

    def test_published_record_class_is_a_member(self, tmp_path: Path) -> None:
        """A published record class that is no family owner is a member."""
        root, module = self._family_module(tmp_path, "mode_helpers", "")
        owner = self._derived_owner(root, "mode_helpers")
        helper = f"{u.derive_class_stem(root.name)}NoPrecondition"
        source = (
            '"""Sentinel and helper."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"class {helper}:\n    pass\n\n\n"
            f"NO_PRECONDITION = {helper}()\n\n\n"
            "def check(value: int) -> int:\n    return value\n\n\n"
            f'__all__: list[str] = ["{helper}", "NO_PRECONDITION", "check"]\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        tm.that(self._top_level(nested), eq=(owner, "__all__"))
        tm.that(nested, has=f"    class {helper}:")
        tm.that(residue, eq={})

    def test_family_suffix_excludes_the_shared_core_stem(self) -> None:
        """Every family suffix follows one shared, non-empty core class stem.

        A suffix spanning the whole core facade name doubles the stem in every
        derived owner (``<Project>FlextUtilities<Module>``).
        """
        stems = {
            getattr(flext_core, letter).__name__.removesuffix(family.suffix)
            for letter, family in u.Infra.facade_families().items()
        }
        tm.that(len(stems), eq=1)
        tm.that(stems.pop(), ne="")

    def test_declared_owner_absorbs_loose_functions(self, tmp_path: Path) -> None:
        """Loose helpers beside the declared owner nest into it, no new owner."""
        root, module = self._family_module(tmp_path, "step_helpers", "")
        owner = self._derived_owner(root, "step_helpers")
        source = (
            '"""Declared owner and loose helpers."""\n\n'
            "from __future__ import annotations\n\n\n"
            "def _strip(value: str) -> str:\n    return value.strip()\n\n\n"
            f"class {owner}:\n"
            '    """Step helpers."""\n\n'
            "    @staticmethod\n"
            "    def clean(value: str) -> str:\n"
            '        """Return the stripped value."""\n'
            "        return _strip(value)\n\n\n"
            f'__all__: list[str] = ["{owner}"]\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        tm.that(self._top_level(nested), eq=(owner, "__all__"))
        tm.that(nested, has="    @staticmethod\n    def _strip(")
        tm.that(nested, lacks="Canonical namespace owner")
        tm.that(residue, eq={})
        compile(nested, str(module), "exec")

    def test_rival_stem_classes_fail_naming_the_module(self, tmp_path: Path) -> None:
        """Two classes carrying the project stem leave the owner undecidable."""
        root, module = self._family_module(tmp_path, "rival_owners", "")
        owner = self._derived_owner(root, "rival_owners")
        source = (
            '"""Two candidate owners."""\n\n'
            "from __future__ import annotations\n\n\n"
            f"class {owner}Alpha:\n    pass\n\n\n"
            f"class {owner}Beta:\n    pass\n\n\n"
            f'__all__: list[str] = ["{owner}Alpha", "{owner}Beta"]\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={module: source},
            )

        tm.fail(planned, has="requires exactly one declared module owner")
        tm.fail(planned, has="rival_owners")

    def test_owner_creation_reads_stay_module_level(self, tmp_path: Path) -> None:
        """A metaclass factory, its builder and their sentinel never nest."""
        root, module = self._family_module(tmp_path, "lazy_helpers", "")
        owner = self._derived_owner(root, "lazy_helpers")
        source = (
            '"""Lazy assembly of one family facade."""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n\n"
            "_SENTINEL: type | None = None\n\n\n"
            "def _build_tree() -> type:\n"
            '    """Assemble the tree on first access."""\n'
            "    global _SENTINEL\n"
            "    if _SENTINEL is not None:\n"
            "        return _SENTINEL\n\n"
            "    class Tree:\n"
            '        """Assembled tree."""\n\n'
            "    _SENTINEL = Tree\n"
            "    return _SENTINEL\n\n\n"
            "def _lazy_meta() -> type:\n"
            '    """Build the lazy metaclass."""\n\n'
            "    class _Meta(type):\n"
            '        """Assemble the tree on first class-level access."""\n\n'
            "        def __getattr__(cls, name: str) -> Any:\n"
            '            if name == "Tree":\n'
            "                tree = _build_tree()\n"
            "                cls.Tree = tree\n"
            "                return tree\n"
            '            msg = f"no attribute {name!r}"\n'
            "            raise AttributeError(msg)\n\n"
            "    return _Meta\n\n\n"
            f"class {owner}(metaclass=_lazy_meta()):\n"
            '    """The facade owner."""\n\n'
            f'__all__: list[str] = ["{owner}"]\n'
        )
        tm.ok(u.Cli.atomic_write_text_file(module, source))

        updated, residue = self._plan(root, {module: source})

        kept = updated[module.resolve()]
        tm.that(
            self._top_level(kept),
            eq=(
                "_SENTINEL",
                "_build_tree",
                "_lazy_meta",
                owner,
                "__all__",
            ),
        )
        tm.that(kept, has="def _lazy_meta() -> type:")
        tm.that(kept, has="tree = _build_tree()")
        tm.that(residue, eq={})
        compile(kept, str(module), "exec")

    def test_nested_class_annotations_keep_a_resolvable_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Annotations inside a moved class name the owner, not a dropped bare name."""
        source = (
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
            "        return cls()\n"
        )
        root, module = self._family_module(tmp_path, "registry_helpers", source)
        owner = self._derived_owner(root, "registry_helpers")

        updated, residue = self._plan(root, {module: source})

        nested = updated[module.resolve()]
        qualified = f"{owner}._Registry"
        tm.that(nested, has=f"def current() -> {qualified}:")
        tm.that(nested, has=f"return {qualified}.current()")
        tm.that(nested, has=f"_current: ClassVar[{qualified} | None] = None")
        tm.that(nested, has=f"def start(cls) -> {qualified}:")
        tm.that(nested, has=f"def current(cls) -> {qualified}:")
        tm.that(residue, eq={})
        compile(nested, str(module), "exec")
