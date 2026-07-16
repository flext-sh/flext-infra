"""Behavior tests for semantic private package-root import detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_infra import m, p, t
from flext_infra.detectors.private_import_bypass_detector import (
    FlextInfraPrivateImportBypassDetector,
)
from flext_tests import tm


class TestsFlextInfraPrivateRootImportDetector:
    """Validate private-root policy through one real Rope workspace session."""

    class Fixture(m.ContractModel):
        """Validated paths composing the semantic detector fixture."""

        workspace_root: Path
        project_root: Path
        package_root: Path
        config_file: Path
        settings_file: Path
        positive_files: tuple[Path, ...]
        negative_files: tuple[Path, ...]

    @staticmethod
    def write(path: Path, source: str) -> Path:
        """Persist one real Python or project resource in the fixture workspace."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    @classmethod
    def build_fixture(cls, tmp_path: Path) -> Fixture:
        """Build two governed projects with the complete P1-P5/N1-N6 matrix."""
        workspace_root = tmp_path / "workspace"
        project_root = workspace_root / "flext-pkg"
        package_root = project_root / "src" / "flext_pkg"
        core_root = workspace_root / "flext-core"
        core_package = core_root / "src" / "flext_core"

        cls.write(
            workspace_root / ".gitmodules",
            '[submodule "flext-pkg"]\n'
            "\tpath = flext-pkg\n"
            "\turl = ../flext-pkg.git\n"
            '[submodule "flext-core"]\n'
            "\tpath = flext-core\n"
            "\turl = ../flext-core.git\n",
        )
        for root, name in ((project_root, "flext-pkg"), (core_root, "flext-core")):
            cls.write(
                root / "pyproject.toml",
                f'[project]\nname = "{name}"\nversion = "0.20.0.dev0"\n',
            )
            cls.write(root / "Makefile", "all:\n\t@true\n")

        cls.write(
            core_package / "__init__.py",
            '"""Minimal upstream package for semantic MRO resolution."""\n',
        )
        cls.write(
            core_package / "_settings.py",
            "from __future__ import annotations\n\n"
            "class FlextSettings:\n"
            '    """Minimal upstream settings base."""\n',
        )

        config_file = cls.write(
            package_root / "_config.py",
            "from __future__ import annotations\n\n"
            "class FlextPkgConfig:\n"
            '    """Validated package configuration."""\n\n'
            "config = FlextPkgConfig()\n",
        )
        settings_file = cls.write(
            package_root / "_settings.py",
            "from __future__ import annotations\n\n"
            "from flext_core._settings import FlextSettings\n\n"
            "class FlextPkgSettings(FlextSettings):\n"
            '    """Validated package settings."""\n\n'
            "settings = FlextPkgSettings()\n",
        )
        generated_root_init = cls.write(
            package_root / "__init__.py",
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            '"""Flext Pkg package."""\n\n'
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from flext_pkg._config import config as config\n"
            "    from flext_pkg._settings import settings as settings\n\n"
            '__all__: tuple[str, ...] = ("config", "settings")\n',
        )

        p1 = cls.write(
            package_root / "p1_singleton.py",
            "from __future__ import annotations\n\n"
            "from flext_pkg._settings import settings\n\n"
            "VALUE = settings\n",
        )
        p2 = cls.write(
            package_root / "p2_class.py",
            "from __future__ import annotations\n\n"
            "from flext_pkg._settings import FlextPkgSettings\n\n"
            "VALUE = FlextPkgSettings\n",
        )
        p3 = cls.write(
            package_root / "p3_alias.py",
            "from __future__ import annotations\n\n"
            "from flext_pkg._config import config as local_config\n\n"
            "VALUE = local_config\n",
        )
        p4 = cls.write(
            package_root / "p4_multiline.py",
            "from __future__ import annotations\n\n"
            "from flext_pkg._config import (\n"
            "    config as multiline_config,\n"
            ")\n\n"
            "VALUE = multiline_config\n",
        )
        cls.write(project_root / "tests" / "__init__.py", '"""Tests package."""\n')
        p5 = cls.write(
            project_root / "tests" / "test_private_settings.py",
            "from __future__ import annotations\n\n"
            "from flext_pkg._settings import settings as test_settings\n\n"
            "VALUE = test_settings\n",
        )

        n2 = cls.write(
            package_root / "n2_public.py",
            "from __future__ import annotations\n\n"
            "from flext_pkg import config, settings\n\n"
            "CONFIG = config\n"
            "SETTINGS = settings\n",
        )
        n4 = cls.write(
            package_root / "_models" / "type_edge.py",
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from flext_pkg._settings import FlextPkgSettings\n\n"
            "class FlextPkgModels:\n"
            '    """Models facade with a proven reverse type edge."""\n\n'
            "    settings_type: type[FlextPkgSettings]\n",
        )
        cls.write(
            package_root / "_models" / "_config.py",
            "from __future__ import annotations\n\n"
            "class FlextModelsConfig:\n"
            '    """Nested model configuration, not the package singleton."""\n',
        )
        n5 = cls.write(
            package_root / "_models" / "__init__.py",
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            '"""Models package."""\n\n'
            "from __future__ import annotations\n\n"
            "from ._config import FlextModelsConfig as FlextModelsConfig\n\n"
            '__all__: tuple[str, ...] = ("FlextModelsConfig",)\n',
        )
        n6 = cls.write(
            package_root / "n6_service.py",
            "from __future__ import annotations\n\n"
            "class PlatformService:\n"
            '    """Unrelated service API."""\n\n'
            "    @staticmethod\n"
            "    def fetch_global() -> str:\n"
            '        """Return an unrelated runtime value."""\n'
            '        return "value"\n\n'
            "VALUE = PlatformService.fetch_global()\n",
        )

        return cls.Fixture(
            workspace_root=workspace_root,
            project_root=project_root,
            package_root=package_root,
            config_file=config_file,
            settings_file=settings_file,
            positive_files=(p1, p2, p3, p4, p5),
            negative_files=(generated_root_init, n2, settings_file, n4, n5, n6),
        )

    @staticmethod
    def snapshot(workspace_root: Path) -> tuple[tuple[str, str], ...]:
        """Return deterministic Python-source bytes for mutation detection."""
        return tuple(
            (
                path.relative_to(workspace_root).as_posix(),
                path.read_text(encoding="utf-8"),
            )
            for path in sorted(workspace_root.rglob("*.py"))
        )

    @staticmethod
    def detect(
        rope: p.Infra.RopeWorkspaceDsl, fixture: Fixture, file_path: Path
    ) -> t.SequenceOf[p.Infra.PrivateImportBypassViolation]:
        """Detect one source through the shared semantic workspace session."""
        parse_failures: t.MutableSequenceOf[p.Infra.ParseFailureViolation] = []
        violations = FlextInfraPrivateImportBypassDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=file_path,
                rope_project=rope.rope_project,
                rope_workspace=rope,
                parse_failures=parse_failures,
                project_name="flext-pkg",
                project_root=fixture.project_root,
            )
        )
        tm.that(tuple(parse_failures), eq=())
        return tuple(violations)

    @classmethod
    def assert_positive_matrix(
        cls, rope: p.Infra.RopeWorkspaceDsl, fixture: Fixture
    ) -> None:
        """Assert P1-P5 exact semantic target and source classifications."""
        expected_rows = (
            (
                fixture.positive_files[0],
                "flext_pkg._settings",
                "settings",
                "settings",
                fixture.settings_file,
                "settings",
                "src",
                "private_settings_import",
            ),
            (
                fixture.positive_files[1],
                "flext_pkg._settings",
                "FlextPkgSettings",
                "FlextPkgSettings",
                fixture.settings_file,
                "settings",
                "src",
                "private_settings_import",
            ),
            (
                fixture.positive_files[2],
                "flext_pkg._config",
                "config",
                "local_config",
                fixture.config_file,
                "config",
                "src",
                "private_config_import",
            ),
            (
                fixture.positive_files[3],
                "flext_pkg._config",
                "config",
                "multiline_config",
                fixture.config_file,
                "config",
                "src",
                "private_config_import",
            ),
            (
                fixture.positive_files[4],
                "flext_pkg._settings",
                "settings",
                "test_settings",
                fixture.settings_file,
                "settings",
                "tests",
                "private_settings_import",
            ),
        )
        for (
            file_path,
            private_module,
            imported_symbol,
            bound_name,
            target_file,
            canonical_singleton,
            surface,
            kind,
        ) in expected_rows:
            violations = cls.detect(rope, fixture, file_path)
            tm.that(len(violations), eq=1)
            violation = violations[0]
            tm.that(violation.file, eq=str(file_path))
            tm.that(violation.line, eq=3)
            tm.that(violation.private_module, eq=private_module)
            tm.that(violation.imported_symbol, eq=imported_symbol)
            tm.that(violation.bound_name, eq=bound_name)
            tm.that(violation.target_file, eq=str(target_file))
            tm.that(violation.canonical_singleton, eq=canonical_singleton)
            tm.that(violation.owner_project, eq="flext-pkg")
            tm.that(violation.surface, eq=surface)
            tm.that(violation.type_checking_guarded, eq=False)
            tm.that(violation.kind, eq=kind)

    @classmethod
    def assert_negative_matrix(
        cls, rope: p.Infra.RopeWorkspaceDsl, fixture: Fixture
    ) -> None:
        """Assert N1-N6 remain semantically distinct from consumer bypasses."""
        for file_path in fixture.negative_files:
            tm.that(tuple(cls.detect(rope, fixture, file_path)), eq=())

    class TestSemanticMatrix:
        """Exercise all cases through one indexed workspace and no source mutation."""

        def test_classifies_p1_p5_and_exempts_n1_n6(self, tmp_path: Path) -> None:
            """Resolve exact private roots while preserving valid owner/type edges."""
            contract = TestsFlextInfraPrivateRootImportDetector
            fixture = contract.build_fixture(tmp_path)
            before = contract.snapshot(fixture.workspace_root)

            with flext_infra.infra.rope_workspace(fixture.workspace_root) as rope:
                rope_project = rope.rope_project
                workspace_index = rope.workspace_index
                indexed_paths = frozenset(
                    entry.file_path
                    for entry in rope.modules(project_names=("flext-pkg",))
                )
                tm.that(
                    frozenset((
                        *fixture.positive_files,
                        *fixture.negative_files,
                    )).issubset(indexed_paths),
                    eq=True,
                )
                tm.that(rope.rope_project is rope_project, eq=True)
                tm.that(rope.workspace_index is workspace_index, eq=True)

                contract.assert_positive_matrix(rope, fixture)
                contract.assert_negative_matrix(rope, fixture)

                tm.that(rope.rope_project is rope_project, eq=True)
                tm.that(rope.workspace_index is workspace_index, eq=True)

            tm.that(contract.snapshot(fixture.workspace_root), eq=before)


__all__: tuple[str, ...] = ("TestsFlextInfraPrivateRootImportDetector",)
