"""Runtime-base discovery across native, provider and re-exported class lineage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, tm, u


class TestsFlextInfraRuntimeEvaluatedNativeBaseClasses:
    """Native ancestry, provider metadata and aliases keep declared lineage."""

    @staticmethod
    @pytest.mark.parametrize("propagated", [False, True])
    def test_sibling_declaration_requires_a_propagated_native_import(
        tmp_path: Path, *, propagated: bool
    ) -> None:
        """A Rope move repairs consumers; an unrelated sibling cannot export it."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        legacy = package / "legacy.py"
        moved = package / "moved.py"
        consumer = package / "consumer.py"
        target = "class Target:\n    marker = 'preserved'\n"
        legacy.write_text(
            (target if propagated else "") + "class Existing: pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        moved.write_text("" if propagated else target, encoding=c.DEFAULT_ENCODING)
        consumer.write_text(
            "from .legacy import Target\nclass Consumer(Target): pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(root) as workspace:
            if propagated:
                tm.that(
                    u.Infra.move_class(
                        m.Infra.ClassMoveRequest(
                            rope_project=workspace.rope_project,
                            source_file=legacy,
                            target_file=moved,
                            class_name="Target",
                            line=1,
                            apply=True,
                        )
                    ),
                    eq=moved,
                )
            before = {path: path.read_bytes() for path in (legacy, moved, consumer)}
            sources = {
                f"{package.name}.{path.stem}": (
                    path,
                    path.read_text(encoding=c.DEFAULT_ENCODING),
                )
                for path in (moved, consumer)
            }
            reference = m.Infra.SourceClassReference(
                target=f"{package.name}.consumer",
                attributes=("Consumer",),
                qualified_base=f"{package.name}.consumer.Consumer",
            )
            if propagated:
                tm.that(
                    u.Infra.source_class_order(
                        workspace.rope_project, sources, (reference,)
                    ),
                    eq=(reference.qualified_base,),
                )
            else:
                with pytest.raises(ValueError, match="does not declare Target"):
                    u.Infra.source_class_order(
                        workspace.rope_project, sources, (reference,)
                    )
            tm.that({path: path.read_bytes() for path in before}, eq=before)
        probe = (
            f"from {package.name}.consumer import Consumer\nprint(Consumer.marker)\n"
        )
        if propagated:
            tm.that(
                u.Tests.run_lazy_init_probe(probe, python_paths=(str(package.parent),)),
                eq=["preserved"],
            )
        else:
            with pytest.raises(AssertionError, match="cannot import name 'Target'"):
                u.Tests.run_lazy_init_probe(probe, python_paths=(str(package.parent),))
