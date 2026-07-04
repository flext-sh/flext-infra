"""Regression tests for stale-symbol docs auditing."""

from __future__ import annotations

from pathlib import Path

from flext_infra._utilities.docs_api import FlextInfraUtilitiesDocsApi
from tests.models import m
from tests.utilities import u


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _stale_symbol_scope(tmp_path: Path) -> m.Infra.DocScope:
    workspace = tmp_path / "workspace"
    project = workspace / "flext-demo"
    package_root = project / "src" / "flext_demo"
    _write(
        workspace / "docs" / "docs_config.json",
        (
            "{\n"
            '  "audit": {\n'
            '    "stale_symbols": ["LiveSymbol", "DeadSymbol"],\n'
            '    "stale_symbol_exempt_paths": []\n'
            "  }\n"
            "}\n"
        ),
    )
    _write(
        project / "pyproject.toml",
        (
            "[project]\n"
            'name = "flext-demo"\n'
            'version = "0.1.0"\n'
            'description = "Demo docs audit project"\n'
        ),
    )
    _write(
        package_root / "__init__.py",
        (
            '"""Demo package for stale-symbol docs tests."""\n\n'
            "class LiveSymbol:\n"
            '    """Exported live symbol."""\n\n'
            '__all__ = ["LiveSymbol"]\n'
        ),
    )
    return m.Infra.DocScope(
        name="flext-demo",
        path=project,
        report_dir=project / ".reports" / "docs",
        package_name="flext_demo",
    )


def test_generated_api_reference_accepts_live_public_symbol(
    tmp_path: Path,
) -> None:
    scope = _stale_symbol_scope(tmp_path)
    _write(
        scope.path / "docs" / "api-reference" / "generated" / "overview.md",
        "# API\n\nPublic symbol exports: `LiveSymbol`\n",
    )

    issues = u.Infra.docs_stale_symbol_issues(scope)

    assert issues == []


def test_generated_api_reference_reports_missing_public_symbol(
    tmp_path: Path,
) -> None:
    scope = _stale_symbol_scope(tmp_path)
    _write(
        scope.path / "docs" / "api-reference" / "generated" / "overview.md",
        "# API\n\nPublic symbol exports: `DeadSymbol`\n",
    )

    issues = u.Infra.docs_stale_symbol_issues(scope)

    assert len(issues) == 1
    assert issues[0].issue_type == "stale_symbol"
    assert issues[0].message == "contains `DeadSymbol`"


def test_manual_docs_report_live_symbol_mentions(
    tmp_path: Path,
) -> None:
    scope = _stale_symbol_scope(tmp_path)
    _write(
        scope.path / "docs" / "guides" / "manual.md",
        "# Manual\n\nDo not mention LiveSymbol in curated prose.\n",
    )

    issues = u.Infra.docs_stale_symbol_issues(scope)

    assert len(issues) == 1
    assert issues[0].file == "docs/guides/manual.md"
    assert issues[0].message == "contains `LiveSymbol`"


def test_public_contract_resolves_imported_lazy_public_exports(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "src" / "demo_pkg"
    _write(
        tmp_path / "pyproject.toml",
        (
            "[project]\n"
            'name = "demo-pkg"\n'
            'version = "0.1.0"\n'
            'description = "Demo public exports project"\n'
        ),
    )
    _write(
        package_root / "__init__.py",
        (
            '"""Demo package."""\n\n'
            "from typing import TYPE_CHECKING\n\n"
            "from demo_pkg._exports import DEMO_PUBLIC_EXPORTS\n"
            "from flext_core.lazy import install_lazy_exports\n\n"
            "if TYPE_CHECKING:\n"
            "    from demo_pkg.facade import LiveSymbol as LiveSymbol\n\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    {},\n"
            "    public_exports=DEMO_PUBLIC_EXPORTS,\n"
            ")\n"
        ),
    )
    _write(
        package_root / "facade.py",
        (
            '"""Demo public facade."""\n\n'
            "from demo_pkg._internal import LiveSymbol\n\n"
            '__all__: list[str] = ["LiveSymbol"]\n'
        ),
    )
    _write(
        package_root / "_internal.py",
        (
            '"""Demo internal implementation."""\n\n'
            "class LiveSymbol:\n"
            '    """Concrete public symbol docs."""\n'
        ),
    )
    _write(
        package_root / "_exports.py",
        (
            '"""Demo export registry."""\n\n'
            "from demo_pkg._exports_parts.all_names import DEMO_PUBLIC_EXPORTS\n"
        ),
    )
    _write(
        package_root / "_exports_parts" / "all_names.py",
        (
            '"""Demo public export names."""\n\n'
            'DEMO_PUBLIC_EXPORTS: tuple[str, ...] = ("LiveSymbol",)\n'
        ),
    )

    contract = FlextInfraUtilitiesDocsApi.public_contract(tmp_path, "demo_pkg")
    exports = contract["exports"]
    public_symbols = contract["public_symbols"]

    assert isinstance(exports, list)
    assert isinstance(public_symbols, list)
    assert "LiveSymbol" in exports
    assert "LiveSymbol" in public_symbols

    issues = FlextInfraUtilitiesDocsApi.docstring_issues(tmp_path, contract)

    assert issues == []


def test_public_contract_resolves_imported_lazy_import_map(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "src" / "demo_pkg"
    _write(
        tmp_path / "pyproject.toml",
        (
            "[project]\n"
            'name = "demo-pkg"\n'
            'version = "0.1.0"\n'
            'description = "Demo public exports project"\n'
        ),
    )
    _write(
        package_root / "__init__.py",
        (
            '"""Demo package."""\n\n'
            "from demo_pkg._exports import DEMO_LAZY_IMPORTS, DEMO_PUBLIC_EXPORTS\n"
            "from flext_core.lazy import install_lazy_exports\n\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    DEMO_LAZY_IMPORTS,\n"
            "    public_exports=DEMO_PUBLIC_EXPORTS,\n"
            ")\n"
        ),
    )
    _write(
        package_root / "_exports.py",
        (
            '"""Demo export registry."""\n\n'
            "from demo_pkg._exports_part import DEMO_LAZY_IMPORTS_PART\n\n"
            "DEMO_LAZY_IMPORTS = {**DEMO_LAZY_IMPORTS_PART}\n"
            'DEMO_PUBLIC_EXPORTS: tuple[str, ...] = ("LiveSymbol",)\n'
        ),
    )
    _write(
        package_root / "_exports_part.py",
        (
            '"""Demo export registry part."""\n\n'
            "from flext_core.lazy import build_lazy_import_map\n\n"
            "DEMO_LAZY_IMPORTS_PART = build_lazy_import_map(\n"
            "    {'.facade': ('LiveSymbol',)},\n"
            ")\n"
        ),
    )
    _write(
        package_root / "facade.py",
        (
            '"""Demo public facade."""\n\n'
            "from demo_pkg._internal import LiveSymbol\n\n"
            '__all__: list[str] = ["LiveSymbol"]\n'
        ),
    )
    _write(
        package_root / "_internal.py",
        (
            '"""Demo internal implementation."""\n\n'
            "class LiveSymbol:\n"
            '    """Concrete public symbol docs."""\n'
        ),
    )

    contract = FlextInfraUtilitiesDocsApi.public_contract(tmp_path, "demo_pkg")

    assert contract["target_map"] == {"LiveSymbol": "demo_pkg.facade"}
    assert FlextInfraUtilitiesDocsApi.docstring_issues(tmp_path, contract) == []


def test_docstring_issues_accepts_direct_part_mro_docstring(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "src" / "demo_pkg"
    _write(
        tmp_path / "pyproject.toml",
        (
            "[project]\n"
            'name = "demo-pkg"\n'
            'version = "0.1.0"\n'
            'description = "Demo public exports project"\n'
        ),
    )
    _write(
        package_root / "__init__.py",
        (
            '"""Demo package."""\n\n'
            "from demo_pkg.part_02 import LiveSymbol\n\n"
            '__all__ = ["LiveSymbol"]\n'
        ),
    )
    _write(
        package_root / "part_01.py",
        (
            '"""Demo base part."""\n\n'
            "class LiveSymbol:\n"
            '    """Canonical public symbol docs."""\n'
        ),
    )
    _write(
        package_root / "part_02.py",
        (
            '"""Demo final part."""\n\n'
            "from demo_pkg.part_01 import LiveSymbol as LiveSymbolPart01\n\n"
            "class LiveSymbol(LiveSymbolPart01):\n"
            "    pass\n"
        ),
    )

    contract = FlextInfraUtilitiesDocsApi.public_contract(tmp_path, "demo_pkg")
    issues = FlextInfraUtilitiesDocsApi.docstring_issues(tmp_path, contract)

    assert issues == []
