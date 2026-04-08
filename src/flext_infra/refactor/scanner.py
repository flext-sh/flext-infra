"""Loose class detection and scanning for flext-infra refactor."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, r, t, u


class FlextInfraRefactorLooseClassScanner:
    """Scan a project tree using rope and report loose top-level classes."""

    def scan(self, project_root: Path) -> r[t.Infra.ContainerDict]:
        """Scan *project_root*/src and return a violation report dict."""
        files_result = self._discover_python_files(project_root)
        if files_result.is_failure:
            out: r[t.Infra.ContainerDict] = r[t.Infra.ContainerDict].fail(
                files_result.error or "discovery failed",
            )
            return out
        discovered_files = files_result.value
        violations, targets_found, classes_scanned = self._scan_discovered_files(
            project_root=project_root,
            discovered_files=discovered_files,
        )
        return r[t.Infra.ContainerDict].ok(
            self._build_report(
                discovered_files=discovered_files,
                violations=violations,
                targets_found=targets_found,
                classes_scanned=classes_scanned,
            ),
        )

    def _scan_discovered_files(
        self,
        *,
        project_root: Path,
        discovered_files: Sequence[Path],
    ) -> tuple[Sequence[m.Infra.LooseClassViolation], Mapping[str, bool], int]:
        violations: MutableSequence[m.Infra.LooseClassViolation] = []
        targets_found: dict[str, bool] = dict.fromkeys(
            c.Infra.REQUIRED_CLASS_TARGETS,
            False,
        )
        classes_scanned = 0
        src_root = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        rope_project = u.Infra.init_rope_project(src_root)
        try:
            for file_path in discovered_files:
                parsed = self._scan_file_with_rope(rope_project, file_path)
                if parsed.is_failure:
                    continue
                occurrences = parsed.value
                classes_scanned += len(occurrences)
                rel = self._relative_module_path(project_root, file_path)
                if rel.is_failure:
                    continue
                rel_path = rel.value
                for occ in occurrences:
                    viol = self._build_violation(rel_path, occ)
                    if viol is None:
                        continue
                    violations.append(viol)
                    if viol.class_name in targets_found:
                        targets_found[viol.class_name] = True
        finally:
            rope_project.close()
        return (tuple(violations), targets_found, classes_scanned)

    def _build_report(
        self,
        *,
        discovered_files: Sequence[Path],
        violations: Sequence[m.Infra.LooseClassViolation],
        targets_found: Mapping[str, bool],
        classes_scanned: int,
    ) -> t.Infra.ContainerDict:
        counters = Counter(v.confidence for v in violations)
        violations_infra: Sequence[t.Infra.InfraValue] = [
            v.model_dump() for v in violations
        ]
        confidence_counts: Mapping[str, t.Infra.InfraValue] = dict(counters)
        required_targets_infra: Mapping[str, t.Infra.InfraValue] = dict(targets_found)
        return {
            "rule": c.Infra.ReportKeys.CLASS_NESTING,
            "files_scanned": len(discovered_files),
            "classes_scanned": classes_scanned,
            c.Infra.ReportKeys.VIOLATIONS_COUNT: len(violations),
            "confidence_counts": confidence_counts,
            "required_targets": required_targets_infra,
            c.Infra.ReportKeys.VIOLATIONS: violations_infra,
        }

    def _build_violation(
        self,
        rel_path: Path,
        occ: m.Infra.ClassOccurrence,
    ) -> m.Infra.LooseClassViolation | None:
        if not occ.is_top_level:
            return None
        prefix = self._expected_prefix_for_module(rel_path)
        if prefix and occ.name.startswith(prefix):
            return None
        confidence = self._confidence_from_location(rel_path)
        score = c.Infra.CONFIDENCE_TO_SCORE[confidence]
        return m.Infra.LooseClassViolation(
            file=rel_path.as_posix(),
            line=max(occ.line, 1),
            class_name=occ.name,
            expected_prefix=prefix,
            rule=c.Infra.ReportKeys.CLASS_NESTING,
            reason="top_level_class_in_private_directory"
            if self._has_private_directory(rel_path)
            else "top_level_class_without_namespace_prefix",
            confidence=confidence,
            score=round(score, 2),
        )

    def _confidence_from_location(self, rel_path: Path) -> str:
        parts = rel_path.parent.parts[1:]
        if any(p.startswith("_") for p in parts):
            return "high"
        return "medium" if parts else c.Infra.Severity.LOW

    def _discover_python_files(self, project_root: Path) -> r[Sequence[Path]]:
        src = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src.is_dir():
            out: r[Sequence[Path]] = r[Sequence[Path]].fail(f"src not found: {src}")
            return out
        file_list: Sequence[Path] = [
            fp
            for fp in u.Infra.iter_directory_python_files(src)
            if not (fp.name.startswith("__") and fp.name != c.Infra.Files.INIT_PY)
        ]
        out2: r[Sequence[Path]] = r[Sequence[Path]].ok(file_list)
        return out2

    def _expected_prefix_for_module(self, rel_path: Path) -> str:
        parts = rel_path.parts
        if len(parts) < c.Infra.MIN_PATH_DEPTH:
            return ""
        pc = self._pascal_case
        proj = pc(parts[0].split("_", maxsplit=1)[0])
        dirs = "".join(pc(p) for p in parts[1:-1])
        return f"{proj}{dirs}{pc(rel_path.stem)}"

    def _has_private_directory(self, rel_path: Path) -> bool:
        return any(p.startswith("_") for p in rel_path.parent.parts[1:])

    def _pascal_case(self, value: str) -> str:
        norm = c.Infra.CLASS_PATTERN.sub(" ", value.replace("_", " "))
        return "".join(w.capitalize() for w in norm.split())

    def _relative_module_path(self, project_root: Path, file_path: Path) -> r[Path]:
        src = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        try:
            rel: Path = file_path.relative_to(src)
            out: r[Path] = r[Path].ok(rel)
            return out
        except ValueError as exc:
            out2: r[Path] = r[Path].fail(str(exc))
            return out2

    def _scan_file_with_rope(
        self,
        rope_project: t.Infra.RopeProject,
        file_path: Path,
    ) -> r[Sequence[m.Infra.ClassOccurrence]]:
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            out: r[Sequence[m.Infra.ClassOccurrence]] = r[
                Sequence[m.Infra.ClassOccurrence]
            ].fail(f"{file_path}: parse_failed")
            return out
        classes = [
            m.Infra.ClassOccurrence(
                name=ci.name,
                line=ci.line,
                is_top_level=True,
            )
            for ci in u.Infra.get_class_info(rope_project, res)
        ]
        return r[Sequence[m.Infra.ClassOccurrence]].ok(classes)


__all__ = ["FlextInfraRefactorLooseClassScanner"]
