from __future__ import annotations

from pathlib import Path

import pytest

try:
    from flext_infra import FlextInfraNamespaceSourceDetector, t, u
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
) -> tuple[Path, Path, str, str, t.Infra.RopeProject]:
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
    rope_project = u.Infra.init_rope_project(tmp_path)
    return project_root, package_dir, package_name, "flext-xyz", rope_project


def test_detects_wrong_source_m_import(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import m\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_detects_wrong_source_u_import(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("u",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import u\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_r_alias_universal_exception(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import r\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_facade_declaration_files(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "models.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        "from flext_core import m\n"
        "class FlextXyzModels:\n"
        "    pass\n\n"
        "m = FlextXyzModels\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_init_file(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "__init__.py"
    target.write_text("from flext_core import m\n")

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_import_as_rename(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import m as mm\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_non_alias_symbols(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import FlextLogger\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_detects_only_wrong_alias_in_mixed_import(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import m, r\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_project_without_alias_facade_has_no_violation(tmp_path: Path) -> None:
    project_root, package_dir, _package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("u",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom flext_core import m\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_rewriter_splits_mixed_imports_correctly(tmp_path: Path) -> None:
    _project_root, package_dir, package_name, _project_name, _rope = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m", "u"),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        "from flext_core import m, r\n"
        f"from {package_name} import u\n"
        "_ = (m, r, u)\n",
    )

    u.Infra.rewrite_import_violations(
        py_files=[target],
        project_package=package_name,
    )

    rewritten = target.read_text(encoding="utf-8")
    assert "from flext_core import m, r" in rewritten
    assert f"from {package_name} import u" in rewritten


def test_rewriter_preserves_non_alias_symbols(tmp_path: Path) -> None:
    _project_root, package_dir, package_name, _project_name, _rope = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("u",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        "from flext_core import FlextLogger, u\n"
        "_ = (FlextLogger, u)\n",
    )

    u.Infra.rewrite_import_violations(
        py_files=[target],
        project_package=package_name,
    )

    rewritten = target.read_text(encoding="utf-8")
    assert "from flext_core import FlextLogger, u" in rewritten
    assert f"from {package_name} import u" not in rewritten


def test_rewriter_namespace_source_is_idempotent_with_ruff(tmp_path: Path) -> None:
    _project_root, package_dir, package_name, _project_name, _rope = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("m", "u"),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        "from flext_core import FlextLogger, m, r\n"
        f"from {package_name}.utilities import u\n"
        "_ = (FlextLogger, m, r, u)\n",
    )

    u.Infra.rewrite_import_violations(
        py_files=[target],
        project_package=package_name,
    )
    first_result = target.read_text(encoding="utf-8")

    u.Infra.rewrite_import_violations(
        py_files=[target],
        project_package=package_name,
    )
    second_result = target.read_text(encoding="utf-8")

    assert first_result == second_result


def test_detects_same_project_submodule_alias_import(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("c",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        f"from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom {package_name}.constants import c\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_same_project_submodule_class_import(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("c",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        f"from {package_name}.constants import FlextXyzConstants\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_same_project_private_submodule(tmp_path: Path) -> None:
    project_root, package_dir, package_name, project_name, rope_project = (
        _create_project_with_facades(
            tmp_path=tmp_path,
            families=("c",),
        )
    )
    target = package_dir / "consumer.py"
    target.write_text(
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        f"from {package_name}._constants import c\n",
    )

    violations = FlextInfraNamespaceSourceDetector.detect_file(
        file_path=target,
        project_name=project_name,
        project_root=project_root,
        rope_project=rope_project,
    )

    assert violations == []
