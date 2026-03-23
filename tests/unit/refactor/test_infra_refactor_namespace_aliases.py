from __future__ import annotations

from pathlib import Path

import pytest

try:
    from flext_infra import ImportAliasDetector, u
except ImportError as exc:
    pytest.skip(f"refactor package unavailable: {exc}", allow_module_level=True)


def test_import_alias_detector_skips_private_and_class_imports(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core import FlextModelFoundation\n"
        "from flext_core import FlextModels\n"
        "from flext_core import m\n",
        encoding="utf-8",
    )

    violations = ImportAliasDetector.detect_file(file_path=sample_file)
    assert violations == []


def test_import_alias_detector_skips_nested_private_and_as_renames(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_infra import FlextInfraNamespaceEnforcerModels\n"
        "from flext_core import m as mm\n",
        encoding="utf-8",
    )

    violations = ImportAliasDetector.detect_file(file_path=sample_file)
    assert violations == []


def test_import_alias_detector_skips_facade_and_subclass_files(tmp_path: Path) -> None:
    sample_file = tmp_path / "models.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core import u\n"
        "from flext_core import FlextModels\n\n"
        "class FlextFooModels(FlextModels):\n"
        "    pass\n",
        encoding="utf-8",
    )

    violations = ImportAliasDetector.detect_file(file_path=sample_file)
    assert violations == []


def test_namespace_rewriter_only_rewrites_runtime_alias_imports(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core import FlextModelFoundation\n"
        "from flext_core import FlextModels\n"
        "from flext_core import m\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.namespace_rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    assert rewritten == "from __future__ import annotations\n"


def test_namespace_rewriter_keeps_contextual_alias_subset(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    source = "from __future__ import annotations\nfrom flext_core.utilities import u\n"
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.namespace_rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    assert rewritten == "from __future__ import annotations\n"


def test_namespace_rewriter_skips_facade_and_subclass_files(tmp_path: Path) -> None:
    sample_file = tmp_path / "models.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core import u\n"
        "from flext_core import FlextModels\n\n"
        "class FlextFooModels(FlextModels):\n"
        "    pass\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.namespace_rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    assert "from flext_core import u" not in rewritten
    assert "from flext_core import u" not in rewritten
    assert "FlextModels" in rewritten


def test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core import c, m, r, t, u, p\n"
        "from flext_infra import FlextInfraNamespaceEnforcerModels\n"
        "from flext_core import m as mm\n"
        "from flext_core import (m)\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.namespace_rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    assert rewritten == "from __future__ import annotations\n"
