"""Real nested operand observations retain every elected source identity.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_core

from tests import m, t, tm, u


class TestsNativeReferenceEpoch:
    """Native container traversal preserves source and declaration change guards."""

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
