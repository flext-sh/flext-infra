"""Public sed-by-list contract for the ``make mod`` text phase publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, m
from flext_infra.codemod import FlextInfraModTextGateEngine
from tests import c, tm, u


class TestsFlextInfraModTextPublication:
    """Exercise text-phase publication, rewrite receipts, and scope election."""

    def test_external_catalogue_id_collision_fails_before_publication(
        self,
        mod_workspace: Path,
    ) -> None:
        """A local rule cannot silently replace the provider's declared rule."""
        provider = tm.ok(
            FlextInfraModTextGateEngine.load_rules(config.ssot_config_dir().parent),
        )
        collision_id = provider[0].rule_id if provider else "consumer-owned-rewrite"
        local_collision = (
            "" if provider else f"  - id: {collision_id}\n    find: 'after'\n"
        )
        first, _ = self._publication_inputs(mod_workspace)
        original = first.read_bytes()
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    f"  - id: {collision_id}\n"
                    "    find: 'before'\n"
                    "    replace: 'after'\n"
                    f"{local_collision}"
                ),
            ),
        )

        result = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.fail(result, has="duplicate text rule id")
        tm.that(first.read_bytes(), eq=original)

    def test_invalid_python_replacement_never_publishes_batch(
        self,
        mod_workspace: Path,
    ) -> None:
        """Syntax preflight rejects a broken rule before its transaction starts."""
        first, second = self._publication_inputs(mod_workspace)
        u.Cli.atomic_write_text_file(
            mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
            (
                "rules:\n"
                "  - id: invalid-python-replacement\n"
                "    find: 'value = \"before\"'\n"
                "    replace: 'value ='\n"
            ),
        ).unwrap()
        originals = (first.read_bytes(), second.read_bytes())

        with pytest.raises(SyntaxError) as rejected:
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.that(rejected.value.filename, eq=str(first))
        tm.that(rejected.value.text, has="value =")
        tm.ok(rejected.value.__traceback__ is not None)

        tm.that((first.read_bytes(), second.read_bytes()), eq=originals)

    @staticmethod
    def _publication_inputs(root: Path) -> tuple[Path, Path]:
        """Declare two authored inputs and one exact text rewrite catalogue.

        Returns:
            The resulting ``tuple[Path, Path]``.

        """
        u.Cli.atomic_write_text_file(
            root / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
            "rules:\n"
            "  - id: publication-probe\n"
            "    find: 'before'\n"
            "    replace: 'after'\n",
        ).unwrap()
        package = root / "src" / "mod_workspace"
        u.Cli.ensure_dir(package).unwrap()
        first, second = package / "first.py", package / "second.py"
        for path in (first, second):
            u.Cli.atomic_write_text_file(path, 'value = "before"\n').unwrap()
        return first, second

    def test_text_plan_retains_working_effects_and_original_physical_receipts(
        self,
        mod_workspace: Path,
    ) -> None:
        """Planning never publishes working text or substitutes it for originals."""
        first, second = self._publication_inputs(mod_workspace)
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in tm.ok(FlextInfraModTextGateEngine.source_paths(mod_workspace))
        )
        original = {
            state.path: tm.not_none(state.content).decode(c.DEFAULT_ENCODING)
            for state in states
        }
        working = {**original, first: original[first] + "# prior planned phase\n"}
        frozen = dict(working)
        _report, planned = tm.ok(
            FlextInfraModTextGateEngine.plan(
                mod_workspace,
                sources=working,
            )
        )
        targets = {plan.path: plan for plan in planned}
        for path in (first, second):
            tm.that(
                targets[path].before,
                eq=next(state for state in states if state.path == path),
            )
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original[path])
            tm.that(
                tm.not_none(targets[path].desired_content).decode(c.DEFAULT_ENCODING),
                eq=working[path].replace("before", "after"),
            )
        tm.that(working, eq=frozen)
        _report, physical = tm.ok(FlextInfraModTextGateEngine.plan(mod_workspace))
        tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        for plan in physical:
            tm.that(plan.path.read_bytes(), eq=plan.desired_content)
        _report, fixed = tm.ok(FlextInfraModTextGateEngine.plan(mod_workspace))
        tm.that(fixed, empty=True)

    def test_generated_destination_keeps_the_text_candidate_unpublished(
        self,
        mod_workspace: Path,
    ) -> None:
        """A rejected generated target leaves authored siblings unpublished."""
        first, second = self._publication_inputs(mod_workspace)
        generated = f'{c.Infra.AUTOGEN_HEADER}\nvalue = "before"\n'
        u.Cli.atomic_write_text_file(second, generated).unwrap()
        tm.fail(
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=False),
            has="canonical generator repair",
        )
        result = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)

        tm.fail(result, has="canonical generator repair")
        tm.that(first.read_bytes(), eq=b'value = "before"\n')
        tm.that(second.read_text(encoding="utf-8"), eq=generated)

    def test_invalid_later_source_retains_its_cause_and_valid_rewrite(
        self,
        mod_workspace: Path,
    ) -> None:
        """A decoding failure escapes with its native cause before any effect."""
        first, second = self._publication_inputs(mod_workspace)
        second.write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)

        tm.that(first.read_bytes(), eq=b'value = "before"\n')
        tm.that(second.read_bytes(), eq=b"\xff")

    def test_invalid_python_replacement_preserves_unpublished_sibling_effects(
        self,
        mod_workspace: Path,
    ) -> None:
        """A malformed rewrite preserves valid desired effects without publication."""
        first, second = self._publication_inputs(mod_workspace)
        original_second = second.read_bytes()
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    "  - id: valid-first\n"
                    "    include: ['src/mod_workspace/first.py']\n"
                    "    find: 'before'\n"
                    "    replace: 'after'\n"
                    "  - id: malformed-second\n"
                    "    include: ['src/mod_workspace/second.py']\n"
                    "    find: 'value = \"before\"'\n"
                    "    replace: |2-\n"
                    "      value = (\n"
                ),
            ),
        )

        malformed_rule = next(
            rule
            for rule in tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
            if rule.rule_id == "malformed-second"
        )
        with pytest.raises(SyntaxError) as expected:
            compile(f"{malformed_rule.replace}\n", str(second), "exec")
        with pytest.raises(SyntaxError) as rejected:
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.that(rejected.value.args, eq=expected.value.args)
        tm.that(rejected.value.filename, eq=expected.value.filename)
        tm.ok(rejected.value.__traceback__ is not None)

        tm.that(first.read_bytes(), eq=b'value = "before"\n')
        tm.that(second.read_bytes(), eq=original_second)

    def test_linked_destination_failure_preserves_valid_sibling_and_link(
        self,
        mod_workspace: Path,
    ) -> None:
        """A symlinked projection is never a text source; its target stays intact."""
        first, second = self._publication_inputs(mod_workspace)
        alias = second.with_suffix(".linked")
        second.rename(alias)
        second.symlink_to(alias)
        original = alias.read_bytes()

        report = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.that(report.files, eq=frozenset({first.relative_to(mod_workspace)}))

        tm.that(first.read_bytes(), eq=b'value = "after"\n')
        tm.ok(second.is_symlink())
        tm.that(second.read_bytes(), eq=original)
        tm.that(alias.read_bytes(), eq=original)

    def test_text_plans_publish_through_the_shared_owner(
        self,
        mod_workspace: Path,
    ) -> None:
        """Planned text rewrites publish as one batch through the shared owner."""
        first, second = self._publication_inputs(mod_workspace)
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=b'value = "after"\n',
                desired_mode=state.mode,
                owner="mod-text",
            )
            for state in (
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                for path in (first, second)
            )
        )
        tm.ok(u.Infra.publish_codegen_plans(mod_workspace, plans))
        for path in (first, second):
            tm.that(path.read_bytes(), eq=b'value = "after"\n')

    @staticmethod
    def test_scan_proves_rewrite_receipt_and_fixed_point(
        mod_workspace: Path,
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
            ),
        )
        sample = mod_workspace / "sample.py"
        # Derived, never frozen: the fixture owns the module's shape, so the
        # expected line is read from it (project law P0 — a test never hardcodes
        # a value its own source of truth can produce).
        expected_line = next(
            index
            for index, text in enumerate(
                sample.read_text(encoding="utf-8").splitlines(),
                start=1,
            )
            if "paths, timeout" in text
        )

        first = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=False,
                validate_receipts=True,
            ),
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
        # This optional migration precondition deliberately does not promise
        # idempotence once the invocation has consumed its exact matches.
        with pytest.raises(
            RuntimeError, match=r"expected 1 finding\(s\), scan produced 0"
        ):
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=True,
                validate_receipts=True,
            )
        # The rewrite is proven by what changed, not by freezing the fixture's
        # whole text: the elected call carries the replacement and the original
        # argument list is gone.
        rewritten = sample.read_text(encoding="utf-8")
        tm.that(rewritten, has="serialization_lock_execute(chunks, deadline)")
        tm.that(rewritten, lacks="serialization_lock_execute(paths, timeout)")

    @staticmethod
    @pytest.mark.parametrize("fix", [False, True])
    def test_scan_requires_declared_receipt_to_match_exactly(
        mod_workspace: Path,
        *,
        fix: bool,
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
            ),
        )
        original = (mod_workspace / "sample.py").read_bytes()
        with pytest.raises(RuntimeError, match=r"expected 2 finding\(s\), scan"):
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=fix,
                validate_receipts=True,
            )
        tm.that((mod_workspace / "sample.py").read_bytes(), eq=original)

    @staticmethod
    def test_load_rules_rejects_unknown_keys_and_duplicate_ids(
        mod_workspace: Path,
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
            ),
        )
        unknown = FlextInfraModTextGateEngine.load_rules(mod_workspace)
        tm.that(unknown.failure)
        tm.ok("unsupported" in str(unknown.error))

        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: first\n    find: 'alpha'\n"
                "  - id: first\n    find: 'beta'\n",
            ),
        )
        duplicate = FlextInfraModTextGateEngine.load_rules(mod_workspace)
        tm.that(duplicate.failure)
        tm.ok("duplicate text rule id" in str(duplicate.error))

        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: first\n    find: 'alpha'\n"
                "  - id: second\n    find: 'beta'\n",
            ),
        )
        valid = tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        tm.ok({"first", "second"} <= {rule.rule_id for rule in valid})

    @pytest.mark.parametrize("scope", ["include", "exclude"])
    @pytest.mark.parametrize(
        "declaration",
        [
            "'src/**'",
            "{'src/**': true}",
            "{}",
            "null",
            "42",
            "[42]",
            "[null]",
            "[false]",
            "['src/**', 42]",
            "['']",
            "['   ']",
        ],
    )
    def test_invalid_scope_rejects_loading_and_scanning_before_publication(
        self,
        mod_workspace: Path,
        scope: str,
        declaration: str,
    ) -> None:
        """Malformed scopes cannot broaden or suppress the authenticated batch."""
        first, second = self._publication_inputs(mod_workspace)
        outside = mod_workspace / "outside.py"
        tm.ok(u.Cli.atomic_write_text_file(outside, 'value = "before"\n'))
        paths = (first, second, outside)
        originals = tuple(path.read_bytes() for path in paths)
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: invalid-scope\n"
                f"    {scope}: {declaration}\n"
                "    find: 'before'\n"
                "    replace: 'after'\n",
            ),
        )
        diagnostic = f"text rule {scope} must be a list of non-empty strings"
        tm.fail(FlextInfraModTextGateEngine.load_rules(mod_workspace), has=diagnostic)
        for fix in (False, True):
            tm.fail(
                FlextInfraModTextGateEngine.scan(mod_workspace, fix=fix),
                has=diagnostic,
            )
            tm.that(tuple(path.read_bytes() for path in paths), eq=originals)

    def test_valid_scope_scan_and_fix_elect_the_same_sources(
        self,
        mod_workspace: Path,
    ) -> None:
        """Valid globs preserve excluded and out-of-scope source bytes."""
        first, second = self._publication_inputs(mod_workspace)
        outside = mod_workspace / "outside.py"
        tm.ok(u.Cli.atomic_write_text_file(outside, 'value = "before"\n'))
        preserved = (second.read_bytes(), outside.read_bytes())
        selected = first.relative_to(mod_workspace).as_posix()
        excluded = second.relative_to(mod_workspace).as_posix()
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: valid-scope\n"
                "    include: ['src/**']\n"
                f"    exclude: ['{excluded}']\n"
                "    find: 'before'\n"
                "    replace: 'after'\n"
                "    expected: 1\n",
            ),
        )
        tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        scanned = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=False,
                validate_receipts=True,
            ),
        )
        tm.that(first.read_text(encoding="utf-8"), eq='value = "before"\n')
        tm.that(
            tuple(entry.file.as_posix() for entry in scanned.entries),
            eq=(selected,),
        )
        applied = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=True,
                validate_receipts=True,
            ),
        )
        tm.that(applied, eq=scanned)
        tm.that(first.read_text(encoding="utf-8"), eq='value = "after"\n')
        tm.that((second.read_bytes(), outside.read_bytes()), eq=preserved)
        tm.that(
            tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False)).findings,
            eq=0,
        )

    @pytest.mark.parametrize("scopes", ["", "    include: []\n    exclude: []\n"])
    def test_omitted_and_empty_scopes_preserve_typed_defaults(
        self,
        mod_workspace: Path,
        scopes: str,
    ) -> None:
        """Absent scopes use typed defaults; explicit empty scopes override them."""
        paths = self._publication_inputs(mod_workspace)
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: scope-defaults\n"
                f"{scopes}"
                "    find: 'before'\n"
                "    replace: 'after'\n",
            ),
        )
        loaded = tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        rule = next(rule for rule in loaded if rule.rule_id == "scope-defaults")
        if not scopes:
            defaults = m.Infra.ModTextRule(rule_id=rule.rule_id, find=rule.find)
            tm.that(
                (rule.include, rule.exclude),
                eq=(defaults.include, defaults.exclude),
            )
            return
        tm.that((rule.include, rule.exclude), eq=((), ()))
        scanned = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False))
        applied = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.that(applied, eq=scanned)
        for path in paths:
            tm.that(path.read_text(encoding="utf-8"), eq='value = "after"\n')

    @staticmethod
    def test_include_and_exclude_globs_elect_exact_targets(
        mod_workspace: Path,
    ) -> None:
        """Glob election scopes the rewrite to the declared surfaces only."""
        package_dir = mod_workspace / "src" / "mod_workspace"
        tm.ok(u.Cli.ensure_dir(package_dir))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package_dir / "frozen.py",
                "LEGACY_PIN = '2026.9.17'\n",
            ),
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
            ),
        )
        first = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=False,
                validate_receipts=True,
            ),
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
            ),
        )
        excluded = tm.ok(
            FlextInfraModTextGateEngine.scan(
                mod_workspace,
                fix=False,
                validate_receipts=True,
            ),
        )
        tm.that(excluded.findings, eq=0)
