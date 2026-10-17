"""Contract for a repository's own config layers over the packaged policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, c
from tests import tm, u


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
        root = tmp_path / "consumer"
        self._consumer_config(root)
        spec = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        tm.that(
            spec.loc_cap.max_lines,
            eq=FlextInfraConfig.fetch_global().Infra.codegen.loc_cap.max_lines,
        )

    def test_local_layer_dict_entries_add_beside_packaged_ones(
        self,
        tmp_path: Path,
    ) -> None:
        """A dict-typed registry gains the local entry and keeps packaged ones."""
        baseline = (
            FlextInfraConfig.fetch_global().Infra.codegen.layout.project_overrides
        )
        root = tmp_path / "consumer"
        (self._consumer_config(root) / "codegen.local.yaml").write_text(
            "Infra:\n"
            "  codegen:\n"
            "    layout:\n"
            "      project_overrides:\n"
            "        example-project:\n"
            "          ignore_globs:\n"
            "            - example\n",
            encoding="utf-8",
        )
        overrides = tm.ok(
            u.Infra.load_codegen_inputs(root)
        ).spec.layout.project_overrides
        tm.that(set(overrides), eq={*baseline, "example-project"})

    def test_target_and_local_layers_use_explicit_repository_root(
        self,
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

    def test_project_toolchain_tools_extend_the_fleet_table(
        self,
        tmp_path: Path,
    ) -> None:
        """A layer's tools concatenate onto the packaged table; fleet tools stay."""
        root = tmp_path / "consumer"
        directory = root / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir(parents=True)
        fleet = tuple(
            tool.name
            for tool in FlextInfraConfig.fetch_global().Infra.codegen.toolchain.tools
        )
        (directory / "codegen.yaml").write_text(
            "Infra:\n  codegen:\n    toolchain:\n      tools:\n"
            "      - name: demo-tool\n"
            "        selector: pypi:demo-tool\n"
            "        version: 1.2.3\n"
            "        version_probe:\n"
            "          binary: demo-tool\n"
            "          arguments: [ --version ]\n"
            "          pattern: '^{version}$'\n",
            encoding="utf-8",
        )
        tools = tm.ok(u.Infra.load_codegen_inputs(root)).spec.toolchain.tools
        tm.that(tuple(tool.name for tool in tools), eq=(*fleet, "demo-tool"))

    def test_provider_registry_declaration_fails_validation(
        self,
        tmp_path: Path,
    ) -> None:
        """The exterminated provider registry cannot come back through a layer."""
        root = tmp_path / "consumer"
        (self._consumer_config(root) / "codegen.local.yaml").write_text(
            "Infra:\n"
            "  codegen:\n"
            "    providers:\n"
            "      - name: example-org\n"
            "        organization: example-org\n"
            "        base_url: https://github.com/example-org\n"
            "        branch: main\n",
            encoding="utf-8",
        )
        tm.fail(u.Infra.load_codegen_inputs(root), has="providers")
