"""Provisioned consumer, fleet, Make-template and checkout fixtures.

Owns the session-scoped provisioning fixtures: consumer templates, installed
fleet workspaces, generated Make templates and provisioned infra checkouts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from collections.abc import Mapping

import re
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
import hashlib
import os
import sys
from collections.abc import Iterator
from functools import partial
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import codegen, config, infra, workspace
from tests import c, m, p, t, tm, u

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_CONSUMER_UPGRADE_RECEIPT = "upgrade-receipt.json"
_CONSUMER_BUILD_RECEIPT = "build-receipt.json"


def _consumer_pyproject_source(distribution: str) -> str:
    """Render the governed consumer fixture's pyproject source.

    Args:
        distribution: The consumer distribution name being provisioned.

    Returns:
        The pyproject source declaring the governed consumer contract.

    """
    modules = c.Tests.CONSUMER_MODULES
    # A governed FLEXT consumer declares exactly one runtime upstream profile;
    # conform derives its project spec from it (context_render.py).
    upstream = u.Tests.flext_source("flext-core")
    dependencies = ", ".join(f'"{name}"' for name in (upstream, *modules))
    infrastructure = tm.ok(
        u.Infra.configured_repository_ref(
            codegen=config.Infra.codegen,
            repository_root=_PROJECT_ROOT,
        ),
    )
    integration = tm.ok(
        u.Infra.flext_integration_line(
            codegen=config.Infra.codegen,
            repository_root=_PROJECT_ROOT,
        ),
    )
    python_required = config.Infra.codegen.toolchain.python_required_version
    infrastructure_source = (
        f"{infrastructure.distribution} @ git+{infrastructure.url}@{integration.branch}"
    )
    development = ", ".join(
        f'"{u.Tests.flext_source(name) if name.startswith("flext-") else requirement}"'
        for requirement in config.Infra.codegen.scaffold.project.dev
        if (name := u.Infra.dep_name(requirement)) is not None and name != distribution
    )
    return (
        '[build-system]\nrequires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n'
        f'[project]\nname = "{distribution}"\nversion = "0.1.0"\n'
        f'description = "{distribution} governed fixture"\n'
        'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n'
        f'license = "{u.Tests.project_spec(distribution).license}"\n'
        f'requires-python = "{python_required}"\n'
        f"dependencies = [{dependencies}]\n"
        '[project.optional-dependencies]\nfeature = ["requests"]\n'
        # A governed checkout declares every internal requirement with its
        # own direct Git source; the scaffold dev SSOT includes flext-tests.
        f'[dependency-groups]\ndev = [{development}, "pip", '
        f'"{infrastructure_source}"]\n'
        "[tool.hatch.metadata]\nallow-direct-references = true\n"
        "[tool.mypy]\n"
        '[tool.deptry]\noptional_dependencies_dev_groups = ["dev"]\n'
    )


def _declare_fleet_members(
    root: Path,
    distribution: str,
    member_dependencies: Mapping[str, Sequence[str]],
) -> None:
    """Commit each fleet member with its runtime requirements and attach it."""
    beads = u.Tests.BeadsIdentity(
        workspace=distribution,
        database=distribution.replace("-", "_"),
        issue_prefix="fleet",
    )
    for name, requirements in member_dependencies.items():
        member = root / name
        u.Tests.WorktreeFixture.initialize_governed_project(
            member,
            name,
            beads=beads,
        )
        manifest = member / c.PYPROJECT_FILENAME
        payload = u.Tests.toml_payload(manifest.read_text(encoding="utf-8"))
        project = u.Tests.toml_mapping(payload["project"])
        tm.ok(
            u.Cli.toml_write_mapping(
                manifest,
                {
                    **payload,
                    "project": {
                        **project,
                        "dependencies": [
                            *u.Tests.toml_strings(project["dependencies"]),
                            *requirements,
                        ],
                    },
                },
            ),
        )
        u.Tests.commit_git_changes(member, "declare fleet runtime requirements")
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member,
            distribution=name,
            relative_path=name,
        )


def _provision_consumer_template(
    parent: Path,
    *,
    member_dependencies: Mapping[str, Sequence[str]] | None = None,
) -> Path:
    """Publish activation inputs, then provision the consumer through real Make.

    The installed session owner keeps this physical checkout at a stable path,
    preserving its editable source binding while restoring each case's data.
    The public ENVRC producer publishes activation before sync consumes it.

    Returns:
        The provisioned consumer with committed locks and a physical environment.

    """
    distribution = "flext-demo"
    root = u.Tests.mk_project(
        parent,
        distribution,
        with_src=True,
        pyproject=_consumer_pyproject_source(distribution),
    )
    (root / "src" / distribution.replace("-", "_") / "__init__.py").write_text(
        "\n".join(
            f"import {name}" for name in ("flext_core", *c.Tests.CONSUMER_MODULES)
        )
        + "\n",
        encoding="utf-8",
    )
    u.Tests.copy_tracked_mise_seeds(root)
    repository = u.Tests.repository_ref(
        root.name,
        role=(
            c.Infra.MakeProfile.WORKSPACE
            if member_dependencies
            else c.Infra.MakeProfile.STANDALONE
        ),
    ).model_copy(update={"editable": True})
    u.Tests.initialize_git_repo(root, origin_url=repository.url)
    if member_dependencies:
        _declare_fleet_members(root, distribution, member_dependencies)
    workspace = u.Tests.workspace_spec(
        repository,
        project=u.Tests.project_spec(root.name),
        subprojects=tuple(
            u.Tests.repository_ref(name, path=Path(name))
            for name in (() if member_dependencies is None else member_dependencies)
        ),
    )
    conform_request = u.Tests.conform_request(
        root,
        what=c.Infra.CodegenConformSurface.MAKEFILE,
    )
    conform = codegen.FlextInfraCodegenConform.Generate(
        repository_root=root,
        state=m.Infra.CodegenConformState(
            repository_root=root,
            initial_workspace=workspace,
            request=conform_request,
        ),
    )
    planned = conform.plan(conform_request)
    plan = tm.ok(planned)
    if plan.exception is not None:
        raise plan.exception
    tm.that(plan.issues, empty=True, msg=str(plan.issues))
    tm.ok(
        u.Tests.materialize_codegen_plans(planned.map(lambda result: result.files)),
    )
    tm.ok(
        infra.codegen_conform(
            u.Tests.conform_request(
                root,
                what=c.Infra.CodegenConformSurface.ENVRC,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        ),
    )
    # A newly scaffolded consumer has no committed locks yet. The public upgrade
    # lifecycle is their sole writer; frozen setup starts only after that first
    # resolved environment has been reviewed and committed by the consumer.
    for verb, receipt in (
        ("upg", _CONSUMER_UPGRADE_RECEIPT),
        ("setup", _INFRA_SETUP_RECEIPT),
        ("build", _CONSUMER_BUILD_RECEIPT),
    ):
        output = tm.ok(
            u.Tests.run_isolated_make(
                [verb],
                cwd=root,
                env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]},
            ),
        )
        _write_receipt(parent / receipt, output)
        tm.that(
            u.Cli.process_succeeded(output.outcome),
            eq=True,
            msg=output.stdout + output.stderr,
        )
        if verb == "upg":
            u.Tests.git_bootstrap(root, ("add", "-A"))
            u.Tests.git_bootstrap(root, ("commit", "-q", "-m", "upg: resolved locks"))
    environment = u.Infra.runtime_environment_dir(root)
    tm.fail(environment.is_symlink())
    tm.ok((environment / "pyvenv.cfg").is_file())
    return root


_FLEET_PROVISION = partial(
    _provision_consumer_template,
    member_dependencies={
        "fleet-provider": (),
        "fleet-consumer": ("fleet-provider",),
    },
)


@pytest.fixture(scope="session")
def fleet_session_runtime(
    tmp_path_factory: pytest.TempPathFactory,
    run_namespace: m.Tests.TestNamespace,
) -> Iterator[p.Tests.SessionRuntime]:
    """Own the distinct installed workspace seed through the shared runtime owner.

    A runtime accepts one provision callback. This topology has Git members,
    while the ordinary consumer seed deliberately remains standalone.

    Yields:
        The leased ``p.Tests.SessionRuntime``.

    """
    runtime = u.Tests.SessionRuntime(
        tmp_path_factory.mktemp(f"{run_namespace.token}-fleet"),
    )
    try:
        yield runtime
    finally:
        runtime.close()


@pytest.fixture
def installed_fleet_workspace(
    fleet_session_runtime: p.Tests.SessionRuntime,
) -> Iterator[Path]:
    """Lease actual generated members and frozen installed metadata at stable paths.

    Yields:
        The leased workspace root ``Path``.

    """
    with fleet_session_runtime.lease(
        _FLEET_PROVISION,
        mutable_environment=True,
    ) as root:
        yield root


@pytest.fixture
def native_fleet_signal_hook(installed_fleet_workspace: Path) -> Path:
    """Inject SIGTERM through the generated hook on the Linux acceptance platform.

    The procfs ancestry contract belongs only to this fault-injection fixture.
    Other native platforms require their own equivalent proof, never a skip
    reported as successful signal handling.

    Returns:
        The leased workspace root ``Path``.

    """
    if sys.platform != "linux":
        pytest.fail(
            "Linux procfs signal injection is inapplicable; this platform "
            "requires its own configured native Make signal proof",
        )
    root = installed_fleet_workspace
    members = tm.ok(
        workspace.FlextInfraWorkspaceEnvironmentProvenance.editable_members(root),
    )
    ordered = u.Infra.workspace_dependency_order(root, members)
    provider = next(member for member in members if member.distribution == ordered[0])
    member_root = root / provider.path
    fault = member_root / "scripts" / "fleet_signal_fault.py"
    fault.parent.mkdir(parents=True, exist_ok=True)
    fault.write_text(
        """\
import os
import sys
from pathlib import Path
from signal import SIGTERM

executable = Path(sys.argv[1]).resolve(strict=True)
makefile = Path(sys.argv[2]).resolve(strict=True)
pid = os.getppid()
targets = []
while pid > 1:
    process = Path("/proc") / str(pid)
    arguments = process.joinpath("cmdline").read_bytes().split(b"\\0")
    arguments = [os.fsdecode(argument) for argument in arguments if argument]
    if process.joinpath("exe").resolve(strict=True) == executable and "-f" in arguments:
        selected = Path(arguments[arguments.index("-f") + 1])
        selected = process.joinpath("cwd").resolve(strict=True) / selected
        if selected.resolve(strict=True) == makefile:
            targets.append(pid)
    parent = next(
        line for line in process.joinpath("status").read_text().splitlines()
        if line.startswith("PPid:")
    )
    pid = int(parent.split()[1])
if not targets:
    raise RuntimeError("No exact fleet Make invocation owns this native hook")
print("Native fleet hook sends SIGTERM to its exact Make ancestry", flush=True)
for target in reversed(targets):
    os.kill(target, SIGTERM)
""",
        encoding=c.DEFAULT_ENCODING,
    )
    custom = member_root / c.Infra.CUSTOM_MAKE_FILENAME
    content = custom.read_text(encoding=c.DEFAULT_ENCODING) if custom.exists() else ""
    tm.fail("pre-fmt:" in content)
    makefile = quote(str(member_root / c.Infra.MAKEFILE_FILENAME))
    custom.write_text(
        content
        + "\n.PHONY: pre-fmt\npre-fmt:\n"
        + f"\t@$(PROJECT_INFRA_RUN) {quote(str(fault))} "
        + f'"$(SELF_MAKE_EXECUTABLE)" {makefile}\n',
        encoding=c.DEFAULT_ENCODING,
    )
    return root


_MAKE_UPGRADE_RECEIPT = c.Tests.MAKE_TEMPLATE_UPG_RECEIPT
_MAKE_CI_SETUP_RECEIPT = c.Tests.MAKE_TEMPLATE_CI_RECEIPT
_INFRA_SETUP_RECEIPT = "setup-receipt.json"
_GIT_MIRRORS_RECEIPT = "mirrors-receipt.txt"
# Every scenario that provisions the candidate's own environment before `gen`.
_INFRA_CHECKOUT_SCENARIOS = (
    "builtin",
    "custom",
    "producer-failure",
    "activation-failure",
)


def _run_scoped(run_root: Path, kind: str, key: str) -> Path:
    """Return the run-scoped home of one provisioned consumer.

    Returns:
        The run-scoped home of one provisioned consumer.

    """
    return run_root / kind / key


def _write_receipt(path: Path, output: p.Cli.CommandOutput) -> None:
    u.Tests.record_dependency_command_output(output)
    tm.ok(
        u.Cli.atomic_write_text_file(
            path,
            m.Cli.CommandOutput.model_validate(
                output,
                from_attributes=True,
            ).model_dump_json(),
        ),
    )


def _provision_make_template(
    run_root: Path,
    profile: c.Infra.MakeProfile,
    git_environment: Mapping[str, str],
) -> None:
    """Resolve one generated consumer through ``make upg`` once per run.

    The upgrade runs under a foreign uv environment with a declared post-upg
    hook, and a checkout of the resolved result installs every locked tool
    into cold CI storage; both receipts are what the consumers assert.
    """
    parent = _run_scoped(run_root, "make-templates", profile.value)
    # Git inputs remain immutable file-only mirrors. Native registry wheels,
    # build requirements and cold Mise artifacts still require provisioning.
    git_environment = {**git_environment, "UV_OFFLINE": c.ParserBooleanToken.ZERO}
    root, _ = u.Tests.render_make_environment(parent, profile, bootstrap=True)
    candidate_url = u.Tests.repository_ref(
        config.Infra.codegen.infra_repository.distribution,
    ).url
    candidate = next(
        source
        for source in u.Tests.locked_git_sources(_PROJECT_ROOT)
        if source[0] == candidate_url
    )
    source_probe = (
        "import base64,hashlib,importlib.metadata as md,json,pathlib,sys,flext_infra; "
        f"distribution=md.distribution({config.Infra.name!r}); "
        "source=json.loads(distribution.read_text('direct_url.json')); "
        f"assert source['url']=={candidate[0]!r},source; "
        f"assert source['vcs_info']['commit_id']=={candidate[2]!r},source; "
        "module=pathlib.Path(flext_infra.__file__).resolve(); "
        "assert module.is_relative_to(pathlib.Path(sys.prefix).resolve()),module; "
        "record=next(item for item in distribution.files "
        "if distribution.locate_file(item).resolve()==module); "
        "assert record.hash is not None,record; "
        "digest=hashlib.new(record.hash.mode,module.read_bytes()); "
        "assert base64.urlsafe_b64encode(digest.digest()).rstrip(b'=').decode()"
        "==record.hash.value,record; "
        f"print('candidate-source={candidate[0]}#{candidate[2]}'); "
        "print('candidate-module='+str(module)); "
        "print('candidate-module-record='+record.hash.value); "
        "print('candidate-prefix='+str(pathlib.Path(sys.prefix).resolve()))"
    )
    hostile_venv = parent / c.Tests.MAKE_TEMPLATE_HOSTILE_VENV
    (hostile_venv / "bin").mkdir(parents=True)
    (hostile_venv / "sentinel").write_text("untouched\n", encoding="utf-8")
    custom = root / c.Infra.CUSTOM_MAKE_FILENAME
    custom.write_text(
        custom.read_text(encoding="utf-8") + ".PHONY: post-upg post-status\n"
        "post-upg:\n\t@printf '%s\\n' 'upg-hook-ran'\n"
        f"post-status:\n\t@$(PROJECT_INFRA_RUN) -I -c {quote(source_probe)}\n",
        encoding="utf-8",
    )
    upgrade = tm.ok(
        u.Tests.run_isolated_make(
            ["--no-print-directory", "upg"],
            cwd=root,
            env={
                **git_environment,
                **u.Tests.hostile_uv_environment(hostile_venv),
            },
        ),
    )
    _write_receipt(parent / _MAKE_UPGRADE_RECEIPT, upgrade)
    if not u.Cli.process_succeeded(upgrade.outcome):
        return
    origin = tm.ok(
        u.Tests.run_isolated_make(
            ["--no-print-directory", "status"],
            cwd=root,
            env=git_environment,
        ),
    )
    _write_receipt(
        parent
        / Path(_MAKE_UPGRADE_RECEIPT).with_stem(
            f"{Path(_MAKE_UPGRADE_RECEIPT).stem}-source",
        ),
        origin,
    )
    if not u.Cli.process_succeeded(origin.outcome):
        return
    checkout = u.Tests.resolved_make_checkout(
        root,
        parent / c.Tests.MAKE_TEMPLATE_CI_CHECKOUT,
        profile,
    )
    make = config.Infra.codegen.make
    ci_custom = checkout / c.Infra.CUSTOM_MAKE_FILENAME
    ci_custom.write_text(
        ".PHONY: post-setup\npost-setup:\n"
        '\t@test -x "$(MAKE_COMMAND)"\n'
        '\t@test "$(MAKE_COMMAND)" = "$(SELF_MAKE_EXECUTABLE)"\n'
        f'\t@test "$({make.ci.variable})" = "{make.ci.value}"\n'
        "\t@printf '%s\\n' 'ci-runtime-provisioned'\n"
        ".PHONY: post-status\n"
        f"post-status:\n\t@$(PROJECT_INFRA_RUN) -I -c {quote(source_probe)}\n",
        encoding="utf-8",
    )
    setup = tm.ok(
        u.Tests.run_isolated_make(
            ["--no-print-directory", "setup"],
            cwd=checkout,
            env={
                **git_environment,
                **u.Tests.hostile_uv_environment(hostile_venv),
                make.ci.variable: make.ci.value,
                c.Tests.MISE_DATA_DIR_ENV: str(parent / c.Tests.COLD_MISE_STORAGE),
            },
        ),
    )
    _write_receipt(parent / _MAKE_CI_SETUP_RECEIPT, setup)
    if not u.Cli.process_succeeded(setup.outcome):
        return
    origin = tm.ok(
        u.Tests.run_isolated_make(
            ["--no-print-directory", "status"],
            cwd=checkout,
            env={
                **git_environment,
                make.ci.variable: make.ci.value,
                c.Tests.MISE_DATA_DIR_ENV: str(parent / c.Tests.COLD_MISE_STORAGE),
            },
        ),
    )
    _write_receipt(
        parent
        / Path(_MAKE_CI_SETUP_RECEIPT).with_stem(
            f"{Path(_MAKE_CI_SETUP_RECEIPT).stem}-source",
        ),
        origin,
    )


def _provision_infra_checkout(run_root: Path, scenario: str) -> None:
    """Set up one candidate checkout from its committed locks before its item."""
    parent = _run_scoped(run_root, "infra-checkouts", scenario)
    root = u.Tests.infra_source_checkout(parent)
    setup = tm.ok(
        u.Tests.run_isolated_make(["--no-print-directory", "setup"], cwd=root),
    )
    _write_receipt(parent / _INFRA_SETUP_RECEIPT, setup)


def _ensure_provisioned(
    run_root: Path,
    parent: Path,
    receipt: str,
    key: c.Infra.MakeProfile | str,
    *,
    git_environment: Mapping[str, str] | None = None,
) -> None:
    """Provision only a consumed fixture under the shared file lock.

    Testmon inventory and selection collect tests without network or writes.
    Provisioning belongs to the item that actually consumes the checkout, so
    its cost and failure remain visible to the test deadline and report.

    Raises:
        ValueError: If a Make profile is requested without its Git environment.

    """
    parent.mkdir(parents=True, exist_ok=True)
    with u.Cli.file_changes_lock(parent / f"{receipt}.lock"):
        if (parent / receipt).is_file():
            return
        match key:
            case c.Infra.MakeProfile():
                if git_environment is None:
                    msg = "Make templates require their declared immutable Git mirrors"
                    raise ValueError(msg)
                _provision_make_template(run_root, key, git_environment)
            case str():
                _provision_infra_checkout(run_root, key)


@pytest.fixture(scope="session")
def hermetic_git_environment(session_runtime: p.Tests.SessionRuntime) -> Mapping[str, str]:
    """Serve the fixture provider's Git sources from this run's local mirrors.

    The mirrors are built once per locked-source set under the canonical
    file lock from objects this checkout already holds; the directory is
    keyed by that set, so a relock never reuses mirrors of superseded commits.
    The returned environment routes the provider to them and makes any network
    transport fail.

    Returns:
        The resulting ``Mapping[str, str]``.

    """
    locked = u.Tests.locked_git_sources(_PROJECT_ROOT)
    sources = "\n".join("@".join(source) for source in locked)
    parent = _run_scoped(
        session_runtime.directory,
        "git-mirrors",
        hashlib.sha256(sources.encode()).hexdigest()[:16],
    )
    parent.mkdir(parents=True, exist_ok=True)
    receipt = parent / _GIT_MIRRORS_RECEIPT
    mirrors = parent / "mirrors"
    with u.Cli.file_changes_lock(receipt.with_name(f"{receipt.name}.lock")):
        if not receipt.is_file():
            mirrored = u.Tests.build_git_mirrors(_PROJECT_ROOT, mirrors, locked)
            tm.ok(u.Cli.atomic_write_text_file(receipt, "\n".join(mirrored) + "\n"))
    return u.Tests.hermetic_git_environment(mirrors)


@pytest.fixture(scope="session", params=tuple(c.Infra.MakeProfile))
def generated_make_template(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[c.Infra.MakeProfile, Path]:
    """Render the real Make contract once per profile and worker session.

    Returns:
        The declared profile and its generated project checkout.

    """
    profile = c.Infra.MakeProfile(request.param)
    root, _ = u.Tests.render_make_environment(
        tmp_path_factory.mktemp(f"make-contract-{profile.value}"),
        profile,
        bootstrap=True,
    )
    return profile, root


@pytest.fixture(scope="session")
def resolved_make_templates(
    session_runtime: p.Tests.SessionRuntime,
    hermetic_git_environment: Mapping[str, str],
) -> Mapping[c.Infra.MakeProfile, Path]:
    """Return committed templates owned by this isolated worker-session.

    Consumers clone a template rather than resolving inside their budget; the
    template directory also holds the upgrade and cold CI setup receipts.

    Returns:
        Every profile's committed ``make upg`` template for this run.

    """
    templates: t.MutableMappingKV[c.Infra.MakeProfile, Path] = {}
    for profile in c.Infra.MakeProfile:
        run_root = session_runtime.directory
        parent = _run_scoped(run_root, "make-templates", profile.value)
        _ensure_provisioned(
            run_root,
            parent,
            _MAKE_UPGRADE_RECEIPT,
            profile,
            git_environment=hermetic_git_environment,
        )
        upgrade = u.Tests.command_receipt(parent / _MAKE_UPGRADE_RECEIPT)
        tm.that(
            u.Cli.process_succeeded(upgrade.outcome),
            eq=True,
            msg=upgrade.stdout + upgrade.stderr,
        )
        templates[profile] = parent / profile.value / "fixture-project"
    return templates


@pytest.fixture(params=_INFRA_CHECKOUT_SCENARIOS)
def provisioned_infra_checkout(
    request: pytest.FixtureRequest,
    session_runtime: p.Tests.SessionRuntime,
) -> tuple[str, Path]:
    """Return one scenario's candidate checkout, set up from committed locks.

    Returns:
        One scenario's candidate checkout, set up from committed locks.

    """
    scenario = str(request.param)
    run_root = session_runtime.directory
    parent = _run_scoped(run_root, "infra-checkouts", scenario)
    _ensure_provisioned(run_root, parent, _INFRA_SETUP_RECEIPT, scenario)
    setup = u.Tests.command_receipt(parent / _INFRA_SETUP_RECEIPT)
    tm.that(
        u.Cli.process_succeeded(setup.outcome),
        eq=True,
        msg=setup.stdout + setup.stderr,
    )
    root = parent / config.Infra.name
    tm.ok((u.Infra.runtime_environment_dir(root) / "pyvenv.cfg").is_file())
    return scenario, root


@pytest.fixture(params=c.Tests.DETECTOR_MODULE_SCENARIOS[:1])
def real_detector_project(
    request: pytest.FixtureRequest,
    session_runtime: p.Tests.SessionRuntime,
) -> Iterator[Path]:
    """Lease the worker consumer with case-local declarations and environment state.

    Yields:
        The shared physical checkout restored after dependency mutation.

    """
    modules = t.Infra.STR_SEQ_ADAPTER.validate_python(request.param)
    with session_runtime.lease(
        _provision_consumer_template, mutable_environment=True
    ) as root:
        manifest = root / c.PYPROJECT_FILENAME
        payload = u.Tests.toml_payload(manifest.read_text(encoding="utf-8"))
        project = u.Tests.toml_mapping(payload["project"])
        dependencies: list[t.JsonValue] = [
            requirement
            for requirement in u.Tests.toml_strings(project["dependencies"])
            if (name := u.Infra.dep_name(requirement)) not in c.Tests.CONSUMER_MODULES
            or name in modules
        ]
        project_update: t.JsonDict = {
            **project,
            "dependencies": dependencies,
        }
        updated: t.JsonMapping = {**payload, "project": project_update}
        tm.ok(u.Cli.toml_write_mapping(manifest, updated))
        (root / "src" / root.name.replace("-", "_") / "__init__.py").write_text(
            "\n".join(
                f"import {name}" for name in ("flext_core", *c.Tests.CONSUMER_MODULES)
            )
            + "\n",
            encoding="utf-8",
        )
        runtime = u.Infra.runtime_environment_dir(root)
        executable = c.Infra.DEPTRY + (".exe" if os.name == "nt" else "")
        tm.that(
            (
                runtime / ("Scripts" if os.name == "nt" else "bin") / executable
            ).is_file(),
            eq=True,
        )
        yield root


@pytest.fixture
def installed_artifact_consumer(
    session_runtime: p.Tests.SessionRuntime,
) -> Iterator[Path]:
    """Lease the native consumer with its installed artifacts restored afterward.

    Yields:
        The leased consumer repository root.

    """
    with session_runtime.lease(
        _provision_consumer_template,
        mutable_environment=True,
    ) as root:
        yield root


@pytest.fixture
def duplicate_project(
    session_runtime: p.Tests.SessionRuntime,
) -> Iterator[Path]:
    """Lease isolated case sources in the worker's once-provisioned consumer.

    Yields:
        The stable editable checkout with case-local source, Git and report state.

    """
    with session_runtime.lease(_provision_consumer_template) as root:
        yield root
