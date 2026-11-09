"""Real analyzer and Rope evidence for protocol-valued native model envelopes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

from flext_infra.gates import FlextInfraGatesPyrefly
from tests import c, m, p, tm, u


class TestsFlextInfraModelEnvelopeContracts:
    """Prove analyzer admission, native transformation and retained model identity."""

    @staticmethod
    def test_native_boundary_preserves_references_and_valid_constructors(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Only the analyzer-proven envelope changes; valid construction survives."""
        workspace, path = rope_contract_consumer
        source = (
            "from pathlib import Path\n"
            "from flext_infra import m, p\n"
            "class ActualEnvelopeSource:\n"
            "    @staticmethod\n"
            "    def retain_original_atomic_file_state_references(\n"
            "        value: p.Cli.AtomicFileState,\n"
            "    ):\n"
            "        return (value,)\n"
            "def boundary(value: p.Cli.AtomicFileState):\n"
            "    return m.Infra.StageSourceOptions(\n"
            "        inputs=(\n"
            "            ActualEnvelopeSource."
            "retain_original_atomic_file_state_references(value)\n"
            "        ),\n"
            "    )\n"
            "def valid():\n"
            "    return m.Infra.StageSourceOptions(inputs=())\n"
            "def unrelated():\n"
            "    return m.Infra.StageSourceOptions(inputs=('wrong',))\n"
            "child = m.Cli.AtomicFileState(path=Path(__file__).with_name('absent'))\n"
            "evidence = (boundary(child).inputs[0] is child, valid().inputs == ())\n"
        )
        source = u.Infra.normalize_python_text(path, source).unwrap()
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        root = workspace.repository_root
        u.Cli.ensure_dir(root / ".reports").unwrap()
        gate = FlextInfraGatesPyrefly(repository_root=root)
        context = m.Infra.GateContext(
            repository_root=root,
            runtime_root=Path(sys.prefix).parent,
            reports_dir=root / ".reports",
        )
        checked = gate.check(root, context)
        tm.that(
            sum(issue.code == "bad-argument-type" for issue in checked.issues),
            eq=2,
        )
        rule = next(
            rule
            for rule in u.Infra.declared_contract_rules(root)
            if rule.operation == c.Infra.RopeContractOperation.NORMALIZE_MODEL_ENVELOPES
        )
        with workspace.rope_project.source_view(
            declared_files=None, additional_source_folders=None
        ) as project:
            resource = project.get_resource(path.relative_to(root).as_posix())
            provider_root = tm.not_none(u.Infra.project_root(Path(__file__)))
            routes = u.Infra.protocol_model_routes_from_source(provider_root, project)
            changes = u.Infra.model_envelope_changes(
                project,
                rule,
                (resource,),
                checked.issues,
                routes,
            )
        tm.that(len(changes), eq=1)
        updated = u.Infra.normalize_source(
            root, path, changes[0].new_contents, before_source=source
        ).unwrap()
        path.write_text(updated, encoding=c.DEFAULT_ENCODING)
        tm.that(runpy.run_path(str(path))["evidence"], eq=(True, True))
        rechecked = gate.check(root, context)
        tm.that(
            sum(issue.code == "bad-argument-type" for issue in rechecked.issues),
            eq=1,
        )
        workspace.refresh()
        with workspace.rope_project.source_view(
            declared_files=None, additional_source_folders=None
        ) as project:
            repeated = u.Infra.model_envelope_changes(
                project,
                rule,
                (project.get_resource(path.relative_to(root).as_posix()),),
                rechecked.issues,
                routes,
            )
        tm.that(repeated, empty=True)
