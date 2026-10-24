"""Fail-closed pytest configuration contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from typing_extensions import TypeForm

from flext_infra import config
from flext_infra.deps import FlextInfraToolTablesPhase
from tests import c, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPytestFailClosedConfig:
    """Prove canonical pytest settings replace local bypasses deterministically."""

    @staticmethod
    @pytest.mark.asyncio
    async def test_declared_async_provider_executes_coroutines() -> None:
        """Exercise the installed provider rather than merely registering a marker."""
        await asyncio.sleep(0)
        tm.ok(asyncio.current_task() is not None)

    @staticmethod
    def test_phase_replaces_stale_collection_and_warning_policy(
        tmp_path: Path,
    ) -> None:
        """Replace ignored roots and warning filters without second-apply drift."""
        policy = config.Infra.tooling.tools.pytest
        native = u.Infra.native_tool_settings(
            config.Infra.tooling, "pytest.ini_options"
        )
        tooling = config.Infra.tooling.model_copy(
            update={
                "settings": {
                    **config.Infra.tooling.settings,
                    "pytest.ini_options": (
                        *config.Infra.tooling.settings["pytest.ini_options"],
                        (
                            "python_classes",
                            ["Spec*", *u.Tests.strings(native["python_classes"])],
                        ),
                        (
                            "python_files",
                            ["spec_*.py", *u.Tests.strings(native["python_files"])],
                        ),
                    ),
                },
                "tools": config.Infra.tooling.tools.model_copy(
                    update={
                        "pytest": policy.model_copy(
                            update={
                                "standard_markers": (
                                    *policy.standard_markers,
                                    "custom: stale local marker",
                                )
                            },
                        ),
                    },
                ),
            },
        )
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(
                '[project]\nname = "flext-sample"\n'
                "[tool.pytest.ini_options]\n"
                'addopts = ["--maxfail=1", "--cov=.", "--markdown-docs"]\n'
                'filterwarnings = ["ignore:legacy warning suppression"]\n'
                'markers = ["custom: stale local marker"]\n'
                'python_classes = ["Spec*"]\n'
                'python_files = ["spec_*.py"]\n'
                'testpaths = ["architecture", "guides", "tests"]\n',
            ),
        )
        phase = FlextInfraToolTablesPhase(tooling)
        pyproject = tmp_path / "flext-sample" / c.PYPROJECT_FILENAME

        first_changes = phase.apply_payload(payload, path=pyproject)
        second_changes = phase.apply_payload(payload, path=pyproject)

        tm.that(first_changes, empty=False)
        tm.that(second_changes, empty=True)
        ini = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["pytest"])[
                "ini_options"
            ],
        )
        tm.that(
            list(u.Tests.strings(ini["filterwarnings"])),
            eq=list(
                u.Infra.native_tool_setting(
                    tooling,
                    "pytest.ini_options",
                    "filterwarnings",
                    TypeForm(t.StrSequence),
                )
            ),
        )
        tm.that(
            list(u.Tests.strings(ini["testpaths"])),
            eq=list(
                u.Infra.native_tool_setting(
                    tooling, "pytest.ini_options", "testpaths", TypeForm(t.StrSequence)
                )
            ),
        )
        tm.that(
            ini["asyncio_default_fixture_loop_scope"],
            eq=u.Infra.native_tool_setting(
                tooling, "pytest.ini_options", "asyncio_default_fixture_loop_scope", str
            ),
        )
        tm.that(
            set(u.Tests.strings(ini["addopts"])),
            eq=set(
                u.Infra.native_tool_setting(
                    tooling, "pytest.ini_options", "addopts", TypeForm(t.StrSequence)
                )
            ),
        )
        tm.that(
            set(u.Tests.strings(ini["markers"])),
            eq={"custom: stale local marker", *policy.standard_markers},
        )
        tm.that(u.Tests.strings(ini["python_classes"]), has="Spec*")
        tm.that(u.Tests.strings(ini["python_files"]), has="spec_*.py")
