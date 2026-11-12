"""A complete native inheritance cohort survives portable supplier cutover.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import codemod, config, infra, workspace as workspace_api
from tests import c, m, p, tm, u

_Case = tuple[
    Path,
    Path,
    Path,
    Path,
    Path,
    Mapping[Path, str],
    Sequence[str],
    p.Infra.SemanticSourcePlan,
]


class TestsFlextInfraPortableRewireCohorts:
    """Exercise multiple supplier files, reexports and actual diamond C3 together."""

    @staticmethod
    def _supplier_sources(
        package: Path, depth: int, *, reverse: bool, homonymous: bool
    ) -> dict[Path, str]:
        """Declare a real protocol diamond with independently imported branches.

        Returns:
            The resulting ``dict[Path, str]``.

        """
        namespace = ".".join(f"Layer{index}" for index in range(depth))
        prefix = namespace + "." if namespace else ""
        imports = {
            "Root": "",
            "Left": f"from {package.name}.legacy.base import RootOwner as Base\n",
            "Right": f"from {package.name}.legacy.base import RootOwner as Base\n",
            "Diamond": (
                f"from {package.name}.legacy.branches import LeftOwner as L\n"
                f"from {package.name}.legacy.branches import RightOwner as R\n"
            ),
        }
        names = {role: "Contract" if homonymous else role for role in imports}
        branches = ("R", "L") if reverse else ("L", "R")
        leaves = {"L": "Left", "R": "Right"}
        bases = {
            "Root": "Protocol",
            "Left": f"Base.{prefix}{names['Root']}, Protocol",
            "Right": f"Base.{prefix}{names['Root']}, Protocol",
            "Diamond": ", ".join(
                f"{branch}.{prefix}{names[leaves[branch]]}" for branch in branches
            )
            + ", Protocol",
        }
        methods = {
            "Root": "execute",
            "Left": "left",
            "Right": "right",
            "Diamond": "compose",
        }
        sources: dict[Path, str] = {}
        for leaf, parents in bases.items():
            lines = [
                "from __future__ import annotations\n",
                "from typing import Protocol, runtime_checkable\n",
                imports[leaf],
                f"class {leaf}Owner:\n",
            ]
            lines.extend(
                f"{'    ' * (level + 1)}class Layer{level}:\n" for level in range(depth)
            )
            indent = "    " * (depth + 1)
            lines.extend((
                f"{indent}@runtime_checkable\n",
                f"{indent}class {names[leaf]}({parents}):\n",
                f"{indent}    def {methods[leaf]}(self) -> str: ...\n",
                f"__all__ = ['{leaf}Owner']\n",
            ))
            sources[package / "_protocols" / f"old_{leaf.lower()}.py"] = "".join(lines)
        sources.update({
            package / "_protocols" / "__init__.py": '"""Structural contracts."""\n',
            package / "legacy" / "__init__.py": '"""Original import surface."""\n',
            package / "legacy" / "base" / "__init__.py": (
                f"from {package.name}._protocols.old_root import RootOwner\n"
                "__all__ = ['RootOwner']\n"
            ),
            package / "legacy" / "branches" / "__init__.py": (
                f"from {package.name}._protocols.old_left import LeftOwner\n"
                f"from {package.name}._protocols.old_right import RightOwner\n"
                "__all__ = ['LeftOwner', 'RightOwner']\n"
            ),
            package / "legacy" / "final" / "__init__.py": (
                f"from {package.name}._protocols.old_diamond import DiamondOwner\n"
                "__all__ = ['DiamondOwner']\n"
            ),
            package / "models.py": (
                "from flext_core import m as core_m\n"
                "class Models(core_m): pass\nm = Models\n__all__ = ['Models', 'm']\n"
            ),
            package / "protocols.py": (
                "from flext_core import p as core_p\n"
                + "".join(
                    f"from {package.name}._protocols.old_{leaf.lower()} import "
                    f"{leaf}Owner\n"
                    for leaf in bases
                )
                + (
                    "class Protocols(core_p):\n"
                    + "".join(
                        f"    class {leaf}({leaf}Owner.{namespace}): pass\n"
                        if namespace
                        else f"    class {leaf}({leaf}Owner): pass\n"
                        for leaf in bases
                    )
                    if homonymous
                    else "class Protocols("
                    + ", ".join((
                        *(
                            f"{leaf}Owner.{namespace}" if namespace else f"{leaf}Owner"
                            for leaf in bases
                        ),
                        "core_p",
                    ))
                    + "): pass\n"
                )
                + "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ),
            package / "services.py": (
                "from __future__ import annotations\n"
                "from flext_core import t\n"
                f"from {package.name}.protocols import p\n"
                "class CapabilityConsumer:\n"
                + "".join(
                    "    @staticmethod\n"
                    f"    def use_{leaf.lower()}(value: "
                    f"t.Port[p.{leaf}{'.Contract' if homonymous else ''}]) -> str:\n"
                    f"        return value.{method}()\n"
                    for leaf, method in methods.items()
                )
            ),
        })
        return sources

    @staticmethod
    @c.Tests.MARK.parametrize("depth", [0, 2])
    @c.Tests.MARK.parametrize("reverse", [False, True])
    @c.Tests.MARK.parametrize("homonymous", [False, True])
    def test_reexported_diamond_cohort_replays_after_supplier_retirement(
        tmp_path: Path, depth: int, *, reverse: bool, homonymous: bool
    ) -> None:
        """One saved source epoch retains the complete C3 contract at every move."""
        case = TestsFlextInfraPortableRewireCohorts._prepare(
            tmp_path, depth, reverse=reverse, homonymous=homonymous
        )
        organization = TestsFlextInfraPortableRewireCohorts._organization(case)
        plans, artifacts = TestsFlextInfraPortableRewireCohorts._project(
            case, organization, homonymous=homonymous
        )
        TestsFlextInfraPortableRewireCohorts._publish(case, plans, artifacts)
        TestsFlextInfraPortableRewireCohorts._final(case, homonymous=homonymous)

    @staticmethod
    def _prepare(
        tmp_path: Path,
        depth: int,
        *,
        reverse: bool,
        homonymous: bool,
    ) -> _Case:
        producer, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiving_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="diamond-receiver", package_name="diamond_receiver"
        )
        for root in (producer, receiver):
            u.Tests.provision_checkout(root)
            u.Tests.provision_runtime_environment(root)
        sources = TestsFlextInfraPortableRewireCohorts._supplier_sources(
            package, depth, reverse=reverse, homonymous=homonymous
        )
        for path, source in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        namespace = ".".join(f"Layer{index}" for index in range(depth))
        scope = namespace + "." if namespace else ""
        consumer = receiving_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.legacy.final import DiamondOwner as Legacy\n"
            f"from {package.name}.protocols import p as contracts\n"
            f"def consume(value: "
            f"'Legacy.{scope}{'Contract' if homonymous else 'Diamond'}') -> "
            f"'contracts.Diamond{'.Contract' if homonymous else ''}':\n"
            "    return value\n",
            encoding=c.DEFAULT_ENCODING,
        )
        baseline = u.Tests.run_lazy_init_probe(
            f"from {package.name}.protocols import p\n"
            f"diamond = p.Diamond{'.Contract' if homonymous else ''}\n"
            "print(tuple(next(name for name in ('execute', 'left', 'right', 'compose') "
            "if name in value.__dict__) for value in diamond.__mro__ "
            "if any(name in value.__dict__ for name in ('execute', 'left', 'right', "
            "'compose'))))\n",
            python_paths=(str(package.parent),),
        )
        seed = tm.ok(codemod.FlextInfraCodemodSemanticApply.build_source_plan(producer))
        return (
            producer,
            package,
            receiver,
            receiving_package,
            consumer,
            sources,
            baseline,
            seed,
        )

    @staticmethod
    def _organization(case: _Case) -> p.Infra.ProtocolOrganizationPlan:
        producer, sources = case[0], case[5]
        with infra.rope_workspace(producer) as workspace:
            inventory = tuple(
                item
                for path in sources
                for item in workspace.objects(
                    path, include_local_scopes=True, include_references=True
                )
            )
            census = u.Infra.protocol_contract_census(
                workspace, sources=sources, objects=inventory
            )
            tm.that(census.findings, eq=())
            return u.Infra.plan_protocol_contract_organization(
                workspace, sources=sources, census=census
            )

    @staticmethod
    def _retired_paths(package: Path, sources: Mapping[Path, str]) -> tuple[Path, ...]:
        retired = tuple(
            path
            for path in sources
            if path.parent.name == "_protocols" and path.name.startswith("old_")
        )
        return retired + tuple(
            path for path in sources if path.is_relative_to(package / "legacy")
        )

    @staticmethod
    def _cleanup_plans(
        producer: Path,
        retired: tuple[Path, ...],
        originals: Mapping[Path, p.Cli.AtomicFileState],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        return tuple(
            m.Infra.CodegenFilePlan(
                project=producer,
                path=path,
                before=originals[path],
                desired_content=None,
                desired_mode=None,
            )
            for path in retired
        )

    @staticmethod
    def _facade_plan(
        producer: Path,
        package: Path,
        organization: p.Infra.ProtocolOrganizationPlan,
        *,
        homonymous: bool,
        originals: Mapping[Path, p.Cli.AtomicFileState],
    ) -> m.Infra.CodegenFilePlan:
        facade = package / "protocols.py"
        destinations = {
            row.source_path.stem.removeprefix("old_").capitalize(): row
            for row in organization.census.contracts
        }
        imports = "from flext_core import p as core_p\n" + "".join(
            f"from {row.destination_module} import "
            f"{row.destination_class.split('.')[0]}\n"
            for row in destinations.values()
        )
        scopes = {
            role: row.destination_class.rpartition(".")[0]
            for role, row in destinations.items()
        }
        declaration = (
            "class Protocols(core_p):\n"
            + "".join(
                f"    class {role}({scope}): pass\n" for role, scope in scopes.items()
            )
            if homonymous
            else "class Protocols("
            + ", ".join((*scopes.values(), "core_p"))
            + "): pass\n"
        )
        return m.Infra.CodegenFilePlan(
            project=producer,
            path=facade,
            before=originals[facade],
            desired_content=(
                imports + declaration + "p = Protocols\n__all__ = ['Protocols', 'p']\n"
            ).encode(c.DEFAULT_ENCODING),
            desired_mode=originals[facade].mode,
        )

    @staticmethod
    def _project(
        case: _Case,
        organization: p.Infra.ProtocolOrganizationPlan,
        *,
        homonymous: bool,
    ) -> tuple[
        tuple[p.Infra.CodegenFilePlan, ...],
        tuple[p.Infra.CodegenFilePlan, ...],
    ]:
        producer, package = case[0], case[1]
        sources, seed = case[5], case[7]
        originals = {state.path: state for state in seed.candidate.inputs}
        retired = TestsFlextInfraPortableRewireCohorts._retired_paths(package, sources)
        cleanup = TestsFlextInfraPortableRewireCohorts._cleanup_plans(
            producer, retired, originals
        )
        facade_plan = TestsFlextInfraPortableRewireCohorts._facade_plan(
            producer, package, organization, homonymous=homonymous, originals=originals
        )
        plans = u.Infra.codegen_compose_file_plans(
            (*organization.files, *cleanup, facade_plan), ordered=True
        )
        projected = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.compose_candidate(seed, plans)
        )
        artifacts = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.rewire_artifact_file_plans(
                    producer,
                    projected,
                    tm.ok(
                        codemod.FlextInfraCodemodSemanticApply.protocol_rewire_intents(
                            producer, projected, organization.census
                        )
                    ),
                    pre_move_sources=organization.pre_move_sources,
                directory=config.Infra.refactor_csv_campaigns.rewire_directory,
            )
        )
        tm.that(len(artifacts), eq=1)
        return plans, artifacts

    @staticmethod
    def _publish(
        case: _Case,
        plans: tuple[p.Infra.CodegenFilePlan, ...],
        artifacts: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> None:
        producer, package, receiver = case[0], case[1], case[2]
        consumer, sources = case[4], case[5]
        tm.ok(u.Infra.publish_codegen_plans(producer, (*plans, *artifacts)))
        for path in TestsFlextInfraPortableRewireCohorts._retired_paths(
            package, sources
        ):
            tm.fail(path.exists())
        artifact, driver = tm.ok(
            codemod.FlextInfraCodemodSemanticApply.load_rename_artifact(
                receiver,
                m.Infra.ModCommand(
                    repository_root=receiver, rename_plan=artifacts[0].path
                ),
            )
        )
        for repeat in (False, True):
            with (
                u.Infra.open_project(
                    tmp_path := package.parent,
                    project_roots=(receiver, producer),
                    consumer_root=receiver,
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
            tm.ok(
                all(
                    path.is_relative_to(receiver) for path in replayed.candidate.updates
                )
            )
            if repeat:
                tm.that(replayed.candidate.updates, eq={})
            else:
                tm.ok(consumer in replayed.candidate.updates)
                tm.ok(
                    codemod.FlextInfraCodemodSemanticApply.publish_candidate(
                        receiver, replayed
                    )
                )
        tm.ok("contracts.Diamond" in consumer.read_text())
        for path in TestsFlextInfraPortableRewireCohorts._retired_paths(
            package, sources
        ):
            tm.fail(path.exists())

    @staticmethod
    def _final(case: _Case, *, homonymous: bool) -> None:
        package, receiving_package, baseline = case[1], case[3], case[6]
        after = u.Tests.run_lazy_init_probe(
            f"from {package.name}.protocols import p\n"
            "from diamond_receiver.consumer import consume, already_current\n"
            "class Service:\n"
            "    def execute(self) -> str: return 'root'\n"
            "    def left(self) -> str: return 'left'\n"
            "    def right(self) -> str: return 'right'\n"
            "    def compose(self) -> str: return 'diamond'\n"
            "value = Service()\nassert consume(value) is value\n"
            "assert already_current(value) is value\n"
            f"assert isinstance(value, p.Diamond{'.Contract' if homonymous else ''})\n"
            f"diamond = p.Diamond{'.Contract' if homonymous else ''}\n"
            "print(tuple(next(name for name in ('execute', 'left', 'right', 'compose') "
            "if name in value.__dict__) for value in diamond.__mro__ "
            "if any(name in value.__dict__ for name in ('execute', 'left', 'right', "
            "'compose'))))\n",
            python_paths=(str(package.parent), str(receiving_package.parent)),
        )
        tm.that(after, eq=baseline)
