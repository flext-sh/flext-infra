"""The compose-module predicate sanctions the public family compose leaves.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m
from tests import tm, u


class TestsFlextInfraCodemodContextComposeModule:
    """Only ``<package>.<leaf>`` canonical compose modules are sanctioned."""

    @staticmethod
    def _declare_compose_module(root: Path, package: str, leaf: str) -> None:
        """Create one canonical compose module file in the fixture package."""
        module_root = root / c.Infra.DEFAULT_SRC_DIR / package
        module_root.mkdir(parents=True, exist_ok=True)
        (module_root / f"{leaf}.py").write_text(
            "__all__: list[str] = []\n",
            encoding="utf-8",
        )

    @pytest.mark.parametrize(
        "leaf",
        ["constants", "models", "protocols", "typings", "utilities"],
    )
    def test_own_package_canonical_compose_module_is_admitted(
        self, mod_workspace: Path, leaf: str
    ) -> None:
        """Test own package canonical compose module is admitted."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare_compose_module(mod_workspace, package, leaf)
        tm.that(
            self._admits(mod_workspace, module=f"{package}.{leaf}"),
            eq=True,
        )

    def test_own_package_undeclared_compose_leaf_is_excluded(
        self, mod_workspace: Path
    ) -> None:
        """A canonical leaf whose module file was never declared stays out."""
        package = u.Infra.project_package_name(mod_workspace)
        tm.that(
            self._admits(mod_workspace, module=f"{package}.constants"),
            eq=False,
        )

    @pytest.mark.parametrize(
        ("leaf", "tail"),
        [("_constants", ""), ("_typings", ".base"), ("constants", ".inner")],
    )
    def test_private_and_nested_module_shapes_are_excluded(
        self, mod_workspace: Path, leaf: str, tail: str
    ) -> None:
        """Private and nested paths are never the compose surface."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare_compose_module(mod_workspace, package, "constants")
        tm.that(
            self._admits(mod_workspace, module=f"{package}.{leaf}{tail}"),
            eq=False,
        )

    def test_root_package_path_is_excluded(self, mod_workspace: Path) -> None:
        """The bare package root is not a compose module."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare_compose_module(mod_workspace, package, "constants")
        tm.that(self._admits(mod_workspace, module=package), eq=False)

    def test_foreign_runtime_compose_module_is_admitted(
        self, mod_workspace: Path
    ) -> None:
        """A runtime-closure package's compose module is the fleet contract."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare_compose_module(mod_workspace, package, "constants")
        document = mod_workspace / c.PYPROJECT_FILENAME
        document.write_text(
            "[project]\n"
            'name = "mod-workspace"\n'
            'version = "0.0.0"\n'
            "dependencies = [\"flext-cli\"]\n",
            encoding="utf-8",
        )
        tm.that(
            self._admits(mod_workspace, module="flext_cli.typings"),
            eq=True,
        )

    def test_foreign_non_compose_submodule_stays_excluded(
        self, mod_workspace: Path
    ) -> None:
        """A leaf outside the canonical compose set is never sanctioned."""
        package = u.Infra.project_package_name(mod_workspace)
        self._declare_compose_module(mod_workspace, package, "constants")
        tm.that(
            self._admits(mod_workspace, module="flext_cli._utilities"),
            eq=False,
        )

    @staticmethod
    def _admits(root: Path, module: str) -> bool:
        """Admit one probe finding through the compose-module predicate."""
        package = u.Infra.project_package_name(root)
        path = root / c.Infra.DEFAULT_SRC_DIR / package / "consumer.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"from {module} import Probe\n",
            encoding="utf-8",
        )
        rule = m.Infra.CodemodRule(
            id="compose-module-probe",
            digest="probe",
            provider="probe",
            resource=Path("probe.yml"),
            fixable=False,
            context=(
                m.Infra.CodemodContextCondition(
                    variable="MODULE",
                    predicate=c.Infra.CodemodContextPredicate.COMPOSE_MODULE,
                    holds=True,
                ),
            ),
        )
        with u.Infra.codemod_binding_project(
            root, m.Infra.CodemodBindingSnapshot(states=())
        ) as (project, sources):
            return u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=root,
                    rule=rule,
                    file_path=path,
                    captures={"MODULE": {"text": module}},
                    facts=u.Infra.codemod_project_facts(root, (rule,)),
                ),
                project=project,
                sources=sources,
            )
