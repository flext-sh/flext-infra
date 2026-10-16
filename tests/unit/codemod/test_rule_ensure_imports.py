"""A rule's ensure-imports completes its rewrite through the public mod CLI.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, main, u
from tests import tm, u as test_u


@pytest.mark.slow
class TestsFlextInfraModRuleEnsureImports:
    """The applied rewrite reaches its fixed point with the import bound."""

    @staticmethod
    def _declare(mod_workspace: Path, package: str) -> None:
        """Declare the compose module, the consumer, and the local rule."""
        package_dir = mod_workspace / c.Infra.DEFAULT_SRC_DIR / package
        tm.ok(
            u.Cli.atomic_write_text_file(
                package_dir / "typings.py",
                (
                    '"""Fixture compose module."""\n'
                    "\n"
                    "\n"
                    "class ModWorkspaceTypes:\n"
                    '    """Fixture family compose class."""\n'
                    "\n"
                    "    class ModWorkspace:\n"
                    '        """Fixture family namespace."""\n'
                    "\n"
                    '        YamlMap = "yaml"\n'
                ),
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / "sample.py",
                '__all__: list[str] = []\n\ncontainer = "before"\n',
            ),
        )
        test_u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                "static-path-probe": (
                    "id: static-path-probe\n"
                    "language: python\n"
                    "severity: error\n"
                    "files:\n"
                    '  - "**/*.py"\n'
                    "metadata:\n"
                    "  ensure-imports:\n"
                    f"    - module: {package}.typings\n"
                    "      name: ModWorkspaceTypes\n"
                    "rule:\n"
                    '  pattern: container = "before"\n'
                    "fix: container = ModWorkspaceTypes.ModWorkspace.YamlMap\n"
                    "message: rewrite through the static compose path\n"
                ),
            },
        )

    @staticmethod
    def _published(mod_workspace: Path) -> str:
        """Return the consumer's published source."""
        return (mod_workspace / "sample.py").read_text(encoding="utf-8")

    def test_apply_rewrites_the_usage_and_completes_the_import(
        self,
        mod_workspace: Path,
    ) -> None:
        """The fixed point binds the name the applied rewrite references."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare(mod_workspace, package)
        tm.ok(test_u.Tests.create_python_environment(mod_workspace))

        main(["refactor", "mod", "--repository-root", str(mod_workspace), "--apply"])

        published = self._published(mod_workspace)
        tm.that(
            published,
            has=f"from {package}.typings import ModWorkspaceTypes",
        )
        tm.that(published, has="container = ModWorkspaceTypes.ModWorkspace.YamlMap")

    def test_completed_state_is_a_stable_fixed_point(
        self,
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A second pass over the completed state changes nothing."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare(mod_workspace, package)
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / "sample.py",
                (
                    "__all__: list[str] = []\n"
                    "\n"
                    f"from {package}.typings import ModWorkspaceTypes\n"
                    "\n"
                    "container = ModWorkspaceTypes.ModWorkspace.YamlMap\n"
                ),
            ),
        )
        tm.ok(test_u.Tests.create_python_environment(mod_workspace))

        main(["refactor", "mod", "--repository-root", str(mod_workspace), "--apply"])
        capture = capsys.readouterr()

        tm.that(
            capture.out + capture.err, has="fixed point verified with zero findings"
        )
        tm.that(
            self._published(mod_workspace),
            has="container = ModWorkspaceTypes.ModWorkspace.YamlMap",
        )

    def test_conflicting_binding_fails_the_publication(
        self,
        mod_workspace: Path,
    ) -> None:
        """A name bound from another module is a loud rule defect, not a skip."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare(mod_workspace, package)
        conflict = mod_workspace / "conflict_source.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                conflict,
                ('from elsewhere import ModWorkspaceTypes\n\ncontainer = "before"\n'),
            ),
        )

        with pytest.raises(Exception, match="binds it from"):
            main([
                "refactor",
                "mod",
                "--repository-root",
                str(mod_workspace),
                "--apply",
            ])
