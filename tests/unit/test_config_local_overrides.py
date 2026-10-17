"""Contract for a repository's own config layers over the packaged policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig
from tests import c, m, tm, u


class TestsFlextInfraConfigLocalOverrides:
    """Prove repository and local layers merge over packaged defaults."""

    @staticmethod
    def test_make_election_preserves_selection_contract() -> None:
        """Election follows capabilities, not spelling, without changing errors."""
        make = FlextInfraConfig.fetch_global().Infra.codegen.make
        profiles = tuple(c.Infra.MakeProfile)
        operation = next(verb for verb in make.verbs if not verb.arguments)
        operation = operation.model_copy(
            update={"name": f"{operation.name}-renamed", "profiles": profiles[::-1]},
        )
        for update in (
            {"arguments": ("INPUT",)},
            {"profiles": profiles[:1]},
        ):
            rejected = operation.model_copy(update=update)
            eligible = u.Infra.selector_free_make_verb(
                rejected.arguments,
                rejected.profiles,
                profiles,
            )
            tm.that(eligible, eq=False)
            payload = make.model_dump(round_trip=True)
            payload.update(
                verbs=(rejected,), violations_sweep_repair_verbs=(rejected.name,)
            )
            with pytest.raises(ValueError, match="declared selector-free verbs"):
                type(make).model_validate(payload)
        eligible = u.Infra.selector_free_make_verb(
            operation.arguments,
            operation.profiles,
            profiles,
        )
        tm.that(eligible, eq=True)
        tm.that("selector_free_verbs" in make.model_dump(), eq=False)

    @staticmethod
    def test_cache_defaults_validate_and_serialize_for_concrete_contracts() -> None:
        """Concrete cache owners preserve validated defaults and native wire values."""
        make = FlextInfraConfig.fetch_global().Infra.codegen.make
        policy = make.testmon_cache_policy
        tm.that(type(policy).model_validate_json(policy.model_dump_json()), eq=policy)
        for spec in (make.ruff_cache, make.mypy_cache):
            cache_type = type(spec)
            cache = cache_type.model_validate(
                {"external_storage_directory": spec.external_storage_directory},
            )
            tm.that(
                cache.data_home_environment_variable,
                eq=c.Infra.MypyCacheEnvironment.DATA_HOME.value,
            )
            tm.that(
                cache.user_home_environment_variable,
                eq=c.Infra.MypyCacheEnvironment.USER_HOME.value,
            )
            tm.that(type(cache.data_home_environment_variable), eq=str)
            tm.that(type(cache.user_home_environment_variable), eq=str)
            tm.that(
                cache_type.model_validate_json(cache.model_dump_json()),
                eq=cache,
            )

    @staticmethod
    def _consumer_config(root: Path) -> Path:
        """Create one consumer repository's own config directory."""
        directory = root / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir(parents=True)
        return directory

    def test_absent_repository_layers_keep_the_packaged_policy(
        self,
        tmp_path: Path,
    ) -> None:
        """A repository that declares no layer reads exactly the packaged policy.

        The expectation is the packaged SSOT read itself (P0): any legitimate
        config change keeps both reads equal, and only a broken merge diverges.
        """
        baseline = FlextInfraConfig.fetch_global()
        inputs = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        tm.that(
            inputs.spec.loc_cap.max_lines,
            eq=baseline.Infra.codegen.loc_cap.max_lines,
        )

    @staticmethod
    def test_empty_mypy_overlay_keeps_selected_global_policy(
        tmp_path: Path,
    ) -> None:
        """Empty local lists cannot remove policy supplied by the YAML owner."""
        baseline = FlextInfraConfig.fetch_global().Infra.tooling
        _, _, local = FlextInfraConfig.config_layer_paths_for_repository(
            tmp_path,
            filename="tooling.yaml",
        )
        local.parent.mkdir(parents=True)
        local.write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            "        plugins: []\n        disable-error-code: []\n",
            encoding="utf-8",
        )
        document = tm.ok(
            u.Infra.load_config_document_inputs(
                tmp_path,
                filename="tooling.yaml",
            ),
        )
        tooling = type(baseline).model_validate(
            u.Cli.json_walk_path(document.values, ("Infra", "tooling")),
        )
        tm.that(
            tuple(tooling.tools.mypy.plugins),
            eq=tuple(baseline.tools.mypy.plugins),
        )
        tm.that(
            tuple(tooling.tools.mypy.disable_error_code),
            eq=tuple(baseline.tools.mypy.disable_error_code),
        )

    @staticmethod
    def test_local_file_dict_entries_add_beside_tracked_ones(
        tmp_path: Path,
    ) -> None:
        """A dict-typed registry gains the local entry and keeps packaged ones."""
        baseline = (
            FlextInfraConfig.fetch_global().Infra.codegen.layout.project_overrides
        )
        _, _, local = FlextInfraConfig.config_layer_paths_for_repository(
            tmp_path,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        local.parent.mkdir()
        local.write_text(
            "Infra:\n"
            "  codegen:\n"
            "    layout:\n"
            "      project_overrides:\n"
            "        example-project:\n"
            "          ignore_globs:\n"
            "            - example\n",
            encoding="utf-8",
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        overrides = inputs.spec.layout.project_overrides
        tm.that("example-project" in overrides, eq=True)
        tm.that(set(overrides), eq={*baseline, "example-project"})

    @staticmethod
    def test_target_and_local_layers_use_explicit_repository_root(
        tmp_path: Path,
    ) -> None:
        """Explicit target layers merge independently of the ambient directory."""
        root = tmp_path / "consumer"
        directory = root / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir(parents=True)
        (directory / "codegen.yaml").write_text(
            "Infra:\n  codegen:\n    make:\n      docs:\n"
            "        overview_preview_limits:\n          aliases: 23\n",
            encoding="utf-8",
        )
        (directory / "codegen.local.yaml").write_text(
            "Infra:\n  codegen:\n    make:\n      docs:\n"
            "        overview_preview_limits:\n          aliases: 31\n",
            encoding="utf-8",
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        tm.that(inputs.spec.make.docs.overview_preview_limits.aliases, eq=31)
        tm.that(
            tuple(state.path for state in inputs.sources)[-2:],
            eq=(directory / "codegen.yaml", directory / "codegen.local.yaml"),
        )

    @staticmethod
    def test_captured_tool_layers_preserve_additions_and_projected_replacement(
        tmp_path: Path,
    ) -> None:
        """Captured layers share the strict source's additive list contract."""
        baseline = FlextInfraConfig.fetch_global().Infra.codegen.toolchain.tools
        seed = next(iter(baseline))
        project_tool, local_tool, replacement_tool = (
            m.Infra.MiseToolEntry.model_validate(
                seed.model_dump(round_trip=True)
                | {"name": f"{seed.name}-{suffix}", "selector": None},
            )
            for suffix in ("project", "local", "replacement")
        )
        _, project_path, local_path = (
            FlextInfraConfig.config_layer_paths_for_repository(
                tmp_path,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )
        )
        project_path.parent.mkdir()
        for path, tool in (
            (project_path, project_tool),
            (local_path, local_tool),
        ):
            tm.ok(
                u.Cli.yaml_dump(
                    path,
                    {
                        "Infra": {
                            "codegen": {
                                "toolchain": {
                                    "tools": [
                                        tool.model_dump(mode="json", round_trip=True),
                                    ],
                                },
                            },
                        },
                    },
                ),
            )
        captured = tm.ok(u.Infra.load_codegen_inputs(tmp_path))
        tm.that(
            captured.spec.toolchain.tools,
            eq=(*baseline, project_tool, local_tool),
        )
        projected = tm.ok(
            u.Infra.project_codegen_inputs(
                tmp_path,
                captured,
                projections=(
                    m.Infra.CodegenLayerProjection(
                        path=project_path,
                        values={
                            "Infra": {
                                "codegen": {
                                    "toolchain": {
                                        "tools": [
                                            replacement_tool.model_dump(
                                                mode="json",
                                                round_trip=True,
                                            ),
                                        ],
                                    },
                                },
                            },
                        },
                    ),
                ),
            ),
        )
        tm.that(
            projected.spec.toolchain.tools,
            eq=(*baseline, replacement_tool, local_tool),
        )

    @staticmethod
    def test_provider_registry_declaration_fails_validation(
        tmp_path: Path,
    ) -> None:
        """The exterminated provider registry cannot come back through a merge."""
        _, _, local = FlextInfraConfig.config_layer_paths_for_repository(
            tmp_path,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        local.parent.mkdir()
        local.write_text(
            "Infra:\n"
            "  codegen:\n"
            "    providers:\n"
            "      - name: example-org\n"
            "        organization: example-org\n"
            "        base_url: https://github.com/example-org\n"
            "        branch: main\n",
            encoding="utf-8",
        )
        inputs = u.Infra.load_codegen_inputs(tmp_path)
        tm.fail(inputs)
        tm.that(inputs.error, has="providers")
