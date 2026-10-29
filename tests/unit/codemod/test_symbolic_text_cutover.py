"""Resolved AST cutovers preserve payloads and independent spelling owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import json
import sys
import typing
from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraModTextGateEngine
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from tests import c, tm, u

if typing.TYPE_CHECKING:
    from tests import p


class TestsFlextInfraSymbolicTextCutover:
    """Exercise native findings, binding snapshots, and public publication."""

    @staticmethod
    def test_unresolved_imports_do_not_share_symbol_identity(tmp_path: Path) -> None:
        """Distinct unresolved imports cannot authorize a semantic rewrite."""
        consumer = tmp_path / "consumer.py"
        consumer.write_text(
            "from unavailable_first import first\n"
            "from unavailable_second import second\n",
            encoding="utf-8",
        )
        with (
            u.Infra.open_project(tmp_path) as project,
            u.Infra.semantic_matching_context(),
        ):
            module = u.Infra.resolve_pymodule(
                project, project.get_resource(consumer.name)
            )
            scope = tm.not_none(module.get_scope())
            first = tm.not_none(u.Infra.expression_name(scope, "first"))
            second = tm.not_none(u.Infra.expression_name(scope, "second"))
            tm.fail(u.Infra.same_name(first, second))

    @staticmethod
    def _observe_native_class_scope(
        root: Path,
        source: str,
        *,
        expression: str,
        proof: tuple[str | None, str],
        scope_name: str | None = None,
    ) -> None:
        """Compare real execution with the public closed native binding owner."""
        expected, runtime_output = proof
        consumer = root / "scope_consumer.py"
        consumer.write_text(source, encoding="utf-8")
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-I",
                    "-c",
                    (
                        "import runpy, sys; sys.path.insert(0, sys.argv[1]); "
                        "runpy.run_path(sys.argv[2])"
                    ),
                    str(root),
                    str(consumer),
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq=runtime_output)
        with (
            u.Infra.open_project(root) as project,
            u.Infra.semantic_matching_context(),
        ):
            module = u.Infra.resolve_pymodule(
                project, project.get_resource(consumer.name)
            )
            module_scope = tm.not_none(module.get_scope())
            scope = module_scope
            if scope_name is not None:
                pending = list(module_scope.get_scopes())
                selected: list[p.Infra.RopeScope] = []
                while pending:
                    candidate = pending.pop()
                    if candidate.pyobject.get_name() == scope_name:
                        selected.append(candidate)
                    pending.extend(candidate.get_scopes())
                tm.that(len(selected), eq=1)
                scope = selected[0]
            actual = u.Infra.resolve_symbol(
                scope,
                ast.parse(expression, mode="eval").body,
            )
            if expected is None:
                tm.that(actual, eq=None)
            else:
                provider = tm.not_none(
                    u.Infra.resolve_symbol(
                        module_scope,
                        ast.parse(expected, mode="eval").body,
                    ),
                )
                tm.ok(u.Infra.same_name(provider, actual))

    @classmethod
    @pytest.mark.parametrize(
        ("binding", "body", "runtime_output", "proven"),
        [
            (
                "earlier",
                (
                    "Chosen = Second\nclass Holder:\n"
                    "    Chosen = First\n    Alias = Chosen\n"
                    "print(Holder.Alias.ERROR)\n"
                ),
                "first",
                True,
            ),
            (
                "same-line",
                (
                    "Chosen = Second\nclass Holder:\n"
                    "    Chosen = First; Alias = Chosen\n"
                    "print(Holder.Alias.ERROR)\n"
                ),
                "first",
                True,
            ),
            (
                "rebound",
                (
                    "class Holder:\n    Alias = First\n    Alias = Second\n"
                    "print(Holder.Alias.ERROR)\n"
                ),
                "second",
                False,
            ),
            (
                "inherited-only",
                (
                    "class Parent:\n    Chosen = First\n"
                    "try:\n    class Holder(Parent):\n        Alias = Chosen\n"
                    "except NameError:\n    print('NameError')\n"
                ),
                "NameError",
                False,
            ),
            (
                "function",
                (
                    "Alias = First\ndef observed():\n"
                    "    Alias = Alias\n    return Alias.ERROR\n"
                    "try:\n    observed()\n"
                    "except UnboundLocalError:\n    print('UnboundLocalError')\n"
                ),
                "UnboundLocalError",
                False,
            ),
        ],
    )
    def test_native_class_alias_lookup_preserves_assignment_scope(
        cls,
        mod_workspace: Path,
        binding: str,
        body: str,
        runtime_output: str,
        *,
        proven: bool,
    ) -> None:
        """Point-specific class names retain real identity and reject rebindings."""
        source = (
            "from enum import StrEnum\n"
            "class First(StrEnum):\n    ERROR = 'first'\n"
            "class Second(StrEnum):\n    ERROR = 'second'\n" + body
        )
        cls._observe_native_class_scope(
            mod_workspace,
            source,
            expression="Alias.ERROR" if binding == "function" else "Holder.Alias.ERROR",
            proof=("First.ERROR" if proven else None, runtime_output),
            scope_name="observed" if binding == "function" else None,
        )

    @classmethod
    @pytest.mark.parametrize("module_import", [False, True])
    def test_prior_class_import_preserves_provider_identity(
        cls,
        mod_workspace: Path,
        *,
        module_import: bool,
    ) -> None:
        """A prior class import supplies its real provider over a global namesake."""
        (mod_workspace / "alias_provider.py").write_text(
            "class ImportedChoice:\n    ERROR = 'provider'\n",
            encoding="utf-8",
        )
        imported = (
            "    import alias_provider as Chosen\n    Alias = Chosen.ImportedChoice\n"
            if module_import
            else "    from alias_provider import ImportedChoice as Chosen\n"
            "    Alias = Chosen\n"
        )
        cls._observe_native_class_scope(
            mod_workspace,
            "import alias_provider as provider\n"
            "class ModuleChoice:\n    ERROR = 'module'\n"
            "Chosen = ModuleChoice\n"
            f"class Holder:\n{imported}"
            "print(Holder.Alias.ERROR)\n",
            expression="Holder.Alias.ERROR",
            proof=("provider.ImportedChoice.ERROR", "provider"),
        )

    @classmethod
    @pytest.mark.parametrize("outer_function", [False, True])
    def test_nested_class_refuses_future_function_local(
        cls,
        mod_workspace: Path,
        *,
        outer_function: bool,
    ) -> None:
        """A not-yet-bound enclosing local cannot supply a proven class identity."""
        body = (
            "def outer():\n"
            "    def observed():\n"
            "        class Holder:\n"
            "            Alias = Chosen\n"
            "        return Holder\n"
            "    result = observed()\n"
            "    Chosen = First\n"
            "    return result\n"
            "try:\n    outer()\n"
            if outer_function
            else "def observed():\n"
            "    class Holder:\n"
            "        Alias = Chosen\n"
            "    Chosen = First\n"
            "    return Holder\n"
            "try:\n    observed()\n"
        )
        cls._observe_native_class_scope(
            mod_workspace,
            "class First:\n    ERROR = 'global'\n"
            "Chosen = First\n"
            + body
            + "except NameError as error:\n    print(type(error).__name__)\n",
            expression="Holder.Alias.ERROR",
            proof=(None, NameError.__name__),
            scope_name="observed",
        )

    @classmethod
    @pytest.mark.parametrize("annotation_only", [False, True])
    def test_uninitialized_class_name_selects_module_global(
        cls,
        mod_workspace: Path,
        *,
        annotation_only: bool,
    ) -> None:
        """A class-local name reads the global instead of a different closure."""
        local = "Chosen: type" if annotation_only else "Chosen = Chosen"
        cls._observe_native_class_scope(
            mod_workspace,
            "class First:\n    ERROR = 'global'\n"
            "class Second:\n    ERROR = 'function'\n"
            "Chosen = First\n"
            "def observed():\n"
            "    Chosen = Second\n"
            "    class Holder:\n"
            f"        {local}\n"
            "        Alias = Chosen\n"
            "    return Holder\n"
            "Holder = observed()\n"
            "print(Holder.Alias.ERROR)\n",
            expression="Holder.Alias.ERROR",
            proof=("First.ERROR", c.ContextScope.GLOBAL),
            scope_name="observed",
        )

    @classmethod
    def test_conditional_class_prior_remains_unproven(
        cls,
        mod_workspace: Path,
    ) -> None:
        """Conditional class writes cannot masquerade as an executed prior."""
        cls._observe_native_class_scope(
            mod_workspace,
            "class First:\n    ERROR = 'conditional'\n"
            "class Second:\n    ERROR = 'global'\n"
            "Chosen = Second\n"
            "class Holder:\n"
            "    if False: Chosen = First\n"
            "    Alias = Chosen\n"
            "print(Holder.Alias.ERROR)\n",
            expression="Holder.Alias.ERROR",
            proof=(None, c.ContextScope.GLOBAL),
        )

    @classmethod
    def test_initialized_outer_local_preserves_class_identity(
        cls,
        mod_workspace: Path,
    ) -> None:
        """An outer value assigned before the inner definition retains identity."""
        cls._observe_native_class_scope(
            mod_workspace,
            "class First:\n    ERROR = 'outer'\n"
            "def outer():\n"
            "    Chosen = First\n"
            "    def observed():\n"
            "        class Holder:\n"
            "            Alias = Chosen\n"
            "        return Holder\n"
            "    return observed()\n"
            "Holder = outer()\n"
            "print(Holder.Alias.ERROR)\n",
            expression="Holder.Alias.ERROR",
            proof=("First.ERROR", "outer"),
            scope_name="observed",
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("binding", ["same", "absent", "independent"])
    def test_packaged_cutover_preserves_json_and_same_spelling_owners(
        mod_workspace: Path,
        binding: str,
    ) -> None:
        """The real legacy payload survives while proven code references migrate."""
        tests = mod_workspace / "tests"
        codegen = tests / "unit" / "codegen"
        codegen.mkdir(parents=True)
        (tests / "__init__.py").write_text(
            "from tests.utilities import TestsFlextInfraUtilities as u\n",
            encoding="utf-8",
        )
        (tests / "utilities.py").write_text(
            "class TestsFlextInfraUtilities:\n"
            "    class CodegenTestSupport:\n"
            "        class Ci:\n"
            "            value = 'owned'\n",
            encoding="utf-8",
        )
        consumer = codegen / "consumer.py"
        imports = "from tests import c, r, u, utilities\n"
        separate = (
            "class SeparateFacade:\n    pass\nu = SeparateFacade\n"
            if binding == "independent"
            else ""
        )
        source = (
            '"""utilities.TestsFlextInfraUtilities.CodegenTestSupport.Ci"""\n'
            "from __future__ import annotations\n"
            "import json\n"
            "from typing import Annotated, Literal\n"
            f"{imports}{separate}"
            "from flext_infra import c\n"
            '\npayload = \'{"status": "TOOL_ERROR"}\'\n'
            'spelling = "utilities.TestsFlextInfraUtilities.CodegenTestSupport.Ci"\n'
            'tag: Literal["utilities.TestsFlextInfraUtilities.CodegenTestSupport.Ci"]\n'
            "meta: Annotated[str, "
            '"utilities.TestsFlextInfraUtilities.CodegenTestSupport.Ci"]\n'
            "identity_metadata: Annotated[str, "
            "utilities.TestsFlextInfraUtilities.CodegenTestSupport.Ci]\n"
            "owned = utilities.TestsFlextInfraUtilities.CodegenTestSupport.Ci.value\n"
            'outcome = c.Infra.ToolOutcome.ERROR == "TOOL_ERROR"\n'
            "class Other:\n"
            "    class TestsFlextInfraUtilities:\n"
            "        class CodegenTestSupport:\n"
            "            class Ci:\n"
            "                value = 'independent'\n"
            "def independent(utilities):\n"
            "    return utilities.TestsFlextInfraUtilities."
            "CodegenTestSupport.Ci.value\n"
            "print(json.dumps([json.loads(payload), owned, independent(Other), "
            "spelling, __doc__, outcome]))\n"
        )
        consumer.write_text(source, encoding="utf-8")
        u.Tests.git_bootstrap(mod_workspace, ("add", "tests"))
        scanned = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        ids = {"codegen-test-public-utility-namespace", "gate-tool-error-typed-code"}
        selected = FlextInfraModGateEngine.recounted(
            tuple(entry for entry in scanned.entries if entry.rule_id in ids)
        )
        # The provider's c lives outside this synthetic closed project. Its
        # NoProject inference is explicitly unsupported, never a guessed fixer.
        tm.that(selected.actionable, eq=1 if binding == "same" else 0)
        binding_findings = tuple(
            entry
            for entry in scanned.entries
            if entry.rule_id == "codegen-test-public-utility-binding-required"
        )
        tm.that(len(binding_findings), eq=0 if binding == "same" else 1)
        tm.ok(all(not entry.actionable for entry in binding_findings))
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)
        tm.ok(FlextInfraModReplacements.publish(mod_workspace, selected))
        published = consumer.read_bytes()
        output = tm.ok(
            u.Cli.run(
                (sys.executable, "-m", "tests.unit.codegen.consumer"),
                cwd=mod_workspace,
            )
        )
        observed = json.loads(output.stdout)
        tm.that(observed[0], eq={"status": "TOOL_ERROR"})
        tm.that(observed[1:3], eq=["owned", "independent"])
        tm.that(observed[3], eq=observed[4])
        tm.that(observed[5], eq=str(c.Infra.ToolOutcome.ERROR) == "TOOL_ERROR")
        remaining = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.that(
            tuple(entry for entry in remaining.entries if entry.rule_id in ids),
            empty=True,
        )
        tm.that(consumer.read_bytes(), eq=published)

    @staticmethod
    def test_packaged_text_phase_preserves_the_json_counterexample(
        mod_workspace: Path,
    ) -> None:
        """Python syntax is insufficient: the actual consumer must still parse JSON."""
        project = mod_workspace / c.PYPROJECT_FILENAME
        project.write_text(
            project.read_text(encoding="utf-8").replace(
                'name = "mod-workspace"', 'name = "flext-infra"'
            ),
            encoding="utf-8",
        )
        guide = mod_workspace / "docs" / "guides" / "testing.md"
        guide.parent.mkdir(parents=True)
        guide.write_text("", encoding="utf-8")
        consumer = mod_workspace / "tests" / "payload.py"
        consumer.parent.mkdir(exist_ok=True)
        consumer.write_text(
            "import json\n"
            'payload = \'{"status": "TOOL_ERROR"}\'\n'
            "print(json.loads(payload)['status'])\n",
            encoding="utf-8",
        )
        original = consumer.read_bytes()
        tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.that(consumer.read_bytes(), eq=original)
        result = tm.ok(u.Cli.run((sys.executable, str(consumer)), cwd=mod_workspace))
        tm.that(result.stdout.strip(), eq="TOOL_ERROR")
