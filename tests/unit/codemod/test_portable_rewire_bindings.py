"""Portable migration intents retain native non-protocol binding identities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import codemod, config, workspace as workspace_api
from tests import c, m, p, tm, u

_BindingCase = tuple[
    Path,
    Path,
    Path,
    Path,
    Path,
    Path,
    Path,
]
_Binding = tuple[str, str, str, str, str, str]


class TestsFlextInfraPortableBindingRewire:
    """Retired supplier modules do not prevent independent consumer rewiring."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        "binding",
        [
            (
                "function",
                "execute",
                "execute",
                "def execute(value: int) -> int:\n    return value + 1\n",
                "",
                "Legacy(1) + Current(1)",
            ),
            (
                "variable",
                "VALUE",
                "VALUE",
                "VALUE = 2\n",
                "",
                "Legacy + Current",
            ),
            (
                "class",
                "Packet",
                "Packet",
                "class Packet:\n    def execute(self) -> int:\n        return 2\n",
                "",
                "Legacy().execute() + Current().execute()",
            ),
            (
                "method",
                "Origin.execute",
                "Destination.execute",
                (
                    "class Origin:\n    @staticmethod\n"
                    "    def execute(value: int) -> int:\n        return value + 1\n"
                ),
                "class Destination:\n    pass\n",
                "Legacy.execute(1) + Current.execute(1)",
            ),
            (
                "module",
                "",
                "",
                "def execute(value: int) -> int:\n    return value + 1\n",
                "",
                "Legacy.execute(1) + Current.execute(1)",
            ),
        ],
    )
    def test_native_binding_replay_after_supplier_retirement(
        tmp_path: Path,
        binding: _Binding,
    ) -> None:
        """Every selected binding is observed and executed before and after replay."""
        case = TestsFlextInfraPortableBindingRewire._prepare(tmp_path, binding)
        TestsFlextInfraPortableBindingRewire._project(case, binding)

    @staticmethod
    def _prepare(tmp_path: Path, binding: _Binding) -> _BindingCase:
        kind, source, scaffold = binding[0], binding[3], binding[4]
        producer, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiving = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="external-receiver", package_name="external_receiver"
        )
        for root in (producer, receiver):
            u.Tests.provision_checkout(root)
            u.Tests.provision_runtime_environment(root)
        origin = package / "legacy.py"
        destination = package / "current.py"
        origin.write_text(source, encoding=c.DEFAULT_ENCODING)
        if kind != "module":
            destination.write_text(scaffold, encoding=c.DEFAULT_ENCODING)
        consumer = receiving / "consumer.py"
        origin_module = f"{package.name}.legacy"
        destination_module = f"{package.name}.current"
        consumer.write_text(
            TestsFlextInfraPortableBindingRewire._consumer_source(
                binding, origin_module, destination_module
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        return (
            producer,
            package,
            receiver,
            receiving,
            consumer,
            origin,
            destination,
        )

    @staticmethod
    def _consumer_source(
        binding: _Binding,
        origin_module: str,
        destination_module: str,
    ) -> str:
        kind, source_scope, destination_scope, _source, _scaffold, call = binding
        if kind == "module":
            imports = (
                f"import {origin_module} as Legacy\n"
                f"import {destination_module} as Current\n"
            )
        else:
            imports = (
                f"from {origin_module} import {source_scope.partition('.')[0]} "
                "as Legacy\n"
                f"from {destination_module} import "
                f"{destination_scope.partition('.')[0]} as Current\n"
            )
        return f"{imports}def consume() -> int:\n    return {call}\n"

    @staticmethod
    def _project(case: _BindingCase, binding: _Binding) -> None:
        producer, package, receiver, _receiving, consumer, origin, destination = case
        origin_module = f"{package.name}.legacy"
        destination_module = f"{package.name}.current"
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(producer))
        states = {state.path: state for state in seed.candidate.inputs}
        states[destination] = tm.ok(u.Cli.atomic_read_binary_file_state(destination))
        plans = TestsFlextInfraPortableBindingRewire._native_plans(
            producer, origin, destination, states, binding
        )
        projected = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.compose_candidate(seed, plans)
        )
        artifacts = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.rewire_artifact_file_plans(
                producer,
                projected,
                (
                    m.Infra.SemanticRewireIntent(
                        supplier_root=producer.relative_to(
                            projected.candidate.workspace
                        ),
                        source_path=origin.relative_to(producer),
                        destination_path=destination.relative_to(producer),
                        kind=binding[0],
                        source_module=origin_module,
                        source_scope=binding[1],
                        destination_module=destination_module,
                        destination_scope=binding[2],
                    ),
                ),
                pre_move_sources={destination: binding[4]},
                directory=config.Infra.refactor_csv_campaigns.rewire_directory,
            )
        )
        tm.that(len(artifacts), eq=1)
        tm.ok(u.Infra.publish_codegen_plans(producer, (*plans, *artifacts)))
        tm.fail(origin.exists())
        TestsFlextInfraPortableBindingRewire._replay(
            receiver, producer, consumer, origin, artifacts[0].path
        )

    @staticmethod
    def _native_plans(
        producer: Path,
        origin: Path,
        destination: Path,
        states: dict[Path, p.Cli.AtomicFileState],
        binding: _Binding,
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        origin_module = f"{origin.parent.name}.legacy"
        destination_module = f"{origin.parent.name}.current"
        kind, source_scope = binding[0], binding[1]
        source = binding[3]
        with u.Infra.open_project(producer, project_roots=(producer,)) as project:
            if kind == "module":
                return tm.ok(
                    u.Infra.plan_module_move(
                        project,
                        origin,
                        destination_file=destination,
                        inputs=(
                            {
                                path: state.content.decode(c.DEFAULT_ENCODING)
                                for path, state in states.items()
                                if state.content is not None
                            },
                            tuple(states.values()),
                        ),
                    )
                )
            if kind == "method":
                changes = tm.not_none(
                    u.Infra.method_transfer_changes(
                        project,
                        m.Infra.RopeMethodTransfer(
                            id="native-method",
                            destination=(destination_module, "Destination"),
                            methods=((origin_module, source_scope),),
                        ),
                        (origin, destination),
                        u.Infra.source_member_resolver(project, sources={}),
                    )
                )
            else:
                changes = u.Infra.move_binding_changes(
                    project,
                    u.Infra.file_resource_at(project, origin),
                    source.index(source_scope),
                    u.Infra.file_resource_at(project, destination),
                    options=m.Infra.RopeMoveOptions(
                        resources=tuple(
                            u.Infra.file_resource_at(project, path)
                            for path in (origin, destination)
                        ),
                    ),
                )
        return tuple(
            m.Infra.CodegenFilePlan(
                project=producer,
                path=Path(change.resource.real_path),
                before=states[Path(change.resource.real_path)],
                desired_content=None
                if Path(change.resource.real_path) == origin
                else change.new_contents.encode(c.DEFAULT_ENCODING),
                desired_mode=None
                if Path(change.resource.real_path) == origin
                else config.Infra.codegen.modes.file_default,
            )
            for change in changes.changes
        )

    @staticmethod
    def _replay(
        receiver: Path,
        producer: Path,
        consumer: Path,
        origin: Path,
        artifact_path: Path,
    ) -> None:
        artifact, driver = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.load_rename_artifact(
                receiver,
                m.Infra.ModCommand(
                    repository_root=receiver, rename_plan=artifact_path
                ),
            )
        )
        for repeated in (False, True):
            with (
                u.Infra.open_project(
                    receiver.parent,
                    project_roots=(receiver, producer),
                    consumer_root=receiver,
                ) as project,
                workspace_api.FlextInfraRopeWorkspace.open_workspace(
                    receiver,
                    rope_repository_root=receiver.parent,
                    source_project=project,
                ) as workspace,
            ):
                replayed = tm.ok(
                    codemod.FlextInfraCodemodSemanticApply.plan_rename_artifact(
                        receiver, artifact, driver, workspace
                    )
                )
            if repeated:
                tm.that(replayed.candidate.updates, eq={})
            else:
                tm.ok(consumer in replayed.candidate.updates)
                tm.ok(
                    codemod.FlextInfraCodemodSemanticApply.publish_candidate(
                        receiver, replayed
                    )
                )
            tm.that(
                u.Tests.run_lazy_init_probe(
                    "from external_receiver.consumer import consume\n"
                    "assert consume() == 4\n",
                    python_paths=(str(origin.parent.parent), str(consumer.parent)),
                ),
                eq=[],
            )
            tm.fail(origin.exists())
