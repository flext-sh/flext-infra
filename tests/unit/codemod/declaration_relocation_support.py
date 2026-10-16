"""Shared source-seeding fixture for declaration-relocation contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, m, t, tm, u


class TestsFlextInfraDeclarationRelocationSupport:
    """Seed a real lazy-init package with relocatable family declarations."""

    @staticmethod
    def _seed(
        tmp_path: Path,
        *,
        body: str = "value: str = Field(default='payload')",
        base: str = "PayloadBase",
        variants: frozenset[str] = frozenset(),
    ) -> t.Pair[Path, t.MutableMappingKV[Path, str]]:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        stem = u.derive_class_stem(root.name)
        models = (
            package / u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
        )
        utilities = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        models.mkdir()
        utilities.mkdir()
        (models / "__init__.py").write_text("", encoding="utf-8")
        (utilities / "__init__.py").write_text("", encoding="utf-8")
        owner = f"{stem}ModelsPayload"
        source_owner = f"{stem}UtilitiesPayload"
        facade = f"{stem}Models"
        sources = {
            models / "payload.py": (
                '"""Authored payload family."""\nfrom __future__ import annotations\n'
                + (
                    "from pydantic import BaseModel as PayloadBase, Field\n"
                    if "existing_imports" in variants
                    else ""
                )
                + (
                    f"from {package.name}._utilities.payload import {source_owner}\n"
                    if "cycle" in variants
                    else ""
                )
                + f"class {owner}:\n    pass\n\n__all__ = ['{owner}']\n"
            ),
            package / "models.py": (
                f"from {package.name}._models.payload import {owner}\n"
                f"class {facade}"
                f"{'' if 'uncomposed' in variants else f'({owner})'}:\n"
                f"    pass\nm = {facade}\n"
                f"__all__ = ['{facade}', 'm']\n"
            ),
            utilities / "payload.py": (
                "from pydantic import BaseModel as PayloadBase, Field\n"
                "from pydantic_settings import BaseSettings\n"
                f"class {source_owner}:\n"
                f"    class Payload({base}):\n        {body}\n"
                f"\ndef local():\n    return {source_owner}.Payload()\n"
                + (
                    f"class {stem}StrayHolder:\n"
                    "    class Stray(PayloadBase):\n        value: str = 'stray'\n"
                    if "stray" in variants
                    else ""
                )
                + f"\n__all__ = ['{source_owner}']\n"
            ),
            package / "consumer.py": (
                "from __future__ import annotations\n"
                "from typing import Annotated, Literal\n"
                f"from {package.name}._utilities.payload "
                f"import {source_owner} as Original\n"
                "def build() -> 'Original.Payload':\n    return Original.Payload()\n"
                "text = 'Original.Payload'\n"
                "literal: Literal['Original.Payload']\n"
                "metadata: Annotated[str, 'Original.Payload']\n"
            ),
            package / "homonym.py": (
                "class Original:\n    class Payload:\n        pass\n"
                "value = Original.Payload()\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        if "uncomposed" not in variants:
            facade_path = package / c.Infra.MODELS_PY
            rendered = tm.not_none(
                u.Infra.render_utility_facade(package, family="m"),
            )
            sources[facade_path] = rendered
            facade_path.write_text(rendered, encoding="utf-8")
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        return root, sources

