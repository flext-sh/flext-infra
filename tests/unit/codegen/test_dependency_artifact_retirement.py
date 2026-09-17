"""Prove dependency artifact retirement does not target coordination locks."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, config
from flext_infra.codegen.conform import FlextInfraCodegenConform


class TestsDependencyArtifactRetirement:
    """Retirement is bounded to the typed dependency artifact inventory."""

    def test_retirement_preserves_journal_lock(self, tmp_path: Path) -> None:
        retired = config.Infra.codegen.toolchain.retired_dependency_artifacts
        for filename in retired:
            (tmp_path / filename).write_text("obsolete dependency state\n")
        journal_lock = tmp_path / "generation.journal.lock"
        journal_lock.write_text("active lease\n")
        plans = tm.ok(FlextInfraCodegenConform.retired_projection_plans(
            tmp_path, c.Infra.MakeProfile.WORKSPACE
        ))
        tm.that({plan.path.name for plan in plans}, eq=set(retired))
        tm.that(all(plan.desired_content is None for plan in plans), eq=True)
        tm.that(journal_lock.read_text(), eq="active lease\n")

    def test_retirement_rejects_symlink(self, tmp_path: Path) -> None:
        target = tmp_path / "active.journal.lock"
        target.write_text("active lease\n")
        filename = config.Infra.codegen.toolchain.retired_dependency_artifacts[0]
        (tmp_path / filename).symlink_to(target)
        with pytest.raises(ValueError, match="Refusing non-file"):
            FlextInfraCodegenConform.retired_projection_plans(
                tmp_path, c.Infra.MakeProfile.WORKSPACE
            )
        tm.that(target.read_text(), eq="active lease\n")
