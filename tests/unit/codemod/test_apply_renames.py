"""Real transactional CSV campaigns and identity-bound external consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.codemod import (
    FlextInfraApplyRenames,
    FlextInfraCodemodSemanticApply,
    FlextInfraRenameSymbols,
)
from tests import c, m, tm, u


class TestsFlextInfraApplyRenames:
    """Campaigns change declared sources, preserve drivers, and prove convergence."""

    @staticmethod
    @pytest.fixture(autouse=True)
    def campaign_runtime(mod_workspace: Path) -> None:
        """Every publication consumes its checkout's independently owned runtime."""
        u.Tests.provision_checkout(mod_workspace)
        u.Tests.provision_runtime_environment(mod_workspace)

    @staticmethod
    def test_rejected_joint_runtime_never_publishes_provider_or_receivers(
        tmp_path: Path,
    ) -> None:
        """A failing real receiver rejects the complete generated cutover preview."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        u.Tests.provision_runtime_environment(root)
        provider = package / "provider.py"
        first = package / "first.py"
        second = package / "second.py"
        provider.write_text(
            '"""Provider contract for receiver rejection."""\n'
            "class FlextProvider:\n"
            '    """Public provider declaration."""\n'
            '__all__ = ["FlextProvider"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        first.write_text(
            '"""Direct receiver contract."""\n'
            "from .provider import FlextProvider as Selected\n"
            "class Derived(Selected):\n"
            '    """Retain the public provider base."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        second.write_text(
            '"""Fail at real runtime, not during static planning."""\n'
            "from .first import Derived\n"
            "class Transitive(Derived):\n"
            '    """Observe the direct receiver base."""\n'
            'raise RuntimeError("receiver rejected candidate")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        originals = {
            path: path.read_bytes()
            for path in (
                provider,
                first,
                second,
                package / c.Infra.INIT_PY,
            )
        }
        driver = root / "renames.csv"
        driver.write_text(
            "old,new\nFlextProvider,FlextRenamedProvider\n", encoding=c.DEFAULT_ENCODING
        )
        result = FlextInfraApplyRenames.run(
            m.Infra.ApplyRenamesInput(
                repository_root=root,
                csv=str(driver),
                roots=(str(root),),
                bindings={"": (f"{package.name}.provider",)},
                rename_definitions=True,
                apply=True,
            )
        )
        tm.fail(result, has="receiver rejected candidate")
        for path, content in originals.items():
            tm.that(path.read_bytes(), eq=content)

    @staticmethod
    def _provider_rename_workspace(
        tmp_path: Path,
        authority: str,
    ) -> tuple[Path, Path, list[Path], list[Path], Path, bytes]:
        """Create independent providers and every native receiver scope.

        Returns:
            Root, Python, project and package paths, provider and unrelated bytes.

        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-provider",
            package_name="provider_pkg",
        )
        u.Tests.provision_checkout(root)
        python = u.Tests.provision_runtime_environment(root)
        projects = [root]
        packages = [package]
        if authority != "standalone":
            for name in ("first", "second"):
                project, receiver = u.Tests.create_lazy_init_workspace(
                    tmp_path if authority == "external" else root,
                    project_name=f"flext-{name}",
                    package_name=f"{name}_pkg",
                )
                projects.append(project)
                packages.append(receiver)
            (root / ".gitmodules").write_text(
                "".join(
                    f'[submodule "{project.name}"]\n'
                    f"path = {project.relative_to(root).as_posix()}\n"
                    f"url = https://example.org/{project.name}.git\n"
                    for project in projects[1:]
                    if authority != "external"
                ),
                encoding=c.DEFAULT_ENCODING,
            )
            if authority == "external":
                for project in projects[1:]:
                    u.Tests.provision_checkout(project)
                    u.Tests.provision_runtime_environment(project)
                inventory = m.Infra.HostWorkspaceInventory(
                    entries=tuple(
                        m.Infra.HostWorkspaceInventoryEntry(
                            project_id=project.name,
                            owner="fixture",
                            path=project,
                            checkout_id=str(project),
                            governing_checkout_id=str(project),
                            project_profile=c.Infra.ProjectKind.INTERNAL_FLEXT,
                            upstream_project_id=None,
                            effective_ref=None,
                        )
                        for project in projects[1:]
                    )
                )
                provider = root / "_inventory.py"
                provider.write_text(
                    '"""Expose the selected canonical host inventory."""\n'
                    "import sys\n"
                    f"sys.stdout.write({(inventory.model_dump_json() + chr(10))!r})\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                (root / "config").mkdir()
                (root / "config" / "codegen.yaml").write_text(
                    "Infra:\n  codegen:\n    workspace_inventory_command: "
                    + json.dumps((str(python), "-B", str(provider)))
                    + "\n",
                    encoding=c.DEFAULT_ENCODING,
                )
        provider = package / "owner.py"
        provider.write_text(
            '"""Public provider identity."""\n'
            "from __future__ import annotations\n"
            "class FlextProvider:\n"
            '    """An independently declared provider."""\n'
            "    @staticmethod\n"
            "    def value() -> int:\n"
            '        """Return the synthetic provider contract.\n\n'
            '        Returns:\n            The provider value.\n        """\n'
            "        return 17\n"
            '__all__ = ["FlextProvider"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "__init__.py").write_text(
            '"""Public provider exports."""\n'
            "from .owner import FlextProvider\n"
            '__all__ = ["FlextProvider"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        first = packages[1] if len(packages) > 1 else package
        second = packages[2] if len(packages) > 2 else package
        (first / "receiver.py").write_text(
            '"""Direct and aliased public provider consumers."""\n'
            "from __future__ import annotations\n"
            "from typing import Annotated, Literal\n"
            "import provider_pkg.owner as ProviderModule\n"
            "from provider_pkg import owner\n"
            "from provider_pkg import FlextProvider\n"
            "from provider_pkg import FlextProvider as Imported\n"
            'def build(value: "FlextProvider") -> "Imported":\n'
            '    """Preserve the actual provider identity.\n\n'
            '    Returns:\n        The supplied provider.\n    """\n'
            "    return value\n"
            "class Derived(Imported):\n"
            '    """Inherit the aliased provider."""\n'
            "class GenericConsumer[Element](list[FlextProvider]):\n"
            '    """Keep the native generic base bound to the provider."""\n'
            'def by_module(value: "owner.FlextProvider") -> (\n'
            '    "ProviderModule.FlextProvider"\n'
            "):\n"
            '    """Preserve module-qualified provider identity.\n\n'
            '    Returns:\n        The supplied provider.\n    """\n'
            "    return value\n"
            'Payload = Literal["FlextProvider"]\n'
            'Tagged = Annotated[Imported, "FlextProvider"]\n'
            'PROSE = "FlextProvider"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (second / "transitive.py").write_text(
            '"""Transitive provider consumer."""\n'
            f"from {first.name}.receiver import Derived as Selected\n"
            "class Transitive(Selected):\n"
            '    """Inherit the direct consumer."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        unrelated = second / "unrelated.py"
        unrelated.write_text(
            '"""An unrelated same-spelled declaration."""\n'
            "class FlextProvider:\n"
            '    """Keep the independently owned identity."""\n'
            "    @staticmethod\n"
            "    def value() -> int:\n"
            '        """Return the unrelated value.\n\n'
            '        Returns:\n            The unrelated contract value.\n        """\n'
            "        return 23\n"
            "__all__: list[str] = []\n",
            encoding=c.DEFAULT_ENCODING,
        )
        for project in projects:
            tests = project / "tests"
            tests.mkdir(exist_ok=True)
            (tests / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
            (tests / "test_receiver.py").write_text(
                '"""The local tests package owns its native import scope."""\n'
                "from provider_pkg import FlextProvider as Selected\n"
                "VALUE = Selected.value()\n",
                encoding=c.DEFAULT_ENCODING,
            )
        return root, python, projects, packages, provider, unrelated.read_bytes()

    @staticmethod
    @pytest.mark.parametrize(
        "authority", ["workspace", "member", "standalone", "external"]
    )
    @pytest.mark.parametrize("operation", ["class", "module"])
    def test_provider_rename_reaches_all_native_consumer_scopes(
        tmp_path: Path,
        authority: str,
        operation: str,
    ) -> None:
        """Public aliases, transitive users and generated exports cut over together."""
        root, python, projects, packages, provider, original_unrelated = (
            TestsFlextInfraApplyRenames._provider_rename_workspace(tmp_path, authority)
        )
        driver = root / "renames.csv"
        driver.write_text(
            "old,new\nFlextProvider,FlextRenamedProvider\n", encoding=c.DEFAULT_ENCODING
        )
        selected = projects[1] if authority == "member" else root
        request = m.Infra.ApplyRenamesInput(
            repository_root=root,
            csv=str(driver),
            roots=(str(selected),),
            bindings={"": ("provider_pkg",)},
            rename_definitions=True,
            apply=True,
        )
        if operation == "class":
            report = tm.ok(FlextInfraApplyRenames.run(request))
            tm.that(report.occurrences, eq=0)
            exported_name = "FlextRenamedProvider"
        else:
            with infra.rope_workspace(root) as workspace:
                artifact = tm.ok(
                    FlextInfraCodemodSemanticApply.build_rename_plan(
                        root,
                        workspace,
                        m.Infra.SemanticRenameSelections(
                            decisions=(
                                m.Infra.SemanticRenameSelection(
                                    qualified_name="provider_pkg.owner",
                                    replacement_name="meaningful",
                                    reason=(
                                        "Move the authenticated provider and all"
                                        " native receivers together"
                                    ),
                                ),
                            )
                        ),
                    )
                )
                driver = root / "rename.artifact"
                tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
                for apply in (False, True):
                    tm.ok(
                        FlextInfraCodemodSemanticApply.consume_rename_plan(
                            m.Infra.ModCommand(
                                repository_root=selected,
                                rename_plan=driver,
                                apply=apply,
                            ),
                            workspace,
                            infra.source_preview(root),
                        )
                    )
                    if not apply:
                        tm.that(provider.is_file(), eq=True)
                        tm.that(provider.with_name("meaningful.py").exists(), eq=False)
                tm.that(provider.exists(), eq=False)
                tm.that(provider.with_name("meaningful.py").is_file(), eq=True)
            exported_name = "FlextProvider"
        tm.that((packages[-1] / "unrelated.py").read_bytes(), eq=original_unrelated)
        TestsFlextInfraApplyRenames._verify_renamed_consumers(
            root, python, projects, packages, exported_name
        )
        if operation == "class":
            again = tm.ok(FlextInfraApplyRenames.run(request))
            tm.that(again.files_changed, eq=0)

    @staticmethod
    def _verify_renamed_consumers(
        root: Path,
        python: Path,
        projects: list[Path],
        packages: list[Path],
        exported_name: str,
    ) -> None:
        """Exercise provider identity and local test imports in fresh interpreters."""
        package = packages[0]
        first = packages[1] if len(packages) > 1 else package
        second = packages[2] if len(packages) > 2 else package
        code = (
            "from typing import get_args, get_type_hints\n"
            f"from provider_pkg import {exported_name} as CanonicalProvider\n"
            f"from {first.name}.receiver import (\n"
            f"    build,\n    by_module,\n    GenericConsumer,\n"
            f"    Imported,\n    Payload,\n    Tagged,\n    PROSE,\n)\n"
            f"from {second.name}.transitive import Transitive\n"
            f"from {second.name}.unrelated import FlextProvider\n"
            "assert get_type_hints(build) == {\n"
            "    'value': CanonicalProvider,\n"
            "    'return': Imported,\n"
            "}\n"
            "assert get_type_hints(by_module) == {\n"
            "    'value': CanonicalProvider,\n"
            "    'return': CanonicalProvider,\n"
            "}\n"
            "assert Imported is CanonicalProvider\n"
            "assert get_args(\n"
            "    GenericConsumer.__orig_bases__[0]\n"
            ") == (CanonicalProvider,)\n"
            "assert issubclass(Transitive, CanonicalProvider)\n"
            "assert Transitive.value() == 17 and FlextProvider.value() == 23\n"
            "assert get_args(Payload) == ('FlextProvider',)\n"
            "assert get_args(Tagged)[1:] == ('FlextProvider',)\n"
            "assert PROSE == 'FlextProvider'\n"
        )
        imported = tm.ok(
            u.Cli.run(
                (str(python), "-B", "-c", code),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env=u.Cli.process_env(
                        overrides={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: (
                                c.Infra.ORCHESTRATOR_ENV_PATH_SEPARATOR.join(
                                    str(project / c.Infra.DEFAULT_SRC_DIR)
                                    for project in projects
                                )
                            ),
                        }
                    )
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(imported.outcome), eq=True)
        for project in projects:
            checked = tm.ok(
                u.Cli.run(
                    (
                        str(python),
                        "-B",
                        "-c",
                        "from tests.test_receiver import VALUE; assert VALUE == 17",
                    ),
                    cwd=project,
                    options=m.Cli.ProcessOptions(
                        env=u.Cli.process_env(
                            overrides={
                                c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                    package.parent
                                ),
                            }
                        )
                    ),
                )
            )
            tm.that(u.Cli.process_succeeded(checked.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("old", "new"),
        [
            ("is_semantic_clone", "semantic_clone"),
            ("is_production_module", "production_module"),
            ("is_unused", "unused"),
        ],
    )
    def test_domain_decision_plans_declarations_contracts_and_full_references(
        mod_workspace: Path, old: str, new: str
    ) -> None:
        """Names enter as decisions, while native Rope owns all reference rewires."""
        definer = mod_workspace / "definer.py"
        source = (
            "from typing import TYPE_CHECKING\n"
            "class Owner:\n"
            "    @staticmethod\n"
            f"    def {old}(value: str) -> bool:\n"
            "        return len(value) > 1\n"
            "class Contract:\n"
            "    if TYPE_CHECKING:\n"
            "        @staticmethod\n"
            f"        def {old}(value: str) -> bool: ...\n"
            "    def evaluate(self, value: str) -> bool:\n"
            f"        return self.{old}(value)\n"
            "class Composed(Contract, Owner):\n"
            "    pass\n"
            "class Foreign:\n"
            "    @staticmethod\n"
            f"    def {old}(value: str) -> bool:\n"
            "        return False\n"
        )
        definer.write_text(source, encoding="utf-8")
        consumer = mod_workspace / "consumer.py"
        consumer.write_text(
            "from definer import Owner as alias, Composed, Foreign\n"
            f"print(alias.{old}('yes'), Composed().evaluate('yes'), "
            f"Foreign.{old}('yes'))\n",
            encoding="utf-8",
        )
        sources = {path: path.read_text() for path in (definer, consumer)}
        declaration = m.Infra.Object(
            project=mod_workspace.name,
            file_path=str(definer),
            line=4,
            name=old,
            kind="method",
            module_name="definer",
            scope_path=f"Owner.{old}",
        )
        contract = declaration.model_copy(
            update={"line": 9, "scope_path": f"Contract.{old}"}
        )
        provider = FlextInfraRenameSymbols((
            m.Infra.SemanticRenameDecision(
                declaration=declaration,
                replacement_name=new,
                reason="Domain predicate retaining its callable contract",
                contracts=(contract,),
            ),
        ))
        with u.Infra.open_project(
            mod_workspace, project_roots=(mod_workspace,)
        ) as project:
            plans = FlextInfraRenameSymbols.plan_candidates(
                project, sources, (declaration,), provider
            )
        tm.that({plan.file_path for plan in plans}, eq={definer, consumer})
        for plan in plans:
            tm.that(plan.file_path.read_text(), eq=plan.original_source)
            plan.file_path.write_text(plan.updated_source, encoding="utf-8")
        output = tm.ok(u.Cli.run((sys.executable, str(consumer))))
        tm.that(output.stdout, eq="True True False\n")
        original_method = next(
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.FunctionDef)
        )
        renamed_method = next(
            node
            for node in ast.walk(ast.parse(definer.read_text()))
            if isinstance(node, ast.FunctionDef)
        )
        tm.that(renamed_method.name, eq=new)
        tm.that(ast.dump(renamed_method.args), eq=ast.dump(original_method.args))
        tm.that(
            [ast.dump(node) for node in renamed_method.body],
            eq=[ast.dump(node) for node in original_method.body],
        )
        for plan in plans:
            plan.file_path.write_text(plan.original_source, encoding="utf-8")
        tm.that(definer.read_text(), eq=source)

    @staticmethod
    @pytest.mark.parametrize(
        ("failure", "error"),
        [
            ("collision", "destination is occupied"),
            ("inherited", "inherited rather than introduced"),
            ("contract", "incompatible contract"),
            ("behavior", "companion has behavior"),
            ("incomplete", "escaped known inventory"),
        ],
    )
    def test_domain_decision_rejects_unsafe_plans_without_publication(
        mod_workspace: Path, failure: str, error: str
    ) -> None:
        """Occupied names, inherited declarations and differing signatures fail."""
        path = mod_workspace / "definer.py"
        source = (
            "class Owner:\n"
            "    def predicate(self, value: str) -> bool:\n"
            "        return bool(value)\n"
            "    def canonical(self, value: str) -> bool:\n"
            "        return False\n"
            "class Derived(Owner):\n"
            "    pass\n"
            "class Contract:\n"
            "    def predicate(self, value: int) -> bool: ...\n"
        )
        if failure == "behavior":
            source = source.replace(
                "value: int) -> bool: ...", "value: str) -> bool: return True"
            )
        path.write_text(source, encoding="utf-8")
        if failure == "incomplete":
            (mod_workspace / "excluded_consumer.py").write_text(
                "from definer import Owner\nvalue = Owner().predicate('yes')\n",
                encoding="utf-8",
            )
        declaration = m.Infra.Object(
            project=mod_workspace.name,
            file_path=str(path),
            line=2,
            name="predicate",
            kind="method",
            module_name="definer",
            scope_path=(
                "Derived.predicate" if failure == "inherited" else "Owner.predicate"
            ),
        )
        contract = declaration.model_copy(
            update={"line": 9, "scope_path": "Contract.predicate"}
        )
        provider = FlextInfraRenameSymbols((
            m.Infra.SemanticRenameDecision(
                declaration=declaration,
                replacement_name=(
                    "canonical" if failure == "collision" else "meaningful"
                ),
                reason="Explicit test domain decision",
                contracts=((contract,) if failure in {"contract", "behavior"} else ()),
            ),
        ))
        with (
            u.Infra.open_project(
                mod_workspace, project_roots=(mod_workspace,)
            ) as project,
            pytest.raises(ValueError, match=error),
        ):
            FlextInfraRenameSymbols.plan_candidates(
                project, {path: source}, (declaration,), provider
            )
        tm.that(path.read_text(), eq=source)

    @staticmethod
    def _request(root: Path, *, apply: bool) -> m.Infra.ApplyRenamesInput:
        return m.Infra.ApplyRenamesInput(
            csv=str(root / "renames.csv"),
            roots=(str(root),),
            apply=apply,
            text_globs=("**/*.md",),
            python_documentation=True,
        )

    @staticmethod
    def _seed(root: Path) -> Path:
        target = root / "guide.md"
        target.write_text(
            "A campaign_token keeps surrounding prose.\n",
            encoding="utf-8",
        )
        (root / "renames.csv").write_text(
            "old,new\ncampaign_token,campaign_renamed_token\n",
            encoding="utf-8",
        )
        return target

    def test_check_and_apply_preserve_drivers_and_reach_fixed_point(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test check and apply preserve drivers and reach fixed point."""
        target = self._seed(mod_workspace)
        projection = mod_workspace / "consumer.md"
        projection.symlink_to(target.name)
        driver = mod_workspace / "renames.csv"
        other = mod_workspace / "another.csv"
        other.write_bytes(driver.read_bytes())
        data = mod_workspace / "documentary.csv"
        data.write_text("description\ncampaign_token\n", encoding="utf-8")
        original_driver = driver.read_bytes()
        original = target.read_bytes()
        request = self._request(mod_workspace, apply=False).model_copy(
            update={"text_globs": ("**/*.md", "**/*.csv")},
        )
        checked = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(checked.occurrences, eq=2)
        tm.that(target.read_bytes(), eq=original)
        first = tm.ok(
            FlextInfraApplyRenames.run(request.model_copy(update={"apply": True})),
        )
        tm.that(first.files_changed >= 2, eq=True)
        tm.that(first.occurrences, eq=0)
        tm.that(
            target.read_text(),
            eq="A campaign_renamed_token keeps surrounding prose.\n",
        )
        tm.that(projection.is_symlink(), eq=True)
        tm.that(projection.read_bytes(), eq=target.read_bytes())
        tm.that(driver.read_bytes(), eq=original_driver)
        tm.that(other.read_bytes(), eq=original_driver)
        tm.that(data.read_text(), eq="description\ncampaign_renamed_token\n")
        second = tm.ok(
            FlextInfraApplyRenames.run(self._request(mod_workspace, apply=True)),
        )
        tm.that(second.files_changed, eq=0)
        tm.that(second.occurrences, eq=0)

    @pytest.mark.parametrize(
        ("rows", "error"),
        [
            ("from,to\ncampaign_token,new\n", "header must be exactly"),
            ("old,new\ncampaign_token,\n", "non-empty old,new values"),
            ("old,new\n", "at least one change"),
            ("old,new\na,b\na,c\n", "conflicting duplicate"),
            ("old,new\na,b\nb,a\n", "overlapping or cascading mappings"),
            ("old,new\na,b\nb,c\n", "overlapping or cascading mappings"),
            ("old,new\na,b\na.member,c\n", "overlapping or cascading mappings"),
        ],
    )
    def test_invalid_campaign_never_publishes(
        self,
        mod_workspace: Path,
        rows: str,
        error: str,
    ) -> None:
        """Test invalid campaign never publishes."""
        target = self._seed(mod_workspace)
        original = target.read_bytes()
        (mod_workspace / "renames.csv").write_text(rows, encoding="utf-8")
        with pytest.raises(ValueError, match=error):
            FlextInfraApplyRenames.run(self._request(mod_workspace, apply=True))
        tm.that(target.read_bytes(), eq=original)

    def test_documentation_changes_without_mutating_executable_strings(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test documentation changes without mutating executable strings."""
        self._seed(mod_workspace)
        consumer = mod_workspace / "consumer.py"
        consumer.write_text(
            '"""campaign_token""" " campaign_token"\n'
            "# campaign_token\n"
            'payload = "campaign_token"\n'
            "def read():\n"
            '    """campaign_token"""\n'
            "    return payload\n"
            'if __name__ == "__main__":\n'
            "    print(read())\n",
            encoding="utf-8",
        )
        tm.ok(FlextInfraApplyRenames.run(self._request(mod_workspace, apply=True)))
        output = tm.ok(u.Cli.run((sys.executable, str(consumer))))
        tm.that(output.stdout.strip(), eq="campaign_token")
        namespace = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "import consumer; print(consumer.__doc__); "
                        "print(consumer.read.__doc__)"
                    ),
                ),
                cwd=mod_workspace,
            ),
        )
        tm.that(
            namespace.stdout,
            eq=(
                "campaign_renamed_token campaign_renamed_token\n"
                "campaign_renamed_token\n"
            ),
        )

    @staticmethod
    def test_owned_method_declarations_and_callers_rename_atomically(
        mod_workspace: Path,
    ) -> None:
        """Real provider imports keep working without renaming parser homonyms."""
        driver = mod_workspace / "renames.csv"
        driver.write_text("old,new\nparse,parse_module\n", encoding="utf-8")
        (mod_workspace / "definer.py").write_text(
            "class ModuleSource:\n"
            "    @staticmethod\n"
            "    def parse(value):\n"
            "        return value.upper()\n"
            "class Parser:\n"
            "    @staticmethod\n"
            "    def parse(value, target):\n"
            "        return target(value)\n"
            "class Facade(Parser, ModuleSource):\n"
            "    pass\n"
            "BOOTSTRAP = ModuleSource.parse('ready')\n",
            encoding="utf-8",
        )
        consumer = mod_workspace / "consumer.py"
        consumer.write_text(
            "from definer import ModuleSource as chosen, Facade, BOOTSTRAP\n"
            "print(BOOTSTRAP, chosen.parse('source'), Facade.parse('7', int))\n",
            encoding="utf-8",
        )
        request = m.Infra.ApplyRenamesInput(
            csv=str(driver),
            roots=(str(mod_workspace),),
            bindings={"": ("definer.ModuleSource",)},
            rename_definitions=True,
            apply=True,
        )
        report = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(
            report.files_changed,
            eq=2,
            msg=(mod_workspace / "definer.py").read_text(encoding="utf-8"),
        )
        tm.that(report.occurrences, eq=0)
        output = tm.ok(u.Cli.run((sys.executable, str(consumer))))
        tm.that(output.stdout, eq="READY SOURCE 7\n")
        again = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(again.files_changed, eq=0)

    @staticmethod
    def test_rope_uses_current_owner_and_preserves_alias_homonyms(
        mod_workspace: Path,
    ) -> None:
        """Test rope uses current owner and preserves alias homonyms."""
        (mod_workspace / "renames.csv").write_text(
            "old,new\nOld,New\n",
            encoding="utf-8",
        )
        (mod_workspace / "definer.py").write_text(
            "class Public:\n    New = 37\n",
            encoding="utf-8",
        )
        consumer = mod_workspace / "external_consumer.py"
        consumer.write_text(
            "from definer import Public as renamed\n"
            "class Inherited(renamed):\n    pass\n"
            "class Overridden(renamed):\n    Old = 19\n"
            "class Homonym:\n    Old = 11\n"
            "def unrelated(renamed):\n    return renamed.Old\n"
            "print(renamed.Old, Inherited.Old, unrelated(Homonym), Overridden.Old)\n",
            encoding="utf-8",
        )
        request = m.Infra.ApplyRenamesInput(
            csv=str(mod_workspace / "renames.csv"),
            roots=(str(mod_workspace),),
            apply=True,
            bindings={"": ("definer.Public",)},
        )
        first = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(first.files_changed, eq=1)
        output = tm.ok(u.Cli.run((sys.executable, str(consumer))))
        tm.that(output.stdout, eq="37 37 11 19\n")
        second = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(second.files_changed, eq=0)
        tm.that(second.occurrences, eq=0)

    def test_missing_public_destination_prevents_text_publication(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test missing public destination prevents text publication."""
        target = self._seed(mod_workspace)
        (mod_workspace / "definer.py").write_text(
            "class Public:\n    Present = 1\n",
            encoding="utf-8",
        )
        before = target.read_bytes()
        request = self._request(mod_workspace, apply=True).model_copy(
            update={"bindings": {"": ("definer.Public",)}},
        )
        with pytest.raises(ValueError, match="no declared current public owner"):
            FlextInfraApplyRenames.run(request)
        tm.that(target.read_bytes(), eq=before)

    def test_untracked_unusual_filename_and_projection_exclusions(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test untracked unusual filename and projection exclusions."""
        self._seed(mod_workspace)
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=mod_workspace)))
        authored = mod_workspace / 'untracked "space"\nname.md'
        authored.write_text("campaign_token", encoding="utf-8")
        projected = mod_workspace / "generated.py"
        generated = f'{c.Infra.AUTOGEN_HEADERS[0]}\n"""campaign_token"""\n'
        projected.write_text(generated, encoding="utf-8")
        report = tm.ok(
            FlextInfraApplyRenames.run(self._request(mod_workspace, apply=True)),
        )
        tm.that(report.files_changed >= 2, eq=True)
        tm.that(authored.read_text(), eq="campaign_renamed_token")
        tm.that(projected.read_text(), eq=generated)

    def test_driver_drift_refuses_candidate_without_overwriting_consumer(
        self,
        mod_workspace: Path,
    ) -> None:
        """A drifted driver refuses exposure without restoring over live gains."""
        target = self._seed(mod_workspace)
        original = target.read_bytes()
        script = (
            "import sys\nfrom pathlib import Path\n"
            "from flext_infra import m\n"
            "from flext_infra.codemod import FlextInfraApplyRenames\n"
            "root = Path(sys.argv[1])\nchanged = False\n"
            "def interfere(event, args):\n"
            "    global changed\n"
            "    if event == 'os.rename' and Path(str(args[1])).name == 'guide.md'"
            " and not changed:\n"
            "        changed = True\n"
            "        (root / 'renames.csv')"
            ".write_text('old,new\\ncampaign_token,concurrent_name\\n')\n"
            "sys.addaudithook(interfere)\n"
            "result = FlextInfraApplyRenames.run(m.Infra.ApplyRenamesInput(\n"
            "    csv=str(root / 'renames.csv'), roots=(str(root),), apply=True,"
            " text_globs=('**/*.md',)))\n"
            "assert changed\nassert result.failure\n"
            "msg = result.error\n"
            "assert 'rename campaign driver changed during publish' in msg, msg\n"
        )
        tm.ok(u.Cli.run_checked((sys.executable, "-c", script, str(mod_workspace))))
        tm.that(target.read_bytes(), eq=original)
        tm.that((mod_workspace / "renames.csv").read_text(), has="concurrent_name")

    @staticmethod
    def test_sibling_repositories_resolve_installed_provider_and_local_mro(
        mod_workspace: Path,
    ) -> None:
        """Test sibling repositories resolve installed provider and local mro."""
        roots = (mod_workspace / "first", mod_workspace / "second")
        for directory in roots:
            package = directory / "src" / directory.name
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "owner.py").write_text(
                "from flext_cli import c\nclass Public(c):\n    pass\n",
                encoding="utf-8",
            )
            (package / "consumer.py").write_text(
                f"from {directory.name}.owner import Public as chosen\n"
                "print(chosen.Retired.PYPROJECT_FILENAME)\n",
                encoding="utf-8",
            )
        driver = mod_workspace / "renames.csv"
        driver.write_text(
            "old,new\nRetired.PYPROJECT_FILENAME,PYPROJECT_FILENAME\n",
            encoding="utf-8",
        )
        request = m.Infra.ApplyRenamesInput(
            csv=str(driver),
            roots=tuple(str(path) for path in roots),
            apply=True,
            bindings={"": ("flext_cli.c",)},
        )
        report = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(report.files_changed, eq=len(roots))
        for directory in roots:
            output = tm.ok(
                u.Cli.run(
                    (sys.executable, "-m", f"{directory.name}.consumer"),
                    cwd=directory / "src",
                ),
            )
            tm.that(output.stdout, eq=f"{c.PYPROJECT_FILENAME}\n")
        again = tm.ok(FlextInfraApplyRenames.run(request))
        tm.that(again.files_changed, eq=0)
