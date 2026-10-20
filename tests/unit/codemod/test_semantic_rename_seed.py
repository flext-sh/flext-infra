"""Authenticated empty campaigns and strict explicit rename inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, tm, u


class TestsFlextInfraSemanticRenameSeed:
    """Zero selected renames still capture and authenticate elected sources."""

    @staticmethod
    @pytest.mark.parametrize("selected", [False, True])
    def test_native_campaign_authenticates_sources_without_requiring_a_rename(
        tmp_path: Path, *, selected: bool
    ) -> None:
        """Empty seeds and actual renames both reject external source drift."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="seed-receiver",
            package_name="seed_receiver",
        )
        driver = root / c.Infra.REPORTS_DIR_NAME / "native" / "seed.artifact"
        driver.parent.mkdir(parents=True, exist_ok=True)
        source = package / "service.py"
        source.write_text("class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.service import Original\nVALUE = Original()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, consumer)
        )
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.Original",
                    replacement_name="Renamed",
                    reason="Explicit domain rename",
                ),
            )
            if selected
            else (),
            consumer_roots=(receiver,),
        )
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, selections
                )
            )
        tm.that(len(artifact.decisions), eq=int(selected))
        tm.that(bool(artifact.candidate.updates), eq=selected)
        if selected:
            tm.that(artifact.candidate.updates[consumer], has="Renamed")
        else:
            tm.that(artifact.edits, eq=())
            tm.that(artifact.moves, eq=())
        tm.that(artifact.consumer_roots, eq=(receiver,))
        for original in originals:
            tm.ok(original in artifact.source_states)
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(driver, required=True))
        hydrated = m.Infra.SemanticRenamePlan.model_validate_json(
            tm.not_none(state.content)
        )
        tm.ok(
            FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                root, hydrated, state
            )
        )
        consumer.write_bytes(consumer.read_bytes() + b"# changed source epoch\n")
        tm.fail(
            FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                root, hydrated, state
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((originals[0], state)))

    @staticmethod
    def test_missing_selected_identity_is_not_an_empty_campaign(tmp_path: Path) -> None:
        """The first inventory exception escapes instead of dropping selections."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        source.write_text("class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        selections = m.Infra.SemanticRenameSelections(
            decisions=tuple(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.{name}",
                    replacement_name="Renamed",
                    reason="Explicit inventory must resolve every selection",
                )
                for name in ("MissingFirst", "MissingSecond")
            )
        )
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match="MissingFirst") as failure,
        ):
            FlextInfraCodemodSemanticApply.build_rename_plan(
                root, workspace, selections
            )
        tm.that(
            str(failure.value),
            eq=f"semantic rename has no inventoried source: {package.name}.service.MissingFirst",
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
