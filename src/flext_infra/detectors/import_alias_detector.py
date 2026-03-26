"""Detect deep imports that should use top-level aliases.

Delegates to ImportNormalizerTransformer for CST-based detection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import FlextInfraScanFileMixin, c, m, p, t


class FlextInfraImportAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect deep import paths that should use top-level aliases."""

    _rule_id: ClassVar[str] = "namespace.import_alias"

    @override
    def _build_message(self, violation: BaseModel) -> str:
        d = violation.model_dump()
        return (
            f"Deep import '{d['current_import']}' should use '{d['suggested_import']}'"
        )

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        return self.detect_file(
            file_path=file_path, rope_project=self._rope, parse_failures=self._pf
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ImportAliasViolation]:
        """Detect deep imports via ImportNormalizerTransformer."""
        del parse_failures, rope_project
        transformer = cls._get_transformer()
        if transformer is None:
            return []
        violations_raw = transformer.detect_file(
            file_path=file_path,
            project_package=cls._discover_package(file_path),
            alias_map=None,
        )
        return [
            m.Infra.ImportAliasViolation.create(
                file=getattr(raw, "file", ""),
                line=getattr(raw, "line", 0),
                current_import=getattr(raw, "current_import", ""),
                suggested_import=getattr(raw, "suggested_import", ""),
            )
            for raw in violations_raw
            if getattr(raw, "violation_type", "") == "deep"
        ]

    @staticmethod
    def _discover_package(file_path: Path) -> str:
        parts = file_path.resolve().parts
        try:
            idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
        except ValueError:
            return ""
        return parts[idx + 1] if idx + 1 < len(parts) else ""

    @staticmethod
    def _get_transformer() -> p.Infra.ImportNormalizerTransformerLike | None:
        mod = __import__(
            "flext_infra.transformers", fromlist=["ImportNormalizerTransformer"]
        )
        obj = getattr(mod, "ImportNormalizerTransformer", None)
        return obj if isinstance(obj, p.Infra.ImportNormalizerTransformerLike) else None


__all__ = ["FlextInfraImportAliasDetector"]
