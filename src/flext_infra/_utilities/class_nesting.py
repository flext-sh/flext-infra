"""Automatic class-nesting plan derivation from source paths and Rope ASTs."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraUtilitiesClassNesting:
    """Derive class-nesting plans without registries or cached policy state."""

    @staticmethod
    def class_nesting_plans(
        project_root: Path,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.SequenceOf[m.Infra.ClassNestingViolation]:
        """Return plans for top-level classes outside the path-owned namespace."""
        relative = file_path.resolve().relative_to(
            (project_root.resolve() / c.Infra.DEFAULT_SRC_DIR).resolve()
        )
        if relative.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return ()
        namespace = "".join(
            u.derive_class_stem(part)
            for part in (*relative.parts[:-1], relative.stem)
        )
        if not namespace:
            return ()
        private = any(part.startswith("_") for part in relative.parent.parts[1:])
        confidence = (
            "high"
            if private
            else "medium"
            if len(relative.parent.parts) > 1
            else c.Infra.SeverityLevel.LOW
        )
        return tuple(
            m.Infra.ClassNestingViolation(
                file=relative.as_posix(),
                line=class_info.line,
                class_name=class_info.name,
                target_namespace=namespace,
                confidence=confidence,
                rewrite_scope=c.Infra.RK_FILE,
            )
            for class_info in FlextInfraUtilitiesRopeAnalysis.get_class_info(
                rope_project, resource
            )
            if class_info.name != namespace
        )


__all__: list[str] = ["FlextInfraUtilitiesClassNesting"]
