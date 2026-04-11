"""Constant detection, analysis, and transformation for codegen.

SSOT module for constant census, deduplication, MRO attribute analysis,
inline value detection, and consolidation with lint-validated rollback.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
from collections import defaultdict
from collections.abc import (
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path
from typing import ClassVar, Final

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)

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
        raw = u.Cli.yaml_load_mapping(
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


# =====================================================================
# Analysis — census, deduplication, MRO attribute extraction
# =====================================================================


class FlextInfraUtilitiesCodegenConstantAnalysis:
    """Census, deduplication, and MRO attribute analysis for constants."""

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

    _ALL_LINT_GATES: ClassVar[t.StrSequence] = tuple(
        tool for tool, _ in c.Infra.LINT_TOOLS
    )

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
                    inner = raw[1:-1]
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
            canon_key = canon.lower().replace("_", "")
            symbol_key = sym.name.lower().replace("_", "")
            if canon_key == symbol_key or symbol_key in canon_key:
                matches.append((sym, f"c.{canon}", raw))
        return matches

    # ── Validated editing (reusable) ─────────────────────────────────

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

        def _restore_edit() -> None:
            resource.write(backup)

        ok, report = FlextInfraUtilitiesProtectedEdit.protected_file_edit(
            py_file,
            workspace=workspace,
            before_source=backup,
            edit_fn=_do_edit,
            restore_fn=_restore_edit,
            keep_backup=True,
            gates=cls._ALL_LINT_GATES,
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
