"""Real analyzer and Rope evidence for protocol-valued native model envelopes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
import sys
from inspect import getfile
from pathlib import Path

from flext_infra.gates import FlextInfraGatesPyrefly
from tests import c, m, p, tm, u


class TestsFlextInfraModelEnvelopeContracts:
    """Prove analyzer admission, native transformation and retained model identity."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        "case",
        [
            ("()", 0, None, "()", "p.Cli.AtomicFileState"),
            ("(value,)", 1, None, "()", "p.Cli.AtomicFileState"),
            ("(value, value)", 2, None, "()", "p.Cli.AtomicFileState"),
            ("(value, 'wrong')", None, None, "()", "p.Cli.AtomicFileState"),
            ("[value]", None, None, "()", "p.Cli.AtomicFileState"),
            (
                "(value,)",
                1,
                "Sequence[m.Cli.AtomicFileState]",
                "()",
                "p.Cli.AtomicFileState",
            ),
            (
                "[value]",
                1,
                "Sequence[m.Cli.AtomicFileState]",
                "()",
                "p.Cli.AtomicFileState",
            ),
            (
                "{'item': value}",
                1,
                "Mapping[str, m.Cli.AtomicFileState]",
                "{}",
                "p.Cli.AtomicFileState",
            ),
            (
                "{'outer': {'item': value}}",
                1,
                "Mapping[str, Mapping[str, m.Cli.AtomicFileState]]",
                "{}",
                "p.Cli.AtomicFileState",
            ),
            (
                "mapping",
                1,
                "Mapping[str, m.Cli.AtomicFileState]",
                "{}",
                "p.Cli.AtomicFileState",
            ),
            (
                "value",
                1,
                "m.Cli.AtomicFileState | None",
                "None",
                "p.Cli.AtomicFileState | m.Cli.AtomicFileState | None",
            ),
            (
                "(value,)",
                1,
                "tuple[m.Cli.AtomicFileState, ...]",
                "()",
                "p.Cli.AtomicFileState | m.Cli.AtomicFileState",
            ),
            (
                "mixed",
                None,
                "m.Cli.AtomicFileState | None",
                "None",
                "p.Cli.AtomicFileState",
            ),
            (
                "missing",
                None,
                "m.Cli.AtomicFileState | None",
                "None",
                "p.Cli.AtomicFileState",
            ),
            (
                "unexpected",
                None,
                "m.Cli.AtomicFileState | None",
                "None",
                "p.Cli.AtomicFileState",
            ),
        ],
    )
    def test_native_boundary_preserves_references_and_valid_constructors(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
        case: tuple[str, int | None, str | None, str, str],
    ) -> None:
        """Only the analyzer-proven envelope changes; valid construction survives."""
        workspace, path = rope_contract_consumer
        envelope = "m.Infra.StageSourceOptions" if case[2] is None else "Envelope"
        declaration = (
            ""
            if case[2] is None
            else (f"class Envelope(m.StrictModel):\n    inputs: {case[2]}\n")
        )
        extra = ""
        if case[0] == "mixed":
            declaration += "    count: int = 0\n"
            extra = "        count='wrong',\n"
        elif case[0] == "missing":
            declaration += "    count: int\n"
        elif case[0] == "unexpected":
            extra = "        unexpected='wrong',\n"
        mapping = (
            ""
            if case[0] != "mapping"
            else (
                "    mapping: t.MutableMappingKV[str, p.Cli.AtomicFileState] = "
                "{'item': value}\n"
            )
        )
        invocation = (
            "mapping"
            if case[0] == "mapping"
            else (
                "ActualEnvelopeSource.retain_original_atomic_file_state_references(value)"
            )
        )
        source = (
            "from collections.abc import Mapping, Sequence\n"
            "from pathlib import Path\n"
            "from typing import get_type_hints\n"
            "from flext_infra import m, p, t\n"
            f"{declaration}"
            "def quoted(value: 'PathAlias') -> 'PathAlias':\n"
            "    return value\n"
            "PathAlias = Path\n"
            "class ActualEnvelopeSource:\n"
            "    @staticmethod\n"
            "    def retain_original_atomic_file_state_references(\n"
            f"        value: {case[4]},\n"
            "    ):\n"
            "        return "
            + (
                "value"
                if case[0] in {"mapping", "mixed", "missing", "unexpected"}
                else case[0]
            )
            + "\n"
            f"def boundary(value: {case[4]}):\n"
            f"{mapping}"
            f"    return {envelope}(\n"
            "        inputs=(\n"
            f"            {invocation}\n"
            "        ),\n"
            f"{extra}"
            "    )\n"
            "def valid():\n"
            f"    return {envelope}(inputs={case[3]})\n"
            "def unrelated():\n"
            f"    return {envelope}(inputs='wrong')\n"
            "def leaves(value):\n"
            "    if isinstance(value, m.Cli.AtomicFileState):\n"
            "        return (value,)\n"
            "    if value is None:\n"
            "        return ()\n"
            "    values = value.values() if isinstance(value, Mapping) else value\n"
            "    return tuple(item for child in values for item in leaves(child))\n"
            "child = m.Cli.AtomicFileState(path=Path(__file__).with_name('absent'))\n"
            "materialized = boundary(child)\n"
            "try:\n"
            "    unrelated()\n"
            "except m.ValidationError:\n"
            "    rejected = True\n"
            "else:\n"
            "    rejected = False\n"
            "evidence = (len(leaves(materialized.inputs)),\n"
            "    all(item is child for item in leaves(materialized.inputs)),\n"
            f"    valid().inputs == {case[3]},\n"
            "    get_type_hints(quoted)['return'] is Path,\n"
            "    isinstance(quoted.__annotations__['value'], str), rejected)\n"
        )
        source = u.Infra.normalize_python_text(path, source).unwrap()
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        u.Cli.ensure_dir(workspace.repository_root / ".reports").unwrap()
        gate = FlextInfraGatesPyrefly(repository_root=workspace.repository_root)
        context = m.Infra.GateContext(
            repository_root=workspace.repository_root,
            runtime_root=Path(sys.prefix).parent,
            reports_dir=workspace.repository_root / ".reports",
        )
        checked = gate.check(workspace.repository_root, context)
        tm.that(
            sum(issue.code == "bad-argument-type" for issue in checked.issues),
            eq=1 + (case[1] != 0) + (case[0] == "mixed"),
        )
        rule = next(
            rule
            for rule in u.Infra.declared_contract_rules(workspace.repository_root)
            if rule.operation == c.Infra.RopeContractOperation.NORMALIZE_MODEL_ENVELOPES
        )
        with workspace.rope_project.source_view(
            declared_files=None, additional_source_folders=None
        ) as project:
            routes = u.Infra.protocol_model_routes_from_source(
                tm.not_none(u.Infra.project_root(Path(getfile(m.Cli.AtomicFileState)))),
                project,
            )
            changes = u.Infra.model_envelope_changes(
                project,
                rule,
                (
                    project.get_resource(
                        path.relative_to(workspace.repository_root).as_posix()
                    ),
                ),
                checked.issues,
                routes,
            )
        if case[0] == "unexpected":
            tm.that(len(changes) <= 1, truth=True)
        else:
            tm.that(
                len(changes),
                eq=int(case[1] not in {None, 0}),
                msg="\n".join(
                    f"{issue.code}@{issue.line}:{issue.column}: {issue.message}"
                    for issue in checked.issues
                ),
            )
        if case[1] is None:
            with u.Tests.raises(m.ValidationError):
                runpy.run_path(str(path))
            if changes:
                path.write_text(
                    u.Infra.normalize_source(
                        workspace.repository_root,
                        path,
                        changes[0].new_contents,
                        before_source=source,
                    ).unwrap(),
                    encoding=c.DEFAULT_ENCODING,
                )
                with u.Tests.raises(m.ValidationError):
                    runpy.run_path(str(path))
            return
        path.write_text(
            u.Infra.normalize_source(
                workspace.repository_root,
                path,
                changes[0].new_contents,
                before_source=source,
            ).unwrap()
            if changes
            else source,
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            runpy.run_path(str(path))["evidence"],
            eq=(case[1], True, True, True, True, True),
        )
        checked = gate.check(workspace.repository_root, context)
        tm.that(
            sum(issue.code == "bad-argument-type" for issue in checked.issues),
            eq=1,
        )
        workspace.refresh()
        with workspace.rope_project.source_view(
            declared_files=None, additional_source_folders=None
        ) as project:
            tm.that(
                u.Infra.model_envelope_changes(
                    project,
                    rule,
                    (
                        project.get_resource(
                            path.relative_to(workspace.repository_root).as_posix()
                        ),
                    ),
                    checked.issues,
                    routes,
                ),
                empty=True,
            )
