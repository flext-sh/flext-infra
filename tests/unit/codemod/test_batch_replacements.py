"""Public replacement transport preserves generator authority and exact CAS.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import c, m, main, t
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.batch_replacements import FlextInfraModReplacements
from tests import tm, u


class TestsFlextInfraBatchReplacements:
    """Only authenticated authored bytes may receive engine-proposed edits."""

    @staticmethod
    def _scanned_consumer(
        root: Path,
    ) -> t.Quad[m.Infra.ModScanReport, Path, Path, Path]:
        """Scan a real public consumer against a locally declared rewrite.

        Returns:
            The admitted report and its consumer, rule and config paths.

        """
        rule_name = "publish-consumer-value"
        u.Tests.declare_codemod_rules(
            root,
            {
                rule_name: (
                    f"id: {rule_name}\n"
                    "language: Python\n"
                    "severity: warning\n"
                    "rule:\n"
                    "  pattern: '\"before\"'\n"
                    "fix: '\"after\"'\n"
                ),
            },
        )
        stem = u.derive_class_stem(root.name.replace("_", "-"))
        consumer = root / "public_consumer.py"
        consumer.write_text(
            '"""Public value consumer."""\n'
            "from __future__ import annotations\n"
            "from typing import ClassVar\n\n"
            f"class {stem}Consumer:\n"
            '    """Own a value observed by a real process."""\n'
            '    value: ClassVar[str] = "before"\n\n'
            f"print({stem}Consumer.value)\n"
            f'__all__ = ["{stem}Consumer"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        config_path = root / c.Infra.CODEMOD_CONFIG_RELPATH
        rule_path = config_path.parent / c.Cli.RULES_DIR_NAME / f"{rule_name}.yml"
        report = tm.ok(FlextInfraModGateEngine.scan(root, fix=False))
        return report, consumer, rule_path, config_path

    @staticmethod
    @pytest.mark.slow
    def test_admitted_report_publishes_the_real_consumer(mod_workspace: Path) -> None:
        """Reuse admitted bytes through the same public CAS publisher."""
        report, consumer, _, _ = TestsFlextInfraBatchReplacements._scanned_consumer(
            mod_workspace
        )
        tm.ok(FlextInfraModGateEngine.apply_report(mod_workspace, report))
        output = tm.ok(u.Cli.run_raw((sys.executable, "-I", str(consumer))))
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="after")
        published = consumer.read_bytes()
        tm.fail(FlextInfraModGateEngine.apply_report(mod_workspace, report))
        tm.that(consumer.read_bytes(), eq=published)

    @staticmethod
    @pytest.mark.slow
    def test_changed_companion_input_prevents_consumer_publication(
        mod_workspace: Path,
    ) -> None:
        """A changed captured companion rejects the entire unchanged scan report."""
        companion = mod_workspace / "companion.py"
        companion.write_text(
            '"""Independent public scan input."""\n'
            "from __future__ import annotations\n",
            encoding=c.DEFAULT_ENCODING,
        )
        report, consumer, _, _ = TestsFlextInfraBatchReplacements._scanned_consumer(
            mod_workspace
        )
        original = consumer.read_bytes()
        concurrent = companion.read_bytes() + b"\n# concurrent input edit\n"
        companion.write_bytes(concurrent)

        tm.fail(
            FlextInfraModGateEngine.apply_report(mod_workspace, report),
            has=str(companion),
        )
        tm.that(consumer.read_bytes(), eq=original)
        tm.that(companion.read_bytes(), eq=concurrent)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "mutation",
        [
            "missing-proof",
            "source-change",
            "source-add",
            "source-remove",
            "rule-change",
            "rule-add",
            "rule-remove",
            "config-change",
        ],
    )
    def test_admitted_report_rejects_changed_inputs(
        mod_workspace: Path,
        mutation: str,
    ) -> None:
        """Changed ownership or physical inputs never publish stale replacements."""
        report, consumer, rule_path, config_path = (
            TestsFlextInfraBatchReplacements._scanned_consumer(mod_workspace)
        )
        original = consumer.read_bytes()
        if mutation == "missing-proof":
            report = report.model_copy(update={"source_states": None})
        elif mutation == "source-change":
            consumer.write_bytes(original + b"\n# changed consumer\n")
        elif mutation == "source-add":
            (mod_workspace / "new_consumer.py").write_text(
                '"""New scanner input."""\n',
                encoding=c.DEFAULT_ENCODING,
            )
        elif mutation == "source-remove":
            consumer.unlink()
        elif mutation == "rule-change":
            rule_path.write_text(
                rule_path.read_text(encoding=c.DEFAULT_ENCODING) + "\n# changed rule\n",
                encoding=c.DEFAULT_ENCODING,
            )
        elif mutation == "rule-add":
            added = rule_path.with_name("new-consumer-rule.yml")
            added.write_text(
                "id: new-consumer-rule\nlanguage: Python\n"
                "severity: warning\nrule:\n  pattern: NEVER_MATCHED\n",
                encoding=c.DEFAULT_ENCODING,
            )
        elif mutation == "rule-remove":
            rule_path.unlink()
        else:
            config_path.write_text(
                config_path.read_text(encoding=c.DEFAULT_ENCODING)
                + "\n# changed scanner configuration\n",
                encoding=c.DEFAULT_ENCODING,
            )
        before = consumer.read_bytes() if consumer.exists() else None
        tm.fail(FlextInfraModGateEngine.apply_report(mod_workspace, report))
        tm.that(
            consumer.read_bytes() if consumer.exists() else None,
            eq=before,
        )

    @staticmethod
    def _report(
        path: Path,
        content: bytes,
        *,
        generated: bool = False,
        replacement: bytes = b"after",
        matched: bytes = b"before",
    ) -> m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence]:
        policy = path.parent / "pyproject.toml"
        if not policy.exists():
            policy.write_text(
                "[project]\nname = 'sample'\nversion = '1.0.0'\n"
                "[tool.ruff.lint]\nselect = ['F401', 'F821']\n",
            )
        path.write_bytes(content)
        state = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
        start = content.index(matched)
        offsets: t.JsonDict = {"start": start, "end": start + len(matched)}
        finding = m.Infra.ModOccurrence(
            rule_file=str(path.parent / "rule.yaml"),
            rule_id="fixture-rewrite",
            repository=path.parent.name,
            file=path,
            source_owner="generator" if generated else "authored",
            source_state=state,
            range={"byteOffset": offsets},
            text=matched.decode(),
            replacement=replacement.decode(),
            actionable=True,
            classification=c.Infra.ModScanFindingClass.ACTIONABLE,
            replacement_offsets=m.Infra.ModReplacementOffsets.model_validate(offsets),
        )
        return m.Infra.ModOccurrenceReport(
            files=frozenset({path}),
            entries=(finding,),
        )

    def test_utf8_replacements_use_engine_byte_offsets(self, tmp_path: Path) -> None:
        """Test utf8 replacements use engine byte offsets."""
        root = u.Tests.git_repository(tmp_path)
        path = root / "subject.py"
        original = '# ação\nvalue = "before"\n'.encode()
        report = self._report(path, original)
        tm.ok(FlextInfraModReplacements.publish(root, report))
        tm.that(path.read_bytes(), eq=original.replace(b"before", b"after"))

    def test_removed_references_leave_no_type_only_import_scaffold(
        self,
        tmp_path: Path,
    ) -> None:
        """Publishing a rewrite normalizes imports as well as formatting."""
        root = u.Tests.git_repository(tmp_path)
        path = root / "subject.py"
        original = (
            b"from __future__ import annotations\n\n"
            b"from typing import TYPE_CHECKING\n\n"
            b"if TYPE_CHECKING:\n    from pathlib import Path\n\n"
            b'value: Path = "before"\n__all__ = ("value",)\n'
        )
        report = self._report(path, original)
        statement = b'value: Path = "before"'
        start = original.index(statement)
        offsets: t.JsonDict = {"start": start, "end": start + len(statement)}
        finding = report.entries[0].model_copy(
            update={
                "text": statement.decode(),
                "replacement": 'value = "after"',
                "range": {"byteOffset": offsets},
                "replacement_offsets": m.Infra.ModReplacementOffsets.model_validate(
                    offsets
                ),
            }
        )
        report = report.model_copy(update={"entries": (finding,)})
        tm.ok(FlextInfraModReplacements.publish(root, report))
        tm.that(path.read_text(), lacks="TYPE_CHECKING")
        tm.that(path.read_text(), lacks="from pathlib import Path")
        tm.that(path.read_text(), has='value = "after"')
        tm.that(path.read_text(), has='__all__ = ("value",)')

    def test_existing_reexport_and_side_effect_import_survive_normalization(
        self,
        tmp_path: Path,
    ) -> None:
        """A fewer-findings cleanup never deletes an unchanged public binding."""
        root = u.Tests.git_repository(tmp_path)
        path = root / "subject.py"
        original = b'from pathlib import Path\nimport os\nvalue = "before"\n'
        tm.ok(FlextInfraModReplacements.publish(root, self._report(path, original)))
        output = tm.ok(
            u.Cli.run([
                sys.executable,
                "-I",
                "-c",
                (
                    "import runpy; "
                    f"exports = runpy.run_path({str(path)!r}); "
                    "print(exports['Path']('survives')); print(exports['os'].name)"
                ),
            ])
        )
        tm.that(output.stdout, has="survives")

    def test_generator_findings_remain_visible_and_unmodified(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generator findings remain visible and unmodified."""
        root = u.Tests.git_repository(tmp_path)
        path = root / "generated.py"
        original = b'value = "before"\n'
        report = self._report(path, original, generated=True)
        result = FlextInfraModReplacements.publish(root, report)
        tm.fail(result)
        tm.that(result.error, has=f"generator:{path}:fixture-rewrite")
        tm.that(report.findings, eq=1)
        tm.that(path.read_bytes(), eq=original)

    @pytest.mark.slow
    @pytest.mark.parametrize("selected", [False, True])
    def test_generator_evidence_never_blocks_authored_rewrites(
        self,
        mod_workspace: Path,
        capsys: pytest.CaptureFixture[str],
        *,
        selected: bool,
    ) -> None:
        """Generated findings block acceptance without blocking authored progress."""
        tm.ok(u.Tests.create_python_environment(mod_workspace))
        rule_id = "mixed-generator-boundary"
        u.Tests.declare_codemod_rules(
            mod_workspace,
            {
                rule_id: (
                    f"id: {rule_id}\nlanguage: Python\nseverity: warning\n"
                    'rule:\n  pattern: value = "before"\n'
                    'fix: value = "after"\n'
                ),
            },
        )
        stem = u.derive_class_stem(mod_workspace.name.replace("_", "-"))
        sources = {
            label: (
                (f"{c.Infra.AUTOGEN_HEADER}\n" if label == "generated" else "")
                + '"""Generator boundary fixture."""\n\n'
                + "from __future__ import annotations\n\n\n"
                + f"class {stem}{label.title()}:\n"
                + '    """Independent rewrite target."""\n\n'
                + '    value = "before"\n'
            )
            for label in ("authored", "generated")
        }
        for label, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(mod_workspace / f"{label}.py", source))
        applied = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=True,
                rule_ids=(rule_id,) if selected else None,
            )
        )
        entries = tuple(entry for entry in applied.entries if entry.rule_id == rule_id)
        tm.that(len(entries), eq=2)
        tm.that({entry.source_owner for entry in entries}, eq={"authored", "generator"})
        tm.that(all(entry.actionable for entry in entries), eq=True)
        tm.that(
            all(
                entry.classification is c.Infra.ModScanFindingClass.ACTIONABLE
                for entry in entries
            ),
            eq=True,
        )
        receipt = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        tm.that(receipt.command, eq=c.Infra.ModScanCommand.APPLY)
        tm.that(receipt.totals_by_rule[rule_id], eq=2)
        expected = tm.ok(
            u.Infra.publish_mod_scan_evidence(
                mod_workspace,
                applied,
                publication=m.Infra.ModScanPublication(
                    command=receipt.command, scope=receipt.scope
                ),
            )
        ).evidence
        tm.that(
            tuple(entry for entry in receipt.entries if entry.rule_id == rule_id),
            eq=tuple(entry for entry in expected.entries if entry.rule_id == rule_id),
        )
        authored = mod_workspace / "authored.py"
        generated = mod_workspace / "generated.py"
        tm.that(
            authored.read_text(encoding=c.DEFAULT_ENCODING),
            eq=sources["authored"].replace('value = "before"', 'value = "after"'),
        )
        tm.that(
            generated.read_bytes(), eq=sources["generated"].encode(c.DEFAULT_ENCODING)
        )
        exit_code = main([
            "refactor",
            "ast",
            "--repository-root",
            str(mod_workspace),
            "--apply",
            *(["--rules", rule_id] if selected else []),
        ])
        capture = capsys.readouterr()
        tm.that(exit_code, ne=0, msg=capture.out + capture.err)
        tm.that(capture.out + capture.err, lacks="fixed point verified")
        remaining = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes(),
        )
        blocking = tuple(
            entry for entry in remaining.entries if entry.rule_id == rule_id
        )
        tm.that(len(blocking), eq=1)
        tm.that(blocking[0].source_owner, eq="generator")
        tm.that(blocking[0].actionable, eq=True)
        tm.that(blocking[0].classification, eq=c.Infra.ModScanFindingClass.ACTIONABLE)
        tm.that(
            generated.read_bytes(), eq=sources["generated"].encode(c.DEFAULT_ENCODING)
        )

    @pytest.mark.parametrize(
        "changed",
        [b'value = "before"\n\n', b'value = "third-party"\n'],
    )
    def test_changed_source_is_not_overwritten(
        self,
        tmp_path: Path,
        changed: bytes,
    ) -> None:
        """Test changed source is not overwritten.

        A drifted source is deferred with a receipt: the publication succeeds
        for every authenticated file and the drifted bytes stay untouched —
        the next scan re-authenticates or stops reporting the finding.

        """
        root = u.Tests.git_repository(tmp_path)
        path = root / "subject.py"
        report = self._report(path, b'value = "before"\n')
        path.write_bytes(changed)
        tm.ok(FlextInfraModReplacements.publish(root, report))
        tm.that(path.read_bytes(), eq=changed)

    def test_missing_actionable_snapshot_is_rejected(self, tmp_path: Path) -> None:
        """Test missing actionable snapshot is rejected."""
        root = u.Tests.git_repository(tmp_path)
        path = root / "subject.py"
        report = self._report(path, b'value = "before"\n')
        finding = report.entries[0].model_copy(update={"source_state": None})
        invalid = report.model_copy(update={"entries": (finding,)})
        tm.fail(FlextInfraModReplacements.publish(root, invalid))

    @pytest.mark.parametrize(
        ("original", "replacement", "accepted"),
        [
            (b"value = before\n", "1", True),
            (b"before = 1\nvalue = before\n", "after", False),
            (b"value = before\nvalue = missing\n", "1\n\n# shifted", True),
            (b"value = before\nvalue = before\n", "another_missing", False),
            (b"before = missing\n", "after = missing\npeer", False),
        ],
    )
    def test_ruff_occurrences_judge_normalized_candidate_before_publication(
        self,
        tmp_path: Path,
        original: bytes,
        replacement: str,
        *,
        accepted: bool,
    ) -> None:
        """Rule reductions and line shifts pass; new occurrence identities fail."""
        root = u.Tests.git_repository(tmp_path)
        (root / "pyproject.toml").write_text(
            "[tool.ruff.lint]\nselect = ['F821']\n",
        )
        path = root / "subject.py"
        report = self._report(path, original)
        finding = report.entries[0].model_copy(update={"replacement": replacement})
        result = FlextInfraModReplacements.publish(
            root,
            report.model_copy(update={"entries": (finding,)}),
        )
        tm.that(result.success, eq=accepted)
        if accepted:
            tm.that(path.read_bytes(), ne=original)
        else:
            tm.that(result.error, has="F821")
            tm.that(path.read_bytes(), eq=original)

    def test_one_regressive_rule_rejects_the_whole_candidate(
        self, tmp_path: Path
    ) -> None:
        """A valid peer rewrite never publishes ahead of a rejected rule."""
        root = u.Tests.git_repository(tmp_path)
        good = root / "a_good.py"
        bad = root / "z_bad.py"
        good_before = b'value = "before"\n'
        bad_before = b"before = 1\nvalue = before\n"
        accepted = self._report(good, good_before).entries[0]
        rejected = self._report(bad, bad_before).entries[0]
        result = FlextInfraModReplacements.publish(
            root,
            m.Infra.ModOccurrenceReport(
                entries=(accepted, rejected),
                files=frozenset({good, bad}),
            ),
        )
        tm.fail(result)
        tm.that(result.error, has="F821")
        tm.that(good.read_bytes(), eq=good_before)
        tm.that(bad.read_bytes(), eq=bad_before)

    @staticmethod
    def test_emptied_statement_publishes_formatter_clean_file(
        tmp_path: Path,
    ) -> None:
        """An emptied statement fix publishes skeleton-free, format-clean bytes.

        The ban-test-suite-module-all rule rewrites its match to ``""``; the
        byte-splice leaves the source line blank and the mod circuit enforces
        canonical formatting on the first pass after applying.
        """
        root = u.Tests.git_repository(tmp_path)
        path = root / "tests" / "unit" / "test_demo.py"
        (root / "pyproject.toml").write_text(
            "[project]\nname = 'sample'\nversion = '1.0.0'\n"
            "[tool.ruff.lint]\nselect = ['F401', 'F821']\n",
        )
        path.parent.mkdir(parents=True)
        original = (
            b'"""Demo."""\n\n__all__ = ["X"]\n\n\ndef t() -> None:\n    assert True\n'
        )
        path.write_bytes(original)
        state = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
        statement = b'__all__ = ["X"]'
        start = original.index(statement)
        offsets: t.JsonDict = {"start": start, "end": start + len(statement)}
        finding = m.Infra.ModOccurrence(
            rule_file=str(root / "rule.yaml"),
            rule_id="ban-test-suite-module-all",
            repository=root.name,
            file=path,
            source_owner="authored",
            source_state=state,
            range={"byteOffset": offsets},
            text=statement.decode(),
            replacement="",
            actionable=True,
            classification=c.Infra.ModScanFindingClass.ACTIONABLE,
            replacement_offsets=m.Infra.ModReplacementOffsets.model_validate(offsets),
        )
        report = m.Infra.ModOccurrenceReport(
            files=frozenset({path}),
            entries=(finding,),
        )
        tm.ok(FlextInfraModReplacements.publish(root, report))
        tm.that(
            path.read_bytes(),
            eq=b'"""Demo."""\n\n\ndef t() -> None:\n    assert True\n',
        )

    @pytest.mark.parametrize(
        ("replacement", "accepted"),
        [
            (b"from pathlib import Path\nvalue = Path('after')", True),
            (b"value = Path('after')", False),
        ],
    )
    def test_candidate_owns_its_import_bindings(
        self, tmp_path: Path, replacement: bytes, *, accepted: bool
    ) -> None:
        """Publish complete imports; reject unbound names without invented bindings."""
        root = u.Tests.git_repository(tmp_path)
        path = root / "subject.py"
        original = b'value = "before"\n'
        report = self._report(
            path, original, matched=original.strip(), replacement=replacement
        )
        result = FlextInfraModReplacements.publish(root, report)
        tm.that(result.success, eq=accepted)
        if not accepted:
            tm.that(result.error, has="F821")
            tm.that(path.read_bytes(), eq=original)
            return
        published = path.read_bytes()
        tm.that(published.count(b"from pathlib import Path"), eq=1)
        tm.ok(u.Cli.run([sys.executable, "-I", str(path)]))
        tm.ok(FlextInfraModReplacements.publish(root, report))
        tm.that(path.read_bytes(), eq=published)
