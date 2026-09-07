"""Public utility evidence for semantic private-import cutovers."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, m, t, u
from flext_tests import tm


class TestsFlextInfraPrivateImportCutover:
    """Exercise private-import automation only through ``u.Infra``."""

    @staticmethod
    def _finding(file_path: Path, text: str) -> m.Infra.ModScanFinding:
        """Build one authenticated-shape semantic finding."""
        return m.Infra.ModScanFinding(
            rule_file="ban-private-import.yml",
            rule_id="ban-private-import",
            repository="flext-sample",
            file=file_path,
            range={},
            text=text,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
            payload={},
        )

    @staticmethod
    def _facade_source(
        *,
        private_module: str,
        private_class: str,
        root_class: str,
        nested_class: str,
        alias: str,
        root_bases: str = "",
    ) -> str:
        """Build one public facade module that nests ``private_class``."""
        return (
            f"from {private_module} import {private_class}\n\n"
            f"class {root_class}{root_bases}:\n"
            f"    class {nested_class}({private_class}):\n"
            "        pass\n\n"
            f"{alias} = {root_class}\n"
        )

    @classmethod
    def _facade_case(
        cls,
        tmp_path: Path,
        family: str,
        leaf: str,
        nested_class: str,
        alias: str,
        *,
        import_alias: str = "",
        root_bases: str = "",
    ) -> tuple[Path, str, dict[Path, str]]:
        """Derive the consumer path, private import, and facade source of one family.

        Every name follows the FLEXT naming contract, so the case is declared
        by ``family``/``leaf`` rather than by frozen literals repeated per test.
        """
        private_module = f"flext_sample._{family}.{leaf}"
        private_class = f"FlextSample{family.title()}{leaf.title()}"
        binding = (
            f"{private_class} as {import_alias}" if import_alias else private_class
        )
        sources = {
            tmp_path / f"flext-sample/src/flext_sample/{family}.py": cls._facade_source(
                private_module=private_module,
                private_class=private_class,
                root_class=f"FlextSample{family.title()}",
                nested_class=nested_class,
                alias=alias,
                root_bases=root_bases,
            )
        }
        consumer_path = tmp_path / "flext-consumer/src/flext_consumer/service.py"
        return consumer_path, f"from {private_module} import {binding}", sources

    @classmethod
    def _plan(
        cls,
        tmp_path: Path,
        sources: t.MappingKV[Path, str],
        consumer_path: Path,
        *private_imports: str,
    ) -> tuple[m.Infra.SemanticMigrationEdit, ...]:
        """Plan the cutover for every private import reported in the consumer."""
        return u.Infra.plan_private_import_cutover(
            root=tmp_path,
            sources=sources,
            findings=tuple(
                cls._finding(consumer_path.relative_to(tmp_path), private_import)
                for private_import in private_imports
            ),
        )

    @classmethod
    def _updated_source(
        cls,
        tmp_path: Path,
        sources: t.MappingKV[Path, str],
        consumer_path: Path,
        *private_imports: str,
    ) -> str:
        """Return the single planned edit's rewritten consumer source."""
        edits = cls._plan(tmp_path, sources, consumer_path, *private_imports)
        return edits[0].updated_source

    def test_rewires_unique_public_facade_binding(self, tmp_path: Path) -> None:
        """Derive the nested facade path and remove the private import atomically."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "utilities", "managers", "Sample", "u"
        )
        sources[consumer_path] = (
            "from flext_sample import p\n"
            f"{private_import}\n\n"
            "manager: FlextSampleUtilitiesManagers.ServiceManagers\n"
        )

        edits = self._plan(tmp_path, sources, consumer_path, private_import)
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source

        tm.that(
            "from flext_sample import p, u" in updated
            or "from flext_sample import u" in updated,
            eq=True,
        )
        tm.that(updated, has="manager: u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)
        tm.that(updated, lacks="FlextSampleUtilitiesManagers.ServiceManagers")

    def test_prefers_nested_facade_over_its_root_ancestor(self, tmp_path: Path) -> None:
        """Select the deepest public namespace when the root shares its base."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path,
            "utilities",
            "managers",
            "Sample",
            "u",
            root_bases="(FlextSampleUtilitiesManagers)",
        )
        sources[consumer_path] = (
            f"{private_import}\n\nmanager = FlextSampleUtilitiesManagers.ServiceManagers\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="manager = u.Sample.ServiceManagers")
        tm.that(updated, lacks=private_import)

    def test_rewrites_only_the_imported_alias_binding(self, tmp_path: Path) -> None:
        """Keep a homonymous local binding outside the authenticated cutover."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "utilities", "managers", "Sample", "u", import_alias="managers"
        )
        sources[consumer_path] = (
            f"{private_import}\n\n"
            "manager = managers.ServiceManagers\n\n"
            "def identity(managers: str) -> str:\n"
            "    return managers\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="manager = u.Sample.ServiceManagers")
        tm.that(updated, has="def identity(managers: str) -> str:")
        tm.that(updated, has="    return managers")
        tm.that(updated, lacks=private_import)

    def test_rejects_shadowed_public_facade_alias(self, tmp_path: Path) -> None:
        """Fail before effects when a local binding would capture the facade alias."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "utilities", "managers", "Sample", "u"
        )
        sources[consumer_path] = (
            f"{private_import}\n\n"
            "def select(u: str) -> str:\n"
            "    return FlextSampleUtilitiesManagers.ServiceManagers or u\n"
        )

        with pytest.raises(ValueError, match="public facade alias u is shadowed"):
            self._plan(tmp_path, sources, consumer_path, private_import)

    def test_accepts_alias_owned_by_removed_private_import(
        self, tmp_path: Path
    ) -> None:
        """Replace the old import binding with its public facade atomically."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "models", "base", "Metadata", "m", import_alias="m"
        )
        sources[consumer_path] = f"{private_import}\n\nmetadata = m.Metadata()\n"

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="from flext_sample import m")
        tm.that(updated, has="metadata = m.Metadata()")
        tm.that(updated, lacks=private_import)

    def test_preserves_type_checking_boundary_for_public_facade(
        self, tmp_path: Path
    ) -> None:
        """Keep a type-only facade import in the original type-only boundary."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "models", "base", "Metadata", "m", import_alias="m"
        )
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            f"    {private_import}\n\n"
            "metadata: m.Metadata\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="if TYPE_CHECKING:\n    from flext_sample import m")
        tm.that(updated, lacks="\nfrom flext_sample import m\n")
        tm.that(updated, lacks=private_import)

    def test_preserves_multiple_type_only_facades_from_one_package(
        self, tmp_path: Path
    ) -> None:
        """Rewire every type facade without promoting imports to runtime."""
        package_path = tmp_path / "flext-sample/src/flext_sample"
        consumer_path = tmp_path / "flext-consumer/src/flext_consumer/service.py"
        layers = (
            ("models", "m", "FlextSampleModelsBase", "Model"),
            ("protocols", "p", "FlextSampleProtocolsBase", "Protocol"),
            ("typings", "t", "FlextSampleTypesBase", "Type"),
        )
        sources: dict[Path, str] = {}
        private_imports: list[str] = []
        annotations: list[str] = []
        for layer, alias, private_class, nested_class in layers:
            private_module = f"flext_sample._{layer}.base"
            private_imports.append(
                f"from {private_module} import {private_class} as {alias}b"
            )
            sources[package_path / f"{layer}.py"] = self._facade_source(
                private_module=private_module,
                private_class=private_class,
                root_class=f"FlextSample{layer.title()}",
                nested_class=nested_class,
                alias=alias,
            )
            annotations.append(f"value_{alias}: {alias}b.Member")
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n    "
            + "\n    ".join(private_imports)
            + "\n\n"
            + "\n".join(annotations)
            + "\n"
        )

        updated = self._updated_source(
            tmp_path, sources, consumer_path, *private_imports
        )

        tm.that(updated, has="    from flext_sample import m, p, t")
        tm.that(updated.count("from flext_sample import"), eq=1)
        for _layer, alias, _private_class, nested_class in layers:
            tm.that(updated, has=f"value_{alias}: {alias}.{nested_class}.Member")
            tm.that(updated, lacks=f"\nfrom flext_sample import {alias}\n")
        for private_import in private_imports:
            tm.that(updated, lacks=private_import)

    def test_discovers_operational_facade_from_live_source(
        self, tmp_path: Path
    ) -> None:
        """Rewire an operational family without a registered family-to-alias map."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "exceptions", "base", "Invalid", "e", import_alias="eb"
        )
        sources[consumer_path] = f"{private_import}\n\nerror: eb.Code\n"

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated, has="from flext_sample import e")
        tm.that(updated, has="error: e.Invalid.Code")
        tm.that(updated, lacks=private_import)

    def test_replaces_public_long_alias_during_private_cutover(
        self, tmp_path: Path
    ) -> None:
        """Delete the long public alias while wiring the canonical facade."""
        consumer_path, private_import, sources = self._facade_case(
            tmp_path, "models", "pydantic", "Pydantic", "m", import_alias="mp"
        )
        sources[consumer_path] = (
            "from __future__ import annotations\n\n"
            f"{private_import}\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from flext_sample import FlextSampleModels as m\n\n"
            "value: m.Metadata\n"
            "model: mp.BaseModel\n"
        )

        updated = self._updated_source(tmp_path, sources, consumer_path, private_import)

        tm.that(updated.count("from flext_sample import m"), eq=1)
        tm.that(updated, lacks="FlextSampleModels as m")
        tm.that(updated, lacks=private_import)
        tm.that(updated, has="model: m.Pydantic.BaseModel")

    def test_preserves_valid_relative_private_import(self, tmp_path: Path) -> None:
        """Leave an already-relative same-owner import outside the finding set."""
        consumer_path = tmp_path / "flext-sample/src/flext_sample/service.py"
        relative_import = (
            "from ._models.pydantic import FlextSampleModelsPydantic as mp"
        )

        edits = self._plan(
            tmp_path,
            {consumer_path: f"{relative_import}\n\nmodel = mp.BaseModel\n"},
            consumer_path,
        )

        tm.that(edits, eq=())

    def test_relativizes_same_owner_import_without_rebinding_alias(
        self, tmp_path: Path
    ) -> None:
        """Avoid package-root re-entry while preserving the imported binding."""
        consumer_path = tmp_path / "flext-sample/src/flext_sample/_utilities/mapper.py"
        private_import = (
            "from flext_sample._models.pydantic import FlextSampleModelsPydantic as mp"
        )

        updated = self._updated_source(
            tmp_path,
            {consumer_path: f"{private_import}\n\nmodel = mp.BaseModel\n"},
            consumer_path,
            private_import,
        )

        tm.that(
            updated,
            has=("from .._models.pydantic import FlextSampleModelsPydantic as mp"),
        )
        tm.that(updated, has="model = mp.BaseModel")
        tm.that(updated, lacks=private_import)
        tm.that(updated, lacks="from flext_sample import m")

    def test_relativizes_handwritten_package_initializer(self, tmp_path: Path) -> None:
        """Apply the same owner rule to handwritten ``__init__.py`` modules."""
        consumer_path = tmp_path / "flext-sample/src/flext_sample/_models/__init__.py"
        private_import = (
            "from flext_sample._models.config import FlextSampleModelsConfig"
        )

        updated = self._updated_source(
            tmp_path,
            {
                consumer_path: (
                    f"{private_import}\n\n__all__ = ['FlextSampleModelsConfig']\n"
                )
            },
            consumer_path,
            private_import,
        )

        tm.that(updated, has="from .config import FlextSampleModelsConfig")
        tm.that(updated, lacks=private_import)

    def test_relativizes_same_owner_root_facade_without_package_reentry(
        self, tmp_path: Path
    ) -> None:
        """Use one leading dot when a package-root module consumes its family."""
        consumer_path = tmp_path / "flext-sample/src/flext_sample/loggings.py"
        private_import = (
            "from flext_sample._utilities.logging_context import "
            "FlextSampleUtilitiesLoggingContext as ulc"
        )

        updated = self._updated_source(
            tmp_path,
            {consumer_path: f"{private_import}\n\ncontext = ulc.Context\n"},
            consumer_path,
            private_import,
        )

        tm.that(
            updated,
            has=(
                "from ._utilities.logging_context import "
                "FlextSampleUtilitiesLoggingContext as ulc"
            ),
        )
        tm.that(updated, has="context = ulc.Context")
        tm.that(updated, lacks=private_import)


__all__: list[str] = ["TestsFlextInfraPrivateImportCutover"]
