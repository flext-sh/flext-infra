"""Public contract for the generated codegen configuration schema.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config, m, p, u
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsCodegenConfigSchema:
    """Prove one typed owner for the whole codegen YAML document."""

    # NOTE (multi-agent, mro-wkii.17.26.2.7 / agent: codex): these tests use
    # only public config/schema facades and the canonical conformance owner.
    def test_whole_document_validates_and_matches_singleton(self) -> None:
        """Validate the complete YAML file into the canonical typed object."""
        config_path = u.Infra.resource_root("config") / "codegen.yaml"
        schema_path = (
            u.Infra.resource_root("schemas")
            / Path(config.Infra.codegen_schema.path).name
        )

        loaded = u.Cli.config_load(
            config_path, schema_path=schema_path, expand_env=False
        )

        tm.ok(loaded)
        document = m.Infra.CodegenConfigDocumentSpec.model_validate(
            loaded.unwrap().data
        )
        tm.that(document.Infra.codegen, eq=config.Infra.codegen)

    def test_schema_rejects_an_unknown_document_field(self, tmp_path: Path) -> None:
        """Reject undeclared data at the external document boundary."""
        config_path = u.Infra.resource_root("config") / "codegen.yaml"
        schema_path = (
            u.Infra.resource_root("schemas")
            / Path(config.Infra.codegen_schema.path).name
        )
        source = u.Cli.files_read_text(config_path)
        tm.ok(source)
        invalid_path = tmp_path / config_path.name
        tm.ok(
            u.Cli.atomic_write_text_file(
                invalid_path, f"{source.unwrap()}\nunknown_document_field: true\n"
            )
        )

        invalid = u.Cli.config_load(
            invalid_path, schema_path=schema_path, expand_env=False
        )

        tm.fail(invalid)

    def test_tracked_schema_matches_deterministic_generation(self) -> None:
        """Keep the tracked schema byte-identical to its typed owner."""
        schema_path = (
            u.Infra.resource_root("schemas")
            / Path(config.Infra.codegen_schema.path).name
        )
        stored = u.Cli.files_read_text(schema_path)
        generated = FlextInfraCodegenConform.render_config_schema()

        tm.ok(stored)
        tm.ok(generated)
        tm.that(stored.unwrap(), eq=generated.unwrap())

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "\0",
            "/absolute/schema.json",
            "../schemas/codegen.schema.json",
            "schemas/../codegen.schema.json",
            "schemas/NUL/codegen.schema.json",
            r"schemas\codegen.schema.json",
            "a" * 256,
            "a" * 4096,
        ],
    )
    def test_schema_path_rejects_unsafe_destinations(self, invalid_path: str) -> None:
        """Reject an unsafe schema destination before conform constructs a Path."""
        policy = config.Infra.codegen_schema
        with pytest.raises(m.ValidationError, match="String should match pattern"):
            _ = m.Infra.CodegenSchemaSpec(
                path=invalid_path,
                dialect=policy.dialect,
                identifier=policy.identifier,
                title=policy.title,
            )

    def test_schema_path_accepts_name_max_component(self) -> None:
        """Accept the portable filesystem component boundary of 255 bytes."""
        policy = config.Infra.codegen_schema

        validated = m.Infra.CodegenSchemaSpec(
            path="a" * 255,
            dialect=policy.dialect,
            identifier=policy.identifier,
            title=policy.title,
        )

        tm.that(validated.path, eq="a" * 255)

    def test_schema_identity_and_title_reject_invalid_values(self) -> None:
        """Reject non-HTTP identities and blank schema titles declaratively."""
        policy = config.Infra.codegen_schema
        with pytest.raises(m.ValidationError):
            _ = m.Infra.CodegenSchemaSpec(
                path=policy.path,
                dialect="not a URI",
                identifier=policy.identifier,
                title=policy.title,
            )
        with pytest.raises(m.ValidationError):
            _ = m.Infra.CodegenSchemaSpec(
                path=policy.path,
                dialect=policy.dialect,
                identifier="relative/schema.json",
                title=policy.title,
            )
        with pytest.raises(m.ValidationError, match="String should match pattern"):
            _ = m.Infra.CodegenSchemaSpec(
                path=policy.path,
                dialect=policy.dialect,
                identifier=policy.identifier,
                title="   ",
            )

    def test_transaction_policy_rejects_unsafe_process_values(self) -> None:
        """Reject invalid environment, active, tool, and command values at load."""
        policy = config.Infra.worktree_transaction
        with pytest.raises(m.ValidationError, match="String should match pattern"):
            _ = m.Infra.WorktreeTransactionSpec(
                environment_variable="INVALID=NAME",
                active_value=policy.active_value,
                root=policy.root,
                timeout_seconds=policy.timeout_seconds,
                lint_commands=policy.lint_commands,
            )
        with pytest.raises(m.ValidationError, match="String should match pattern"):
            _ = m.Infra.WorktreeTransactionSpec(
                environment_variable=policy.environment_variable,
                active_value="\0",
                root=policy.root,
                timeout_seconds=policy.timeout_seconds,
                lint_commands=policy.lint_commands,
            )
        with pytest.raises(m.ValidationError, match="String should match pattern"):
            _ = m.Infra.WorktreeTransactionLintCommandSpec(
                tool="   ", command=policy.lint_commands[0].command
            )
        with pytest.raises(m.ValidationError, match="String should match pattern"):
            _ = m.Infra.WorktreeTransactionLintCommandSpec(
                tool=policy.lint_commands[0].tool,
                command=(policy.lint_commands[0].command[0], "\0"),
            )

    def test_policy_patterns_compile_as_ecma_262_unicode(self) -> None:
        """Compile every emitted policy pattern with the JSON Schema regex engine."""
        schemas = u.Cli.json_normalize_value([
            m.Infra.CodegenSchemaSpec.model_json_schema(),
            m.Infra.WorktreeTransactionLintCommandSpec.model_json_schema(),
            m.Infra.WorktreeTransactionSpec.model_json_schema(),
        ])
        serialized = u.Cli.json_dumps(schemas)
        tm.ok(serialized)
        script = (
            "const schemas=JSON.parse(process.argv[1]);const patterns=[];"
            "const visit=(value)=>{if(Array.isArray(value)){value.forEach(visit);return;}"
            "if(value&&typeof value==='object'){Object.entries(value).forEach(([key,child])=>{"
            "if(key==='pattern')patterns.push(child);visit(child);});}};"
            "visit(schemas);if(patterns.length===0)throw new Error('no patterns');"
            "patterns.forEach((pattern)=>new RegExp(pattern,'u'));"
            "console.log(`compiled=${patterns.length}`);"
        )

        compiled = u.Cli.capture(["node", "-e", script, serialized.value])

        tm.ok(compiled)
        tm.that(compiled.value, has="compiled=")

    def test_public_apply_writes_owner_schema_and_check_is_empty(
        self, tmp_path: Path
    ) -> None:
        """Write the configured owner schema and prove the immediate fixed point."""
        source_repository = u.Cli.capture(["git", "rev-parse", "--show-toplevel"])
        tm.ok(source_repository)
        source_root = Path(source_repository.value)
        root_repository = next(
            item for item in config.Infra.codegen.repositories if item.name == "flext"
        )
        owner_repository = next(
            item
            for item in config.Infra.codegen.repositories
            if item.name == config.Infra.name
        )
        package_name = root_repository.distribution.replace("-", "_")
        class_stem = u.derive_class_stem(root_repository.name)
        namespace = class_stem.removeprefix("Flext") or class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        project_policy = config.Infra.codegen.scaffold.project
        dependency_profile = next(iter(project_policy.dependency_profiles))
        repository_page = root_repository.url.removesuffix(".git")
        workspace = m.Infra.WorkspaceSpec(
            version=1,
            name=root_repository.name,
            repository=root_repository,
            project=m.Infra.ProjectSpec(
                package_name=package_name,
                class_stem=class_stem,
                namespace=namespace,
                constant_name=root_repository.name,
                namespace_attribute=alias,
                alias=alias,
                environment_prefix=f"{package_name.upper()}_",
                description="FLEXT workspace fixture",
                version=config.Infra.version,
                license=project_policy.supported_licenses[0],
                author_name="FLEXT Team",
                author_email="team@flext.dev",
                upstream=dependency_profile.upstream,
                homepage=repository_page,
                documentation=repository_page,
                workspace_root_rel=root_repository.path.as_posix(),
                year=2026,
            ),
            members=(owner_repository,),
        )
        workspace_root = tmp_path / "workspace"
        tm.ok(
            u.Cli.yaml_dump(
                workspace_root / "config" / "workspace.yaml",
                workspace.model_dump(mode="json", exclude_none=True),
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                workspace_root / "pyproject.toml",
                f"""[project]
name = "{root_repository.distribution}"
version = "{config.Infra.version}"

[tool.uv.workspace]
members = ["{owner_repository.path.as_posix()}"]
""",
            )
        )
        tm.ok(u.Cli.run_checked([c.Infra.GIT, "init", "-q"], cwd=workspace_root))
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-q",
                    "--name",
                    config.Infra.name,
                    str(source_root),
                    owner_repository.path.as_posix(),
                ],
                cwd=workspace_root,
            )
        )
        root = workspace_root / config.Infra.name
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "user.email", "infra@example.com"], cwd=root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "config", "user.name", "Infra Fixtures"], cwd=root
            )
        )
        schema_path = root / config.Infra.codegen_schema.path
        package_schema_path = (
            root
            / c.Infra.DEFAULT_SRC_DIR
            / owner_repository.distribution.replace("-", "_")
            / config.Infra.codegen_schema.path
        )
        tm.ok(u.Cli.atomic_write_text_file(package_schema_path, '{"stale": true}\n'))
        relative_package_schema_path = package_schema_path.relative_to(root).as_posix()
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "add", "--", relative_package_schema_path], cwd=root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "commit",
                    "-q",
                    "-m",
                    "Seed committed schema drift",
                    "--",
                    relative_package_schema_path,
                ],
                cwd=root,
            )
        )
        applied = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            )
        )

        tm.ok(applied)
        schema_resource_root = schema_path.parent
        tm.that(
            applied.value.written_files.index(schema_resource_root)
            < applied.value.written_files.index(schema_path),
            eq=True,
        )
        tm.that(package_schema_path.parent.exists(), eq=False)
        stored = u.Cli.files_read_text(schema_path)
        rendered = FlextInfraCodegenConform.render_config_schema()
        tm.ok(stored)
        tm.ok(rendered)
        tm.that(stored.value, eq=rendered.value)

        checked = FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=root,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        tm.ok(checked)
        tm.that(
            tuple(file.path for file in checked.value.plan.files if file.changed), eq=()
        )
