"""A re-export aggregator's ``__all__`` never claims single ownership.

Regression coverage: a generated TYPE_CHECKING re-export sidecar (e.g.
``tests/_exports_typing_facades.py`` in flext-core) imports many facades and
relists their class/alias names in its own ``__all__``. ``_resolve_family``
used to derive that module's ``expected_alias``/``expected_family`` from the
FIRST class/alias pair appearing in its ``__all__`` -- exactly as if the
aggregator itself declared that class. When a two-base root ``constants.py``
module (``class X(ExternalConstants, OwnProjectConstants)``) happened to be
the alphabetically-first re-export in the aggregator's list, the aggregator
tied the real owner's collision score and won the tie-break, dropping the
real ``constants.py``-owned class and alias entirely from the generated root
``__init__.py``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraLazyInitFamilyAggregator:
    """A multi-name aggregator module never wins family/alias ownership."""

    @staticmethod
    @pytest.mark.parametrize("part_name", ["FlextScope", "FlextScopePart03"])
    def test_private_split_preserves_public_wrapper(
        tmp_path: Path, part_name: str
    ) -> None:
        """Double-underscore implementation packages never displace their wrapper."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        context = package / "_models" / "_context"
        parts = context / "_scope"
        parts.mkdir(parents=True)
        (parts / "flextscope_part_03.py").write_text(
            f"class {part_name}:\n    marker = True\n__all__ = ['{part_name}']\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        (context / "_scope.py").write_text(
            "from ._scope import flextscope_part_03\n"
            f"class FlextScope(flextscope_part_03.{part_name}):\n    pass\n"
            "__all__ = ['FlextScope']\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}._models._context import FlextScope\n"
                f"from {package.name}._models._context._scope import "
                "FlextScope as Declared\n"
                "print(FlextScope is Declared)\n"
                "print(FlextScope.marker)\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["True", "True"],
        )

    @staticmethod
    def test_aggregator_sidecar_never_shadows_real_constants_owner(
        tmp_path: Path,
    ) -> None:
        """The real ``constants.py`` owner survives a re-export aggregator."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-test-agg",
            package_name="flext_test_agg",
        )
        package_root.joinpath("base.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestAggServiceBase:\n"
            "    pass\n\n"
            "s = FlextTestAggServiceBase\n\n"
            '__all__: list[str] = ["FlextTestAggServiceBase", "s"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestAggConstants:\n"
            "    pass\n\n"
            "c = FlextTestAggConstants\n\n"
            '__all__: list[str] = ["FlextTestAggConstants", "c"]\n',
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        # The aggregator sidecar: a generated-style TYPE_CHECKING re-export
        # module that forwards MANY facades' class/alias pairs through its
        # own __all__ without defining any of them itself. Its __all__ lists
        # "FlextTestAggConstants"/"c" FIRST -- the exact ordering that used
        # to make _resolve_family mistake it for the declared owner.
        package_root.joinpath("_exports_typing_aggregate.py").write_text(
            "from __future__ import annotations\n\n"
            "from .base import FlextTestAggServiceBase, s\n"
            "from .constants import FlextTestAggConstants, c\n\n"
            "__all__: list[str] = [\n"
            '    "FlextTestAggConstants",\n'
            '    "FlextTestAggServiceBase",\n'
            '    "c",\n'
            '    "s",\n'
            "]\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = package_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )

        # Decision 1: a static class alias imports its class and binds the letter.
        tm.that(
            generated.splitlines(),
            has=[
                f"    from {package_root.name}.constants import FlextTestAggConstants",
                "    c = FlextTestAggConstants",
            ],
        )
        tm.that(generated, lacks="FlextTestAggConstants as c")
        entries, _refs = u.Infra.lazy_import_mapping_source(generated)
        tm.that(dict(entries).get(".constants", ()), eq=("FlextTestAggConstants", "c"))
        tm.that(generated, lacks="_exports_typing_aggregate")
