"""Behavior tests for environment provenance of native callables.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from tests import c, m, p, tm, u


class TestsFlextInfraWorkspaceEnvironmentProvenanceCallables:
    """Prove generated and decorated callables authenticate their native origin."""

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
        *,
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
        """Passive preflight and cold authentication preserve original effects."""
        u.Tests.write_package_init(
            tmp_path / "effect_provider",
            "from dataclasses import dataclass\n"
            "from pathlib import Path\n"
            "import os\n"
            "effects = []\n"
            "marker = (Path(__file__).parent.parent / "
            "f'{__name__}.{os.getpid()}.effects')\n"
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
            "source_preflight(module.__name__).unwrap()\n"
            "if sys.argv[2] == 'code':\n"
            "    module.Payload.__init__.__code__ = "
            "module.Payload.__init__.__code__.replace(co_name='replaced')\n"
            "source_preflight(module.__name__).unwrap()\n"
            "assert tuple(module.effects) == before\n"
            "assert module.marker.read_bytes() == marker\n"
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
            "reference = provenance.capture("
            "(m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "defect = sys.argv[2]\n"
            "if defect == 'filename':\n"
            "    method = module.Payload.__init__\n"
            "    method.__code__ = method.__code__.replace(co_filename='<foreign>')\n"
            "elif defect == 'annotation':\n"
            "    module.Payload.__annotations__['value'] = Annotated[int, Ge(3)]\n"
            "elif defect == 'parameters':\n"
            "    module.Payload.__dataclass_params__ = module.ForeignParameters()\n"
            "observed = provenance.capture("
            "(m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
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
            "reference = provenance.capture("
            "(m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
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
            "observed = provenance.capture("
            "(m.Infra.SourceClassReference(target=module.__name__),))\n"
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
        """Source preflight pins generated providers without replaying their import."""
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
            "observed = source_preflight(module.__name__)\n"
            "observed.unwrap()\n"
            "assert not effect.exists(), 'source admission replayed the module'\n"
        )
        native_consumer(consumer, str(tmp_path))

    @staticmethod
    @pytest.mark.parametrize("defect", ["none", "defaults", "kwdefaults", "closure"])
    def test_installed_annotation_dataclass_retains_native_constructor_proof(
        native_consumer: p.Tests.NativeConsumer,
        defect: str,
    ) -> None:
        """Authenticate Protocol dataclasses and reject constructor-state drift."""
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
            "    tm.ok(result.success), result.error\n"
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

    @staticmethod
    def test_installed_bindings_do_not_admit_executable_declarations(
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
            "reference = producer.capture("
            "(m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
            "yaml.safe_load.__module__ = None\n"
            "module.producer.__code__ = module.producer.__code__.replace("
            "co_filename='<unbound producer>')\n"
            "environment.validate(root).unwrap()\n"
            "observed = producer.capture("
            "(m.Infra.SourceClassReference(target=module.__name__),)).unwrap()\n"
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
