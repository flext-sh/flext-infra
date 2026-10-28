"""Generated facade-alias-base rule drops bare runtime aliases used as bases.

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

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodemodFacadeAliasBaseRules:
    """A bare alias base outside the facade families and api.py is removed."""

    @staticmethod
    def _apply(project: Path, catalog: Path, source: Path) -> None:
        """Stage the project's facade-alias-base rule natively and apply it."""
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        (catalog / "utils").mkdir(parents=True, exist_ok=True)
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            documents = u.Infra.codemod_facade_alias_base_rules(snapshot, project)
        for identity, document in documents.items():
            tm.ok(u.Cli.yaml_dump(catalog / "rules" / f"{identity}.yml", document))
        tm.ok(
            u.Cli.capture([
                c.Infra.SG,
                "scan",
                "-c",
                str(catalog / "sgconfig.yml"),
                "--update-all",
                str(source),
            ])
        )

    @staticmethod
    def test_consumer_alias_bases_are_dropped(
        tmp_path: Path, infra_project_root: Path
    ) -> None:
        """Every bare alias base leaves; an attribute base through it stays."""
        source = tmp_path / "consumer.py"
        source.write_text(
            "from flext_core import m, s, t\n\n"
            "class Identity(t):\n    pass\n\n"
            "class Staging(s, t):\n    pass\n\n"
            "class Model(m.Value):\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodFacadeAliasBaseRules._apply(
            infra_project_root, tmp_path / "catalog", source
        )
        rewritten = source.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(rewritten, has="class Model(m.Value):", lacks=("(t)", "(s, t)"))
        tm.that(rewritten, has=("class Identity(", "class Staging("))

    @staticmethod
    def test_family_modules_and_api_compose_their_facades(
        tmp_path: Path, infra_project_root: Path
    ) -> None:
        """Facade composition inside a family directory and api.py is kept."""
        declaring = "from flext_core import t\n\nclass FlextDemoTypes(t):\n    pass\n"
        family = tmp_path / "_typings" / "base.py"
        family.parent.mkdir()
        api = tmp_path / c.Infra.API_PY
        for source in (family, api):
            source.write_text(declaring, encoding=c.DEFAULT_ENCODING)
            TestsFlextInfraCodemodFacadeAliasBaseRules._apply(
                infra_project_root, tmp_path / f"catalog-{source.stem}", source
            )
            tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=declaring)
