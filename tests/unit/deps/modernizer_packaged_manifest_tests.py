"""Modernization preserves the distribution roots declared by the project.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, main
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class TestsFlextInfraModernizerPackagedManifest:
    """Exercise declared data through the public modernizer."""

    @staticmethod
    def test_modernization_preserves_declared_data(
        infra_git_repo: Path,
    ) -> None:
        """A local dependency update retains the package's configuration data."""
        distribution = "flext-packaging-fixture"
        _ = u.Tests.standalone_workspace(infra_git_repo, distribution)
        data_dir = c.CONFIG_DIR_NAME
        project = u.Tests.project_spec(distribution).model_copy(
            update={"packaged_data_paths": (data_dir,), "cli_module": False},
        )
        declaration = m.Infra.RepositoryDeltaSpec(project=project)
        tm.ok(
            u.Cli.yaml_dump(
                infra_git_repo / data_dir / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": declaration.model_dump(
                                mode="json", exclude_unset=True
                            )
                        }
                    }
                },
            ),
        )
        authored: t.JsonDict = {
            "only-include": ["assets"],
            "include": ["assets/**"],
            "exclude": ["**/*.secret"],
            "force-include": {"notice.txt": "notice.txt"},
        }
        tm.ok(
            u.Cli.atomic_write_text_file(
                infra_git_repo / "assets/data.yaml", "item: true\n"
            )
        )
        tm.ok(u.Cli.atomic_write_text_file(infra_git_repo / "notice.txt", "Notice\n"))
        manifest = infra_git_repo / c.PYPROJECT_FILENAME
        additions: t.MutableJsonMapping = {
            "tool": {
                "hatch": {
                    "build": {"targets": dict.fromkeys(("wheel", "sdist"), authored)}
                }
            },
        }
        manifest.write_text(
            manifest.read_text(encoding=c.DEFAULT_ENCODING)
            + u.Cli.toml_document_from_mapping(additions).as_string(),
            encoding=c.DEFAULT_ENCODING,
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
            tm.that(u.Tests.toml_list(selected["only-include"]), has="assets")
            tm.that(selected["include"], eq=authored["include"])
            tm.that(selected["exclude"], eq=authored["exclude"])
            tm.that(
                u.Tests.toml_mapping(selected["force-include"])["notice.txt"],
                eq="notice.txt",
            )
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
        tm.that(
            main([
                "codegen",
                "conform",
                "--root",
                str(infra_git_repo),
                "--what",
                "pyproject",
                "--scope",
                "self",
                "--mode",
                "apply",
            ]),
            eq=0,
        )
        source = (infra_git_repo / c.PYPROJECT_FILENAME).read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        for target in ("wheel", "sdist"):
            selected = u.Tests.toml_table_at(
                source,
                c.Infra.TOOL,
                "hatch",
                "build",
                "targets",
                target,
            )
            tm.that(selected["include"], eq=authored["include"])
            tm.that(u.Tests.toml_list(selected["exclude"]), has="**/*.secret")
            tm.that(u.Tests.toml_list(selected["only-include"]), has="assets")
            tm.that(
                u.Tests.toml_mapping(selected["force-include"])["notice.txt"],
                eq="notice.txt",
            )
