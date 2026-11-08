"""The deep-import rewrite never targets the importing module's own top package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodemodDeepImportOwnRoot:
    """A package's own modules keep deep imports; other packages' modules move."""

    @staticmethod
    def test_rewrite_spares_own_top_package_and_moves_other_packages(
        tmp_path: Path,
    ) -> None:
        """Rewrite only imports whose top package differs from the importer's."""
        root = u.Tests.mk_project(
            tmp_path,
            "deep-import",
            pyproject='[project]\nname = "deep-import"\nversion = "0.1.0"\n',
            with_src=True,
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / "deep_import"
        tests_root = root / c.Infra.DIR_TESTS
        sources = {
            package / c.Infra.INIT_PY: (
                "from deep_import.api import Api\n"
                "from deep_import.client import Client\n"
                "__all__ = ['Api', 'Client']\n"
            ),
            package / "client.py": "class Client:\n    pass\n",
            package / "services" / c.Infra.INIT_PY: (
                "from deep_import.services.runner import Runner\n__all__ = ['Runner']\n"
            ),
            package / "services" / "runner.py": "class Runner:\n    pass\n",
            package / "api.py": (
                "from deep_import.client import Client\n"
                "from deep_import.services.runner import Runner\n"
                "class Api:\n    parts = (Client, Runner)\n"
            ),
            tests_root / c.Infra.INIT_PY: (
                "from tests.support import Support\n__all__ = ['Support']\n"
            ),
            tests_root / "support.py": "class Support:\n    pass\n",
            tests_root / "helpers.py": (
                "from tests.support import Support\nHELPERS = (Support,)\n"
            ),
            tests_root / "unit" / c.Infra.INIT_PY: "",
            tests_root / "unit" / "test_client.py": (
                "from deep_import.client import Client\n"
                "from deep_import.services.runner import Runner\n"
                "PARTS = (Client, Runner)\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        own_root = (package / "api.py", tests_root / "helpers.py")
        consumer = tests_root / "unit" / "test_client.py"
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                root,
                fix=True,
                selection=("rewire-deep-import-to-package",),
                source_files=(*own_root, consumer),
            )
        )
        tm.that(
            {u.Infra.codemod_source_path(root, row.file) for row in report.entries},
            eq={consumer.resolve()},
        )
        for path in own_root:
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=sources[path])
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            eq=(
                "from deep_import import Client\n"
                "from deep_import.services import Runner\n"
                "PARTS = (Client, Runner)\n"
            ),
        )


__all__: list[str] = ["TestsFlextInfraCodemodDeepImportOwnRoot"]
