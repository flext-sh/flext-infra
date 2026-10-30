"""Immutable source-bundle and physical-path contracts for docs planning.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_infra.docs.generator import FlextInfraDocGenerator
from tests import p, tm, u

_DOCS_CONSUMER_SOURCE = r"""sys.path.insert(0, sys.argv[1])
from flext_infra.docs import FlextInfraDocGenerator
from tests import c, tm, u
from tests.unit.docs.generator_bundle_tests import TestsFlextInfraDocsGeneratorBundle
tmp_path = Path(sys.argv[2])
case = TestsFlextInfraDocsGeneratorBundle()
"""


class TestsFlextInfraDocsGeneratorBundle:
    """Immutable source-bundle and physical-path contracts for docs planning."""

    @staticmethod
    def _generator(workspace: Path) -> FlextInfraDocGenerator:
        """Return the public generator for the governed fixture project.

        Returns:
            The public generator for the governed fixture project.

        """
        return FlextInfraDocGenerator(
            repository_root=workspace,
            selected_projects=["flext-a"],
        )

    @staticmethod
    def test_noop_destination_edit_rejects_original_publication_state(
        tmp_path: Path,
    ) -> None:
        """A no-op still proves its original state before reporting success."""
        target = tmp_path / "artifact.md"
        target.write_bytes(b"original\n")
        before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
        plan = m.Infra.CodegenFilePlan(
            project=tmp_path,
            path=target,
            before=before,
            desired_content=before.content,
            desired_mode=before.mode,
            owner="docs",
        )
        target.write_bytes(b"concurrent\n")

        published = u.Cli.publish_file_changes(
            (plan,), lock_path=u.Infra.mutation_lock_path(plan.project).unwrap()
        )

        tm.fail(published)
        tm.that(target.read_bytes(), eq=b"concurrent\n")

    @staticmethod
    def test_docs_target_leaf_symlink_to_in_project_file_is_rejected(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Never turn a managed lexical target into an unmanaged in-project referent."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(
    tmp_path, project_names=("flext-a",)
)
project = workspace / "flext-a"
unmanaged = project / "NOTES.md"
unmanaged.write_text("keep\n", encoding="utf-8")
target = project / "README.md"
target.unlink()
target.symlink_to(unmanaged.name)
generator = case._generator(workspace)
prepared = generator.prepare_bundle()
tm.ok(prepared)
planned = generator.plan_files(prepared.value)
tm.fail(planned)
tm.that(planned.error or "", has="atomic")
tm.that(unmanaged.read_text(encoding="utf-8"), eq="keep\n")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_generated_parent_symlink_is_rejected_before_prune(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Reject an aliased generated tree before deriving any delete artifact."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(
    tmp_path, project_names=("flext-a",)
)
project = workspace / "flext-a"
curated = project / "curated"
curated.mkdir()
keep = curated / "keep.md"
keep.write_text("keep\n", encoding="utf-8")
generated = project / c.Infra.DIR_DOCS / "api-reference/generated"
generated.parent.mkdir(parents=True, exist_ok=True)
generated.symlink_to(curated, target_is_directory=True)
generator = case._generator(workspace)
prepared = generator.prepare_bundle()
tm.fail(prepared)
tm.that(prepared.error or "", has="atomic")
tm.that(keep.read_text(encoding="utf-8"), eq="keep\n")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_selected_project_symlink_cannot_escape_workspace(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Reject a selected local path whose physical project is outside the root."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(tmp_path)
outside = tmp_path / "outside"
package = outside / "src/outside"
package.mkdir(parents=True)
(package / "__init__.py").write_text("", encoding="utf-8")
(outside /  c.PYPROJECT_FILENAME).write_text(
    '[project]\nname = "outside"\nversion = "0.1.0"\n',
    encoding="utf-8",
)
(workspace / "escaped").symlink_to(outside, target_is_directory=True)
generator = FlextInfraDocGenerator(
    repository_root=workspace,
    selected_projects=["escaped"],
)
prepared = generator.prepare_bundle()
tm.fail(prepared)
tm.that(prepared.error or "", has="atomic")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )

    @staticmethod
    def test_cached_pyproject_cannot_diverge_from_bundle_source_bytes(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Render a later valid pyproject version rather than a path-keyed old value."""
        native_consumer(
            _DOCS_CONSUMER_SOURCE
            + r"""workspace = u.Tests.create_docs_workspace(
    tmp_path, project_names=("flext-a",)
)
generator = case._generator(workspace)
first = generator.prepare_bundle()
tm.ok(first)
pyproject = workspace / "flext-a/pyproject.toml"
pyproject.write_text(
    '[project]\nname = "flext-a"\nversion = "0.2.0"\n'
    'description = "Fresh metadata"\n',
    encoding="utf-8",
)
second = generator.prepare_bundle()
tm.ok(second)
readme = next(
    artifact
    for scoped in second.value.scopes
    if scoped.scope.name == "flext-a"
    for artifact in scoped.artifacts
    if artifact.relative_path.as_posix() == "README.md"
)
tm.that(readme.desired_content or b"", has=b"Fresh metadata")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
        )
