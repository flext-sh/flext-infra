"""The generated-module native utility selects generator projections only.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodemodGeneratedModuleUtility:
    """A rule matching ``generated-module`` reaches generated files only."""

    @staticmethod
    def test_generated_module_utility_selects_only_generator_projections(
        tmp_path: Path,
    ) -> None:
        """Native ast-grep matches the header-first module, not an authored one."""
        predicate = c.Infra.CODEMOD_GENERATED_MODULE_UTILITY
        with u.Infra.codemod_workspace_snapshot(tmp_path) as snapshot:
            documents = u.Infra.codemod_native_utilities(
                snapshot, tmp_path, ("codemod_generated_module_utilities",)
            )
        catalog = tmp_path / "catalog"
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "utils" / f"{predicate}.yml", documents[predicate]
            )
        )
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "rules" / "probe.yml",
                {
                    "id": "probe",
                    "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                    "severity": "hint",
                    "rule": {"matches": predicate},
                },
            )
        )
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        sources = tmp_path / "sources"
        sources.mkdir()
        generated = sources / "generated.py"
        generated.write_text(
            f"{c.Infra.AUTOGEN_HEADER}\nvalue = 1\n", encoding=c.DEFAULT_ENCODING
        )
        authored = sources / "authored.py"
        authored.write_text(
            f"value = 1\n{c.Infra.AUTOGEN_HEADER}\n", encoding=c.DEFAULT_ENCODING
        )
        matched = tm.ok(
            u.Cli.capture([
                c.Infra.SG,
                "scan",
                "-c",
                str(catalog / "sgconfig.yml"),
                "--files-with-matches",
                str(sources),
            ])
        )
        tm.that(
            {Path(line).name for line in matched.splitlines()},
            eq={generated.name},
        )


__all__: list[str] = ["TestsFlextInfraCodemodGeneratedModuleUtility"]
