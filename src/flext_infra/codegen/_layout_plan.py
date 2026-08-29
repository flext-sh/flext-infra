"""Pure planning for the project-layout engine (mro-0wuz, epic mro-hzox).

Every classification derives from ``config.Infra.codegen.layout`` — this mixin
reads the declarative SSOT and produces typed findings; it never writes.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path

from flext_infra import c, config, m, t, u


class FlextInfraCodegenLayoutPlanMixin:
    """Build the per-project layout plan from the declarative layout SSOT."""

    @property
    def _layout_spec(self) -> m.Infra.LayoutSpec:
        """Layout SSOT loaded once through the validated config singleton."""
        return config.Infra.codegen.layout

    def plan_project(self, project_dir: Path) -> m.Infra.LayoutProjectReport:
        """Classify every root entry of one project without writing anything."""
        spec = self._layout_spec
        project_name = project_dir.name
        allowed = self._allowed_root_names(spec)
        findings: list[m.Infra.LayoutFinding] = []
        for entry in sorted(project_dir.iterdir()):
            name = entry.name
            if spec.allow_hidden and name.startswith("."):
                continue
            if name in spec.special_root_dirs:
                continue
            if name in allowed:
                continue
            findings.append(self._classify_root_entry(spec, project_name, entry))
        findings.extend(self._gitignore_findings(spec, project_dir))
        return m.Infra.LayoutProjectReport(
            project=project_name, findings=tuple(findings)
        )

    @staticmethod
    def _allowed_root_names(spec: m.Infra.LayoutSpec) -> frozenset[str]:
        """Canonical root names from the generic layout contract."""
        return frozenset({
            *spec.canonical_root_files,
            *spec.canonical_root_dotfiles,
            *spec.canonical_root_dirs,
            *spec.special_root_dirs,
            *spec.reference_root_dirs,
        })

    def _classify_root_entry(
        self, spec: m.Infra.LayoutSpec, project_name: str, entry: Path
    ) -> m.Infra.LayoutFinding:
        """Classify one non-canonical root entry into move/archive/review."""
        name = entry.name
        if entry.is_dir() and name in spec.move_docs_dirs:
            return self._finding("move", name, f"{spec.docs_target}/{name}")
        if entry.is_file() and name in spec.move_docs_files:
            target = f"{spec.docs_target}/{name}"
            if (entry.parent / target).exists():
                return self._finding(
                    "archive",
                    name,
                    f"{spec.archive_root}/{project_name}/{name}",
                    message=(
                        f"archive {name} -> {spec.archive_root}/{project_name}/{name} "
                        f"(canonical docs/{name} kept)"
                    ),
                )
            return self._finding("move", name, target)
        if entry.is_file() and name in spec.move_example_files:
            return self._finding("move", name, f"{spec.examples_target}/{name}")
        if entry.is_file() and any(
            fnmatchcase(name, glob) for glob in spec.move_diagram_globs
        ):
            return self._finding("move", name, f"{spec.diagrams_target}/{name}")
        if name in spec.archive_names or any(
            fnmatchcase(name, glob) for glob in spec.archive_globs
        ):
            return self._finding(
                "archive", name, f"{spec.archive_root}/{project_name}/{name}"
            )
        return self._finding("review", name)

    def _gitignore_findings(
        self, spec: m.Infra.LayoutSpec, project_dir: Path
    ) -> t.SequenceOf[m.Infra.LayoutFinding]:
        """Missing ``.gitignore`` patterns required by the layout SSOT."""
        required = [f"{spec.archive_root}/"]
        current = ""
        gitignore_path = project_dir / c.Infra.GITIGNORE
        if gitignore_path.is_file():
            read = u.Cli.files_read_text(gitignore_path)
            if read.success:
                current = read.value
        covered = {line.strip() for line in current.splitlines()}
        findings: list[m.Infra.LayoutFinding] = []
        for pattern in required:
            if pattern in covered or pattern.rstrip("/") in covered:
                continue
            findings.append(self._finding("gitignore", c.Infra.GITIGNORE, pattern))
        return tuple(findings)

    @staticmethod
    def _finding(
        rule: t.Infra.LayoutRule,
        path: str,
        target: str = "",
        *,
        message: str | None = None,
    ) -> m.Infra.LayoutFinding:
        """Build one typed finding with a canonical message."""
        messages: t.MappingKV[t.Infra.LayoutRule, str] = {
            "move": f"move {path} -> {target}",
            "archive": f"archive {path} -> {target}",
            "gitignore": f"add .gitignore entry: {target}",
            "review": f"non-canonical root entry requires review: {path}",
        }
        return m.Infra.LayoutFinding(
            rule=rule,
            path=path,
            target=target,
            message=message if message is not None else messages[rule],
        )


__all__: list[str] = ["FlextInfraCodegenLayoutPlanMixin"]
