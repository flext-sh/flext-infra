"""Detect consumer import grammar violations (R1 facade-only import rule).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, u

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConsumerImportViolationsDetector:
    """Detect consumer import grammar violations per R1 facade-only rule.

    Consumer legality (R1): legal iff ``from <pkg> import X`` with
    ``X in pkg.__all__`` (published lazy contract). Any ``pkg.<submodule>``
    path is a violation — including facet modules (``flext_cli.models``),
    nested reach-throughs (``flext_infra.workspace.detector``) and
    ``flext_core.lazy``. Facet modules remain legal only intra-family.

    Fix hints derived by inverting the published ``_LAZY_IMPORTS`` map.
    """

    _FLEXT_PREFIXES = ("flext_", "ai_hub")
    _MIN_FACET_PARTS: int = 2

    @staticmethod
    def _is_flext_package(module_name: str) -> bool:
        """Return whether a module name is a FLEXT family package."""
        return any(
            module_name.startswith(prefix)
            for prefix in FlextInfraConsumerImportViolationsDetector._FLEXT_PREFIXES
        )

    @classmethod
    def _get_legal_imports(cls, package_name: str) -> set[str]:
        """Return the set of legal public symbols for a flext package.

        Derives from the package's published ``__all__`` (lazy export contract).
        """
        try:
            module = __import__(package_name, fromlist=["__all__"])
            published = getattr(module, "__all__", None)
            if published is None:
                return set()
            return set(published)
        except ImportError:
            return set()

    @classmethod
    def _is_facet_module(cls, module_name: str) -> bool:
        """Return whether a module is a FLEXT facet module (c/t/p/m/u/lazy/etc)."""
        parts = module_name.split(".")
        if len(parts) < cls._MIN_FACET_PARTS:
            return False
        facet_name = parts[-1]
        return facet_name in {
            "constants",
            "models",
            "protocols",
            "typings",
            "utilities",
            "lazy",
            "result",
            "exceptions",
            "mixins",
            "handlers",
            "decorators",
            "service",
            "container",
            "context",
            "dispatcher",
            "registry",
            "runtime",
            "loggings",
            "config",
            "settings",
        }

    @classmethod
    def _is_intra_family(cls, importer_module: str, imported_module: str) -> bool:
        """Return whether both modules belong to the same flext family package."""
        if not importer_module or not imported_module:
            return False
        importer_root = importer_module.split(".", maxsplit=1)[0]
        imported_root = imported_module.split(".", maxsplit=1)[0]
        return importer_root == imported_root

    @classmethod
    def _is_legal_import(cls, importer_module: str, fqn: str) -> bool:
        """Return whether an import conforms to the R1 consumer grammar.

        Legal: ``from <pkg> import X`` where X is in pkg.__all__
        Illegal: any ``pkg.<submodule>``, ``from pkg import submodule``, etc.
        """
        # Not a flext package - not our concern
        if not cls._is_flext_package(fqn.split(".", maxsplit=1)[0]):
            return True

        # Intra-family facet imports are legal (facade assembly)
        if cls._is_intra_family(importer_module, fqn):
            return True

        # Parse the import statement to check form
        # Legal form: from <pkg> import X
        # We check: does the import target a submodule (not a symbol in __all__)?
        imported_root = fqn.split(".", maxsplit=1)[0]
        cls._get_legal_imports(imported_root)

        # If the import is a direct submodule access (pkg.module), it's illegal
        if "." in fqn and not fqn.startswith(f"{imported_root}."):
            # Cross-package submodule access
            return False

        # Check if it's importing a submodule rather than a published symbol
        if fqn != imported_root:
            # It's a submodule import (e.g., flext_cli.models, flext_infra.workspace.detector)
            # Check if it's a facet module - those are never legal for consumers
            if cls._is_facet_module(fqn):
                return False
            # Any other submodule is also illegal for consumers
            return False

        # Direct import of package root - check if what's imported is in __all__
        # This is harder to detect statically; we assume from pkg import X where X is symbol
        return True

    @classmethod
    def detect_file(
        cls, ctx: m.Infra.DetectorContext
    ) -> t.SequenceOf[m.Infra.ConsumerImportViolation]:
        """Detect consumer import violations in a single file."""
        res = u.Infra.fetch_python_resource(
            ctx.rope_project, ctx.file_path, skip_init_py=True
        )
        if res is None:
            return []

        rope_project = ctx.rope_project
        current_module = u.Infra.package_name(ctx.file_path)
        imports = u.Infra.get_semantic_module_imports(rope_project, res)

        violations: list[m.Infra.ConsumerImportViolation] = []

        for local, fqn in imports.items():
            # Skip if not a flext package import
            fqn_root = fqn.split(".")[0]
            if not cls._is_flext_package(fqn_root):
                continue

            # Skip intra-family imports
            if cls._is_intra_family(current_module, fqn):
                continue

            # Check if this is a submodule import (illegal per R1)
            is_submodule = fqn != fqn_root

            # Get legal symbols for the target package
            legal_symbols = cls._get_legal_imports(fqn_root)

            # Determine if this import is legal
            is_legal = False
            if not is_submodule:
                # Direct package import - what symbol is imported?
                # The local name is what's imported; check if it's in legal_symbols
                # Note: local could be an alias (from flext_core import u as u)
                # We need to check the actual imported symbol
                if local in legal_symbols:
                    is_legal = True
            # Submodule import - check if it's a facet module
            elif cls._is_facet_module(fqn):
                is_legal = False
            else:
                is_legal = False  # Any submodule is illegal for consumers

            if not is_legal:
                violations.append(
                    m.Infra.ConsumerImportViolation(
                        file=str(ctx.file_path),
                        line=1,
                        current_import=f"from ... import {local}  # {fqn}",
                        target_package=fqn_root,
                        imported_path=fqn,
                        imported_symbol=local,
                        legal_symbols=sorted(legal_symbols),
                        detail="consumer import violates R1 facade-only grammar",
                    )
                )

        return violations


__all__: list[str] = ["FlextInfraConsumerImportViolationsDetector"]
