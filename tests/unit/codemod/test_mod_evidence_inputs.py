"""Native occurrence evidence shares complete authenticated source inputs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m, main
from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraModEvidenceInputs:
    """Validate public evidence round-trips without duplicated input bodies."""

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
        snapshot = u.Infra.codemod_binding_snapshot(
            tmp_path, tuple(inputs), projects=tuple(selections)
        )
        paths = [state.path for state in snapshot.states]
        tm.that(len(paths), eq=len(set(paths)))
        for selection in selections:
            owner = selection.root / "owner.py"
            tm.that(owner in paths)
            owner.write_text("invalid syntax !!!\n", encoding="utf-8")
            with u.Infra.codemod_binding_project(selection.root, snapshot) as (
                project,
                sources,
            ):
                consumer = selection.source_paths[0]
                module = project.get_pymodule(project.get_resource(consumer.name))
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
        source = mod_workspace / "consumer.py"
        owner = mod_workspace / "binding_owner.py"
        owner.write_text("class Public:\n    value = 'captured'\n", encoding="utf-8")
        marker = "descriptor evidence sentinel"
        source.write_text(
            f"# {marker}\nfrom __future__ import annotations\n"
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
        inputs = list(snapshot.states)
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
        tm.that(encoded.count(marker.encode("utf-8")), eq=1)
        tm.that(u.Cli.sha256_bytes(encoded), eq=receipt.sha256)
        tm.that(restored.deferred, eq=1)
        shared: dict[tuple[Path, ...], tuple[m.Cli.AtomicFileState, ...]] = {}
        for original, occurrence in zip(report.entries, restored.entries, strict=True):
            tm.that(occurrence.payload, eq=original.payload)
            tm.that(occurrence.source_state, eq=original.source_state)
            tm.that(occurrence.binding_states, eq=original.binding_states)
            tm.that(
                occurrence.binding_paths,
                eq=tuple(state.path for state in original.binding_states),
            )
            tm.that(occurrence.classification, eq=original.classification)
            tm.that(
                occurrence.binding_states
                is shared.setdefault(
                    occurrence.binding_paths, occurrence.binding_states
                )
            )
        tm.that(
            len(restored.inputs.states),
            eq=len({
                state.path for state in (*tm.not_none(report.source_states), *inputs)
            }),
        )
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
        closure = nested.evidence.entries[0].binding_states
        tm.that(closure[-1] is closure[0])
        owner.write_text("invalid syntax !!!\n", encoding="utf-8")
        with u.Infra.codemod_binding_project(
            mod_workspace, m.Infra.CodemodBindingSnapshot(states=closure)
        ) as (project, sources):
            module = project.get_pymodule(project.get_resource(source.name))
            tm.that(
                u.Infra.name_definition_resource_path(
                    module, sources[source].rindex("Public")
                ),
                eq=str(owner),
            )
        missing_source = mod_workspace / "absent_source.py"
        missing_binding = mod_workspace / "absent_binding.py"
        for reference, expected_key in (
            ({"source_path": missing_source}, missing_source),
            ({"binding_paths": (missing_binding,)}, missing_binding),
            (
                {
                    "source_path": missing_source,
                    "binding_paths": (missing_binding,),
                },
                missing_source,
            ),
        ):
            tampered = restored.model_copy(
                update={
                    "entries": (
                        restored.entries[0].model_copy(update=reference),
                        *restored.entries[1:],
                    )
                }
            )
            with pytest.raises(KeyError) as missing:
                m.Infra.ModScanEvidence.model_validate_json(
                    tampered.model_dump_json(round_trip=True)
                )
            tm.that(missing.value.args, eq=(expected_key,))
        with pytest.raises(m.ValidationError):
            m.Infra.CodemodBindingSnapshot(
                states=(
                    snapshot.states[0],
                    snapshot.states[0].model_copy(update={"content": b"changed"}),
                )
            )
