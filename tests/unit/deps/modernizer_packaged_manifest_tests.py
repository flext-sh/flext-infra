"""Modernization replaces generator-owned packaging tables from the declaration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

from flext_infra import FlextInfraCli, m
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class TestsFlextInfraModernizerPackagedManifest:
    """Exercise declared data through the public modernizer and generator."""

    @staticmethod
    def test_modernization_replaces_authored_build_targets(
        infra_git_repo: Path,
    ) -> None:
        """Modernize and gen agree: declared data survives, authored targets go.

        The pyproject ownership SSOT declares ``tool.hatch.build`` generator-owned,
        so authored target entries are replaced by the declared topology.
        """
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

        tm.that(FlextInfraCli.infra_main(command), eq=0)

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
            only_include = u.Tests.toml_list(selected["only-include"])
            tm.that(only_include, has=data_dir)
            tm.that(only_include, lacks="assets")
            tm.fail("include" in selected)
            tm.fail("exclude" in selected)
            tm.that(
                u.Tests.toml_mapping(selected.get("force-include", {})),
                lacks="notice.txt",
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
        tm.that(FlextInfraCli.infra_main(command), eq=0)
        tm.that(
            (infra_git_repo / c.PYPROJECT_FILENAME).read_text(
                encoding=c.DEFAULT_ENCODING,
            ),
            eq=source,
        )
        tm.that(
            FlextInfraCli.infra_main([
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
            tm.fail("include" in selected)
            tm.fail("exclude" in selected)
            tm.that(u.Tests.toml_list(selected["only-include"]), lacks="assets")
            tm.that(
                u.Tests.toml_mapping(selected.get("force-include", {})),
                lacks="notice.txt",
            )
