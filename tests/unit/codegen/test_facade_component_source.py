"""Behavior tests for composing a facade from its declared family providers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFacadeComponentSource:
    """Validate that the composed facade is built from the facade's own source."""

    @staticmethod
    def test_nested_namespace_from_family_keeps_facade_source(
        tmp_path: Path,
    ) -> None:
        """A nested namespace whose base lives in the family stays the facade's.

        Premise: inspecting the namespace's family bases must not rebind the
        facade resource. When it did, the composed text came from the last
        inspected provider module while the class layout came from the facade,
        splicing the facade header into the provider body.
        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        directory = package / family.directory
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (directory / c.Infra.INIT_PY).parent.mkdir(parents=True, exist_ok=True)
        (directory / c.Infra.INIT_PY).write_text(
            "from flext_sample_constants import FlextSampleConstantsBase\n"
            "__all__ = ['FlextSampleConstantsBase']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (directory / "base.py").write_text(
            '"""Provider body that must never become the facade."""\n\n'
            "class FlextSampleConstantsBase:\n"
            "    PROVIDER_ONLY = 'provider-only-marker'\n"
            "    PADDING = (\n"
            + "".join(f"        'line-{index}',\n" for index in range(40))
            + "    )\n\n"
            "__all__ = ['FlextSampleConstantsBase']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        facade = package / c.Infra.CONSTANTS_PY
        facade.write_text(
            '"""Sample facade."""\n\n'
            "from flext_sample._constants import FlextSampleConstantsBase\n\n\n"
            "class FlextSampleConstants:\n"
            "    class Sample(FlextSampleConstantsBase):\n"
            "        pass\n\n\n"
            "c = FlextSampleConstants\n"
            "__all__ = ['FlextSampleConstants', 'c']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            rendered = tm.ok(
                u.Infra.facade_component_source(
                    rope.rope_project,
                    facade,
                    directory,
                    family=c.Infra.FacadeFamily.C,
                )
            )
        ast.parse(rendered)
        tm.that(rendered, has="class FlextSampleConstants")
        tm.that("provider-only-marker" in rendered, eq=False)
