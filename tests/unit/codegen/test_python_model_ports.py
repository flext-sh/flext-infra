"""The static model's opaque cache preserves its writable protocol contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import p, tm, u


class TestsFlextInfraPythonModelPorts:
    """Exercise the real parser through a caller-owned, typed mutable cache."""

    @staticmethod
    def test_parser_populates_the_injected_cache_once(tmp_path: Path) -> None:
        """The shared port retains its identity and returns the cached facts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                source, "class Observed:\n    pass\n__all__ = ['Observed']\n"
            )
        )
        name = f"{package.name}.provider"
        with u.Infra.workspace_snapshot(root, (root,)) as snapshot:
            cache = snapshot.python_module_facts
            run: p.Infra.PythonModelRun = u.Infra.python_model_run(
                snapshot.engine, {name: source}, module_facts=cache
            )
            tm.that(run.modules is cache, eq=True)
            first = u.Infra.python_model_module_at(run, source, name)
            tm.that(len(cache), eq=1)
            tm.that(next(iter(cache.values())) is first, eq=True)
            second = u.Infra.python_model_module_at(run, source, name)
            tm.that(second is first, eq=True)
            tm.that(len(cache), eq=1)
