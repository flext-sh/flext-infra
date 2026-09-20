"""Public sed-by-list contract for the ``make mod`` text phase."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, u
from flext_infra.codemod import FlextInfraModTextGateEngine


class TestsFlextInfraModTextGateEngine:
    """Exercise the declarative sed-by-list engine through its public scan."""

    def test_scan_proves_rewrite_receipt_and_fixed_point(
        self, mod_workspace: Path
    ) -> None:
        """One list entry rewrites its match once and reaches a fixed point."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    "  - id: rewrite-serialization-lock-call\n"
                    "    description: prove one list-driven rewrite receipt\n"
                    "    find: 'serialization_lock_execute\\(paths, timeout\\)'\n"
                    "    replace: 'serialization_lock_execute(chunks, deadline)'\n"
                    "    expected: 1\n"
                ),
            )
        )
        sample = mod_workspace / "sample.py"
        # Derived, never frozen: the fixture owns the module's shape, so the
        # expected line is read from it (project law P0 — a test never hardcodes
        # a value its own source of truth can produce).
        expected_line = next(
            index
            for index, text in enumerate(
                sample.read_text(encoding="utf-8").splitlines(), start=1
            )
            if "paths, timeout" in text
        )

        first = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace, fix=False, validate_receipts=True
            )
        )
        tm.that(first.findings, eq=1)
        tm.that(first.actionable, eq=1)
        tm.that(len(first.files), eq=1)
        finding = first.entries[0]
        tm.that(finding.rule_id, eq="rewrite-serialization-lock-call")
        tm.that(finding.line, eq=expected_line)
        tm.that(sample.read_text(encoding="utf-8").count("paths, timeout"), eq=1)

        applied = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.that(applied.findings, eq=1)
        final = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False))
        tm.that(final.findings, eq=0)
        # The rewrite is proven by what changed, not by freezing the fixture's
        # whole text: the elected call carries the replacement and the original
        # argument list is gone.
        rewritten = sample.read_text(encoding="utf-8")
        tm.that(rewritten, has="serialization_lock_execute(chunks, deadline)")
        tm.that(rewritten, lacks="serialization_lock_execute(paths, timeout)")

    def test_scan_requires_declared_receipt_to_match_exactly(
        self, mod_workspace: Path
    ) -> None:
        """A wrong expected-count receipt fails the scan loudly."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    "  - id: rewrite-serialization-lock-call\n"
                    "    find: 'serialization_lock_execute\\(paths, timeout\\)'\n"
                    "    replace: 'serialization_lock_execute(chunks, deadline)'\n"
                    "    expected: 2\n"
                ),
            )
        )
        with pytest.raises(RuntimeError, match="expected 2 finding\\(s\\), scan"):
            FlextInfraModTextGateEngine.scan(
                mod_workspace, fix=False, validate_receipts=True
            )

    def test_load_rules_rejects_unknown_keys_and_duplicate_ids(
        self, mod_workspace: Path
    ) -> None:
        """Declarative list entries must be exact and unique."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    "  - id: first\n"
                    "    find: 'alpha'\n"
                    "  - id: second\n"
                    "    find: 'beta'\n"
                    "    unsupported: true\n"
                ),
            )
        )
        unknown = FlextInfraModTextGateEngine.load_rules(mod_workspace)
        tm.that(unknown.failure)
        tm.that("unsupported" in str(unknown.error), eq=True)

        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n  - id: first\n    find: 'alpha'\n  - id: first\n    find: 'beta'\n",
            )
        )
        duplicate = FlextInfraModTextGateEngine.load_rules(mod_workspace)
        tm.that(duplicate.failure)
        tm.that("duplicate text rule id" in str(duplicate.error), eq=True)

        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n  - id: first\n    find: 'alpha'\n  - id: second\n    find: 'beta'\n",
            )
        )
        valid = tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        tm.that(len(valid), eq=2)

    def test_include_and_exclude_globs_elect_exact_targets(
        self, mod_workspace: Path
    ) -> None:
        """Glob election scopes the rewrite to the declared surfaces only."""
        package_dir = mod_workspace / "src" / "mod_workspace"
        tm.ok(u.Cli.ensure_dir(package_dir))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package_dir / "frozen.py", "LEGACY_PIN = '2026.8.14'\n"
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    "  - id: rewrite-frozen-pin\n"
                    "    include: ['src/**']\n"
                    "    exclude: ['**/legado/**']\n"
                    "    find: 'LEGACY_PIN = .*'\n"
                    "    replace: 'LEGACY_PIN = values.pin()'\n"
                    "    expected: 1\n"
                ),
            )
        )
        first = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace, fix=False, validate_receipts=True
            )
        )
        tm.that(first.findings, eq=1)
        tm.that(first.entries[0].file.as_posix(), eq="src/mod_workspace/frozen.py")

        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    "  - id: rewrite-frozen-pin\n"
                    "    include: ['src/**']\n"
                    "    exclude: ['**/frozen.py']\n"
                    "    find: 'LEGACY_PIN = .*'\n"
                    "    replace: 'LEGACY_PIN = values.pin()'\n"
                    "    expected: 0\n"
                ),
            )
        )
        excluded = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace, fix=False, validate_receipts=True
            )
        )
        tm.that(excluded.findings, eq=0)


__all__: list[str] = ["TestsFlextInfraModTextGateEngine"]
