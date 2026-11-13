"""A class moved out of a family leaves its regenerated facade's exports.

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


class TestsFlextInfraFacadeForeignPublication:
    """A generated facade publishes only its owner, letter and family parts."""

    @staticmethod
    def test_moved_class_disappears_from_the_regenerated_facade(
        tmp_path: Path,
    ) -> None:
        """The previous projection re-exports a class now owned by a sibling.

        Premise: ``refactor move-module`` moved ``_utilities/client.py`` to
        ``application/client.py`` and rewired the generated facade's import.
        The application package now publishes ``FlextSampleClient``; the
        regenerated facade must neither re-export nor import it, while a
        re-exported family part stays published.
        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        directory = package / family.directory
        application = package / "application"
        for folder in (directory, application):
            folder.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (directory / "kept.py").write_text(
            '"""Provider that stays."""\n\n'
            "class FlextSampleUtilitiesKept:\n"
            "    KEPT = 'kept'\n\n"
            "__all__ = ['FlextSampleUtilitiesKept']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (directory / c.Infra.INIT_PY).write_text(
            "from flext_sample._utilities.kept import FlextSampleUtilitiesKept\n\n"
            "__all__ = ['FlextSampleUtilitiesKept']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (application / "client.py").write_text(
            '"""Orchestrator moved out of the family."""\n\n'
            "class FlextSampleClient:\n"
            "    NAME = 'client'\n\n"
            "__all__ = ['FlextSampleClient']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (application / c.Infra.INIT_PY).write_text(
            "from flext_sample.application.client import FlextSampleClient\n\n"
            "__all__ = ['FlextSampleClient']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        facade = package / c.Infra.UTILITIES_PY
        facade.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '"""Previous facade projection."""\n\n'
            "from __future__ import annotations\n\n"
            "from flext_sample._utilities import FlextSampleUtilitiesKept\n"
            "from flext_sample.application import FlextSampleClient\n\n\n"
            "class FlextSampleUtilities:\n"
            "    class Sample(FlextSampleUtilitiesKept):\n"
            "        pass\n\n\n"
            "u = FlextSampleUtilities\n"
            "__all__ = [\n"
            "    'FlextSampleClient',\n"
            "    'FlextSampleUtilities',\n"
            "    'FlextSampleUtilitiesKept',\n"
            "    'u',\n"
            "]\n",
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
        tm.that("FlextSampleClient" in rendered, eq=False)
        tm.that(rendered, has="FlextSampleUtilitiesKept")


__all__: list[str] = ["TestsFlextInfraFacadeForeignPublication"]
