"""Source base resolution of ``type(<class>)`` metaclass bases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraCodegenLazyInitMetaclassBase:
    """A metaclass base resolves externally and stays fail-loud when governed."""

    @staticmethod
    def _write_family(package_root: Path, base: str) -> None:
        family = package_root / "_typings"
        family.mkdir()
        family.joinpath(c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        family.joinpath("meta.py").write_text(
            "from typing import Protocol\n\n"
            "class FlextTestProjectLocal:\n"
            '    """Governed declaration."""\n\n'
            f"class FlextTestProjectProtocolMeta({base}):\n"
            '    """Metaclass derived from a class metaclass."""\n\n'
            '__all__ = ["FlextTestProjectLocal", "FlextTestProjectProtocolMeta"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        package_root.joinpath("typings.py").write_text(
            "from flext_test_project._typings.meta import (\n"
            "    FlextTestProjectProtocolMeta,\n"
            ")\n\n"
            "class FlextTestProjectTypings(FlextTestProjectProtocolMeta):\n"
            '    """Facade over the metaclass family."""\n\n'
            "t = FlextTestProjectTypings\n"
            '__all__ = ["FlextTestProjectTypings", "t"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

    @staticmethod
    def test_external_class_metaclass_base_resolves(tmp_path: Path) -> None:
        """``type(Protocol)`` resolves to the external metaclass and publishes."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        TestsFlextInfraCodegenLazyInitMetaclassBase._write_family(
            package_root, "type(Protocol)"
        )
        bases = u.Infra.runtime_evaluated_base_classes(
            repository_root, {}, (c.Infra.PYDANTIC_MODEL_IDENTITY,)
        )
        tm.that(bases, has=c.Infra.PYDANTIC_MODEL_IDENTITY)

    @staticmethod
    def test_governed_class_metaclass_base_fails_loud(tmp_path: Path) -> None:
        """A governed class's metaclass is never read from runtime."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        TestsFlextInfraCodegenLazyInitMetaclassBase._write_family(
            package_root, "type(FlextTestProjectLocal)"
        )
        with pytest.raises(TypeError, match="Unsupported metaclass base"):
            u.Infra.runtime_evaluated_base_classes(
                repository_root, {}, (c.Infra.PYDANTIC_MODEL_IDENTITY,)
            )
