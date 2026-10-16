"""Public generated config lifecycle contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
from pathlib import Path

import pytest
from jinja2 import Template

from flext_infra import config, infra
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsVerification,
)
from tests import c, tm, u
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
        for verb in ("build", "setup"):
            output = tm.ok(
                u.Tests.run_isolated_make(
                    [verb],
                    cwd=root,
                    env={
                        config.Infra.codegen.make.ci.variable: (
                            config.Infra.codegen.make.ci.value
                        ),
                    },
                ),
            )
            tm.that(
                u.Cli.process_succeeded(output.outcome),
                eq=True,
                msg=output.stdout + output.stderr,
            )
        script = """
import sys
from importlib.metadata import distribution
from importlib.resources import files
from pathlib import Path

from flext_cli import FlextCliConfig, u
from flext_demo import FlextDemoConfig, config, m, settings

assert FlextDemoConfig.fetch_global() is config
assert FlextCliConfig.fetch_global() is not config
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
        raise AssertionError(f"Generated schema coerces an incompatible input: {schema}")
enabled = not settings.Demo.enabled
prefix = type(settings).model_config["env_prefix"]
native = u.Cli.run_raw(
    [
        sys.executable, "-c",
        "from flext_demo import settings; "
        f"assert settings.Demo.enabled is {enabled!r}",
    ],
    cwd=Path.cwd(),
    options=m.Cli.ProcessOptions(
        env={f"{prefix}Demo__enabled": str(enabled).lower()},
    ),
)
assert native.success, native.error
assert u.Cli.process_succeeded(native.value.outcome), native.value.stderr
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

    @staticmethod
    def test_initializer_no_op_publishes_observable_request_proof(
        tmp_path: Path,
    ) -> None:
        """A settled initializer batch retains scope identity on repeated APPLY."""
        root = test_codegen_ci_matrix.TestsFlextInfraCodegenCiMatrix.render_project(
            tmp_path / "project",
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(request))
        tm.that(tm.ok(infra.codegen_conform(request)).written_files, eq=())
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
    def test_installed_git_artifact_retains_complete_declaration(
        installed_artifact_consumer: Path,
    ) -> None:
        """Read the native Git artifact and reject bytes outside its wheel RECORD."""
        root = installed_artifact_consumer
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
