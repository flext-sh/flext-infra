"""Real transactional CSV campaigns and identity-bound external consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from flext_infra import c, m, u
from flext_infra.codemod import FlextInfraApplyRenames, FlextInfraRenameSymbols
from tests import tm


class TestsFlextInfraApplyRenames:
    """Campaigns change declared sources, preserve drivers, and prove convergence."""

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
        tm.that(first.files_changed, eq=2)
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
        tm.that(report.files_changed, eq=2)
        tm.that(authored.read_text(), eq="campaign_renamed_token")
        tm.that(projected.read_text(), eq=generated)

    def test_driver_drift_during_publication_rolls_back_consumer(
        self,
        mod_workspace: Path,
    ) -> None:
        """Test driver drift during publication rolls back consumer."""
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
            "assert 'rename campaign driver changed during publish' in result.error, result.error\n"
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
