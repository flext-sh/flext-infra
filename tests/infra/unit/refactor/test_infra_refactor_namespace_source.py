from __future__ import annotations

from pathlib import Path

import pytest

try:
    from flext_infra.refactor.dependency_analyzer import NamespaceSourceDetector
    from flext_infra.refactor.namespace_rewriter import NamespaceEnforcementRewriter
except ImportError as exc:
    pytest.skip(f"refactor package unavailable: {exc}", allow_module_level=True)


FAMILY_FILE_MAP = {
    "c": "constants.py",
    "t": "typings.py",
    "p": "protocols.py",
    "m": "models.py",
    "u": "utilities.py",
}

FAMILY_SUFFIX_MAP = {
    "c": "Constants",
    "t": "Types",
    "p": "Protocols",
    "m": "Models",
    "u": "Utilities",
}


def _create_project_with_facades(
    *,
    tmp_path: Path,
    families: tuple[str, ...],
) -> tuple[Path, Path, str, str]:
    project_root = tmp_path / "flext-xyz"
    package_name = "flext_xyz"
    package_dir = project_root / "src" / package_name
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    class_stem = "FlextXyz"
    for family in families:
        suffix = FAMILY_SUFFIX_MAP[family]
        class_name = f"{class_stem}{suffix}"
        facade_file = package_dir / FAMILY_FILE_MAP[family]
        facade_file.write_text(
            "from __future__ import annotations\n"
            f"class {class_name}:\n"
            "    pass\n\n"
            f"{family} = {class_name}\n",
            encoding="utf-8",
        )
    return project_root, package_dir, package_name, "flext-xyz"


def test_detects_wrong_source_m_import(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text("from __future__ import annotations\nfrom flext_core import m\n")

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert len(violations) == 1
    assert violations[0].alias == "m"
    assert violations[0].current_source == "flext_core"
    assert violations[0].correct_source == package_name


def test_detects_wrong_source_u_import(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("u",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text("from __future__ import annotations\nfrom flext_core import u\n")

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert len(violations) == 1
    assert violations[0].alias == "u"
    assert violations[0].correct_source == package_name


def test_skips_r_alias_universal_exception(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text("from __future__ import annotations\nfrom flext_core import r\n")

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert violations == []


def test_skips_facade_declaration_files(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "models.py"
    target.write_text(
        "from __future__ import annotations\n"
        "from flext_core import m\n"
        "class FlextXyzModels:\n"
        "    pass\n\n"
        "m = FlextXyzModels\n",
    )

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert violations == []


def test_skips_init_file(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "__init__.py"
    target.write_text("from flext_core import m\n")

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert violations == []


def test_skips_import_as_rename(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\nfrom flext_core import m as mm\n",
    )

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert violations == []


def test_skips_non_alias_symbols(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\nfrom flext_core import FlextLogger\n",
    )

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert violations == []


def test_detects_only_wrong_alias_in_mixed_import(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\nfrom flext_core import m, r\n",
    )

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert len(violations) == 1
    assert violations[0].alias == "m"
    assert violations[0].correct_source == package_name


def test_project_without_alias_facade_has_no_violation(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("u",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text("from __future__ import annotations\nfrom flext_core import m\n")

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )

    assert violations == []


def test_rewriter_splits_mixed_imports_correctly(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m", "u"),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n"
        "from flext_core import m, r\n"
        f"from {package_name} import u\n",
    )

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )
    NamespaceEnforcementRewriter.rewrite_namespace_source_violations(
        violations=violations,
        parse_failures=[],
    )

    rewritten = target.read_text(encoding="utf-8")
    assert "from flext_core import r" in rewritten
    assert f"from {package_name} import u, m" in rewritten


def test_rewriter_preserves_non_alias_symbols(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("u",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\nfrom flext_core import FlextLogger, u\n",
    )

    violations = NamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
    )
    NamespaceEnforcementRewriter.rewrite_namespace_source_violations(
        violations=violations,
        parse_failures=[],
    )

    rewritten = target.read_text(encoding="utf-8")
    assert "from flext_core import FlextLogger" in rewritten
    assert f"from {package_name} import u" in rewritten
