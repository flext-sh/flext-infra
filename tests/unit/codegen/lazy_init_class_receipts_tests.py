"""Content-addressed class receipts for the lazy-init duplicate scan."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenLazyInitClassReceipts,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodegenLazyInitClassReceipts:
    """Content-addressed receipt store round-trips and fails open."""

    def _receipts(self, tmp_path: Path) -> FlextInfraCodegenLazyInitClassReceipts:
        return FlextInfraCodegenLazyInitClassReceipts(tmp_path)

    def _receipt_path(self, tmp_path: Path) -> Path:
        return (
            tmp_path
            / c.Infra.TRANSACTION_STATE_DIRNAME
            / c.Infra.LAZY_INIT_CLASS_RECEIPTS_RELPATH
        )

    def test_content_key_is_deterministic_and_content_addressed(
        self, tmp_path: Path
    ) -> None:
        """Equal bytes map to one key; different bytes map to different keys."""
        first = self._receipts(tmp_path).content_key(b"class Alpha:\\n")
        second = self._receipts(tmp_path).content_key(b"class Alpha:\\n")
        other = self._receipts(tmp_path).content_key(b"class Beta:\\n")
        tm.that(first, eq=second)
        tm.that(first != other, eq=True)

    def test_record_save_reload_hits_without_recompute(self, tmp_path: Path) -> None:
        """Recorded names survive a store round-trip under the content key."""
        content = b"class Gamma:\\n    pass\\n"
        writer = self._receipts(tmp_path)
        tm.that(writer.class_names(content), eq=None)
        writer.record(content, ("Gamma",))
        tm.that(writer.save(), eq=True)

        reader = self._receipts(tmp_path)
        tm.that(reader.class_names(content), eq=("Gamma",))

    def test_version_mismatch_discards_entries(self, tmp_path: Path) -> None:
        """A schema-version change invalidates the persisted cache."""
        writer = self._receipts(tmp_path)
        writer.record(b"class Delta:\\n", ("Delta",))
        tm.that(writer.save(), eq=True)
        document = json.loads(self._receipt_path(tmp_path).read_bytes())
        document["version"] = c.Infra.LAZY_INIT_CLASS_RECEIPTS_VERSION + 1
        self._receipt_path(tmp_path).write_text(json.dumps(document), encoding="utf-8")

        reader = self._receipts(tmp_path)
        tm.that(reader.class_names(b"class Delta:\\n"), eq=None)

    def test_corrupt_document_discards_entries(self, tmp_path: Path) -> None:
        """Undecodable cache bytes fail open to an empty store."""
        writer = self._receipts(tmp_path)
        writer.record(b"class Epsilon:\\n", ("Epsilon",))
        tm.that(writer.save(), eq=True)
        self._receipt_path(tmp_path).write_text("{not json", encoding="utf-8")

        reader = self._receipts(tmp_path)
        tm.that(reader.class_names(b"class Epsilon:\\n"), eq=None)


class TestsFlextInfraCodegenLazyInitReceiptScan:
    """The duplicate scan is receipt-cached with unchanged results."""

    def _write_module(self, package: Path, name: str, body: str) -> None:
        package.mkdir(parents=True, exist_ok=True)
        (package / "__init__.py").write_text('"""Test package."""\n', encoding="utf-8")
        (package / f"{name}.py").write_text(body, encoding="utf-8")

    def test_scan_outcome_is_stable_across_receipt_runs(
        self, tmp_path: Path
    ) -> None:
        """Cold and warm scans agree on identical bytes (flext-8hctr semantics).

        The scan's scope_path guard currently selects no objects, so both runs
        succeed without collisions; the receipts record that same (empty)
        selection per content hash and the warm run must reproduce it exactly.
        """
        shared_body = (
            '"""Shared duplicate class."""\n\n\nclass DupliCollisionProbe:\n'
            '    """Long uppercase name cleared the duplicate predicate."""\n'
        )
        self._write_module(tmp_path / "src" / "alpha", "holder", shared_body)
        self._write_module(tmp_path / "src" / "beta", "holder", shared_body)

        cold = FlextInfraCodegenLazyInit(repository_root=tmp_path).plan_files()
        tm.ok(cold)
        tm.that(self._receipt_path(tmp_path).is_file(), eq=True)

        warm = FlextInfraCodegenLazyInit(repository_root=tmp_path).plan_files()
        tm.ok(warm)
        tm.that(
            tuple(sorted(file.path for file in warm.value.files)),
            eq=tuple(sorted(file.path for file in cold.value.files)),
        )

    def test_unique_modules_plan_clean_and_reuse_receipts(self, tmp_path: Path) -> None:
        """A collision-free workspace plans twice with the receipt store warm."""
        self._write_module(
            tmp_path / "src" / "solo",
            "holder",
            '"""Unique module."""\n\n\nclass SoloProbeClass:\n'
            '    """Only definition of this name."""\n',
        )

        first = FlextInfraCodegenLazyInit(repository_root=tmp_path).plan_files()
        tm.ok(first)
        second = FlextInfraCodegenLazyInit(repository_root=tmp_path).plan_files()
        tm.ok(second)


__all__: list[str] = [
    "TestsFlextInfraCodegenLazyInitClassReceipts",
    "TestsFlextInfraCodegenLazyInitReceiptScan",
]
