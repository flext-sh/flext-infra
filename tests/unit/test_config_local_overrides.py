"""Contract for the gitignored per-clone local config override file.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from flext_core import e
from flext_infra import FlextInfraConfig, c
from tests import tm, u


class TestsFlextInfraConfigLocalOverrides:
    """Prove the local override file merges last through the public surface."""

    @staticmethod
    def test_cache_defaults_validate_and_serialize_for_concrete_contracts() -> None:
        """Concrete cache owners preserve validated defaults and native wire values."""
        make = FlextInfraConfig.fetch_global().Infra.codegen.make
        for spec in (make.ruff_cache, make.mypy_cache):
            cache_type = type(spec)
            cache = cache_type.model_validate({
                "external_storage_directory": spec.external_storage_directory,
            })
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
    def _copy_tracked_configs(target: Path) -> None:
        """Seed one config directory with the real tracked fleet config."""
        for tracked in FlextInfraConfig.ssot_config_dir().glob("*.yaml"):
            shutil.copy(tracked, target / tracked.name)

    def test_tracked_configs_keep_fleet_defaults(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Without a local file the tracked scalar survives untouched.

        The expectation is the tracked SSOT read itself (P0): any legitimate
        config change keeps both loads equal, and only a broken merge diverges.
        """
        self._copy_tracked_configs(tmp_path)
        baseline = FlextInfraConfig.fetch_global()
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            fresh = FlextInfraConfig.fetch_global()
            tm.that(
                fresh.Infra.codegen.loc_cap.max_lines,
                eq=baseline.Infra.codegen.loc_cap.max_lines,
            )
        finally:
            FlextInfraConfig.reset_for_testing()

    def test_empty_mypy_overlay_keeps_selected_global_policy(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty local lists cannot remove policy supplied by the YAML owner."""
        baseline = FlextInfraConfig.fetch_global().Infra.tooling.tools.mypy
        self._copy_tracked_configs(tmp_path)
        (tmp_path / c.Infra.CODEGEN_LOCAL_OVERRIDES_FILENAME).write_text(
            "Infra:\n  tooling:\n    tools:\n      mypy:\n"
            "        plugins: []\n        disable-error-code: []\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            policy = FlextInfraConfig.fetch_global().Infra.tooling.tools.mypy
            tm.that(tuple(policy.plugins), eq=tuple(baseline.plugins))
            tm.that(
                tuple(policy.disable_error_code),
                eq=tuple(baseline.disable_error_code),
            )
        finally:
            FlextInfraConfig.reset_for_testing()

    def test_local_file_scalar_wins_despite_sorted_glob_position(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The local override wins scalars although its name sorts first.

        ``codegen-overrides.local.yaml`` sorts before the tracked files, so a
        plain glob would let the tracked config clobber it; the loader must
        anchor it last regardless of lexicographic position.
        """
        self._copy_tracked_configs(tmp_path)
        (tmp_path / c.Infra.CODEGEN_LOCAL_OVERRIDES_FILENAME).write_text(
            "Infra:\n  codegen:\n    loc_cap:\n      max_lines: 500\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            fresh = FlextInfraConfig.fetch_global()
            tm.that(fresh.Infra.codegen.loc_cap.max_lines, eq=500)
        finally:
            FlextInfraConfig.reset_for_testing()

    def test_local_file_dict_entries_add_beside_tracked_ones(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A dict-typed registry gains the local entry and keeps tracked ones."""
        self._copy_tracked_configs(tmp_path)
        (tmp_path / c.Infra.CODEGEN_LOCAL_OVERRIDES_FILENAME).write_text(
            "Infra:\n"
            "  codegen:\n"
            "    layout:\n"
            "      project_overrides:\n"
            "        example-project:\n"
            "          ignore_globs:\n"
            "            - example\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            fresh = FlextInfraConfig.fetch_global()
            overrides = fresh.Infra.codegen.layout.project_overrides
            tm.that("example-project" in overrides, eq=True)
            tm.that("flext-cli" in overrides, eq=True)
        finally:
            FlextInfraConfig.reset_for_testing()

    def test_target_and_local_layers_use_explicit_repository_root(
        self,
        tmp_path: Path,
    ) -> None:
        """Explicit target layers merge independently of the ambient directory."""
        root = tmp_path / "consumer"
        directory = root / c.Infra.CODEGEN_CONFIG_DIR
        directory.mkdir(parents=True)
        (directory / "codegen.yaml").write_text(
            "Infra:\n  codegen:\n    make:\n      docs:\n        overview_preview_limits:\n          aliases: 23\n",
            encoding="utf-8",
        )
        (directory / "codegen.local.yaml").write_text(
            "Infra:\n  codegen:\n    make:\n      docs:\n        overview_preview_limits:\n          aliases: 31\n",
            encoding="utf-8",
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        tm.that(inputs.spec.make.docs.overview_preview_limits.aliases, eq=31)
        tm.that(
            tuple(state.path for state in inputs.sources)[-2:],
            eq=(directory / "codegen.yaml", directory / "codegen.local.yaml"),
        )

    def test_provider_registry_declaration_fails_validation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The exterminated provider registry cannot come back through a merge."""
        self._copy_tracked_configs(tmp_path)
        (tmp_path / c.Infra.CODEGEN_LOCAL_OVERRIDES_FILENAME).write_text(
            "Infra:\n"
            "  codegen:\n"
            "    providers:\n"
            "      - name: example-org\n"
            "        organization: example-org\n"
            "        base_url: https://github.com/example-org\n"
            "        branch: main\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("FLEXT_INFRA_CONFIG_DIR", str(tmp_path))
        FlextInfraConfig.reset_for_testing()
        try:
            # The settings boundary surfaces pydantic's own ValidationError
            # (public alias e.PydanticValidationError); the exterminated
            # providers registry is rejected as a forbidden extra field.
            with pytest.raises(e.PydanticValidationError, match="providers"):
                FlextInfraConfig.fetch_global()
        finally:
            FlextInfraConfig.reset_for_testing()
