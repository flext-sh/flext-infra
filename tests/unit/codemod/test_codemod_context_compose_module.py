"""The compose-module predicate sanctions the public family compose leaves.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

import pytest

from flext_infra import m
from tests import c, tm, u


class TestsFlextInfraCodemodContextComposeModule:
    """Only ``<package>.<leaf>`` canonical compose modules are sanctioned."""

    @staticmethod
    @pytest.mark.parametrize("changed", ["export", "directory"])
    def test_class_stem_pass_preserves_verdicts_and_rejects_namespace_drift(
        mod_workspace: Path, changed: str
    ) -> None:
        """Repeated stem admissions retain export and membership authentication."""
        layout = tm.not_none(u.Infra.layout(mod_workspace))
        export = layout.package_dir / "stem_probe.py"
        export.write_text('__all__ = ["probe"]\n', encoding="utf-8")
        rule = next(
            rule
            for rule in tm.ok(u.Infra.codemod_rule_plan(mod_workspace)).rules
            if rule.id == "require-project-class-stem"
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        epoch = u.Infra.codemod_source_epoch(m.Infra.CodemodBindingSnapshot(states=()))
        cases = (
            ("source.py", f"{layout.class_stem}Source", False),
            ("examples/source.py", f"{layout.class_stem}Scenario", False),
            ("tests/source.py", f"Tests{layout.class_stem}Source", False),
            ("tests/bare.py", f"{layout.class_stem}Bare", True),
            ("foreign.py", "Foreign", True),
        )
        for relative, name, _expected in cases:
            path = mod_workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"class {name}: pass\n", encoding="utf-8")
        with ExitStack() as scope:
            project, sources = scope.enter_context(
                u.Infra.codemod_binding_project(mod_workspace, epoch)
            )
            for _repeat in range(2):
                for relative, name, expected in cases:
                    tm.that(
                        u.Infra.codemod_context_admits(
                            m.Infra.CodemodAdmission(
                                root=mod_workspace,
                                rule=rule,
                                file_path=Path(relative),
                                captures={"NAME": {"text": name}},
                                facts=facts,
                                snapshot=epoch.snapshot,
                            ),
                            project=project,
                            sources=sources,
                        ),
                        eq=expected,
                    )
            target = (
                export
                if changed == "export"
                else layout.package_dir / "new_stem_probe.py"
            )
            target.write_text("__all__ = [missing]\n", encoding="utf-8")
            with pytest.raises(ValueError, match="source"):
                scope.close()
        with (
            pytest.raises(ValueError, match="invalid __all__"),
            u.Infra.codemod_binding_project(mod_workspace, epoch) as (project, sources),
        ):
            u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=mod_workspace,
                    rule=rule,
                    file_path=Path(cases[0][0]),
                    captures={"NAME": {"text": cases[0][1]}},
                    facts=facts,
                    snapshot=epoch.snapshot,
                ),
                project=project,
                sources=sources,
            )

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
        tm.fail(self._admits(mod_workspace, module=package))

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
            'dependencies = ["flext-cli"]\n',
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
    @pytest.mark.parametrize(
        ("relative", "module", "expected"),
        [
            ("_typings/base.py", "flext_cli.utilities", True),
            ("_typings/base.py", "flext_cli._utilities.conversion", True),
            ("_typings/nested/config.py", "flext_cli.utilities", True),
            ("_models/base.py", "flext_cli.utilities", True),
            ("_constants/base.py", "flext_cli.utilities", True),
            ("_typings/base.py", "flext_cli.constants", False),
            ("_config.py", "flext_cli.utilities", False),
            ("_settings.py", "flext_cli.utilities", False),
        ],
    )
    @pytest.mark.parametrize("outside_src", [False, True])
    def test_compose_import_cannot_bypass_the_declaration_layer(
        mod_workspace: Path,
        relative: str,
        module: str,
        *,
        expected: bool,
        outside_src: bool,
    ) -> None:
        """Real rule admission retains the importer's first architectural role."""
        package = u.Infra.project_package_name(mod_workspace)
        document = mod_workspace / c.PYPROJECT_FILENAME
        document.write_text(
            '[project]\nname = "mod-workspace"\nversion = "0.0.0"\n'
            'dependencies = ["flext-cli"]\n',
            encoding="utf-8",
        )
        base = (
            mod_workspace
            if outside_src
            else mod_workspace / c.Infra.DEFAULT_SRC_DIR / package
        )
        path = base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"from {module} import Probe\n", encoding="utf-8")
        rule = next(
            rule
            for rule in u.Infra.codemod_rule_plan(mod_workspace).unwrap().rules
            if rule.id == "ban-reverse-runtime-import"
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        # A layer-zero verdict reads the importer from its captured epoch.
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (u.Cli.atomic_read_binary_file_state(path, required=True).unwrap(),),
            facts.binding_modules,
        )
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            admitted = u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=mod_workspace,
                    rule=rule,
                    file_path=path,
                    captures={"TARGET": {"text": module}},
                    facts=facts,
                    snapshot=snapshot,
                ),
                project=project,
                sources=sources,
            )
        tm.that(admitted, eq=expected)

    @staticmethod
    @pytest.mark.parametrize(
        ("relative", "service", "expected"),
        [
            ("workspace/detector.py", True, False),
            ("workspace/cases/parts/detector.py", True, False),
            ("workspace/cases/parts/detector.py", False, True),
            ("base.py", True, True),
            ("workspace/detector.py", False, True),
            ("_utilities/worker.py", True, True),
            ("base.py", False, False),
        ],
    )
    def test_native_service_role_preserves_both_layer_directions(
        mod_workspace: Path,
        relative: str,
        *,
        service: bool,
        expected: bool,
    ) -> None:
        """Only actual own-root subclasses refine a fallback module's role."""
        package = u.Infra.project_package_name(mod_workspace)
        module_root = mod_workspace / c.Infra.DEFAULT_SRC_DIR / package
        base = module_root / "base.py"
        worker = module_root / (
            "workspace/worker.py" if relative == "base.py" else relative
        )
        worker.parent.mkdir(parents=True, exist_ok=True)
        base.write_text(
            "from flext_core import s as CoreService\n"
            "class RootService[T](CoreService[T]):\n    pass\n\ns = RootService\n",
            encoding="utf-8",
        )
        worker.write_text(
            f"from {package}.base import RootService\n"
            f"class DetectorService({'RootService[bool]' if service else 'object'}):\n"
            "    pass\nordinary = 1\nunresolved: Unavailable\n",
            encoding="utf-8",
        )
        if "/cases/" in relative:
            worker.with_name("__init__.py").write_text("", encoding="utf-8")
            worker.with_name("document.py").write_text(
                f"from {package}.base import RootService\n"
                f"class Parent({'RootService[bool]' if service else 'object'}): pass\n",
                encoding="utf-8",
            )
            worker.write_text(
                f"from {package}.workspace.cases.parts import document as part\n"
                "class DetectorService(part.Parent): pass\n",
                encoding="utf-8",
            )
        source = base if relative == "base.py" else worker
        target = f"{package}.workspace.worker" if source == base else f"{package}.base"
        if source == base:
            with base.open("a", encoding="utf-8") as stream:
                stream.write(f"from {target} import DetectorService\n")
        rule = next(
            rule
            for rule in u.Infra.codemod_rule_plan(mod_workspace).unwrap().rules
            if rule.id == "ban-reverse-runtime-import"
        )
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                for path in dict.fromkeys((base, worker, *worker.parent.glob("*.py")))
            ),
        )
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            admitted = u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=mod_workspace,
                    rule=rule,
                    file_path=source,
                    captures={"TARGET": {"text": target}},
                    facts=u.Infra.codemod_project_facts(mod_workspace, (rule,)),
                    snapshot=snapshot,
                ),
                project=project,
                sources=sources,
            )
        tm.that(admitted, eq=expected)

    @staticmethod
    def _admits(root: Path, module: str) -> bool:
        """Admit one probe finding through the compose-module predicate.

        Returns:
            Whether the real binding owner admits the probe finding.

        """
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
            root,
            u.Infra.codemod_source_epoch(m.Infra.CodemodBindingSnapshot(states=())),
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
