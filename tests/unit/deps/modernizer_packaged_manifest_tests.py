"""Modernization preserves the distribution roots declared by the project.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, main
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraModernizerPackagedManifest:
    """Exercise declared data through the public modernizer."""

    def test_modernization_preserves_declared_data(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A local dependency update retains the package's configuration data."""
        distribution = "flext-packaging-fixture"
        _ = u.Tests.standalone_workspace(infra_git_repo, distribution)
        data_dir = c.CONFIG_DIR_NAME
        _ = u.Tests.write_standalone_workspace_manifest(
            infra_git_repo,
            distribution,
            declaration=u.Tests.StandaloneManifestDeclaration(
                packaged_data_paths=(data_dir,),
                cli_module=False,
            ),
        )
        command = [
            c.Infra.CLI_GROUP_DEPS,
            "modernize",
            "--apply",
            "--repository-root",
            str(infra_git_repo),
            "--projects",
            ".",
        ]

        tm.that(main(command), eq=0)

        source = (infra_git_repo / c.PYPROJECT_FILENAME).read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        package_name = u.Tests.project_spec(distribution).package_name
        for target in ("wheel", "sdist"):
            selected = u.Tests.toml_table_at(
                source,
                c.Infra.TOOL,
                "hatch",
                "build",
                "targets",
                target,
            )
            tm.that(u.Tests.toml_list(selected["only-include"]), has=data_dir)
        wheel_sources = u.Tests.toml_table_at(
            source,
            c.Infra.TOOL,
            "hatch",
            "build",
            "targets",
            "wheel",
            "sources",
        )
        tm.that(wheel_sources[data_dir], eq=f"{package_name}/{data_dir}")
        tm.that(main(command), eq=0)
        tm.that(
            (infra_git_repo / c.PYPROJECT_FILENAME).read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
            eq=source,
        )
