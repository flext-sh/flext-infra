"""Public sed-by-list contract for the ``make mod`` text phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config, infra, m
from flext_infra.codemod import FlextInfraModTextGateEngine
from tests import c, tm, u


class TestsFlextInfraModTextGateEngine:
    """Exercise the declarative sed-by-list engine through its public scan."""

    @staticmethod
    def test_unsupported_declared_input_is_red_and_preserves_original_sources(
        mod_workspace: Path,
    ) -> None:
        """An unhandled configured input cannot masquerade as a zero-match run."""
        selected = mod_workspace / "selected.py"
        unsupported = mod_workspace / "declared.toml"
        tm.ok(u.Cli.atomic_write_text_file(selected, 'value = "before"\n'))
        tm.ok(u.Cli.atomic_write_text_file(unsupported, 'value = "before"\n'))
        before = unsupported.read_bytes()
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: unhandled-declaration\n"
                "    include: ['declared.toml']\n"
                "    find: 'before'\n"
                "    replace: 'after'\n"
                "  - id: supported-sibling\n"
                "    include: ['selected.py']\n"
                "    find: 'before'\n"
                "    replace: 'after'\n",
            ),
        )
        result = infra.mod_text(
            m.Infra.ModTextCommand(repository_root=mod_workspace, apply=True),
        )
        tm.fail(result)
        tm.that("unsupported input" in str(result.error), truth=True)
        tm.that(
            selected.read_text(encoding=c.DEFAULT_ENCODING) == 'value = "before"\n',
            truth=True,
        )
        tm.that(unsupported.read_bytes() == before, truth=True)
        tm.fail(FlextInfraModTextGateEngine.source_paths(mod_workspace))

    @staticmethod
    def test_yaml_method_replacement_preserves_public_class_behavior(
        mod_workspace: Path,
    ) -> None:
        """A real YAML rewrite retains class binding in a fresh Python process."""
        target = mod_workspace / "public_behavior.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                target,
                "class PublicUtility:\n"
                "    @staticmethod\n"
                "    def transform(value: str) -> str:\n"
                "        return value\n\n"
                "    @staticmethod\n"
                "    def downstream(value: str) -> str:\n"
                "        return PublicUtility.transform(value)\n\n"
                'if __name__ == "__main__":\n'
                '    print(PublicUtility.downstream("input"))\n',
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: replace-public-behavior\n"
                "    include: ['public_behavior.py']\n"
                "    find: '(?m)^(    )@staticmethod\\n"
                "    def transform\\(value: str\\) -> str:\\n"
                "        return value\\n\\n'\n"
                "    replace: |+\n"
                "      \\g<1>@staticmethod\n"
                "          def transform(value: str) -> str:\n"
                '              return value + "!"\n\n',
            ),
        )

        tm.ok(
            infra.mod_text(
                m.Infra.ModTextCommand(
                    repository_root=mod_workspace,
                    apply=True,
                ),
            ),
        )
        output = tm.ok(
            u.Cli.capture([sys.executable, str(target)], cwd=mod_workspace),
        )
        tm.that(output.strip(), eq="input!")
        before = target.read_bytes()
        tm.ok(
            infra.mod_text(
                m.Infra.ModTextCommand(
                    repository_root=mod_workspace,
                    apply=True,
                ),
            ),
        )
        tm.that(target.read_bytes(), eq=before)

    @staticmethod
    def test_failed_project_catalog_preserves_the_unpublished_member_plan(
        tmp_path: Path,
    ) -> None:
        """An invalid catalogue keeps independent desired effects unpublished."""
        root = tmp_path / "projects"
        member = u.Tests.WorktreeFixture.governed_workspace_with_member(root)
        catalogue = root / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        tm.ok(u.Cli.atomic_write_text_file(catalogue, "rules: [\n"))
        original = catalogue.read_bytes()
        target = member / "selected.py"
        tm.ok(u.Cli.atomic_write_text_file(target, 'value = "before"\n'))
        tm.ok(
            u.Cli.atomic_write_text_file(
                member / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: member-repair\n"
                "    include: ['selected.py']\n"
                "    find: 'before'\n"
                "    replace: 'after'\n",
            )
        )
        result = FlextInfraModTextGateEngine.scan(root, fix=True)
        tm.fail(result)
        tm.fail(FlextInfraModTextGateEngine.plan(root))
        tm.that(target.read_text(encoding="utf-8"), eq='value = "before"\n')
        tm.that(catalogue.read_bytes(), eq=original)

    @staticmethod
    def test_invalid_target_keeps_its_first_cause_and_unpublished_valid_effects(
        mod_workspace: Path,
    ) -> None:
        """One malformed target retains its cause without publishing valid siblings."""
        package = mod_workspace / "src" / "mod_workspace"
        invalid = package / "a_invalid.py"
        valid = package / "z_valid.py"
        malformed = 'value = ("before"\n'
        tm.ok(u.Cli.atomic_write_text_file(invalid, malformed))
        tm.ok(u.Cli.atomic_write_text_file(valid, 'value = "before"\n'))
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: independent-targets\n"
                "    include: ['src/**']\n"
                "    find: 'before'\n"
                "    replace: 'after'\n",
            )
        )
        with pytest.raises(SyntaxError):
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=False)
        tm.that(valid.read_text(encoding="utf-8"), eq='value = "before"\n')
        with pytest.raises(SyntaxError) as raised:
            infra.mod_text(
                m.Infra.ModTextCommand(repository_root=mod_workspace, apply=True)
            )
        tm.that(raised.value.filename, eq=str(invalid))
        tm.that(invalid.read_text(encoding="utf-8"), eq=malformed)
        with pytest.raises(SyntaxError):
            FlextInfraModTextGateEngine.plan(mod_workspace)
        tm.that(valid.read_text(encoding="utf-8"), eq='value = "before"\n')

    @staticmethod
    @pytest.mark.parametrize("change", ["remove", "change", "add"])
    def test_foreign_source_changes_do_not_veto_owned_publication(
        mod_workspace: Path, change: str
    ) -> None:
        """A real unrelated filesystem edit cannot reject the selected target."""
        package = mod_workspace / "src" / "mod_workspace"
        foreign = package / "a_foreign.py"
        target = package / "z_selected.py"
        added = package / "new_foreign.py"
        tm.ok(u.Cli.atomic_write_text_file(foreign, 'value = "foreign"\n'))
        tm.ok(u.Cli.atomic_write_text_file(target, 'value = "before"\n'))
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: owned-publication\n"
                f"    include: ['{target.relative_to(mod_workspace).as_posix()}']\n"
                "    find: 'before'\n"
                "    replace: 'after'\n",
            )
        )
        active = True
        armed = True

        def alter_foreign_source() -> None:
            """Apply one independent physical edit during the selected read."""
            nonlocal armed
            armed = False
            if change == "remove":
                foreign.unlink()
            elif change == "change":
                foreign.write_text('value = "independent"\n', encoding="utf-8")
            else:
                added.write_text('value = "independent"\n', encoding="utf-8")

        sys.addaudithook(
            lambda event, arguments: (
                alter_foreign_source()
                if active
                and armed
                and event == "open"
                and arguments
                and isinstance(arguments[0], str)
                and Path(arguments[0]).name == target.name
                else None
            )
        )
        try:
            tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        finally:
            active = False
        tm.fail(armed)
        tm.that(target.read_text(encoding="utf-8"), eq='value = "after"\n')
        if change == "remove":
            tm.fail(foreign.exists())
        elif change == "change":
            tm.that(foreign.read_text(encoding="utf-8"), eq='value = "independent"\n')
        else:
            tm.that(added.read_text(encoding="utf-8"), eq='value = "independent"\n')

    @staticmethod
    def test_external_consumer_inherits_provider_and_composes_local_rules(
        mod_workspace: Path,
    ) -> None:
        """A standalone consumer sees the packaged catalogue and its own overlay."""
        provider_root = config.ssot_config_dir().parent
        provider = tm.ok(FlextInfraModTextGateEngine.load_rules(provider_root))
        inherited = tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        tm.that(inherited, eq=provider)

        local_id = "consumer-owned-rewrite"
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                (
                    "rules:\n"
                    f"  - id: {local_id}\n"
                    "    include: ['src/**']\n"
                    "    find: 'before'\n"
                    "    replace: 'after'\n"
                ),
            ),
        )
        sample = mod_workspace / "src" / "mod_workspace" / "consumer.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, 'value = "before"\n'))

        composed = tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        tm.that(composed[:-1], eq=provider)
        tm.that(composed[-1].rule_id, eq=local_id)
        applied = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.ok(any(entry.rule_id == local_id for entry in applied.entries))
        tm.that(sample.read_text(encoding="utf-8"), eq='value = "after"\n')
        fixed_point = tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False))
        tm.that(fixed_point.actionable, eq=0)

    @staticmethod
    def test_distribution_selects_rules_before_required_markdown_inventory(
        mod_workspace: Path,
    ) -> None:
        """Only a rule selected by [project].name may require its source."""
        catalogue = mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        project_document = mod_workspace / c.PYPROJECT_FILENAME
        distribution = u.Infra.project_name_from_payload(
            project_document,
            u.Infra.pyproject_payload(project_document),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalogue,
                (
                    "rules:\n"
                    "  - id: selected-markdown-rule\n"
                    f"    distributions: [not-{distribution}]\n"
                    "    include: [docs/required.md]\n"
                    "    find: 'before'\n"
                    "    replace: 'after'\n"
                ),
            ),
        )
        tm.ok(infra.mod_text(m.Infra.ModTextCommand(repository_root=mod_workspace)))

        tm.ok(
            u.Cli.atomic_write_text_file(
                catalogue,
                (
                    "rules:\n"
                    "  - id: selected-markdown-rule\n"
                    f"    distributions: [{distribution}]\n"
                    "    include: [docs/required.md]\n"
                    "    find: 'before'\n"
                    "    replace: 'after'\n"
                ),
            ),
        )
        selected = infra.mod_text(m.Infra.ModTextCommand(repository_root=mod_workspace))
        tm.fail(selected, has="text Markdown include has no source")

    @staticmethod
    def test_public_mod_text_reselects_rules_after_project_identity_changes(
        mod_workspace: Path,
    ) -> None:
        """The public command must select rules from current project bytes."""
        document = mod_workspace / c.PYPROJECT_FILENAME
        distribution = u.Infra.project_name_from_payload(
            document,
            u.Infra.pyproject_payload(document),
        )
        catalogue = mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        tm.ok(
            u.Cli.atomic_write_text_file(
                catalogue,
                (
                    "rules:\n"
                    "  - id: identity-dependent-markdown\n"
                    f"    distributions: [{distribution}]\n"
                    "    include: [docs/identity-required.md]\n"
                    "    find: 'before'\n"
                    "    replace: 'after'\n"
                ),
            ),
        )
        request = m.Infra.ModTextCommand(repository_root=mod_workspace)
        tm.fail(infra.mod_text(request), has="text Markdown include has no source")

        original = document.read_text(encoding=c.DEFAULT_ENCODING)
        changed = original.replace(
            f'name = "{distribution}"',
            f'name = "changed-{distribution}"',
        )
        tm.fail(changed == original)
        tm.ok(u.Cli.atomic_write_text_file(document, changed))
        tm.ok(infra.mod_text(request))

        tm.ok(u.Cli.atomic_write_text_file(document, original))
        tm.fail(infra.mod_text(request), has="text Markdown include has no source")

    @staticmethod
    def test_declared_markdown_rule_replays_and_reaches_fixed_point(
        mod_workspace: Path,
    ) -> None:
        """An authored Markdown guide is an authenticated public text input."""
        guide = mod_workspace / "docs" / "guide.md"
        tm.ok(u.Cli.ensure_dir(guide.parent))
        tm.ok(u.Cli.atomic_write_text_file(guide, "Old guidance.\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: guide-contract\n"
                "    include: ['docs/*.md']\n"
                "    find: 'Old guidance\\.'\n"
                "    replace: 'Current guidance.'\n",
            ),
        )

        tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.that(guide.read_text(encoding="utf-8"), eq="Current guidance.\n")
        tm.that(
            tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False)).findings,
            eq=0,
        )

    @staticmethod
    def test_declared_markdown_symlink_fails_before_publication(
        mod_workspace: Path,
    ) -> None:
        """A declared guide cannot route publication through a symbolic link."""
        source = mod_workspace / "guide-source.md"
        tm.ok(u.Cli.atomic_write_text_file(source, "Old guidance.\n"))
        guide = mod_workspace / "docs" / "guide.md"
        tm.ok(u.Cli.ensure_dir(guide.parent))
        guide.symlink_to(source)
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: guide-contract\n"
                "    include: ['docs/guide.md']\n"
                "    find: 'Old guidance\\.'\n"
                "    replace: 'Current guidance.'\n",
            ),
        )

        tm.fail(
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=True),
            has="text Markdown source must be physical",
        )
        tm.that(source.read_text(encoding="utf-8"), eq="Old guidance.\n")

    @staticmethod
    def test_capture_guard_rejects_wrong_keyword_before_publication(
        mod_workspace: Path,
    ) -> None:
        """A broad regex cannot rewrite a different keyword by accident."""
        source = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "token = 1\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: guarded-keyword\n"
                "    include: ['sample.py']\n"
                "    find: '(?P<keyword>[a-z]+) = 1'\n"
                "    capture_equals: {keyword: secret}\n"
                "    replace: 'secret = 2'\n",
            ),
        )
        before = source.read_bytes()

        with pytest.raises(ValueError, match="capture keyword expected"):
            FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)

        tm.that(source.read_bytes(), eq=before)

    @staticmethod
    def test_capture_guard_accepts_declared_keyword_and_fixed_point(
        mod_workspace: Path,
    ) -> None:
        """A guarded rule rewrites once, then observes no further match."""
        source = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "secret = 1\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: guarded-keyword\n"
                "    include: ['sample.py']\n"
                "    find: '(?P<keyword>[a-z]+) = 1'\n"
                "    capture_equals: {keyword: secret}\n"
                "    replace: 'secret = 2'\n",
            ),
        )

        tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        tm.that(source.read_text(encoding="utf-8"), eq="secret = 2\n")
        tm.that(
            tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=False)).findings,
            eq=0,
        )

    @staticmethod
    def test_capture_guard_requires_a_declared_named_group(
        mod_workspace: Path,
    ) -> None:
        """An invalid catalogue fails before scanning any candidate source."""
        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: missing-capture\n"
                "    find: '[a-z]+ = 1'\n"
                "    capture_equals: {keyword: secret}\n",
            ),
        )

        tm.fail(
            FlextInfraModTextGateEngine.load_rules(mod_workspace),
            has="unknown regex captures",
        )
