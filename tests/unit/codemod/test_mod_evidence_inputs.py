"""Native occurrence evidence shares complete authenticated source inputs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, infra, m, main, t
from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraModEvidenceInputs:
    """Validate public evidence round-trips without duplicated input bodies."""

    @staticmethod
    @pytest.mark.parametrize("source", ["  Symbol  ", "block\n", "\tSymbol\t"])
    def test_native_capture_preserves_exact_source_bytes(source: str) -> None:
        """Whitespace belongs to the authenticated source, not normalization."""
        capture = m.Infra.AstGrepCapture.model_validate({
            "text": source,
            "range": {"byteOffset": {"start": 0, "end": len(source.encode("utf-8"))}},
        })
        tm.that(capture.text, eq=source)
        tm.that(capture.end_byte, eq=len(capture.text.encode("utf-8")))

    @staticmethod
    @pytest.mark.parametrize(
        ("declarations", "expected_lines"),
        [
            (
                (
                    "def load():\n"
                    "    import first_owner as selected\n"
                    "    import second_owner as selected\n"
                ),
                ((4, 5), (5, 6)),
            ),
            (
                (
                    "enabled = True\n"
                    "if enabled: from first_owner import Value\n"
                    "else: import second_owner\n"
                ),
                ((4, 5), (5, 6)),
            ),
            (
                (
                    "def load():\n"
                    "    yield from (); import first_owner; import second_owner\n"
                ),
                ((4, 5), (4, 5)),
            ),
            (
                (
                    "def load():\n"
                    "    message = 'café'; from first_owner import (\n"
                    "        Value as selected,\n"
                    "    )\n"
                    "    import second_owner\n"
                ),
                ((4, 7), (7, 8)),
            ),
        ],
    )
    def test_binding_snapshot_captures_all_native_import_scopes(
        mod_workspace: Path,
        declarations: str,
        expected_lines: tuple[tuple[int, int], ...],
    ) -> None:
        """Capture conditional and rebound imports while excluding textual decoys."""
        owners = tuple(
            mod_workspace / f"{name}_owner.py" for name in ("first", "second")
        )
        for owner in owners:
            tm.ok(
                u.Cli.atomic_write_text_file(
                    owner,
                    "class Value:\n    pass\n",
                ),
            )
        decoy = mod_workspace / "decoy_owner.py"
        tm.ok(u.Cli.atomic_write_text_file(decoy, "class Value:\n    pass\n"))
        consumer = mod_workspace / "consumer.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                consumer,
                "# import decoy_owner\n"
                "message = 'from decoy_owner import Value'\n" + declarations,
            ),
        )
        state = tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True))
        snapshot = u.Infra.codemod_binding_snapshot(mod_workspace, (state,))
        captured = {item.path for item in snapshot.states}
        tm.that(set(owners).issubset(captured))
        tm.that(decoy in captured, eq=False)
        with infra.rope_workspace(mod_workspace) as workspace:
            statements = u.Infra.source_import_statements(
                workspace.rope_project,
                consumer.read_text(encoding=c.DEFAULT_ENCODING),
            )
        tm.that(
            tuple((item.start_line, item.end_line) for item in statements),
            eq=expected_lines,
        )

    @staticmethod
    def test_composed_native_scan_preserves_provider_utils_and_local_shadows(
        mod_workspace: Path,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """One invocation keeps provider bindings and local utilities separate."""
        rules: list[m.Infra.CodemodRule] = []
        rulesets: list[m.Infra.CodemodRuleset] = []
        for provider in ("left", "right"):
            catalog = tmp_path / "providers" / provider
            rule_directory = catalog / c.Infra.CODEMOD_RULE_DIRS_KEY
            utility_directory = catalog / c.Infra.CODEMOD_UTIL_DIRS_KEY
            rule_directory.mkdir(parents=True)
            utility_directory.mkdir()
            configuration = catalog / c.Infra.CODEMOD_CONFIG_FILENAME
            tm.ok(
                u.Cli.yaml_dump(
                    configuration,
                    {
                        c.Infra.CODEMOD_RULE_DIRS_KEY: [rule_directory.name],
                        c.Infra.CODEMOD_UTIL_DIRS_KEY: [utility_directory.name],
                    },
                )
            )
            tm.ok(
                u.Cli.yaml_dump(
                    utility_directory / f"shared{c.Infra.CODEMOD_RULE_SUFFIX}",
                    {
                        "id": "shared",
                        "language": "Python",
                        "rule": {"pattern": repr(provider)},
                    },
                )
            )
            tm.ok(
                u.Cli.yaml_dump(
                    rule_directory / f"global{c.Infra.CODEMOD_RULE_SUFFIX}",
                    {
                        "id": f"{provider}-global",
                        "language": "Python",
                        "severity": "error",
                        "rule": {"matches": "shared"},
                    },
                )
            )
            if provider == "left":
                tm.ok(
                    u.Cli.yaml_dump(
                        rule_directory / f"local{c.Infra.CODEMOD_RULE_SUFFIX}",
                        {
                            "id": f"{provider}-local",
                            "language": "Python",
                            "severity": "error",
                            "utils": {"shared": {"pattern": repr("local")}},
                            "rule": {"matches": "shared"},
                        },
                    )
                )
            selected = tm.ok(u.Infra.codemod_catalog_rules(provider, configuration))
            rules.extend(selected)
            rulesets.append(
                m.Infra.CodemodRuleset(
                    provider=provider,
                    config=configuration,
                    rule_ids=tuple(rule.id for rule in selected),
                    fixable_rule_ids=tuple(
                        rule.id for rule in selected if rule.fixable
                    ),
                )
            )
        plan = m.Infra.CodemodRulePlan(
            provider_order=tuple(ruleset.provider for ruleset in rulesets),
            rules=tuple(rules),
            rulesets=tuple(rulesets),
            project_rule_ids={
                mod_workspace.resolve(): tuple(rule.id for rule in rules)
            },
        )
        source = mod_workspace / "consumer.py"
        source.write_text("a = 'left'\nb = 'right'\nc = 'local'\n", encoding="utf-8")
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, plan=plan, source_files=(source,)
            )
        )
        console = capsys.readouterr()
        tm.that(console.err.count(f"mod: start {c.Infra.SG} scan"), eq=1)
        tm.that(
            sorted((entry.rule_id, entry.text) for entry in report.entries),
            eq=[
                ("left-global", "'left'"),
                ("left-local", "'local'"),
                ("right-global", "'right'"),
            ],
        )
        duplicate_rules = tuple(
            rule.model_copy(update={"id": rules[0].id})
            if rule.provider == rules[-1].provider
            else rule
            for rule in rules
        )
        for index, conflicting in enumerate((
            m.Infra.CodemodRulePlan(
                provider_order=plan.provider_order,
                rules=duplicate_rules,
                rulesets=plan.rulesets,
                project_rule_ids=plan.project_rule_ids,
            ),
            plan.model_copy(update={"rules": duplicate_rules}),
        )):
            destination = tmp_path / f"conflicting-native-{index}"
            with pytest.raises(ValueError, match="native codemod rule IDs"):
                u.Infra.codemod_stage_scan_ruleset(conflicting, destination)
            tm.that(destination.exists(), eq=False)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        resource = rules[0].resource
        declaration = tm.ok(u.Cli.yaml_safe_load(resource))
        tm.ok(
            u.Cli.yaml_dump(
                resource,
                {**declaration, "rule": {"pattern": repr("changed")}},
            ),
        )
        with pytest.raises(
            ValueError, match="elected codemod rule changed before projection"
        ):
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, plan=plan, source_files=(source,)
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True)),
            eq=before,
        )

    @staticmethod
    def test_native_record_digest_and_operational_fields_fail_closed(
        mod_workspace: Path,
    ) -> None:
        """Complete native evidence refuses altered references and mismatched fields."""
        source = mod_workspace / "consumer.py"
        source.write_text(
            "def edge(value: str) -> str:\n    return str(value)\n",
            encoding="utf-8",
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, rule_ids=("ban-pass-through-wrapper",)
            )
        )
        tm.that(report.findings, eq=1)
        finding = report.entries[0]
        with u.Infra.mod_native_readers(report.native_artifacts) as readers:
            raw = u.Infra.mod_native_payload(finding, readers)
            tm.that(raw["text"], eq=finding.text)
            corrupted = finding.model_copy(
                update={
                    "native_record": m.Infra.ModNativeRecord(
                        offset=finding.native_record.offset,
                        length=finding.native_record.length,
                        sha256=u.Cli.sha256_bytes(b"foreign record"),
                    ),
                }
            )
            with pytest.raises(ValueError, match="record digest"):
                u.Infra.mod_native_payload(corrupted, readers)
            changed = finding.model_copy(update={"text": "foreign source"})
            with pytest.raises(ValueError, match="operational fields"):
                u.Infra.mod_native_payload(changed, readers)

    @staticmethod
    def test_native_report_requires_output_even_when_no_occurrences(
        mod_workspace: Path,
    ) -> None:
        """A zero report still records and authenticates the scanner's real output."""
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, rule_ids=("ban-pass-through-wrapper",)
            )
        )
        tm.that(report.findings, eq=0)
        tm.that(bool(report.native_artifacts))
        evidence = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes()
        )
        tm.that(evidence.native_artifacts, eq=report.native_artifacts)
        with u.Infra.mod_native_readers(evidence.native_artifacts) as readers:
            artifact = evidence.native_artifacts[0]
            tm.that(
                u.Cli.sha256_bytes(
                    readers[artifact.path].read_range(0, tm.not_none(artifact.size))
                ),
                eq=artifact.sha256,
            )

    @staticmethod
    def test_native_jsonl_preserves_large_unicode_record(mod_workspace: Path) -> None:
        """A real native record spanning read blocks retains complete evidence."""
        source = mod_workspace / "consumer.py"
        content = (
            'def edge(value: str = "'
            + "é\u2028" * 600_000
            + '") -> str:\n    return str(value)\n'
        )
        source.write_text(content, encoding="utf-8")
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, rule_ids=("ban-pass-through-wrapper",)
            )
        )
        tm.that(report.findings, eq=1)
        finding = report.entries[0]
        tm.that(finding.text, eq=content.rstrip("\n"))
        with u.Infra.mod_native_readers(report.native_artifacts) as readers:
            native = u.Infra.mod_native_payload(finding, readers)
        tm.that(native["text"], eq=finding.text)
        tm.that(tm.not_none(finding.source_state).content, eq=content.encode("utf-8"))
        evidence = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes()
        )
        with u.Infra.mod_native_readers(evidence.native_artifacts) as readers:
            restored = u.Infra.mod_native_payload(evidence.entries[0], readers)
        tm.that(restored, eq=native)
        tm.that(evidence.native_artifacts, eq=report.native_artifacts)

    @staticmethod
    @pytest.mark.slow
    def test_full_diagnostic_runs_one_native_scan(
        mod_workspace: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The public whole-catalog summary consumes the existing scan receipt."""
        exit_code = main(["refactor", "ast", "--repository-root", str(mod_workspace)])
        console = capsys.readouterr()
        evidence = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes()
        )
        tm.that(console.err.count(f"mod: start {c.Infra.SG} scan"), eq=1)
        tm.that(console.err.count("mod: capture bindings projects="), eq=1)
        if evidence.findings:
            tm.that(exit_code, ne=0)

    @staticmethod
    def test_selected_projects_share_capture_without_mixing_bindings(
        tmp_path: Path,
    ) -> None:
        """One immutable capture keeps each same-spelling import's real owner."""
        selections, inputs = TestsFlextInfraModEvidenceInputs._built_binding_projects(
            tmp_path
        )
        snapshot = u.Infra.codemod_binding_snapshot(
            tmp_path, tuple(inputs), projects=tuple(selections)
        )
        TestsFlextInfraModEvidenceInputs._verified_owner_bindings(selections, snapshot)

    @staticmethod
    def _built_binding_projects(
        tmp_path: Path,
    ) -> tuple[list[m.Infra.CodemodBindingProject], list[m.Cli.AtomicFileState]]:
        """Build two same-spelling binding projects with distinct owners.

        Args:
            tmp_path: Test scratch root owning both projects.

        Returns:
            The binding selections with their captured consumer states.

        """
        selections: list[m.Infra.CodemodBindingProject] = []
        inputs: list[m.Cli.AtomicFileState] = []
        for name in ("left", "right"):
            project = u.Tests.mk_project(
                tmp_path,
                name,
                pyproject=f'[project]\nname = "{name}"\nversion = "0.1.0"\n',
                with_src=True,
            )
            owner = project / "owner.py"
            owner.write_text(f"class Public:\n    value = '{name}'\n", encoding="utf-8")
            consumer = project / "consumer.py"
            consumer.write_text(
                "from __future__ import annotations\n"
                "from owner import Public\nvalue = Public\n",
                encoding="utf-8",
            )
            inputs.append(
                tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True))
            )
            selections.append(
                m.Infra.CodemodBindingProject(
                    root=project, source_paths=(consumer,), modules=()
                )
            )
        return selections, inputs

    @staticmethod
    def _verified_owner_bindings(
        selections: list[m.Infra.CodemodBindingProject],
        snapshot: m.Infra.CodemodBindingSnapshot,
    ) -> None:
        """Verify each project's consumer resolves to its own captured owner.

        Args:
            selections: The binding selections under proof.
            snapshot: The shared immutable binding capture.

        """
        paths = [state.path for state in snapshot.states]
        tm.that(len(paths), eq=len(set(paths)))
        epoch = u.Infra.codemod_source_epoch(snapshot)
        for selection in selections:
            owner = selection.root / "owner.py"
            tm.that(owner in paths)
            owner.write_text("invalid syntax !!!\n", encoding="utf-8")
            with u.Infra.codemod_binding_project(selection.root, epoch) as (
                project,
                sources,
            ):
                tm.that(sources is epoch.sources)
                consumer = selection.source_paths[0]
                module = u.Infra.resolve_pymodule(
                    project,
                    u.Infra.require_file_resource(
                        project.get_resource(consumer.name), consumer
                    ),
                )
                offset = sources[consumer].rindex("Public")
                tm.that(
                    u.Infra.name_definition_resource_path(module, offset),
                    eq=str(owner),
                )

    @staticmethod
    @pytest.mark.parametrize(("occurrences", "resources"), [(2, 0), (96, 32)])
    def test_native_occurrences_share_authenticated_inputs(
        mod_workspace: Path, occurrences: int, resources: int
    ) -> None:
        """Distinct binding groups share inputs through both JSON publication paths."""
        report, snapshot, inputs, source, owner = (
            TestsFlextInfraModEvidenceInputs._scanned_shared_occurrences(
                mod_workspace, occurrences
            )
        )
        for index in range(resources):
            resource = mod_workspace / f"binding_{index}.py"
            resource.write_text(f"value = {index}\n", encoding="utf-8")
            inputs.append(
                tm.ok(u.Cli.atomic_read_binary_file_state(resource, required=True))
            )
        bindings = (
            (*inputs, inputs[0], inputs[-1], inputs[0]),
            (inputs[0],),
            tuple(reversed(inputs)),
            (),
            tuple(inputs[:1]),
        )
        report = report.model_copy(
            update={
                "entries": tuple(
                    entry.model_copy(
                        update={
                            "binding_states": bindings[index % len(bindings)],
                            **(
                                {
                                    "source_state": None,
                                    "classification": (
                                        c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT
                                    ),
                                    "actionable": False,
                                }
                                if index == occurrences - 1
                                else {}
                            ),
                        }
                    )
                    for index, entry in enumerate(report.entries)
                )
            }
        )
        receipt = tm.ok(
            u.Infra.publish_mod_scan_evidence(
                mod_workspace,
                report,
                publication=m.Infra.ModScanPublication(
                    command=c.Infra.ModScanCommand.SCAN, scope=(str(source),)
                ),
            )
        )
        encoded = receipt.path.read_bytes()
        restored = m.Infra.ModScanEvidence.model_validate_json(encoded)
        source_state = tm.not_none(report.entries[0].source_state)
        content = t.Infra.STR_ADAPTER.dump_json(
            t.Infra.STR_ADAPTER.validate_python(
                source_state.model_dump(mode="json")["content"],
                strict=True,
            ),
        )
        tm.that(encoded.count(content), eq=1)
        tm.that(
            sum(state.path == source for state in restored.inputs.states),
            eq=1,
        )
        tm.that(u.Cli.sha256_bytes(encoded), eq=receipt.sha256)
        tm.that(restored.deferred, eq=1)
        tm.that(
            len(restored.binding_graphs),
            eq=len({
                tuple(state.path for state in entry.binding_states)
                for entry in report.entries
            }),
        )
        shared: dict[int, tuple[m.Cli.AtomicFileState, ...]] = {}
        for original, occurrence in zip(report.entries, restored.entries, strict=True):
            tm.that(occurrence.native_record, eq=original.native_record)
            tm.that(occurrence.source_state, eq=original.source_state)
            tm.that(occurrence.binding_states, eq=original.binding_states)
            tm.that(
                restored.binding_graphs[occurrence.binding_graph],
                eq=tuple(state.path for state in original.binding_states),
            )
            tm.that(occurrence.classification, eq=original.classification)
            tm.that(
                occurrence.binding_states
                is shared.setdefault(
                    occurrence.binding_graph, occurrence.binding_states
                )
            )
        tm.that(
            len(restored.inputs.states),
            eq=len({
                state.path for state in (*tm.not_none(report.source_states), *inputs)
            }),
        )
        nested = TestsFlextInfraModEvidenceInputs._verified_nested_evidence(
            mod_workspace, receipt, restored, inputs, report
        )
        closure = nested.evidence.entries[0].binding_states
        tm.that(closure[-1] is closure[0])
        owner.write_text("invalid syntax !!!\n", encoding="utf-8")
        with u.Infra.codemod_binding_project(
            mod_workspace,
            u.Infra.codemod_source_epoch(
                m.Infra.CodemodBindingSnapshot(states=closure)
            ),
        ) as (project, sources):
            tm.that(
                u.Infra.name_definition_resource_path(
                    u.Infra.resolve_pymodule(
                        project,
                        u.Infra.require_file_resource(
                            project.get_resource(source.name), source
                        ),
                    ),
                    sources[source].rindex("Public"),
                ),
                eq=str(owner),
            )
        TestsFlextInfraModEvidenceInputs._rejected_tampered_evidence(restored, snapshot)

    @staticmethod
    def _scanned_shared_occurrences(
        mod_workspace: Path,
        occurrences: int,
    ) -> tuple[
        m.Infra.ModScanReport,
        m.Infra.CodemodBindingSnapshot,
        list[m.Cli.AtomicFileState],
        Path,
        Path,
    ]:
        """Scan the shared-occurrence workspace with its authenticated inputs.

        Args:
            mod_workspace: The governed mod workspace root.
            occurrences: The expected native finding count.

        Returns:
            The scanned report, its binding snapshot, the captured inputs,
            the consumer source and the binding owner.

        """
        source = mod_workspace / "consumer.py"
        owner = mod_workspace / "binding_owner.py"
        owner.write_text("class Public:\n    value = 'captured'\n", encoding="utf-8")
        source.write_text(
            "# descriptor evidence sentinel\nfrom __future__ import annotations\n"
            "from binding_owner import Public\n"
            + "".join(
                f"def call_{index}(value: str) -> str:\n    return str(value)\n"
                for index in range(occurrences)
            ),
            encoding="utf-8",
        )
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, rule_ids=("ban-pass-through-wrapper",)
            )
        )
        tm.that(report.findings, eq=occurrences)
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace, (tm.not_none(report.entries[0].source_state),)
        )
        return report, snapshot, list(snapshot.states), source, owner

    @staticmethod
    def _verified_nested_evidence(
        mod_workspace: Path,
        receipt: m.Infra.ModScanEvidenceReceipt,
        restored: m.Infra.ModScanEvidence,
        inputs: list[m.Cli.AtomicFileState],
        report: m.Infra.ModScanReport,
    ) -> m.Infra.ModScanEvidenceReceipt:
        """Publish the evidence again and prove nested identity sharing.

        Args:
            mod_workspace: The governed mod workspace root.
            receipt: The original evidence publication receipt.
            restored: The restored evidence payload.
            inputs: Every captured input state of the run.
            report: The original scanner's source inventory.

        Returns:
            The nested evidence receipt with its identity proof.

        """
        nested_path = tm.ok(
            u.Infra.publish_refactor_report_evidence(
                mod_workspace, receipt, relative_path=Path("nested-evidence.json")
            )
        )
        nested = m.Infra.ModScanEvidenceReceipt.model_validate_json(
            nested_path.read_bytes()
        )
        tm.that(nested.evidence, eq=restored)
        tm.that(nested.sha256, eq=u.Cli.sha256_bytes(nested.path.read_bytes()))
        indexed = {state.path: state for state in nested.evidence.inputs.states}
        for occurrence in nested.evidence.entries:
            if occurrence.source_path is not None:
                tm.that(occurrence.source_state is indexed[occurrence.source_path])
            for state in occurrence.binding_states:
                tm.that(state is indexed[state.path])
        tm.that(
            len(restored.inputs.states),
            eq=len({
                state.path for state in (*tm.not_none(report.source_states), *inputs)
            }),
        )
        return nested

    @staticmethod
    def _rejected_tampered_evidence(
        restored: m.Infra.ModScanEvidence,
        snapshot: m.Infra.CodemodBindingSnapshot,
    ) -> None:
        """Reject every tampered evidence projection at its validation boundary.

        Args:
            restored: The restored evidence payload to tamper with.
            snapshot: The binding snapshot whose duplicate states are invalid.

        """
        for updates, expected_key in (
            (
                {
                    "entries": (
                        restored.entries[0].model_copy(
                            update={"source_path": Path("absent_source.py")}
                        ),
                        *restored.entries[1:],
                    )
                },
                Path("absent_source.py"),
            ),
            (
                {
                    "binding_graphs": (
                        (Path("absent_binding.py"),),
                        *restored.binding_graphs[1:],
                    )
                },
                Path("absent_binding.py"),
            ),
            (
                {
                    "binding_graphs": (
                        (Path("absent_binding.py"),),
                        *restored.binding_graphs[1:],
                    ),
                    "entries": (
                        restored.entries[0].model_copy(
                            update={"source_path": Path("absent_source.py")}
                        ),
                        *restored.entries[1:],
                    ),
                },
                Path("absent_binding.py"),
            ),
        ):
            tampered = restored.model_copy(update=updates)
            with pytest.raises(KeyError) as missing:
                m.Infra.ModScanEvidence.model_validate_json(
                    tampered.model_dump_json(round_trip=True)
                )
            tm.that(missing.value.args, eq=(expected_key,))
        tampered_graph = restored.model_copy(
            update={
                "entries": (
                    restored.entries[0].model_copy(
                        update={"binding_graph": len(restored.binding_graphs)}
                    ),
                    *restored.entries[1:],
                )
            }
        )
        with pytest.raises(m.ValidationError, match="binding graph is missing"):
            m.Infra.ModScanEvidence.model_validate_json(
                tampered_graph.model_dump_json(round_trip=True)
            )
        for field in ("totals_by_repository", "totals_by_rule"):
            totals = dict(getattr(restored, field))
            totals[next(iter(totals))] += 1
            with pytest.raises(m.ValidationError, match="totals differ"):
                m.Infra.ModScanEvidence.model_validate_json(
                    restored.model_copy(update={field: totals}).model_dump_json(
                        round_trip=True
                    )
                )
        with pytest.raises(m.ValidationError):
            m.Infra.ModScanEvidence.model_validate_json(
                restored.model_copy(
                    update={
                        "schema_version": c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION - 1
                    }
                ).model_dump_json(round_trip=True)
            )
        with pytest.raises(m.ValidationError):
            m.Infra.CodemodBindingSnapshot(
                states=(
                    snapshot.states[0],
                    snapshot.states[0].model_copy(update={"content": b"changed"}),
                )
            )

    @staticmethod
    def test_empty_scan_retains_zero_inventory(mod_workspace: Path) -> None:
        """An empty native result publishes a complete zero-count inventory."""
        source = mod_workspace / "consumer.py"
        source.write_text("value = 1\n", encoding="utf-8")
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace, fix=False, rule_ids=("ban-pass-through-wrapper",)
            )
        )
        tm.that(report.findings, eq=0)
        receipt = tm.ok(
            u.Infra.publish_mod_scan_evidence(
                mod_workspace,
                report,
                publication=m.Infra.ModScanPublication(
                    command=c.Infra.ModScanCommand.SCAN,
                    scope=(str(source),),
                    repositories=(mod_workspace.name,),
                    rule_ids=("ban-pass-through-wrapper",),
                ),
            )
        )
        restored = m.Infra.ModScanEvidence.model_validate_json(
            receipt.path.read_bytes()
        )
        tm.that(restored.entries, eq=())
        tm.that(restored.binding_graphs, eq=())
        tm.that(restored.totals_by_repository, eq={mod_workspace.name: 0})
        tm.that(restored.totals_by_rule, eq={"ban-pass-through-wrapper": 0})
