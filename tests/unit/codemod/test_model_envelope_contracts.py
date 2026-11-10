"""Real analyzer and Rope evidence for protocol-valued native model envelopes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import runpy
import sys
from inspect import getfile
from pathlib import Path

from flext_infra import FlextInfraCli
from flext_infra.gates import FlextInfraGatesPyrefly
from tests import c, m, p, t, tm, u


class TestsFlextInfraModelEnvelopeContracts:
    """Prove analyzer admission, native transformation and retained model identity."""

    @staticmethod
    def test_source_declaration_records_match_loaded_public_owners(
        rope_contract_consumer: tuple[p.Infra.RopeWorkspaceDsl, Path],
    ) -> None:
        """Facade and inherited-base records name their actual native declarations."""
        workspace, _path = rope_contract_consumer
        with workspace.rope_project.source_view(
            declared_files=None, additional_source_folders=None
        ) as project:
            for model_type, protocol_type in (
                (m.Cli.AtomicFileState, p.Cli.AtomicFileState),
                (m.ProjectMetadata.__mro__[1], p.ProjectMetadata.__mro__[1]),
            ):
                repository_root = tm.not_none(
                    u.Infra.project_root(Path(getfile(model_type)))
                )
                records = tuple(
                    record
                    for package in u.Infra.protocol_model_package_names(
                        repository_root, project
                    )
                    for record in u.Infra.protocol_model_declarations_from_source(
                        repository_root,
                        project,
                        package_name=package,
                    )
                    if record[0] == f"{model_type.__module__}.{model_type.__qualname__}"
                )
                tm.that(len(records), eq=1)
                tm.that(
                    records[0][1],
                    eq=f"{protocol_type.__module__}.{protocol_type.__qualname__}",
                )
                tm.that(
                    records[0][2].resolve(), eq=Path(getfile(protocol_type)).resolve()
                )

    @staticmethod
    @c.Tests.MARK.slow
    def test_public_nested_namespace_envelopes_retain_native_references(
        tmp_path: Path,
        capsys: t.Tests.CaptureFixture[str],
        native_consumer: p.Tests.NativeConsumer,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Namespace and local constructors converge without admitting a namesake."""
        root, primary = u.Tests.create_lazy_init_workspace(tmp_path)
        declaration = u.Tests.project_spec(root.name).model_copy(
            update={"repository_namespace_packages": ("infra",)}
        )
        u.Cli.yaml_dump(
            root / "config" / "codegen.yaml",
            {
                "Infra": {
                    "codegen": {
                        "repository": {
                            "project": declaration.model_dump(mode="json"),
                        }
                    }
                }
            },
        ).unwrap()
        package = root / "infra" / "pulumi" / "lib"
        sources = {
            package / "__init__.py": (
                "from .models import m\nfrom .protocols import p\n"
                "__all__ = ['m', 'p']\n"
            ),
            package / "models.py": (
                "from ._models.payload import PayloadModels\n"
                "class InfraPulumiLibModels(PayloadModels): pass\n"
                "m = InfraPulumiLibModels\n"
                "__all__ = ['InfraPulumiLibModels', 'm']\n"
            ),
            package / "protocols.py": (
                "class InfraPulumiLibProtocols: pass\n"
                "p = InfraPulumiLibProtocols\n"
                "__all__ = ['InfraPulumiLibProtocols', 'p']\n"
            ),
            package / "_models" / "__init__.py": "",
            package / "_models" / "payload.py": (
                "from __future__ import annotations\n"
                "from collections.abc import Mapping\n"
                "from flext_core import m\n"
                "class PayloadModels:\n"
                "    class Payload(m.StrictModel):\n        value: str\n"
                "    class Envelope(m.StrictModel):\n"
                "        inputs: Mapping[str, tuple[PayloadModels.Payload, ...]]\n"
                "__all__ = ['PayloadModels']\n"
            ),
        }
        for path, source in sources.items():
            u.Cli.ensure_dir(path.parent).unwrap()
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with u.Infra.facade_source_project(root) as binding:
            projected = u.Infra.protocol_model_sources_from_source(
                root, binding[0], package_name="infra.pulumi.lib"
            ).unwrap()
        for relative, source in projected.items():
            u.Cli.ensure_dir((root / relative).parent).unwrap()
            (root / relative).write_text(source, encoding=c.DEFAULT_ENCODING)
        (package / "protocols.py").write_text(
            "from ._protocols.payload import InfraPulumiLibProtocolsPayload\n"
            "class InfraPulumiLibProtocols(InfraPulumiLibProtocolsPayload): pass\n"
            "p = InfraPulumiLibProtocols\n"
            "__all__ = ['InfraPulumiLibProtocols', 'p']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = primary / "consumer.py"
        original = (
            "from collections.abc import Mapping\n"
            "from flext_core import m as core_m\n"
            "from infra.pulumi.lib import m, p\n"
            "class Envelope(core_m.StrictModel):\n"
            "    inputs: Mapping[str, tuple[m.Payload, ...]]\n"
            "class Payload(core_m.StrictModel):\n    value: str\n"
            "def local(value: p.Payload):\n"
            "    inputs: Mapping[str, tuple[p.Payload, ...]] = {'nested': (value,)}\n"
            "    return Envelope(inputs=inputs)\n"
            "def namespace(value: p.Payload):\n"
            "    inputs: Mapping[str, tuple[p.Payload, ...]] = {'nested': (value,)}\n"
            "    return m.Envelope(inputs=inputs)\n"
            "def unrelated(value: Payload):\n"
            "    inputs: Mapping[str, tuple[Payload, ...]] = {'nested': (value,)}\n"
            "    return Envelope(inputs=inputs)\n"
            "def invalid(value: p.Payload):\n"
            "    inputs: Mapping[str, tuple[p.Payload, str]] = "
            "{'nested': (value, 'wrong')}\n"
            "    return Envelope(inputs=inputs)\n"
        )
        consumer.write_text(original, encoding=c.DEFAULT_ENCODING)
        u.Tests.create_python_environment(
            root,
            dependency_projects=u.Tests.python_dependency_projects(root),
            session_runtime=session_runtime,
        ).unwrap()
        u.Tests.provision_checkout(root)
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.declare_rules(
            root,
            {
                "fixture-unused": (
                    "id: fixture-unused\nlanguage: Python\nseverity: warning\n"
                    "rule:\n  pattern: fixture_old($A)\nfix: fixture_new($A)\n"
                )
            },
        )
        u.Cli.ensure_dir(root / ".reports").unwrap()
        checked = FlextInfraGatesPyrefly(repository_root=root).check(
            root,
            m.Infra.GateContext(
                repository_root=root, runtime_root=root, reports_dir=root / ".reports"
            ),
        )
        tm.that(
            sum(issue.code == "bad-argument-type" for issue in checked.issues),
            gte=2,
            msg=checked.raw_output,
        )
        route = [
            "refactor",
            "mod",
            "--repository-root",
            str(root),
            "--rule",
            "pydantic-native-protocol-model-envelope",
        ]
        preview = FlextInfraCli.infra_main([*route, "--dry-run"])
        capture = capsys.readouterr()
        tm.that(preview, ne=0, msg=capture.out + capture.err)
        tm.that(capture.out + capture.err, has="pending semantic file")
        tm.that(capture.out + capture.err, has="admitted_calls=2")
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        applied = FlextInfraCli.infra_main(route)
        capture = capsys.readouterr()
        tm.that(applied, eq=0, msg=capture.out + capture.err)
        migrated = consumer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            migrated.count(".model_validate("),
            eq=2,
            msg=capture.out + capture.err,
        )
        tm.that(migrated, has="Envelope(inputs=inputs)")
        native_consumer(
            f"sys.path[:0] = [{str(primary.parent)!r}, {str(root)!r}]\n"
            f"from {primary.name}.consumer import (\n"
            "    local, namespace, unrelated, invalid, Payload)\n"
            "from infra.pulumi.lib import m\n"
            "from pydantic import ValidationError\n"
            "child = m.Payload(value='retained')\n"
            "assert local(child).inputs['nested'][0] is child\n"
            "assert namespace(child).inputs['nested'][0] is child\n"
            "for operation, value in ((unrelated, Payload(value='different owner')),\n"
            "                         (invalid, child)):\n"
            "    try:\n        operation(value)\n"
            "    except ValidationError:\n        pass\n"
            "    else:\n        raise AssertionError('invalid source was admitted')\n",
            cwd=root,
        )
        fixed = FlextInfraCli.infra_main([*route, "--dry-run"])
        capture = capsys.readouterr()
        tm.that(fixed, eq=0, msg=capture.out + capture.err)
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=migrated)

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
                "tuple(sorted((value, value), key=str))",
                2,
                "tuple[m.Cli.AtomicFileState, ...]",
                "()",
                "p.Cli.AtomicFileState | m.Cli.AtomicFileState",
            ),
            (
                "tuple(sorted((value, 'wrong'), key=str))",
                None,
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
            else (f"class EnvelopeFields(m.StrictModel):\n    inputs: {case[2]}\n")
        )
        extra = ""
        if case[0] == "mixed":
            declaration += "    count: int = 0\n"
            extra = "        count='wrong',\n"
        elif case[0] == "missing":
            declaration += "    count: int\n"
        elif case[0] == "unexpected":
            extra = "        unexpected='wrong',\n"
        if case[2] is not None:
            declaration += "class Envelope(EnvelopeFields):\n    pass\n"
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
            declarations = u.Infra.protocol_model_declarations_from_source(
                tm.not_none(u.Infra.project_root(Path(getfile(m.Cli.AtomicFileState)))),
                project,
            )
            routes = {model: protocol for model, protocol, _destination in declarations}
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
