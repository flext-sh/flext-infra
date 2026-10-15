"""Public evidence for callback admission before native compiler operations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from sys import executable

import pytest

from tests import c, tm, u


class TestsNativeCompilerAdmission:
    """Observe native consumers and unchanged effects during provenance rejection."""

    @staticmethod
    @pytest.mark.parametrize(
        "defect", ["none", "origin", "argument", "unpacked", "subclass_state"]
    )
    def test_native_generic_alias_retains_public_operands_without_lazy_callbacks(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Typer's real type alias and authored subclass storage retain their state."""
        package = tmp_path / "native_generic_alias_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from typer.models import AnyType\n"
                "from types import GenericAlias\n"
                "effects = []\n"
                "class Argument:\n"
                "    @property\n"
                "    def __parameters__(self):\n"
                "        effects.append('parameters')\n"
                "        raise AssertionError('lazy authored parameters')\n"
                "class Alias(GenericAlias):\n"
                "    __slots__ = ('state',)\n"
                "    def __call__(self):\n"
                "        return object.__getattribute__(self, 'state')\n"
                "annotation = AnyType\n"
                "argument = Argument()\n"
                "callback_annotation = GenericAlias(list, (argument,))\n"
                "subclass_annotation = Alias(list, (argument,))\n"
                "subclass_annotation.state = 'before'\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from typing import Any, get_args, get_origin\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_generic_alias_consumer')\n"
            "assert get_origin(module.annotation) is type\n"
            "assert get_args(module.annotation) == (Any,)\n"
            "assert module.annotation('Created', (object,), {}).__name__ == 'Created'\n"
            "assert module.subclass_annotation() == 'before'\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "defect = sys.argv[2]\n"
            "if defect == 'origin':\n"
            "    module.annotation = module.GenericAlias(list, (Any,))\n"
            "elif defect == 'argument':\n"
            "    module.annotation = module.GenericAlias(type, (int,))\n"
            "elif defect == 'unpacked':\n"
            "    module.annotation = next(iter(module.annotation))\n"
            "elif defect == 'subclass_state':\n"
            "    module.subclass_annotation.state = 'after'\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "compared = native.compare(original, changed)\n"
            "assert compared.success == (defect == 'none'), compared\n"
            "admitted = provenance.loaded_import_sources(module.__name__)\n"
            "assert admitted.success == (defect == 'none'), admitted\n"
            "assert module.effects == []\n"
            "if defect == 'origin':\n"
            "    assert module.annotation((1, 2)) == [1, 2]\n"
            "elif defect == 'argument':\n"
            "    assert get_args(module.annotation) == (int,)\n"
            "elif defect == 'unpacked':\n"
            "    assert get_origin(module.annotation) is type\n"
            "    assert get_args(module.annotation) == (Any,)\n"
            "    assert str(module.annotation).startswith('*')\n"
            "elif defect == 'subclass_state':\n"
            "    assert module.subclass_annotation() == 'after'\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["state", "order", "code"])
    def test_native_slice_retains_operands_and_protocol_code_without_callbacks(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real slicing observes bound order, receiver state and index code."""
        package = tmp_path / "native_slice_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import operator\n"
                "effects = []\n"
                "class Index:\n"
                "    def __init__(self, value): self.value = value\n"
                "    def __index__(self):\n"
                "        effects.append('index')\n"
                "        return self.value\n"
                "    def __hash__(self):\n"
                "        effects.append('hash')\n"
                "        return self.value\n"
                "    def __repr__(self):\n"
                "        effects.append('repr')\n"
                "        return 'Index'\n"
                "def changed_index(self):\n"
                "    effects.append('changed_index')\n"
                "    return 2\n"
                "index = Index(1)\n"
                "operation = operator.itemgetter(slice(index, None, None))\n",
            ),
        )
        consumer = (
            "import importlib, operator, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_slice_consumer')\n"
            "data = ('zero', 'one', 'two')\n"
            "assert module.operation(data) == ('one', 'two')\n"
            "before = tuple(module.effects)\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "defect = sys.argv[2]\n"
            "if defect == 'state':\n"
            "    module.index.value = 2\n"
            "elif defect == 'order':\n"
            "    module.operation = operator.itemgetter(slice(None, module.index, None))\n"
            "else:\n"
            "    module.Index.__index__.__code__ = module.changed_index.__code__\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
            "assert module.operation(data) == (('zero',) if defect == 'order' else ('two',))\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    def test_native_inherited_slot_preserves_unset_without_attribute_callbacks(
        tmp_path: Path,
    ) -> None:
        """Unset and None differ while authored attribute hooks remain untouched."""
        package = tmp_path / "native_optional_slot_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import operator\n"
                "effects = []\n"
                "class Base:\n"
                "    __slots__ = ('state',)\n"
                "class Operand(Base):\n"
                "    __slots__ = ()\n"
                "    def __getattribute__(self, name):\n"
                "        if name == 'state':\n"
                "            effects.append('getattribute')\n"
                "            raise AssertionError('authored attribute accessor')\n"
                "        return object.__getattribute__(self, name)\n"
                "    def __getattr__(self, name):\n"
                "        effects.append('getattr')\n"
                "        raise AssertionError('authored attribute fallback')\n"
                "class Consumer:\n"
                "    def accept(self, value):\n"
                "        return object.__getattribute__(value, 'state')\n"
                "operand = Operand()\n"
                "operation = operator.methodcaller('accept', operand)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_optional_slot_consumer')\n"
            "try:\n"
            "    module.operation(module.Consumer())\n"
            "except AttributeError:\n"
            "    pass\n"
            "else:\n"
            "    raise AssertionError('unset slot unexpectedly had a value')\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "module.operand.state = None\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert module.effects == []\n"
            "assert module.operation(module.Consumer()) is None\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "globals", "exports"])
    def test_native_no_default_constant_rejects_an_impostor_without_callbacks(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """The real native typing constant has no arbitrary constructor recipe."""
        consumer = (
            "import _typing, sys, typing\n"
            "from typing_inspection import typing_objects as module\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "effects = []\n"
            "function = module.is_nodefault\n"
            "canonical = typing.NoDefault\n"
            "assert canonical is _typing.NoDefault\n"
            "assert function(canonical) is True\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "class Fake:\n"
            "    __slots__ = ()\n"
            "    def __new__(cls):\n"
            "        effects.append('constructor')\n"
            "        return object.__new__(cls)\n"
            "    def __reduce__(self):\n"
            "        effects.append('reducer')\n"
            "        return 'NoDefault'\n"
            "fake = object.__new__(Fake)\n"
            "Fake.__name__ = 'NoDefaultType'\n"
            "Fake.__module__ = 'builtins'\n"
            "defect = sys.argv[1]\n"
            "if defect == 'globals':\n"
            "    for name, stored in tuple(function.__globals__.items()):\n"
            "        if stored is canonical:\n"
            "            function.__globals__[name] = fake\n"
            "        elif type(stored) is tuple:\n"
            "            function.__globals__[name] = tuple("
            "fake if item is canonical else item for item in stored)\n"
            "elif defect == 'exports':\n"
            "    _typing.NoDefault = typing.NoDefault = fake\n"
            "if defect == 'none':\n"
            "    repeated = native.capture((module.__name__,)).unwrap()\n"
            "    assert native.compare(original, repeated).unwrap() is True\n"
            "    provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "elif defect == 'globals':\n"
            "    assert native.capture((module.__name__,)).failure\n"
            "    assert provenance.loaded_import_sources(module.__name__).failure\n"
            "    assert function(canonical) is False and function(fake) is True\n"
            "else:\n"
            "    try:\n"
            "        native.capture((module.__name__,))\n"
            "    except ValueError:\n"
            "        pass\n"
            "    else:\n"
            "        raise AssertionError('native constant exports accepted an impostor')\n"
            "    finally:\n"
            "        _typing.NoDefault = typing.NoDefault = canonical\n"
            "assert effects == []\n"
        )
        tm.ok(u.Cli.capture([executable, "-c", consumer, defect], cwd=tmp_path))

    @staticmethod
    def test_generated_predicate_distinguishes_a_clone_of_an_empty_singleton(
        tmp_path: Path,
    ) -> None:
        """The real NoExtraItems predicate retains its registered singleton."""
        consumer = (
            "import typing_extensions\n"
            "from typing_inspection import typing_objects as module\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "function = module.is_noextraitems\n"
            "canonical = typing_extensions.NoExtraItems\n"
            "assert function(canonical) is True\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "clone = object.__new__(type(canonical))\n"
            "assert clone is not canonical\n"
            "for name, stored in tuple(function.__globals__.items()):\n"
            "    if stored is canonical:\n"
            "        function.__globals__[name] = clone\n"
            "    elif type(stored) is tuple:\n"
            "        function.__globals__[name] = tuple("
            "clone if item is canonical else item for item in stored)\n"
            "assert typing_extensions.NoExtraItems is canonical\n"
            "assert native.capture((module.__name__,)).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert function(canonical) is False and function(clone) is True\n"
        )
        tm.ok(u.Cli.capture([executable, "-c", consumer], cwd=tmp_path))

    @staticmethod
    def test_native_constructor_retains_empty_python_slots_and_alias_identity(
        tmp_path: Path,
    ) -> None:
        """An empty receiver remains proved, and an unregistered clone differs."""
        package = tmp_path / "native_empty_slots_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import operator\n"
                "effects = []\n"
                "class Empty:\n"
                "    __slots__ = ()\n"
                "    def __init__(self): effects.append('construction')\n"
                "sentinel = Empty()\n"
                "del Empty\n"
                "class Receiver:\n"
                "    def accept(self, value): return value is sentinel\n"
                "operation = operator.methodcaller('accept', sentinel)\n",
            ),
        )
        consumer = (
            "import importlib, operator, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_empty_slots_consumer')\n"
            "assert module.operation(module.Receiver()) is True\n"
            "before = tuple(module.effects)\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "clone = object.__new__(type(module.sentinel))\n"
            "module.operation = operator.methodcaller('accept', clone)\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
            "assert module.operation(module.Receiver()) is False\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    def test_native_constructor_retains_authenticated_language_singletons(
        tmp_path: Path,
    ) -> None:
        """Constructor operands preserve singleton identity and native booleans."""
        package = tmp_path / "native_singleton_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import operator\n"
                "class Receiver:\n"
                "    def accept(self, *values): return values\n"
                "operation = operator.methodcaller("
                "'accept', NotImplemented, ..., None, True, False)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_singleton_consumer')\n"
            "values = module.operation(module.Receiver())\n"
            "assert values[0] is NotImplemented and values[1] is ...\n"
            "assert values[2] is None and values[3] is True and values[4] is False\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "provenance.loaded_import_sources(module.__name__).unwrap()\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    def test_native_extension_identity_retains_code_and_registered_exports(
        tmp_path: Path,
    ) -> None:
        """Renaming another real Cython callback never substitutes its executable."""
        package = tmp_path / "native_extension_identity_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import yaml._yaml\n"
                "operation = yaml._yaml.get_version\n",
            ),
        )
        consumer = (
            "import importlib, sys, yaml._yaml\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_extension_identity_consumer')\n"
            "assert type(module.operation()) is tuple\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "replacement = yaml._yaml.get_version_string\n"
            "replacement.__name__ = module.operation.__name__\n"
            "replacement.__qualname__ = module.operation.__qualname__\n"
            "module.operation = replacement\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert type(module.operation()) is str\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "code", "globals"])
    def test_generated_module_predicate_requires_its_physical_compiler(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real generated predicates reject changed executable or cached globals."""
        consumer = (
            "import sys, typing\n"
            "from typing_inspection import typing_objects as module\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "effects = []\n"
            "argument = typing.TypeVar('T')\n"
            "function = module.is_typevar\n"
            "assert function(argument) is True\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "def changed(obj):\n"
            "    obj.effect()\n"
            "    return False\n"
            "class Probe:\n"
            "    def effect(self): effects.append('predicate')\n"
            "class Meta(type):\n"
            "    def __instancecheck__(cls, obj):\n"
            "        effects.append('instancecheck')\n"
            "        return False\n"
            "class Other(metaclass=Meta): pass\n"
            "defect = sys.argv[1]\n"
            "if defect == 'code':\n"
            "    function.__code__ = changed.__code__\n"
            "elif defect == 'globals':\n"
            "    for name in function.__code__.co_names:\n"
            "        if name in function.__globals__:\n"
            "            function.__globals__[name] = Other\n"
            "if defect == 'none':\n"
            "    repeated = native.capture((module.__name__,)).unwrap()\n"
            "    assert native.compare(original, repeated).unwrap() is True\n"
            "    provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "else:\n"
            "    assert native.capture((module.__name__,)).failure\n"
            "    assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert effects == []\n"
            "if defect == 'code':\n"
            "    assert function(Probe()) is False\n"
            "elif defect == 'globals':\n"
            "    assert function(argument) is False\n"
            "if defect != 'none': assert len(effects) == 1\n"
        )
        tm.ok(u.Cli.capture([executable, "-c", consumer, defect], cwd=tmp_path))

    @staticmethod
    def test_native_constructor_never_hashes_an_authored_operand_type(
        tmp_path: Path,
    ) -> None:
        """A local protocol receiver retains evidence without metaclass callbacks."""
        package = tmp_path / "native_type_identity_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import operator\n"
                "effects = []\n"
                "def factory():\n"
                "    class Meta(type):\n"
                "        def __hash__(cls):\n"
                "            effects.append('hash')\n"
                "            return type.__hash__(cls)\n"
                "    class Operand(metaclass=Meta):\n"
                "        def __index__(self): return 0\n"
                "    return Operand()\n"
                "operation = operator.itemgetter(factory())\n"
                "del factory\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_type_identity_consumer')\n"
            "assert module.operation(('left', 'right')) == 'left'\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "assert module.effects == []\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["state", "code"])
    def test_native_constructor_retains_a_registered_protocol_receiver(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Registration never replaces receiver state or its executable protocol."""
        package = tmp_path / "native_index_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import operator\n"
                "effects = []\n"
                "class Key:\n"
                "    def __init__(self, index): self.index = index\n"
                "    def __index__(self): return self.index\n"
                "def changed_index(self):\n"
                "    effects.append('index')\n"
                "    return 1\n"
                "key = Key(0)\n"
                "operation = operator.itemgetter(key)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_index_consumer')\n"
            "assert module.operation(('left', 'right')) == 'left'\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "if sys.argv[2] == 'state':\n"
            "    module.key.index = 1\n"
            "else:\n"
            "    module.Key.__index__.__code__ = module.changed_index.__code__\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert module.effects == []\n"
            "assert module.operation(('left', 'right')) == 'right'\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("target", ["itemgetter", "partial"])
    def test_native_authority_rejects_non_text_metadata_without_equality(
        tmp_path: Path,
        target: str,
    ) -> None:
        """Poisoned constructor metadata never runs an authored equality method."""
        package = tmp_path / "native_metadata_identity_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "effects = []\n"
                "class Marker:\n"
                "    def __eq__(self, other):\n"
                "        effects.append('equality')\n"
                "        return False\n"
                "class itemgetter: pass\n"
                "class partial: pass\n",
            ),
        )
        consumer = (
            "import _functools, _operator, functools, importlib, operator, sys\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_metadata_identity_consumer')\n"
            "target = sys.argv[2]\n"
            "replacement = vars(module)[target]\n"
            "replacement.__module__ = module.Marker()\n"
            "facade, owner = ((operator, _operator) if target == 'itemgetter' "
            "else (functools, _functools))\n"
            "setattr(facade, target, replacement)\n"
            "setattr(owner, target, replacement)\n"
            "assert native.capture((module.__name__,)).failure\n"
            "assert module.effects == []\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), target],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["accessor", "format"])
    def test_native_rejection_diagnostics_never_format_authored_metadata(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """An unsupported receiver fails before metaclass access or formatting."""
        package = tmp_path / "native_diagnostic_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "effects = []\n"
                "class Meta(type):\n"
                "    def __getattribute__(cls, name):\n"
                "        if name == '__module__': effects.append('accessor')\n"
                "        return type.__getattribute__(cls, name)\n"
                "class Marker:\n"
                "    def __format__(self, spec):\n"
                "        effects.append('format')\n"
                "        return 'foreign'\n"
                "class Receiver(metaclass=Meta):\n"
                "    __call__ = object.__str__\n"
                "operation = Receiver()\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_diagnostic_consumer')\n"
            "if sys.argv[2] == 'format':\n"
            "    module.Receiver.__module__ = module.Marker()\n"
            "    try:\n"
            "        native.capture((module.__name__,))\n"
            "    except ValueError as error:\n"
            "        assert str(error).startswith("
            "'native lexical identity has non-text metadata: ')\n"
            "    else:\n"
            "        raise AssertionError('non-text diagnostic metadata was admitted')\n"
            "else:\n"
            "    assert native.capture((module.__name__,)).failure\n"
            "assert module.effects == []\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "code", "globals", "builtins"])
    def test_named_tuple_constructor_retains_its_compiler_globals(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A real NamedTuple preserves compiler code and anonymous operand bindings."""
        package = tmp_path / "native_named_tuple_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import typing\n"
                "effects = []\n"
                "_tuple_new = tuple.__new__\n"
                "class Record(typing.NamedTuple):\n"
                "    value: int\n"
                "    extra: int = 2\n"
                "def changed_new(cls, value, extra=2):\n"
                "    return _tuple_new(cls, (value + 1, extra))\n"
                "def changed_tuple(cls, values):\n"
                "    effects.append('tuple_new')\n"
                "    return tuple.__new__(cls, (values[0] + 1, *values[1:]))\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_named_tuple_consumer')\n"
            "assert module.Record(3) == (3, 2)\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "constructor = module.Record.__new__\n"
            "defect = sys.argv[2]\n"
            "if defect == 'code':\n"
            "    constructor.__code__ = module.changed_new.__code__\n"
            "elif defect == 'globals':\n"
            "    constructor.__globals__['_tuple_new'] = module.changed_tuple\n"
            "elif defect == 'builtins':\n"
            "    del constructor.__globals__['_tuple_new']\n"
            "    constructor.__builtins__['_tuple_new'] = module.changed_tuple\n"
            "if defect == 'none':\n"
            "    provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "else:\n"
            "    assert native.capture((module.__name__,)).failure\n"
            "    assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert module.effects == []\n"
            "assert module.Record(3) == ((3, 2) if defect == 'none' else (4, 2))\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), defect],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    def test_generated_function_requires_its_physical_class_owner(
        tmp_path: Path,
    ) -> None:
        """An arbitrary anonymous function never acquires compiler provenance."""
        package = tmp_path / "unowned_generated_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "def operation(): return 1\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('unowned_generated_consumer')\n"
            "module.operation = eval('lambda: 2', vars(module))\n"
            "assert module.operation() == 2\n"
            "try:\n"
            "    native.capture((module.__name__,))\n"
            "except ValueError as error:\n"
            "    assert str(error) == "
            "'generated function has no unique physical literal factory call'\n"
            "else:\n"
            "    raise AssertionError('unowned generated function was admitted')\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("value", [1, 2])
    def test_python_callable_with_hidden_native_base_state_is_rejected(
        tmp_path: Path,
        value: int,
    ) -> None:
        """An int-derived receiver never substitutes an empty Python dictionary."""
        package = tmp_path / "native_base_callable_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "class Receiver(int):\n"
                "    def __call__(self): return int(self)\n"
                f"operation = Receiver({value})\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_base_callable_consumer')\n"
            f"assert module.operation() == {value}\n"
            "observed = native.capture((module.__name__,))\n"
            "assert observed.failure, observed\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    def test_dataclass_metadata_preserves_its_native_proxy_backing(
        tmp_path: Path,
    ) -> None:
        """Real dataclass metadata changes remain visible through its native proxy."""
        package = tmp_path / "native_metadata_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass, field\n"
                "metadata = {'label': 'before'}\n"
                "@dataclass\n"
                "class Record:\n"
                "    value: int = field(default=1, metadata=metadata)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from dataclasses import fields\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_metadata_consumer')\n"
            "assert module.Record(3).value == 3\n"
            "assert fields(module.Record)[0].metadata['label'] == 'before'\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "module.metadata['label'] = 'after'\n"
            "assert fields(module.Record)[0].metadata['label'] == 'after'\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("base", ["object", "dict"])
    def test_native_proxy_rejects_authored_mapping_callbacks(
        tmp_path: Path,
        base: str,
    ) -> None:
        """Unknown proxy backing never invokes authored mapping methods."""
        package = tmp_path / "foreign_metadata_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass, field\n"
                "from types import MappingProxyType\n"
                "effects = []\n"
                "def forbidden(name):\n"
                "    effects.append(name)\n"
                "    raise AssertionError('authored mapping callback was invoked')\n"
                f"class Foreign({base}):\n"
                "    def __getitem__(self, key): return forbidden('getitem')\n"
                "    def __iter__(self): return forbidden('iter')\n"
                "    def __len__(self): return forbidden('len')\n"
                "    def items(self): return forbidden('items')\n"
                "    def copy(self): return forbidden('copy')\n"
                "metadata = Foreign()\n"
                "view = MappingProxyType(metadata)\n"
                "@dataclass\n"
                "class Record:\n"
                "    value: int = field(default=1, metadata=metadata)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from pytest import raises\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('foreign_metadata_consumer')\n"
            "assert module.effects == [], module.effects\n"
            "with raises(ValueError, match='requires one exact dict backing'):\n"
            "    native.capture((module.__name__,))\n"
            "assert module.effects == [], module.effects\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    def test_real_callable_annotation_remains_usable_after_capture(
        tmp_path: Path,
    ) -> None:
        """The real typing singleton retains its public annotation behavior."""
        package = tmp_path / "python_callable_alias_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from typing import Callable\n"
                "def annotation(): return Callable[[int], str]\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from typing import Callable\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('python_callable_alias_consumer')\n"
            "assert module.annotation() == Callable[[int], str]\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            "provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "assert module.annotation() == Callable[[int], str]\n"
            "module.Callable = Callable[..., int]\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("storage", ["dict", "slots"])
    @pytest.mark.parametrize("defect", ["none", "state", "implementation"])
    def test_python_callable_state_and_implementation_are_authenticated(
        tmp_path: Path,
        storage: str,
        defect: str,
    ) -> None:
        """Real receiver dictionaries and slots expose changed state or methods."""
        package = tmp_path / "python_callable_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        slots = "    __slots__ = ('offset',)\n" if storage == "slots" else ""
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "class Receiver:\n"
                + slots
                + "    def __init__(self, offset): self.offset = offset\n"
                "    def __call__(self, value): return self.offset + value\n"
                "    def alternate(self, value): return self.offset - value\n"
                "operation = Receiver(3)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('python_callable_consumer')\n"
            "assert module.operation(4) == 7\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            f"defect = {defect!r}\n"
            "if defect == 'state':\n"
            "    module.operation.offset = 11\n"
            "elif defect == 'implementation':\n"
            "    module.Receiver.__call__ = module.Receiver.alternate\n"
            "observed = native.capture((module.__name__,))\n"
            "if observed.success:\n"
            "    compared = native.compare(original, observed.value)\n"
            "    assert compared.success == (defect == 'none'), compared\n"
            "else:\n"
            "    assert defect != 'none', observed\n"
            "admitted = provenance.loaded_import_sources(module.__name__)\n"
            "assert admitted.success == (defect == 'none'), admitted\n"
            "expected = 7 if defect == 'none' else 15 if defect == 'state' else -1\n"
            "assert module.operation(4) == expected\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    def test_bound_native_constructor_callbacks_require_receiver_proof(
        tmp_path: Path,
    ) -> None:
        """Opaque bound receivers fail before their unequal state can collide."""
        package = tmp_path / "native_bound_receiver_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from operator import methodcaller\n"
                "class Receiver:\n"
                "    def observe(self, callback): return tuple(callback.__self__)\n"
                "left = [1]\n"
                "right = [2]\n"
                "operation = methodcaller('observe', left.append)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from pytest import raises\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_bound_receiver_consumer')\n"
            "assert module.operation(module.Receiver()) == (1,)\n"
            "with raises(ValueError, match='no admitted receiver state'):\n"
            "    native.capture((module.__name__,))\n"
            "module.operation = module.methodcaller('observe', module.right.append)\n"
            "assert module.operation(module.Receiver()) == (2,)\n"
            "with raises(ValueError, match='no admitted receiver state'):\n"
            "    native.capture((module.__name__,))\n"
        )
        tm.ok(
            u.Cli.capture([executable, "-c", consumer, str(tmp_path)], cwd=tmp_path),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "wrapper"])
    def test_native_class_targets_keep_their_public_wrapper_contract(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real subscription and static construction retain native class targets."""
        package = tmp_path / "native_class_alias_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from collections.abc import Iterable\n"
                "from types import GenericAlias\n"
                "class Factory:\n"
                "    create = staticmethod(GenericAlias)\n"
                "def iterable_annotation(): return Iterable[int]\n"
                "def list_annotation(): return Factory.create(list, int)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from typing import get_args, get_origin\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_class_alias_consumer')\n"
            "annotation = module.iterable_annotation()\n"
            "assert get_origin(annotation) is module.Iterable\n"
            "assert get_args(annotation) == (int,)\n"
            "assert module.list_annotation() == list[int]\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            f"defect = {defect!r}\n"
            "if defect == 'wrapper':\n"
            "    module.Factory.create = classmethod(module.GenericAlias)\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "compared = native.compare(original, changed)\n"
            "assert compared.success == (defect == 'none'), compared\n"
            "admitted = provenance.loaded_import_sources(module.__name__)\n"
            "assert admitted.success == (defect == 'none'), admitted\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize(
        ("factory", "replacement", "argument", "expected", "changed"),
        [
            (
                "methodcaller('lower')",
                "methodcaller('upper')",
                "'NaTiVe'",
                "'native'",
                "'NATIVE'",
            ),
            (
                "methodcaller('replace', 'a', 'b', 1)",
                "methodcaller('replace', 'a', 'c', 1)",
                "'aaa'",
                "'baa'",
                "'caa'",
            ),
            (
                "methodcaller('format', field='first')",
                "methodcaller('format', field='second')",
                "'{field}'",
                "'first'",
                "'second'",
            ),
            (
                "itemgetter(itemgetter)",
                "itemgetter(type)",
                "{operator.itemgetter: 'original', type: 'replacement'}",
                "'original'",
                "'replacement'",
            ),
            (
                "itemgetter((0, 1))",
                "itemgetter(0, 1)",
                "{(0, 1): 'tuple', 0: 'zero', 1: 'one'}",
                "'tuple'",
                "('zero', 'one')",
            ),
        ],
    )
    @pytest.mark.parametrize("defect", ["none", "state", "binding", "supplier"])
    def test_native_callable_arguments_and_bindings_are_authenticated(
        tmp_path: Path,
        factory: str,
        replacement: str,
        argument: str,
        expected: str,
        changed: str,
        defect: str,
    ) -> None:
        """Native constructor state retains arguments and rejects foreign bindings."""
        # Adapt the public regression without invoking authored callbacks.
        package = tmp_path / "native_callable_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from operator import itemgetter, methodcaller\n"
                f"operation = {factory}\n",
            ),
        )
        consumer = (
            "import importlib, operator, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_callable_consumer')\n"
            f"assert module.operation({argument}) == {expected}\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "repeated = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, repeated).unwrap() is True\n"
            f"defect = {defect!r}\n"
            "if defect == 'state':\n"
            f"    module.operation = module.{replacement}\n"
            f"    assert module.operation({argument}) == {changed}\n"
            "elif defect == 'binding':\n"
            "    module.operation = operator.attrgetter('real')\n"
            "elif defect == 'supplier':\n"
            "    setattr(operator, type(module.operation).__name__, operator.attrgetter)\n"
            "observed = native.capture((module.__name__,))\n"
            "if defect == 'supplier':\n"
            "    assert observed.failure, observed\n"
            "else:\n"
            "    compared = native.compare(original, observed.unwrap())\n"
            "    assert compared.success == (defect == 'none'), compared\n"
            "admitted = provenance.loaded_import_sources(module.__name__)\n"
            "assert admitted.success == (defect == 'none'), admitted\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    def test_native_callable_keyword_order_retains_consumer_behavior(
        tmp_path: Path,
    ) -> None:
        """Equal keyword mappings with different order have distinct native state."""
        package = tmp_path / "native_keyword_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from operator import methodcaller\n"
                "class Receiver:\n"
                "    def accept(self, **keywords): return tuple(keywords)\n"
                "operation = methodcaller('accept', first=1, second=2)\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_keyword_consumer')\n"
            "assert module.operation(module.Receiver()) == ('first', 'second')\n"
            "original = native.capture((module.__name__,)).unwrap()\n"
            "module.operation = module.methodcaller('accept', second=2, first=1)\n"
            "assert module.operation(module.Receiver()) == ('second', 'first')\n"
            "changed = native.capture((module.__name__,)).unwrap()\n"
            "assert native.compare(original, changed).failure\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("defect", ["partial", "importer", "reducer"])
    def test_native_reduction_rejects_authored_callbacks_before_invocation(
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Poisoned compiler boundaries leave the authored callback untouched."""
        package = tmp_path / "native_reducer_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from operator import methodcaller\n"
                "effects = []\n"
                "operation = methodcaller('format', field='native')\n"
                "def forbidden(*arguments, **keywords):\n"
                "    effects.append('invoked')\n"
                "    raise AssertionError('authored callback was invoked')\n"
                "class Foreign:\n"
                "    def __call__(self, value): return value\n"
                "    def __reduce__(self): return forbidden()\n"
                "keyword_operation = methodcaller('format', field=forbidden)\n",
            ),
        )
        consumer = (
            "import builtins, functools, importlib, sys\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_reducer_consumer')\n"
            "assert module.operation('{field}') == 'native'\n"
            "native.capture((module.__name__,)).unwrap()\n"
            "assert module.effects == [], module.effects\n"
            "original_importer = builtins.__import__\n"
            "original_partial = functools.partial\n"
            f"defect = {defect!r}\n"
            "if defect == 'partial':\n"
            "    functools.partial = module.forbidden\n"
            "elif defect == 'importer':\n"
            "    builtins.__import__ = module.forbidden\n"
            "else:\n"
            "    module.operation = module.Foreign()\n"
            "try:\n"
            "    observed = native.capture((module.__name__,))\n"
            "finally:\n"
            "    builtins.__import__ = original_importer\n"
            "    functools.partial = original_partial\n"
            "assert observed.failure, observed\n"
            "assert module.effects == [], module.effects\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("dumper", ["CDumper", "CSafeDumper"])
    @pytest.mark.parametrize("defect", ["none", "binding", "supplier"])
    def test_native_extension_alias_retains_its_lexical_binding_proof(
        tmp_path: Path,
        dumper: str,
        defect: str,
    ) -> None:
        """Real YAML emission admits native aliases and rejects replaced exports."""
        # Preserve 8ab3eff's real-consumer regression through the current public API.
        package = tmp_path / "native_yaml_consumer"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "import yaml\n"
                "callback = yaml.CSafeDumper.__setstate__\n"
                "def emit(value, dumper):\n"
                "    return yaml.dump(value, Dumper=vars(yaml)[dumper])\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from types import MethodType\n"
            "import yaml\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as native\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_yaml_consumer')\n"
            "assert module.emit({'native': 'emitted'}, sys.argv[2]) "
            "== 'native: emitted\\n'\n"
            "exported = module.callback\n"
            "callback = exported.__func__ "
            "if type(exported) is MethodType else exported\n"
            "observed = native.capture((module.__name__,)).unwrap()\n"
            "assert any(item.supplier == callback.__module__ "
            "and item.name == callback.__name__ "
            "and item.qualname == callback.__qualname__ "
            "for item in observed.bindings)\n"
            "if sys.argv[3] == 'binding':\n"
            "    module.callback = yaml.CSafeLoader.__setstate__\n"
            "    result = provenance.loaded_import_sources(module.__name__)\n"
            "    assert result.failure, result\n"
            "elif sys.argv[3] == 'supplier':\n"
            "    import _datetime\n"
            "    callback.__module__ = _datetime.__name__\n"
            "    result = provenance.loaded_import_sources(module.__name__)\n"
            "    assert result.failure, result\n"
            "else:\n"
            "    provenance.loaded_import_sources(module.__name__).unwrap()\n"
        )
        tm.ok(
            u.Cli.capture(
                [
                    executable,
                    "-c",
                    consumer,
                    str(tmp_path),
                    dumper,
                    defect,
                ],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    def test_provenance_never_replays_an_absolute_import_effect(
        tmp_path: Path,
    ) -> None:
        """A source proof preserves effects even when staging cannot relocate them."""
        package = tmp_path / "absolute_effect_provider"
        marker = tmp_path / "absolute-import-effects"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "marker = __import__('pathlib').Path(" + repr(str(marker)) + ")\n"
                "with marker.open('a', encoding='utf-8') as stream:\n"
                "    stream.write('import\\n')\n"
                "class Payload:\n"
                "    def operation(self): return 'native'\n",
            ),
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('absolute_effect_provider')\n"
            "assert module.marker.read_text(encoding='utf-8') == 'import\\n'\n"
            "provenance.loaded_import_sources(module.__name__).unwrap()\n"
            "assert module.marker.read_text(encoding='utf-8') == 'import\\n'\n"
            "method = module.Payload.operation\n"
            "method.__code__ = method.__code__.replace(co_name='foreign')\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert module.marker.read_text(encoding='utf-8') == 'import\\n'\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            ),
        )

    @staticmethod
    @pytest.mark.parametrize("fields", [1, 3])
    @pytest.mark.parametrize("defect", ["none", "code", "filename", "closure"])
    def test_frozen_methods_authenticate_across_native_batch_positions(
        tmp_path: Path,
        fields: int,
        defect: str,
    ) -> None:
        """Native method offsets vary; executable code and bindings remain exact."""
        package = tmp_path / "frozen_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                "@dataclass(frozen=True, repr=False, eq=False)\n"
                "class Payload:\n"
                + "".join(f"    value_{index}: int\n" for index in range(fields)),
            )
        )
        consumer = (
            "import dataclasses, importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('frozen_provider')\n"
            "values = tuple(range(int(sys.argv[2])))\n"
            "payload = module.Payload(*values)\n"
            "assert dataclasses.astuple(payload) == values\n"
            "try:\n"
            "    del payload.value_0\n"
            "except dataclasses.FrozenInstanceError:\n"
            "    pass\n"
            "else:\n"
            "    raise AssertionError('Frozen consumer allowed field deletion')\n"
            "descriptor = module.Payload.__delattr__\n"
            "defect = sys.argv[3]\n"
            "if defect == 'code':\n"
            "    descriptor.__code__ = descriptor.__code__.replace(co_name='foreign')\n"
            "elif defect == 'filename':\n"
            "    descriptor.__code__ = "
            "descriptor.__code__.replace(co_filename='foreign')\n"
            "elif defect == 'closure':\n"
            "    cells = dict(zip("
            "descriptor.__code__.co_freevars, descriptor.__closure__))\n"
            "    cells['__class__'].cell_contents = str\n"
            "observed = provenance.loaded_import_sources(module.__name__)\n"
            "if defect == 'none':\n"
            "    observed.unwrap()\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), str(fields), defect],
                cwd=tmp_path,
            )
        )

    @staticmethod
    @pytest.mark.parametrize("hook", ["hash", "equality", "getattribute"])
    def test_annotation_operand_is_rejected_before_callbacks_repeat(
        tmp_path: Path,
        hook: str,
    ) -> None:
        """An authenticated stdlib compiler cannot admit authored operand hooks."""
        package = tmp_path / "operand_provider"
        tm.ok(u.Cli.ensure_dir(package))
        operation = {
            "hash": (
                "    def __hash__(cls):\n"
                "        record('hash')\n"
                "        return type.__hash__(cls)\n"
            ),
            "equality": (
                "    def __hash__(cls):\n"
                "        return type.__hash__(int)\n"
                "    def __eq__(cls, other):\n"
                "        record('equality')\n"
                "        return type.__eq__(cls, other)\n"
            ),
            "getattribute": (
                "    def __getattribute__(cls, name):\n"
                "        record('getattribute')\n"
                "        return type.__getattribute__(cls, name)\n"
            ),
        }[hook]
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                "from pathlib import Path\n"
                "from typing import Union\n"
                "effects = []\n"
                "marker = Path(__file__).with_suffix('.effects')\n"
                "marker.write_text('', encoding='utf-8')\n"
                "def record(effect):\n"
                "    effects.append(effect)\n"
                "    with marker.open('a', encoding='utf-8') as stream:\n"
                "        stream.write(effect + '\\n')\n"
                "class Meta(type):\n" + operation + "class Operand(metaclass=Meta):\n"
                "    pass\n"
                "@dataclass\n"
                "class Payload:\n"
                "    value: Union[Operand, int]\n",
            )
        )
        consumer = (
            "import importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('operand_provider')\n"
            "value = module.Operand()\n"
            "assert module.Payload(value).value is value\n"
            "before = tuple(module.effects)\n"
            "marker = module.marker.read_bytes()\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path)],
                cwd=tmp_path,
            )
        )

    @staticmethod
    @pytest.mark.parametrize("supplier", ["Field", "_FuncBuilder"])
    def test_foreign_native_constructor_is_rejected_before_invocation(
        tmp_path: Path,
        supplier: str,
    ) -> None:
        """A native function cannot authorize a replaced compiler class binding."""
        package = tmp_path / "constructor_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / c.Infra.INIT_PY,
                "from dataclasses import dataclass\n"
                "from pathlib import Path\n"
                "effects = []\n"
                "marker = Path(__file__).with_suffix('.effects')\n"
                "marker.write_text('', encoding='utf-8')\n"
                "def record(effect):\n"
                "    effects.append(effect)\n"
                "    with marker.open('a', encoding='utf-8') as stream:\n"
                "        stream.write(effect + '\\n')\n"
                "class Foreign:\n"
                "    def __new__(cls, *args, **kwargs):\n"
                "        record('new')\n"
                "        return object.__new__(cls)\n"
                "    def __init__(self, *args, **kwargs):\n"
                "        record('init')\n"
                "@dataclass\n"
                "class Payload:\n"
                "    value: int = 1\n",
            )
        )
        consumer = (
            "import dataclasses, importlib, sys\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('constructor_provider')\n"
            "assert module.Payload(2).value == 2\n"
            "before = tuple(module.effects)\n"
            "marker = module.marker.read_bytes()\n"
            "setattr(dataclasses, sys.argv[2], module.Foreign)\n"
            "assert provenance.loaded_import_sources(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
        )
        tm.ok(
            u.Cli.capture(
                [executable, "-c", consumer, str(tmp_path), supplier],
                cwd=tmp_path,
            )
        )
