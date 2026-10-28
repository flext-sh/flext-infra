"""Behavior tests for environment provenance of native callables.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from tests import c, m, p, tm, u


class TestsFlextInfraWorkspaceEnvironmentProvenanceCallables:
    """Prove generated and decorated callables authenticate their native origin."""

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
            "from flext_infra.workspace import "
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
            "from flext_infra.workspace import "
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
        package = u.Infra.declared_package_dir(
            metadata.package_name,
            search_paths=(str(member_root / c.Infra.DEFAULT_SRC_DIR),),
        )
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
            "from flext_infra.workspace import "
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
