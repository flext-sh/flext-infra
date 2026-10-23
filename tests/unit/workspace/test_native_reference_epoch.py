"""Real nested operand observations retain every elected source identity.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_core
import pytest

from tests import m, p, t, tm, u


class TestsNativeReferenceEpoch:
    """Native container traversal preserves source and declaration change guards."""

    @staticmethod
    @pytest.mark.parametrize(
        "defect",
        [
            "none",
            "type",
            "default",
            "metadata",
            "cached_type",
            "params",
            "order",
            "executable",
            "writer",
            "unresolved",
        ],
    )
    def test_native_dataclass_metadata_projection_retains_negative_guards(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        defect: str,
    ) -> None:
        """Real project warmup changes only proved metadata annotation caches."""
        native_consumer(
            "from dataclasses import fields\n"
            "from rope.base.prefs import Prefs\n"
            "from rope.base.project import Project\n"
            "from pytoolconfig import PyToolConfig\n"
            "from typing import ForwardRef\n"
            "import pytest\n"
            "selection = (m.Infra.SourceClassReference(\n"
            "    target='rope.base.prefs', attributes=('Prefs',)),)\n"
            "cold = native.capture(selection).unwrap()\n"
            "constructor = Prefs.__init__\n"
            "original = repr(Prefs())\n"
            "project = Project(sys.argv[1], ropefolder=None)\n"
            "project.close()\n"
            "assert Prefs.__init__ is constructor\n"
            "assert repr(Prefs()) == original\n"
            "native.compare(cold, native.capture(selection).unwrap()).unwrap()\n"
            "field = next(item for item in fields(Prefs) if item.type is int)\n"
            "metadata = next(iter(field.metadata.values()))\n"
            "assert metadata._type is field.type\n"
            "defect = sys.argv[2]\n"
            "if defect == 'type':\n"
            "    field.type = str\n"
            "elif defect == 'default':\n"
            "    field.default += 1\n"
            "elif defect == 'metadata':\n"
            "    metadata.description = 'different native metadata'\n"
            "elif defect == 'cached_type':\n"
            "    metadata._type = bytes\n"
            "elif defect == 'params':\n"
            "    Prefs.__dataclass_params__.eq = not Prefs.__dataclass_params__.eq\n"
            "elif defect == 'order':\n"
            "    original_field = Prefs.__dataclass_fields__.pop(field.name)\n"
            "    Prefs.__dataclass_fields__[field.name] = original_field\n"
            "elif defect == 'executable':\n"
            "    Prefs.__init__ = lambda self: None\n"
            "elif defect == 'writer':\n"
            "    writer = PyToolConfig.__init__.__globals__['_gather_config_fields']\n"
            "    writer.__code__ = (lambda model: {}).__code__\n"
            "elif defect == 'unresolved':\n"
            "    field.type = ForwardRef('MissingNativeType')\n"
            "if defect == 'unresolved':\n"
            "    with pytest.raises(TypeError, "
            "match='unresolved native annotation'):\n"
            "        native.capture(selection)\n"
            "elif defect == 'none':\n"
            "    observed = native.capture(selection)\n"
            "    native.compare(cold, observed.unwrap()).unwrap()\n"
            "    authenticate('rope.base.prefs').unwrap()\n"
            "else:\n"
            "    observed = native.capture(selection)\n"
            "    if observed.success:\n"
            "        assert native.compare(cold, observed.value).failure\n"
            "    else:\n"
            "        assert observed.failure\n",
            str(tmp_path),
            defect,
        )

    @staticmethod
    def test_sdk_source_epoch_preserves_original_bytes(
        mod_workspace: t.DirectoryPath,
    ) -> None:
        """The real SDK capture retains raw bytes through its separate text view."""
        source = Path(tm.not_none(flext_core.__file__)).with_name("_settings.py")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        content = tm.not_none(original.content)
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (original,),
            projects=(
                m.Infra.CodemodBindingProject(
                    root=mod_workspace, source_paths=(), modules=("flext_core",)
                ),
            ),
        )
        retained = next(state for state in snapshot.states if state.path == source)
        epoch = u.Infra.codemod_source_epoch(snapshot)
        tm.that(retained is original, truth=True)
        tm.that(retained.content is content, truth=True)
        tm.that(epoch.contents[source] is content, truth=True)
        tm.that(epoch.sources[source].encode("utf-8"), eq=content)
        with u.Infra.codemod_binding_project(mod_workspace, epoch):
            tm.ok(
                u.Cli.atomic_verify_binary_file_states(
                    snapshot.states, nonsecret_source_paths=(source,)
                )
            )
        observed = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        tm.that(observed, eq=original)
        for label, body in (("captured", content), ("observed", observed.content)):
            payload = tm.not_none(body)
            _ = u.fetch_logger(__name__).info(
                f"SDK source byte witness: path={source}; stage={label}; "
                f"type={type(payload).__name__}; length={len(payload)}; "
                f"sha256={u.Cli.sha256_bytes(payload)}"
            )

    @staticmethod
    def test_nested_native_operands_retain_distinct_source_owners(
        real_python_package: t.DirectoryPath,
    ) -> None:
        """Slices and aliases retain both classes across independent captures."""
        root = real_python_package / "src"
        u.Tests.write_package_init(
            root / "test_pkg",
            "from types import GenericAlias\n"
            "class First:\n"
            "    value = 'first'\n"
            "class Second:\n"
            "    value = 'second'\n"
            "retained = tuple(\n"
            "    (slice(None, owner), GenericAlias(tuple, (owner,)))\n"
            "    for owner in (First, Second)\n"
            ")\n"
            "def execute(inputs=retained):\n"
            "    return inputs\n",
        )
        u.Tests.run_lazy_init_probe(
            """from flext_infra import m
from flext_tests import tm
from flext_infra.workspace.native_reference import (
    FlextInfraWorkspaceNativeReference as native,
)
import test_pkg as module
selection = (
    m.Infra.SourceClassReference(target=module.__name__, attributes=('execute',)),
)
before = tm.ok(native.capture(selection))
tm.that(tm.ok(native.compare(before, tm.ok(native.capture(selection)))), eq=True)
elected = {source[0] for source in before.sources}
tm.that('test_pkg::First' in elected, eq=True)
tm.that('test_pkg::Second' in elected, eq=True)
module.Second.value = 'changed'
tm.fail(native.compare(before, tm.ok(native.capture(selection))))
""",
            python_paths=(str(root),),
            cwd=real_python_package,
        )
