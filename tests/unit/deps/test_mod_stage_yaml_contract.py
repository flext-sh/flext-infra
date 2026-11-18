"""Strict tooling-loader contracts for native YAML stage selections.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraConfig, config
from tests import c, tm, u


class TestsFlextInfraModStageYamlContract:
    """Exercise the real layered YAML loader without weakening strict values."""

    @staticmethod
    def test_packaged_stage_arrays_keep_their_declared_selections(
        tmp_path: Path,
    ) -> None:
        """The packaged YAML stage arrays match their canonical typed policy."""
        actual = tm.ok(u.Infra.load_tooling_inputs(tmp_path)).document.mod.phases
        expected = config.Infra.tooling.mod.phases
        tm.that(actual.stages, eq=expected.stages)
        for stage in actual.stages:
            tm.that(type(stage.shapes), eq=tuple)
            tm.that(type(stage.select), eq=tuple)

    @staticmethod
    @c.Tests.MARK.parametrize("field", ["shapes", "select"])
    @c.Tests.MARK.parametrize("value", ["not-an-array", 1])
    def test_non_array_stage_selections_remain_invalid(
        tmp_path: Path, field: str, value: str | int
    ) -> None:
        """Scalar YAML values cannot masquerade as selection arrays."""
        _, _, local = FlextInfraConfig.config_layer_paths_for_repository(
            tmp_path, filename="tooling.yaml"
        )
        stage = config.Infra.tooling.mod.phases.stages[0].model_dump(
            mode="json", by_alias=True
        )
        stage[field] = value
        tm.ok(
            u.Cli.yaml_dump(
                local,
                {"Infra": {"tooling": {"mod": {"phases": {"stages": [stage]}}}}},
            )
        )
        tm.fail(u.Infra.load_tooling_inputs(tmp_path), has="tuple_type")
