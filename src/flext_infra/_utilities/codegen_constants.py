"""Constant detection, analysis, and transformation for codegen.

SSOT module for constant census, deduplication, MRO attribute analysis,
inline value detection, and consolidation with lint-validated rollback.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
import importlib
import operator
import re
from collections import defaultdict
from collections.abc import (
    Callable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import ClassVar, Final

from flext_cli import FlextCliUtilities
from flext_core import r, u
from flext_infra import c, m, t

from .discovery import FlextInfraUtilitiesDiscovery
from .rope import FlextInfraUtilitiesRope
from .subprocess import FlextInfraUtilitiesSubprocess

# =====================================================================
# Governance — canonical values and rule configuration
# =====================================================================


class FlextInfraUtilitiesCodegenGovernance:
    """Loads and caches constants-governance YAML config."""

    _config_cache: ClassVar[MutableMapping[str, m.Infra.ConstantsGovernanceConfig]] = {}
    GOVERNANCE_FILE: Final[Path] = (
        Path(__file__).parent.parent / "rules" / "constants-governance.yml"
    )

    @staticmethod
    def load_governance_config() -> m.Infra.ConstantsGovernanceConfig:
        cached = FlextInfraUtilitiesCodegenGovernance._config_cache.get("config")
        if cached is not None:
            return cached
        raw = FlextCliUtilities.Cli.yaml_load_mapping(
            FlextInfraUtilitiesCodegenGovernance.GOVERNANCE_FILE
        )
        config = m.Infra.ConstantsGovernanceConfig.model_validate(raw)
        FlextInfraUtilitiesCodegenGovernance._config_cache["config"] = config
        return config

    @staticmethod
    def is_rule_fixable(rule_id: str, module: str) -> bool:
        config = FlextInfraUtilitiesCodegenGovernance.load_governance_config()
        for rule in config.rules:
            if rule.id != rule_id:
                continue
            if not rule.fixable:
                return False
            if rule.fixable_exclusion is None:
                return True
            return not module.endswith(rule.fixable_exclusion)
        return False


# =====================================================================
# Detection — constant declarations and usages
# =====================================================================


class FlextInfraUtilitiesCodegenConstantDetection:
    """Regex-based detection of constant declarations and usages."""

    @staticmethod
    def iter_py_files(
        root: Path,
        exclude: frozenset[str] = frozenset(),
        *,
        max_files: int = 0,
    ) -> Iterator[Path]:
        """Yield ``*.py`` files under *root*, skipping excluded dirs."""
        count = 0
        for py_file in root.rglob(c.Infra.Extensions.PYTHON_GLOB):
            if max_files and count >= max_files:
                return
            if any(excl in py_file.parts for excl in exclude):
                continue
            count += 1
            yield py_file

    @staticmethod
    def read_source_safe(path: Path) -> str | None:
        """Read a file, returning ``None`` on error."""
        try:
            return path.read_text(c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def is_quoted(value: str) -> bool:
        """Check if a string value is quoted."""
        return (
            len(value) >= c.Infra.Detection.MIN_QUOTED_LITERAL_LEN
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        )

    @staticmethod
    def unquote(value: str) -> str:
        """Remove surrounding quotes from a string value."""
        det = FlextInfraUtilitiesCodegenConstantDetection
        return value[1:-1] if det.is_quoted(value) else value

    @staticmethod
    def infer_project(py_file: Path, root: Path) -> str:
        """Infer the project name from a Python file path."""
        try:
            parts = py_file.relative_to(root).parts
            src = c.Infra.Paths.DEFAULT_SRC_DIR
            if src in parts:
                idx = parts.index(src)
                if idx + 1 < len(parts):
                    return parts[idx + 1].replace("_", "-")
        except ValueError:
            pass
        return "unknown"

    @staticmethod
    def walk_mro_attrs(
        target_cls: type,
        *,
        skip_types: bool = False,
    ) -> Iterator[tuple[str, object, str, str]]:
        """Yield ``(attr_name, attr_value, qualname, module)`` from MRO."""
        for klass in reversed(target_cls.__mro__):
            if klass is object:
                continue
            for name, value in dict(vars(klass)).items():
                if name.startswith("_"):
                    continue
                if skip_types and isinstance(value, type):
                    continue
                yield (
                    name,
                    value,
                    klass.__qualname__,
                    getattr(klass, "__module__", ""),
                )

    @staticmethod
    def scan_patterns(
        source: str,
        patterns: Sequence[t.Infra.RegexPattern],
    ) -> tuple[Sequence[t.Infra.StrIntPair], ...]:
        """Scan *source* for multiple regex patterns."""
        results: list[MutableSequence[t.Infra.StrIntPair]] = [[] for _ in patterns]
        for line_num, line in enumerate(source.splitlines(), 1):
            for i, pat in enumerate(patterns):
                for match in pat.finditer(line):
                    results[i].append((match.group(1), line_num))
        return tuple(results)

    @staticmethod
    def semantic_name_matches(symbol_name: str, canonical_name: str) -> bool:
        """Return True when *symbol_name* semantically matches *canonical_name*."""
        if not canonical_name:
            return False
        cn = canonical_name.lower().replace("_", "")
        sn = symbol_name.lower().replace("_", "")
        return cn == sn or sn in cn

    # ── Definitions ──────────────────────────────────────────────────

    @staticmethod
    def extract_constant_definitions(
        file_path: Path,
        project: str,
    ) -> Sequence[m.Infra.ConstantDefinition]:
        """Extract ``NAME: Final[...] = VALUE`` declarations from a file."""
        source = FlextInfraUtilitiesCodegenConstantDetection.read_source_safe(file_path)
        if source is None:
            return []
        definitions: MutableSequence[m.Infra.ConstantDefinition] = []
        class_stack: MutableSequence[t.Infra.StrIntPair] = []

        for line_num, line in enumerate(source.splitlines(), 1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)

            if stripped.startswith("class ") and stripped.endswith(":"):
                cm = c.Infra.Detection.CLASS_DECL_RE.match(stripped)
                if cm:
                    while class_stack and class_stack[-1][1] >= indent:
                        class_stack.pop()
                    class_stack.append((cm.group(1), indent))

            while class_stack and indent <= class_stack[-1][1]:
                class_stack.pop()

            match = c.Infra.Detection.FINAL_DECL_RE.match(line)
            if match:
                definitions.append(
                    m.Infra.ConstantDefinition(
                        name=match.group("name"),
                        value_repr=match.group("value").strip(),
                        type_annotation=match.group("ann"),
                        file_path=str(file_path),
                        class_path=".".join(n for n, _ in class_stack),
                        project=project,
                        line=line_num,
                    )
                )
        return definitions

    @staticmethod
    def extract_all_constant_definitions(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[m.Infra.ConstantDefinition]]:
        """Extract all constant definitions across workspace."""
        all_defs: defaultdict[str, MutableSequence[m.Infra.ConstantDefinition]] = (
            defaultdict(list)
        )
        for py_file in FlextInfraUtilitiesCodegenConstantDetection.iter_py_files(
            root_path, exclude_packages or frozenset()
        ):
            proj = FlextInfraUtilitiesCodegenConstantDetection.infer_project(
                py_file, root_path
            )
            defs = FlextInfraUtilitiesCodegenConstantDetection.extract_constant_definitions(
                py_file,
                proj,
            )
            if defs:
                all_defs[proj].extend(defs)
        return dict(all_defs)

    # ── Usages ───────────────────────────────────────────────────────

    @staticmethod
    def scan_constant_usages(
        py_file: Path,
        *,
        collect_all_refs: bool = False,
    ) -> tuple[
        Sequence[t.Infra.StrIntPair],
        Sequence[t.Infra.StrIntPair],
        Sequence[t.Infra.StrIntPair],
    ]:
        """Scan one file → ``(direct_refs, alias_refs, all_refs)``."""
        source = FlextInfraUtilitiesCodegenConstantDetection.read_source_safe(py_file)
        if source is None:
            return ([], [], [])
        direct, alias = FlextInfraUtilitiesCodegenConstantDetection.scan_patterns(
            source,
            [c.Infra.Detection.DIRECT_USAGE_RE, c.Infra.Detection.ALIAS_USAGE_RE],
        )
        all_refs = [*direct, *alias] if collect_all_refs else []
        return (direct, alias, all_refs)

    @staticmethod
    def scan_all_constant_usages(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[t.Infra.StrIntPair]]:
        """Scan all constant usages across workspace."""
        usage_map: defaultdict[str, MutableSequence[t.Infra.StrIntPair]] = defaultdict(
            list
        )
        for py_file in FlextInfraUtilitiesCodegenConstantDetection.iter_py_files(
            root_path, exclude_packages or frozenset()
        ):
            _, _, all_refs = (
                FlextInfraUtilitiesCodegenConstantDetection.scan_constant_usages(
                    py_file,
                    collect_all_refs=True,
                )
            )
            for name, line_num in all_refs:
                usage_map[name].append((str(py_file), line_num))
        return dict(usage_map)

    @staticmethod
    def detect_unused_constants(
        definitions: Sequence[m.Infra.ConstantDefinition],
        all_used_names: t.Infra.StrSet,
    ) -> Sequence[m.Infra.UnusedConstant]:
        return [
            m.Infra.UnusedConstant(
                name=d.name,
                file_path=d.file_path,
                class_path=d.class_path,
                project=d.project,
                line=d.line,
            )
            for d in definitions
            if d.name not in all_used_names
            and not re.match(r"Flext\w*Constants\.", d.value_repr)
        ]

    @staticmethod
    def resolve_parent_package(pkg_dir: Path) -> str:
        return FlextInfraUtilitiesDiscovery.resolve_parent_constants(
            pkg_dir,
            return_module=True,
        )


# =====================================================================
# Analysis — census, deduplication, MRO attribute extraction
# =====================================================================


class FlextInfraUtilitiesCodegenConstantAnalysis:
    """Census, deduplication, and MRO attribute analysis for constants."""

    @staticmethod
    def extract_class_attributes_with_mro(
        class_path: str,
    ) -> Mapping[str, m.Infra.ConstantDefinition]:
        """Extract class attributes following MRO chain via importlib."""
        if "." not in class_path:
            return {}
        module_path, class_name = class_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)
        except (ImportError, ModuleNotFoundError):
            return {}
        cls_obj = getattr(module, class_name, None)
        if cls_obj is None or not isinstance(cls_obj, type):
            return {}

        attrs: MutableMapping[str, m.Infra.ConstantDefinition] = {}
        for (
            attr_name,
            attr_value,
            klass_qualname,
            klass_module,
        ) in FlextInfraUtilitiesCodegenConstantDetection.walk_mro_attrs(cls_obj):
            annotations = getattr(
                next(
                    (k for k in cls_obj.__mro__ if attr_name in dict(vars(k))),
                    cls_obj,
                ),
                "__annotations__",
                {},
            )
            attrs[attr_name] = m.Infra.ConstantDefinition(
                name=attr_name,
                value_repr=repr(attr_value)[:200],
                type_annotation=str(annotations.get(attr_name, "")),
                file_path=f"{klass_module}.{klass_qualname}",
                class_path=klass_qualname,
                project=(klass_module or module_path).split(".")[0].replace("_", "-"),
                line=1,
            )
        return attrs

    @staticmethod
    def scan_class_attribute_usages(
        root_path: Path,
        class_name: str,
        exclude_patterns: frozenset[str] = c.Infra.DEFAULT_EXCLUDE,
        max_files: int = 5000,
    ) -> tuple[t.Infra.StrSet, Mapping[str, Sequence[t.Infra.StrIntPair]]]:
        """Scan for usages of class attributes across Python files."""
        used_attrs: t.Infra.StrSet = set()
        usage_map: defaultdict[str, MutableSequence[t.Infra.StrIntPair]] = defaultdict(
            list
        )
        prefix = class_name.replace("Constants", "").removeprefix("Flext")
        direct_pat = re.compile(rf"\b{re.escape(class_name)}\.([A-Za-z_]\w*)")
        alias_pat = re.compile(
            rf"\bc\.{re.escape(prefix)}\.([A-Za-z_]\w*)"
            if prefix
            else r"\bc\.([A-Za-z_]\w*)",
        )
        for py_file in FlextInfraUtilitiesCodegenConstantDetection.iter_py_files(
            root_path, exclude_patterns, max_files=max_files
        ):
            source = FlextInfraUtilitiesCodegenConstantDetection.read_source_safe(
                py_file
            )
            if source is None:
                continue
            direct, alias = FlextInfraUtilitiesCodegenConstantDetection.scan_patterns(
                source, [direct_pat, alias_pat]
            )
            for refs in (direct, alias):
                for attr_name, line_num in refs:
                    used_attrs.add(attr_name)
                    usage_map[attr_name].append((str(py_file), line_num))
        return used_attrs, dict(usage_map)

    @staticmethod
    def analyze_class_object_census(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str] = c.Infra.DEFAULT_EXCLUDE,
        max_files: int = 5000,
    ) -> Mapping[
        str,
        int
        | Mapping[str, int | t.IntMapping]
        | Mapping[str, t.IntMapping]
        | Mapping[str, Sequence[t.Infra.StrIntPair]],
    ]:
        """Comprehensive census of all objects in a class."""
        cls = FlextInfraUtilitiesCodegenConstantAnalysis
        attrs = cls.extract_class_attributes_with_mro(class_path)
        if not attrs:
            return {}
        simple_name = class_path.rsplit(".", 1)[-1]
        used_attrs, usage_map = cls.scan_class_attribute_usages(
            root_path,
            simple_name,
            exclude_patterns,
            max_files,
        )

        by_type: MutableMapping[str, t.MutableIntMapping] = {}
        for attr_name, attr_def in attrs.items():
            tp = attr_def.type_annotation
            if tp not in by_type:
                by_type[tp] = {"total": 0, "used": 0, "unused": 0}
            by_type[tp]["total"] += 1
            by_type[tp]["used" if attr_name in used_attrs else "unused"] += 1

        return {
            "total_objects": len(attrs),
            "total_used": len(used_attrs),
            "total_unused": len(attrs) - len(used_attrs),
            "by_type": by_type,
            "usage_map": usage_map,
        }

    @staticmethod
    def propose_deduplication_fixes(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str] = c.Infra.DEFAULT_EXCLUDE,
        max_files: int = 2000,
    ) -> r[Sequence[m.Infra.DeduplicationFixProposal]]:
        """Propose fixes to deduplicate constant values across a class."""
        cls = FlextInfraUtilitiesCodegenConstantAnalysis
        attrs = cls.extract_class_attributes_with_mro(class_path)
        if not attrs:
            return r[Sequence[m.Infra.DeduplicationFixProposal]].ok(())
        simple_name = class_path.rsplit(".", 1)[-1]
        _, usage_map = cls.scan_class_attribute_usages(
            root_path,
            simple_name,
            exclude_patterns,
            max_files,
        )

        by_value: defaultdict[str, list[m.Infra.DeduplicationCandidate]] = defaultdict(
            list
        )
        for name, defn in attrs.items():
            by_value[defn.value_repr[:100]].append(
                m.Infra.DeduplicationCandidate(
                    name=name,
                    type_annotation=defn.type_annotation,
                    usages=len(usage_map.get(name, [])),
                )
            )

        fixes: MutableSequence[m.Infra.DeduplicationFixProposal] = []
        for value, candidates in by_value.items():
            if len(candidates) <= 1:
                continue
            canonical = max(candidates, key=operator.attrgetter("usages"))
            duplicates = tuple(
                candidate
                for candidate in candidates
                if candidate.name != canonical.name
            )
            fixes.append(
                m.Infra.DeduplicationFixProposal(
                    value_repr=value,
                    canonical=canonical,
                    duplicates=duplicates,
                    total_occurrences=len(candidates),
                )
            )
        ordered = tuple(
            sorted(fixes, key=operator.methodcaller("impact_score"), reverse=True)
        )
        return r[Sequence[m.Infra.DeduplicationFixProposal]].ok(ordered)

    @staticmethod
    def apply_deduplication_fix(
        fix_proposal: m.Infra.DeduplicationFixProposal,
        root_path: Path,
        class_path: str,
        *,
        dry_run: bool = True,
    ) -> r[m.Infra.DeduplicationApplyResult]:
        """Apply a single deduplication fix using rope."""
        if "." not in class_path:
            return r[m.Infra.DeduplicationApplyResult].fail("Invalid class path")

        module_name = class_path.rsplit(".", 1)[0]
        rope_project = FlextInfraUtilitiesRope.init_rope_project(root_path)
        resource = FlextInfraUtilitiesRope.get_file_resource(
            rope_project, module_name
        ) or FlextInfraUtilitiesRope.get_file_resource(
            rope_project,
            f"{module_name}.constants",
        )
        if not resource:
            return r[m.Infra.DeduplicationApplyResult].fail(
                f"No resource for {module_name}"
            )

        files_modified = 0
        replaced_names: MutableSequence[str] = []
        replacements: MutableSequence[m.Infra.DeduplicationReplacement] = []

        for duplicate in fix_proposal.duplicates:
            dup_name = duplicate.name
            offset = FlextInfraUtilitiesRope.find_definition_offset(
                rope_project,
                resource,
                dup_name,
            )
            if offset is None:
                continue
            replaced_names.append(dup_name)
            changed = FlextInfraUtilitiesRope.rename_symbol_workspace(
                rope_project,
                resource,
                offset,
                fix_proposal.canonical.name,
                apply=not dry_run,
            )
            files_modified += len(changed)
            replacements.extend(
                m.Infra.DeduplicationReplacement(
                    file_path=changed_file,
                    line=0,
                    old_name=dup_name,
                )
                for changed_file in changed
            )

        return r[m.Infra.DeduplicationApplyResult].ok(
            m.Infra.DeduplicationApplyResult(
                canonical_name=fix_proposal.canonical.name,
                replaced_names=tuple(replaced_names),
                replacements=tuple(replacements),
                files_modified=files_modified,
                dry_run=dry_run,
            )
        )

    @staticmethod
    def deduplicate_constants(
        options: m.Infra.DeduplicationRunOptions | None = None,
        *,
        class_path: str = "",
        root_path: Path | None = None,
        dry_run: bool = True,
        max_files: int = 2000,
        exclude_patterns: frozenset[str] | None = None,
    ) -> r[m.Infra.DeduplicationRunReport]:
        """Run typed constant deduplication end-to-end with validated options."""
        resolved_patterns: frozenset[str] = exclude_patterns or frozenset()
        payload: Mapping[str, t.ValueOrModel] = {
            "class_path": class_path,
            "root_path": root_path,
            "dry_run": dry_run,
            "max_files": max_files,
            "exclude_patterns": tuple(resolved_patterns),
        }
        return u.resolve_options(
            options,
            payload,
            m.Infra.DeduplicationRunOptions,
        ).flat_map(FlextInfraUtilitiesCodegenConstantAnalysis._run_deduplication)

    @staticmethod
    def _run_deduplication(
        options: m.Infra.DeduplicationRunOptions,
    ) -> r[m.Infra.DeduplicationRunReport]:
        effective_excludes = options.exclude_patterns or c.Infra.DEFAULT_EXCLUDE
        return FlextInfraUtilitiesCodegenConstantAnalysis.propose_deduplication_fixes(
            options.class_path,
            options.root_path,
            effective_excludes,
            options.max_files,
        ).flat_map(
            lambda proposals: (
                FlextInfraUtilitiesCodegenConstantAnalysis._build_deduplication_report(
                    options,
                    proposals,
                )
            )
        )

    @staticmethod
    def _build_deduplication_report(
        options: m.Infra.DeduplicationRunOptions,
        proposals: Sequence[m.Infra.DeduplicationFixProposal],
    ) -> r[m.Infra.DeduplicationRunReport]:
        if not proposals:
            return r[m.Infra.DeduplicationRunReport].ok(
                m.Infra.DeduplicationRunReport(
                    class_path=options.class_path,
                    dry_run=options.dry_run,
                    proposals=(),
                    applied=(),
                    total_files_modified=0,
                )
            )
        return (
            r[m.Infra.DeduplicationApplyResult]
            .traverse(
                proposals,
                lambda proposal: (
                    FlextInfraUtilitiesCodegenConstantAnalysis.apply_deduplication_fix(
                        proposal,
                        options.root_path,
                        options.class_path,
                        dry_run=options.dry_run,
                    )
                ),
                fail_fast=False,
            )
            .map(
                lambda applied: m.Infra.DeduplicationRunReport(
                    class_path=options.class_path,
                    dry_run=options.dry_run,
                    proposals=tuple(proposals),
                    applied=tuple(applied),
                    total_files_modified=sum(
                        result.files_modified for result in applied
                    ),
                )
            )
        )

    @staticmethod
    def detect_duplicate_constants(
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        """Detect duplicate constants by name and value across projects."""
        by_name: defaultdict[str, list[m.Infra.ConstantDefinition]] = defaultdict(list)
        by_value: defaultdict[str, list[m.Infra.ConstantDefinition]] = defaultdict(list)
        for defn in definitions:
            by_name[defn.name].append(defn)
            by_value[defn.value_repr].append(defn)

        duplicates: MutableSequence[m.Infra.DuplicateConstantGroup] = []
        for name, defs in by_name.items():
            if len(defs) > 1:
                duplicates.append(
                    m.Infra.DuplicateConstantGroup(
                        constant_name=name,
                        definitions=defs,
                        is_value_identical=len({d.value_repr for d in defs}) == 1,
                        canonical_ref="",
                    )
                )
        for value_key, defs in by_value.items():
            if len(defs) > 1 and len({d.name for d in defs}) > 1:
                duplicates.append(
                    m.Infra.DuplicateConstantGroup(
                        constant_name=f"[value: {value_key}]",
                        definitions=defs,
                        is_value_identical=True,
                        canonical_ref="",
                    )
                )
        return duplicates


# =====================================================================
# Transformation — inline values → c.* references
# =====================================================================


class FlextInfraUtilitiesCodegenConstantTransformation:
    """Consolidation: inline values → ``c.*`` references with rollback."""

    @staticmethod
    def resolve_constants_facade(pkg_name: str) -> type | None:
        """Import ``{pkg_name}.constants`` and return the facade class."""
        module_name = f"{pkg_name}.constants"
        try:
            mod = importlib.import_module(module_name)
        except (ImportError, ModuleNotFoundError):
            return None
        return next(
            (
                attr
                for attr in vars(mod).values()
                if isinstance(attr, type)
                and getattr(attr, "__module__", "") == module_name
                and "Constants" in attr.__name__
                and len(attr.__name__) > 1
            ),
            None,
        )

    @staticmethod
    def build_value_map(facade_cls: type) -> Mapping[str, str]:
        """Walk facade + inner classes via MRO → ``{repr: "Prefix.ATTR"}``."""
        vmap: MutableMapping[str, str] = {}
        targets: MutableSequence[tuple[type, str]] = [(facade_cls, "")]
        targets.extend(
            (a, a.__name__)
            for a in dict(vars(facade_cls)).values()
            if isinstance(a, type) and a is not type
        )
        for cls, prefix in targets:
            for (
                name,
                value,
                _,
                _,
            ) in FlextInfraUtilitiesCodegenConstantDetection.walk_mro_attrs(
                cls, skip_types=True
            ):
                raw = repr(value)[:200]
                if not raw:
                    continue
                canon = f"{prefix}.{name}" if prefix else name
                vmap[raw] = canon
                if FlextInfraUtilitiesCodegenConstantDetection.is_quoted(raw):
                    inner = FlextInfraUtilitiesCodegenConstantDetection.unquote(raw)
                    vmap[f"'{inner}'"] = vmap[f'"{inner}"'] = canon
        return vmap

    @staticmethod
    def match_assignments(
        symbols: Sequence[m.Infra.SymbolInfo],
        source_lines: Sequence[str],
        value_to_ref: Mapping[str, str],
    ) -> Sequence[tuple[m.Infra.SymbolInfo, str, str]]:
        """Match rope-detected assignments against canonical value map."""
        matches: MutableSequence[tuple[m.Infra.SymbolInfo, str, str]] = []
        for sym in symbols:
            if sym.line < 1 or sym.line > len(source_lines):
                continue
            eq = source_lines[sym.line - 1].find("=")
            if eq < 0:
                continue
            raw = source_lines[sym.line - 1][eq + 1 :].strip()
            if raw in c.Infra.Detection.TRIVIAL_VALUES:
                continue
            canon = value_to_ref.get(raw)
            if canon is None or canon == sym.name:
                continue
            if FlextInfraUtilitiesCodegenConstantDetection.semantic_name_matches(
                sym.name,
                canon,
            ):
                matches.append((sym, f"c.{canon}", raw))
        return matches

    # ── Validated editing (reusable) ─────────────────────────────────

    @staticmethod
    def lint_snapshot(py_file: Path, workspace: Path) -> t.Infra.LintSnapshot:
        """Run all lint tools on *py_file* → ``{tool: [error_lines]}``."""
        errors: MutableMapping[str, Sequence[str]] = {}
        for tool, tmpl in c.Infra.LINT_TOOLS:
            cmd = [a.replace("{file}", str(py_file)) for a in tmpl]
            res = FlextInfraUtilitiesSubprocess.run_raw(
                cmd,
                cwd=workspace,
                timeout=c.Infra.Timeouts.SHORT,
            )
            if res.is_success and res.value.exit_code != 0:
                out = (res.value.stdout + res.value.stderr).strip()
                errors[tool] = [ln for ln in out.splitlines() if ln.strip()]
        return errors

    @staticmethod
    def lint_new_errors(
        before: t.Infra.LintSnapshot,
        after: t.Infra.LintSnapshot,
    ) -> t.Infra.LintSnapshot:
        """Return only errors in *after* not present in *before*."""
        return {
            tool: added
            for tool, lines in after.items()
            if (
                added := [
                    ln for ln in lines if ln not in frozenset(before.get(tool, []))
                ]
            )
        }

    @staticmethod
    def validated_rope_edit(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        py_file: Path,
        workspace: Path,
        backup: str,
        edit_fn: Callable[[], None],
    ) -> t.Infra.EditResult:
        """Snapshot lint → call *edit_fn* → diff lint → rollback if new errors.

        *edit_fn* is a zero-arg closure that performs the rope operations.
        Returns ``(success, report_lines)``.
        """
        cls = FlextInfraUtilitiesCodegenConstantTransformation
        rel = py_file.relative_to(workspace)
        before = cls.lint_snapshot(py_file, workspace)

        edit_fn()

        # Check for new lint errors
        new_errors = cls.lint_new_errors(before, cls.lint_snapshot(py_file, workspace))

        # Pytest for test files
        test_fail: str | None = None
        if not new_errors and (
            "tests" in py_file.parts or py_file.name.startswith("test_")
        ):
            tr = FlextInfraUtilitiesSubprocess.run_raw(
                ["pytest", str(py_file), "-x", "--tb=short", "-q"],
                cwd=workspace,
                timeout=c.Infra.Timeouts.MEDIUM,
            )
            if tr.is_success and tr.value.exit_code != 0:
                test_fail = (tr.value.stdout + tr.value.stderr)[:300]

        if not new_errors and not test_fail:
            return (True, [])

        # Rollback + diff report
        modified = FlextInfraUtilitiesRope.read_source(resource)
        diff = list(
            difflib.unified_diff(
                backup.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
                n=3,
            )
        )
        FlextInfraUtilitiesRope.write_source(rope_project, resource, backup)
        report: MutableSequence[str] = [f"  REVERTED {rel}:"]
        report.extend(f"    {dl.rstrip()}" for dl in diff[:30])
        for tool, msgs in new_errors.items():
            report.extend((
                f"    NEW {tool} errors:",
                *(f"      {m}" for m in msgs[:5]),
            ))
        if test_fail:
            report.append(f"    pytest failure: {test_fail}")
        return (False, report)

    @staticmethod
    def apply_and_validate(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        py_file: Path,
        workspace: Path,
        pkg_name: str,
        backup: str,
        matches: Sequence[tuple[m.Infra.SymbolInfo, str, str]],
    ) -> t.Infra.EditResultWithDescs:
        """Build offset edits from *matches*, apply, validate, rollback on failure."""
        cls = FlextInfraUtilitiesCodegenConstantTransformation
        src_lines = backup.splitlines(keepends=True)
        rel = py_file.relative_to(workspace)

        edits: MutableSequence[tuple[int, int, str]] = []
        descs: MutableSequence[str] = []
        for sym, ref, val in matches:
            if sym.line < 1 or sym.line > len(src_lines):
                continue
            line = src_lines[sym.line - 1]
            eq = line.find("=")
            if eq < 0:
                continue
            off = sum(len(src_lines[i]) for i in range(sym.line - 1))
            edits.append((
                off + eq + 1,
                off + eq + 1 + len(line[eq + 1 :].rstrip()),
                f" {ref}",
            ))
            descs.append(f"{sym.name} = {val} -> {ref}")

        if not edits:
            return (True, [], [])

        def _do_edit() -> None:
            FlextInfraUtilitiesRope.rewrite_source_at_offsets(
                rope_project,
                resource,
                edits,
                apply=True,
            )
            FlextInfraUtilitiesRope.add_import(
                rope_project,
                resource,
                pkg_name,
                ["c"],
                apply=True,
            )

        ok, report = cls.validated_rope_edit(
            rope_project,
            resource,
            py_file,
            workspace,
            backup,
            _do_edit,
        )
        if ok:
            return (True, list(descs), [f"  APPLIED {rel}: {d}" for d in descs])
        return (False, list(descs), report)


__all__ = [
    "FlextInfraUtilitiesCodegenConstantAnalysis",
    "FlextInfraUtilitiesCodegenConstantDetection",
    "FlextInfraUtilitiesCodegenConstantTransformation",
    "FlextInfraUtilitiesCodegenGovernance",
]
