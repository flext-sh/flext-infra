"""Project-owned ignore patterns: declaration, composition, and rendering.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import tm

if TYPE_CHECKING:
    from tests import t


class TestsFlextInfraProjectGitignorePatterns:
    """A project declares the ignores the fleet scaffold cannot know."""

    @staticmethod
    def _project(root: Path, documents: t.MappingKV[str, str]) -> Path:
        root.mkdir(parents=True)
        (root / "config").mkdir()
        for name, body in documents.items():
            (root / "config" / name).write_text(body, encoding="utf-8")
        return root

    def test_declared_patterns_render_as_one_project_section(
        self,
        tmp_path: Path,
    ) -> None:
        """Test declared patterns render as one project section."""
        root = self._project(
            tmp_path / "project",
            {
                "tooling.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    patterns:\n"
                    "      - .dmypy/\n      - mcp/generated/*\n"
                    "      - '!mcp/generated/.gitkeep'\n"
                ),
            },
        )

        rendered = FlextInfraCodegenConform.render_project_gitignore(
            config.Infra.codegen,
            profile=c.Infra.MakeProfile.STANDALONE,
            project_name=root.name,
            project_dir=root,
        )

        text = tm.ok(rendered)
        section = text.index(c.Infra.GITIGNORE_PROJECT_SECTION_NAME)
        tm.that(
            text.index(".dmypy/", section) < text.index("mcp/generated/*", section),
            truth=True,
        )
        tm.that("!mcp/generated/.gitkeep" in text[section:], truth=True)

    def test_patterns_compose_across_documents_without_duplicates(
        self,
        tmp_path: Path,
    ) -> None:
        """Test patterns compose across documents without duplicates."""
        root = self._project(
            tmp_path / "project",
            {
                "one.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    patterns: [.dmypy/, logs/]\n"
                ),
                "two.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    patterns: [logs/, .serena/]\n"
                ),
            },
        )

        resolved = u.Infra.load_project_managed_artifacts(root)

        patterns = tm.ok(resolved).artifacts.Gitignore.patterns
        tm.that(sorted(patterns) == [".dmypy/", ".serena/", "logs/"], truth=True)

    def test_absent_declaration_adds_no_section(self, tmp_path: Path) -> None:
        """Test absent declaration adds no section."""
        root = self._project(
            tmp_path / "project",
            {"tooling.yaml": "ManagedArtifacts: {}\n"},
        )

        rendered = FlextInfraCodegenConform.render_project_gitignore(
            config.Infra.codegen,
            profile=c.Infra.MakeProfile.STANDALONE,
            project_name=root.name,
            project_dir=root,
        )

        tm.that(
            c.Infra.GITIGNORE_PROJECT_SECTION_NAME not in tm.ok(rendered), truth=True
        )

    def test_empty_pattern_is_rejected(self, tmp_path: Path) -> None:
        """Test empty pattern is rejected."""
        root = self._project(
            tmp_path / "project",
            {"tooling.yaml": "ManagedArtifacts:\n  Gitignore:\n    patterns: ['']\n"},
        )

        with pytest.raises(m.ValidationError):
            u.Infra.load_project_managed_artifacts(root)

    @staticmethod
    def _external_project(root: Path) -> Path:
        """Declare marker ownership without copying external destinations.

        Returns:
            The resulting ``Path``.

        """
        return TestsFlextInfraProjectGitignorePatterns._project(
            root,
            {
                "tooling.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    preserved_blocks:\n"
                    "      - begin: '# BEGIN external projection'\n"
                    "        end: '# END external projection'\n"
                ),
            },
        )

    def test_external_block_survives_render_with_original_bytes(
        self,
        tmp_path: Path,
    ) -> None:
        """The external generator retains exclusive ownership of its block."""
        root = self._external_project(tmp_path / "project")
        external = (
            "# BEGIN external projection\r\n"
            "/projection/a\r\n"
            "/projection/b\r\n"
            "# END external projection\r\n"
        )
        (root / ".gitignore").write_bytes(("old policy\n\n" + external).encode())

        first = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )
        template = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
            ),
        )
        planned = tm.ok(
            FlextInfraCodegenConform.compose_project_artifact(
                root,
                c.Infra.GITIGNORE,
                template,
            ),
        )
        tm.that(planned.rendered == first, truth=True)
        tm.that(external in first, truth=True)
        tm.that("old policy" not in first, truth=True)
        (root / ".gitignore").write_bytes(first.encode())
        second = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )
        tm.that(second.encode() == first.encode(), truth=True)

    def test_runtime_policy_survives_preserved_negation(self, tmp_path: Path) -> None:
        """Git enforces local-artifact policy after retaining an external whitelist."""
        root = self._external_project(tmp_path / "project")
        tm.ok(u.Infra.git_init(m.Infra.GitRepoRequest(repo_root=root)))
        relative = Path("runtime-binding.json")
        artifact = m.Infra.ManagedFileSpec(
            path=relative,
            owner=c.Infra.CODEGEN_OWNER_VSCODE,
            policy="merge",
            tracking="runtime-local",
        )
        codegen = config.Infra.codegen.model_copy(
            update={"managed_files": (artifact,)},
        )
        external = (
            "# BEGIN external projection\n"
            f"!/{relative.as_posix()}\n"
            "# END external projection\n"
        )
        ignore = root / c.Infra.GITIGNORE
        ignore.write_text(external, encoding=c.DEFAULT_ENCODING)
        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )
        tm.that(external in rendered, truth=True)
        ignore.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        observed = tm.ok(
            u.Cli.run(
                (c.Infra.GIT, "check-ignore", "--no-index", relative.as_posix()),
                cwd=root,
            ),
        )
        tm.that(observed.stdout.strip(), eq=relative.as_posix())
        repeated = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )
        tm.that(repeated, eq=rendered)

    @pytest.mark.parametrize(
        "current",
        [
            "# BEGIN external projection\n/only-start\n",
            "# END external projection\n",
            "# END external projection\n# BEGIN external projection\n",
            (
                "# BEGIN external projection\n# BEGIN external projection\n"
                "# END external projection\n"
            ),
            "# BEGIN external projection extra\n# END external projection\n",
        ],
    )
    def test_malformed_external_block_fails_without_rewriting(
        self,
        tmp_path: Path,
        current: str,
    ) -> None:
        """Incomplete, duplicate and modified delimiters never get normalized."""
        root = self._external_project(tmp_path / "project")
        (root / ".gitignore").write_text(current, encoding="utf-8")

        result = FlextInfraCodegenConform.render_project_gitignore(
            config.Infra.codegen,
            profile=c.Infra.MakeProfile.STANDALONE,
            project_name=root.name,
            project_dir=root,
        )

        tm.that(result.failure, truth=True)
        tm.that(
            (root / ".gitignore").read_text(encoding="utf-8") == current, truth=True
        )

    def test_undeclared_external_block_is_not_retained(self, tmp_path: Path) -> None:
        """Only the project's typed configuration delegates block ownership."""
        root = self._project(
            tmp_path / "project",
            {"tooling.yaml": "ManagedArtifacts: {}\n"},
        )
        (root / ".gitignore").write_text(
            "# BEGIN external projection\n/projection/a\n# END external projection\n",
            encoding="utf-8",
        )

        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )

        tm.that("# BEGIN external projection" not in rendered, truth=True)

    def test_overlapping_declared_blocks_fail(self, tmp_path: Path) -> None:
        """Nested ownership regions are ambiguous and cannot be composed."""
        root = self._project(
            tmp_path / "project",
            {
                "tooling.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    preserved_blocks:\n"
                    "      - begin: '# BEGIN outer'\n        end: '# END outer'\n"
                    "      - begin: '# BEGIN inner'\n        end: '# END inner'\n"
                ),
            },
        )
        (root / ".gitignore").write_text(
            "# BEGIN outer\n# BEGIN inner\n/owned\n# END inner\n# END outer\n",
            encoding="utf-8",
        )

        result = FlextInfraCodegenConform.render_project_gitignore(
            config.Infra.codegen,
            profile=c.Infra.MakeProfile.STANDALONE,
            project_name=root.name,
            project_dir=root,
        )

        tm.that(result.failure, truth=True)

    def test_distinct_prefix_markers_preserve_both_blocks(
        self,
        tmp_path: Path,
    ) -> None:
        """A longer exact delimiter is not a malformed shorter delimiter."""
        root = self._project(
            tmp_path / "project",
            {
                "tooling.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    preserved_blocks:\n"
                    "      - begin: '# BEGIN external projection'\n"
                    "        end: '# END external projection'\n"
                    "      - begin: '# BEGIN external projection extended'\n"
                    "        end: '# END external projection extended'\n"
                ),
            },
        )
        (root / ".gitignore").write_text(
            "# BEGIN external projection\n/first\n# END external projection\n\n"
            "# BEGIN external projection extended\n/second\n"
            "# END external projection extended\n",
            encoding="utf-8",
        )

        first = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )
        tm.that(first.count("# BEGIN external projection\n") == 1, truth=True)
        tm.that(first.count("# BEGIN external projection extended\n") == 1, truth=True)
        (root / ".gitignore").write_text(first, encoding="utf-8")
        second = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )
        tm.that(second == first, truth=True)

    def test_comment_mentioning_marker_is_not_a_delimiter(
        self,
        tmp_path: Path,
    ) -> None:
        """A normal comment may quote a marker without claiming the block."""
        root = self._external_project(tmp_path / "project")
        (root / ".gitignore").write_text(
            "# This comment quotes # BEGIN external projection for readers.\n"
            "# BEGIN external projection\n/owned\n# END external projection\n",
            encoding="utf-8",
        )

        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.STANDALONE,
                project_name=root.name,
                project_dir=root,
            ),
        )

        tm.that("# This comment quotes" not in rendered, truth=True)
        tm.that(
            rendered.endswith(
                "# BEGIN external projection\n/owned\n# END external projection\n"
            ),
            truth=True,
        )

    def test_duplicate_block_declaration_fails(self, tmp_path: Path) -> None:
        """Two project config documents cannot claim the same external marker."""
        root = self._project(
            tmp_path / "project",
            {
                "one.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    preserved_blocks:\n"
                    "      - begin: '# BEGIN external projection'\n"
                    "        end: '# END external projection'\n"
                ),
                "two.yaml": (
                    "ManagedArtifacts:\n  Gitignore:\n    preserved_blocks:\n"
                    "      - begin: '# BEGIN external projection'\n"
                    "        end: '# END external projection'\n"
                ),
            },
        )

        tm.that(u.Infra.load_project_managed_artifacts(root).failure, truth=True)
