"""Resolved AST cutovers preserve payloads and independent spelling owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, m
from flext_infra.codemod import FlextInfraModTextGateEngine
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from tests import u


class TestsFlextInfraSymbolicTextCutover:
    """Exercise native findings, binding admission, and public publication."""

    @staticmethod
    @pytest.mark.parametrize("namespace", [False, True])
    @pytest.mark.parametrize("layout", ["same-root", "importing-folder"])
    def test_snapshot_preserves_child_lookup_with_a_file_owner(
        mod_workspace: Path,
        *,
        namespace: bool,
        layout: str,
    ) -> None:
        """Snapshot closure preserves the SDK's independent child resolution."""
        source = mod_workspace / c.Infra.DEFAULT_SRC_DIR
        importing = source if layout == "same-root" else mod_workspace / "consumer_area"
        importing.mkdir(exist_ok=True)
        package = importing / "search_owner"
        package.mkdir(parents=True)
        earlier = source / "search_owner.py"
        earlier.write_text("class Earlier:\n    pass\n", encoding="utf-8")
        if not namespace:
            (package / c.Infra.INIT_PY).write_text("", encoding="utf-8")
        child = package / "child.py"
        child.write_text("class Later:\n    pass\n", encoding="utf-8")
        consumer = importing / "consumer.py"
        consumer.write_text("from search_owner import child\n", encoding="utf-8")

        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
        )
        captured = {state.path: state.content for state in snapshot.states}
        tm.that(earlier in captured, eq=layout == "importing-folder")
        if layout == "importing-folder":
            tm.that(captured[earlier], eq=earlier.read_bytes())
        tm.that(captured[child], eq=child.read_bytes())

    @staticmethod
    def test_snapshot_preserves_imports_in_nested_statement_suites(
        mod_workspace: Path,
    ) -> None:
        """Static closure includes inactive function, handler, and case imports."""
        owners = ("function_owner", "handler_owner", "case_owner")
        for name in owners:
            (mod_workspace / f"{name}.py").write_text(
                "class Public:\n    pass\n",
                encoding="utf-8",
            )
        consumer = mod_workspace / "consumer.py"
        consumer.write_text(
            "def deferred():\n"
            "    import function_owner\n"
            "try:\n"
            "    pass\n"
            "except Exception:\n"
            "    import handler_owner\n"
            "match None:\n"
            "    case None:\n"
            "        import case_owner\n",
            encoding="utf-8",
        )

        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
        )

        captured = {state.path: state.content for state in snapshot.states}
        for name in owners:
            owner = mod_workspace / f"{name}.py"
            tm.that(captured[owner], eq=owner.read_bytes())

    @staticmethod
    def test_snapshot_preserves_importing_folder_owners(mod_workspace: Path) -> None:
        """A shared missing absolute module retains each folder's own source."""
        inputs: list[m.Cli.AtomicFileState] = []
        owners: list[Path] = []
        for package_name in ("left", "right"):
            package = mod_workspace / package_name
            package.mkdir()
            (package / c.Infra.INIT_PY).write_text("", encoding="utf-8")
            owner = package / "local_owner.py"
            owner.write_text(
                f"class {package_name.title()}:\n    pass\n",
                encoding="utf-8",
            )
            owners.append(owner)
            consumer = package / "consumer.py"
            consumer.write_text("import local_owner\n", encoding="utf-8")
            inputs.append(
                tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True))
            )

        snapshot = u.Infra.codemod_binding_snapshot(mod_workspace, tuple(inputs))

        captured = {state.path: state.content for state in snapshot.states}
        for owner in owners:
            tm.that(captured[owner], eq=owner.read_bytes())

    @staticmethod
    def test_binding_receipt_cannot_resolve_another_occurrence(
        mod_workspace: Path,
        binding_probe_rule: m.Infra.CodemodRule,
    ) -> None:
        """A stale span is rejected instead of falling back to another same name."""
        consumer = mod_workspace / "consumer.py"
        consumer.write_text("value = 1\n", encoding="utf-8")
        rule = binding_probe_rule.model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="OWNER",
                        predicate=c.Infra.CodemodContextPredicate.SAME_BINDING,
                        arg=("value",),
                        holds=True,
                    ),
                ),
            }
        )
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
        )
        with (
            u.Infra.codemod_binding_project(mod_workspace, snapshot) as (
                project,
                sources,
            ),
            pytest.raises(ValueError, match="binding capture differs from source"),
        ):
            u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=mod_workspace,
                    rule=rule,
                    file_path=consumer,
                    captures={
                        "OWNER": {
                            "text": "other",
                            "range": {"byteOffset": {"start": 0, "end": 5}},
                        }
                    },
                    facts=u.Infra.codemod_project_facts(mod_workspace, (rule,)),
                    snapshot=snapshot,
                ),
                project=project,
                sources=sources,
            )
        tm.that(consumer.read_text(encoding="utf-8"), eq="value = 1\n")

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
        imports = (
            "from tests import u, utilities\n"
            if binding == "same"
            else "from tests import utilities\n"
        )
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
        tm.that(all(not entry.actionable for entry in binding_findings), eq=True)
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
