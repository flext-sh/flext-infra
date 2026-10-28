"""Source campaigns and strict explicit rename artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, tm, u


class TestsFlextInfraSemanticRenameSeed:
    """Source campaigns never weaken the explicit rename artifact contract."""

    @staticmethod
    def test_package_preview_expands_files_modes_and_cross_root_consumers(
        tmp_path: Path,
    ) -> None:
        """A package preview retains nested content and never moves live sources."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="package-receiver", package_name="package_receiver"
        )
        origin = package / "parts"
        nested = origin / "nested"
        nested.mkdir(parents=True)
        contents = {
            origin / "__init__.py": "from .service import Original\n",
            origin / "service.py": "class Original:\n    pass\n",
            nested / "__init__.py": "",
            nested / "consumer.py": "from ..service import Original\n",
        }
        for path, content in contents.items():
            path.write_text(content, encoding=c.DEFAULT_ENCODING)
        source = origin / "service.py"
        source.chmod(0o750)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.parts.service import Original\n",
            encoding=c.DEFAULT_ENCODING,
        )
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.parts",
                    replacement_name="_parts",
                    reason="Explicit package naming decision",
                ),
            ),
            consumer_roots=(receiver,),
        )
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, selections
                )
            )
        target = package / "_parts"
        tm.that(
            artifact.moves,
            eq=tuple(
                sorted((path, target / path.relative_to(origin)) for path in contents)
            ),
        )
        for path, content in contents.items():
            tm.that(artifact.candidate.updates[path], eq=None)
            tm.that(
                artifact.candidate.updates[target / path.relative_to(origin)],
                eq=content,
            )
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
        tm.that(artifact.candidate.modes[target / source.name], eq=original.mode)
        tm.that(artifact.candidate.updates[consumer], has="._parts.service")
        tm.fail(target.exists())

    @staticmethod
    @pytest.mark.parametrize(
        "conflict", ["payload", "directory", "module", "child", "empty"]
    )
    def test_package_preview_rejects_incomplete_or_overlapping_moves(
        tmp_path: Path, conflict: str
    ) -> None:
        """Unsupported resources and occupied or overlapping moves fail prepublish."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        origin = package / "parts"
        origin.mkdir()
        initializer = origin / "__init__.py"
        initializer.write_text("", encoding=c.DEFAULT_ENCODING)
        source = origin / "service.py"
        content = "class Original:\n    pass\n"
        source.write_text(content, encoding=c.DEFAULT_ENCODING)
        decisions = [
            m.Infra.SemanticRenameSelection(
                qualified_name=f"{package.name}.parts",
                replacement_name="_parts",
                reason="Explicit package naming decision",
            )
        ]
        if conflict == "payload":
            (origin / "resource.json").write_text("{}", encoding=c.DEFAULT_ENCODING)
            diagnostic = "cannot preserve uninventoried payload"
        elif conflict == "directory":
            (package / "_parts").mkdir()
            diagnostic = "destination is occupied"
        elif conflict == "module":
            (package / "_parts.py").write_text("", encoding=c.DEFAULT_ENCODING)
            diagnostic = "destination is occupied"
        elif conflict == "empty":
            (origin / "empty").mkdir()
            diagnostic = "cannot preserve empty directory"
        else:
            decisions.append(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.parts.service",
                    replacement_name="renamed",
                    reason="Overlapping child decision",
                )
            )
            diagnostic = "separate virtual waves for overlapping selections"
        selections = m.Infra.SemanticRenameSelections(decisions=tuple(decisions))
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match=diagnostic),
        ):
            FlextInfraCodemodSemanticApply.build_rename_plan(
                root, workspace, selections
            )
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
        tm.ok(initializer.exists())

    @staticmethod
    def test_native_rename_artifact_round_trips_and_rejects_consumer_drift(
        tmp_path: Path,
    ) -> None:
        """A real naming decision round-trips and rejects external source drift."""
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
            ),
            consumer_roots=(receiver,),
        )
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, selections
                )
            )
        tm.that(len(artifact.decisions), eq=1)
        tm.that(artifact.candidate.updates[consumer], has="Renamed")
        tm.that(artifact.consumer_roots, eq=(receiver,))
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(driver, required=True))
        hydrated = m.Infra.SemanticRenamePlan.model_validate_json(
            tm.not_none(state.content)
        )
        with infra.rope_workspace(root) as workspace:
            tm.ok(
                FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                    root, hydrated, state, workspace
                )
            )
        consumer.write_bytes(consumer.read_bytes() + b"# changed source epoch\n")
        with infra.rope_workspace(root) as workspace:
            tm.fail(
                FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                    root, hydrated, state, workspace
                )
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((originals[0], state)))

    @staticmethod
    def test_empty_rename_is_rejected_at_construction_json_and_builder(
        tmp_path: Path,
    ) -> None:
        """An authenticated no-op source campaign is never a rename artifact."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        campaign = tm.ok(FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="decisions"):
            m.Infra.SemanticRenamePlan(
                decisions=(), edits=(), candidate=campaign.candidate
            )
        payload = campaign.model_dump(mode="json")
        payload.update(decisions=[], edits=[], moves=[])
        content = tm.ok(u.Cli.json_dumps(payload))
        with pytest.raises(ValueError, match="decisions"):
            m.Infra.SemanticRenamePlan.model_validate_json(content)
        driver = root / "empty.artifact"
        tm.ok(u.Cli.atomic_write_text_file(driver, content))
        with pytest.raises(ValueError, match="decisions"):
            FlextInfraCodemodSemanticApply.load_rename_artifact(
                root, m.Infra.ModCommand(repository_root=root, rename_plan=driver)
            )
        with infra.rope_workspace(root) as workspace:
            tm.fail(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, m.Infra.SemanticRenameSelections(decisions=())
                ),
                has="explicit naming decision",
            )

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
            eq=(
                "semantic rename has no inventoried source: "
                f"{package.name}.service.MissingFirst"
            ),
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
