"""Runtime behavior of the generated structural protocol assembly.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator
from importlib.metadata import distribution
from importlib.util import find_spec
from pathlib import Path

import pytest

from flext_infra import infra, settings
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, t, tm, u

MEMBER = "demo_member"
ALIAS_CASES: t.VariadicTuple[t.Quad[str, str, str, str]] = (
    ("tags", "t.VariadicTuple[str]", "()", "tuple[str, ...]"),
    ("permuted", "Permuted[int, str]", '("tag", 1)', "tuple[str, int]"),
    ("repeated", "Repeated[int]", "(1, 2)", "tuple[int, int]"),
    ("unused", "Unused[str, int]", "()", "tuple[str, ...]"),
    ("identity", "Identity[str]", '"identity"', "str"),
    ("nested", "Nested[int]", "([1], 1)", "tuple[list[int], int]"),
    ("factory", "type[str]", "str", "type[str]"),
)

MODELS = (
    '''\
"""Demo member models."""


from flext_core import m, t


type Permuted[First, Second] = tuple[Second, First]
type Repeated[Value] = tuple[Value, Value]
type Unused[Value, Ignored] = tuple[Value, ...]
type Identity[Value] = Value
type Nested[Value] = Permuted[Value, list[Value]]


class Order(m.FrozenModel):
    """A validated order."""

    sku: str = m.Field(description="Stock keeping unit of the ordered item.")
    quantity: int = m.Field(default=1, description="Number of units ordered.")
'''
    + "".join(
        f"    {name}: {annotation} = m.Field(default={default}, description={name!r})\n"
        for name, annotation, default, _expected in ALIAS_CASES
    )
    + '''


type Envelope[Value] = tuple[Order, Value]


class Shipment(m.FrozenModel):
    """A validated shipment referencing its order."""

    order: Order | None = m.Field(default=None, description="Shipped order.")
    envelope: Envelope[str] | None = m.Field(
        default=None, description="Typed envelope.")


class _InventoryBase(m.BaseModel):
    """Inherited model fields retain their native attribute bindings."""

    environment: str = m.Field(default="test", description="Inventory environment.")


class Inventory(_InventoryBase):
    """A mutable inventory count."""

    quantity: int = m.Field(default=1, description="Available units.")
    sku: str = m.Field(default="item", frozen=True, description="Fixed item.")


type ShipmentPayload = Shipment
type Payload = Order | ShipmentPayload


class DemoMemberModels(m):
    """Member models container."""

    class DemoMember:
        """The member's public model namespace."""

        Order = Order
        Shipment = Shipment
        Inventory = Inventory
        Payload = Payload


m = DemoMemberModels
__all__ = ["DemoMemberModels", "m"]
'''
)


PROTOCOLS = '''\
"""Demo member protocols container."""

from demo_member._protocols.manual_ports import ManualPort
from flext_core import p

__all__ = ["DemoMemberProtocols", "p"]


class DemoMemberProtocols(p):
    """Member protocols container."""

    class DemoMember:
        """The member's public protocol namespace."""

        ManualPort = ManualPort


p = DemoMemberProtocols
'''

MANUAL_PORTS = '''\
"""Hand-declared ports; the generator never regenerates these."""

from __future__ import annotations

from typing import Protocol


class ManualPort(Protocol):
    """A hand-owned structural port."""

    class Record(Protocol):
        """A same-owner nested structural entity."""

        @property
        def value(self) -> str: ...

    def bind(self) -> bool:
        """Bind the port."""
        ...

    def selected(self) -> ManualPort.Record: ...
'''

CONSUMER = '''\
"""Consumer referencing the member protocols facade."""

from demo_member import p

NAMESPACE = p.DemoMember


def ship(order: p.DemoMember.Order) -> p.DemoMember.Payload:
    """Consume the structural contracts."""
    raise NotImplementedError
'''

TYPINGS = '''\
"""Demo member typings container."""


from flext_core import t


class DemoMemberTypes(t):
    """Member typings container."""

    VariadicTuple = t.VariadicTuple


t = DemoMemberTypes
__all__ = ["DemoMemberTypes", "t"]
'''


def _verify_supplier_sources() -> t.Pair[t.DirectoryPath, str]:
    """Capture the supplier's source and locked dependency identities.

    Returns:
        The supplier root and the original source receipt declarations.

    """
    source_context = tm.ok(infra.project_context(Path.cwd()))
    supplier_root = tm.not_none(source_context.runtime).runtime_root
    supplier_modules = ("flext_core", "flext_cli", "flext_infra")
    supplier_states = tuple(
        tm.ok(
            u.Cli.atomic_read_binary_file_state(
                Path(tm.not_none(tm.not_none(find_spec(module)).origin)), required=True
            )
        )
        for module in supplier_modules
    )
    for source in supplier_states:
        tm.that(source.path.is_relative_to(supplier_root), eq=True)
    supplier_identities = tuple(
        tm.ok(
            u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=source.path.parent))
        )
        for source in supplier_states
    )
    rope_distribution = distribution("rope")
    rope_receipt = m.Infra.DirectUrlReceipt.model_validate_json(
        tm.not_none(rope_distribution.read_text("direct_url.json"))
    )
    tm.not_none(rope_receipt.vcs_info)
    for module, state, identity in zip(
        supplier_modules, supplier_states, supplier_identities, strict=True
    ):
        u.Cli.info(
            f"fixture source module={module} path={state.path}; "
            f"head={identity.head_oid}; dirty={identity.dirty}"
        )
    u.Cli.info(
        f"fixture source rope={rope_distribution.metadata['Name']}; "
        f"commit={tm.not_none(rope_receipt.vcs_info).commit_id}"
    )
    return supplier_root, (
        f"modules = {supplier_modules!r}\n"
        f"states = {tuple(state.model_dump_json() for state in supplier_states)!r}\n"
        "identities = "
        f"{tuple((str(i.repo_root), i.head_oid) for i in supplier_identities)!r}\n"
        f"rope_name = {rope_distribution.metadata['Name']!r}\n"
        "expected_rope = m.Infra.DirectUrlReceipt.model_validate_json("
        f"{rope_receipt.model_dump_json()!r})\n"
    )


def _provision_member(parent: t.DirectoryPath) -> t.DirectoryPath:
    """Provision the member with its canonical frozen runtime.

    Returns:
        The provisioned member root.

    """
    github_token = t.SecretStr(settings.env_required("GITHUB_TOKEN"))
    supplier_root, supplier_receipt = _verify_supplier_sources()
    root = parent / "demo-member"
    u.Tests.WorktreeFixture.write_python_project(root, root.name)
    package = root / c.Infra.DEFAULT_SRC_DIR / MEMBER
    u.Tests.write_project_beads_config(root, root.name)
    repository = u.Tests.repository_ref(root.name, role=c.Infra.MakeProfile.STANDALONE)
    u.Tests.initialize_git_repo(root, origin_url=repository.url)
    (package / "_protocols").mkdir()
    for filename, content in (
        ("models.py", MODELS),
        ("protocols.py", PROTOCOLS),
        ("typings.py", TYPINGS),
        ("consumer.py", CONSUMER),
        ("_protocols/manual_ports.py", MANUAL_PORTS),
    ):
        (package / filename).write_text(content, encoding=c.DEFAULT_ENCODING)
    u.Tests.copy_tracked_mise_seeds(root)
    local_path = root / c.CONFIG_DIR_NAME / "codegen.local.yaml"
    supplier_declaration: t.JsonDict = {
        "Infra": {
            "codegen": {
                "make": {
                    "uv_resolution": {
                        "editable_supplier_root": supplier_root.as_posix(),
                    }
                }
            }
        },
    }
    if local_path.exists():
        local = tm.ok(u.Cli.yaml_roundtrip_load_map(local_path))
        u.Cli.yaml_overlay_preserving_order(local, supplier_declaration)
        tm.ok(
            u.Cli.atomic_write_text_file(
                local_path, tm.ok(u.Cli.yaml_roundtrip_dump_text(local))
            )
        )
    else:
        tm.ok(u.Cli.yaml_dump(local_path, supplier_declaration))
    tm.that(
        tm.ok(
            u.Infra.load_codegen_inputs(root)
        ).spec.make.uv_resolution.editable_supplier_root,
        eq=supplier_root,
    )
    u.Tests.run_lazy_init(root)
    proposed = {package / "epoch_probe.py": "EPOCH = 'proposed'\n"}
    with u.Infra.facade_source_project(root, planned_sources=proposed) as binding:
        with pytest.raises(
            ValueError, match="native lazy alias membership differs"
        ) as mismatch:
            u.Infra.runtime_evaluated_base_classes(
                root, {}, (), source_project=binding[0]
            )
        u.Cli.info(str(mismatch.value))
        u.Infra.runtime_evaluated_base_classes(
            root, proposed, (), source_project=binding[0]
        )
    _conform_member(
        root,
        u.Tests.workspace_spec(repository, project=u.Tests.project_spec(root.name)),
    )
    _install_member_runtime(root, supplier_root, github_token)
    _verify_member_runtime(root, supplier_receipt)
    return root


def _conform_member(root: t.DirectoryPath, workspace: m.Infra.WorkspaceSpec) -> None:
    """Materialize the member's native Make and resolution surfaces."""
    manifest = m.Infra.WorkspaceManifestSpec(
        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
        name=workspace.name,
        namespace_scan_dirs=workspace.namespace_scan_dirs,
        repository=workspace.repository,
        project=workspace.project,
        members=workspace.subprojects,
        external_dependency_paths=workspace.external_dependency_paths,
        integration=workspace.integration,
    )
    tm.ok(
        u.Cli.yaml_dump(
            root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME,
            manifest.model_dump(mode="json", exclude_none=True),
        )
    )
    request = u.Tests.conform_request(root, what=c.Infra.CodegenConformSurface.MAKEFILE)
    conform = FlextInfraCodegenConform(
        repository_root=root,
        state=m.Infra.CodegenConformState(
            repository_root=root, request=request, initial_workspace=workspace
        ),
    )
    planned = conform.plan(request)
    plan = tm.ok(planned)
    if plan.exception is not None:
        raise plan.exception
    tm.that(plan.issues, empty=True, msg=str(plan.issues))
    tm.ok(u.Tests.materialize_codegen_plans(planned.map(lambda result: result.files)))
    tm.ok(
        u.Tests.materialize_codegen_plans(
            conform.native_resolution_plans(
                root,
                workspace,
                tm.ok(u.Infra.load_codegen_inputs(root)),
                plan.files,
                rendered_by=conform.rendered_by_stamp(),
            ).map(tuple)
        )
    )
    tm.ok(
        infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=root, apply=True)
        )
    )


def _install_member_runtime(
    root: t.DirectoryPath, supplier_root: t.DirectoryPath, github_token: t.SecretStr
) -> None:
    """Install and verify the member's independently elected runtime."""
    resolution = tm.ok(FlextInfraWorkspaceDetector.resolution_context(root))
    policy = tm.ok(u.Infra.load_codegen_inputs(root)).spec.make.uv_resolution
    tm.that(
        resolution.pyproject_path,
        eq=root / policy.editable_directory / c.PYPROJECT_FILENAME,
    )
    tm.that(resolution.environment_path, eq=root / c.Infra.ENVIRONMENT_DIRECTORY)
    u.Cli.info(
        f"fixture election supplier={supplier_root}; view={resolution.pyproject_path}; "
        f"lock={resolution.lock_path}; environment={resolution.environment_path}"
    )
    private_env = {"GITHUB_TOKEN": github_token}
    for verb in ("upg", "setup"):
        provisioned = tm.ok(
            u.Tests.run_isolated_make([verb], cwd=root, private_env=private_env)
        )
        tm.that(
            u.Cli.process_succeeded(provisioned.outcome),
            eq=True,
            msg=provisioned.stdout + provisioned.stderr,
        )
    environment = u.Infra.runtime_environment_dir(root)
    tm.that(environment.is_symlink(), eq=False)
    tm.that((environment / "pyvenv.cfg").is_file(), eq=True)


def _verify_member_runtime(root: t.DirectoryPath, supplier_receipt: str) -> None:
    """Compare the installed runtime against the supplier source identities."""
    package = root / c.Infra.DEFAULT_SRC_DIR / MEMBER
    environment = u.Infra.runtime_environment_dir(root)
    u.Tests.run_lazy_init_probe(
        "import sys\n"
        "from pathlib import Path\n"
        "from importlib.util import find_spec\n"
        "from importlib.metadata import distribution\n"
        "from flext_infra import m, u\n"
        "from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance\n"
        "from flext_infra.workspace import FlextInfraWorkspaceDetector\n"
        "from flext_tests import tm\n"
        f"root = Path({str(root)!r})\n"
        f"assert Path(sys.prefix).resolve() == Path({str(environment)!r}).resolve()\n"
        f"package = find_spec({MEMBER!r})\n"
        "assert package is not None and package.origin is not None\n"
        "assert Path(package.origin).resolve() == "
        f"Path({str(package / c.Infra.INIT_PY)!r}).resolve()\n"
        "repository = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root)).repository\n"
        "installed = distribution(repository.distribution)\n"
        "receipt = m.Infra.DirectUrlReceipt.model_validate_json("
        "tm.not_none(installed.read_text('direct_url.json')))\n"
        "assert tm.ok(FlextInfraWorkspaceEnvironmentProvenance."
        "validate_editable_installation(repository, root, installed, receipt))\n"
        + supplier_receipt
        + "for module, encoded, identity in "
        "zip(modules, states, identities, strict=True):\n"
        "    expected = m.Cli.AtomicFileState.model_validate_json(encoded)\n"
        "    elected = find_spec(module)\n"
        "    assert elected is not None and elected.origin is not None\n"
        "    assert tm.ok(u.Cli.atomic_read_binary_file_state("
        "expected.path, required=True)) == expected\n"
        "    current = tm.ok(u.Infra.git_identity("
        "m.Infra.GitRepoRequest(repo_root=expected.path.parent)))\n"
        "    assert (str(current.repo_root), current.head_oid) == identity\n"
        "    print(f'fixture supplier module="
        "{module} source={elected.origin}; '"
        "f'head={current.head_oid}; dirty={current.dirty}')\n"
        "rope = distribution('rope')\n"
        "assert rope.metadata['Name'] == rope_name\n"
        "observed_rope = m.Infra.DirectUrlReceipt.model_validate_json("
        "tm.not_none(rope.read_text('direct_url.json')))\n"
        "assert observed_rope.url == expected_rope.url "
        "and observed_rope.vcs_info == expected_rope.vcs_info\n"
        "rope_module = find_spec('rope')\n"
        "assert rope_module is not None and rope_module.origin is not None\n"
        "assert Path(rope_module.origin).resolve().is_relative_to("
        f"Path({str(environment)!r}).resolve())\n"
        "print(f'fixture runtime prefix={sys.prefix}; "
        'rope={rope.metadata["Name"]}; vcs={observed_rope.vcs_info}\')\n',
        runtime_root=root,
        cwd=root,
    )


@pytest.fixture
def member_root(session_runtime: p.Tests.SessionRuntime) -> Iterator[t.DirectoryPath]:
    """Lease this project's own installed runtime at its stable source path.

    Yields:
        The isolated project with its original source and physical environment.

    """
    with session_runtime.lease(_provision_member) as root:
        yield root


def _probe(
    root: t.DirectoryPath,
    script: str = "tm.ok(service.execute())\n",
    *,
    consumer: str = (
        "from demo_member import m, p\n"
        'assert isinstance(m.DemoMember.Order(sku="a"), p.DemoMember.Order)\n'
        "assert callable(p.DemoMember.ManualPort.bind)\n"
    ),
) -> None:
    """Generate, then exercise the public facade in a separate real interpreter."""
    u.Tests.run_lazy_init_probe(
        "from pathlib import Path\n"
        "from flext_tests import tm\n"
        "from flext_infra import FlextInfra\n"
        "from flext_infra.codegen import FlextInfraCodegenProtocolModels\n"
        f"root = Path({str(root)!r})\n"
        "service = FlextInfraCodegenProtocolModels(\n"
        "    repository_root=root, apply_changes=True,\n"
        "    conform=FlextInfra(repository_root=root).codegen_conform)\n" + script,
        runtime_root=root,
        cwd=root,
    )
    if consumer:
        u.Tests.run_lazy_init_probe(
            "from typing import get_type_hints\n" + consumer,
            runtime_root=root,
            cwd=root,
        )


def test_apply_generates_runtime_checkable_contracts(
    member_root: t.DirectoryPath,
) -> None:
    """A generated protocol and its reported native effects are publicly valid."""
    _probe(
        member_root,
        "from flext_infra import FlextInfra, c, m\n"
        "result = tm.ok(service.execute())\n"
        "receipt = result.publication_receipt\n"
        "assert receipt is not None and receipt.completed\n"
        "report = root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH\n"
        "assert report in receipt.written_files\n"
        "assert report not in result.written_files\n"
        "assert set(result.written_files) <= set(receipt.written_files)\n"
        "assert root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH "
        "in receipt.written_files\n"
        "assert any(report in batch.written_files and report in batch.effect_targets "
        "for batch in receipt.batches)\n"
        "public = m.Infra.CodegenPhaseOutcome.model_validate_json("
        "report.read_bytes())\n"
        "assert public.transaction_id == receipt.transaction_id and public.completed\n"
        "tm.ok(FlextInfra(repository_root=root).codegen_conform(m.Infra.CodegenConformRequest(\n"
        "    root=root, mode=c.Infra.CodegenConformMode.CHECK)))\n"
        "again = tm.ok(service.execute())\n"
        "assert not again.written_files\n"
        "assert again.publication_receipt is not None "
        "and again.publication_receipt.completed\n"
        "assert again.publication_receipt.written_files\n",
    )


def test_refactor_cli_registers_and_projects_contracts(
    member_root: t.DirectoryPath,
) -> None:
    """CLI input remains data while API wiring supplies required conformance."""
    _probe(
        member_root,
        "from flext_infra import main\n"
        "assert main(['refactor', 'mod', '--help']) == 0\n"
        "assert main(['refactor', 'protocol-models', '--help']) == 0\n"
        "arguments = ['refactor', 'protocol-models', '--repository-root', str(root)]\n"
        "assert main([*arguments, '--apply']) == 0\n"
        "assert main([*arguments, '--check']) == 0\n"
        "assert main([*arguments, '--apply', '--dry-run']) == 0\n",
    )


@pytest.mark.parametrize("change", [None, "content", "membership"])
def test_projected_outputs_keep_original_transaction_inputs(
    member_root: t.DirectoryPath, change: str | None
) -> None:
    """Virtual outputs publish, but original file and membership changes fail."""
    _probe(
        member_root,
        "from flext_infra import c, config, m, u\n"
        "from flext_infra.codegen import FlextInfraCodegenMiseArtifacts, "
        "FlextInfraCodegenTransaction\n"
        'source = root / "original-input.txt"\n'
        'source.write_bytes(b"original input\\n")\n'
        'target = root / "unchanged-output.txt"\n'
        "requested_change = None\n"
        "phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT\n"
        "owner = FlextInfraCodegenTransaction("
        "FlextInfraCodegenMiseArtifacts(repository_root=root))\n"
        "roots = owner.capability_roots(phase.value, (root,))\n"
        "def publish(scope_root):\n"
        "    original = tm.ok(u.Cli.atomic_read_binary_file_state("
        "source, required=True))\n"
        "    before = tm.ok(u.Cli.atomic_read_binary_file_state("
        "target, required=False))\n"
        "    plan = m.Infra.CodegenFilePlan(\n"
        "        project=root, path=target, before=before, "
        'desired_content=b"published output\\n",\n'
        "        desired_mode=config.Infra.codegen.modes.file_default)\n"
        "    with u.Infra.facade_source_project("
        "root, source_states=(original,), declared_files=(plan,)) as binding:\n"
        "        assert binding[0].source_bytes(source) == original.content\n"
        "        assert target in binding[0].source_children(root)\n"
        "        states, directories, topology = binding[1]()\n"
        "        physical = next(item for item in directories "
        "if item.root.path == root and item.membership_queried)\n"
        "        assert target.name not in {item.name for item in physical.entries}\n"
        "    change = requested_change\n"
        '    if change == "content":\n'
        '        source.write_bytes(b"changed input\\n")\n'
        '    elif change == "membership":\n'
        '        (root / "unplanned-input.txt").write_bytes(b"unplanned\\n")\n'
        "    plan = plan.model_copy(update={\n"
        '        "source_states": states, "source_directories": directories, '
        '"source_query_topology": topology})\n'
        "    analysis = m.Infra.CodegenPhaseAnalysis(\n"
        "        phase=phase, files=(plan,), inputs=states, "
        "source_directories=directories, source_query_topology=topology)\n"
        "    return owner.publish_file_phase_locked(scope_root, roots, analysis, "
        "m.Infra.CodegenPhasePublicationPolicy(directories=()))\n"
        "tm.ok(owner.run_files_locked(roots, publish))\n"
        'assert target.read_bytes() == b"published output\\n"\n'
        'target = root / "planned-output.txt"\n'
        f"requested_change = {change!r}\n"
        + (
            "from pytest import raises\n"
            'with raises(ValueError, match="source directory membership '
            'changed:.*unplanned-input.txt"):\n'
            "    owner.run_files_locked(roots, publish)\n"
            "assert not target.exists()\n"
            if change == "membership"
            else "outcome = owner.run_files_locked(roots, publish)\n"
            + (
                "assert outcome.failure\nassert not target.exists()\n"
                if change == "content"
                else "tm.ok(outcome)\nassert target.read_bytes() "
                '== b"published output\\n"\n'
            )
        ),
        consumer="",
    )


def test_transitive_model_dependency_is_a_structural_contract(
    member_root: t.DirectoryPath,
) -> None:
    """An indirectly referenced field resolves through the generated public port."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        "from demo_member import p\n"
        "def ship(value: p.DemoMember.Shipment) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        'assert get_type_hints(p.DemoMember.Shipment.order.fget)["return"] '
        "== p.DemoMember.Order | None\n"
        'assert isinstance(m.DemoMember.Order(sku="nested"), p.DemoMember.Order)\n',
    )


@pytest.mark.parametrize("owned_parent", [True, False])
def test_missing_parent_epoch_requires_a_journal_owned_transition(
    member_root: t.DirectoryPath, owned_parent: bool
) -> None:
    """Cross-phase input absence survives only the journal's actual parent gain."""
    _probe(
        member_root,
        "from flext_infra import c, config, m, r, u\n"
        "from flext_infra.codegen import FlextInfraCodegenMiseArtifacts, "
        "FlextInfraCodegenTransaction, FlextInfraMiseArtifactsJournal, "
        "FlextInfraMiseArtifactsVerification, FlextInfraStagedPackage\n"
        'source = root / "input-parent" / "input.txt"\n'
        'target = root / "owned-parent-output.txt"\n'
        "phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT\n"
        "owner = FlextInfraCodegenTransaction("
        "FlextInfraCodegenMiseArtifacts(repository_root=root))\n"
        "roots = owner.capability_roots(phase.value, (root,))\n"
        "def publish(scope_root):\n"
        "    original = tm.ok(u.Cli.atomic_read_binary_file_state("
        "source, required=False))\n"
        "    assert original.parent_device is None and original.content is None\n"
        "    before = tm.ok(u.Cli.atomic_read_binary_file_state("
        "target, required=False))\n"
        "    session = tm.ok(owner.begin_files_locked("
        "scope_root, roots, (original,)))\n"
        f"    owned = {owned_parent!r}\n"
        "    if owned:\n"
        "        session = tm.ok(owner.append_directories_locked("
        "session, c.Infra.CodegenStagedFilePhase.LAYOUT, (source.parent,)))\n"
        "    else:\n"
        "        source.parent.mkdir()\n"
        "    bound = FlextInfraMiseArtifactsVerification.session_input_states("
        "(original,), session)\n"
        "    if owned:\n"
        "        accepted = tm.ok(bound)\n"
        "        assert accepted[0].content is None and accepted[0].device is None\n"
        "        assert accepted[0].parent_inode == source.parent.stat().st_ino\n"
        "        candidate = tm.ok(FlextInfraStagedPackage.plan_sources("
        "root, {}, options=m.Infra.StageSourceOptions(inputs=accepted)))\n"
        "        assert next(item for item in candidate.inputs "
        "if item.path == source) == accepted[0]\n"
        "        assert original.parent_inode is None and original.content is None\n"
        "    else:\n"
        "        assert bound.failure\n"
        "    plan = m.Infra.CodegenFilePlan(\n"
        "        project=root, path=target, before=before, "
        'desired_content=b"owned transition\\n",\n'
        "        desired_mode=config.Infra.codegen.modes.file_default, "
        "source_states=(original,))\n"
        "    appended = owner.append_phase_locked(session, phase, (plan,))\n"
        "    if not owned:\n"
        "        assert appended.failure\n"
        '        assert "parent" in appended.error '
        "and str(source.parent) in appended.error\n"
        "        assert source.parent.is_dir() and not target.exists()\n"
        "        return r[tuple[Path, ...]].from_failure(appended)\n"
        "    ready = tm.ok(appended)\n"
        "    journal, _state = tm.ok(FlextInfraMiseArtifactsJournal.read("
        "ready.plan.layout))\n"
        "    assert any(item.created is not None "
        "and item.created.path == source.parent for item in journal.directories)\n"
        "    records = [item for item in journal.sources if item.path == source]\n"
        "    assert any(item.phase == phase for item in records)\n"
        "    assert all(item.parent_device is None and item.absent_parent is not None "
        "and source.parent in item.absent_parent.directories for item in records)\n"
        "    return owner.commit_locked(ready)\n"
        "result = owner.run_files_locked(roots, publish)\n"
        + (
            'tm.ok(result)\nassert target.read_bytes() == b"owned transition\\n"\n'
            if owned_parent
            else "assert result.failure\nassert not target.exists()\n"
            "assert source.parent.is_dir()\n"
        ),
        consumer="",
    )


@pytest.mark.parametrize("change", [None, "content", "identity"])
def test_candidate_inputs_advance_only_through_native_publication(
    member_root: t.DirectoryPath, change: str | None
) -> None:
    """A candidate reads owned new bytes but rejects subsequent foreign changes."""
    _probe(
        member_root,
        "from flext_infra import c, config, m, r, u\n"
        "from flext_infra.codegen import FlextInfraCodegenMiseArtifacts, "
        "FlextInfraCodegenTransaction\n"
        'source = root / "publication-input.txt"\n'
        "original = tm.ok(u.Cli.atomic_read_binary_file_state("
        "source, required=False))\n"
        "phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT\n"
        "owner = FlextInfraCodegenTransaction("
        "FlextInfraCodegenMiseArtifacts(repository_root=root))\n"
        "roots = owner.capability_roots(phase.value, (root,))\n"
        "def publish(scope_root):\n"
        "    session = tm.ok(owner.begin_files_locked("
        "scope_root, roots, (original,)))\n"
        "    plan = m.Infra.CodegenFilePlan("
        "project=root, path=source, before=original,\n"
        '        desired_content=b"owned bytes\\n", '
        "desired_mode=config.Infra.codegen.modes.file_default, "
        "source_states=(original,))\n"
        "    ready = tm.ok(owner.append_phase_locked(session, phase, (plan,)))\n"
        "    receipt = tm.ok(owner.publication_outcome(ready, completed=True))\n"
        "    return owner.commit_locked(ready).map(lambda _: receipt)\n"
        "receipt = tm.ok(owner.run_files_locked(roots, publish))\n"
        "assert original.content is None and original.device is None\n"
        f"change = {change!r}\n"
        'if change == "content":\n'
        '    source.write_bytes(b"foreign bytes\\n")\n'
        'elif change == "identity":\n'
        '    foreign = root / "foreign-input.txt"\n'
        '    foreign.write_bytes(b"owned bytes\\n")\n'
        "    foreign.chmod(source.stat().st_mode)\n"
        "    foreign.replace(source)\n"
        "reader = FlextInfraCodegenTransaction("
        "FlextInfraCodegenMiseArtifacts(repository_root=root), "
        "prior_publications=(receipt,))\n"
        "view = reader.preview_sources(root, {}, "
        "lambda candidate, _: (candidate / source.name).read_bytes(),\n"
        "    options=m.Infra.CodegenSourcePreviewOptions("
        "inputs=(original,), runtime_check=False))\n"
        "if change is None:\n"
        '    assert tm.ok(view) == b"owned bytes\\n"\n'
        "else:\n"
        "    assert view.failure\n"
        "assert original.content is None and original.device is None\n",
        consumer="",
    )


def test_mutable_fields_and_frozen_fields_retain_public_contract(
    member_root: t.DirectoryPath,
) -> None:
    """Writable attributes and frozen accessors match the model's native fields."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        "from demo_member import p\n"
        "def count(value: p.DemoMember.Inventory) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "contract = p.DemoMember.Inventory\n"
        'assert get_type_hints(contract)["quantity"] is int\n'
        'assert get_type_hints(contract.sku.fget)["return"] is str\n'
        "value = m.DemoMember.Inventory()\n"
        "value.quantity = 5\n"
        "assert value.quantity == 5 and isinstance(value, contract)\n"
        'assert value.model_dump()["quantity"] == 5\n',
    )


@pytest.mark.parametrize(
    ("namespace", "base"),
    [("Commerce", "m.BaseModel"), ("Shipping", "m.FrozenModel")],
)
def test_model_namespaces_preserve_nested_contracts(
    member_root: t.DirectoryPath, namespace: str, base: str
) -> None:
    """Model ancestry does not hide inherited nested models or their aliases."""
    package = member_root / "src" / MEMBER
    original_namespace = '''    class DemoMember:
        """The member's public model namespace."""

        Order = Order
        Shipment = Shipment
        Inventory = Inventory
        Payload = Payload
'''
    source = (
        MODELS
        .replace(
            "class DemoMemberModels(m):",
            "class Root(m.FrozenModel):\n"
            '    """A strongly typed nested payload."""\n'
            "    root: tuple[str, ...] = m.Field(default=(), "
            'description="Payload.")\n\n\n'
            "class NamespaceParts:\n"
            '    """Inherited model declarations."""\n'
            "    Root: ClassVar[type[Root]] = Root\n"
            "    AliasRoot: ClassVar[type[Root]] = Root\n\n\n"
            "class DemoMemberModels(m):",
        )
        .replace(
            "from flext_core import m, t",
            "from typing import ClassVar\n\nfrom flext_core import m, t",
        )
        .replace(
            original_namespace,
            f"    class {namespace}(NamespaceParts, {base}):\n"
            '        """A model that also exposes nested model declarations."""\n',
        )
    )
    (package / "models.py").write_text(source, encoding=c.DEFAULT_ENCODING)
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("class DemoMember:", f"class {namespace}:"),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        f"def payload(value: p.{namespace}.Root) -> p.{namespace}.AliasRoot: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        f"models, ports = m.{namespace}, p.{namespace}\n"
        "assert models.Root is models.AliasRoot\n"
        "value = models.Root(root=('source', 'identity'))\n"
        "for contract in (ports.Root, ports.AliasRoot):\n"
        "    assert isinstance(value, contract)\n"
        "    assert get_type_hints(contract.root.fget)['return'] == tuple[str, ...]\n"
        "    assert contract.__module__.startswith("
        "'demo_member._protocols.generated')\n"
        "assert callable(ports.ManualPort.bind)\n"
        "assert (get_type_hints(ports.ManualPort.selected)['return']\n"
        "        is ports.ManualPort.Record)\n",
    )
    (package / "models.py").write_text(
        source.replace(
            "\nm = DemoMemberModels",
            f"\n    Mirror = {namespace}\n\nm = DemoMemberModels",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        f"def payload(value: p.{namespace}.Root) -> p.Mirror.Root: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        "from flext_infra import u\n"
        "from flext_infra.workspace import FlextInfraRopeWorkspace, "
        "FlextInfraWorkspaceDetector\n"
        "project = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec("
        "root)).project\n"
        "with u.Infra.facade_source_project(root) as binding:\n"
        "    with FlextInfraRopeWorkspace.open_workspace(root,\n"
        "            rope_repository_root=Path(binding[0].root.real_path),\n"
        "            source_project=binding[0]) as workspace:\n"
        "        modules, identities = tm.ok(service.render_modules("
        "project, workspace))\n"
        f"assert identities[{namespace + '.Root'!r}] == identities['Mirror.Root']\n"
        "assert modules\n",
        consumer="",
    )


@pytest.mark.parametrize(
    ("field_name", "expected"),
    [(name, expected) for name, _annotation, _default, expected in ALIAS_CASES],
)
def test_generated_annotations_resolve_specialized_aliases(
    member_root: t.DirectoryPath,
    field_name: str,
    expected: str,
) -> None:
    """Public runtime hints retain specialized parameters without free aliases."""
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "protocol = p.DemoMember.Order\n"
        f"accessor = getattr(protocol, {field_name!r})\n"
        f'assert get_type_hints(accessor.fget)["return"] == {expected}\n'
        'assert isinstance(m.DemoMember.Order(sku="alias consumer"), protocol)\n',
    )


def test_apply_is_idempotent(member_root: t.DirectoryPath) -> None:
    """Repeated apply retains every generated byte and check-only succeeds."""
    _probe(
        member_root,
        "tm.ok(service.execute())\n"
        f'generated = root / "src" / {MEMBER!r} / "_protocols"\n'
        "before = "
        '{path: path.read_bytes() for path in generated.glob("generated*.py")}\n'
        "tm.ok(service.execute())\n"
        "assert {path: path.read_bytes() "
        'for path in generated.glob("generated*.py")} == before\n'
        "tm.ok(FlextInfraCodegenProtocolModels(\n"
        "    repository_root=root, apply_changes=False, "
        "conform=service.conform).execute())\n",
    )


def test_check_only_reports_drift(member_root: t.DirectoryPath) -> None:
    """A fresh process detects drift after the canonical model changes."""
    _probe(member_root, "tm.ok(service.execute())\n")
    models_path = member_root / "src" / MEMBER / "models.py"
    models_path.write_text(
        MODELS.replace(
            '    sku: str = m.Field(description="Stock keeping unit of the ordered '
            'item.")',
            '    sku: str = m.Field(description="Stock keeping unit of the ordered '
            'item.")'
            '\n    weight: float = m.Field(default=1.0, description="Drift probe '
            'weight.")',
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        "result = FlextInfraCodegenProtocolModels(\n"
        "    repository_root=root, apply_changes=False, "
        "conform=service.conform).execute()\n"
        'assert result.failure and "drifted" in result.error\n',
        consumer="",
    )


def test_unresolved_reference_fails_typed(member_root: t.DirectoryPath) -> None:
    """A protocol without a corresponding model fails with its exact name."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        CONSUMER + "\n\ndef ghost(port: p.DemoMember.Ghost) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        "result = service.execute()\n"
        'assert result.failure and "Ghost" in result.error\n',
        consumer="",
    )


@pytest.mark.parametrize(
    ("namespace", "empty_model"), [("Tools", False), ("Ports", True)]
)
def test_plain_namespace_prefix_preserves_native_operational_members(
    member_root: t.DirectoryPath, namespace: str, *, empty_model: bool
) -> None:
    """Namespace proof needs native types, not an admitted Pydantic descendant."""
    package = member_root / "src" / MEMBER
    domain = package / "_models/domain.py"
    domain.write_text(
        domain
        .read_text(encoding=c.DEFAULT_ENCODING)
        .replace(
            "class DemoMemberModels(m):",
            "class ModelNamespaceParts:\n"
            + (
                "    pass\n\n\n"
                if empty_model
                else "    class Token:\n        pass\n\n\n"
            )
            + "class DemoMemberModels(m):",
        )
        .replace(
            "\nm = DemoMemberModels",
            f"\n    class {namespace}(ModelNamespaceParts):\n"
            "        pass\n\nm = DemoMemberModels",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS + "\n\nfrom typing import runtime_checkable\n"
        "class NamespaceMarker(Protocol):\n    pass\n"
        "class ProtocolNamespaceParts:\n"
        "    @runtime_checkable\n"
        "    class Token(Protocol):\n"
        "        def bind(self) -> bool: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "protocols.py").write_text(
        PROTOCOLS.replace(
            "import ManualPort",
            "import ManualPort, NamespaceMarker, ProtocolNamespaceParts",
        ).replace(
            "\np = DemoMemberProtocols",
            f"\n    class {namespace}"
            + (
                "(NamespaceMarker):\n"
                "        Token: type[ProtocolNamespaceParts.Token] = "
                "ProtocolNamespaceParts.Token\n"
                if empty_model
                else "(ProtocolNamespaceParts, NamespaceMarker):\n        pass\n"
            )
            + "\np = DemoMemberProtocols",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        CONSUMER + f"\nPUBLIC_NAMESPACE = p.{namespace}\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import consumer, m, p\n"
        "from demo_member._protocols.manual_ports import ProtocolNamespaceParts\n"
        f"assert consumer.PUBLIC_NAMESPACE is p.{namespace}\n"
        f"assert p.{namespace}.Token is ProtocolNamespaceParts.Token\n"
        f"assert not hasattr(m.{namespace}, 'model_fields')\n"
        + (
            ""
            if empty_model
            else f"assert not hasattr(m.{namespace}.Token, 'model_fields')\n"
        )
        + "class LivePort:\n    def bind(self) -> bool: return True\n"
        f"assert isinstance(LivePort(), p.{namespace}.Token)\n"
        "assert callable(p.DemoMember.ManualPort.bind)\n"
        "assert isinstance(m.DemoMember.Order(sku='namespace-consumer'), "
        "p.DemoMember.Order)\n",
    )


@pytest.mark.parametrize(
    "shape", ["empty", "fields", "nested-fields", "class-valued-field"]
)
def test_payload_with_plain_counterpart_still_fails_before_publication(
    member_root: t.DirectoryPath, shape: str
) -> None:
    """Empty markers and nested types cannot hide a non-model payload counterpart."""
    package = member_root / "src" / MEMBER
    nested = shape in {"nested-fields", "class-valued-field"}
    domain = package / "_models/domain.py"
    domain.write_text(
        domain.read_text(encoding=c.DEFAULT_ENCODING).replace(
            "Order = Order",
            "Order = Order\n        class Invalid:\n"
            + (
                "            class Record:\n                pass\n"
                if nested
                else "            pass\n"
            ),
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS
        + "\n\nclass Invalid(Protocol):\n"
        + ("    class Record(Protocol):\n        pass\n" if nested else "")
        + (
            "    pass\n"
            if shape == "empty"
            else "    value: str = Record\n"
            if shape == "class-valued-field"
            else "    value: str\n"
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("import ManualPort", "import ManualPort, Invalid").replace(
            "ManualPort = ManualPort",
            "ManualPort = ManualPort\n        Invalid = Invalid",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        CONSUMER + "\n\ndef reject(value: p.DemoMember.Invalid) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        f"package = root / 'src' / {MEMBER!r}\n"
        "before = {path: path.read_bytes() for path in package.rglob('*.py')}\n"
        "result = service.execute()\n"
        "assert result.failure\n"
        "assert 'referenced protocol p.DemoMember.Invalid is not a model declaration' "
        "in result.error\n"
        "assert {path: path.read_bytes() for path in package.rglob('*.py')} "
        "== before\n",
        consumer="",
    )


def test_authored_model_projection_transfers_without_removing_operational_ports(
    member_root: t.DirectoryPath,
) -> None:
    """The native transfer replaces incomplete data while retaining real ports."""
    package = member_root / "src" / MEMBER
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS + "\n\nclass Order(Protocol):\n"
        '    """An incomplete authored model-shaped projection."""\n'
        "    sku: str\n",
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("import ManualPort", "import ManualPort, Order").replace(
            "ManualPort = ManualPort", "ManualPort = ManualPort\n        Order = Order"
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "from demo_member._protocols.manual_ports import ManualPort\n"
        "assert p.DemoMember.ManualPort is ManualPort\n"
        "assert callable(ManualPort.bind)\n"
        'assert get_type_hints(p.DemoMember.Order.quantity.fget)["return"] is int\n'
        'assert isinstance(m.DemoMember.Order(sku="transferred"), '
        "p.DemoMember.Order)\n",
    )


def test_generation_uses_current_source_not_cached_model_classes(
    member_root: t.DirectoryPath,
) -> None:
    """A previously imported class cannot override the authenticated source view."""
    _probe(
        member_root,
        "from demo_member import m\n"
        "cached = m.DemoMember.Order\n"
        'assert cached.model_fields["sku"].annotation is str\n'
        'domain = root / "src/demo_member/_models/domain.py"\n'
        'domain.write_text(domain.read_text().replace("sku: str", "sku: bytes"))\n'
        "tm.ok(service.execute())\n"
        'assert cached.model_fields["sku"].annotation is str\n',
        consumer="from demo_member import p\n"
        'assert get_type_hints(p.DemoMember.Order.sku.fget)["return"] is bytes\n',
    )


def test_concrete_model_alias_is_rewired_without_retiring_the_schema(
    member_root: t.DirectoryPath,
) -> None:
    """Replacing a leaked m alias must preserve the original Pydantic model."""
    package = member_root / "src" / MEMBER
    (package / "protocols.py").write_text(
        PROTOCOLS.replace(
            "from flext_core import p",
            "from flext_core import p\nfrom demo_member import m",
        ).replace(
            "ManualPort = ManualPort",
            "ManualPort = ManualPort\n        Order = m.DemoMember.Order",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "assert p.DemoMember.Order is not m.DemoMember.Order\n"
        'value = m.DemoMember.Order(sku="retained-schema")\n'
        "assert isinstance(value, p.DemoMember.Order)\n"
        'assert value.model_dump()["sku"] == "retained-schema"\n',
    )


def test_transferred_consumer_binds_the_canonical_public_protocol_facade(
    member_root: t.DirectoryPath,
) -> None:
    """The final consumer imports public p and accepts the real model at runtime."""
    package = member_root / "src" / MEMBER
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS + "\n\nclass Order(Protocol):\n"
        '    """An incomplete legacy data projection."""\n'
        "    sku: str\n",
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("import ManualPort", "import ManualPort, Order").replace(
            "ManualPort = ManualPort", "ManualPort = ManualPort\n        Order = Order"
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        "def ship(order: p.DemoMember.Order) -> str:\n"
        "    return order.sku\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import consumer, m, p\n"
        "assert consumer.p is p\n"
        'assert get_type_hints(consumer.ship)["order"] is p.DemoMember.Order\n'
        'value = m.DemoMember.Order(sku="public-boundary")\n'
        "assert isinstance(value, p.DemoMember.Order)\n"
        'assert consumer.ship(value) == "public-boundary"\n',
    )


def test_tooling_observes_the_projected_facade_and_export_epoch(
    member_root: t.DirectoryPath,
) -> None:
    """A legacy facade spelling cannot leak from the old source into tooling."""
    package = member_root / "src" / MEMBER
    (package / "protocols.py").write_text(
        PROTOCOLS.replace("DemoMemberProtocols", "DemoMemberProtocolParts"),
        encoding=c.DEFAULT_ENCODING,
    )
    u.Tests.run_lazy_init(member_root)
    _probe(
        member_root,
        consumer="from demo_member import consumer, m, p\n"
        'assert get_type_hints(consumer.ship)["order"] is p.DemoMember.Order\n'
        'assert isinstance(m.DemoMember.Order(sku="fresh-source"), '
        "p.DemoMember.Order)\n",
    )


def test_operational_port_model_annotations_use_the_projected_contract(
    member_root: t.DirectoryPath,
) -> None:
    """Native annotation rewiring retains the authored operational interface."""
    package = member_root / "src" / MEMBER
    (package / "_protocols/manual_ports.py").write_text(
        MANUAL_PORTS.replace(
            "from typing import Protocol",
            "from typing import Protocol\nfrom demo_member import m",
        ).replace(
            "def bind(self) -> bool:",
            "def bind(self, value: m.DemoMember.Order) -> m.DemoMember.Order:",
        ),
        encoding=c.DEFAULT_ENCODING,
    )
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        "def bind(port: p.DemoMember.ManualPort) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "from demo_member._protocols.manual_ports import ManualPort\n"
        "assert p.DemoMember.ManualPort is ManualPort\n"
        "hints = get_type_hints(ManualPort.bind)\n"
        'assert hints["value"] is p.DemoMember.Order\n'
        'assert hints["return"] is p.DemoMember.Order\n'
        'assert isinstance(m.DemoMember.Order(sku="port"), hints["value"])\n',
    )


def test_distinct_same_named_models_cannot_silently_collapse_a_union(
    member_root: t.DirectoryPath,
) -> None:
    """Distinct native Item identities fail explicitly instead of losing a leaf."""
    domain = member_root / "src" / MEMBER / "_models/domain.py"
    source = domain.read_text(encoding=c.DEFAULT_ENCODING)
    source = source.replace(
        "type Payload = Order | ShipmentPayload",
        "class Left:\n    class Item(m.FrozenModel):\n"
        '        left: str = m.Field(description="Left value.")\n'
        "class Right:\n    class Item(m.FrozenModel):\n"
        '        right: int = m.Field(description="Right value.")\n'
        "type Payload = Left.Item | Right.Item",
    ).replace(
        "Payload = Payload",
        "Payload = Payload\n        Left = Left\n        Right = Right",
    )
    domain.write_text(source, encoding=c.DEFAULT_ENCODING)
    _probe(
        member_root,
        "result = service.execute()\n"
        'assert result.failure and "competing generated protocol member identities" '
        "in result.error\n",
        consumer="",
    )


def test_specialized_alias_closes_over_its_model_payload(
    member_root: t.DirectoryPath,
) -> None:
    """An Envelope[str] field retains its source Order dependency and argument."""
    (member_root / "src" / MEMBER / "consumer.py").write_text(
        "from demo_member import p\n"
        "def ship(value: p.DemoMember.Shipment) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import p\n"
        'assert get_type_hints(p.DemoMember.Shipment.envelope.fget)["return"] '
        "== tuple[p.DemoMember.Order, str] | None\n",
    )


def test_recursive_member_annotations_resolve_through_real_owner_names(
    member_root: t.DirectoryPath,
) -> None:
    """Mutual model references remain resolvable without own-facade reentry."""
    package = member_root / "src" / MEMBER
    domain = package / "_models/domain.py"
    source = (
        domain
        .read_text(encoding=c.DEFAULT_ENCODING)
        .replace(
            "class DemoMemberModels(m):",
            "class NodeA(m.FrozenModel):\n"
            '    """A node referencing the second model."""\n'
            '    peer: "NodeB | None" = m.Field(default=None, description="Peer.")\n'
            "class NodeB(m.FrozenModel):\n"
            '    """A node referencing the first model."""\n'
            '    peer: NodeA | None = m.Field(default=None, description="Peer.")\n'
            "NodeA.model_rebuild()\n\nclass DemoMemberModels(m):",
        )
        .replace(
            "Order = Order",
            "Order = Order\n        NodeA = NodeA\n        NodeB = NodeB",
        )
    )
    domain.write_text(source, encoding=c.DEFAULT_ENCODING)
    (package / "consumer.py").write_text(
        "from demo_member import p\n"
        "def accept(value: p.DemoMember.NodeA) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        'assert get_type_hints(p.DemoMember.NodeA.peer.fget)["return"] '
        "== p.DemoMember.NodeB | None\n"
        'assert get_type_hints(p.DemoMember.NodeB.peer.fget)["return"] '
        "== p.DemoMember.NodeA | None\n"
        "assert isinstance(m.DemoMember.NodeA(peer=m.DemoMember.NodeB()), "
        "p.DemoMember.NodeA)\n",
    )


def test_budgeted_owners_are_resolvable_through_the_generated_barrel(
    member_root: t.DirectoryPath,
) -> None:
    """A real multi-part projection exports every requested model contract."""
    package = member_root / "src" / MEMBER
    domain = package / "_models/domain.py"
    declarations = "\n\n".join(
        f'class Bulk{index}(m.FrozenModel):\n    """A budgeted model."""\n'
        + "\n".join(
            f'    field{field}: str = m.Field(default="value", description="Field.")'
            for field in range(25)
        )
        + (
            f"\n    previous: Bulk{index - 1} | None = m.Field(default=None, "
            'description="Previous model.")'
            if index
            else ""
        )
        for index in range(18)
    )
    source = (
        domain
        .read_text(encoding=c.DEFAULT_ENCODING)
        .replace(
            "class DemoMemberModels(m):",
            f"{declarations}\n\nclass DemoMemberModels(m):",
        )
        .replace(
            "Order = Order",
            "Order = Order\n"
            + "\n".join(f"        Bulk{index} = Bulk{index}" for index in range(18)),
        )
    )
    domain.write_text(source, encoding=c.DEFAULT_ENCODING)
    types = ", ".join(f"p.DemoMember.Bulk{index}" for index in range(18))
    (package / "consumer.py").write_text(
        f"from demo_member import p\ndef accept(values: tuple[{types}]) -> None: ...\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(
        member_root,
        consumer="from demo_member import m, p\n"
        "for index in range(18):\n"
        '    port = getattr(p.DemoMember, f"Bulk{index}")\n'
        '    model = getattr(m.DemoMember, f"Bulk{index}")\n'
        "    assert isinstance(model(), port)\n"
        '    assert get_type_hints(port.field24.fget)["return"] is str\n'
        "    if index:\n"
        '        assert get_type_hints(port.previous.fget)["return"] '
        '== getattr(p.DemoMember, f"Bulk{index - 1}") | None\n',
    )


@pytest.mark.parametrize(
    ("imports", "alias", "signature", "message"),
    [
        (
            "from typing import Any\n",
            "type Weak = Any\n",
            "value: Weak",
            "forbidden generated protocol annotation",
        ),
        ("", "", "value", "untyped signature"),
    ],
)
def test_weak_or_untyped_method_contracts_fail_before_publication(
    member_root: t.DirectoryPath,
    imports: str,
    alias: str,
    signature: str,
    message: str,
) -> None:
    """Weak aliases and untyped parameters are not emitted as structural ports."""
    domain = member_root / "src" / MEMBER / "_models/domain.py"
    source = domain.read_text(encoding=c.DEFAULT_ENCODING)
    source = source.replace(
        "from flext_core import m, t", f"{imports}from flext_core import m, t\n{alias}"
    )
    source = source.replace(
        "    quantity: int = m.Field(default=1, "
        'description="Number of units ordered.")',
        "    quantity: int = m.Field(default=1, "
        'description="Number of units ordered.")\n'
        f"    def inspect(self, {signature}) -> str: ...",
    )
    domain.write_text(source, encoding=c.DEFAULT_ENCODING)
    _probe(
        member_root,
        "from pytest import raises\n"
        f"with raises(TypeError, match={message!r}):\n"
        "    service.execute()\n",
        consumer="",
    )


@pytest.mark.parametrize(
    "source_root", ["tests", "scripts", "examples", "workflow_tools"]
)
@pytest.mark.parametrize(
    "annotation", ["ports.DemoMember.Order", '"ports.DemoMember.Order"']
)
def test_discovery_uses_real_references_in_every_root(
    member_root: t.DirectoryPath,
    source_root: str,
    annotation: str,
) -> None:
    """Aliases work; documentation and shadowed names select no contracts."""
    (member_root / "src" / MEMBER / "consumer.py").unlink()
    source = member_root / source_root
    source.mkdir()
    (source / "consumer.py").write_text(
        '"""ports.DemoMember.Ghost is documentation."""\n'
        "from demo_member import p as ports\n"
        f"def ship(order: {annotation}) -> None: ...\n"
        "def shadow(ports: str) -> str: return ports.strip()\n"
        "# ports.DemoMember.Ghost is documentation.\n",
        encoding=c.DEFAULT_ENCODING,
    )
    _probe(member_root)
