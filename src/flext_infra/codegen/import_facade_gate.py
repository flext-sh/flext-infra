"""Parametrized facade-import validator executed inside codegen.

One ast-grep rule template, parametrized per package with the package's REAL
exported facade aliases (SSOT: the lazy-init planner's module policy plus the
canonical alias vocabulary), plus two universal matchers. Covers the three
import cases with a single service, never one rule file per package:

- Case A ``from flext_<ns> import <names>``: violation when any bound name is
  not in ``<ns>``'s real allowlist, or when any ``as`` alias is present. This
  is the only case parametrized by ``{PKG}`` + ``{ALLOW}``.
- Case B ``from flext_<ns>.<sub> import ...``: always a violation (the facade is
  imported from the package root only). One universal matcher.
- Case C ``import flext_<ns>...``: always a violation (a module import cannot
  bind a facade alias). One universal matcher.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import override

from flext_core import c as core_c, r
from flext_infra import c, config, p, t, u
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra.base import s
from flext_infra.codegen.lazy_init_planner import FlextInfraCodegenLazyInitPlanner
from flext_infra.workspace.rope import FlextInfraRopeWorkspace

# NOTE (mro-c68a): externals are resolved at the real monorepo root (the parent
# of the .gitmodules workspace), never the worktree parent. These are the
# declared external consumers of the flext ecosystem.
_EXTERNAL_SIBLING_NAMES: t.StrSequence = (
    "algar-oud-mig",
    "algar-oud_mig",
    "gruponos-meltano-native",
)

_CASE_A_TEMPLATE = """id: flext-facade-import-{PKG}
language: python
severity: error
message: "Import only the canonical facade aliases from {PKG}; a concrete class, private symbol, or `as`-alias bypasses the composed namespace/MRO. Use `from {PKG} import c, t, p, m, u` (and the aliases {PKG} really exports)."
rule:
  kind: import_from_statement
  all:
    - has: {{ field: module_name, regex: '^{PKG}$' }}
    - any:
        - has: {{ stopBy: end, kind: aliased_import }}
        - has:
            stopBy: end
            kind: identifier
            all:
              - not: {{ regex: '^{PKG}$' }}
              - not: {{ regex: '^({ALLOW})$' }}
"""

_CASE_B_RULE = r"""id: flext-deep-module-import
language: python
severity: error
message: "Import the facade from the package root, never a deep submodule path. Use `from flext_<ns> import r`, never `from flext_core.result import r`."
rule:
  kind: import_from_statement
  has: { field: module_name, regex: '^flext_[a-z0-9_]+\.' }
"""

_CASE_C_RULE = """id: flext-bare-module-import
language: python
severity: error
message: "Use `from flext_<ns> import <alias>` for the canonical facade, never `import flext_<ns>...` (a module import cannot bind a facade alias)."
rule:
  kind: import_statement
  has: { kind: identifier, stopBy: end, regex: '^flext_[a-z0-9_]+$' }
"""


class FlextInfraCodegenImportFacadeGate(s[bool]):
    """Validate flext facade imports across every internal and external target."""

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the gate and return its CLI success/failure status."""
        report_result = self.build_report()
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "import facade gate build failed"
            )
        verdict = u.Cli.json_pick_str(report_result.value, "verdict", "FAIL")
        if self.successful_verdict(verdict):
            return r[bool].ok(True)
        return r[bool].fail(f"import facade gate verdict: {verdict}")

    def build_report(self) -> p.Result[t.JsonMapping]:
        """Collect findings across the three import cases and build the report."""
        targets = self.scan_targets(self.workspace_root)
        with FlextInfraRopeWorkspace.open_workspace(self.workspace_root) as rope:
            planner = FlextInfraCodegenLazyInitPlanner(
                rope_workspace=rope, lazy_init=config.Infra.tooling.lazy_init
            )
            allowlists = self.package_allowlists(rope, planner)
        findings: list[t.JsonValue] = []
        for pkg, aliases in sorted(allowlists.items()):
            if not aliases:
                continue
            rule = _CASE_A_TEMPLATE.format(
                PKG=re.escape(pkg), ALLOW="|".join(map(re.escape, aliases))
            )
            findings.extend(self.run_rule(rule, targets, case="A", pkg=pkg))
        findings.extend(self.run_rule(_CASE_B_RULE, targets, case="B", pkg=""))
        findings.extend(self.run_rule(_CASE_C_RULE, targets, case="C", pkg=""))
        verdict = "PASS" if not findings else "FAIL"
        report_data: dict[str, t.JsonValue] = {
            "workspace": str(self.workspace_root),
            "generated_at": u.now().isoformat(),
            "verdict": verdict,
            "packages_checked": len(allowlists),
            "targets_checked": len(targets),
            "findings_total": len(findings),
            "findings": findings,
        }
        return r[t.JsonMapping].ok(
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(report_data)
        )

    @classmethod
    def package_allowlists(
        cls, rope: p.Infra.RopeWorkspaceDsl, planner: FlextInfraCodegenLazyInitPlanner
    ) -> t.MappingKV[str, t.StrSequence]:
        """Return each package's real facade-alias allowlist from the SSOT.

        allowlist(P) = expected_alias(P) UNION (raw exports(P) INTERSECT the
        canonical single-letter alias vocabulary). Both terms are SSOT-derived
        (planner module policy + flext-core canonical constant); no hardcoded
        per-package list.
        """
        canonical = frozenset(core_c.ENFORCEMENT_CANONICAL_ALIASES)
        allowlists: dict[str, t.StrSequence] = {}
        for package_dir in cls._package_dirs(rope):
            context = planner.context(package_dir)
            if not context.current_pkg or "." in context.current_pkg:
                continue
            allow = planner.facade_alias_allowlist(context, canonical=canonical)
            allowlists[context.current_pkg] = tuple(sorted(allow))
        return allowlists

    @staticmethod
    def _package_dirs(rope: p.Infra.RopeWorkspaceDsl) -> t.SequenceOf[Path]:
        """Return the top-level ``src`` package dirs of every indexed project."""
        seen: dict[str, Path] = {}
        for entry in rope.workspace_index.packages_by_dir.values():
            pkg = entry.package_name
            if pkg and "." not in pkg:
                seen.setdefault(pkg, entry.package_dir.resolve())
        return tuple(seen.values())

    @classmethod
    def scan_targets(cls, workspace_root: Path) -> t.SequenceOf[Path]:
        """Return every internal and external directory to scan."""
        monorepo_root = u.Infra.rope_workspace_root(workspace_root)
        roots: list[Path] = []
        pyproject_result = FlextInfraUtilitiesDiscovery.find_all_pyproject_files(
            monorepo_root
        )
        if pyproject_result.success:
            roots.extend(
                pyproject.parent
                for pyproject in pyproject_result.value
                if (pyproject.parent / c.Infra.DEFAULT_SRC_DIR).is_dir()
            )
        external_parent = cls._externals_parent(monorepo_root)
        roots.extend(
            candidate
            for name in _EXTERNAL_SIBLING_NAMES
            if (candidate := external_parent / name).is_dir()
        )
        targets: dict[str, Path] = {}
        for root in roots:
            for sub in ("src", "tests", "examples", "scripts"):
                candidate = (root / sub).resolve()
                if candidate.is_dir():
                    targets.setdefault(str(candidate), candidate)
        return tuple(targets.values())

    @staticmethod
    def _externals_parent(monorepo_root: Path) -> Path:
        """Return the directory that holds the declared external consumers.

        The externals live beside the main checkout of the flext monorepo. When
        run from a git worktree, ``monorepo_root`` is the worktree, so the main
        checkout is resolved from the shared git common dir (``.../flext/.git``
        -> ``.../flext`` -> parent). Falls back to the workspace parent.
        """
        run = u.Cli.run_raw(
            [c.Infra.GIT, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=monorepo_root,
        )
        if run.success and run.value.exit_code == 0:
            common_dir = run.value.stdout.strip()
            if common_dir:
                return Path(common_dir).parent.parent
        return monorepo_root.parent

    @staticmethod
    def run_rule(
        rule: str, targets: t.SequenceOf[Path], *, case: str, pkg: str
    ) -> t.SequenceOf[t.JsonValue]:
        """Run one ast-grep inline rule over all targets and parse findings."""
        if not targets:
            return []
        cmd: list[str] = [
            c.Infra.SG,
            c.Infra.SCAN,
            "--inline-rules",
            rule,
            "--json=stream",
            *(str(target) for target in targets),
        ]
        run = u.Cli.run_raw(cmd, timeout=c.Infra.TIMEOUT_DEFAULT)
        if run.failure or run.value.exit_code not in {0, 1}:
            return []
        findings: list[t.JsonValue] = []
        for line in (run.value.stdout or "").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            parsed = u.Cli.json_parse(stripped)
            if parsed.failure:
                continue
            entry = u.Cli.json_as_mapping(parsed.value)
            findings.append({
                "case": case,
                "package": pkg,
                "file": u.Cli.json_pick_str(entry, "file"),
                "line": u.Cli.json_nested_int(entry, "range.start.line") + 1,
                "text": u.Cli.json_pick_str(entry, "lines").strip(),
            })
        return findings

    @staticmethod
    def successful_verdict(verdict: str) -> bool:
        """Return True for verdicts that should exit with status 0."""
        return verdict == "PASS"


__all__: list[str] = ["FlextInfraCodegenImportFacadeGate"]
