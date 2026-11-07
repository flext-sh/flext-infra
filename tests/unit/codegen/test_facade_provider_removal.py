"""Removing a family provider from a consumer re-derives its generated facade.

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


class TestsFlextInfraFacadeProviderRemoval:
    """A generated facade never keeps a provider the family no longer declares."""

    @staticmethod
    def test_removed_provider_leaves_the_regenerated_facade(tmp_path: Path) -> None:
        """The previous projection names a deleted provider; the new one drops it.

        Premise: a consumer deleted ``_utilities/gone.py`` (zero-residue
        cutover). The generated lazy initializer and the generated facade still
        name ``FlextSampleUtilitiesGone`` from the previous run; regeneration
        must derive the facade from the providers that exist, not resolve the
        stale base of its own previous projection — including through a class
        nested inside the stale holder.
        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        directory = package / family.directory
        directory.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (directory / "kept.py").write_text(
            '"""Provider that stays."""\n\n'
            "class FlextSampleUtilitiesKept:\n"
            "    KEPT = 'kept'\n\n"
            "__all__ = ['FlextSampleUtilitiesKept']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (directory / c.Infra.INIT_PY).write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '"""Previous lazy projection."""\n\n'
            "from __future__ import annotations\n\n"
            "from types import MappingProxyType\n"
            "from typing import TYPE_CHECKING\n\n"
            "from flext_core.lazy import install_lazy_exports\n\n"
            "if TYPE_CHECKING:\n"
            "    from flext_sample._utilities.gone import FlextSampleUtilitiesGone\n"
            "    from flext_sample._utilities.kept import FlextSampleUtilitiesKept\n\n"
            "__all__: tuple[str, ...] = (\n"
            "    'FlextSampleUtilitiesGone',\n"
            "    'FlextSampleUtilitiesKept',\n"
            ")\n\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    MappingProxyType({\n"
            "        'FlextSampleUtilitiesGone': '.gone',\n"
            "        'FlextSampleUtilitiesKept': '.kept',\n"
            "    }),\n"
            "    public_exports=__all__,\n"
            ")\n",
            encoding=c.DEFAULT_ENCODING,
        )
        facade = package / c.Infra.UTILITIES_PY
        facade.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '"""Previous facade projection."""\n\n'
            "from __future__ import annotations\n\n"
            "from flext_sample._utilities import (\n"
            "    FlextSampleUtilitiesGone,\n"
            "    FlextSampleUtilitiesKept,\n"
            ")\n\n\n"
            "class FlextSampleUtilities:\n"
            "    class Sample(FlextSampleUtilitiesGone, FlextSampleUtilitiesKept):\n"
            "        class Inner(FlextSampleUtilitiesKept):\n"
            "            pass\n\n\n"
            "u = FlextSampleUtilities\n"
            "__all__ = ['FlextSampleUtilities', 'u']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            rendered = tm.ok(
                u.Infra.facade_component_source(
                    rope.rope_project,
                    facade,
                    directory,
                    family=c.Infra.FacadeFamily.U,
                )
            )
        ast.parse(rendered)
        tm.that(rendered, has="FlextSampleUtilitiesKept")
        tm.that("FlextSampleUtilitiesGone" in rendered, eq=False)
