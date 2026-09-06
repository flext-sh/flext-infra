"""Loose class detection and scanning for flext-infra refactor."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraRefactorLooseClassScanner:
    """Scan a project tree using rope and report loose top-level classes."""

    def scan(self, project_root: Path) -> p.Result[t.JsonMapping]:
        """Scan *project_root*/src and return a violation report dict."""
        src_root = project_root / c.Infra.DEFAULT_SRC_DIR
        if not src_root.is_dir():
            out: p.Result[t.JsonMapping] = r[t.JsonMapping].fail(
                f"src not found: {src_root}"
            )
            return out
        violations, targets_found, classes_scanned, files_scanned = (
            self._scan_discovered_files(project_root=project_root)
        )
        return r[t.JsonMapping].ok(
            self._build_report(
                files_scanned=files_scanned,
                violations=violations,
                targets_found=targets_found,
                classes_scanned=classes_scanned,
            )
        )

    def _scan_discovered_files(
        self, *, project_root: Path
    ) -> tuple[t.SequenceOf[m.Infra.LooseClassViolation], t.BoolMapping, int, int]:
        """Scan discovered files."""
        violations: t.MutableSequenceOf[m.Infra.LooseClassViolation] = []
        targets_found: dict[str, bool] = dict.fromkeys(
            c.Infra.REQUIRED_CLASS_TARGETS, False
        )
        classes_scanned = 0
        files_scanned = 0
        src_root = (project_root / c.Infra.DEFAULT_SRC_DIR).resolve()
        with u.Infra.open_project(project_root) as rope_project:
            for resource in rope_project.get_python_files():
                file_path = Path(resource.real_path).resolve()
                if not file_path.is_relative_to(src_root):
                    continue
                if (
                    file_path.name.startswith("__")
                    and file_path.name != c.Infra.INIT_PY
                ):
                    continue
                files_scanned += 1
                rel_path = file_path.relative_to(src_root)
                class_info = u.Infra.get_class_info(rope_project, resource)
                classes_scanned += len(class_info)
                for occ in (
                    m.Infra.ClassOccurrence(
                        name=ci.name, line=ci.line, is_top_level=True
                    )
                    for ci in class_info
                ):
                    viol = self._build_violation(file_path, rel_path, occ)
                    if viol is None:
                        continue
                    violations.append(viol)
                    if viol.class_name in targets_found:
                        targets_found[viol.class_name] = True
        return (tuple(violations), targets_found, classes_scanned, files_scanned)

    def _build_report(
        self,
        *,
        files_scanned: int,
        violations: t.SequenceOf[m.Infra.LooseClassViolation],
        targets_found: t.BoolMapping,
        classes_scanned: int,
    ) -> t.JsonMapping:
        """Build report."""
        counters = Counter(v.confidence for v in violations)
        violations_infra: t.SequenceOf[t.Infra.InfraValue] = [
            v.model_dump() for v in violations
        ]
        confidence_counts: t.MappingKV[str, t.Infra.InfraValue] = dict(counters)
        required_targets_infra: t.MappingKV[str, t.Infra.InfraValue] = dict(
            targets_found
        )
        result: t.JsonMapping = t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
            "rule": c.Infra.RK_CLASS_NESTING,
            "files_scanned": files_scanned,
            "classes_scanned": classes_scanned,
            c.Infra.RK_VIOLATIONS_COUNT: len(violations),
            "confidence_counts": confidence_counts,
            "required_targets": required_targets_infra,
            c.Infra.RK_VIOLATIONS: violations_infra,
        })
        return result

    def _build_violation(
        self, file_path: Path, rel_path: Path, occ: m.Infra.ClassOccurrence
    ) -> m.Infra.LooseClassViolation | None:
        """Report a top-level class that is not the module's own facade.

        The facade a module may declare at top level is the family class its
        namespace policy derives from the module's own ``__all__``; every other
        top-level class belongs nested under that facade. The same derivation
        names the nesting target, so discovery and target share one owner.
        """
        if not occ.is_top_level:
            return None
        family = u.Infra.policy(file_path, rel_path=rel_path).expected_family
        if family is not None and occ.name == family:
            return None
        confidence = self._confidence_from_location(rel_path)
        score = c.Infra.CONFIDENCE_TO_SCORE[confidence]
        return m.Infra.LooseClassViolation(
            file=rel_path.as_posix(),
            line=max(occ.line, 1),
            class_name=occ.name,
            expected_prefix=family or "",
            rule=c.Infra.RK_CLASS_NESTING,
            reason="top_level_class_in_private_directory"
            if self._has_private_directory(rel_path)
            else "top_level_class_without_namespace_prefix",
            confidence=confidence,
            score=round(score, 2),
        )

    def _confidence_from_location(self, rel_path: Path) -> str:
        """Confidence from location."""
        parts = rel_path.parent.parts[1:]
        if any(p.startswith("_") for p in parts):
            return "high"
        return "medium" if parts else c.Infra.SeverityLevel.LOW

    def _has_private_directory(self, rel_path: Path) -> bool:
        """Has private directory."""
        return any(p.startswith("_") for p in rel_path.parent.parts[1:])


__all__: list[str] = ["FlextInfraRefactorLooseClassScanner"]
