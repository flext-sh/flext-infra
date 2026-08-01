"""Tool-once contracts for generation and protected source edits."""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, config, m
from flext_tests import tm


class TestsCodegenToolOnce:
    """Keep generic quality tools under their canonical Make owners."""

    @staticmethod
    def _source_owners() -> tuple[Path, ...]:
        """Return source owners that execute generation and protected edits."""
        root = Path(__file__).resolve().parents[3]
        codegen = root / "src" / "flext_infra" / "codegen"
        utilities = root / "src" / "flext_infra" / "_utilities"
        refactor = root / "src" / "flext_infra" / "refactor"
        return (
            *sorted(codegen.glob("*.py")),
            utilities / "namespace_analysis.py",
            utilities / "namespace_moves.py",
            utilities / "protected_edit_apply.py",
            utilities / "protected_edit_linting.py",
            utilities / "protected_edit_preview.py",
            utilities / "rope_imports.py",
            refactor / "_census_apply_formatting.py",
        )

    def test_process_calls_exclude_configured_quality_tools(self) -> None:
        """No generation-owned process call names a configured quality tool."""
        configured_tools = frozenset(
            config.Infra.tooling.tools.__class__.model_fields
        ) | frozenset({c.Infra.UV})
        process_calls = frozenset({"run_raw", "run_checked", "Popen"})
        violations: list[str] = []
        for path in self._source_owners():
            tree = ast.parse(path.read_text(encoding=c.Cli.ENCODING_DEFAULT))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                call_name = (
                    node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else node.func.id
                    if isinstance(node.func, ast.Name)
                    else ""
                )
                if call_name not in process_calls:
                    continue
                referenced = {
                    child.value.lower()
                    for child in ast.walk(node)
                    if isinstance(child, ast.Constant) and isinstance(child.value, str)
                } | {
                    child.attr.lower()
                    for child in ast.walk(node)
                    if isinstance(child, ast.Attribute)
                }
                overlap = sorted(configured_tools.intersection(referenced))
                if overlap:
                    violations.append(f"{path.relative_to(path.parents[3])}: {overlap}")
        tm.that(violations, eq=[])

    def test_protected_edit_contract_has_no_quality_tool_flags(self) -> None:
        """Protected edits expose structural validation without bypass flags."""
        request_models = (
            m.Infra.ProtectedFileEditRequest,
            m.Infra.ProtectedSourceWriteRequest,
            m.Infra.ProtectedSourceWritesRequest,
            m.Infra.ApplyRenamesInput,
            m.Infra.RefactorMigrateMroInput,
            m.Infra.RefactorNamespaceEnforceInput,
            m.Infra.ModernizeInput,
            m.Infra.AccessorMigrationInput,
        )
        field_names = {name for model in request_models for name in model.model_fields}
        stale_flags = {
            name for name in field_names if name == "gates" or name.startswith("skip_")
        }
        tm.that(stale_flags, eq=set())
        tm.that(hasattr(c.Infra, "LINT_TOOLS"), eq=False)


__all__: list[str] = []
