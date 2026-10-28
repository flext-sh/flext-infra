"""Rope reference-site and module-tier helpers for FlextInfraUtilitiesRopeInventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._rope.rope_imports import FlextInfraUtilitiesRopeImports


class FlextInfraUtilitiesRopeInventorySites:
    """Reference-site, fingerprint, and facade-tier helpers of the inventory."""

    @staticmethod
    def _location_line(location: t.Infra.RopeLocation) -> int:
        """Location line.

        Returns:
            The resulting ``int``.

        """
        line = getattr(location, "lineno", None)
        return line if isinstance(line, int) and line >= 0 else 0

    @staticmethod
    def _reference_site(location: t.Infra.RopeLocation) -> m.Infra.ReferenceSite | None:
        """Build a reference site from a rope location.

        Returns:
            The resulting ``m.Infra.ReferenceSite | None``.

        """
        file_path = FlextInfraUtilitiesRopeImports.location_file_path(location)
        if file_path is None:
            return None
        return m.Infra.ReferenceSite(
            file_path=FlextInfraUtilitiesRopeInventorySites._normalize_file_path(
                file_path
            ),
            line=FlextInfraUtilitiesRopeInventorySites._location_line(location),
            surface=FlextInfraUtilitiesRopeInventorySites._reference_surface(file_path),
        )

    @staticmethod
    def _discard_definition_site(
        sites: list[m.Infra.ReferenceSite],
        *,
        definition_path: Path,
        line: int,
    ) -> None:
        """Discard definition site."""
        definition_key = (
            FlextInfraUtilitiesRopeInventorySites._normalize_file_path(definition_path),
            line,
        )
        match_index = next(
            (
                index
                for index, site in enumerate(sites)
                if (site.file_path, site.line) == definition_key
            ),
            None,
        )
        if match_index is not None:
            sites.pop(match_index)

    @staticmethod
    def _normalize_file_path(file_path: Path) -> str:
        """Normalize file path.

        Returns:
            The resulting ``str``.

        """
        return str(file_path.resolve() if file_path.is_absolute() else file_path)

    @staticmethod
    def _is_definition_occurrence(
        location: t.Infra.RopeLocation,
        *,
        definition_path: Path | None,
        line: int,
        offset: int,
    ) -> bool:
        """Is definition occurrence.

        Returns:
            The resulting ``bool``.

        """
        location_path = FlextInfraUtilitiesRopeImports.location_file_path(location)
        if (
            definition_path is not None
            and location_path is not None
            and location_path != definition_path
        ):
            return False
        location_line = getattr(location, "lineno", None)
        if isinstance(location_line, int) and location_line != line:
            return False
        location_offset = getattr(location, "offset", None)
        if isinstance(location_offset, int):
            return location_offset == offset
        return bool(
            definition_path is not None
            and location_path == definition_path
            and location_line == line,
        )

    @staticmethod
    def _reference_surface(file_path: Path | None) -> str:
        """Return the reference surface for a file path.

        Returns:
            The reference surface for a file path.

        """
        default_src: str = c.Infra.DEFAULT_SRC_DIR
        if file_path is None:
            return default_src
        parts = set(file_path.parts)
        tests_dir: str = c.Infra.DIR_TESTS
        if tests_dir in parts:
            return tests_dir
        examples_dir: str = c.Infra.DIR_EXAMPLES
        if examples_dir in parts:
            return examples_dir
        scripts_dir: str = c.Infra.DIR_SCRIPTS
        if scripts_dir in parts:
            return scripts_dir
        return default_src

    @staticmethod
    def _fingerprint(
        source: str,
        *,
        name: str,
        line: int,
        child_scope: p.Infra.RopeScopeDsl | None,
    ) -> str:
        """Fingerprint.

        Returns:
            The resulting ``str``.

        """
        start = max(1, line)
        end = child_scope.get_end() if child_scope is not None else start
        end = max(end, start)
        lines = source.splitlines()
        snippet = "\n".join(lines[start - 1 : end])
        return " ".join(snippet.replace(name, "<name>").split())

    @staticmethod
    def _actual_tier(convention: m.Infra.RopeModuleConvention) -> str:
        """Classify the containing package before the module filename.

        ``relative_path`` is local to the indexed package and can contain only
        the basename. The qualified package identity retains its family without
        admitting unrelated ancestor directories of the checkout.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If directory or filename families are ambiguous.

        """
        families = FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        directory_families = {
            family.suffix
            for family in families
            if family.directories.intersection(convention.package_name.split("."))
        }
        if len(directory_families) > 1:
            msg = (
                f"ambiguous facade family directories for {convention.relative_path}: "
                f"{sorted(directory_families)}"
            )
            raise ValueError(msg)
        if directory_families:
            return next(iter(directory_families))
        file_families = {
            family.suffix
            for family in families
            if convention.file_path.name in family.file_names
        }
        if len(file_families) > 1:
            msg = (
                f"ambiguous facade family filename for {convention.relative_path}: "
                f"{sorted(file_families)}"
            )
            raise ValueError(msg)
        if file_families:
            return next(iter(file_families))
        policy = convention.module_policy
        expected: str = policy.expected_family or ""
        if expected:
            return expected
        if "services" in convention.relative_path.parts:
            return "Services"
        stem: str = convention.file_path.stem
        return stem

    @staticmethod
    def _expected_tier(convention: m.Infra.RopeModuleConvention, *, kind: str) -> str:
        """Return the expected tier for a module convention.

        Returns:
            The expected tier for a module convention.

        """
        if kind == "constant":
            return FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                c.Infra.CONSTANTS_PY,
            ).suffix
        return FlextInfraUtilitiesRopeInventorySites._actual_tier(convention)

    @staticmethod
    def _is_facade_member(
        convention: m.Infra.RopeModuleConvention,
        *,
        name: str,
        scope_chain: t.StrSequence,
    ) -> bool:
        """Is facade member.

        Returns:
            The resulting ``bool``.

        """
        if scope_chain:
            return False
        layout = convention.project_layout
        family = convention.module_policy.expected_family or ""
        alias = convention.module_policy.expected_alias or ""
        if name == alias:
            return True
        return bool(
            layout is not None and family and name == f"{layout.class_stem}{family}",
        )


__all__: list[str] = ["FlextInfraUtilitiesRopeInventorySites"]
