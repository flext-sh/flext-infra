from __future__ import annotations

from pathlib import Path

import pytest

try:
    from flext_infra.refactor.dependency_analyzer import ImportAliasDetector
    from flext_infra.refactor.namespace_rewriter import NamespaceEnforcementRewriter
except ImportError as exc:
    pytest.skip(f"refactor package unavailable: {exc}", allow_module_level=True)


def test_import_alias_detector_skips_private_and_class_imports(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core._models import FlextModelFoundation\n"
        "from flext_core.models import FlextModels\n"
        "from flext_core.models import m\n",
        encoding="utf-8",
    )

    violations = ImportAliasDetector.detect_file(file_path=sample_file)
    assert len(violations) == 1
    assert violations[0].current_import == "from flext_core.models import m"


def test_import_alias_detector_skips_nested_private_and_as_renames(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_infra.refactor._models_namespace_enforcer import FlextInfraNamespaceEnforcerModels\n"
        "from flext_core.models import m as mm\n",
        encoding="utf-8",
    )

    violations = ImportAliasDetector.detect_file(file_path=sample_file)
    assert violations == []


def test_namespace_rewriter_only_rewrites_runtime_alias_imports(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core._models import FlextModelFoundation\n"
        "from flext_core.models import FlextModels\n"
        "from flext_core.models import m\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    NamespaceEnforcementRewriter.rewrite_import_alias_violations(py_files=[sample_file])

    rewritten = sample_file.read_text(encoding="utf-8")
    assert "from flext_core._models import FlextModelFoundation" in rewritten
    assert "from flext_core.models import FlextModels" in rewritten
    assert "from flext_core import c, m, r, t, u, p" in rewritten


def test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core import c, m, r, t, u, p\n"
        "from flext_infra.refactor._models_namespace_enforcer import FlextInfraNamespaceEnforcerModels\n"
        "from flext_core.models import m as mm\n"
        "from flext_core.models import (m)\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    NamespaceEnforcementRewriter.rewrite_import_alias_violations(py_files=[sample_file])

    rewritten = sample_file.read_text(encoding="utf-8")
    assert rewritten.count("from flext_core import c, m, r, t, u, p") == 1
    assert (
        "from flext_infra.refactor._models_namespace_enforcer import FlextInfraNamespaceEnforcerModels"
        in rewritten
    )
    assert "from flext_core.models import m as mm" in rewritten
    assert "from flext_core.models import (m)" not in rewritten
