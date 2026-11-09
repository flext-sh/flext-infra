"""Portable migration intents retain native non-protocol binding identities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import codemod, config, workspace as workspace_api
from tests import c, m, tm, u


class TestsFlextInfraPortableBindingRewire:
    """Retired supplier modules do not prevent independent consumer rewiring."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("kind", "source_scope", "destination_scope", "source", "scaffold", "call"),
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
        kind: str,
        source_scope: str,
        destination_scope: str,
        source: str,
        scaffold: str,
        call: str,
    ) -> None:
        """Every selected binding is observed and executed before and after replay."""
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
        consumer.write_text(
            f"{imports}def consume() -> int:\n    return {call}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(producer))
        states = {state.path: state for state in seed.candidate.inputs}
        states[destination] = tm.ok(u.Cli.atomic_read_binary_file_state(destination))
        with u.Infra.open_project(producer, project_roots=(producer,)) as project:
            if kind == "module":
                plans = tm.ok(
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
            else:
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
                        resources=tuple(
                            u.Infra.file_resource_at(project, path)
                            for path in (origin, destination)
                        ),
                    )
                plans = tuple(
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
                        kind=kind,
                        source_module=origin_module,
                        source_scope=source_scope,
                        destination_module=destination_module,
                        destination_scope=destination_scope,
                    ),
                ),
                pre_move_sources={destination: scaffold},
                directory=config.Infra.refactor_csv_campaigns.rewire_directory,
            )
        )
        tm.that(len(artifacts), eq=1)
        tm.ok(u.Infra.publish_codegen_plans(producer, (*plans, *artifacts)))
        tm.fail(origin.exists())
        artifact, driver = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.load_rename_artifact(
                receiver,
                m.Infra.ModCommand(
                    repository_root=receiver, rename_plan=artifacts[0].path
                ),
            )
        )
        for repeated in (False, True):
            with (
                u.Infra.open_project(
                    tmp_path, project_roots=(receiver, producer), consumer_root=receiver
                ) as project,
                workspace_api.FlextInfraRopeWorkspace.open_workspace(
                    receiver, rope_repository_root=tmp_path, source_project=project
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
                    python_paths=(str(package.parent), str(receiving.parent)),
                ),
                eq=[],
            )
            tm.fail(origin.exists())
