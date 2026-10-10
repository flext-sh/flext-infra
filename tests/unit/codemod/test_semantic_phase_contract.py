"""Real-source regression evidence for staged semantic cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSemanticPhaseContract:
    """Require planned and published sources to reach the same fixed point."""

    @staticmethod
    @pytest.mark.parametrize(
        "upstream_import",
        [
            "from flext_core import c as core_c",
            "from flext_core.constants import FlextConstants as core_c",
        ],
    )
    def test_constant_consumers_resolve_upstream_binding_without_shadow_rewrites(
        tmp_path: Path,
        upstream_import: str,
    ) -> None:
        """Inherited constants use the existing facade and reach a fixed point."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "consumer.py"
        shadowed = "def local(core_c):\n    return core_c.PRIMITIVES_TYPES\n"
        sources = {
            package / c.Infra.CONSTANTS_PY: (
                "from flext_cli import c\n"
                f"class {owner}(c):\n    pass\n"
                f"c = {owner}\n"
                f'__all__ = ["{owner}", "c"]\n'
            ),
            package / c.Infra.INIT_PY: 'from .constants import c\n__all__ = ["c"]\n',
            path: (
                f"{upstream_import}\n"
                f"from {package.name} import c\n"
                "upstream = core_c.PRIMITIVES_TYPES\n"
                "downstream = c.PRIMITIVES_TYPES\n\n"
                f"{shadowed}"
            ),
        }
        for source_path, source in sources.items():
            source_path.write_text(source, encoding="utf-8")
        phase = c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            tm.that(tuple(edit.file_path for edit in planned.value), eq=(path,))
            updated = planned.value[0].updated_source
            tm.that(updated, has="upstream = c.PRIMITIVES_TYPES")
            tm.that(updated, has="downstream = c.PRIMITIVES_TYPES")
            tm.that(updated, has=shadowed)
            tm.that(updated.count(f"from {package.name} import c"), eq=1)
            tm.that(upstream_import in updated, eq=False)
            remaining = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources={**sources, path: updated},
            )
        tm.ok(remaining)
        tm.that(remaining.value, empty=True)
        for source_path, source in sources.items():
            tm.that(source_path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("case", ["ambiguous", "cyclic"])
    def test_constant_consumers_reject_unproven_upstream_bindings(
        tmp_path: Path,
        case: str,
    ) -> None:
        """Competing terminal identities and export cycles never yield edits."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        upstream = package.parent / "flext_upstream"
        upstream.mkdir()
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        sources = {
            package / c.Infra.CONSTANTS_PY: (
                f'class {owner}:\n    pass\nc = {owner}\n__all__ = ["{owner}", "c"]\n'
            ),
            package / "consumer.py": (
                "from flext_upstream import c as core_c\n"
                f"from {package.name} import c\n"
                "value = core_c.PRIMITIVES_TYPES\n"
            ),
            upstream / c.Infra.INIT_PY: (
                "from .left import Left as c\nfrom .right import Right as c\n"
                if case == "ambiguous"
                else "from .loop import c\n"
            ),
            upstream / "left.py": "class Left:\n    pass\n",
            upstream / "right.py": "class Right:\n    pass\n",
            upstream / "loop.py": "from . import c\n",
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(planned, has=case)
        tm.that(planned.error, has="flext_upstream.c")
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_annotations_and_nesting_complete_in_one_atomic_cutover(
        tmp_path: Path,
    ) -> None:
        """Test annotations and nesting complete in one atomic cutover."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        # Publication runs through the codegen transaction, which coordinates
        # only inside an exact Git worktree root, exactly as in production.
        u.Tests.initialize_git_repo(root)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "constants.py"
        u.Tests.write_lazy_init_namespace_module(
            path,
            class_name=owner,
            alias="c",
            extra_class_names=(f"{owner}Member",),
        )
        source = path.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            "",
        )
        path.write_text(source, encoding="utf-8")
        # Semantic publication runs inside a codegen transaction, which only
        # coordinates through a real repository rooted at the project.
        u.Tests.initialize_git_repo(root)
        finding = m.Infra.ModScanFinding(
            rule_file="require-future-annotations.yml",
            rule_id="require-future-annotations",
            repository=root.name,
            file=path.relative_to(root),
            range={},
            text=source,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
            payload={},
        )
        report = m.Infra.ModScanReport(
            findings=1,
            actionable=0,
            detection_only=1,
            non_actionable_with_fix=0,
            files=frozenset({path}),
            entries=(finding,),
        )
        with infra.rope_workspace(root) as rope:
            tm.ok(FlextInfraCodemodSemanticApply.apply(root, report, rope))
        published = path.read_text(encoding="utf-8")
        tm.that(published, has="from __future__ import annotations")
        tm.that(published, has=f"    class {owner}Member")
        with infra.rope_workspace(root) as rope:
            tm.ok(FlextInfraCodemodSemanticApply.apply(root, report, rope))
        tm.that(path.read_text(encoding="utf-8"), eq=published)

    @staticmethod
    def test_nesting_replans_proposed_sources_without_publishing(
        tmp_path: Path,
    ) -> None:
        """Test nesting replans proposed sources without publishing."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "constants.py"
        u.Tests.write_lazy_init_namespace_module(
            path,
            class_name=owner,
            alias="c",
            extra_class_names=(f"{owner}Member",),
        )
        original = path.read_text(encoding="utf-8")
        nesting = c.Infra.SemanticCutoverPhase.CLASS_NESTING
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                nesting,
                rope_workspace=rope,
                sources={path: original},
            )
            tm.ok(planned)
            tm.that(len(planned.value), eq=1)
            tm.that(
                planned.value[0].changes,
                eq=(f"nested {owner}Member under {owner}",),
            )
            remaining = u.Infra.plan_semantic_cutover(
                nesting,
                rope_workspace=rope,
                sources={path: planned.value[0].updated_source},
            )
        tm.ok(remaining)
        tm.that(remaining.value, empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=original)

    @staticmethod
    def test_nesting_reports_every_module_without_an_owner_as_a_failure(
        tmp_path: Path,
    ) -> None:
        """Rival stem-carrying classes leave the owner undecidable: the plan fails."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "models.py"
        stem = (
            f"{u.derive_class_stem(root.name)}"
            f"{u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).suffix}"
        )
        source = (
            f"class {stem}FirstCandidate:\n    pass\n\n"
            f"class {stem}SecondCandidate:\n    pass\n\n"
            f'__all__ = ["{stem}FirstCandidate", "{stem}SecondCandidate"]\n'
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="requires exactly one declared module owner")
