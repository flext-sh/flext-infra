"""Shared facade-naming and planning fixtures for private-import cutover contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from flext_infra import infra, m, p, t, u
from tests import c, tm


@dataclasses.dataclass(frozen=True)
class TestsFlextInfraFacadeNaming:
    """The resolved facade identity of one public/private module pair."""

    __test__ = False

    private_module: str
    private_class: str
    root_class: str
    nested_class: str
    alias: str
    root_bases: str = ""

    @classmethod
    def from_family(
        cls,
        family: str,
        leaf: str,
        nested_class: str,
        alias: str,
    ) -> TestsFlextInfraFacadeNaming:
        """Derive every name from the sampled family naming contract.

        Returns:
            The resulting ``TestsFlextInfraFacadeNaming``.

        """
        return cls(
            private_module=f"flext_sample._{family}.{leaf}",
            private_class=f"FlextSample{family.title()}{leaf.title()}",
            root_class=f"FlextSample{family.title()}",
            nested_class=nested_class,
            alias=alias,
        )


class TestsFlextInfraPrivateImportCutoverSupport:
    """Plan and render private-import cutovers only through ``u.Infra``."""

    @staticmethod
    def _finding(file_path: Path, text: str) -> m.Infra.ModOccurrence:
        """Build one authenticated-shape semantic finding.

        Returns:
            The resulting ``m.Infra.ModOccurrence``.

        """
        return m.Infra.ModOccurrence(
            rule_file="ban-private-import.yml",
            rule_id="ban-private-import",
            repository="flext-sample",
            file=file_path,
            range={},
            text=text,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )

    @staticmethod
    def _facade_source(*, naming: TestsFlextInfraFacadeNaming) -> str:
        """Build one public facade module that nests the private class.

        Returns:
            The resulting ``str``.

        """
        return (
            f"from {naming.private_module} import {naming.private_class}\n\n"
            f"class {naming.root_class}{naming.root_bases}:\n"
            f"    class {naming.nested_class}({naming.private_class}):\n"
            "        pass\n\n"
            f"{naming.alias} = {naming.root_class}\n"
        )

    @classmethod
    def _facade_case(
        cls,
        tmp_path: Path,
        naming: TestsFlextInfraFacadeNaming,
        *,
        import_alias: str = "",
    ) -> t.Triple[Path, str, t.MutableMappingKV[Path, str]]:
        """Derive the consumer path, private import, and facade source of one family.

        Returns:
            The resulting ``t.Triple[Path, str, t.MutableMappingKV[Path, str]]``.

        """
        binding = (
            f"{naming.private_class} as {import_alias}"
            if import_alias
            else naming.private_class
        )
        family_dir = naming.private_module.split(".")[1].removeprefix("_")
        sources = {
            tmp_path / f"flext-sample/src/flext_sample/{family_dir}.py": (
                cls._facade_source(naming=naming)
            ),
        }
        consumer_path = tmp_path / "flext-consumer/src/flext_consumer/service.py"
        return consumer_path, f"from {naming.private_module} import {binding}", sources

    @classmethod
    def _plan(
        cls,
        tmp_path: Path,
        sources: t.MappingKV[Path, str],
        consumer_path: Path,
        *private_imports: str,
    ) -> p.ResultView[t.VariadicTuple[p.Infra.SemanticMigrationEdit]]:
        """Plan the cutover for every private import reported in the consumer.

        Returns:
            The originating immutable result view of semantic migration edits.

        """
        with infra.rope_workspace(tmp_path) as rope:
            return u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.PRIVATE_IMPORT,
                rope_workspace=rope,
                sources=sources,
                findings=tuple(
                    cls._finding(consumer_path.relative_to(tmp_path), private_import)
                    for private_import in private_imports
                ),
            )

    @classmethod
    def _edits(
        cls,
        tmp_path: Path,
        sources: t.MappingKV[Path, str],
        consumer_path: Path,
        *private_imports: str,
    ) -> t.VariadicTuple[p.Infra.SemanticMigrationEdit]:
        """Return the successful plan's edits.

        Returns:
            The successful plan's edits.

        """
        planned = cls._plan(tmp_path, sources, consumer_path, *private_imports)
        tm.ok(planned)
        return planned.value

    @classmethod
    def _updated_source(
        cls,
        tmp_path: Path,
        sources: t.MappingKV[Path, str],
        consumer_path: Path,
        *private_imports: str,
    ) -> str:
        """Return the single planned edit's rewritten consumer source.

        Returns:
            The single planned edit's rewritten consumer source.

        """
        return cls._edits(tmp_path, sources, consumer_path, *private_imports)[
            0
        ].updated_source
