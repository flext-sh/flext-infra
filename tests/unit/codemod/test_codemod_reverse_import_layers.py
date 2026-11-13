"""Import-layer direction rules rank a src-layout module by its module name.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodemodReverseImportLayers:
    """Exercise the public reverse-import rule renderer on a src layout."""

    @staticmethod
    def project(root: Path) -> Path:
        """Provide a src-layout package with a services module.

        Returns:
            The services module path.

        """
        (root / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "layer-demo"\ndependencies = []\n',
            encoding="utf-8",
        )
        package = root / "src" / "layer_demo"
        services = package / "services"
        services.mkdir(parents=True)
        (package / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        (services / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        for name, owner, letter in (
            ("constants.py", "LayerDemoConstants", "c"),
            ("base.py", "LayerDemoServiceBase", "s"),
        ):
            (package / name).write_text(
                f'"""Family {letter}."""\n\nfrom __future__ import annotations\n\n\n'
                f'class {owner}:\n    """Family {letter}."""\n\n\n'
                f"{letter} = {owner}\n"
                f'__all__: list[str] = ["{owner}", "{letter}"]\n',
                encoding="utf-8",
            )
        module = services / "consulta.py"
        module.write_text(
            '"""Service module of the package."""\n\n'
            "from __future__ import annotations\n\n"
            "from layer_demo import c, p, s\n\n\n"
            'class LayerDemoConsulta(s):\n    """Service."""\n\n    VALOR = c\n',
            encoding="utf-8",
        )
        (root / "config").mkdir()
        (root / "config" / "codegen.yaml").write_text(
            "Infra:\n  codegen:\n    repository: {}\n",
            encoding="utf-8",
        )
        return module

    def test_src_layout_service_is_not_ranked_other(self, tmp_path: Path) -> None:
        """A service under src/ belongs to the services layer, never to other."""
        module = self.project(tmp_path)
        relative = module.relative_to(tmp_path).as_posix()
        with u.Infra.codemod_workspace_snapshot(tmp_path) as snapshot:
            documents = u.Infra.codemod_reverse_import_rules(snapshot, tmp_path)
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        prefix = f"{c.Infra.CODEMOD_REVERSE_IMPORT_SHAPE}{separator}layer_demo"
        other = f"{prefix}{separator}{c.Infra.IMPORT_LAW_OTHER_LAYER}"
        base = f"{prefix}{separator}base"
        tm.that(
            "**/src/layer_demo/base.py" in str(documents.get(base, {})),
            truth=True,
            msg=str(documents),
        )
        listed = str(documents.get(other, {}))
        tm.that(f"**/{relative}" in listed, truth=False, msg=listed)
