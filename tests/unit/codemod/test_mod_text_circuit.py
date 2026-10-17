"""Public sed-by-list contract for the ``make mod`` text phase.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from typing_extensions import TypeForm

from flext_infra import c, config, infra, m, p, r, t
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from flext_infra.codemod import FlextInfraModTextGateEngine
from tests import tm, u


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
        assert result.error_data is not None
        wire = u.type_adapter(TypeForm(tuple[t.JsonMapping, ...])).validate_json(
            tm.ok(u.Cli.json_dumps(result.error_data["issues"])),
        )
        issues = u.type_adapter(TypeForm(tuple[m.Infra.Issue, ...])).validate_json(
            tm.ok(
                u.Cli.json_dumps(
                    [
                        {
                            key: value
                            for key, value in issue.items()
                            if key not in m.Infra.Issue.model_computed_fields
                        }
                        for issue in wire
                    ],
                ),
            ),
        )
        tm.that(
            any(
                issue.file == str(unsupported)
                and issue.code == c.Infra.ToolOutcome.ERROR.value
                for issue in issues
            ),
            eq=True,
        )
        tm.that(isinstance(result.exception, ValueError), eq=True)
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
        _report, analysis = tm.ok(FlextInfraModTextGateEngine.plan(root))
        tm.that(any(plan.path == target for plan in analysis.files), eq=True)
        tm.that(analysis.issues, empty=False)
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
        diagnostic = FlextInfraModTextGateEngine.scan(mod_workspace, fix=False)
        tm.fail(diagnostic)
        tm.that(isinstance(diagnostic.exception, SyntaxError), eq=True)
        tm.that(valid.read_text(encoding="utf-8"), eq='value = "before"\n')
        result = infra.mod_text(
            m.Infra.ModTextCommand(repository_root=mod_workspace, apply=True)
        )
        tm.fail(result)
        exception = result.exception
        assert isinstance(exception, SyntaxError)
        tm.that(exception.filename, eq=str(invalid))
        tm.that(invalid.read_text(encoding="utf-8"), eq=malformed)
        _report, analysis = tm.ok(FlextInfraModTextGateEngine.plan(mod_workspace))
        tm.that(any(plan.path == valid for plan in analysis.files), eq=True)
        tm.that(isinstance(analysis.exception, SyntaxError), eq=True)
        tm.that(valid.read_text(encoding="utf-8"), eq='value = "before"\n')
        metadata = result.error_data
        assert metadata is not None
        tm.that(
            u.type_adapter(TypeForm(t.StrTuple)).validate_python(
                metadata["written_files"]
            ),
            eq=(),
        )

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
        tm.that(armed, eq=False)
        tm.that(target.read_text(encoding="utf-8"), eq='value = "after"\n')
        if change == "remove":
            tm.that(foreign.exists(), eq=False)
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
        tm.that(any(entry.rule_id == local_id for entry in applied.entries), eq=True)
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
        tm.that(changed == original, eq=False)
        tm.ok(u.Cli.atomic_write_text_file(document, changed))
        tm.ok(infra.mod_text(request))

        tm.ok(u.Cli.atomic_write_text_file(document, original))
        tm.fail(infra.mod_text(request), has="text Markdown include has no source")

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

        rejected = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.fail(rejected, has="capture keyword expected")
        tm.that(isinstance(rejected.exception, ValueError), eq=True)

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

        rejected = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.fail(rejected, has=str(first))
        native = tm.not_none(rejected.exception)
        tm.that(isinstance(native, SyntaxError), eq=True)
        if isinstance(native, SyntaxError):
            tm.that(native.filename, eq=str(first))
            tm.that(native.text, has="value =")
        tm.that(native.__traceback__ is not None, eq=True)

        tm.that((first.read_bytes(), second.read_bytes()), eq=originals)

    @staticmethod
    def _publication_inputs(root: Path) -> t.Pair[Path, Path]:
        """Declare two authored inputs and one exact text rewrite catalogue.

        Returns:
            The resulting ``t.Pair[Path, Path]``.

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
        _report, analysis = tm.ok(FlextInfraModTextGateEngine.plan(
            mod_workspace, sources=working, source_states=states,
        ))
        tm.that(analysis.issues, empty=True)
        targets = {plan.path: plan for plan in analysis.files}
        for path in (first, second):
            tm.that(targets[path].before, eq=next(state for state in states if state.path == path))
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=original[path])
            tm.that(tm.not_none(targets[path].desired_content).decode(c.DEFAULT_ENCODING),
                    eq=working[path].replace("before", "after"))
        tm.that(working, eq=frozen)
        virtual = first.parent / "planned" / "candidate.py"
        absence = tm.ok(u.Cli.atomic_plan_directory_chain(virtual.parent))
        declaration = m.Infra.CodegenFilePlan(
            project=mod_workspace, path=virtual, before=absence,
            desired_content=original[first].encode(c.DEFAULT_ENCODING),
            desired_mode=tm.not_none(next(state.mode for state in states if state.path == first)),
            source_states=states,
        )
        _report, candidate = tm.ok(FlextInfraModTextGateEngine.plan(
            mod_workspace,
            sources={**working, virtual: original[first]},
            source_states=states, declared_files=(declaration,),
        ))
        tm.that(candidate.issues, empty=True)
        virtual_plan = next(plan for plan in candidate.files if plan.path == virtual)
        tm.that(virtual_plan.before, eq=absence)
        tm.that(virtual_plan.desired_content, eq=original[first].replace("before", "after").encode(c.DEFAULT_ENCODING))
        tm.that(virtual.parent.exists(), eq=False)
        _report, physical = tm.ok(FlextInfraModTextGateEngine.plan(mod_workspace))
        tm.ok(FlextInfraModTextGateEngine.scan(mod_workspace, fix=True))
        for plan in physical.files:
            tm.that(plan.path.read_bytes(), eq=plan.desired_content)
        _report, fixed = tm.ok(FlextInfraModTextGateEngine.plan(mod_workspace))
        tm.that(fixed.files, empty=True)

    def test_generated_destination_keeps_the_text_candidate_unpublished(
        self,
        mod_workspace: Path,
    ) -> None:
        """A rejected generated target leaves authored siblings unpublished."""
        first, second = self._publication_inputs(mod_workspace)
        generated = f'{c.Infra.AUTOGEN_HEADERS[0]}\nvalue = "before"\n'
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
        """A decoding failure retains its native cause and unpublished sibling."""
        first, second = self._publication_inputs(mod_workspace)
        second.write_bytes(b"\xff")
        result = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.fail(result)
        tm.that(isinstance(result.exception, UnicodeDecodeError), eq=True)

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
        rejected = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.fail(rejected, has=str(second))
        native = rejected.exception
        assert isinstance(native, SyntaxError)
        tm.that(native.args, eq=expected.value.args)
        tm.that(native.filename, eq=expected.value.filename)
        tm.that(native.__traceback__ is not None, eq=True)
        tm.that(expected.value.__traceback__ is not None, eq=True)

        tm.that(first.read_bytes(), eq=b'value = "before"\n')
        tm.that(second.read_bytes(), eq=original_second)

    def test_linked_destination_failure_preserves_valid_sibling_and_link(
        self,
        mod_workspace: Path,
    ) -> None:
        """A symlink cannot impersonate an authenticated physical destination."""
        first, second = self._publication_inputs(mod_workspace)
        alias = second.with_suffix(".linked")
        second.rename(alias)
        second.symlink_to(alias)
        original = first.read_bytes()

        result = FlextInfraModTextGateEngine.scan(mod_workspace, fix=True)
        tm.fail(result, has="regular file")

        tm.that(first.read_bytes(), eq=b'value = "before"\n')
        tm.that(second.is_symlink(), eq=True)
        tm.that(second.read_bytes(), eq=original)
        tm.that(alias.read_bytes(), eq=original)

    def test_project_identity_change_rejects_authenticated_text_publication(
        self,
        mod_workspace: Path,
    ) -> None:
        """A changed dependency rejects its target and preserves an independent gain."""
        first, second = self._publication_inputs(mod_workspace)
        original_source = first.read_bytes()
        document = mod_workspace / c.PYPROJECT_FILENAME
        identity = tm.ok(u.Cli.atomic_read_binary_file_state(document, required=True))
        source = tm.ok(u.Cli.atomic_read_binary_file_state(first, required=True))
        sibling = tm.ok(u.Cli.atomic_read_binary_file_state(second, required=True))
        distribution = u.Infra.project_name_from_payload(
            document,
            u.Infra.pyproject_payload(document),
        )
        original_document = document.read_text(encoding="utf-8")
        changed_document = original_document.replace(
            f'name = "{distribution}"',
            f'name = "changed-{distribution}"',
        )
        tm.that(changed_document == original_document, eq=False)
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=mod_workspace),
        )
        roots = {"@mod-text": mod_workspace}
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.MOD_TEXT,
            files=(
                m.Infra.CodegenFilePlan(
                    project=mod_workspace,
                    path=first,
                    before=source,
                    desired_content=b'value = "after"\n',
                    desired_mode=source.mode,
                    source_states=(identity, source),
                    owner="mod-text",
                ),
                m.Infra.CodegenFilePlan(
                    project=mod_workspace,
                    path=second,
                    before=sibling,
                    desired_content=b'value = "after"\n',
                    desired_mode=sibling.mode,
                    source_states=(sibling,),
                    owner="mod-text",
                ),
            ),
            inputs=(identity, source, sibling),
        )

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            tm.ok(u.Cli.atomic_write_text_file(document, changed_document))
            return transaction.publish_file_phase_locked(
                scope,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                ),
            )

        rejected = transaction.run_files_locked(roots, publish)
        tm.fail(rejected, has="generation authenticated state changed")
        tm.that(first.read_bytes(), eq=original_source)
        tm.that(second.read_bytes(), eq=sibling.content)
        tm.that(document.read_text(encoding="utf-8"), eq=changed_document)

    def test_same_phase_dependency_uses_the_accepted_publication_receipt(
        self,
        mod_workspace: Path,
    ) -> None:
        """A later target can consume an earlier target's authenticated new state."""
        first, second = self._publication_inputs(mod_workspace)
        first_state = tm.ok(u.Cli.atomic_read_binary_file_state(first, required=True))
        second_state = tm.ok(u.Cli.atomic_read_binary_file_state(second, required=True))
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=b'value = "after"\n',
                desired_mode=state.mode,
                source_states=(first_state,)
                if state.path == first
                else (first_state, second_state),
                owner="mod-text",
            )
            for state in (first_state, second_state)
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.MOD_TEXT,
            files=plans,
            inputs=(first_state, second_state),
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=mod_workspace)
        )
        roots = {"@mod-text": mod_workspace}

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            return transaction.publish_file_phase_locked(
                scope,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                ),
            )

        tm.ok(transaction.run_files_locked(roots, publish))
        for path in (first, second):
            tm.that(path.read_bytes(), eq=b'value = "after"\n')

    @pytest.mark.parametrize("raise_failure", [False, True])
    def test_text_phase_validation_failure_preserves_original_files(
        self,
        mod_workspace: Path,
        *,
        raise_failure: bool,
    ) -> None:
        """A complete staged consumer fails before any live target is modified."""
        paths = self._publication_inputs(mod_workspace)
        states = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in paths
        )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=b'value = "after"\n',
                desired_mode=state.mode,
                source_states=(state,),
                owner="mod-text",
            )
            for state in states
        )
        analysis = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.MOD_TEXT,
            files=plans,
            inputs=states,
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=mod_workspace),
        )
        roots = {"@mod-text": mod_workspace}
        failure = RuntimeError("text publication acceptance rejected")

        def reject_candidate(
            session: m.Infra.CodegenTransactionSession,
            staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            candidates = tuple(
                tm.not_none(publication.replacement).path for publication in staged
            )
            consumed = tm.ok(
                u.Cli.run_raw(
                    (
                        sys.executable,
                        "-c",
                        (
                            "import runpy, sys; "
                            "assert all(runpy.run_path(path)['value'] == 'after' "
                            "for path in sys.argv[1:])"
                        ),
                        *(str(candidate) for candidate in candidates),
                    ),
                    cwd=session.plan.layout.scope_root,
                ),
            )
            tm.that(u.Cli.process_succeeded(consumed.outcome), eq=True)
            for state in states:
                tm.that(state.path.read_bytes(), eq=state.content)
            if raise_failure:
                raise failure
            return r[m.Infra.CodegenTransactionSession].fail(
                str(failure),
                exception=failure,
            )

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            return transaction.publish_file_phase_locked(
                scope,
                roots,
                analysis,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=(),
                    staged_validator=reject_candidate,
                ),
            )

        if raise_failure:
            with pytest.raises(RuntimeError) as raised:
                transaction.run_files_locked(roots, publish)
            tm.that(raised.value is failure, eq=True)
        else:
            result = transaction.run_files_locked(roots, publish)
            tm.fail(result, has="text publication acceptance rejected")
        for state in states:
            tm.that(state.path.read_bytes(), eq=state.content)
        tm.that(tuple(mod_workspace.rglob("*.semantic-staging")), empty=True)

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
        rejected = FlextInfraModTextGateEngine.scan(
            mod_workspace,
            fix=True,
            validate_receipts=True,
        )
        tm.fail(rejected, has="expected 1 finding(s), scan produced 0")
        tm.that(isinstance(rejected.exception, RuntimeError), eq=True)
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
        rejected = FlextInfraModTextGateEngine.scan(
            mod_workspace,
            fix=fix,
            validate_receipts=True,
        )
        tm.fail(rejected, has="expected 2 finding(s), scan")
        tm.that(isinstance(rejected.exception, RuntimeError), eq=True)
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
        tm.that("unsupported" in str(unknown.error), eq=True)

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
        tm.that("duplicate text rule id" in str(duplicate.error), eq=True)

        tm.ok(
            u.Cli.atomic_write_text_file(
                mod_workspace / c.Infra.CODEMOD_TEXT_RULES_RELPATH,
                "rules:\n"
                "  - id: first\n    find: 'alpha'\n"
                "  - id: second\n    find: 'beta'\n",
            ),
        )
        valid = tm.ok(FlextInfraModTextGateEngine.load_rules(mod_workspace))
        tm.that({"first", "second"} <= {rule.rule_id for rule in valid}, eq=True)

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
