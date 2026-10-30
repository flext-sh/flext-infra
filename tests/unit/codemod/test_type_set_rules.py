"""Generated type-set rules rewire inline isinstance sets to their constants.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodemodTypeSetRules:
    """Each tuple-of-classes constant rewrites its exact inline set natively."""

    @staticmethod
    def _apply(project: Path, catalog: Path, source: Path) -> None:
        """Stage the project's type-set rules natively and apply them twice."""
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        (catalog / "utils").mkdir(parents=True, exist_ok=True)
        with u.Infra.codemod_workspace_snapshot(project) as snapshot:
            documents = u.Infra.type_set_rules(snapshot, project)
        for identity, document in documents.items():
            tm.ok(u.Cli.yaml_dump(catalog / "rules" / f"{identity}.yml", document))
        for _pass in range(2):
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
    def test_every_spelling_of_a_declared_set_reads_its_constant(
        tmp_path: Path, infra_project_root: Path
    ) -> None:
        """Stdlib, facade-alias, union and tuple spellings all become the constant."""
        source = tmp_path / "consumer.py"
        source.write_text(
            "import ast\n\n"
            "a = isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)\n"
            "b = isinstance(node, (c.Infra.Cst.FunctionDef, c.Infra.Cst.ClassDef))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodTypeSetRules._apply(
            infra_project_root, tmp_path / "catalog", source
        )
        rewritten = source.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(rewritten, has="a = isinstance(node, c.Infra.AST_FUNCTION_TYPES)")
        tm.that(rewritten, has="b = isinstance(node, c.Infra.CST_DEFINITION_TYPES)")

    @staticmethod
    def test_a_set_no_constant_declares_and_the_constants_family_stay(
        tmp_path: Path, infra_project_root: Path
    ) -> None:
        """A partial or larger set, and any constants module, are left unchanged."""
        partial = (
            "import ast\n\n"
            "a = isinstance(node, ast.FunctionDef | ast.Module)\n"
            "b = isinstance(node, (ast.Lambda, ast.Module, ast.FunctionDef))\n"
        )
        declaring = (
            "import ast\n\nX = isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)\n"
        )
        consumer = tmp_path / "consumer.py"
        consumer.write_text(partial, encoding=c.DEFAULT_ENCODING)
        constants = tmp_path / "constants.py"
        constants.write_text(declaring, encoding=c.DEFAULT_ENCODING)
        for source in (consumer, constants):
            TestsFlextInfraCodemodTypeSetRules._apply(
                infra_project_root, tmp_path / f"catalog-{source.stem}", source
            )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=partial)
        tm.that(constants.read_text(encoding=c.DEFAULT_ENCODING), eq=declaring)
