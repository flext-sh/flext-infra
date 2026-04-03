from __future__ import annotations

import sys
from collections.abc import MutableSequence
from pathlib import Path

from flext_infra import c, m, t, u


class FlextInfraPostCheckGate:
    def validate(
        self,
        result: m.Infra.Result,
        expected: t.Infra.ContainerDict,
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        errors: MutableSequence[str] = []
        if not result.success:
            if result.error:
                return (False, [result.error])
            return (False, ["transform_failed"])
        if not result.modified:
            return (True, [])
        file_path = result.file_path
        post_checks = u.string_list(
            expected.get(c.Infra.ReportKeys.POST_CHECKS),
        )
        quality_gates = u.string_list(expected.get("quality_gates"))
        if self._check_enabled("imports_resolve", post_checks):
            errors.extend(self._validate_imports(file_path))
        source_symbol_raw = expected.get(c.Infra.ReportKeys.SOURCE_SYMBOL, "")
        source_symbol = source_symbol_raw if isinstance(source_symbol_raw, str) else ""
        expected_chain = u.string_list(expected.get("expected_base_chain"))
        if (
            source_symbol
            and expected_chain
            and self._check_enabled("mro_valid", post_checks)
        ):
            errors.extend(self._validate_mro(file_path, source_symbol, expected_chain))
        if self._check_enabled("lsp_diagnostics_clean", quality_gates):
            errors.extend(self._validate_types(file_path))
        return (not errors, errors)

    def _check_enabled(self, check_name: str, checks: t.StrSequence) -> bool:
        return check_name in checks

    def _validate_imports(self, file_path: Path) -> t.StrSequence:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return [f"parse_error:{file_path}:parse_failed"]
        unresolved: MutableSequence[str] = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            if c.Infra.SourceCode.BARE_IMPORT_FROM_RE.match(line):
                unresolved.append(f"line_{lineno}:invalid_import_from")
        return unresolved

    def _validate_mro(
        self,
        file_path: Path,
        class_name: str,
        expected_bases: t.StrSequence,
    ) -> t.StrSequence:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except (OSError, UnicodeDecodeError):
            return [f"mro_parse_error:{file_path}:parse_failed"]
        for match in c.Infra.SourceCode.CLASS_WITH_BASES_RE.finditer(source):
            if match.group(1) != class_name:
                continue
            bases_str = match.group(2)
            actual = [
                b.strip().split("[")[0].rsplit(".", maxsplit=1)[-1]
                for b in bases_str.split(",")
                if b.strip()
            ]
            actual_clean = [name for name in actual if name]
            expected_prefix = list(expected_bases)[: len(actual_clean)]
            if actual_clean != expected_prefix:
                return [
                    f"mro_mismatch:{class_name}:expected={expected_prefix}:actual={actual_clean}",
                ]
            return []
        return [f"class_not_found:{class_name}"]

    def _validate_types(self, file_path: Path) -> t.StrSequence:
        cmd = [sys.executable, "-m", "py_compile", str(file_path)]
        result = u.capture(cmd)
        return result.fold(
            on_failure=lambda e: [f"lsp_diagnostics_clean_failed:{e or ''}"],
            on_success=lambda _: [],
        )


__all__ = ["FlextInfraPostCheckGate"]
