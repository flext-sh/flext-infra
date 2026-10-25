"""Rule planning distinguishes repeated search paths from duplicate installs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraDistributionIdentity:
    """Exercise real installed metadata through the public rule planner."""

    @staticmethod
    def project(root: Path) -> None:
        """Provide ``project``."""
        (root / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "metadata-consumer"\ndependencies = []\n',
            encoding="utf-8",
        )

    @staticmethod
    def distribution(root: Path) -> None:
        """Provide ``distribution``."""
        metadata = root / "rule_identity_fixture-1.0.dist-info"
        metadata.mkdir(parents=True)
        (metadata / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: rule-identity-fixture\nVersion: 1.0\n",
            encoding="utf-8",
        )

    def test_repeated_directory_is_one_installation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test repeated directory is one installation."""
        self.project(tmp_path)
        site = tmp_path / "site"
        self.distribution(site)
        with tm.scope(python_paths=(str(site), str(site))):
            with u.Infra.codemod_workspace_snapshot(tmp_path) as snapshot:
                planned = u.Infra.codemod_rule_plan(snapshot)
        tm.that(planned.success, truth=True, msg=planned.error)

    def test_distinct_duplicate_installations_are_rejected(
        self,
        tmp_path: Path,
    ) -> None:
        """Test distinct duplicate installations are rejected."""
        self.project(tmp_path)
        sites: list[str] = []
        for name in ("first", "second"):
            site = tmp_path / name
            self.distribution(site)
            sites.append(str(site))
        with (
            tm.scope(python_paths=sites),
            pytest.raises(ValueError, match="duplicate installed distribution"),
        ):
            with u.Infra.codemod_workspace_snapshot(tmp_path) as snapshot:
                u.Infra.codemod_rule_plan(snapshot)

    def test_selected_provider_cycle_escapes_without_normalization(
        self,
        tmp_path: Path,
    ) -> None:
        """The installed providers retain the dependency owner's cycle failure."""
        self.project(tmp_path)
        site = tmp_path / "site"
        providers = ("catalog-cycle-first", "catalog-cycle-second")
        for name, dependency in zip(providers, reversed(providers), strict=True):
            metadata = site / f"{name.replace('-', '_')}-1.0.dist-info"
            metadata.mkdir(parents=True)
            (metadata / "METADATA").write_text(
                f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n"
                f"Requires-Dist: {dependency}\n",
                encoding=c.DEFAULT_ENCODING,
            )
            package = site / name.replace("-", "_")
            catalogue = package / c.Infra.CODEMOD_CONFIG_RELPATH
            catalogue.parent.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
            catalogue.write_text(
                f"{c.Infra.CODEMOD_SCOPE_KEY}: {c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        with (
            tm.scope(python_paths=(str(site),)),
            pytest.raises(
                ValueError,
                match=(
                    r"^cyclic dependency graph: catalog-cycle-first -> "
                    r"catalog-cycle-second -> catalog-cycle-first$"
                ),
            ),
            u.Infra.codemod_workspace_snapshot(tmp_path) as snapshot,
        ):
            u.Infra.codemod_rule_plan(snapshot)
