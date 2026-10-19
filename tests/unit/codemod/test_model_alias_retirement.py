"""Native retirement of pure utility model re-publication namespaces.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from flext_infra.refactor import FlextInfraImportNormalization
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


class TestsFlextInfraModelAliasRetirement:
    """The public semantic planner preserves canonical class identity."""

    @staticmethod
    def _workspace(
        tmp_path: Path, consumer: str
    ) -> t.Pair[Path, t.MappingKV[Path, str]]:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        models = package / u.Infra.facade_families()[c.Infra.FacadeFamily.M].directory
        utilities = (
            package / u.Infra.facade_families()[c.Infra.FacadeFamily.U].directory
        )
        models.mkdir()
        utilities.mkdir()
        (models / "__init__.py").write_text("", encoding="utf-8")
        (models / "payload.py").write_text(
            "from pydantic import BaseModel\n\n"
            "class CanonicalPayloads:\n"
            "    class First(BaseModel):\n"
            "        value: int\n"
            "    class Second(BaseModel):\n"
            "        value: str\n",
            encoding="utf-8",
        )
        (utilities / "relay.py").write_text(
            f"from {package.name}._models.payload import CanonicalPayloads\n\n"
            "class RedundantRelay:\n"
            '    """Only re-published model declarations."""\n'
            "    First = CanonicalPayloads.First\n"
            "    Second = CanonicalPayloads.Second\n\n"
            '__all__ = ["RedundantRelay"]\n',
            encoding="utf-8",
        )
        (utilities / "__init__.py").write_text(
            c.Infra.AUTOGEN_HEADERS[0] + "\n"
            "from .relay import RedundantRelay\n"
            '__all__ = ["RedundantRelay"]\n',
            encoding="utf-8",
        )
        (package / "consumer.py").write_text(
            f"from {package.name}._utilities import RedundantRelay\n" + consumer,
            encoding="utf-8",
        )
        return root, {
            path.resolve(): path.read_text(encoding="utf-8")
            for path in package.rglob("*.py")
        }

    @staticmethod
    def test_public_planner_rewires_aliases_annotations_and_runtime_identity(
        tmp_path: Path,
    ) -> None:
        """Two native aliases converge without changing ordinary string payloads."""
        root, sources = TestsFlextInfraModelAliasRetirement._workspace(
            tmp_path,
            "from typing import Literal\n"
            "def first(value: RedundantRelay.First) -> RedundantRelay.Second:\n"
            "    return RedundantRelay.Second(value=str(value.value))\n"
            'def forward(value: "RedundantRelay.First") -> "RedundantRelay.Second":\n'
            "    return first(value)\n"
            'PAYLOAD = "RedundantRelay.First"\n'
            'MARKER: Literal["RedundantRelay.Second"] = "RedundantRelay.Second"\n',
        )
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                    import_normalizer=FlextInfraImportNormalization.normalize_source,
                    rope_workspace=workspace,
                    sources=sources,
                )
            )
            updated = dict(sources)
            updated.update((edit.file_path, edit.updated_source) for edit in edits)
            tm.that(len(edits) >= 2, eq=True)
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                        import_normalizer=FlextInfraImportNormalization.normalize_source,
                        rope_workspace=workspace,
                        sources=updated,
                    )
                ),
                eq=(),
            )
        for path, source in updated.items():
            if source != sources[path]:
                tm.that(source.startswith(c.Infra.AUTOGEN_HEADERS), eq=False)
                path.write_text(source, encoding="utf-8")
        package = next(path.parent for path in sources if path.name == "consumer.py")
        consumer = (package / "consumer.py").read_text(encoding="utf-8")
        tm.that('PAYLOAD = "RedundantRelay.First"' in consumer, eq=True)
        tm.that('Literal["RedundantRelay.Second"]' in consumer, eq=True)
        result = tm.ok(
            u.Cli.run((
                sys.executable,
                "-c",
                (
                    f"import sys; sys.path.insert(0, {str(package.parent)!r}); "
                    f"from {package.name} import consumer; "
                    f"from {package.name}._models.payload import CanonicalPayloads; "
                    "from typing import get_type_hints; "
                    "assert consumer.first.__annotations__['value'] "
                    "is CanonicalPayloads.First; "
                    "assert get_type_hints(consumer.forward)['return'] "
                    "is CanonicalPayloads.Second; "
                    "assert type(consumer.first("
                    "CanonicalPayloads.First(value=1))) "
                    "is CanonicalPayloads.Second"
                ),
            ))
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @pytest.mark.parametrize(
        "consumer",
        [
            "ESCAPE = RedundantRelay\n",
            "class Derived(RedundantRelay):\n    pass\n",
            'def value(arg: "RedundantRelay") -> None:\n    pass\n',
            "VALUE = RedundantRelay.Unknown\n",
            "RedundantRelay.First = str\n",
        ],
    )
    @staticmethod
    def test_type_value_escapes_fail_before_any_source_effect(
        tmp_path: Path, consumer: str
    ) -> None:
        """Unknown, mutated and first-class wrapper uses cannot partially retire."""
        root, sources = TestsFlextInfraModelAliasRetirement._workspace(
            tmp_path, consumer
        )
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match=r"model alias|model import"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                import_normalizer=FlextInfraImportNormalization.normalize_source,
                rope_workspace=workspace,
                sources=sources,
            )
        tm.that(
            {path: path.read_text(encoding="utf-8") for path in sources}, eq=sources
        )

    @staticmethod
    def test_real_utility_behavior_is_not_an_alias_namespace(tmp_path: Path) -> None:
        """A method makes a utility owner legitimate, even beside model aliases."""
        root, original = TestsFlextInfraModelAliasRetirement._workspace(
            tmp_path,
            "VALUE = RedundantRelay\n",
        )
        sources = dict(original)
        path = next(path for path in sources if path.name == "relay.py")
        sources[path] = sources[path].replace(
            "    First =",
            "    def execute(self):\n        return 1\n\n    First =",
        )
        path.write_text(sources[path], encoding="utf-8")
        with infra.rope_workspace(root) as workspace:
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.COMPAT_ALIAS,
                        import_normalizer=FlextInfraImportNormalization.normalize_source,
                        rope_workspace=workspace,
                        sources=sources,
                    )
                ),
                eq=(),
            )
