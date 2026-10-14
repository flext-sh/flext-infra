"""Rule-test snapshots change only through their explicit refresh, never in mod.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from flext_infra import c, main
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler
from tests import t, tm, u


class TestsFlextInfraModRuleFixtureSnapshots:
    """Verification rejects snapshot drift; the refresh records it for review."""

    @pytest.mark.slow
    def test_protocol_candidates_require_native_semantic_admission(
        self, tmp_path: Path
    ) -> None:
        """Raw superclass candidates retain only actual protocol declarations."""
        u.Tests.WorktreeFixture.write_python_project(tmp_path, "protocol-fixture")
        _ = self._owner(tmp_path)
        source_catalog = self._source_catalog(Path(__file__).resolve().parents[3])
        name = "ban-manual-protocol-outside-protocols"
        rule = self._catalog(tmp_path) / "rules" / f"{name}.yml"
        text = (source_catalog / "rules" / rule.name).read_text(
            encoding=c.DEFAULT_ENCODING
        )
        tm.ok(u.Cli.atomic_write_text_file(rule, text))
        plan = tm.ok(u.Infra.codemod_rule_plan(tmp_path))
        elected = next(item for item in plan.rules if item.resource == rule)
        u.Tests.provision_checkout(tmp_path)
        namespace = u.Infra.project_package_name(tmp_path)
        package = tmp_path / c.Infra.DEFAULT_SRC_DIR / namespace
        for path, text in (
            (
                package / "protocols.py",
                (
                    "from typing import Protocol\nclass Protocols:\n"
                    "    class Input(Protocol):\n        @property\n"
                    "        def value(self) -> str: ...\np = Protocols\n__all__ = ['p']\n"
                ),
            ),
            (
                package / c.Infra.INIT_PY,
                "from .protocols import p\n__all__ = ['p']\n",
            ),
        ):
            tm.ok(u.Cli.atomic_write_text_file(path, text))
        sample = package / "consumer.py"
        imports = (
            f"from typing import Protocol as Contract\nfrom {namespace} import p\n"
        )
        negative = (
            "class Base:\n    pass\nclass Service(Base):\n    pass\n"
            "class Implementation(p.Input):\n    pass\n"
            "class Protocol(Base):\n    pass\nclass Pretender(Protocol):\n    pass\n"
            "class Metadata(Base):\n    class Field(Base):\n        label: str\n"
            "    @property\n    def protocol(self) -> str:\n        return 'Protocol'\n"
            "def build():\n    class Local(Contract):\n        pass\n"
        )
        for declarations, expected in (
            (negative, []),
            (
                negative
                + "class Reader(Contract):\n    def read(self) -> str: ...\n"
                + "class Root:\n    class Input(Contract):\n        @property\n"
                + "        def value(self) -> str: ...\n"
                + "class PublicInput(p.Input, Contract):\n    pass\n",
                ["Reader", "Input", "PublicInput"],
            ),
        ):
            source = imports + declarations
            tm.ok(u.Cli.atomic_write_text_file(sample, source))
            report = tm.ok(
                FlextInfraModGateEngine.scan(
                    tmp_path, fix=False, rule_ids=(elected.id,)
                )
            )
            names: list[str] = []
            for finding in report.entries:
                tm.that(finding.rule_id, eq=elected.id)
                tm.that(finding.file, eq=sample.relative_to(tmp_path))
                mapping = u.type_adapter(t.JsonMapping)
                captures = mapping.validate_python(finding.payload["metaVariables"])
                single = mapping.validate_python(captures["single"])
                capture = mapping.validate_python(single[elected.context[0].variable])
                names.append(u.type_adapter(str).validate_python(capture["text"]))
            tm.that(sorted(names), eq=sorted(expected))
            tm.that(sample.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @pytest.mark.slow
    def test_failure_transport_uses_resolved_inherited_owner(
        self, tmp_path: Path
    ) -> None:
        """The native root guard admits inherited recovery, not foreign homonyms."""
        u.Tests.WorktreeFixture.write_python_project(tmp_path, "failure-transport")
        demo = self._owner(tmp_path)
        owner = Path(__file__).resolve().parents[3]
        source_catalog = self._source_catalog(owner)
        rule = self._catalog(tmp_path) / "rules" / "result-failure-rebind.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule,
                (source_catalog / "rules" / rule.name).read_text(
                    encoding=c.DEFAULT_ENCODING
                ),
            )
        )
        plan = tm.ok(u.Infra.codemod_rule_plan(tmp_path))
        selected = tuple(item.id for item in plan.rules if item.resource == rule)
        for fixture in (source_catalog / "tests").glob("*.yml"):
            if tm.ok(u.Cli.yaml_safe_load(fixture))["id"] in selected:
                tm.ok(
                    u.Cli.atomic_write_text_file(
                        self._catalog(tmp_path) / "tests" / fixture.name,
                        fixture.read_text(encoding=c.DEFAULT_ENCODING),
                    )
                )
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path, (demo, rule), apply=True
            )
        )
        u.Tests.provision_checkout(tmp_path)
        sample = tmp_path / "src" / "consumer.py"
        source = (
            "from flext_infra import p\n"
            "from flext_infra.codegen import FlextInfraCodegenTransaction\n"
            "class Consumer(FlextInfraCodegenTransaction):\n"
            "    def accept(self, layout, result: p.Result[bool]):\n"
            "        if result.failure:\n"
            "            return self._recover_failure(layout, result.error or 'context', "
            "exception=result.exception, error_code=result.error_code, error_data=result.error_data)\n"
            "    def unstable(self, layout, result, other):\n"
            "        if result.failure:\n"
            "            result = other\n"
            "            return self._recover_failure(layout, result.error or 'context')\n"
            "    def effectful(self, layout, result, context):\n"
            "        if result.failure:\n"
            "            return self._recover_failure(layout, result.error or context())\n"
            "    def getter(self, layout):\n"
            "        if self.result.failure:\n"
            "            return self._recover_failure(layout, self.result.error or 'context')\n"
            "class Foreign:\n"
            "    def _recover_failure(self, layout, text, **kwargs):\n"
            "        return text\n"
            "    def accept(self, layout, result):\n"
            "        if result.failure:\n"
            "            return self._recover_failure(layout, result.error or 'context')\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(sample, source))
        report = tm.ok(
            FlextInfraModGateEngine.scan(tmp_path, fix=False, rule_ids=selected)
        )
        tm.that(len(report.entries), eq=1)
        finding = report.entries[0]
        tm.that(finding.file, eq=sample.relative_to(tmp_path))
        tm.that(
            tm.not_none(finding.replacement), has="context=result.error or 'context'"
        )
        tm.that(sample.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @pytest.mark.parametrize("relative_catalog", ["policy", "nested/native/policy"])
    def test_native_snapshots_follow_declared_catalog_root(
        self,
        tmp_path: Path,
        relative_catalog: str,
    ) -> None:
        """Resolve and refresh a catalog without assuming its checkout location."""
        catalog = tmp_path / relative_catalog
        rule = self._owner(tmp_path, catalog_root=catalog)
        resolved = FlextInfraCodemodSnapshotReconciler.config_root(rule)
        tm.that(resolved, eq=catalog.resolve())
        directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(resolved)
        tm.that(len(directories.test_dirs), eq=1)
        snapshot = (
            directories.test_dirs[0]
            / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            / f"demo{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}"
        )
        changes = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        tm.that(changes, eq=(f"created {snapshot}",))
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))
        snapshots = tm.ok(u.Cli.yaml_safe_load(snapshot))["snapshots"]
        assert isinstance(snapshots, Mapping)
        for source, projection in snapshots.items():
            assert isinstance(source, str)
            assert isinstance(projection, Mapping)
            fixed = projection["fixed"]
            assert isinstance(fixed, str)
            _ = ast.parse(source)
            _ = ast.parse(fixed)
        tm.that((tmp_path / c.Infra.CODEMOD_CONFIG_RELPATH).exists(), eq=False)

    @pytest.mark.slow
    def test_contract_review_fixtures_preserve_assertions_and_syntax(
        self,
        tmp_path: Path,
    ) -> None:
        """Keep every reported contract defect intact through native apply."""
        u.Tests.WorktreeFixture.write_python_project(tmp_path, "rule-fixture")
        demo = self._owner(tmp_path)
        owner = Path(__file__).resolve().parents[3]
        rule_id = "remove-test-own-literal-tautology"
        catalog = self._catalog(tmp_path)
        for relative in (
            Path("rules") / f"{rule_id}.yml",
            Path("tests") / f"{rule_id}-test.yml",
        ):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    catalog / relative,
                    (self._source_catalog(owner) / relative).read_text(
                        encoding=c.DEFAULT_ENCODING,
                    ),
                ),
            )
        rule = catalog / "rules" / f"{rule_id}.yml"
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (demo, rule),
                apply=True,
            ),
        )
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (demo, rule)))
        u.Tests.provision_checkout(tmp_path)
        snapshots = tm.ok(u.Cli.yaml_safe_load(self._snapshot(tmp_path, rule_id)))[
            "snapshots"
        ]
        assert isinstance(snapshots, Mapping)
        tests = tmp_path / "tests"
        tm.ok(u.Cli.ensure_dir(tests))
        sample = tests / "test_consumer.py"
        for source, snapshot in snapshots.items():
            assert isinstance(source, str)
            assert isinstance(snapshot, Mapping)
            tm.that("fixed" in snapshot, eq=False)
            _ = ast.parse(source)
            tm.ok(u.Cli.atomic_write_text_file(sample, source))
            report = tm.ok(
                FlextInfraModGateEngine.scan(
                    tmp_path,
                    fix=True,
                    rule_ids=(rule_id,),
                ),
            )
            tm.that(report.actionable, eq=0)
            tm.that(report.detection_only, gt=0)
            for entry in report.entries:
                tm.that(entry.rule_id, eq=rule_id)
                tm.that(entry.replacement, eq=None)
            published = sample.read_text(encoding=c.DEFAULT_ENCODING)
            tm.that(published, eq=source)
            _ = ast.parse(published)

    @pytest.mark.slow
    def test_tautology_detection_preserves_runtime_and_unrelated_fixes(
        self, installed_dependency_path: Path
    ) -> None:
        """Native apply leaves effectful assertions intact and fixes other owners."""
        tmp_path, demo = self._provider(installed_dependency_path)
        u.Tests.provision_checkout(tmp_path)
        owner = Path(__file__).resolve().parents[3]
        rule_id = "remove-test-own-literal-tautology"
        rule = self._catalog(tmp_path) / "rules" / f"{rule_id}.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule,
                (self._source_catalog(owner) / "rules" / rule.name).read_text(
                    encoding=c.DEFAULT_ENCODING
                ),
            )
        )
        tests = tmp_path / "tests"
        tm.ok(u.Cli.ensure_dir(tests))
        sample = tests / "test_consumer.py"
        assertion = "assert (result.success or result.failure) and check(), explain()"
        source = (
            "events = []\n"
            "class Probe:\n"
            "    @property\n"
            "    def success(self):\n"
            "        events.append('success')\n        return False\n"
            "    @property\n"
            "    def failure(self):\n"
            "        events.append('failure')\n        return True\n"
            "def check():\n    events.append('check')\n    return False\n"
            "def explain():\n    events.append('message')\n    return 'contract'\n"
            "def foo(value):\n    return value\n"
            "def bar(value):\n    return value\n"
            "result = Probe()\nvalue = foo(1)\ntry:\n"
            f"    {assertion}\n"
            "except AssertionError as error:\n"
            "    assert error.args == ('contract',)\n"
            "else:\n    raise RuntimeError('meaningful check was erased')\n"
            "assert events == ['success', 'failure', 'check', 'message']\n"
            "assert value == 1\n"
        )
        tm.ok(u.Cli.atomic_write_text_file(sample, source))
        selected = ("demo", rule_id)
        elected = tm.ok(u.Infra.codemod_rule_plan(tmp_path, rule_ids=selected))
        tm.that(
            next(rule.resource for rule in elected.rules if rule.id == "demo"),
            eq=demo,
        )
        tm.fail(
            u.Infra.codemod_rule_plan(tmp_path, rule_ids=("undeclared-fixture-rule",)),
            has="unknown codemod rule IDs",
        )
        before = tm.ok(
            FlextInfraModGateEngine.scan(tmp_path, fix=False, rule_ids=selected)
        )
        tm.that(before.actionable, eq=1)
        tm.that(before.detection_only, eq=1)
        for _ in range(2):
            tm.ok(FlextInfraModGateEngine.scan(tmp_path, fix=True, rule_ids=selected))
            published = sample.read_text(encoding=c.DEFAULT_ENCODING)
            tm.that(published, eq=source.replace("value = foo(1)", "value = bar(1)"))
            tm.that(published, has=assertion)
            _ = ast.parse(published)
            outcome = tm.ok(u.Cli.run_raw((sys.executable, str(sample))))
            tm.that(outcome.exit_code, eq=0, msg=outcome.stderr)
            after = tm.ok(
                FlextInfraModGateEngine.scan(tmp_path, fix=False, rule_ids=selected)
            )
            tm.that(after.actionable, eq=0)
            tm.that(after.detection_only, eq=before.detection_only)
            tm.that(after.entries[0].replacement, eq=None)

    @pytest.mark.slow
    @pytest.mark.parametrize(("rule_suffix", "operator"), [("eq", "=="), ("ne", "!=")])
    @pytest.mark.parametrize("verdict", [True, False])
    def test_assert_message_fixes_preserve_comparison_evaluation(
        self,
        rule_suffix: str,
        operator: str,
        verdict: bool,
    ) -> None:
        """Execute native fixes with non-complementary operators and lazy messages.

        Args:
            rule_suffix: The suffix of the rule being tested.
            operator: The comparison operator used in the assertion.
            verdict: The expected boolean outcome of the assertion.

        Raises:
            TypeError: If the snapshot or fix is not of the expected type.
        """
        owner = Path(__file__).resolve().parents[3]
        original = (
            f"from flext_tests import tm\nassert left() {operator} right(), explain()\n"
        )
        snapshots = tm.ok(
            u.Cli.yaml_safe_load(
                self._source_catalog(owner)
                / "tests"
                / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
                / f"rewire-test-assert-{rule_suffix}-message{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}"
            ),
        )["snapshots"]
        if not isinstance(snapshots, Mapping):
            message = "Rule snapshots must be a mapping"
            raise TypeError(message)
        snapshot = snapshots[original]
        if not isinstance(snapshot, Mapping):
            message = "Rule snapshot must be a mapping"
            raise TypeError(message)
        fixed = snapshot["fixed"]
        if not isinstance(fixed, str):
            message = "Rule fix must be source text"
            raise TypeError(message)
        expected_events = ["left", "right", operator, "truth"]
        if not verdict:
            expected_events.append("message")
        setup = (
            "from flext_tests import tm\n"
            f"verdict = {verdict!r}\nevents = []\npayload = ('failure',)\n"
            "class Truth:\n"
            "    def __bool__(self):\n"
            "        events.append('truth')\n        return verdict\n"
            "class Probe:\n"
            "    def __eq__(self, other):\n"
            "        events.append('==')\n        return Truth()\n"
            "    def __ne__(self, other):\n"
            "        events.append('!=')\n        return Truth()\n"
            "def left():\n    events.append('left')\n    return Probe()\n"
            "def right():\n    events.append('right')\n    return Probe()\n"
            "def explain():\n    events.append('message')\n    return payload\n"
        )
        for candidate in (original, fixed):
            source = (
                setup
                + "try:\n"
                + "".join(f"    {line}\n" for line in candidate.splitlines())
                + "except AssertionError as error:\n"
                "    tm.that(verdict, truth=False)\n"
                "    tm.that(error.args, eq=(payload,))\n"
                "else:\n    tm.that(verdict, truth=True)\n"
                f"tm.that(events, eq={expected_events!r})\n"
            )
            outcome = tm.ok(u.Cli.run_raw((sys.executable, "-c", source)))
            tm.that(outcome.exit_code, eq=0, msg=outcome.stderr)
            tm.that(outcome.stderr, eq="")

    @pytest.mark.parametrize("collection", ["dict", "list"])
    def test_typing_collection_fixes_preserve_runtime_values(
        self,
        tmp_path: Path,
        collection: str,
    ) -> None:
        """Validate real fixes and execute concrete collection/Pydantic contracts."""
        owner = Path(__file__).resolve().parents[3]
        demo = self._owner(tmp_path)
        catalog = self._catalog(tmp_path)
        source_catalog = self._source_catalog(owner)
        tm.ok(u.Cli.ensure_dir(catalog / "utils"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                tmp_path / c.Infra.CODEMOD_CONFIG_RELPATH,
                "ruleDirs: [rules]\nutilDirs: [utils]\n"
                "testConfigs:\n  - testDir: tests\n",
            ),
        )
        for name in (
            "semantic-type-context",
            "typing-annotated-form",
            "typing-literal-form",
            "typing-module-binding",
            "t-locally-bound",
            f"typing-{collection}-generic",
            f"{collection}-imported-from-typing",
        ):
            relative = Path("utils") / f"{name}.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    catalog / relative,
                    (source_catalog / relative).read_text(encoding="utf-8"),
                ),
            )
        rule_id = (
            "typing-dict-to-mapping-kv"
            if collection == "dict"
            else "typing-list-to-sequence-of"
        )
        rule = catalog / "rules" / f"{rule_id}.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule,
                (source_catalog / "rules" / rule.name).read_text(encoding="utf-8"),
            ),
        )
        for selected_id in (rule_id, f"typing-{collection}-missing-t-import"):
            relative = Path("tests") / f"{selected_id}-test.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    catalog / relative,
                    (source_catalog / relative).read_text(encoding="utf-8"),
                ),
            )
        rules = (demo, rule)
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                rules,
                apply=True,
            ),
        )
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, rules))
        snapshots = tm.ok(u.Cli.yaml_safe_load(self._snapshot(tmp_path, rule_id)))[
            "snapshots"
        ]
        assert isinstance(snapshots, Mapping)
        runtime_consumers = 0
        for snapshot in snapshots.values():
            assert isinstance(snapshot, Mapping)
            fixed = snapshot["fixed"]
            assert isinstance(fixed, str)
            _ = ast.parse(fixed)
            if "class Payload(m.ArbitraryTypesModel):" in fixed:
                outcome = tm.ok(u.Cli.run_raw((sys.executable, "-c", fixed)))
                tm.that(outcome.exit_code, eq=0, msg=outcome.stderr)
                tm.that(outcome.stderr, eq="")
                runtime_consumers += 1
        tm.that(runtime_consumers, eq=1)

    @pytest.mark.parametrize("suffix", ["", "; value = 1", ";"])
    def test_managed_artifact_sequential_full_source_fixes_parse(
        self,
        tmp_path: Path,
        suffix: str,
    ) -> None:
        """Parse sequential pinned-engine outputs and prove both fixed points."""
        owner = Path(__file__).resolve().parents[3]
        private_import = (
            "from flext_infra._utilities.project_managed_artifacts import "
            "FlextInfraUtilitiesProjectManagedArtifacts"
        )
        source = (
            f"from flext_infra import u\n{private_import}{suffix}\n"
            "result = FlextInfraUtilitiesProjectManagedArtifacts."
            "snapshot_config_sources(root)\n"
        )
        _ = ast.parse(source)
        staged: list[tuple[Path, Path, Path, str]] = []
        for filename, rule_id, expect_fix in (
            (
                "rewire-project-managed-artifacts",
                "rewire-project-managed-artifacts-call",
                True,
            ),
            (
                "remove-project-managed-artifacts-private-import",
                "remove-project-managed-artifacts-private-import",
                not suffix,
            ),
        ):
            root = tmp_path / filename
            demo = self._owner(root)
            rule = self._catalog(root) / "rules" / f"{filename}.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rule,
                    (self._source_catalog(owner) / "rules" / rule.name).read_text(
                        encoding="utf-8",
                    ),
                ),
            )
            fixture = self._catalog(root) / "tests" / f"{rule_id}-test.yml"
            case = "  - |\n" + "".join(f"    {line}\n" for line in source.splitlines())
            tm.ok(
                u.Cli.atomic_write_text_file(
                    fixture,
                    f"id: {rule_id}\nvalid: []\ninvalid:\n{case}"
                    if expect_fix
                    else f"id: {rule_id}\nvalid:\n{case}invalid: []\n",
                ),
            )
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    root,
                    (demo, rule),
                    apply=True,
                ),
            )
            if expect_fix:
                snapshots = tm.ok(
                    u.Cli.yaml_safe_load(self._snapshot(root, rule_id)),
                )["snapshots"]
                assert isinstance(snapshots, Mapping)
                tm.that(len(snapshots), eq=1)
                snapshot = next(iter(snapshots.values()))
                assert isinstance(snapshot, Mapping)
                fixed = snapshot["fixed"]
                assert isinstance(fixed, str)
                source = fixed
            _ = ast.parse(source)
            staged.append((root, demo, rule, rule_id))
        tm.that(source, has="result = u.Infra.snapshot_config_sources(root)")
        tm.that(private_import in source, eq=bool(suffix))
        for root, demo, rule, rule_id in staged:
            case = "  - |\n" + "".join(f"    {line}\n" for line in source.splitlines())
            fixture = self._catalog(root) / "tests" / f"{rule_id}-test.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    fixture,
                    f"id: {rule_id}\nvalid:\n{case}invalid: []\n",
                ),
            )
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    root,
                    (demo, rule),
                    apply=True,
                ),
            )
            tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(root, (demo, rule)))

    def test_managed_artifact_cutover_preserves_live_export_owner(
        self,
        tmp_path: Path,
    ) -> None:
        """Run the owned rules against the live initializer and consumer fixtures."""
        demo = self._owner(tmp_path)
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (demo,),
                apply=True,
            ),
        )
        owner = Path(__file__).resolve().parents[3]
        catalog = self._source_catalog(owner)
        rules = [demo]
        for filename in (
            "remove-project-managed-artifacts-private-import",
            "rewire-project-managed-artifacts",
        ):
            source_rule = catalog / "rules" / f"{filename}.yml"
            rule = self._catalog(tmp_path) / "rules" / source_rule.name
            tm.ok(
                u.Cli.atomic_write_text_file(
                    rule,
                    source_rule.read_text(encoding="utf-8"),
                ),
            )
            rules.append(rule)
            rule_id = (
                "rewire-project-managed-artifacts-call"
                if filename == "rewire-project-managed-artifacts"
                else filename
            )
            for relative in (
                Path("tests") / f"{rule_id}-test.yml",
                Path("tests")
                / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
                / f"{rule_id}{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}",
            ):
                source = (catalog / relative).read_text(encoding="utf-8")
                if relative.name == f"{filename}-test.yml":
                    initializer = (
                        owner / "src/flext_infra/_utilities/__init__.py"
                    ).read_text(encoding="utf-8")
                    live_case = "  - |\n" + "".join(
                        f"    {line}\n" for line in initializer.splitlines()
                    )
                    source = source.replace("invalid:\n", f"{live_case}invalid:\n")
                destination = self._catalog(tmp_path) / relative
                tm.ok(u.Cli.ensure_dir(destination.parent))
                tm.ok(u.Cli.atomic_write_text_file(destination, source))

        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, tuple(rules)))
        for rule in rules[1:]:
            rule_id = tm.ok(u.Cli.yaml_safe_load(rule))["id"]
            assert isinstance(rule_id, str)
            cases = tm.ok(
                u.Cli.yaml_safe_load(
                    self._catalog(tmp_path) / "tests" / f"{rule_id}-test.yml",
                ),
            )["valid"]
            assert isinstance(cases, list)
            for source in cases:
                assert isinstance(source, str)
                _ = ast.parse(source)
            snapshots = tm.ok(u.Cli.yaml_safe_load(self._snapshot(tmp_path, rule_id)))[
                "snapshots"
            ]
            assert isinstance(snapshots, Mapping)
            fixed_cases = ""
            for snapshot in snapshots.values():
                assert isinstance(snapshot, Mapping)
                fixed = snapshot["fixed"]
                assert isinstance(fixed, str)
                _ = ast.parse(fixed)
                fixed_cases += "  - |\n" + "".join(
                    f"    {line}\n" for line in fixed.splitlines()
                )
            fixture = self._catalog(tmp_path) / "tests" / f"{rule_id}-test.yml"
            tm.ok(
                u.Cli.atomic_write_text_file(
                    fixture,
                    fixture.read_text(encoding="utf-8").replace(
                        "invalid:\n",
                        f"{fixed_cases}invalid:\n",
                    ),
                ),
            )
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, tuple(rules)))

    @staticmethod
    def _source_catalog(root: Path) -> Path:
        """Resolve the live provider from the canonical composed rule plan.

        Args:
            root: The root directory of the repository.

        Returns:
            The path to the live provider catalog.
        """
        plan = tm.ok(u.Infra.codemod_rule_plan(root))
        catalogs = tuple(
            ruleset.config.parent
            for ruleset in plan.rulesets
            if ruleset.config.is_relative_to(root)
        )
        tm.that(len(catalogs), eq=1)
        return catalogs[0]

    @staticmethod
    def _catalog(root: Path) -> Path:
        """Return the declared default for a new scratch catalog, not a provider.

        Returns:
            The directory holding the local ``sgconfig.yml`` the plan reads.

        """
        return root / c.Infra.CODEMOD_CONFIG_RELPATH.parent

    @classmethod
    def _owner(
        cls,
        root: Path,
        *,
        fix: str = "bar($A)",
        invalid: t.StrSequence = ("foo(1)",),
        catalog_root: Path | None = None,
    ) -> Path:
        """Declare one governed rule with its test in the local catalog.

        The fixture configuration declares its rule and test directories at the
        supplied catalog root. Git decides which provider a repository governs.

        Returns:
            The resulting ``Path``.

        """
        catalog = cls._catalog(root) if catalog_root is None else catalog_root
        config_path = catalog / c.Infra.CODEMOD_CONFIG_FILENAME
        for directory in (root / "src", catalog / "rules", catalog / "tests"):
            tm.ok(u.Cli.ensure_dir(directory))
        u.Tests.copy_tracked_mise_seeds(root)
        tm.ok(
            u.Cli.atomic_write_text_file(
                config_path,
                "ruleDirs: [rules]\ntestConfigs:\n  - testDir: tests\n",
            ),
        )
        rule = catalog / "rules" / "demo.yml"
        tm.ok(
            u.Cli.atomic_write_text_file(
                rule,
                "id: demo\nlanguage: python\nseverity: error\n"
                f"rule:\n  pattern: foo($A)\nfix: {fix}\n",
            ),
        )
        cases = "".join(f"  - {case}\n" for case in invalid)
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalog / "tests" / "demo-test.yml",
                f"id: demo\nvalid:\n  - baz(1)\ninvalid:\n{cases}",
            ),
        )
        # The rule engine runs ast-grep through the owner's pinned Mise lock,
        # which every governed repository carries; without it a host-global
        # binary (or none, on CI runners) answered instead.
        u.Tests.copy_tracked_mise_seeds(root)
        # A bare root becomes a checkout through its initial commit; an
        # existing checkout commits the catalog it now declares.
        if (root / c.Infra.GIT_DIR).exists():
            u.Tests.commit_git_changes(root, "Declare the demo rule catalog")
        else:
            u.Tests.initialize_git_repo(root)
        u.Tests.git_bootstrap(root, ("add", str(config_path.relative_to(root))))
        u.Tests.git_bootstrap(root, ("add", str(catalog.relative_to(root))))
        return rule

    @classmethod
    def _snapshot(cls, root: Path, rule_id: str = "demo") -> Path:
        """Return the committed snapshot path of one rule under ``root``.

        Returns:
            The committed snapshot path of one rule under ``root``.

        """
        return (
            cls._catalog(root)
            / "tests"
            / c.Infra.CODEMOD_SNAPSHOT_DIRNAME
            / f"{rule_id}{c.Infra.CODEMOD_SNAPSHOT_SUFFIX}"
        )

    @classmethod
    def _provider(cls, site: Path) -> tuple[Path, Path]:
        """Declare a real installed distribution and its governed fixture catalog.

        Returns:
            The resulting ``tuple[Path, Path]``.
        """
        name = "snapshot-fixture-provider"
        package = site / name.replace("-", "_")
        pyproject = u.Tests.WorktreeFixture.write_python_project(package, name)
        project = u.Tests.toml_table_at(
            pyproject.read_text(encoding=c.DEFAULT_ENCODING), "project"
        )
        version = project["version"]
        assert isinstance(version, str)
        dependencies = u.type_adapter(t.StrSequence).validate_python(
            project["dependencies"],
        )
        tm.ok(u.Cli.atomic_write_text_file(package / "__init__.py", ""))
        metadata = site / f"{name.replace('-', '_')}-{version}.dist-info"
        tm.ok(u.Cli.ensure_dir(metadata))
        tm.ok(
            u.Cli.atomic_write_text_file(
                metadata / "METADATA",
                f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
                + "".join(f"Requires-Dist: {value}\n" for value in dependencies),
            ),
        )
        rule = cls._owner(package)
        tm.ok(
            u.Cli.atomic_write_text_file(
                cls._catalog(package) / c.Infra.CODEMOD_CONFIG_FILENAME,
                f"{c.Infra.CODEMOD_SCOPE_KEY}: {c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n"
                "ruleDirs: [rules]\ntestConfigs:\n  - testDir: tests\n",
            ),
        )
        return package, rule

    def test_selected_rule_preserves_unselected_owner_snapshots(
        self, tmp_path: Path
    ) -> None:
        """Fixture validity belongs to the full catalog, not execution election."""
        rule = self._owner(tmp_path)
        other = rule.with_name("other.yml")
        tm.ok(
            u.Cli.atomic_write_text_file(
                other,
                rule.read_text(encoding=c.DEFAULT_ENCODING).replace(
                    "id: demo",
                    "id: other",
                ),
            ),
        )
        fixture = self._catalog(tmp_path) / "tests"
        tm.ok(
            u.Cli.atomic_write_text_file(
                fixture / "other-test.yml",
                (fixture / "demo-test.yml")
                .read_text(encoding=c.DEFAULT_ENCODING)
                .replace(
                    "id: demo",
                    "id: other",
                ),
            ),
        )
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule, other),
                apply=True,
            ),
        )
        snapshot = self._snapshot(tmp_path, "other")
        before = snapshot.read_bytes()
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))
        tm.that(
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    tmp_path,
                    (rule,),
                    apply=True,
                ),
            ),
            empty=True,
        )
        tm.that(snapshot.read_bytes(), eq=before)

    def test_refresh_records_what_verification_then_accepts(
        self,
        tmp_path: Path,
    ) -> None:
        """A dry refresh writes nothing; the applied refresh makes mod verify."""
        rule = self._owner(tmp_path)

        preview = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=False,
            ),
        )
        tm.that(preview, eq=(f"created {self._snapshot(tmp_path)}",))
        tm.that(self._snapshot(tmp_path).exists(), eq=False)
        tm.fail(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))

        applied = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )

        tm.that(applied, eq=preview)
        tm.that(self._snapshot(tmp_path).exists(), eq=True)
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))
        tm.that(
            tm.ok(
                FlextInfraModGateEngine.refresh_rule_snapshots(
                    tmp_path,
                    (rule,),
                    apply=True,
                ),
            ),
            empty=True,
        )

    def test_changed_rule_output_fails_verification_without_rewriting(
        self,
        tmp_path: Path,
    ) -> None:
        """Mod never accepts a new fix output as its own expectation."""
        rule = self._owner(tmp_path)
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        committed = self._snapshot(tmp_path).read_bytes()
        _ = self._owner(tmp_path, fix="qux($A)")

        failure = FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,))

        tm.fail(failure, has=c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT)
        tm.that(self._snapshot(tmp_path).read_bytes(), eq=committed)
        changes = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        tm.that(changes, eq=(f"updated {self._snapshot(tmp_path)}",))
        tm.that(self._snapshot(tmp_path).read_text(encoding="utf-8"), has="qux(1)")
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))

    @pytest.mark.parametrize("residue", ["removed-rule", "deleted-case"])
    def test_snapshot_residue_fails_verification_until_refreshed(
        self,
        tmp_path: Path,
        residue: str,
    ) -> None:
        """A snapshot no rule test produces is reported, then removed by refresh."""
        rule = self._owner(tmp_path, invalid=("foo(1)", "foo(2)"))
        tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        if residue == "removed-rule":
            stale = self._snapshot(tmp_path, "retired")
            tm.ok(
                u.Cli.atomic_write_text_file(
                    stale,
                    self
                    ._snapshot(tmp_path)
                    .read_text(encoding="utf-8")
                    .replace("id: demo", "id: retired"),
                ),
            )
            expected = f"removed {stale}"
        else:
            _ = self._owner(tmp_path, invalid=("foo(1)",))
            expected = f"updated {self._snapshot(tmp_path)}"

        failure = FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,))

        tm.fail(failure, has=c.Infra.CODEMOD_SNAPSHOT_REFRESH_HINT)
        changes = tm.ok(
            FlextInfraModGateEngine.refresh_rule_snapshots(
                tmp_path,
                (rule,),
                apply=True,
            ),
        )
        tm.that(changes, eq=(expected,))
        tm.ok(FlextInfraModGateEngine.validate_rule_fixtures(tmp_path, (rule,)))

    @pytest.mark.slow
    def test_public_refresh_route_dry_run_fails_until_applied(
        self,
        installed_dependency_path: Path,
    ) -> None:
        """The public route previews pending snapshots as red and applies them."""
        mod_workspace, _ = self._provider(installed_dependency_path)
        snapshot = self._snapshot(mod_workspace)
        route = ["refactor", "mod-snapshots", "--repository-root", str(mod_workspace)]

        tm.that(main(route), ne=0)
        tm.that(snapshot.exists(), eq=False)
        tm.that(main([*route, "--apply"]), eq=0)
        tm.that(snapshot.exists(), eq=True)
        tm.that(main(route), eq=0)
