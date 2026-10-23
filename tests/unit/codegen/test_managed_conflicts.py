"""Owner-declared managed document conflict recovery tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m, u
from tests import c, tm


class TestsFlextInfraManagedConflictRecovery:
    """Prove conflict recovery remains bounded by the document SSOT."""

    @staticmethod
    def test_managed_tool_paths_retain_declared_subtree_boundaries() -> None:
        """Classify the source segment without promoting ownership to its parent."""
        spec = m.Infra.ManagedFileSpec(
            path=Path(c.PYPROJECT_FILENAME),
            owner="codegen",
            policy="merge",
            conflict_sections=(
                "build-system",
                "tools.unowned",
                "toolkit.unowned",
                "tool.vendor.generated",
                "tool.other",
                "tool.vendor.generated.child",
                "tool.vendor.generated",
            ),
        )
        tm.that(
            spec.managed_tool_tables,
            eq=("vendor.generated", "other", "vendor.generated.child"),
        )
        declared = tm.ok(u.Infra.pyproject_managed_file())
        tm.that(
            declared.managed_tool_tables,
            eq=tuple(
                dict.fromkeys(
                    section.removeprefix("tool.")
                    for section in declared.conflict_sections
                    if section.startswith("tool.")
                )
            ),
        )

    @staticmethod
    def test_regeneration_preserves_custom_siblings_of_a_managed_subtree() -> None:
        """The real declaration keeps CUSTOM siblings beside the namespace table."""
        owned = u.Cli.toml_dot_path(*c.Infra.CONFORM_NAMESPACE_TABLE)
        parent = owned.rsplit(".", 1)[0]
        custom = (
            '[project]\nname = "fixture-project"\n'
            f'[{parent}.custom]\nlabel = "Preservar"\n'
        )
        source = (
            custom
            + f'[{owned}]\nstale = "owner must replace this"\n'
            + f"[{owned}.child]\nstale = true\n"
        )
        recovered = tm.ok(u.Infra.pyproject_regeneration_source(source))
        tm.that(recovered, eq=custom)
        tm.that(tm.ok(u.Infra.pyproject_regeneration_source(recovered)), eq=recovered)

    @staticmethod
    @pytest.mark.parametrize("render_owned", [True, False])
    def test_overlay_preserves_inline_custom_and_replaces_entire_owned_subtree(
        render_owned: bool,
    ) -> None:
        """Keep sibling data while replacing owned descendants and unknown keys."""
        rendered = '[project]\nname = "fixture-project"\n'
        if render_owned:
            rendered += (
                '[tool.vendor.generated]\nvalue = "new"\n'
                '[tool.vendor.generated.child]\nvalue = "current"\n'
            )
        live = (
            '[project]\nname = "fixture-project"\n'
            '[tool.vendor]\nlabel = "custom parent"\n'
            'generated = {value = "old", stale = true, child = {stale = true}}\n'
            'custom = {label = "Preservar", nested = {enabled = true}}\n'
            '[tool.vendor_extra]\nvalue = "unrelated"\n'
        )
        overlaid = tm.ok(
            u.Infra.overlay_preserved(
                rendered, live, managed_tool_tables=("vendor.generated",)
            )
        )
        payload = tm.not_none(u.Cli.toml_mapping_from_text(overlaid))
        vendor = tm.not_none(u.Cli.toml_mapping_path(payload, ("tool", "vendor")))
        tm.that(vendor["label"], eq="custom parent")
        tm.that(
            vendor["custom"],
            eq={"label": "Preservar", "nested": {"enabled": True}},
        )
        tm.that(
            u.Cli.toml_mapping_path(payload, ("tool", "vendor_extra")),
            eq={"value": "unrelated"},
        )
        if render_owned:
            tm.that(
                vendor["generated"],
                eq={"value": "new", "child": {"value": "current"}},
            )
        else:
            tm.that("generated" in vendor, eq=False)
        tm.that(
            tm.ok(
                u.Infra.overlay_preserved(
                    rendered, overlaid, managed_tool_tables=("vendor.generated",)
                )
            ),
            eq=overlaid,
        )

    @staticmethod
    @pytest.mark.parametrize("closing_quotes", [0, 1, 2])
    @pytest.mark.parametrize("delimiter", ['"""', "'''"])
    @pytest.mark.parametrize("newline", ["\n", "\r\n"])
    def test_tooling_regeneration_preserves_custom_multiline_values(
        delimiter: str,
        newline: str,
        closing_quotes: int,
    ) -> None:
        """A header inside custom data is never treated as managed policy."""
        spec = tm.ok(u.Infra.pyproject_managed_file())
        owned = f"tool.{spec.managed_tool_tables[0]}"
        custom = newline.join((
            "[project]",
            'name = "fixture-project"',
            f"description = {delimiter}",
            f"[{owned}]",
            delimiter + delimiter[0] * closing_quotes,
            "[dependency-groups]",
            'dev = ["fixture-dependency>=1"]',
            "",
        ))
        corrupt = custom + newline.join((
            f"[[{owned}.rows]]",
            "enabled = true",
            "enabled = false",
            "",
        ))

        recovered = tm.ok(u.Infra.pyproject_regeneration_source(corrupt))

        tm.ok(u.Cli.toml_mapping_from_text(custom) is not None)
        tm.that(recovered, eq=custom)
        tm.that(
            u.Cli.toml_mapping_from_text(recovered),
            eq=u.Cli.toml_mapping_from_text(custom),
        )

    @staticmethod
    def test_every_table_the_conform_pipeline_writes_is_recoverable() -> None:
        """Whatever the owner writes, the owner must be able to recover.

        The table is named by the same constant the conform pipeline writes
        through, so the writer and this declaration cannot drift. They did
        drift once: the pipeline gained a table while the declaration did not,
        and absorbing the integration base then dead-ended the superproject
        merge on the owner's own output.
        """
        pyproject = tm.ok(u.Infra.pyproject_managed_file())

        tm.that(
            u.Infra.toml_section_is_owned(
                u.Cli.toml_dot_path(*c.Infra.CONFORM_NAMESPACE_TABLE),
                pyproject.conflict_sections,
            ),
            eq=True,
        )

    @staticmethod
    def test_every_generated_pyproject_section_declares_recovery() -> None:
        """A section the owner renders must be recoverable, or a merge dead-ends.

        `per-file-ignores` is rendered from `tooling.yaml` exactly like the
        pytest and uv sections. Without the declaration, absorbing an
        integration base that still carries the previous lint projection left
        the superproject merge unresolvable through the canonical surface.
        """
        pyproject = tm.ok(u.Infra.pyproject_managed_file())
        tm.ok("tool.uv" in pyproject.conflict_sections)
        tm.ok("build-system" in pyproject.conflict_sections)
        tm.that(pyproject.preserve_project_keys, empty=False)
        tm.that(pyproject.overwrite_project_keys, empty=False)
        tm.that(
            set(pyproject.overwrite_project_keys).isdisjoint(
                pyproject.preserve_project_keys,
            ),
            eq=True,
        )

    @staticmethod
    def test_recovers_the_lint_policy_section() -> None:
        """Keep the owner's current lint projection over an absorbed base."""
        content = (
            "[tool.ruff.lint.per-file-ignores]\n"
            "<<<<<<< HEAD\n"
            '"**/__init__.py" = ["unused-import"]\n'
            "=======\n"
            '"**/.vulture_whitelist.py" = ["ALL"]\n'
            ">>>>>>> origin/0.12.0-dev\n"
        )

        recovered = tm.ok(
            u.Infra.recover_managed_toml(
                content,
                conflict_sections=("tool.ruff.lint.per-file-ignores",),
            ),
        )

        tm.that(
            recovered,
            eq=(
                "[tool.ruff.lint.per-file-ignores]\n"
                '"**/__init__.py" = ["unused-import"]\n'
            ),
        )

    @staticmethod
    def test_recovers_only_configured_toml_section() -> None:
        """Keep the current projection for a configured owner section."""
        content = (
            "[project]\n"
            'name = "fixture"\n'
            "\n"
            "[tool.uv]\n"
            "<<<<<<< HEAD\n"
            'link-mode = "copy"\n'
            "=======\n"
            'link-mode = "clone"\n'
            'required-version = "==0.11.32"\n'
            ">>>>>>> origin/0.12.0-dev\n"
            "\n"
            "[tool.ruff]\n"
            "line-length = 100\n"
        )

        recovered: str = tm.ok(
            u.Infra.recover_managed_toml(content, conflict_sections=("tool.uv",)),
        )

        tm.that(
            recovered,
            eq=(
                "[project]\n"
                'name = "fixture"\n'
                "\n"
                "[tool.uv]\n"
                'link-mode = "copy"\n'
                "\n"
                "[tool.ruff]\n"
                "line-length = 100\n"
            ),
        )

    @staticmethod
    def test_rejects_conflict_outside_configured_toml_section() -> None:
        """Fail closed when the canonical owner did not declare the section."""
        content = (
            "[project]\n"
            "<<<<<<< HEAD\n"
            'name = "current"\n'
            "=======\n"
            'name = "incoming"\n'
            ">>>>>>> origin/0.12.0-dev\n"
        )

        result = u.Infra.recover_managed_toml(content, conflict_sections=("tool.uv",))

        tm.fail(result, has="outside owner-declared TOML sections: project")

    @staticmethod
    def test_preserves_clean_document_bytes() -> None:
        """Leave documents without conflict markers byte-identical."""
        content = '[tool.uv]\nlink-mode = "copy"\n'

        recovered: str = tm.ok(
            u.Infra.recover_managed_toml(content, conflict_sections=("tool.uv",)),
        )

        tm.that(recovered, eq=content)

    @staticmethod
    def test_recovery_tracks_content_and_section_ownership_changes() -> None:
        """Repeated reads never reuse validity or recovery for different inputs."""
        clean = '[tool.fixture]\nvalue = "first"\n'
        duplicated = clean + 'value = "first"\n'
        for _ in range(2):
            tm.that(
                tm.ok(
                    u.Infra.recover_managed_toml(
                        clean,
                        conflict_sections=("tool.fixture",),
                    )
                ),
                eq=clean,
            )
            tm.that(
                tm.ok(
                    u.Infra.recover_managed_toml(
                        duplicated,
                        conflict_sections=("tool.fixture",),
                    )
                ),
                eq=clean,
            )
            tm.that(
                tm.ok(
                    u.Infra.recover_managed_toml(
                        duplicated,
                        conflict_sections=("tool.other",),
                    )
                ),
                eq=duplicated,
            )

    @staticmethod
    def test_recovers_identical_managed_multiline_assignments() -> None:
        """Regeneration can read identical duplicated projection assignments."""
        assignment = 'value = [\n  "first",\n  "second",\n]\n'
        content = "[tool.fixture]\n" + assignment + assignment
        recovered = tm.ok(
            u.Infra.recover_managed_toml(
                content,
                conflict_sections=("tool.fixture",),
            ),
        )
        tm.that(recovered, eq="[tool.fixture]\n" + assignment)
        tm.that(u.Cli.toml_mapping_from_text(recovered), none=False)

    @staticmethod
    def test_rejects_divergent_managed_assignments() -> None:
        """A duplicate with unique content requires adjudication, not a choice."""
        result = u.Infra.recover_managed_toml(
            '[tool.fixture]\nvalue = "first"\nvalue = "second"\n',
            conflict_sections=("tool.fixture",),
        )
        tm.fail(result, has="divergent managed TOML assignment")

    @staticmethod
    def test_preserves_unmanaged_duplicate_assignments() -> None:
        """An undeclared table stays untouched and remains invalid for its owner."""
        content = '[tool.custom]\nvalue = "first"\nvalue = "first"\n'
        recovered = tm.ok(
            u.Infra.recover_managed_toml(
                content,
                conflict_sections=("tool.fixture",),
            ),
        )
        tm.that(recovered, eq=content)
        tm.that(u.Cli.toml_mapping_from_text(recovered), none=True)

    @staticmethod
    def test_preserves_distinct_array_table_assignments() -> None:
        """Repeated array tables own distinct assignments, not duplicate keys."""
        content = (
            '[tool.fixture]\nvalue = "parent"\n'
            '[[tool.fixture.items]]\nvalue = "first"\n'
            '[[tool.fixture.items]]\nvalue = "second"\n'
        )
        recovered = tm.ok(
            u.Infra.recover_managed_toml(
                content,
                conflict_sections=("tool.fixture",),
            ),
        )
        tm.that(recovered, eq=content)
        tm.that(u.Cli.toml_mapping_from_text(recovered), none=False)

    @staticmethod
    def test_preserves_valid_commented_table_headers() -> None:
        """Valid external TOML syntax is never rewritten by managed recovery."""
        content = (
            '[tool.fixture]\nvalue = "parent"\n'
            '[[tool.fixture.items]] # first item\nvalue = "first"\n'
            '[[tool.fixture.items]] # second item\nvalue = "second"\n'
        )
        recovered = tm.ok(
            u.Infra.recover_managed_toml(
                content,
                conflict_sections=("tool.fixture",),
            ),
        )
        tm.that(recovered, eq=content)
