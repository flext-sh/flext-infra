"""Behavior tests for fail-closed workspace editable provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from json import dumps
from pathlib import Path
from sys import executable, prefix
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

from flext_infra import config
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from tests import c, m, tm, u

if TYPE_CHECKING:
    from collections.abc import Iterator

    from tests import p, t


class TestsFlextInfraWorkspaceEnvironmentProvenance:
    """Validate real PEP 610 and distribution file metadata."""

    @staticmethod
    @pytest.mark.parametrize(
        "condition", ["TC", "typing_alias.TYPE_CHECKING", "not TC"]
    )
    @pytest.mark.parametrize(
        "defect",
        [
            "none",
            "alias",
            "supplier",
            "source",
            "flag",
            "condition",
            "ambiguous",
            "code",
            "cycle",
        ],
    )
    def test_native_typing_branch_retains_runtime_metaclass_alias(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        condition: str,
        defect: str,
    ) -> None:
        """Typing-only shadows never replace the physical runtime supplier proof."""
        package = tmp_path / "conditional_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "supplier.py",
                "effects = []\n"
                "class NativeMeta(type):\n"
                "    def __new__(cls, name, bases, namespace):\n"
                "        effects.append('native-construction')\n"
                "        return super().__new__(cls, name, bases, namespace)\n"
                "class OtherMeta(type): pass\n",
            )
        )
        shadow = (
            "    @shadow_decorator\n    class RuntimeMeta(supplier.NativeMeta): pass\n"
        )
        alias = "    RuntimeMeta = supplier.NativeMeta\n"
        body, otherwise = (alias, shadow) if condition == "not TC" else (shadow, alias)
        u.Tests.write_package_init(
            package,
            "from typing import TYPE_CHECKING as TC\n"
            "import typing as typing_alias\n"
            "from . import supplier\n"
            "effects = []\n"
            "def shadow_decorator(cls):\n"
            "    effects.append('typing-shadow')\n"
            "    return cls\n"
            f"if {condition}:\n{body}else:\n{otherwise}"
            "class Payload(metaclass=RuntimeMeta):\n"
            "    def operation(self): return 'physical'\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('conditional_provider')\n"
            "supplier = module.supplier\n"
            "assert type(module.Payload) is module.RuntimeMeta is supplier.NativeMeta\n"
            "assert not module.effects\n"
            "before = tuple(supplier.effects)\n"
            "authenticate(module.__name__).unwrap()\n"
            "defect = sys.argv[2]\n"
            "source = pathlib.Path(module.__file__)\n"
            "if defect == 'alias': module.RuntimeMeta = supplier.OtherMeta\n"
            "elif defect == 'supplier': supplier.NativeMeta = supplier.OtherMeta\n"
            "elif defect == 'source':\n"
            "    source.write_text(source.read_text().replace("
            "'RuntimeMeta = supplier.NativeMeta',"
            " 'RuntimeMeta = supplier.OtherMeta'))\n"
            "elif defect == 'flag':\n"
            "    if sys.argv[3] == 'typing_alias.TYPE_CHECKING':"
            " module.typing_alias.TYPE_CHECKING = True\n"
            "    else: module.TC = True\n"
            "elif defect == 'condition':\n"
            "    source.write_text(source.read_text().replace("
            "'if ' + sys.argv[3] + ':', 'if unproven_condition:'))\n"
            "elif defect == 'ambiguous':\n"
            "    source.write_text(source.read_text().replace('class Payload',"
            " 'RuntimeMeta = supplier.NativeMeta\\nclass Payload'))\n"
            "elif defect == 'code':\n"
            "    supplier.NativeMeta.__new__.__code__ ="
            " supplier.NativeMeta.__new__.__code__.replace(co_name='replaced')\n"
            "elif defect == 'cycle':\n"
            "    source.write_text(source.read_text()"
            ".replace('RuntimeMeta = supplier.NativeMeta', 'RuntimeMeta = Loop')"
            ".replace('class Payload', 'Loop = RuntimeMeta\\nclass Payload'))\n"
            "observed = authenticate(module.__name__)\n"
            "assert observed.success == (defect == 'none'), observed\n"
            "assert tuple(supplier.effects) == before\n"
            "assert not module.effects\n"
        )
        native_consumer(consumer, str(tmp_path), defect, condition)

    @staticmethod
    @pytest.mark.parametrize("supplier_kind", ["absent", "function", "class", "value"])
    @pytest.mark.parametrize("installed_layout", [False, True])
    def test_unknown_factory_diagnostics_preserve_private_values(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        supplier_kind: str,
        *,
        installed_layout: bool,
    ) -> None:
        """An unproven binding fails with declaration context, never operand contents."""
        import_root = tmp_path / "site-packages" if installed_layout else tmp_path
        u.Tests.write_package_init(
            import_root / "diagnostic_provider",
            "from dataclasses import dataclass\n"
            "@dataclass\n"
            "class Payload:\n"
            "    value: str\n"
            "class Holder:\n"
            "    class unproven: pass\n",
        )
        consumer = (
            "import json\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('diagnostic_provider')\n"
            "authenticate(module.__name__).unwrap()\n"
            "effects = []\n"
            "class Private:\n"
            "    def __repr__(self):\n"
            "        effects.append('repr')\n"
            "        return 'private-material-must-not-appear'\n"
            "kind = sys.argv[2]\n"
            "if kind == 'function': module.unproven = module.dataclass\n"
            "elif kind == 'class': module.unproven = module.Holder.unproven\n"
            "elif kind == 'value': module.unproven = Private()\n"
            "source = pathlib.Path(module.__file__)\n"
            "source.write_text(source.read_text().replace('@dataclass', '@unproven'))\n"
            "result = authenticate(module.__name__)\n"
            "assert result.failure, result\n"
            "error = result.error\n"
            "assert module.__name__ in error, error\n"
            "assert error.startswith('construction factory has no authenticated source "
            "binding:'), error\n"
            "assert 'identifier=' + json.dumps('unproven') in error, error\n"
            "assert 'module=' + json.dumps(module.__name__) in error, error\n"
            "assert 'package=' + json.dumps(module.__package__) in error, error\n"
            "assert 'registered=True' in error, error\n"
            "assert 'receiver=' + json.dumps(module.Payload.__qualname__) in error, "
            "error\n"
            "assert 'declaration=' + json.dumps(module.Payload.__name__) in error, "
            "error\n"
            "assert 'source=' + json.dumps(str(source)) in error, error\n"
            "assert 'supplier_kind=' + kind in error, error\n"
            "assert 'private-material-must-not-appear' not in error\n"
            "assert not effects\n"
        )
        native_consumer(consumer, str(import_root), supplier_kind)

    @staticmethod
    @pytest.mark.parametrize("package_name", ["external_provider", "flext_lookalike"])
    @pytest.mark.parametrize("defect", ["none", "source", "code"])
    def test_public_declaration_binding_authenticates_every_owned_namespace(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        package_name: str,
        defect: str,
    ) -> None:
        """Inherited guard calls keep non-fleet declarations and reject native changes."""
        u.Tests.write_package_init(
            tmp_path / package_name,
            "class Payload:\n"
            "    instance = None\n"
            "    def operation(self): return 'physical-before'\n",
        )
        consumer = (
            "class Derived(fresh): pass\n"
            "fresh = Derived\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module(sys.argv[2])\n"
            "module.Payload.instance = module.Payload()\n"
            "sources = authenticate(module.__name__).unwrap().sources\n"
            "assert any(item[0] == module.__name__ + '::Payload.operation'"
            " and item[1] == module.__file__ for item in sources)\n"
            "defect = sys.argv[3]\n"
            "if defect == 'source':\n"
            "    source = pathlib.Path(module.__file__)\n"
            "    source.write_text(source.read_text().replace("
            "'physical-before', 'physical-after'))\n"
            "elif defect == 'code':\n"
            "    module.Payload.operation.__code__ ="
            " module.Payload.operation.__code__.replace(co_name='replaced')\n"
            "observed = authenticate(module.__name__)\n"
            "assert observed.success == (defect == 'none'), observed\n"
            "assert module.Payload.instance.operation() == 'physical-before'\n"
        )
        native_consumer(consumer, str(tmp_path), package_name, defect)

    @staticmethod
    @pytest.mark.parametrize("local_accessor", [False, True])
    def test_class_metadata_admission_uses_declaring_module(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        *,
        local_accessor: bool,
    ) -> None:
        """Imported GitPython metadata does not replace the local class proof."""
        source = "from git import Git\n"
        if local_accessor:
            source += (
                "class Metadata(type):\n"
                "    def __getattribute__(cls, name):\n"
                "        return super().__getattribute__(name)\n"
                "class Local(metaclass=Metadata):\n"
                "    value = 'payload'\n"
            )
        else:
            source += "class Local:\n    value = 'payload'\n"
        u.Tests.write_package_init(
            tmp_path / "metadata_provider",
            source,
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('metadata_provider')\n"
            "result = authenticate(module.__name__)\n"
            "if sys.argv[2] == 'local':\n"
            "    assert result.failure, result\n"
            "    assert 'binding=Local' in result.error, result\n"
            "else:\n"
            "    result.unwrap()\n"
        )
        native_consumer(
            consumer, str(tmp_path), "local" if local_accessor else "imported"
        )

    @staticmethod
    @pytest.mark.parametrize(
        "defect",
        [
            "none",
            "receiver",
            "supplier",
            "code",
            "receiver-source",
            "supplier-source",
            "import",
            "wrapped",
            "class-bound",
            "static-wrapped",
            "property",
        ],
    )
    @pytest.mark.parametrize("inherited", [False, True])
    @pytest.mark.parametrize("installed_layout", [False, True])
    def test_physical_alias_authenticates_receiver_and_mro_supplier(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
        inherited: bool,
        *,
        installed_layout: bool,
    ) -> None:
        """Relative imports retain raw alias identity and both physical declarations."""
        import_root = tmp_path / "site-packages" if installed_layout else tmp_path
        package = import_root / "alias_provider"
        tm.ok(u.Cli.ensure_dir(package))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "supplier.py",
                "class Ancestor:\n"
                "    def operation(self): return 'supplier-before'\n"
                "    def alternate(self): return 'alternate'\n"
                "    @property\n"
                "    def value(self): return 'property'\n"
                "    @property\n"
                "    def other_value(self): return 'other-property'\n"
                "    @classmethod\n"
                "    def owner(cls): return cls\n"
                "    @staticmethod\n"
                "    def static(): return 'static'\n"
                "class Supplier(Ancestor): pass\n",
            )
        )
        base = "supplier.Ancestor" if inherited else "object"
        u.Tests.write_package_init(
            package,
            "from . import supplier\n"
            f"class Receiver({base}):\n"
            "    operation = supplier.Supplier.operation\n"
            "    value = supplier.Supplier.value\n"
            "    owner = supplier.Supplier.owner\n"
            "    static = supplier.Supplier.static\n",
        )
        consumer = (
            "from contextlib import contextmanager\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('alias_provider')\n"
            "supplier = module.supplier\n"
            "authenticate(module.__name__).unwrap()\n"
            "defect = sys.argv[2]\n"
            "if defect == 'receiver':\n"
            "    module.Receiver.operation = supplier.Ancestor.alternate\n"
            "elif defect == 'supplier':\n"
            "    supplier.Ancestor.operation = supplier.Ancestor.alternate\n"
            "elif defect == 'code':\n"
            "    supplier.Ancestor.operation.__code__ ="
            " supplier.Ancestor.operation.__code__.replace(co_name='replaced')\n"
            "elif defect == 'receiver-source':\n"
            "    source = pathlib.Path(module.__file__)\n"
            "    source.write_text(source.read_text().replace("
            "'Supplier.operation', 'Supplier.alternate'))\n"
            "elif defect == 'supplier-source':\n"
            "    source = pathlib.Path(supplier.__file__)\n"
            "    source.write_text(source.read_text().replace("
            "'supplier-before', 'supplier-after'))\n"
            "elif defect == 'import':\n"
            "    module.supplier = pathlib\n"
            "elif defect == 'wrapped':\n"
            "    module.Receiver.operation = contextmanager("
            "supplier.Ancestor.operation)\n"
            "elif defect == 'class-bound':\n"
            "    module.Receiver.owner = supplier.Ancestor.owner\n"
            "elif defect == 'static-wrapped':\n"
            "    module.Receiver.static = staticmethod(module.Receiver.static)\n"
            "elif defect == 'property':\n"
            "    module.Receiver.value = supplier.Ancestor.other_value\n"
            "observed = authenticate(module.__name__)\n"
            "if defect == 'none':\n"
            "    sources = observed.unwrap().sources\n"
            "    assert module.Receiver().operation() == 'supplier-before'\n"
            "    assert module.Receiver().value == 'property'\n"
            "    assert module.Receiver.owner() is supplier.Supplier\n"
            "    assert module.Receiver().owner() is supplier.Supplier\n"
            "    assert module.Receiver.static() == 'static'\n"
            "    assert any(item[0] == module.__name__ + '::Receiver.operation'"
            " and item[1] == module.__file__ for item in sources)\n"
            "    assert any(item[0] == supplier.__name__ + '::Ancestor.operation'"
            " and item[1] == supplier.__file__ for item in sources)\n"
            "else:\n"
            "    assert observed.failure, observed\n"
            "    assert module.__name__ in observed.error, observed\n"
            "    if defect in {'receiver', 'supplier', 'receiver-source', 'wrapped', "
            "'class-bound', 'static-wrapped', 'property'}:\n"
            "        error = observed.error\n"
            "        assert error.startswith('descriptor differs from its physical "
            "alias supplier:'), error\n"
            "        assert 'module=\"alias_provider\"' in error, error\n"
            "        assert 'receiver=\"Receiver\"' in error, error\n"
            "        assert 'attribute=' in error and 'alias_identifier=' in error, "
            "error\n"
            "        assert 'supplier_module=' in error and 'supplier_owner=' in "
            "error, error\n"
            "        assert 'receiver_kind=' in error and 'supplier_kind=' in error, "
            "error\n"
        )
        native_consumer(consumer, str(import_root), defect)

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "receiver", "supplier", "code"])
    def test_installed_pydantic_aliases_retain_representation_identity(
        native_consumer: p.Tests.NativeConsumer,
        defect: str,
    ) -> None:
        """The real BaseModel alias authenticates without replaying model."""
        consumer = (
            "import sys\n"
            "from pydantic import BaseModel\n"
            "from pydantic._internal import _repr\n"
            "descriptor = vars(BaseModel)['__rich_repr__']\n"
            "assert descriptor is vars(_repr.Representation)['__rich_repr__']\n"
            "authenticate(BaseModel.__module__).unwrap()\n"
            "defect = sys.argv[1]\n"
            "if defect == 'receiver':\n"
            "    BaseModel.__rich_repr__ = BaseModel.__repr__\n"
            "elif defect == 'supplier':\n"
            "    _repr.Representation.__rich_repr__ = _repr.Representation.__pretty__\n"
            "elif defect == 'code':\n"
            "    descriptor.__code__ ="
            " descriptor.__code__.replace(co_name='replaced')\n"
            "observed = authenticate(BaseModel.__module__)\n"
            "if defect == 'none':\n"
            "    sources = observed.unwrap().sources\n"
            "    assert any(item[0] == BaseModel.__module__"
            " + '::BaseModel.__rich_repr__' for item in sources)\n"
            "    assert any(item[0] == _repr.__name__"
            " + '::Representation.__rich_repr__'"
            " and item[1] == _repr.__file__ for item in sources)\n"
            "else: assert observed.failure, observed\n"
        )
        native_consumer(consumer, defect)

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "annotation"])
    def test_installed_eager_callable_dataclass_preserves_native_schema(
        native_consumer: p.Tests.NativeConsumer,
        defect: str,
    ) -> None:
        """Real eager Callable metadata authenticates; a changed signature does not."""
        consumer = (
            "import annotated_types\n"
            "from collections.abc import Callable\n"
            "from typing import Any, get_args, get_origin\n"
            "import sys\n"
            "predicate = annotated_types.Not(str.isalpha)\n"
            "assert predicate('123') is True\n"
            "assert predicate('alphabetic') is False\n"
            "original = annotated_types.Not.__annotations__['func']\n"
            "assert get_origin(original) is Callable\n"
            "assert get_args(original) == ([Any], bool)\n"
            "if sys.argv[1] == 'annotation':\n"
            "    annotated_types.Not.__annotations__['func'] = Callable[[Any], int]\n"
            "observed = authenticate(annotated_types.__name__)\n"
            "if sys.argv[1] == 'none': observed.unwrap()\n"
            "else: assert observed.failure\n"
            "assert predicate('123') is True\n"
            "assert predicate('alphabetic') is False\n"
        )
        native_consumer(consumer, defect)

    @staticmethod
    def test_fresh_native_source_authenticates_the_loaded_guard(
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """The public guard accepts its own freshly imported native declarations."""
        consumer = (
            "observed = authenticate(preconditions.__module__)\n"
            "assert observed.success, observed\n"
            "assert observed.unwrap().sources\n"
        )
        native_consumer(consumer)

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "foreign"])
    def test_declaring_owner_authenticates_native_rebound_and_inherited_descriptors(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Metaclass rebinding retains source ownership; an unrelated class does not."""
        u.Tests.write_package_init(
            tmp_path / "descriptor_provider",
            "from enum import Enum\n"
            "class Parent:\n"
            "    @staticmethod\n"
            "    def static(value): return value\n"
            "    @classmethod\n"
            "    def owner(cls): return cls\n"
            "    def instance(self): return type(self)\n"
            "class Child(Parent): pass\n"
            "class Other:\n"
            "    def instance(self): return type(self)\n"
            "class Token(Enum):\n"
            "    def __new__(cls, value):\n"
            "        result = object.__new__(cls)\n"
            "        result._value_ = value\n"
            "        return result\n"
            "    item = 'native'\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('descriptor_provider')\n"
            "if sys.argv[2] == 'foreign':"
            " module.Child.instance = module.Other.instance\n"
            "observed = authenticate(module.__name__)\n"
            "if sys.argv[2] == 'none':\n"
            "    observed.unwrap()\n"
            "    assert module.Child.static('native') == 'native'\n"
            "    assert module.Child.owner() is module.Child\n"
            "    assert module.Child().instance() is module.Child\n"
            "    assert module.Token('native') is module.Token.item\n"
            "else: assert observed.failure\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize("changed", [False, True])
    def test_inherited_property_authenticates_its_physical_provider(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        changed: bool,
    ) -> None:
        """An inherited accessor retains its supplier, not its importing class's file."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / "ancestor_provider.py",
                "class Ancestor:\n"
                "    @property\n"
                "    def value(self):\n        return 'ancestor-before'\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / "child_provider.py",
                "from ancestor_provider import Ancestor\n"
                "class Child(Ancestor):\n    pass\n",
            )
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('child_provider')\n"
            "ancestor = sys.modules['ancestor_provider']\n"
            "source = pathlib.Path(ancestor.__file__)\n"
            "if sys.argv[2] == 'True':\n"
            "    source.write_text(source.read_text().replace("
            "'ancestor-before', 'ancestor-after'))\n"
            "observed = authenticate(module.__name__)\n"
            "assert observed.success == (sys.argv[2] == 'False'), observed\n"
            "if observed.success:\n"
            "    assert any(item[0].startswith('ancestor_provider::')"
            " and item[1] == str(source) for item in observed.unwrap().sources)\n"
            "assert module.Child().value == 'ancestor-before'\n"
        )
        native_consumer(consumer, str(tmp_path), str(changed))

    @staticmethod
    def test_homonymous_declarations_keep_distinct_module_identities(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """A source inventory retains legitimate same-named declarations."""
        package = tmp_path / "homonym_provider"
        u.Tests.write_package_init(
            package,
            "from . import first, second\n",
        )
        for member in ("first", "second"):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    package / f"{member}.py",
                    f"class Declaration:\n    @classmethod"
                    f"\n    def value(cls):\n        return '{member}'\n",
                )
            )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('homonym_provider')\n"
            "observed = authenticate(module.__name__).unwrap().sources\n"
            "assert isinstance(observed, tuple)\n"
            "for member in (module.first, module.second):\n"
            "    assert any(item[0] == member.__name__ + '::Declaration.value'"
            " and item[1] == member.__file__ for item in observed)\n"
            "assert module.first.Declaration.value()"
            " != module.second.Declaration.value()\n"
        )
        native_consumer(consumer, str(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("namespace", ["collections.abc", "builtins", "_struct"])
    def test_native_artifacts_retain_identity_without_becoming_python_text(
        native_consumer: p.Tests.NativeConsumer,
        namespace: str,
    ) -> None:
        """Public provenance authenticates real frozen, builtin and extension inputs."""
        consumer = (
            "from inspect import getsourcefile\n"
            "module = importlib.import_module(sys.argv[1])\n"
            "sources = authenticate(sys.argv[1]).unwrap().sources\n"
            "paths = {pathlib.Path(item[2] or item[1]) for item in sources}\n"
            "origin = module.__spec__.origin\n"
            "artifact = pathlib.Path(sys.executable).resolve()"
            " if origin in {'built-in', 'frozen'} else pathlib.Path(origin)\n"
            "assert artifact in paths\n"
            "if origin == 'frozen':\n"
            "    source = getsourcefile(module)\n"
            "    assert source is not None and pathlib.Path(source) in paths\n"
            "else:\n"
            "    assert module.__spec__.loader.get_source("
            "module.__spec__.name) is None\n"
        )
        native_consumer(consumer, namespace, cwd=Path(__file__).parent)

    @staticmethod
    @pytest.mark.parametrize(
        "mutation",
        [
            "none",
            "function",
            "property",
            "classmethod",
            "class",
            "schema",
            "deleted",
            "binding",
            "callable",
            "syntax",
        ],
    )
    def test_loaded_declarations_require_the_current_physical_source(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Cached objects cannot authenticate changed source or foreign descriptors."""
        package = tmp_path / "identity_provider"
        package.mkdir()
        source = package / c.Infra.INIT_PY
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "from __future__ import annotations\n"
                "from dataclasses import dataclass\n"
                "from functools import wraps\n"
                "def operation():\n    return 'function-before'\n"
                "@dataclass\n"
                "class Payload:\n"
                "    instance = None\n"
                "    value: str\n"
                "    def identify(self):\n        return 'class-before'\n"
                "    @property\n"
                "    def observed(self):\n        return 'property-before'\n"
                "    @classmethod\n"
                "    def create(cls):\n        return cls('classmethod-before')\n"
                "class Other:\n"
                "    @property\n"
                "    def observed(self):\n        return 'foreign-binding'\n"
                "class Callable:\n"
                "    def __call__(self):\n        return 'callable'\n",
            )
        )
        consumer = (
            "from flext_core import FlextSettings\n"
            "assert FlextSettings.fetch_global() is FlextSettings.fetch_global()\n"
            "authenticate(FlextSettings.__module__).unwrap()\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('identity_provider')\n"
            "source = pathlib.Path(module.__file__)\n"
            "module.Payload.instance = module.Payload('live-instance')\n"
            "before = authenticate(module.__name__).unwrap()\n"
            "assert before.sources\n"
            "mutation = sys.argv[2]\n"
            "if mutation == 'deleted':\n    source.unlink()\n"
            "elif mutation == 'binding':\n    module.Payload.observed = "
            "module.Other.observed\n"
            "elif mutation == 'callable':\n    "
            "module.operation.__wrapped__ = module.Callable()\n"
            "elif mutation == 'syntax':\n    source.write_text('def invalid(:\\n')\n"
            "elif mutation != 'none':\n"
            "    old = 'value: str' if mutation == 'schema' else mutation + '-before'\n"
            "    new = 'replacement: str' if mutation == 'schema' else mutation + "
            "'-after'\n"
            "    source.write_text(source.read_text().replace(old, new))\n"
            "try:\n"
            "    observed = authenticate(module.__name__)\n"
            "except SyntaxError as error:\n"
            "    assert mutation == 'syntax' and error.filename is not None\n"
            "else:\n"
            "    assert mutation != 'syntax'\n"
            "    assert observed.success == (mutation == 'none'), observed\n"
            "assert module.operation() == 'function-before'\n"
        )
        native_consumer(consumer, str(tmp_path), mutation)

    @staticmethod
    @pytest.mark.parametrize(
        "defect", ["none", "foreign", "cycle", "source", "advertised", "descriptor"]
    )
    def test_decorated_callable_authenticates_its_executable_chain(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real contextmanager declarations retain source and reject tampered chains."""
        package = tmp_path / "decorated_provider"
        package.mkdir()
        source = package / c.Infra.INIT_PY
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "from contextlib import contextmanager\n"
                "from functools import wraps\n"
                "native = dict.__repr__\n"
                "@wraps(native)\n"
                "def native_operation(value):\n"
                "    return native(value)\n"
                "@contextmanager\n"
                "def operation():\n"
                "    yield 'authenticated'\n",
            ),
        )
        consumer = (
            "from contextlib import contextmanager\n"
            "from inspect import getfile\n"
            "from functools import wraps\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('decorated_provider')\n"
            "operation = module.operation\n"
            "defect = sys.argv[2]\n"
            "if defect == 'foreign':\n"
            "    operation.__wrapped__ = pathlib.Path.is_file\n"
            "elif defect == 'cycle':\n"
            "    operation.__wrapped__ = operation\n"
            "elif defect == 'source':\n"
            "    original = operation.__wrapped__\n"
            "    original.__code__ = original.__code__.replace(co_name='replaced')\n"
            "elif defect == 'advertised':\n"
            "    operation.__module__ = 'reprlib'\n"
            "elif defect == 'descriptor':\n"
            "    operation.__wrapped__ = dict.__repr__\n"
            "if defect == 'none':\n"
            "    with operation() as value:\n"
            "        assert value == 'authenticated'\n"
            "    assert module.native_operation({}) == '{}'\n"
            "    observed = authenticate(module.__name__)"
            ".unwrap().sources\n"
            "    assert observed\n"
            "    paths = {pathlib.Path(item[1]) for item in observed}\n"
            "    assert "
            "{pathlib.Path(module.__file__), pathlib.Path(getfile(contextmanager)), "
            "pathlib.Path(getfile(wraps)), pathlib.Path(sys.executable).resolve()} <= "
            "paths\n"
            "else:\n"
            "    assert authenticate(module.__name__).failure\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize("surface", ["decorator", "metaclass"])
    def test_construction_binding_does_not_invoke_foreign_accessors(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        surface: str,
    ) -> None:
        """Reject a replaced import before consulting its attribute callbacks."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / "static_supplier.py",
                "class Meta(type):\n    pass\n",
            )
        )
        supplier = "dataclasses" if surface == "decorator" else "static_supplier"
        construction = (
            "@supplier.dataclass\nclass Payload:\n"
            if surface == "decorator"
            else "@dataclass\nclass Payload(metaclass=supplier.Meta):\n"
        )
        u.Tests.write_package_init(
            tmp_path / "accessor_provider",
            f"import {supplier} as supplier\n"
            "from dataclasses import dataclass\n"
            "effects = []\n"
            "original = supplier\n"
            "class Accessor:\n"
            "    def __getattr__(self, name):\n"
            "        effects.append('accessor')\n"
            "        return getattr(original, name)\n"
            + construction
            + "    value: str = 'native'\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('accessor_provider')\n"
            "assert module.Payload().value == 'native'\n"
            "assert authenticate(module.__name__).unwrap()\n"
            "before = tuple(module.effects)\n"
            "module.supplier = module.Accessor()\n"
            "assert authenticate(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
        )
        native_consumer(consumer, str(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("keyword_only", [False, True])
    def test_generated_defaults_do_not_invoke_foreign_equality(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        keyword_only: bool,
    ) -> None:
        """Reject altered default values without executing their equality method."""
        u.Tests.write_package_init(
            tmp_path / "equality_provider",
            "from dataclasses import dataclass\n"
            "effects = []\n"
            "class Foreign:\n"
            "    def __eq__(self, other):\n"
            "        effects.append('equality')\n"
            "        return True\n"
            f"@dataclass(kw_only={keyword_only})\n"
            "class Payload:\n"
            "    value: str = 'native'\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('equality_provider')\n"
            "assert module.Payload().value == 'native'\n"
            "assert authenticate(module.__name__).unwrap()\n"
            "before = tuple(module.effects)\n"
            "if sys.argv[2] == 'True':\n"
            "    module.Payload.__init__.__kwdefaults__ = {'value': module.Foreign()}\n"
            "else:\n"
            "    module.Payload.__init__.__defaults__ = (module.Foreign(),)\n"
            "assert authenticate(module.__name__).failure\n"
            "assert tuple(module.effects) == before\n"
        )
        native_consumer(consumer, str(tmp_path), str(keyword_only))

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "code"])
    def test_generated_provenance_does_not_repeat_construction_effects(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Authentication preserves effects of the actual imported construction."""
        u.Tests.write_package_init(
            tmp_path / "effect_provider",
            "from dataclasses import dataclass\n"
            "from pathlib import Path\n"
            "effects = []\n"
            "marker = Path(__file__).with_suffix('.effects')\n"
            "def track(cls):\n"
            "    effects.append('decorator')\n"
            "    return cls\n"
            "class Meta(type):\n"
            "    def __new__(cls, name, bases, namespace):\n"
            "        effects.append('metaclass')\n"
            "        return super().__new__(cls, name, bases, namespace)\n"
            "class Parent:\n"
            "    def __init_subclass__(cls):\n"
            "        effects.append('subclass')\n"
            "@track\n"
            "@dataclass\n"
            "class Payload(Parent, metaclass=Meta):\n"
            "    effects.append('body')\n"
            "    with marker.open('a', encoding='utf-8') as stream:\n"
            "        stream.write('body\\n')\n"
            "    value: str = 'native'\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('effect_provider')\n"
            "assert module.Payload().value == 'native'\n"
            "before = tuple(module.effects)\n"
            "marker = module.marker.read_bytes()\n"
            "assert set(before) == {'body', 'decorator', 'metaclass', 'subclass'}\n"
            "authenticate(module.__name__).unwrap()\n"
            "if sys.argv[2] == 'code':\n"
            "    module.Payload.__init__.__code__ = "
            "module.Payload.__init__.__code__.replace(co_name='replaced')\n"
            "observed = authenticate(module.__name__)\n"
            "assert observed.success == (sys.argv[2] == 'none'), observed\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "options", "supplier"])
    def test_generated_descriptor_requires_authored_factory_binding(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A genuine regenerated descriptor cannot bless an altered construction."""
        u.Tests.write_package_init(
            tmp_path / "factory_provider",
            "from dataclasses import dataclass as construct\n"
            "FROZEN = False\n"
            "@construct(frozen=FROZEN)\n"
            "class Payload:\n"
            "    value: str = 'native'\n",
        )
        consumer = (
            "from dataclasses import fields, make_dataclass\n"
            "from attr import attrs\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('factory_provider')\n"
            "assert module.Payload().value == 'native'\n"
            "defect = sys.argv[2]\n"
            "if defect == 'options':\n"
            "    module.FROZEN = True\n"
            "    original = module.Payload\n"
            "    module.Payload = make_dataclass(\n"
            "        original.__name__,\n"
            "        [(item.name, item.type, item.default) for item in "
            "fields(original)],\n"
            "        bases=original.__bases__, module=module.__name__, frozen=True,\n"
            "    )\n"
            "elif defect == 'supplier':\n"
            "    module.construct = attrs\n"
            "    module.Payload = attrs(module.Payload)\n"
            "assert module.Payload().value == 'native'\n"
            "observed = authenticate(module.__name__)\n"
            "if defect == 'none':\n"
            "    assert observed.unwrap()\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize(
        "defect",
        ["none", "descriptor", "wrapped", "code", "defaults", "parameters"],
    )
    @pytest.mark.parametrize("options", ["", "frozen=True, slots=True"])
    @pytest.mark.parametrize("base", ["object", "Parent"])
    def test_dataclass_generated_callable_authenticates_its_descriptor(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
        options: str,
        base: str,
    ) -> None:
        """Real compiler methods retain class ownership and reject moved bindings."""
        package = tmp_path / "generated_provider"
        package.mkdir()
        source = package / c.Infra.INIT_PY
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                "from dataclasses import dataclass\n"
                "class Parent:\n"
                "    def __init__(self):\n"
                "        raise RuntimeError('inherited constructor is not explicit')\n"
                "class Generic[T]:\n"
                "    value: str\n"
                "class Holder:\n"
                "    class Generic[T]:\n"
                "        value: str\n"
                f"@dataclass({options})\n"
                f"class Payload({base}):\n"
                "    value: str\n"
                f"@dataclass({options})\n"
                f"class Other({base}):\n"
                "    value: str\n",
            ),
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('generated_provider')\n"
            "defect = sys.argv[2]\n"
            "if defect == 'descriptor':\n"
            "    module.Payload.__repr__ = module.Other.__repr__\n"
            "elif defect == 'wrapped':\n"
            "    module.Payload.__repr__.__wrapped__ = "
            "module.Other.__repr__.__wrapped__\n"
            "elif defect == 'code':\n"
            "    module.Payload.__init__.__code__ = module.Payload.__init__.__code__."
            "replace(co_name='foreign')\n"
            "elif defect == 'defaults':\n"
            "    module.Payload.__init__.__defaults__ = ('foreign',)\n"
            "elif defect == 'parameters':\n"
            "    class ForeignParameters:\n"
            "        @property\n"
            "        def frozen(self):\n"
            "            raise AssertionError('unadmitted parameter accessor ran')\n"
            "    module.Payload.__dataclass_params__ = ForeignParameters()\n"
            "if defect == 'none':\n"
            "    assert repr(module.Payload('authenticated')) == "
            "\"Payload(value='authenticated')\"\n"
            "    observed = "
            "authenticate(module.__name__).unwrap().sources\n"
            "    generated = [item for item in observed if item[2]]\n"
            "    assert generated\n"
            "    assert all(pathlib.Path(item[2]) == "
            "pathlib.Path(module.__file__) for item in generated)\n"
            "else:\n"
            "    assert authenticate(module.__name__).failure\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "constructor", "getter"])
    def test_annotation_metadata_constructor_is_admitted_before_callbacks(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real immutable metadata preserves operands and rejects authored callbacks."""
        u.Tests.write_package_init(
            tmp_path / "metadata_provider",
            "from dataclasses import dataclass\n"
            "from typing import Annotated\n"
            "from annotated_types import Ge\n"
            "@dataclass\n"
            "class Payload:\n"
            "    value: Annotated[int, Ge(0)]\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('metadata_provider')\n"
            "defect = sys.argv[2]\n"
            "def forbidden(*args, **kwargs):\n"
            "    raise AssertionError('unadmitted metadata callback ran')\n"
            "if defect == 'constructor':\n"
            "    module.Ge.__init__ = forbidden\n"
            "elif defect == 'getter':\n"
            "    module.Ge.ge = property(forbidden)\n"
            "observed = authenticate(module.__name__)\n"
            "if defect == 'none':\n"
            "    assert module.Payload(3).value == 3\n"
            "    assert observed.unwrap()\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize(
        "defect",
        ["none", "filename", "annotation", "parameters"],
    )
    def test_native_reference_compares_static_metadata_without_callbacks(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A captured native epoch detects mutations before reading authored getters."""
        u.Tests.write_package_init(
            tmp_path / "static_reference_provider",
            "from dataclasses import dataclass\n"
            "from typing import Annotated\n"
            "from annotated_types import Ge\n"
            "@dataclass(frozen=True)\n"
            "class Payload:\n"
            "    value: Annotated[int, Ge(0)]\n"
            "class ForeignParameters:\n"
            "    @property\n"
            "    def frozen(self):\n"
            "        raise AssertionError('unadmitted frozen getter ran')\n"
            "    @property\n"
            "    def __class__(self):\n"
            "        raise AssertionError('unadmitted class getter ran')\n",
        )
        consumer = (
            "from typing import Annotated\n"
            "from annotated_types import Ge\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('static_reference_provider')\n"
            "assert module.Payload(3).value == 3\n"
            "reference = provenance.capture((m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "defect = sys.argv[2]\n"
            "if defect == 'filename':\n"
            "    method = module.Payload.__init__\n"
            "    method.__code__ = method.__code__.replace(co_filename='<foreign>')\n"
            "elif defect == 'annotation':\n"
            "    module.Payload.__annotations__['value'] = Annotated[int, Ge(3)]\n"
            "elif defect == 'parameters':\n"
            "    module.Payload.__dataclass_params__ = module.ForeignParameters()\n"
            "observed = provenance.capture((m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "compared = provenance.compare(observed, reference)\n"
            "assert compared.success == (defect == 'none'), compared.error\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize(
        "defect",
        ["none", "wrapped", "cached_wrapped", "partial_arguments"],
    )
    def test_native_c_wrapper_requires_actual_callable_topology(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real native wrappers retain function links and reject cache-assisted."""
        u.Tests.write_package_init(
            tmp_path / "native_wrapper_provider",
            "from functools import lru_cache, partial\n"
            "def counterfeit(value='foreign'):\n"
            "    raise AssertionError('unadmitted callable was executed')\n"
            "@lru_cache(maxsize=None)\n"
            "def produce(value='native'):\n"
            "    return value\n"
            "selected = partial(produce, value='native')\n",
        )
        consumer = (
            "from gc import get_referents\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as provenance\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('native_wrapper_provider')\n"
            "reference = provenance.capture((m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "defect = sys.argv[2]\n"
            "if defect == 'wrapped':\n"
            "    module.produce.__wrapped__ = module.counterfeit\n"
            "elif defect == 'cached_wrapped':\n"
            "    cache = next(item for item in get_referents(module.produce)\n"
            "        if type(item) is dict and '__wrapped__' not in item)\n"
            "    cache['counterfeit'] = module.counterfeit\n"
            "    module.produce.__wrapped__ = module.counterfeit\n"
            "elif defect == 'partial_arguments':\n"
            "    module.selected.keywords['value'] = 'foreign'\n"
            "observed = provenance.capture((m.Infra.SourceClassReference(target=module.__name__),))\n"
            "if defect in {'wrapped', 'cached_wrapped'}:\n"
            "    assert observed.failure, observed\n"
            "else:\n"
            "    compared = provenance.compare(observed.unwrap(), reference)\n"
            "    assert compared.success == (defect == 'none'), compared.error\n"
            "    if defect == 'none':\n"
            "        assert module.selected() == 'native'\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    def test_source_preflight_does_not_reimport_authored_effects(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Static provenance fails generated admission without replaying import."""
        u.Tests.write_package_init(
            tmp_path / "import_effect_provider",
            "from dataclasses import dataclass\n"
            "import pathlib\n"
            "pathlib.Path(__file__).with_name('effect').write_text('imported')\n"
            "@dataclass\n"
            "class Payload:\n"
            "    value: str\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('import_effect_provider')\n"
            "effect = pathlib.Path(module.__file__).with_name('effect')\n"
            "assert effect.read_text() == 'imported'\n"
            "effect.unlink()\n"
            "observed = authenticate(module.__name__)\n"
            "assert observed.failure, observed\n"
            "assert not effect.exists(), 'source admission replayed the module'\n"
        )
        native_consumer(consumer, str(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "defaults", "kwdefaults", "closure"])
    def test_installed_annotation_dataclass_retains_native_constructor_proof(
        native_consumer: p.Tests.NativeConsumer,
        defect: str,
    ) -> None:
        """Authenticate real Protocol dataclasses and reject altered constructor state."""
        consumer = (
            "import inspect\n"
            "from annotated_types import Interval, Len, MaxLen, MinLen\n"
            "import sys\n"
            "defect = sys.argv[1]\n"
            "if defect == 'defaults':\n"
            "    Len.__init__.__defaults__ = (1, None)\n"
            "elif defect == 'kwdefaults':\n"
            "    Len.__init__.__kwdefaults__ = {'foreign': None}\n"
            "elif defect == 'closure':\n"
            "    cells = "
            "dict(zip(Len.__init__.__code__.co_freevars, Len.__init__.__closure__))\n"
            "    cells['__dataclass_builtins_object__'].cell_contents = str\n"
            "if defect == 'none':\n"
            "    assert Len().min_length == 0\n"
            "    assert Len().max_length is None\n"
            "    assert list(Len(2, max_length=5)) == [MinLen(2), MaxLen(5)]\n"
            "    assert Interval(gt=1).gt == 1\n"
            "    observed = authenticate(Len.__module__).unwrap().sources\n"
            "    assert any(item[2] == inspect.getfile(Len) for item in observed)\n"
            "else:\n"
            "    assert authenticate(Len.__module__).failure\n"
        )
        native_consumer(consumer, defect)

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "code", "defaults", "kwdefaults"])
    def test_attrs_generated_callable_authenticates_native_decorator(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Native attrs constructors preserve public behavior and reject tampering."""
        u.Tests.write_package_init(
            tmp_path / "attrs_provider",
            "from attr import attrs, attrib\n"
            "@attrs(slots=True, unsafe_hash=True)\n"
            "class Payload:\n"
            "    value = attrib(default='captured')\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module('attrs_provider')\n"
            "defect = sys.argv[2]\n"
            "if defect == 'code':\n"
            "    module.Payload.__init__.__code__ = module."
            "Payload.__init__.__code__.replace(co_name='foreign')\n"
            "elif defect == 'defaults':\n"
            "    module.Payload.__init__.__defaults__ = ('foreign',)\n"
            "elif defect == 'kwdefaults':\n"
            "    module.Payload.__init__.__kwdefaults__ = {'foreign': None}\n"
            "if defect == 'none':\n"
            "    assert module.Payload().value == 'captured'\n"
            "    assert module.Payload(value='native').value == 'native'\n"
            "    observed = "
            "authenticate(module.__name__).unwrap().sources\n"
            "    assert any(item[2] == str(pathlib.Path(module.__file__)) "
            "for item in observed)\n"
            "else:\n"
            "    assert authenticate(module.__name__).failure\n"
        )
        native_consumer(consumer, str(tmp_path), defect)

    @staticmethod
    @pytest.mark.parametrize(
        "defect", ["none", "code", "scope", "advertised", "defaults"]
    )
    def test_native_generated_class_authenticates_its_compiler_scope(
        native_consumer: p.Tests.NativeConsumer,
        defect: str,
    ) -> None:
        """The installed Pillow consumer proves native factory, not a module label."""
        consumer = (
            "import pathlib, sys\n"
            "from collections import namedtuple\n"
            "from inspect import getfile\n"
            "from PIL import ImageMode\n"
            "operation = ImageMode.ModeDescriptor.__new__\n"
            "defect = sys.argv[1]\n"
            "if defect == 'code':\n"
            "    operation.__code__ = operation.__code__.replace(co_name='forged')\n"
            "elif defect == 'scope':\n"
            "    operation.__globals__['_tuple_new'] = dict.__new__\n"
            "elif defect == 'advertised':\n"
            "    operation.__module__ = 'reprlib'\n"
            "elif defect == 'defaults':\n"
            "    operation.__defaults__ = ('foreign',)\n"
            "observed = authenticate(ImageMode.__name__)\n"
            "if defect == 'none':\n"
            "    assert isinstance(ImageMode.getmode('RGB'), "
            "ImageMode.ModeDescriptor)\n"
            "    sources = observed.unwrap().sources\n"
            "    assert any(item[2] == ImageMode.__file__ for item in sources)\n"
            "    paths = {pathlib.Path(item[2] or item[1]) for item in sources}\n"
            "    assert pathlib.Path(getfile(namedtuple)) in paths\n"
            "    assert pathlib.Path(sys.executable).resolve() in paths\n"
            "else:\n"
            "    assert observed.failure\n"
        )
        native_consumer(consumer, defect, cwd=Path(__file__).parent)

    @staticmethod
    def test_package_election_does_not_reuse_a_retired_loaded_origin(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """A real imported package cannot authenticate its retired physical tree."""
        u.Tests.write_package_init(
            tmp_path / "retired_provider",
            "",
        )
        consumer = (
            "from flext_infra import u\n"
            "root = pathlib.Path(sys.argv[1])\n"
            "sys.path.insert(0, str(root))\n"
            "loaded = importlib.import_module('retired_provider')\n"
            "expected = root / loaded.__name__\n"
            "assert u.Infra.declared_package_dir(loaded.__name__) == expected\n"
            "assert u.Infra.declared_package_dir('flext_infra.codegen') is not None\n"
            "expected.rename(root / 'retired_tree')\n"
            "importlib.invalidate_caches()\n"
            "assert u.Infra.declared_package_dir(loaded.__name__) is None\n"
            "assert loaded.__file__ is not None\n"
            "assert not pathlib.Path(loaded.__file__).is_file()\n"
        )
        native_consumer(consumer, str(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("source_location", ["declared", "foreign"])
    def test_loaded_source_requires_declared_checkout_containment(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        source_location: str,
    ) -> None:
        """A cold-elected real supplier is not proof of declared checkout ownership."""
        checkout = tmp_path / "declared"
        u.Tests.WorktreeFixture.write_python_project(checkout, "owned-provider")
        metadata = tm.ok(u.Infra.read_project_metadata_result(checkout))
        source_root = (
            checkout / "src" if source_location == "declared" else tmp_path / "foreign"
        )
        package = source_root / metadata.package_name
        package.mkdir(parents=True, exist_ok=True)
        u.Tests.write_package_init(
            package,
            "from contextlib import contextmanager\n"
            "@contextmanager\n"
            "def operation():\n"
            "    yield 'authenticated'\n",
        )
        consumer = (
            "sys.path.insert(0, sys.argv[1])\n"
            "module = importlib.import_module(sys.argv[2])\n"
            "result = authenticate(module.__name__, "
            "source_root=pathlib.Path(sys.argv[3]))\n"
            "if sys.argv[4] == 'declared':\n"
            "    assert result.success, result.error\n"
            "    with module.operation() as value:\n"
            "        assert value == 'authenticated'\n"
            "else:\n"
            "    assert result.failure\n"
            "    assert 'loaded code differs from declaration' in result.error\n"
        )
        native_consumer(
            consumer,
            str(source_root),
            metadata.package_name,
            str(checkout),
            source_location,
        )

    @staticmethod
    def _toolchain_identity(site_packages: Path) -> str:
        """Read real installed metadata in a fresh process's public search path.

        Returns:
            The fingerprint emitted by the workspace provenance owner.

        """
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    executable,
                    "-c",
                    (
                        "from flext_infra.workspace import "
                        "FlextInfraWorkspaceEnvironmentProvenance\n"
                        "print(FlextInfraWorkspaceEnvironmentProvenance"
                        ".installed_toolchain_identity())\n"
                    ),
                ),
                cwd=site_packages.parent,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(site_packages)},
                ),
            ),
        )
        u.Tests.record_dependency_command_output(outcome)
        tm.that(
            u.Cli.process_succeeded(outcome.outcome),
            eq=True,
            msg=outcome.stdout + outcome.stderr,
        )
        return outcome.stdout.strip()

    def test_toolchain_identity_excludes_editable_checkout_paths(
        self,
        tmp_path: Path,
    ) -> None:
        """Two live checkouts of the same installed packages share one identity."""
        identities: list[str] = []
        for name in ("first-checkout", "second-checkout"):
            site_packages = tmp_path / name
            source = tmp_path / f"{name}-source"
            self._installed_editable(
                site_packages,
                "sample-member",
                direct_root=source,
                source_root=source,
            )
            identities.append(self._toolchain_identity(site_packages))
        tm.that(identities[0], eq=identities[1])

    def test_toolchain_identity_distinguishes_git_revisions_at_equal_version(
        self,
        tmp_path: Path,
    ) -> None:
        """Installed PEP 610 commits participate even when METADATA is unchanged."""
        identities: list[str] = []
        for ordinal, commit in enumerate(("a" * 40, "b" * 40)):
            site_packages = tmp_path / str(ordinal)
            self._installed_editable(
                site_packages,
                "sample-member",
                direct_root=tmp_path,
                source_root=tmp_path,
            )
            receipt = m.Infra.DirectUrlReceipt(
                url=u.Tests.WorktreeFixture.governed_repository_url("sample-member"),
                vcs_info=m.Infra.DirectUrlVcsInfo(vcs="git", commit_id=commit),
            )
            (
                site_packages / "sample_member-1.0.dist-info" / "direct_url.json"
            ).write_text(receipt.model_dump_json(), encoding="utf-8")
            identities.append(self._toolchain_identity(site_packages))
        tm.that(identities[0] != identities[1], eq=True)

    @staticmethod
    def test_actual_cli_preserves_toml_occurrence_comments() -> None:
        """Exercise the real TOML supplier used by dependency overlay generation."""
        document = u.Cli.toml_parse_text(
            '[metadata]\nvalues = [\n"first", # occurrence\n"second",\n]\n',
        )
        if document is None:
            pytest.fail("The public CLI parser rejected valid TOML")
        table = u.Cli.toml_table_child(document, "metadata")
        if table is None:
            pytest.fail("The public CLI parser lost the declared TOML table")
        tm.that(
            u.Cli.toml_array_item_comments(table, "values"),
            eq=("# occurrence", ""),
        )

    @staticmethod
    def test_real_checkout_runtime_has_declared_provenance() -> None:
        """Authenticate actual PEP 610 and RECORD metadata for the full workspace."""
        tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.validate(Path(__file__).parent),
        )

    @staticmethod
    def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
        """Derive independent runtime probes from the real typed topology."""
        if "live_repository" not in metafunc.fixturenames:
            return
        runtime = tm.ok(
            u.Infra.git_repository_root(
                m.Infra.GitRepoRequest(repo_root=Path(__file__).parent),
            ),
        ).repository_root
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(runtime))
        repositories = tuple(
            repository
            for repository in (workspace.repository, *workspace.subprojects)
            if repository.package and repository.editable
        )
        metafunc.parametrize(
            "live_repository",
            repositories,
            ids=tuple(repository.distribution for repository in repositories),
        )

    @staticmethod
    def test_real_checkout_runtime_uses_declared_source(
        live_repository: m.Infra.RepositoryRef,
    ) -> None:
        """Authenticate each real public import resolver without fake packages."""
        checkout = tm.ok(
            u.Infra.git_identity(
                m.Infra.GitRepoRequest(repo_root=Path(__file__).resolve().parent),
            ),
        ).repo_root
        runtime = tm.ok(
            u.Infra.git_repository_root(m.Infra.GitRepoRequest(repo_root=checkout)),
        ).repository_root
        ci = config.Infra.codegen.make.ci
        if u.Infra.env_value(ci.variable).strip() == ci.value:
            return
        member_root = (runtime / live_repository.path).resolve()
        metadata = tm.ok(u.Infra.read_project_metadata_result(member_root))
        package = u.Infra.declared_package_dir(metadata.package_name)
        tm.that(package is not None, eq=True, msg=live_repository.distribution)
        if package is not None:
            tm.that(
                package.resolve().is_relative_to(member_root),
                eq=True,
                msg=f"{live_repository.distribution}: {package} outside {member_root}",
            )

    @pytest.fixture
    def ci_mode(self) -> bool:
        """Read the hosted-runner contract used by the public consumer.

        Returns:
            Whether this test invocation selects locked CI provenance.

        """
        policy = config.Infra.codegen.make.uv_resolution
        return u.Infra.env_value(policy.hosted_variable).strip() == policy.hosted_value

    @pytest.fixture
    def site_packages(self) -> Iterator[Path]:
        """Isolate metadata beneath the owned prefix without installing packages.

        Yields:
            The metadata directory within the active environment's prefix.

        """
        with TemporaryDirectory(dir=prefix) as temporary:
            yield Path(temporary) / "site-packages"

    @staticmethod
    def _lock_path(root: Path) -> Path:
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(root))
        tm.ok(u.Cli.ensure_dir(context.lock_path.parent))
        return context.lock_path

    @staticmethod
    def _workspace(root: Path, distribution: str = "sample-member") -> Path:
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "sample",
            beads=u.Tests.BeadsIdentity(
                workspace="sample-workspace",
                database="sample-database",
                issue_prefix="sample-prefix",
            ),
        )
        member = root / distribution
        u.Tests.WorktreeFixture.initialize_governed_project(
            member,
            distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=f"{distribution}-workspace",
                database=f"{distribution}-database",
                issue_prefix=f"{distribution}-prefix",
            ),
            beads_owner=False,
        )
        u.Tests.WorktreeFixture.link_member_beads(
            member,
            root,
            workspace_name="sample-workspace",
            database="sample-database",
            issue_prefix="sample-prefix",
        )
        u.Tests.WorktreeFixture.write_gitmodules(root, (distribution,))
        return root

    @staticmethod
    def _installed_editable(
        site_packages: Path,
        distribution: str,
        *,
        direct_root: Path,
        source_root: Path,
    ) -> None:
        site_packages.mkdir()
        normalized = distribution.replace("-", "_")
        dist_info = site_packages / f"{normalized}-1.0.dist-info"
        dist_info.mkdir()
        pth_name = f"_editable_impl_{normalized}.pth"
        (site_packages / pth_name).write_text(f"{source_root}\n", encoding="utf-8")
        (dist_info / "METADATA").write_text(
            f"Metadata-Version: 2.4\nName: {distribution}\nVersion: 1.0\n",
            encoding="utf-8",
        )
        (dist_info / "direct_url.json").write_text(
            (f'{{"url":"{direct_root.as_uri()}","dir_info":{{"editable":true}}}}\n'),
            encoding="utf-8",
        )
        (dist_info / "RECORD").write_text(
            (
                f"{pth_name},,\n"
                f"{dist_info.name}/METADATA,,\n"
                f"{dist_info.name}/direct_url.json,,\n"
                f"{dist_info.name}/RECORD,,\n"
            ),
            encoding="utf-8",
        )

    def _stale_checkout(self, tmp_path: Path) -> t.Triple[Path, Path, Path]:
        """Create the governed workspace, its member, and one stale checkout tree.

        Returns:
            The resulting ``t.Triple[Path, Path, Path]``.

        """
        workspace = self._locked_workspace(tmp_path)
        member = workspace / "sample-member"
        stale = tmp_path / "stale" / "sample-member"
        (stale / "src").mkdir(parents=True)
        return workspace, member, stale

    @staticmethod
    def _provenance_failure(workspace: Path, site_packages: Path) -> str:
        """Validate provenance once and return its typed failure message.

        Returns:
            The resulting ``str``.

        """
        result = FlextInfraWorkspaceEnvironmentProvenance.validate(
            workspace,
            metadata_paths=(str(site_packages),),
        )
        return tm.fail(result)

    def test_accepts_exact_live_editable(
        self,
        tmp_path: Path,
        site_packages: Path,
        *,
        ci_mode: bool,
    ) -> None:
        """Accept one exact PEP 610 editable installed from the live member."""
        workspace = self._locked_workspace(tmp_path)
        member = workspace / "sample-member"
        self._installed_editable(
            site_packages,
            "sample-member",
            direct_root=member,
            source_root=member / "src",
        )

        result = FlextInfraWorkspaceEnvironmentProvenance.validate(
            workspace,
            metadata_paths=(str(site_packages),),
        )

        if ci_mode:
            tm.that(tm.fail(result), has="CI dependency is editable")
        else:
            tm.ok(result, eq=1)

    def test_member_eligibility_reads_installed_editable_independently_of_ci(
        self,
        tmp_path: Path,
        site_packages: Path,
    ) -> None:
        """Changing the invocation context never changes a live source election."""
        workspace = self._locked_workspace(tmp_path)
        member = workspace / "sample-member"
        self._installed_editable(
            site_packages,
            "sample-member",
            direct_root=member,
            source_root=member / "src",
        )
        ci = config.Infra.codegen.make.ci
        for token in ("", ci.value):
            with u.Tests.env_vars_context(env_vars={ci.variable: token}):
                selected = tm.ok(
                    FlextInfraWorkspaceEnvironmentProvenance.editable_members(
                        workspace,
                        metadata_paths=(str(site_packages),),
                    ),
                )
            tm.that(tuple(item.path for item in selected), eq=(Path("sample-member"),))

    @pytest.mark.parametrize(
        "layout", ["package", "namespace", "multiple", "hatch-sources"]
    )
    def test_editable_path_must_expose_declared_package_sources(
        self,
        installed_artifact_consumer: Path,
        layout: str,
    ) -> None:
        """Authenticate native backend paths and reject a case-local docs-only path."""
        root = installed_artifact_consumer
        if layout != "package":
            roots = (root / "left", root / "right")
            primary = u.Infra.project_package_name(root)
            package_names = (
                (primary, primary)
                if layout == "namespace"
                else (primary, f"{primary}_companion")
            )
            declarations = []
            for source_root, name in zip(roots, package_names, strict=True):
                package = source_root / name
                tm.ok(u.Cli.ensure_dir(package))
                if layout in {"multiple", "hatch-sources"}:
                    tm.ok(u.Cli.atomic_write_text_file(package / c.Infra.INIT_PY, ""))
                else:
                    tm.ok(u.Cli.atomic_write_text_file(package / "portion.py", ""))
                declarations.append(package.relative_to(root).as_posix())
            pyproject = root / c.PYPROJECT_FILENAME
            payload = u.Tests.toml_payload(pyproject.read_text(encoding="utf-8"))
            tool = u.Tests.toml_mapping(payload.get("tool", {}))
            hatch = u.Tests.toml_mapping(tool.get("hatch", {}))
            build = u.Tests.toml_mapping(hatch.get("build", {}))
            targets = u.Tests.toml_mapping(build.get("targets", {}))
            wheel = u.Tests.toml_mapping(targets.get("wheel", {}))
            declared_wheel = {**wheel, "packages": declarations}
            if layout == "hatch-sources":
                declared_wheel = {
                    key: value
                    for key, value in wheel.items()
                    if key not in {"packages", "include", "sources"}
                }
                declared_wheel["include"] = [
                    f"/{declaration}/**" for declaration in declarations
                ]
                declared_wheel["sources"] = dict(
                    zip(declarations, package_names, strict=True)
                )
            tm.ok(
                u.Cli.toml_write_mapping(
                    pyproject,
                    {
                        **payload,
                        "tool": {
                            **tool,
                            "hatch": {
                                **hatch,
                                "build": {
                                    **build,
                                    "targets": {
                                        **targets,
                                        "wheel": declared_wheel,
                                    },
                                },
                            },
                        },
                    },
                )
            )
            ci = config.Infra.codegen.make.ci
            setup = tm.ok(
                u.Tests.run_isolated_make(
                    ["setup"],
                    cwd=root,
                    env={ci.variable: ci.local_value},
                )
            )
            tm.that(
                u.Cli.process_succeeded(setup.outcome),
                eq=True,
                msg=setup.stdout + setup.stderr,
            )
        locations = tm.ok(
            u.Cli.run_raw(
                [
                    str(u.Infra.runtime_python(root)),
                    "-c",
                    (
                        "import json, sysconfig; "
                        "print(json.dumps([sysconfig.get_path('purelib')]))"
                    ),
                ],
                cwd=root,
            )
        )
        tm.that(
            u.Cli.process_succeeded(locations.outcome),
            eq=True,
            msg=locations.stdout + locations.stderr,
        )
        metadata_paths = t.Infra.STR_SEQ_ADAPTER.validate_json(locations.stdout)
        repository = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root)
        ).repository
        installed = u.installed_distributions(
            name=repository.distribution,
            path=metadata_paths,
        )
        tm.that(len(installed), eq=1)
        direct_url = installed[0].read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        tm.that(direct_url is not None, eq=True)
        if direct_url is None:
            pytest.fail("native editable installation has no PEP 610 receipt")
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(direct_url, strict=True)
        tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
                repository,
                root,
                installed[0],
                receipt,
            ),
        )
        inventory = installed[0].files
        tm.that(inventory is not None, eq=True)
        if inventory is None:
            pytest.fail("installed editable has no file inventory")
        pth_files = tuple(
            Path(str(installed[0].locate_file(item)))
            for item in inventory
            if str(item).endswith(".pth")
        )
        tm.that(len(pth_files), eq=1)
        docs = root / "docs"
        tm.ok(u.Cli.ensure_dir(docs))
        tm.ok(u.Cli.atomic_write_text_file(pth_files[0], f"{docs}\n"))
        tm.fail(
            FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
                repository,
                root,
                installed[0],
                receipt,
            ),
            has="pth exposes no declared package",
        )

    def test_installed_bindings_do_not_admit_executable_declarations(
        self,
        installed_artifact_consumer: Path,
    ) -> None:
        """Real installation bindings survive unrelated defects."""
        root = installed_artifact_consumer
        package_name = u.Infra.project_package_name(root)
        source = root / "src" / package_name / c.Infra.INIT_PY
        original = source.read_text(encoding=c.DEFAULT_ENCODING)
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                original
                + "\ndef producer():\n"
                + "    return 'installed native producer'\n",
            ),
        )
        consumer = (
            "import importlib, pathlib, sys\n"
            "import yaml\n"
            "from flext_infra import m\n"
            "from flext_infra.workspace import "
            "FlextInfraWorkspaceEnvironmentProvenance as environment\n"
            "from flext_infra.workspace.native_reference import "
            "FlextInfraWorkspaceNativeReference as producer\n"
            "root = pathlib.Path(sys.argv[1])\n"
            "module = importlib.import_module(sys.argv[2])\n"
            "reference = producer.capture((m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "yaml.safe_load.__module__ = None\n"
            "module.producer.__code__ = module.producer.__code__.replace("
            "co_filename='<unbound producer>')\n"
            "environment.validate(root).unwrap()\n"
            "observed = producer.capture((m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "rejected = producer.compare(observed, reference)\n"
            "assert rejected.failure, rejected\n"
            "assert module.producer.__qualname__ in rejected.error, rejected.error\n"
        )
        process = tm.ok(
            u.Cli.run_raw(
                [
                    str(u.Infra.runtime_python(root)),
                    "-c",
                    consumer,
                    str(root),
                    package_name,
                ],
                cwd=root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )

    def test_frozen_member_remains_a_library_when_its_checkout_is_present(
        self,
        tmp_path: Path,
        site_packages: Path,
    ) -> None:
        """A native noneditable PEP 610 receipt authorizes no member mutation."""
        workspace = self._locked_workspace(tmp_path)
        member = workspace / "sample-member"
        self._installed_editable(
            site_packages,
            "sample-member",
            direct_root=member,
            source_root=member / "src",
        )
        direct_url = site_packages / "sample_member-1.0.dist-info/direct_url.json"
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(direct_url.read_bytes())
        tm.that(receipt.dir_info is not None, eq=True)
        if receipt.dir_info is not None:
            frozen = receipt.model_copy(
                update={
                    "dir_info": receipt.dir_info.model_copy(update={"editable": False}),
                },
            )
            direct_url.write_text(frozen.model_dump_json(), encoding=c.DEFAULT_ENCODING)
        selected = tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.editable_members(
                workspace,
                metadata_paths=(str(site_packages),),
            ),
        )
        tm.that(selected, empty=True)

    def test_rejects_stale_direct_url(
        self,
        tmp_path: Path,
        site_packages: Path,
        *,
        ci_mode: bool,
    ) -> None:
        """Reject an editable whose direct URL targets an obsolete checkout."""
        workspace, member, stale = self._stale_checkout(tmp_path)
        self._installed_editable(
            site_packages,
            "sample-member",
            direct_root=stale,
            source_root=member / "src",
        )
        error = self._provenance_failure(workspace, site_packages)
        if ci_mode:
            tm.that(error, has="CI dependency is editable")
        else:
            tm.that(error, has="direct_url mismatch")
            tm.that(error, has=f"expected={member}")
            tm.that(error, has=f"actual={stale}")

    def test_rejects_stale_pth_source(
        self,
        tmp_path: Path,
        site_packages: Path,
        *,
        ci_mode: bool,
    ) -> None:
        """Reject an editable path file that exposes an obsolete source tree."""
        workspace, member, stale = self._stale_checkout(tmp_path)
        self._installed_editable(
            site_packages,
            "sample-member",
            direct_root=member,
            source_root=stale / "src",
        )
        error = self._provenance_failure(workspace, site_packages)
        if ci_mode:
            tm.that(error, has="CI dependency is editable")
        else:
            tm.that(error, has="pth mismatch")
            tm.that(error, has=f"expected_root={member}")
            tm.that(error, has=f"actual={stale / 'src'}")

    def test_rejects_missing_distribution(
        self,
        tmp_path: Path,
        site_packages: Path,
    ) -> None:
        """Fail loud when a declared editable distribution is not installed."""
        workspace = self._locked_workspace(tmp_path)
        site_packages.mkdir()

        error = self._provenance_failure(workspace, site_packages)
        tm.that(error, has="distribution")
        tm.that(error, has="sample-member")

    def _locked_workspace(self, tmp_path: Path) -> Path:
        """Declare a virtual root and commit its member's exact native gitlink.

        Returns:
            The governed workspace root.

        """
        workspace = self._workspace(tmp_path / "workspace")
        member = workspace / "sample-member"
        u.Tests.commit_git_changes(member, "declare member ledger route")
        u.Tests.WorktreeFixture.attach_submodule(
            workspace,
            member,
            distribution="sample-member",
            relative_path="sample-member",
        )
        manifest = tm.ok(u.Infra.load_workspace_manifest(workspace))[0]
        repository = u.Tests.repository_ref(
            "sample-member",
            path=Path("sample-member"),
        ).model_copy(update={"checkout": c.Infra.CheckoutKind.SUBMODULE.value})
        declared = manifest.model_copy(
            update={
                "repository": manifest.repository.model_copy(update={"package": False}),
                "members": (repository,),
            },
        )
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(workspace),
                declared.model_dump(mode="json"),
            ),
        )
        lock = self._lock_path(workspace)
        relative = Path(os.path.relpath(member, lock.parent)).as_posix()
        lock.write_text(
            '[[package]]\nname = "sample-member"\nversion = "1.0"\n'
            f'source = {{ editable = "{relative}" }}\n',
            encoding="utf-8",
        )
        u.Tests.commit_git_changes(workspace, "declare locked workspace")
        return workspace

    def _locked_verdict(
        self,
        workspace: Path,
        *,
        direct_root: Path | None = None,
        source_root: Path | None = None,
        receipt: m.Infra.DirectUrlReceipt | None = None,
    ) -> p.Result[int]:
        """Read real distribution metadata without changing the active environment.

        Returns:
            The public locked-provenance verdict.

        """
        member = workspace / "sample-member"
        with TemporaryDirectory(dir=prefix) as temporary:
            site_packages = Path(temporary) / "site-packages"
            self._installed_editable(
                site_packages,
                "sample-member",
                direct_root=member if direct_root is None else direct_root,
                source_root=Path(prefix) if source_root is None else source_root,
            )
            build_origin = (
                m.Infra.DirectUrlReceipt(
                    url=(member if direct_root is None else direct_root).as_uri(),
                    dir_info=m.Infra.DirectUrlDirectoryInfo(),
                )
                if receipt is None
                else receipt
            )
            direct_url = (
                site_packages / "sample_member-1.0.dist-info" / "direct_url.json"
            )
            direct_url.write_text(
                build_origin.model_dump_json(),
                encoding="utf-8",
            )
            return FlextInfraWorkspaceEnvironmentProvenance.validate_locked(
                workspace,
                metadata_paths=(str(site_packages),),
            )

    @pytest.mark.parametrize(
        ("root_name", "branch"),
        [("candidate one", "integration/alpha"), ("candidate-two", "release/beta")],
    )
    def test_locked_accepts_declared_workspace_gitlink(
        self,
        tmp_path: Path,
        root_name: str,
        branch: str,
    ) -> None:
        """A noneditable local build retains its declared immutable gitlink proof."""
        workspace = self._locked_workspace(tmp_path / root_name)
        u.Tests.git_run(workspace / "sample-member", "checkout", "-b", branch)
        tm.ok(self._locked_verdict(workspace), eq=1)

    @pytest.mark.parametrize("surface", ["direct_url", "pth"])
    def test_locked_rejects_stale_build_identity(
        self,
        tmp_path: Path,
        surface: str,
    ) -> None:
        """The locked-local build retains origin and environment path confinement."""
        workspace = self._locked_workspace(tmp_path)
        stale = tmp_path / "stale"
        stale.mkdir()
        result = self._locked_verdict(
            workspace,
            direct_root=stale if surface == "direct_url" else None,
            source_root=stale if surface == "pth" else None,
        )
        diagnostic = (
            "direct_url mismatch"
            if surface == "direct_url"
            else "CI artifact exposes an external source path"
        )
        tm.that(tm.fail(result), has=diagnostic)

    @pytest.mark.parametrize(
        "defect",
        ["editable", "missing_directory", "vcs", "remote", "relative"],
    )
    def test_locked_rejects_invalid_workspace_build_receipt(
        self,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """A declared member cannot authorize editable or fabricated build metadata."""
        workspace = self._locked_workspace(tmp_path)
        member = workspace / "sample-member"
        identity = tm.ok(
            u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=member)),
        )
        receipt = m.Infra.DirectUrlReceipt(
            url=(
                u.Tests.WorktreeFixture.governed_repository_url("sample-member")
                if defect == "remote"
                else "file:sample-member"
                if defect == "relative"
                else member.as_uri()
            ),
            dir_info=(
                None
                if defect == "missing_directory"
                else m.Infra.DirectUrlDirectoryInfo(editable=defect == "editable")
            ),
            vcs_info=(
                m.Infra.DirectUrlVcsInfo(vcs="git", commit_id=identity.head_oid)
                if defect == "vcs"
                else None
            ),
        )
        result = self._locked_verdict(workspace, receipt=receipt)
        tm.that(
            tm.fail(result),
            has=(
                "CI dependency is editable"
                if defect == "editable"
                else "direct_url mismatch"
            ),
        )

    def test_locked_accepts_declared_noneditable_directory(
        self,
        tmp_path: Path,
    ) -> None:
        """Directory locks require the same declaration and committed Git identity."""
        workspace = self._locked_workspace(tmp_path)
        manifest = tm.ok(u.Infra.load_workspace_manifest(workspace))[0]
        declared = manifest.model_copy(
            update={
                "members": (
                    manifest.members[0].model_copy(update={"editable": False}),
                ),
            },
        )
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(workspace),
                declared.model_dump(mode="json"),
            ),
        )
        lock = self._lock_path(workspace)
        lock.write_text(
            lock.read_text(encoding="utf-8").replace("editable =", "directory ="),
            encoding="utf-8",
        )
        u.Tests.commit_git_changes(workspace, "declare noneditable local source")
        tm.ok(self._locked_verdict(workspace), eq=len(declared.members))

    def test_locked_accepts_standalone_root_build(
        self,
        tmp_path: Path,
    ) -> None:
        """A standalone root authenticates its own noneditable build of the checkout."""
        root = tmp_path / "standalone"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "sample-root",
            beads=u.Tests.BeadsIdentity(
                workspace="sample-root-workspace",
                database="sample-root-database",
                issue_prefix="sample-root-prefix",
            ),
        )
        manifest = tm.ok(u.Infra.load_workspace_manifest(root))[0]
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(root),
                manifest.model_copy(
                    update={
                        "repository": manifest.repository.model_copy(
                            update={"editable": True},
                        ),
                    },
                ).model_dump(mode="json"),
            ),
        )
        lock = self._lock_path(root)
        relative = Path(os.path.relpath(root, lock.parent)).as_posix()
        lock.write_text(
            '[[package]]\nname = "sample-root"\nversion = "1.0"\n'
            f'source = {{ editable = "{relative}" }}\n',
            encoding="utf-8",
        )
        u.Tests.commit_git_changes(root, "declare standalone root lock")
        with TemporaryDirectory(dir=prefix) as temporary:
            site_packages = Path(temporary) / "site-packages"
            self._installed_editable(
                site_packages,
                "sample-root",
                direct_root=root,
                source_root=Path(prefix),
            )
            (
                site_packages / "sample_root-1.0.dist-info" / "direct_url.json"
            ).write_text(
                m.Infra.DirectUrlReceipt(
                    url=root.as_uri(),
                    dir_info=m.Infra.DirectUrlDirectoryInfo(),
                ).model_dump_json(),
                encoding="utf-8",
            )
            tm.ok(
                FlextInfraWorkspaceEnvironmentProvenance.validate_locked(
                    root,
                    metadata_paths=(str(site_packages),),
                ),
                eq=1,
            )

    @pytest.mark.parametrize(
        ("defect", "diagnostic"),
        [
            ("lock_path", "locked workspace source differs"),
            ("origin", "workspace checkout identity differs"),
            ("dirty", "workspace checkout identity differs"),
            ("head", "workspace checkout differs from locked gitlink"),
            ("gitlink", "governed gitlink is absent"),
            ("staged_gitlink", "workspace checkout differs from locked gitlink"),
            ("checkout", "workspace member has no declared gitlink checkout"),
            ("editable_policy", "locked workspace source differs"),
            ("undeclared", "CI member needs a locked artifact source"),
            ("standalone", "CI member needs a locked artifact source"),
        ],
    )
    def test_locked_rejects_unproven_local_source(
        self,
        tmp_path: Path,
        defect: str,
        diagnostic: str,
    ) -> None:
        """A local source cannot replace declared checkout and revision provenance."""
        workspace = self._locked_workspace(tmp_path)
        member = workspace / "sample-member"
        if defect == "lock_path":
            lock = self._lock_path(workspace)
            relative = Path(os.path.relpath(member, lock.parent)).as_posix()
            lock.write_text(
                lock.read_text(encoding="utf-8").replace(
                    f'editable = "{relative}"',
                    'editable = "elsewhere"',
                ),
                encoding="utf-8",
            )
        elif defect == "origin":
            u.Tests.git_run(
                member,
                "remote",
                "set-url",
                "origin",
                u.Tests.WorktreeFixture.governed_repository_url("different-provider"),
            )
        elif defect in {"dirty", "head"}:
            (member / "changed.txt").write_text("changed\n", encoding="utf-8")
            if defect == "head":
                u.Tests.commit_git_changes(member, "advance member without gitlink")
        elif defect == "gitlink":
            u.Tests.git_run(
                workspace,
                "update-index",
                "--force-remove",
                "sample-member",
            )
        elif defect == "staged_gitlink":
            root_identity = tm.ok(
                u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=workspace)),
            )
            tm.ok(
                u.Infra.git_update_index_gitlink(
                    m.Infra.GitUpdateIndexGitlinkRequest(
                        repo_root=workspace,
                        oid=root_identity.head_oid,
                        relative_path="sample-member",
                    ),
                ),
            )
        else:
            manifest = tm.ok(u.Infra.load_workspace_manifest(workspace))[0]
            if defect == "standalone":
                manifest = manifest.model_copy(
                    update={
                        "repository": manifest.repository.model_copy(
                            update={"role": c.Infra.MakeProfile.STANDALONE},
                        ),
                    },
                )
            elif defect in {"checkout", "editable_policy"}:
                manifest = manifest.model_copy(
                    update={
                        "members": (
                            manifest.members[0].model_copy(
                                update=(
                                    {"checkout": c.Infra.CheckoutKind.INDEPENDENT.value}
                                    if defect == "checkout"
                                    else {"editable": False}
                                ),
                            ),
                        ),
                    },
                )
            else:
                manifest = manifest.model_copy(update={"members": ()})
            tm.ok(
                u.Cli.yaml_dump(
                    u.Infra.workspace_manifest_path(workspace),
                    manifest.model_dump(mode="json"),
                ),
            )
        tm.that(tm.fail(self._locked_verdict(workspace)), has=diagnostic)

    @pytest.mark.parametrize(
        "defect",
        ["none", "revision", "remote", "vcs", "editable", "missing"],
    )
    def test_locked_external_git_keeps_exact_revision(
        self,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """An external noneditable provider still requires its locked Git receipt."""
        workspace = self._locked_workspace(tmp_path)
        manifest = tm.ok(u.Infra.load_workspace_manifest(workspace))[0]
        tm.ok(
            u.Cli.yaml_dump(
                u.Infra.workspace_manifest_path(workspace),
                manifest.model_copy(update={"members": ()}).model_dump(mode="json"),
            ),
        )
        identity = tm.ok(
            u.Infra.git_identity(
                m.Infra.GitRepoRequest(repo_root=workspace / "sample-member"),
            ),
        )
        url = u.Tests.WorktreeFixture.governed_repository_url("sample-member")
        self._lock_path(workspace).write_text(
            '[[package]]\nname = "sample-member"\nversion = "1.0"\n'
            f'source = {{ git = "{url}#{identity.head_oid}" }}\n',
            encoding="utf-8",
        )
        with TemporaryDirectory(dir=prefix) as temporary:
            site_packages = Path(temporary) / "site-packages"
            self._installed_editable(
                site_packages,
                "sample-member",
                direct_root=workspace / "sample-member",
                source_root=Path(prefix),
            )
            receipt = m.Infra.DirectUrlReceipt(
                url=(
                    u.Tests.WorktreeFixture.governed_repository_url(
                        "different-provider",
                    )
                    if defect == "remote"
                    else url
                ),
                dir_info=(
                    m.Infra.DirectUrlDirectoryInfo(editable=True)
                    if defect == "editable"
                    else None
                ),
                vcs_info=m.Infra.DirectUrlVcsInfo(
                    vcs="hg" if defect == "vcs" else "git",
                    commit_id=(
                        "0" * len(identity.head_oid)
                        if defect == "revision"
                        else identity.head_oid
                    ),
                ),
            )
            direct_url = (
                site_packages / "sample_member-1.0.dist-info" / "direct_url.json"
            )
            if defect == "missing":
                direct_url.unlink()
            else:
                direct_url.write_text(
                    dumps(receipt.model_dump(mode="json")),
                    encoding="utf-8",
                )
            result = FlextInfraWorkspaceEnvironmentProvenance.validate_locked(
                workspace,
                metadata_paths=(str(site_packages),),
            )
        if defect == "none":
            tm.ok(result, eq=1)
        else:
            diagnostic = (
                "CI dependency is editable"
                if defect == "editable"
                else "lacks PEP 610 provenance"
                if defect == "missing"
                else "origin differs from committed lock"
            )
            tm.that(tm.fail(result), has=diagnostic)
