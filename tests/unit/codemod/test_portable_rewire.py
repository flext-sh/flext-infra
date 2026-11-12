"""Native supplier cutovers remain replayable by a separate consumer checkout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from flext_infra import codemod, config, workspace as workspace_api
from tests import c, m, p, tm, u

_Case = tuple[
    Path,
    Path,
    Path,
    Path,
    Path,
    Path,
    str,
    Path,
    Path,
]


class TestsFlextInfraPortableRewire:
    """A saved producer intent derives fresh consumer edits after the move."""

    @staticmethod
    @c.Tests.MARK.parametrize("existing_scaffold", [True, False])
    def test_external_consumer_after_supplier_module_retirement(
        tmp_path: Path, *, existing_scaffold: bool
    ) -> None:
        """Direct holder aliases move while public facade receivers stay public."""
        case = TestsFlextInfraPortableRewire._prepare(
            tmp_path, existing_scaffold=existing_scaffold
        )
        seed, plans = TestsFlextInfraPortableRewire._supplier_plans(case)
        artifacts = TestsFlextInfraPortableRewire._artifacts(case, seed, plans)
        TestsFlextInfraPortableRewire._publish_and_replay(case, plans, artifacts)

    @staticmethod
    def _prepare(tmp_path: Path, *, existing_scaffold: bool) -> _Case:
        producer, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiving_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="external-receiver", package_name="external_receiver"
        )
        for root in (producer, receiver):
            u.Tests.provision_checkout(root)
            u.Tests.provision_runtime_environment(root)
        origin = package / "_protocols" / "old.py"
        destination = package / "_protocols" / "_external" / "current.py"
        destination.parent.mkdir(parents=True)
        (destination.parent / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        source = (
            "from typing import Protocol, runtime_checkable\n"
            "class Holder:\n"
            "    @runtime_checkable\n"
            "    class Contract(Protocol):\n"
            "        def execute(self) -> str: ...\n"
        )
        scaffold = "class Destination:\n    pass\n"
        origin.write_text(source, encoding=c.DEFAULT_ENCODING)
        if existing_scaffold:
            destination.write_text(scaffold, encoding=c.DEFAULT_ENCODING)
        facade = package / "protocols.py"
        facade.write_text(
            f"from {package.name}._protocols.old import Holder\n"
            "class Protocols(Holder): pass\n"
            "p = Protocols\n__all__ = ['Protocols', 'p']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = receiving_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}._protocols.old import Holder as Legacy\n"
            f"from {package.name}._protocols._external.current import Destination as "
            f"Current\n"
            f"from {package.name}.protocols import p\n"
            "def consume(value: 'Legacy.Contract') -> 'p.Contract':\n"
            "    return value\n"
            "def already_current(value: 'Current.Contract') -> 'p.Contract':\n"
            "    return value\n",
            encoding=c.DEFAULT_ENCODING,
        )
        return (
            producer,
            package,
            receiver,
            receiving_package,
            origin,
            destination,
            scaffold,
            facade,
            consumer,
        )

    @staticmethod
    def _supplier_plans(
        case: _Case,
    ) -> tuple[p.Infra.SemanticSourcePlan, tuple[p.Infra.CodegenFilePlan, ...]]:
        producer, origin, destination = case[0], case[4], case[5]
        scaffold, facade = case[6], case[7]
        source = (
            "from typing import Protocol, runtime_checkable\n"
            "class Holder:\n"
            "    @runtime_checkable\n"
            "    class Contract(Protocol):\n"
            "        def execute(self) -> str: ...\n"
        )
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(producer))
        states = {state.path: state for state in seed.candidate.inputs}
        if destination not in states:
            states[destination] = tm.ok(
                u.Cli.atomic_read_binary_file_state(destination)
            )
        scaffold_plan = m.Infra.CodegenFilePlan(
            project=producer,
            path=destination,
            before=states[destination],
            desired_content=scaffold.encode(c.DEFAULT_ENCODING),
            desired_mode=states[destination].mode
            or config.Infra.codegen.modes.file_default,
        )
        with (
            u.Infra.open_project(producer, project_roots=(producer,)) as live,
            closing(
                u.Infra.planned_project(
                    live,
                    election=u.Infra.native_election(live),
                    declared_files=(scaffold_plan,),
                )
            ) as project,
        ):
            changes = u.Infra.move_class_changes(
                project,
                u.Infra.file_resource_at(project, origin),
                source.index("Contract"),
                u.Infra.file_resource_at(project, destination),
                options=m.Infra.RopeMoveOptions(
                    destination_offset=scaffold.index("Destination"),
                    resources=(
                        u.Infra.file_resource_at(project, origin),
                        u.Infra.file_resource_at(project, destination),
                    ),
                ),
            )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=producer,
                path=Path(change.resource.real_path),
                before=before,
                desired_content=(
                    None
                    if Path(change.resource.real_path) == origin
                    else change.new_contents.encode(c.DEFAULT_ENCODING)
                ),
                desired_mode=(
                    None
                    if Path(change.resource.real_path) == origin
                    else before.mode or config.Infra.codegen.modes.file_default
                ),
            )
            for change in changes.changes
            for before in (states[Path(change.resource.real_path)],)
        )
        facade_before = tm.ok(u.Cli.atomic_read_binary_file_state(facade))
        plans += (
            m.Infra.CodegenFilePlan(
                project=producer,
                path=facade,
                before=facade_before,
                desired_content=(
                    "from "
                    f"{origin.parent.parent.name}._protocols._external.current "
                    "import Destination\n"
                    "class Protocols(Destination): pass\n"
                    "p = Protocols\n__all__ = ['Protocols', 'p']\n"
                ).encode(c.DEFAULT_ENCODING),
                desired_mode=facade_before.mode,
            ),
        )
        return seed, plans

    @staticmethod
    def _artifacts(
        case: _Case,
        seed: p.Infra.SemanticSourcePlan,
        plans: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        producer, package = case[0], case[1]
        origin, destination = case[4], case[5]
        projected = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.compose_candidate(seed, plans)
        )
        census = m.Infra.ProtocolPlacementCensus(
            contracts=(
                m.Infra.ProtocolContractPlacement(
                    source_module=f"{package.name}._protocols.old",
                    source_class="Holder.Contract",
                    source_path=origin.relative_to(producer),
                    line=4,
                    category=c.Infra.ProtocolOrigin.EXTERNAL,
                    destination_module=f"{package.name}._protocols._external.current",
                    destination_class="Destination.Contract",
                    destination_path=destination.relative_to(producer),
                    public_routes=("p.Contract",),
                    evidence=("Native supplier nested protocol transfer",),
                ),
            )
        )
        return tuple(
            tm.ok(
                codemod.FlextInfraCodemodSemanticApply.rewire_artifact_file_plans(
                    producer,
                    projected,
                    tm.ok(
                        codemod.FlextInfraCodemodSemanticApply.protocol_rewire_intents(
                            producer, projected, census
                        )
                    ),
                    pre_move_sources={destination: "class Destination:\n    pass\n"},
                    directory=config.Infra.refactor_csv_campaigns.rewire_directory,
                )
            )
        )

    @staticmethod
    def _publish_and_replay(
        case: _Case,
        plans: tuple[p.Infra.CodegenFilePlan, ...],
        artifacts: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> None:
        producer, package, receiver, receiving_package, origin, _destination = case[:6]
        _scaffold, _facade, consumer = case[6:9]
        tm.that(len(artifacts), eq=1)
        tm.ok(u.Infra.publish_codegen_plans(producer, (*plans, *artifacts)))
        artifact, driver = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.load_rename_artifact(
                receiver,
                m.Infra.ModCommand(
                    repository_root=receiver, rename_plan=artifacts[0].path
                ),
            )
        )
        tm.fail(origin.exists())
        with (
            u.Infra.open_project(
                package.parent,
                project_roots=(receiver, producer),
                consumer_root=receiver,
            ) as project,
            workspace_api.FlextInfraRopeWorkspace.open_workspace(
                receiver, rope_repository_root=package.parent, source_project=project
            ) as workspace,
        ):
            replayed = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.plan_rename_artifact(
                    receiver, artifact, driver, workspace
                )
            )
        tm.ok(consumer in replayed.candidate.updates)
        tm.ok(all(path.is_relative_to(receiver) for path in replayed.candidate.updates))
        tm.ok(
            codemod.FlextInfraCodemodSemanticApply.publish_candidate(receiver, replayed)
        )
        tm.ok("p.Contract" in consumer.read_text())
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.protocols import p\n"
                "from external_receiver.consumer import consume, already_current\n"
                "class Service:\n"
                "    def execute(self) -> str: return 'ready'\n"
                "value = Service()\n"
                "assert isinstance(value, p.Contract)\nassert consume(value) is value\n"
                "assert already_current(value) is value\n",
                python_paths=(str(package.parent), str(receiving_package.parent)),
            ),
            eq=[],
        )
        before_repeat = consumer.read_bytes()
        with (
            u.Infra.open_project(
                package.parent,
                project_roots=(receiver, producer),
                consumer_root=receiver,
            ) as project,
            workspace_api.FlextInfraRopeWorkspace.open_workspace(
                receiver, rope_repository_root=package.parent, source_project=project
            ) as workspace,
        ):
            repeated = tm.ok(
                codemod.FlextInfraCodemodSemanticApply.plan_rename_artifact(
                    receiver, artifact, driver, workspace
                )
            )
        tm.that(repeated.candidate.updates, eq={})
        tm.that(consumer.read_bytes(), eq=before_repeat)
        tm.fail(origin.exists())
