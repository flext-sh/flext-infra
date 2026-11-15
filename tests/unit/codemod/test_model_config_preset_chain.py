"""The model_config normalization feeds the preset rewrites it is elected with.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import ClassVar

from tests import c, tm, u


class TestsFlextInfraCodemodModelConfigPresetChain:
    """The authored theme rules converge a relaxed contract to its preset."""

    THEME_RULE_FILES: ClassVar[tuple[str, ...]] = (
        "pydantic-model-config-m-configdict-classvar.yml",
        "namespace-constant-classvar-import.yml",
        "namespace-constant-classvar-import-new.yml",
        "rewire-relaxed-contract-to-external-contract.yml",
    )
    RELAXED_CONTRACT: ClassVar[str] = (
        "from __future__ import annotations\n\n"
        "from flext_api import m\n\n\n"
        "class PkgModels:\n"
        "    class Thing(m.ContractModel):\n"
        '        model_config = m.ConfigDict(extra="ignore")\n\n'
        "        name: str\n"
    )
    THEME_UTIL_FILES: ClassVar[tuple[str, ...]] = (
        "pydantic-model-config-assignment.yml",
        "pydantic-namespace-constant.yml",
    )
    EXTERNAL_CONTRACT_LINES: ClassVar[tuple[str, ...]] = (
        "from __future__ import annotations",
        "from flext_api import m",
        "class PkgModels:",
        "    class Thing(m.ExternalContractModel):",
        "        name: str",
    )

    @staticmethod
    def test_relaxed_contract_reaches_the_external_contract_preset(
        tmp_path: Path, infra_project_root: Path
    ) -> None:
        """The ClassVar form the first rule writes is the form the rewrite reads."""
        cls = TestsFlextInfraCodemodModelConfigPresetChain
        authored = (
            infra_project_root
            / c.Infra.DEFAULT_SRC_DIR
            / c.Infra.PACKAGE_IMPORT_NAME
            / c.Infra.CODEMOD_CONFIG_RELPATH
        ).parent
        catalog = tmp_path / "catalog"
        rules = catalog / c.Cli.RULES_DIR_NAME
        rules.mkdir(parents=True)
        for name in cls.THEME_RULE_FILES:
            shutil.copyfile(authored / c.Cli.RULES_DIR_NAME / name, rules / name)
        utils = catalog / "utils"
        utils.mkdir()
        for name in cls.THEME_UTIL_FILES:
            shutil.copyfile(authored / "utils" / name, utils / name)
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": [c.Cli.RULES_DIR_NAME], "utilDirs": ["utils"]},
            )
        )
        source = tmp_path / "src" / "pkg" / "_models" / "sample.py"
        source.parent.mkdir(parents=True)
        source.write_text(cls.RELAXED_CONTRACT, encoding=c.DEFAULT_ENCODING)

        for _pass in range(2):
            tm.ok(
                u.Cli.capture([
                    c.Infra.SG,
                    "scan",
                    "-c",
                    str(catalog / "sgconfig.yml"),
                    "--update-all",
                    str(source.parent),
                ])
            )

        converged = source.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            tuple(line.rstrip() for line in converged.splitlines() if line.strip()),
            eq=cls.EXTERNAL_CONTRACT_LINES,
        )
