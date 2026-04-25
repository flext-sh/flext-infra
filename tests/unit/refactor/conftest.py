"""Edge-case fixture factory for the rule lifecycle (Task 0.7).

Each fixture builds a minimal on-disk project under ``tmp_path`` that
demonstrates one of the nine canonical edge cases listed in plan §0.7.
The factory pattern keeps every fixture small (≤ 30 LOC) and avoids
27+ static scaffold files that would otherwise fan out across the
repository — refactor handlers consume the fixtures via the
``edge_case_<a..i>`` pytest fixtures returning
``(workspace_root: Path, target_files: tuple[Path, ...])``.

The 9 edge cases (per plan §0.7):
  a — integration project with dual MRO
  b — auto-generated ``__init__.py`` lazy chain
  c — flext-core bootstrap aliases (``mp`` / ``up`` / ``ta``)
  d — ``tests/`` tier with ``TestsFlext<Project><Tier>`` facade naming
  e — ``examples/`` and ``scripts/`` tiers
  f — ``services/*.py`` mixin tree
  g — ``FlextSettings`` subclass with ``auto_register`` decorator
  h — Pydantic ``@field_validator`` / ``@model_validator`` decorated method
  i — ``@override`` / ``@final`` decorated members
"""

from __future__ import annotations

import textwrap
from collections.abc import Sequence
from pathlib import Path

import pytest

EdgeCaseFixture = tuple[Path, tuple[Path, ...]]
"""``(workspace_root, target_files)`` returned by every edge-case fixture."""


def _scaffold_file(root: Path, relative: str, content: str) -> Path:
    """Create ``relative`` under ``root`` with dedented ``content``; return path."""
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return target


def _build_project(
    tmp_path: Path,
    project: str,
    files: Sequence[tuple[str, str]],
) -> EdgeCaseFixture:
    """Materialise ``project`` under ``tmp_path/<project>`` with ``files`` records.

    Each ``(relative_path, content)`` becomes a real file on disk; returns the
    workspace root plus the resolved file tuple in declaration order.
    """
    workspace = tmp_path
    project_root = workspace / project
    targets = tuple(
        _scaffold_file(project_root, relative, content) for relative, content in files
    )
    return workspace, targets


@pytest.fixture
def edge_case_a(tmp_path: Path) -> EdgeCaseFixture:
    """Integration project with dual MRO (tap-style protocol composition)."""
    return _build_project(
        tmp_path,
        "flext_alpha_a",
        (
            (
                "src/flext_alpha_a/protocols.py",
                """
                class _MeltanoProtocols:
                    pass


                class _BaseProtocols:
                    pass


                class FlextAlphaProtocols(_MeltanoProtocols, _BaseProtocols):
                    pass
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_b(tmp_path: Path) -> EdgeCaseFixture:
    """Auto-generated ``__init__.py`` lazy chain (build_lazy_import_map)."""
    return _build_project(
        tmp_path,
        "flext_alpha_b",
        (
            (
                "src/flext_alpha_b/__init__.py",
                """
                # AUTO-GENERATED FILE
                _LAZY_IMPORTS = {
                    ".models": ("FlextAlphaModels",),
                    ".utilities": ("FlextAlphaUtilities",),
                }
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_c(tmp_path: Path) -> EdgeCaseFixture:
    """flext-core bootstrap aliases (mp / up / ta) inside a model tree."""
    return _build_project(
        tmp_path,
        "flext_alpha_c",
        (
            (
                "src/flext_alpha_c/_models/sample.py",
                """
                from flext_core import FlextModelsPydantic as mp
                from flext_core import FlextUtilities as up
                from flext_core import FlextTypingBase as ta


                class FlextAlphaSample(mp.BaseModel):
                    pass
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_d(tmp_path: Path) -> EdgeCaseFixture:
    """tests/ tier with ``TestsFlext<Project><Tier>`` facade naming."""
    return _build_project(
        tmp_path,
        "flext_alpha_d",
        (
            (
                "tests/models.py",
                """
                class TestsFlextAlphaModels:
                    pass
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_e(tmp_path: Path) -> EdgeCaseFixture:
    """examples/ and scripts/ tiers carry their own facade names."""
    return _build_project(
        tmp_path,
        "flext_alpha_e",
        (
            (
                "examples/sample.py",
                """
                class ExamplesFlextAlphaSample:
                    pass
                """,
            ),
            (
                "scripts/sample.py",
                """
                class ScriptsFlextAlphaSample:
                    pass
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_f(tmp_path: Path) -> EdgeCaseFixture:
    """services/*.py mixin tree (one mixin per file)."""
    return _build_project(
        tmp_path,
        "flext_alpha_f",
        (
            (
                "src/flext_alpha_f/services/alpha.py",
                """
                class FlextAlphaServicesAlpha:
                    pass
                """,
            ),
            (
                "src/flext_alpha_f/services/beta.py",
                """
                class FlextAlphaServicesBeta:
                    pass
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_g(tmp_path: Path) -> EdgeCaseFixture:
    """FlextSettings subclass with ``auto_register`` decorator."""
    return _build_project(
        tmp_path,
        "flext_alpha_g",
        (
            (
                "src/flext_alpha_g/settings.py",
                """
                from flext_core import FlextSettings, auto_register


                @auto_register
                class FlextAlphaSettings(FlextSettings):
                    name: str = "alpha"
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_h(tmp_path: Path) -> EdgeCaseFixture:
    """Pydantic ``@field_validator`` / ``@model_validator`` decorated members."""
    return _build_project(
        tmp_path,
        "flext_alpha_h",
        (
            (
                "src/flext_alpha_h/models.py",
                """
                from pydantic import BaseModel, field_validator, model_validator


                class FlextAlphaModels(BaseModel):
                    name: str

                    @field_validator("name")
                    @classmethod
                    def _check_name(cls, value: str) -> str:
                        return value.strip()

                    @model_validator(mode="after")
                    def _check_self(self) -> "FlextAlphaModels":
                        return self
                """,
            ),
        ),
    )


@pytest.fixture
def edge_case_i(tmp_path: Path) -> EdgeCaseFixture:
    """``@override`` / ``@final`` decorated members."""
    return _build_project(
        tmp_path,
        "flext_alpha_i",
        (
            (
                "src/flext_alpha_i/models.py",
                """
                from typing import final, override


                class FlextAlphaBase:
                    def name(self) -> str:
                        return "base"


                @final
                class FlextAlphaModels(FlextAlphaBase):
                    @override
                    def name(self) -> str:
                        return "alpha"
                """,
            ),
        ),
    )
