"""Public utility evidence for semantic API-alias cutovers."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, u
from flext_tests import tm


class TestsFlextInfraApiAliasCutover:
    """Exercise owner-first alias removal only through ``u.Infra``."""

    def test_rewires_consumer_before_removing_owner(self, tmp_path: Path) -> None:
        """Plan the complete owner/export/import/reference cutover together."""
        owner = tmp_path / "flext-sample/src/flext_sample/api.py"
        consumer = tmp_path / "flext-sample/tests/test_api.py"
        sources = {
            owner: (
                "class FlextSample:\n"
                "    pass\n\n"
                "sample = FlextSample\n"
                '__all__ = ["FlextSample", "sample"]\n'
            ),
            consumer: ("from flext_sample.api import sample\n\nfacade = sample\n"),
        }
        finding = m.Infra.ModScanFinding(
            rule_file="ban-compat-alias.yml",
            rule_id="ban-compat-alias",
            repository="flext-sample",
            file=owner.relative_to(tmp_path),
            range={},
            text="sample = FlextSample",
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
            payload={},
        )

        edits = u.Infra.plan_api_alias_cutover(
            root=tmp_path, sources=sources, findings=(finding,)
        )
        by_path = {edit.file_path: edit.updated_source for edit in edits}

        tm.that(len(edits), eq=2)
        tm.that(by_path[owner], lacks="sample = FlextSample")
        tm.that(by_path[owner], lacks='"sample"')
        tm.that(by_path[consumer], has="from flext_sample.api import FlextSample")
        tm.that(by_path[consumer], has="facade = FlextSample")
        tm.that(by_path[consumer], lacks="import sample")


__all__: list[str] = ["TestsFlextInfraApiAliasCutover"]
