"""Public evidence for discovery-driven utility-facade projection."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import u


class TestsFlextInfraUtilityFacadeProjection:
    """Exercise consumer-driven owner projection only through ``u.Infra``."""

    @staticmethod
    def _write(path: Path, source: str) -> None:
        """Create one fixture source through the canonical atomic writer."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(path, source))

    def test_projects_only_uniquely_discovered_missing_owner(
        self, tmp_path: Path
    ) -> None:
        """Derive the required owner from the executable public consumer."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "codemod" / "batch_apply.py",
            "from flext_sample import u\n\nu.Sample.plan_cutover()\n",
        )
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> None:\n"
            "        pass\n",
        )
        facade = package / "utilities.py"
        self._write(
            facade,
            "from upstream import u\n"
            "from flext_sample._utilities.existing import Existing\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(\n"
            "        Existing,\n"
            "    ):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n",
        )
        updated = u.Infra.render_utility_facade(package)

        tm.that(updated is not None, eq=True)
        assert updated is not None
        tm.that(updated, has="from flext_sample._utilities.semantic_cutover import (")
        tm.that(updated.count("FlextSampleUtilitiesSemanticCutover"), eq=2)
        tm.that(
            "FlextSampleUtilitiesSemanticCutover" not in facade.read_text(), eq=True
        )

    def test_rejects_ambiguous_method_ownership(self, tmp_path: Path) -> None:
        """Fail before projection when two local owners claim one method."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "codemod" / "batch_apply.py",
            "from flext_sample import u\n\nu.Sample.plan_cutover()\n",
        )
        for module, class_name in (("first", "First"), ("second", "Second")):
            self._write(
                package / "_utilities" / f"{module}.py",
                f"class {class_name}:\n"
                "    @staticmethod\n"
                "    def plan_cutover() -> None:\n"
                "        pass\n",
            )
        facade = package / "utilities.py"
        original = (
            "from upstream import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(u):\n"
            "        pass\n"
        )
        self._write(facade, original)

        with pytest.raises(ValueError, match=r"ambiguous u\.Infra owner"):
            u.Infra.render_utility_facade(package)
        tm.that(facade.read_text(), eq=original)

    def test_rejects_owners_without_a_public_facade(self, tmp_path: Path) -> None:
        """Utility owners without a facade have no public surface at all."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "_utilities" / "owner.py", "class Owner:\n    pass\n")

        with pytest.raises(ValueError, match="have no public facade"):
            u.Infra.render_utility_facade(package)

    def test_facade_without_local_owners_is_complete(self, tmp_path: Path) -> None:
        """A pure re-export facade with no owners directory needs no projection."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "utilities.py", "class Owner:\n    pass\n")

        tm.that(u.Infra.render_utility_facade(package), eq=None)

    def test_rejects_unsupported_facade_base_expression(self, tmp_path: Path) -> None:
        """Reject dynamic bases instead of converting them to an empty owner."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "codemod" / "batch_apply.py",
            "from flext_sample import u\n\nu.Sample.plan_cutover()\n",
        )
        # The facade and its private family exist together in a real package;
        # without the owner directory the renderer stops at the incomplete
        # artifact check and never reaches the base expression under test.
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> None:\n"
            "        pass\n",
        )
        self._write(
            package / "utilities.py",
            "from upstream import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(owner_factory()):\n"
            "        pass\n",
        )

        with pytest.raises(ValueError, match="unsupported utility facade base"):
            u.Infra.render_utility_facade(package)


__all__: list[str] = ["TestsFlextInfraUtilityFacadeProjection"]
