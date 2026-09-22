"""Exercise generated merge attributes through Git's native consumer."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m, u
from tests import u as test_u


class TestsGeneratedGitAttributes:
    """Generated paths reject textual merges without hiding authored diffs."""

    def test_git_consumes_exact_generated_paths(self, tmp_path: Path) -> None:
        """Git interprets quoted paths and leaves authored sources mergeable."""
        root = test_u.Tests.git_repository(tmp_path)
        codegen = config.Infra.codegen
        generated = "generated output.txt"
        authored = "source.py"
        rendered = tm.ok(u.Cli.template_render(
            u.Infra.codegen_templates_root(codegen) / codegen.make.git_attributes_template,
            m.Infra.MakeWorkflowRenderSpec(
                dist=root.name, make=codegen.make, generated_paths=(f"/{generated}",),
            ),
        ))
        tm.ok(u.Cli.atomic_write_text_file(root / c.Infra.GITATTRIBUTES_FILENAME, rendered))
        observed = tm.ok(u.Cli.run(
            [c.Infra.GIT, "check-attr", "merge", "linguist-generated", "--", generated, authored],
            cwd=root,
        ))
        tm.that(observed.stdout, has=f"{generated}: merge: unset")
        tm.that(observed.stdout, has=f"{generated}: linguist-generated: set")
        tm.that(observed.stdout, has=f"{authored}: merge: unspecified")

    def test_unchanged_checkpoint_preserves_head(self, tmp_path: Path) -> None:
        """Repeated checkpoint calls never manufacture a new commit."""
        root = test_u.Tests.git_repository(tmp_path)
        before = tm.ok(u.Cli.run([c.Infra.GIT, "rev-parse", "HEAD"], cwd=root)).stdout.strip()
        checkpoint = tm.ok(u.Infra.git_checkpoint_worktree(root, message="checkpoint"))
        repeated = tm.ok(u.Infra.git_checkpoint_worktree(root, message="checkpoint again"))
        after = tm.ok(u.Cli.run([c.Infra.GIT, "rev-parse", "HEAD"], cwd=root)).stdout.strip()
        tm.that(checkpoint, eq=before)
        tm.that(repeated, eq=before)
        tm.that(after, eq=before)


__all__: list[str] = ["TestsGeneratedGitAttributes"]
