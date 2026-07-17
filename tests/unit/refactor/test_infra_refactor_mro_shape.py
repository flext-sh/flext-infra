from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from flext_tests import tm

from flext_infra.detectors.mro_shape_detector import FlextInfraMROShapeDetector
from tests import m, p, t


def _write_file(tmp_path: Path, rel_path: str, source: str) -> Path:
    """Write ``source`` to ``tmp_path / rel_path`` and return the file path."""
    file_path = tmp_path / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(source, encoding="utf-8")
    return file_path


def _detect(
    file_path: Path, rope_project: t.Infra.RopeProject
) -> t.SequenceOf[p.Infra.MROShapeViolation]:
    """Run the detector against ``file_path``."""
    return FlextInfraMROShapeDetector.detect_file(
        m.Infra.DetectorContext(file_path=file_path, rope_project=rope_project)
    )


class TestsFlextInfraRefactorInfraRefactorMroShape:
    """Behavior contract for the rope MRO-shape detector."""

    def test_enforce_047_flags_facade_with_peer_first_base(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/models.py",
            "from __future__ import annotations\n"
            "class FlextExampleTypes:\n"
            "    pass\n"
            "class FlextExamplePeer:\n"
            "    pass\n"
            "class FlextExampleModels(FlextExamplePeer, FlextExampleTypes):\n"
            "    pass\n",
        )

        violations = _detect(target, rope_project)

        tm.that(len(violations), eq=1)
        tm.that(violations[0].rule_id, eq="047")
        tm.that(violations[0].class_name, eq="FlextExampleModels")
        tm.that(violations[0].first_base, eq="FlextExamplePeer")

    def test_enforce_047_allows_alias_first_base(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/models.py",
            "from __future__ import annotations\n"
            "class FlextExampleTypes:\n"
            "    pass\n"
            "class FlextExamplePeer:\n"
            "    pass\n"
            "class FlextExampleModels(FlextExampleTypes, FlextExamplePeer):\n"
            "    pass\n",
        )

        violations = _detect(target, rope_project)

        assert not violations

    def test_enforce_049_allows_peer_first_when_shared_alias_base(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/models.py",
            "from __future__ import annotations\n"
            "class FlextExampleTypes:\n"
            "    pass\n"
            "class FlextExamplePeerA(FlextExampleTypes):\n"
            "    pass\n"
            "class FlextExamplePeerB(FlextExampleTypes):\n"
            "    pass\n"
            "class FlextExampleModels(FlextExamplePeerA, FlextExamplePeerB):\n"
            "    pass\n",
        )

        violations = _detect(target, rope_project)

        assert not violations

    def test_enforce_046_flags_redundant_nested_namespace(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/service.py",
            "from __future__ import annotations\n"
            "class FlextExampleService:\n"
            "    class Config(FlextExampleService):\n"
            "        __slots__ = ()\n",
        )

        violations = _detect(target, rope_project)

        tm.that(len(violations), eq=1)
        tm.that(violations[0].rule_id, eq="046")
        tm.that(violations[0].class_name, eq="FlextExampleService.Config")

    def test_enforce_046_skips_nested_class_with_methods(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/service.py",
            "from __future__ import annotations\n"
            "class FlextExampleService:\n"
            "    class Config(FlextExampleService):\n"
            "        def method(self) -> None: ...\n",
        )

        violations = _detect(target, rope_project)

        assert not violations

    def test_enforce_051_flags_utilities_self_root(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/utilities.py",
            "from __future__ import annotations\n"
            "class u:\n"
            "    pass\n"
            "class FlextExampleUtilities(u, object):\n"
            "    def run(self) -> None:\n"
            "        u.something()\n",
        )

        violations = _detect(target, rope_project)

        tm.that(len(violations), eq=1)
        tm.that(violations[0].rule_id, eq="051")
        tm.that(violations[0].class_name, eq="FlextExampleUtilities")

    def test_enforce_051_skips_utilities_without_u_reference(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/utilities.py",
            "from __future__ import annotations\n"
            "class u:\n"
            "    pass\n"
            "class FlextExampleUtilities(u, object):\n"
            "    def run(self) -> None:\n"
            "        pass\n",
        )

        violations = _detect(target, rope_project)

        assert not violations

    def test_parse_failure_is_reported(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        target = _write_file(
            tmp_path,
            "src/flext_example/models.py",
            "from __future__ import annotations\nclass FlextExampleModels(\n",
        )
        ctx = m.Infra.DetectorContext(
            file_path=target, rope_project=rope_project, parse_failures=[]
        )

        violations = FlextInfraMROShapeDetector.detect_file(ctx)

        assert not violations
        tm.that(ctx.parse_failures, none=False)
        tm.that(len(ctx.parse_failures), eq=1)
        tm.that(ctx.parse_failures[0].stage, eq="mro_shape")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
