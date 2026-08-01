"""Owner-declared managed document conflict recovery tests."""

from __future__ import annotations

from flext_infra.codegen.managed_conflicts import FlextInfraCodegenManagedConflicts
from flext_tests import tm


class TestsFlextInfraCodegenManagedConflicts:
    """Prove conflict recovery remains bounded by the document SSOT."""

    def test_recovers_only_configured_toml_section(self) -> None:
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

        recovered = tm.ok(
            FlextInfraCodegenManagedConflicts.recover_toml(
                content, conflict_sections=("tool.uv",)
            )
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

    def test_rejects_conflict_outside_configured_toml_section(self) -> None:
        """Fail closed when the canonical owner did not declare the section."""
        content = (
            "[project]\n"
            "<<<<<<< HEAD\n"
            'name = "current"\n'
            "=======\n"
            'name = "incoming"\n'
            ">>>>>>> origin/0.12.0-dev\n"
        )

        result = FlextInfraCodegenManagedConflicts.recover_toml(
            content, conflict_sections=("tool.uv",)
        )

        tm.fail(result, has="outside owner-declared TOML sections: project")

    def test_preserves_clean_document_bytes(self) -> None:
        """Leave documents without conflict markers byte-identical."""
        content = '[tool.uv]\nlink-mode = "copy"\n'

        recovered = tm.ok(
            FlextInfraCodegenManagedConflicts.recover_toml(
                content, conflict_sections=("tool.uv",)
            )
        )

        tm.that(recovered, eq=content)
