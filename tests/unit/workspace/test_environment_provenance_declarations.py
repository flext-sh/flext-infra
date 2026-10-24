"""Behavior tests for environment provenance of native declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from tests import c, m, p, t, tm, u


class TestsFlextInfraWorkspaceEnvironmentProvenanceDeclarations:
    """Prove declaration, alias and descriptor identity against physical sources."""

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
    def test_changed_factory_source_preserves_private_values(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        supplier_kind: str,
        *,
        installed_layout: bool,
    ) -> None:
        """Changed factory source fails with its identity and no operand contents."""
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
            "assert str(source) in error, error\n"
            "assert 'private-material-must-not-appear' not in error\n"
            "assert not effects\n"
            "assert module.Payload('native').value == 'native'\n"
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
        """Inherited guards retain declarations and reject native changes."""
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
        *,
        inherited: bool,
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
        *,
        changed: bool,
    ) -> None:
        """Inherited accessors retain the physical supplier of their implementation."""
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
            self._materialize_editable_layout(root, layout)
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
        tm.ok(direct_url is not None)
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
        declaration = tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                root,
                repository,
            ),
        )
        tm.that(declaration.path, eq=(root / c.PYPROJECT_FILENAME).resolve())
        tm.that(
            declaration.content,
            eq=(root / c.PYPROJECT_FILENAME).read_bytes(),
        )
        inventory = installed[0].files
        tm.ok(inventory is not None)
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
        tm.fail(
            FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                root,
                repository,
            ),
            has="pth exposes no declared package",
        )

    @staticmethod
    def _materialize_editable_layout(root: Path, layout: str) -> None:
        """Declare real source roots through the existing native Hatch table."""
        roots = (root / "left", root / "right")
        primary = u.Infra.project_package_name(root)
        package_names = (
            (primary, primary)
            if layout == "namespace"
            else (primary, f"{primary}_companion")
        )
        declarations: list[str] = []
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
        wheel = tm.not_none(
            u.Cli.toml_mapping_path(
                payload, ("tool", "hatch", "build", "targets", "wheel")
            )
        )
        if layout == "hatch-sources":
            for key in ("packages", "include", "sources"):
                wheel.pop(key, None)
            wheel["include"] = [f"/{declaration}/**" for declaration in declarations]
            wheel["sources"] = dict(zip(declarations, package_names, strict=True))
        else:
            boundary_packages: t.JsonValueList = list(declarations)
            wheel["packages"] = boundary_packages
        tm.ok(u.Cli.toml_write_mapping(pyproject, payload))
