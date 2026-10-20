"""Public generated config lifecycle contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
from pathlib import Path

import pytest
from jinja2 import Template

from flext_infra import config, infra, settings
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.gates import FlextInfraRuffFormatGate, FlextInfraRuffLintGate
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from tests import c, m, tm, u
from tests.unit.codegen import test_codegen_ci_matrix
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport

pytestmark = pytest.mark.slow


class TestsFlextInfraCodegenConfigLifecycle:
    """Exercise the generated public config rather than inspect source spelling."""

    @staticmethod
    def test_check_consumes_completed_generation_without_rendering(
        infra_git_repo: Path,
    ) -> None:
        """Apply and no-op publication both support a read-only public observation."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.ENVRC,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        generation = cProfile.Profile()
        result = tm.ok(generation.runcall(infra.codegen_conform, request))
        tm.that(
            any(
                entry.code is Template.render.__code__
                for entry in generation.getstats()
            ),
            eq=True,
        )
        tm.that(result.plan is not None, eq=True)
        if result.plan is None:
            pytest.fail("generation did not return its actual plan")
        destinations = tuple(file.path for file in result.plan.files)
        no_op = tm.ok(infra.codegen_conform(request))
        tm.that(no_op.written_files, eq=())
        paths = (
            *destinations,
            root
            / FlextInfraMiseArtifactsVerification.publication_receipt(
                c.Infra.CodegenConformSurface.ENVRC,
            ),
        )
        before = tuple(
            tm.ok(FlextInfraMiseArtifactsFiles.read_state(path, required=True))
            for path in paths
        )
        observation = cProfile.Profile()
        checked = tm.ok(
            observation.runcall(
                infra.codegen_conform,
                request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
            ),
        )
        tm.that(checked.plan, eq=None)
        tm.that(checked.verified_publication is not None, eq=True)
        tm.that(checked.written_files, eq=())
        tm.that(
            any(
                entry.code is Template.render.__code__
                for entry in observation.getstats()
            ),
            eq=False,
        )
        after = tuple(
            tm.ok(FlextInfraMiseArtifactsFiles.read_state(path, required=True))
            for path in paths
        )
        tm.that(after, eq=before)

    @staticmethod
    def test_generated_config_keeps_settings_independent(
        installed_artifact_consumer: Path,
    ) -> None:
        """The real generated package loads typed YAML and freezes only config."""
        root = test_codegen_ci_matrix.TestsFlextInfraCodegenCiMatrix.render_project(
            installed_artifact_consumer,
        )
        test_paths = tuple(
            sorted({
                path
                for directory in config.Infra.tooling.tools.pytest.test_paths
                for pattern in config.Infra.tooling.tools.pytest.python_files
                for path in (root / directory).rglob(pattern)
                if path.is_file()
            }),
        )
        tm.that(
            bool(test_paths),
            eq=True,
            msg="The generated project must own executable Python tests",
        )
        for path in test_paths:
            state = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            tm.ok(
                u.Cli.atomic_write_binary_file_guarded(
                    state,
                    tm.not_none(state.content)
                    + b"\n# Authored test changes survive managed generation.\n",
                    permission_mode=tm.not_none(state.mode),
                ),
            )
        retained_tests = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in test_paths
        )
        for verb in ("upg", "setup", "build"):
            output = tm.ok(
                u.Tests.run_isolated_make(
                    [verb],
                    cwd=root,
                    env={
                        "GITHUB_TOKEN": settings.env_required("GITHUB_TOKEN"),
                        config.Infra.codegen.make.ci.variable: (
                            "" if verb == "upg" else config.Infra.codegen.make.ci.value
                        ),
                        config.Infra.codegen.make.uv_resolution.hosted_variable: (
                            ""
                            if verb == "upg"
                            else config.Infra.codegen.make.uv_resolution.hosted_value
                        ),
                    },
                ),
            )
            tm.that(
                u.Cli.process_succeeded(output.outcome),
                eq=True,
                msg=output.stdout + output.stderr,
            )
            if verb == "upg":
                u.Tests.commit_git_changes(
                    root,
                    "resolve the generated consumer declarations and locks",
                )
        script = """
import os
import sys
from importlib.metadata import distribution
from importlib.resources import files
from pathlib import Path
from typing import get_protocol_members, get_type_hints, is_protocol

from flext_cli import FlextCliConfig, u
from flext_core import c
from flext_demo import FlextDemo, FlextDemoConfig, config, m, p, settings

assert FlextDemoConfig.fetch_global() is config
assert FlextCliConfig.fetch_global() is not config
assert type(settings).fetch_global() is settings
for port, namespace, singleton in (
    (p.Demo.Config, p.Demo.ConfigNamespace, config),
    (p.Demo.Settings, p.Demo.SettingsNamespace, settings),
):
    assert get_type_hints(port, localns={"p": p})["Demo"] is namespace
    assert is_protocol(namespace)
    assert get_protocol_members(namespace) == set(type(singleton.Demo).model_fields)
    assert isinstance(singleton.Demo, namespace)
assert Path(str(files("flext_demo"))).resolve().is_relative_to(
    Path(sys.prefix).resolve(),
)
source = u.Cli.yaml_safe_load(Path(str(files("flext_demo") / "config/Demo.yaml")))
assert source.success, source.error
assert config.Demo.model_dump() == source.value["Demo"]
before = config.model_dump()
try:
    config.Demo = config.Demo
except m.ValidationError as error:
    assert all(item["type"] == "frozen_instance" for item in error.errors())
else:
    raise AssertionError("Generated config is mutable")
adjusted = settings.clone(debug=not settings.debug)
assert adjusted.debug != settings.debug
assert config.model_dump() == before
isolated_settings = settings.clone(Demo={"enabled": not settings.Demo.enabled})
for runtime in (settings, isolated_settings):
    service = FlextDemo(
        configuration=config,
        runtime_options=runtime,
        runtime_settings=runtime,
    )
    assert service.settings is runtime
    result = service.ping(m.Demo.PingInput())
    tm.ok(result.success), result.error
    expected = (
        config.Demo.ping_reply if runtime.Demo.enabled else config.Demo.disabled_reply
    )
    assert result.value.message == expected
assert settings.Demo.enabled != isolated_settings.Demo.enabled
try:
    FlextDemo()
except m.ValidationError as error:
    assert all(item["type"] == "missing" for item in error.errors())
else:
    raise AssertionError("Generated service accepts missing dependency ports")
message = f"  {config.Demo.ping_reply}\\n"
reply = m.Demo.PingResult(message=message)
assert reply.message == message
for schema, payload in (
    (m.Demo.ConfigNamespace, config.Demo.model_dump()),
    (m.Demo.SettingsNamespace, settings.Demo.model_dump()),
    (m.Demo.PingInput, {}),
    (m.Demo.PingResult, {"message": message}),
):
    value = schema.model_validate(payload)
    assert schema.model_validate_json(value.model_dump_json()) == value
    try:
        schema.model_validate({**payload, "__unexpected__": True})
    except m.ValidationError as error:
        assert all(item["type"] == "extra_forbidden" for item in error.errors())
    else:
        raise AssertionError(f"Generated schema accepts undeclared input: {schema}")
for schema, payload, error_type in (
    (m.Demo.PingResult, {"message": message.encode()}, "string_type"),
    (m.Demo.SettingsNamespace, {"enabled": "false"}, "bool_type"),
):
    try:
        schema.model_validate(payload)
    except m.ValidationError as error:
        assert all(item["type"] == error_type for item in error.errors())
    else:
        raise AssertionError(
            f"Generated schema coerces an incompatible input: {schema}"
        )
enabled = not settings.Demo.enabled
prefix = type(settings).model_config["env_prefix"]
namespace_key = f"{prefix}Demo"
environment_key = (
    f"{namespace_key}{type(settings).model_config['env_nested_delimiter']}enabled"
)
normalize = str if type(settings).model_config["case_sensitive"] else str.casefold
namespace_inputs = tuple(
    key for key in os.environ
    if normalize(key) == normalize(namespace_key)
    or normalize(key).startswith(
        normalize(
            f"{namespace_key}{type(settings).model_config['env_nested_delimiter']}"
        ),
    )
)
native = u.Cli.run_raw(
    [
        sys.executable, "-c",
        "from flext_demo import settings; "
        f"assert settings.Demo.enabled is {enabled!r}",
    ],
    cwd=Path.cwd(),
    options=m.Cli.ProcessOptions(
        env={environment_key: str(enabled).lower()},
        remove_env_keys=tuple(
            key for key in namespace_inputs if key != environment_key
        ),
    ),
)
assert native.success, native.error
assert u.Cli.process_succeeded(native.value.outcome), native.value.stderr
runtime_root = Path.cwd() / "settings-runtime"
runtime_root.mkdir()
(runtime_root / c.ENV_FILE_DEFAULT).write_text(
    f"{environment_key}={str(enabled).lower()}\\n", encoding="utf-8",
)
selected_env_file = Path.cwd() / f"{c.ENV_FILE_DEFAULT}.selected"
selected_env_file.write_text(
    f"{environment_key}={str(settings.Demo.enabled).lower()}\\n", encoding="utf-8",
)
for expected, overrides, removed in (
    (enabled, {}, (*namespace_inputs, c.ENV_FILE_ENV_VAR)),
    (
        settings.Demo.enabled,
        {c.ENV_FILE_ENV_VAR: str(selected_env_file)},
        namespace_inputs,
    ),
):
    observed = u.Cli.run_raw(
        [
            sys.executable, "-c",
            "from flext_demo import settings; "
            f"assert settings.Demo.enabled is {expected!r}",
        ],
        cwd=runtime_root,
        options=m.Cli.ProcessOptions(env=overrides, remove_env_keys=removed),
    )
    assert observed.success, observed.error
    assert u.Cli.process_succeeded(observed.value.outcome), observed.value.stderr
entry = next(
    item for item in distribution(config.Demo.name).entry_points
    if item.group == "console_scripts" and item.name == config.Demo.name
)
expected_reply = (
    config.Demo.ping_reply if settings.Demo.enabled else config.Demo.disabled_reply
)
for argv in (
    [sys.executable, "-m", "flext_demo", config.Demo.ping_command_name],
    [str(Path(sys.executable).parent / entry.name), config.Demo.ping_command_name],
):
    called = u.Cli.run_raw(argv, cwd=Path.cwd())
    assert called.success, called.error
    assert u.Cli.process_succeeded(called.value.outcome), called.value.stderr
    assert expected_reply in called.value.stdout
print(
    "generated config: frozen YAML, subclass identity, "
    "independent settings, typed payloads, native CLI entrypoints"
)
"""
        process = tm.ok(
            u.Cli.run_raw(
                [str(u.Infra.runtime_python(root)), "-c", script],
                cwd=root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        tm.that(process.stdout, has="generated config: frozen YAML")
        for verb in ("gen", "check", "test-full"):
            output = tm.ok(
                u.Tests.run_isolated_make(
                    [verb],
                    cwd=root,
                    env={
                        "GITHUB_TOKEN": settings.env_required("GITHUB_TOKEN"),
                        config.Infra.codegen.make.ci.variable: (
                            config.Infra.codegen.make.ci.value if verb == "gen" else ""
                        ),
                        config.Infra.codegen.make.uv_resolution.hosted_variable: (
                            config.Infra.codegen.make.uv_resolution.hosted_value
                        ),
                    },
                ),
            )
            tm.that(
                u.Cli.process_succeeded(output.outcome),
                eq=True,
                msg=output.stdout + output.stderr,
            )
            tm.ok(u.Cli.atomic_verify_binary_file_states(retained_tests))

    @staticmethod
    def test_initializer_no_op_publishes_observable_request_proof(
        installed_artifact_consumer: Path,
    ) -> None:
        """First publication is policy-clean and repeated APPLY retains its proof."""
        root, package = u.Tests.create_lazy_init_workspace(installed_artifact_consumer)
        u.Tests.WorktreeFixture.attach_submodule(
            installed_artifact_consumer,
            root,
            distribution=root.name,
            relative_path=str(root.relative_to(installed_artifact_consumer)),
        )
        metadata = root / c.PYPROJECT_FILENAME
        document = tm.not_none(
            u.Cli.toml_parse_text(metadata.read_text(encoding=c.DEFAULT_ENCODING)),
        )
        document["tool"] = {
            "ruff": {
                "indent-width": 2,
                "format": {"quote-style": "single"},
                "lint": {"select": ["F", "I"]},
            },
        }
        metadata.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
        authored_module = package / "authored.py"
        owner = u.Infra.project_prefix(authored_module) + "Authored"
        notice = u.Infra.copyright_notice(package, module=authored_module)
        authored_module.write_text(
            '"""Authored module retained by initializer publication.\n\n'
            f'{notice}\n"""\n\n\n'
            f"class {owner}:\n"
            '  """Public authored declaration."""\n\n\n'
            f"__all__: list[str] = ['{owner}']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        authored = (
            tm.ok(u.Cli.atomic_read_binary_file_state(authored_module, required=True)),
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        first = tm.ok(infra.codegen_conform(request))
        plan = tm.not_none(first.plan)
        tm.that(bool(first.written_files), eq=True)
        for file in plan.files:
            tm.that(file.path.read_bytes(), eq=file.desired_content)
        context = m.Infra.GateContext(repository_root=root, reports_dir=root)
        for gate in (FlextInfraRuffLintGate(root), FlextInfraRuffFormatGate(root)):
            checked = gate.check_files(
                tuple(file.path for file in plan.files),
                root,
                context,
            )
            tm.that(checked.result.passed, eq=True, msg=checked.raw_output)
        tm.ok(u.Cli.atomic_verify_binary_file_states(authored))
        tm.that(tm.ok(infra.codegen_conform(request)).written_files, eq=())
        tm.ok(u.Cli.atomic_verify_binary_file_states(authored))
        report = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.LAZY_INIT,
        )
        before = tm.ok(FlextInfraMiseArtifactsFiles.read_state(report, required=True))
        checked = tm.ok(
            infra.codegen_conform(
                request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
            ),
        )
        tm.that(checked.verified_publication is not None, eq=True)
        tm.that(checked.written_files, eq=())
        tm.that(
            tm.ok(FlextInfraMiseArtifactsFiles.read_state(report, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.parametrize("target_exists", [False, True])
    def test_directed_initializer_rejects_banned_import_before_publication(
        tmp_path: Path,
        *,
        target_exists: bool,
    ) -> None:
        """Native unrepairable diagnostics leave target bytes or absence unchanged."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = root / c.PYPROJECT_FILENAME
        document = tm.not_none(
            u.Cli.toml_parse_text(metadata.read_text(encoding=c.DEFAULT_ENCODING)),
        )
        wheel = u.Cli.toml_ensure_path(
            document,
            ("tool", "hatch", "build", "targets", "wheel"),
        )
        wheel["packages"] = [package.relative_to(root).as_posix()]
        ruff = u.Cli.toml_ensure_path(document, ("tool", "ruff"))
        ruff["lint"] = {
            "select": ["F", "I", "TID251"],
            "flake8-tidy-imports": {
                "banned-api": {
                    "types.MappingProxyType": {
                        "msg": "Fixture rejects the template's immutable mapping API",
                    },
                },
            },
        }
        metadata.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
        destination = package / c.Infra.INIT_PY
        u.Tests.write_lazy_init_namespace_module(
            package / "constants.py",
            class_name=u.Infra.project_prefix(destination) + "Constants",
            alias="c",
        )
        if not target_exists:
            destination.unlink()
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(destination, required=False),
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        rejected = infra.codegen_conform(request)
        tm.that(rejected.failure, eq=True)
        tm.that(str(rejected.error), has="TID251")
        tm.that(str(rejected.error), has="MappingProxyType")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False)),
            eq=before,
        )

    @staticmethod
    def test_installed_git_artifact_retains_complete_declaration(
        installed_artifact_consumer: Path,
    ) -> None:
        """Read the native Git artifact and reject bytes outside its wheel RECORD."""
        root = installed_artifact_consumer
        repository = tm.ok(
            u.Infra.configured_repository_ref(
                codegen=config.Infra.codegen,
                repository_root=root,
            ),
        )
        state = tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                root,
                repository,
            ),
        )
        tm.that(
            state.path.is_relative_to(u.Infra.runtime_environment_dir(root)),
            eq=True,
        )
        script = """
import sys
from pathlib import Path

from flext_infra import c, config, u
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)

root = Path(sys.argv[1])
context = FlextInfraWorkspaceDetector.resolution_context(root).unwrap()
lock_state = u.Cli.atomic_read_binary_file_state(
    context.lock_path, required=True,
).unwrap()
assert lock_state.mode is not None
obsolete = root / c.Infra.UV_LOCK_FILENAME
if obsolete != context.lock_path:
    obsolete_state = u.Cli.atomic_read_binary_file_state(
        obsolete, required=False,
    ).unwrap()
    u.Cli.atomic_write_binary_file_guarded(
        obsolete_state,
        b"obsolete root lock must not be parsed\\n",
        permission_mode=lock_state.mode,
    ).unwrap()
repository = u.Infra.configured_repository_ref(
    codegen=config.Infra.codegen,
    repository_root=root,
).unwrap()
state = FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
    root, repository
).unwrap()
explicit = FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
    root, repository, lock_state=lock_state,
).unwrap()
assert explicit == state
if obsolete != context.lock_path:
    foreign_lock = lock_state.model_copy(update={"path": obsolete})
    refused = FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
        root, repository, lock_state=foreign_lock,
    )
    assert refused.failure
    assert "captured elected lock" in refused.error
assert u.Cli.atomic_read_binary_file_state(
    context.lock_path, required=True,
).unwrap() == lock_state
print("installed declaration elected-lock=" + str(context.lock_path))
assert state.path.is_relative_to(Path(sys.prefix))
metadata, requirements = u.Infra.member_declaration_requirements(
    state,
    repository.distribution,
).unwrap()
assert state.content is not None
document = u.Cli.toml_parse_text(state.content.decode(c.DEFAULT_ENCODING))
assert document is not None
payload = u.Cli.toml_as_mapping(document)
assert payload is not None
project = payload["project"]
assert metadata.dependencies == tuple(project.get("dependencies", ()))
assert metadata.optional_dependencies == {
    name: tuple(entries)
    for name, entries in project.get("optional-dependencies", {}).items()
}
assert {
    name: [
        entry if isinstance(entry, str) else entry.model_dump(by_alias=True)
        for entry in entries
    ]
    for name, entries in metadata.dependency_groups.items()
} == payload.get("dependency-groups", {})
assert tuple(requirements) == tuple(
    u.Infra.document_requirement_lines(document).unwrap()
)
assert state.mode is not None
u.Cli.atomic_write_binary_file_guarded(
    state,
    state.content + b"\\n",
    permission_mode=state.mode,
).unwrap()
changed = FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
    root, repository
)
assert changed.failure
assert "RECORD" in changed.error
print("installed Git declaration: complete groups, extras and RECORD authentication")
"""
        output = tm.ok(
            u.Cli.run_raw(
                [str(u.Infra.runtime_python(root)), "-c", script, str(root)],
                cwd=root,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(output.outcome),
            eq=True,
            msg=output.stdout + output.stderr,
        )
        tm.that(output.stdout, has="installed Git declaration: complete groups")
        tm.fail(
            FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                root,
                repository,
            ),
            has="RECORD",
        )
