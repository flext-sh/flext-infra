"""Pytest fixtures for FLEXT infra tests.

Provides reusable fixtures for creating real project structures using tmp_path.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import os
import sys
from collections.abc import Iterator
from functools import partial
from pathlib import Path
from shlex import quote

import pytest

from flext_infra import config, infra
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from tests import c, m, p, t, tm, u

_FIXTURES_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def native_consumer(tmp_path: Path) -> p.Tests.NativeConsumer:
    """Exercise public native authentication against real fixture source trees.

    Returns:
        The resulting ``p.Tests.NativeConsumer``.

    """
    runtime = tm.ok(
        FlextInfraWorkspaceDetector.resolution_context(_PROJECT_ROOT)
    ).runtime_root
    prelude = (
        "import importlib, pathlib, sys\n"
        "from pathlib import Path\n"
        "from flext_infra import m\n"
        "from flext_infra.codegen import FlextInfraCodegenPreconditions as "
        "preconditions\n"
        "from flext_infra.validate import FlextInfraValidateFreshImport\n"
        "from flext_infra.workspace.native_reference import "
        "FlextInfraWorkspaceNativeReference as native\n"
        f"runtime_root = Path({str(runtime)!r})\n"
        "def authenticate(name, *, source_root=None):\n"
        "    return FlextInfraValidateFreshImport.capture_producer_reference(\n"
        "        Path.cwd() if source_root is None else source_root,\n"
        "        runtime_root, (m.Infra.SourceClassReference(target=name),))\n"
        "def source_preflight(name):\n"
        "    return preconditions.capture_source_authority(runtime_root,\n"
        "        nominated=(m.Infra.SourceClassReference(target=name),))\n"
    )

    def consume(code: str, *arguments: str, cwd: Path | None = None) -> None:
        u.Tests.run_lazy_init_probe(
            prelude + code,
            python_paths=(),
            arguments=arguments,
            cwd=tmp_path if cwd is None else cwd,
        )

    return consume


@pytest.fixture
def declaration_workspace(tmp_path: Path) -> t.Pair[Path, Path]:
    """Provide the standard FLEXT workspace fabric for native declarations.

    Returns:
        The resulting ``t.Pair[Path, Path]``.

    """
    return u.Tests.create_lazy_init_workspace(tmp_path)


@pytest.fixture
def binding_probe_rule() -> m.Infra.CodemodRule:
    """Supply one validated metadata owner for semantic binding probes.

    Returns:
        The probe rule whose consumer supplies its context conditions.

    """
    return m.Infra.CodemodRule(
        id="binding-probe",
        digest="probe",
        provider="probe",
        resource=Path("probe.yml"),
        fixable=True,
    )


def _read_fixture(*parts: str) -> str:
    return _FIXTURES_DIR.joinpath(*parts).read_text(encoding="utf-8")


def _modernizer_pyproject(name: str) -> str:
    return f'[project]\nname = "{name}"\nversion = "0.1.0"\n'


def _modernizer_workspace_pyproject(*members: str) -> str:
    base = _modernizer_pyproject("workspace")
    if not members:
        return base
    members_text = ", ".join(f'"{member}"' for member in members)
    return f"{base}\n[tool.uv.workspace]\nmembers = [{members_text}]\n"


def _write_modernizer_codegen_config(workspace: Path) -> None:
    """Copy the valid governed SSOT into the isolated modernizer owner.

    Constraint rewriting validates the complete typed codegen contract and
    must never write the installed infrastructure checkout (flext-eles2).
    """
    config_dir = workspace / c.Infra.CODEGEN_CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / c.Infra.CODEGEN_CONFIG_FILENAME).write_bytes(
        (
            _PROJECT_ROOT / c.Infra.CODEGEN_CONFIG_DIR / c.Infra.CODEGEN_CONFIG_FILENAME
        ).read_bytes(),
    )


@pytest.fixture
def deptry_report_payload() -> t.JsonPayload:
    """Provide ``deptry_report_payload``.

    Returns:
        The resulting ``t.JsonPayload``.

    """
    parsed = u.Cli.json_parse(_read_fixture("deps", "deptry_report.json"))
    parsed = tm.not_none(parsed)
    tm.ok(parsed)
    return parsed.value


@pytest.fixture(autouse=True)
def runner_ci_context_cleared() -> Iterator[None]:
    """Keep the runner's CI context out of every test body.

    The approval path runs the suite under ``CI=Y``: collection reads it to
    deselect CI-excluded tests, but a test body must behave identically on a
    runner and on a workstation. Inherited ``CI`` silently selected CI-only
    contracts (the CI member identity, the CI resolution guard) in local
    scenarios; a scenario that exercises a CI contract passes the configured
    variable explicitly.

    Yields:
        Control inside the scoped environment.

    """
    with u.Tests.env_vars_context(
        vars_to_clear=(config.Infra.codegen.make.ci.variable,),
    ):
        yield


@pytest.fixture
def tool_config_document() -> m.Infra.ToolConfigDocument:
    """Provide ``tool_config_document``.

    Returns:
        The resulting ``m.Infra.ToolConfigDocument``.

    """
    return u.Tests.tool_config_document()


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


def _provision_consumer_template(
    parent: Path,
    *,
    member_dependencies: t.MappingKV[str, t.StrSequence] | None = None,
) -> Path:
    """Upgrade and set up the shared worker consumer once through real Make.

    The installed session owner keeps this physical checkout at a stable path,
    preserving its editable source binding while restoring each case's data.

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
    workspace = u.Tests.workspace_spec(
        repository,
        project=u.Tests.project_spec(root.name),
    )
    conform_request = u.Tests.conform_request(
        root,
        what=c.Infra.CodegenConformSurface.MAKEFILE,
    )
    plan = tm.ok(
        FlextInfraCodegenConform(
            repository_root=root,
            initial_workspace=workspace,
            request=conform_request,
        ).plan(conform_request),
    )
    makefile = next(
        item for item in plan.files if item.path.name == c.Infra.MAKEFILE_FILENAME
    )
    tm.ok(
        u.Cli.atomic_write_text_file(
            root / c.Infra.MAKEFILE_FILENAME,
            u.Tests.codegen_file_text(makefile),
        ),
    )
    tm.ok(
        infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=root, apply=True),
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
    tm.that(environment.is_symlink(), eq=False)
    tm.that((environment / "pyvenv.cfg").is_file(), eq=True)
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
        FlextInfraWorkspaceEnvironmentProvenance.editable_members(root),
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
    tm.that("pre-fmt:" in content, eq=False)
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
    git_environment: t.StrMapping,
) -> None:
    """Resolve one generated consumer through ``make upg`` once per run.

    The upgrade runs under a foreign uv environment with a declared post-upg
    hook, and a checkout of the resolved result installs every locked tool
    into cold CI storage; both receipts are what the consumers assert.
    """
    parent = _run_scoped(run_root, "make-templates", profile.value)
    # Git inputs remain immutable file-only mirrors. Native registry wheels,
    # build requirements and cold Mise artifacts still require provisioning.
    git_environment = {**git_environment, "UV_OFFLINE": "0"}
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
                make.uv_resolution.hosted_variable: make.uv_resolution.hosted_value,
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
                make.uv_resolution.hosted_variable: make.uv_resolution.hosted_value,
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
    git_environment: t.StrMapping | None = None,
) -> None:
    """Provision only a consumed fixture under the canonical filesystem lease.

    Testmon inventory and selection collect tests without network or writes.
    Provisioning belongs to the item that actually consumes the checkout, so
    its cost and failure remain visible to the test deadline and report.

    Raises:
        ValueError: If a Make profile is requested without its Git environment.

    """
    parent.mkdir(parents=True, exist_ok=True)
    with u.Infra.codegen_transaction_lease(parent / receipt):
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
def hermetic_git_environment(session_runtime: p.Tests.SessionRuntime) -> t.StrMapping:
    """Serve the fixture provider's Git sources from this run's local mirrors.

    The mirrors are built once per locked-source set under the canonical
    filesystem lease from objects this checkout already holds; the directory is
    keyed by that set, so a relock never reuses mirrors of superseded commits.
    The returned environment routes the provider to them and makes any network
    transport fail.

    Returns:
        The resulting ``t.StrMapping``.

    """
    sources = "\n".join(
        "@".join(source) for source in u.Tests.locked_git_sources(_PROJECT_ROOT)
    )
    parent = _run_scoped(
        session_runtime.directory,
        "git-mirrors",
        hashlib.sha256(sources.encode()).hexdigest()[:16],
    )
    parent.mkdir(parents=True, exist_ok=True)
    receipt = parent / _GIT_MIRRORS_RECEIPT
    mirrors = parent / "mirrors"
    with u.Infra.codegen_transaction_lease(receipt):
        if not receipt.is_file():
            mirrored = u.Tests.build_git_mirrors(_PROJECT_ROOT, mirrors)
            tm.ok(u.Cli.atomic_write_text_file(receipt, "\n".join(mirrored) + "\n"))
    return u.Tests.hermetic_git_environment(mirrors)


@pytest.fixture(scope="session", params=tuple(c.Infra.MakeProfile))
def generated_make_template(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
) -> t.Pair[c.Infra.MakeProfile, Path]:
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
    hermetic_git_environment: t.StrMapping,
) -> t.MappingKV[c.Infra.MakeProfile, Path]:
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
) -> t.Pair[str, Path]:
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
    tm.that((u.Infra.runtime_environment_dir(root) / "pyvenv.cfg").is_file(), eq=True)
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
        (root / "limits.toml").write_text(
            "[typing_libraries]\nexclude = []\n", encoding="utf-8"
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


@pytest.fixture
def real_toml_project(tmp_path: Path) -> Path:
    """Create a real project with valid pyproject.toml.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    pyproject_content = """\
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
authors = [{name = "Test", email = "test@example.com"}]
"""
    (project_root / "pyproject.toml").write_text(pyproject_content)
    return project_root


@pytest.fixture
def real_makefile_project(tmp_path: Path) -> Path:
    """Create a real project with valid Makefile.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "makefile_project"
    project_root.mkdir()
    makefile_content = """\
.PHONY: help setup check test

help:
\t@echo "Available targets"

setup:
\t@echo "Setting up"

check:
\t@echo "Checking"

test:
\t@echo "Testing"
"""
    (project_root / "Makefile").write_text(makefile_content)
    return project_root


@pytest.fixture
def real_python_package(tmp_path: Path) -> Path:
    """Create a real Python package with src layout.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "python_package"
    project_root.mkdir()
    src_dir = project_root / "src" / "test_pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Test package."""\n__version__ = "0.1.0"\n')
    (src_dir / "identity.py").write_text(
        '"""Substantive unique source consumed by real scanner fixtures."""\n\n'
        "def normalize_identity(parts: tuple[str, ...]) -> str:\n"
        '    """Normalize one ordered identity without duplicated code."""\n'
        "    normalized = tuple(part.strip() for part in parts if part.strip())\n"
        "    if not normalized:\n"
        '        raise ValueError("identity requires at least one non-empty part")\n'
        '    return "::".join(normalized).casefold()\n',
        encoding="utf-8",
    )
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "test-pkg"\nversion = "0.1.0"\n',
    )
    return project_root


@pytest.fixture
def cached_runner_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a real one-test consumer for the public cached pytest runner.

    Returns:
        The resulting ``Path``.

    """
    external_cache = tmp_path / "external-cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(external_cache))
    monkeypatch.setenv("LOCALAPPDATA", str(external_cache))
    project_root = tmp_path / "cached_runner_project"
    policy = config.Infra.codegen.make.testmon_cache
    package_root = project_root / c.Infra.DEFAULT_SRC_DIR / "runner_sample"
    tests_root = project_root / policy.target_directory
    package_root.mkdir(parents=True)
    tests_root.mkdir(parents=True)
    # A faithful consumer project carries the fleet-standard coverage
    # boundary: the Cython provider mapping of dependency_injector is not
    # parseable source and is omitted by every fleet coverage config.
    tm.ok(
        u.Cli.toml_write_mapping(
            project_root / c.PYPROJECT_FILENAME,
            {
                "tool": {
                    "coverage": {
                        "run": {"omit": ["*/dependency_injector/providers.pyx"]},
                    },
                    "pytest": {
                        "ini_options": {
                            "pythonpath": [c.Infra.DEFAULT_SRC_DIR],
                            "markers": list(
                                config.Infra.tooling.tools.pytest.standard_markers,
                            ),
                        },
                    },
                },
            },
        ),
    )
    (package_root / "__init__.py").write_text(
        "def answer() -> int:\n    return 42\n",
        encoding="utf-8",
    )
    # The runner contract is proven through process evidence (exit codes,
    # manifests, accounting), not through the child's assertion library. The
    # consumer's suite stays on plain asserts: every nested runner lifecycle
    # imports the child suite, and the shared assertion facade drags the full
    # infrastructure model materialization into each of those interpreters.
    (tests_root / "test_runtime.py").write_text(
        "from runner_sample import answer\n\n"
        "def test_runtime() -> None:\n"
        "    assert answer() == 42\n",
        encoding="utf-8",
    )
    return project_root


@pytest.fixture
def policy_violation_project(tmp_path: Path) -> Path:
    """Create a real consumer whose suite violates the slow-timeout policy.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "policy_violation_project"
    policy = config.Infra.codegen.make.testmon_cache
    tests_root = project_root / policy.target_directory
    tests_root.mkdir(parents=True)
    # The ini value is an arbitrary non-production budget owned by this probe.
    (project_root / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\nflext_slow_timeout_seconds = "30"\n',
        encoding="utf-8",
    )
    (tests_root / "test_policy.py").write_text(
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.mark.timeout(1)\n"
        "def test_breaks_policy() -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )
    return project_root


@pytest.fixture
def mod_workspace(installed_dependency_path: Path) -> Path:
    """Create the shared real workspace for the public refactor-mod CLI.

    Returns:
        The resulting ``Path``.

    """
    project_document = u.read_project_document_cached(_PROJECT_ROOT)
    project = u.build_project_metadata(_PROJECT_ROOT, project_document)
    workspace = installed_dependency_path / "mod_workspace"
    author_name = tm.ok(u.Cli.json_dumps(project.project.authors[0].name))
    license_id = tm.ok(
        u.Cli.json_dumps(
            u.Cli.json_walk_path(
                u.Infra.pyproject_payload(_PROJECT_ROOT / c.PYPROJECT_FILENAME),
                (c.Infra.PROJECT, c.Infra.LICENSE),
            ),
        ),
    )
    tm.ok(u.Cli.ensure_dir(workspace))
    metadata = (
        installed_dependency_path
        / f"{workspace.name}-{project.project.version}.dist-info"
    )
    tm.ok(u.Cli.ensure_dir(metadata))
    tm.ok(
        u.Cli.atomic_write_text_file(
            metadata / "METADATA",
            f"Metadata-Version: 2.1\nName: {workspace.name.replace('_', '-')}\n"
            f"Version: {project.project.version}\n",
        )
    )
    tm.ok(
        u.Cli.atomic_write_text_file(
            workspace / c.PYPROJECT_FILENAME,
            (
                "[project]\n"
                f'name = "{workspace.name.replace("_", "-")}"\n'
                f'version = "{project.project.version}"\n'
                f"authors = [{{name = {author_name}}}]\n"
                f"license = {license_id}\n"
                f"{c.Infra.DEPENDENCIES} = []\n"
            ),
        ),
    )
    # A declared distribution owns a package: resolving the package name from
    # `[project].name` alone is impossible for a `flext-` distribution, so a
    # fixture without `src/<pkg>/` is not the project it claims to be. The
    # package follows the fixture's own declared name: naming it after the
    # real project would shadow the installed flext_infra for Rope, and every
    # packaged campaign binding (flext_infra.c / .t) would lose its owner.
    package_dir = workspace / c.Infra.DEFAULT_SRC_DIR / workspace.name
    tm.ok(u.Cli.ensure_dir(package_dir))
    tm.ok(
        u.Cli.atomic_write_text_file(
            package_dir / c.Infra.INIT_PY,
            '"""Public refactor-mod fixture package."""\n\n'
            "from __future__ import annotations\n",
        ),
    )
    tm.ok(
        u.Cli.atomic_write_text_file(
            workspace / "sample.py",
            # The fixture owns every name it uses and carries exactly one
            # defect: the governance rule the tests exercise. Undefined names
            # or an unresolvable import would make the diagnostic gates red for
            # a reason unrelated to the rule, and mod's own contract is that
            # the tree is clean before and after.
            (
                '"""Public refactor-mod fixture module with one governance defect."""\n'
                "\n"
                "from __future__ import annotations\n"
                "\n"
                "from flext_core import t\n"
                "\n"
                "class _FixtureInfra:\n"
                '    """Stand-in infra namespace owning every name'
                ' the fixture uses."""\n'
                "\n"
                "    @staticmethod\n"
                "    def serialization_lock_execute(\n"
                "        paths: tuple[str, ...], timeout: float\n"
                "    ) -> None:\n"
                '        """Accept the governed call shape without any effect."""\n'
                "\n"
                "\n"
                "class _FixtureFacade:\n"
                '    """Stand-in utilities facade exposing the infra namespace."""\n'
                "\n"
                "    Infra = _FixtureInfra\n"
                "\n"
                "\n"
                "u = _FixtureFacade()\n"
                "paths: tuple[str, ...] = ()\n"
                "timeout: float = 1.0\n"
                "\n"
                "u.Infra.serialization_lock_execute(paths, timeout)\n"
            ),
        ),
    )
    u.Tests.initialize_git_repo(workspace)
    return workspace


@pytest.fixture
def real_workspace(tmp_path: Path) -> Path:
    """Create a real multi-project workspace.

    Returns:
        The resulting ``Path``.

    """
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    (repository_root / "Makefile").write_text(
        ".PHONY: help\nhelp:\n\t@echo 'Workspace'\n",
    )
    (repository_root / "pyproject.toml").write_text(
        '[project]\nname = "workspace"\nversion = "0.1.0"\n',
    )
    for i in range(1, 4):
        project_dir = repository_root / f"project_{i}"
        project_dir.mkdir()
        (project_dir / "pyproject.toml").write_text(
            f'[project]\nname = "project-{i}"\nversion = "0.1.0"\n',
        )
        src_dir = project_dir / "src" / f"project_{i}"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text(f'"""Project {i}."""\n')
    return repository_root


@pytest.fixture
def modernizer_workspace(tmp_path: Path) -> Path:
    """Provide ``modernizer_workspace``.

    Returns:
        The resulting ``Path``.

    """
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    # The governed tree above the workspace carries the committed Mise
    # declaration and lock that activate its locked tools.
    u.Tests.copy_tracked_mise_seeds(tmp_path)
    (workspace / c.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject(),
        encoding="utf-8",
    )
    u.Tests.write_beads_project(
        workspace,
        workspace="workspace",
        database="workspace",
        issue_prefix="workspace",
    )
    _write_modernizer_codegen_config(workspace)
    return workspace


@pytest.fixture
def modernizer_workspace_with_projects(modernizer_workspace: Path) -> Path:
    """Provide ``modernizer_workspace_with_projects``.

    Returns:
        The resulting ``Path``.

    """
    (modernizer_workspace / c.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject("selected", "ignored"),
        encoding="utf-8",
    )
    selected = u.Tests.mk_project(
        modernizer_workspace,
        "selected",
        pyproject=_modernizer_pyproject("selected"),
    )
    ignored = u.Tests.mk_project(
        modernizer_workspace,
        "ignored",
        pyproject=_modernizer_pyproject("ignored"),
    )
    for project in (selected, ignored):
        u.Tests.write_beads_project(
            project,
            workspace="workspace",
            database=project.name,
            issue_prefix=project.name,
        )
    (modernizer_workspace / ".gitmodules").write_text(
        '[submodule "selected"]\n\tpath = selected\n'
        "\turl = https://github.com/flext-sh/selected.git\n"
        '[submodule "ignored"]\n\tpath = ignored\n'
        "\turl = https://github.com/flext-sh/ignored.git\n",
        encoding="utf-8",
    )
    # FLEXT: public modernizer commands fail loud outside a real Git workspace.
    u.Tests.initialize_git_repo(modernizer_workspace)
    return modernizer_workspace


@pytest.fixture
def real_docs_project(tmp_path: Path) -> Path:
    """Create a real project with documentation.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "docs_project"
    project_root.mkdir()
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("# Documentation\n")
    (docs_dir / "index.md").write_text("# Index\n")
    (project_root / "README.md").write_text("# Project\n")
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "docs-project"\nversion = "0.1.0"\n',
    )
    return project_root


@pytest.fixture
def semantic_rope_workspace(tmp_path: Path) -> t.Pair[t.Infra.RopeProject, Path]:
    """Create a real rope workspace with semantic-analysis fixtures.

    Returns:
        The resulting ``t.Pair[t.Infra.RopeProject, Path]``.

    """
    repository_root = tmp_path / "rope_workspace"
    package_root = repository_root / "src" / "rope_demo"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "models.py").write_text(
        "from pathlib import Path\n\n"
        "class Animal:\n"
        "    pass\n\n"
        "class Dog(Animal):\n"
        "    home = Path('kennel')\n\n"
        "    @staticmethod\n"
        "    def fetch() -> str:\n"
        "        return 'ball'\n\n"
        "    @classmethod\n"
        "    def breed(cls) -> str:\n"
        "        return cls.__name__\n\n"
        "    def _wag(self) -> str:\n"
        "        return 'wag'\n",
        encoding="utf-8",
    )
    (package_root / "services.py").write_text(
        "from rope_demo.models import Dog\n\n"
        "class Kennel:\n"
        "    def adopt(self) -> Dog:\n"
        "        return Dog()\n",
        encoding="utf-8",
    )

    rope_project = u.Infra.init_rope_project(repository_root)
    return rope_project, repository_root


@pytest.fixture
def models_resource(
    semantic_rope_workspace: t.Pair[t.Infra.RopeProject, Path],
) -> t.Infra.RopeFile:
    """Return the Rope resource for the semantic models fixture module.

    Returns:
        The Rope resource for the semantic models fixture module.

    """
    rope_project, repository_root = semantic_rope_workspace
    resource = u.Infra.resolve_resource_from_path(
        rope_project,
        repository_root / "src" / "rope_demo" / "models.py",
    )
    return tm.not_none(resource)


@pytest.fixture
def services_resource(
    semantic_rope_workspace: t.Pair[t.Infra.RopeProject, Path],
) -> t.Infra.RopeFile:
    """Return the Rope resource for the semantic services fixture module.

    Returns:
        The Rope resource for the semantic services fixture module.

    """
    rope_project, repository_root = semantic_rope_workspace
    resource = u.Infra.resolve_resource_from_path(
        rope_project,
        repository_root / "src" / "rope_demo" / "services.py",
    )
    return tm.not_none(resource)
