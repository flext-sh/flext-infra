from __future__ import annotations

from pathlib import Path

import pytest

try:
    from flext_infra import FlextInfraMROCompletenessDetector, t, u
except ImportError as exc:
    pytest.skip(f"refactor package unavailable: {exc}", allow_module_level=True)


def _make_rope(workspace: Path) -> t.Infra.RopeProject:
    """Create a rope project rooted at *workspace*."""
    return u.Infra.init_rope_project(workspace)


def _write_models_project(
    *,
    tmp_path: Path,
    facade_bases: str,
    candidate_class: str,
) -> tuple[Path, t.Infra.RopeProject]:
    project_root = tmp_path / "flext-example"
    package_dir = project_root / "src" / "flext_example"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    # Build import lines for any bases defined in _models/ so rope can resolve them.
    imports = "".join(
        f"from flext_example._models.domain import {base}\n"
        for base in facade_bases.replace(" ", "").split(",")
        if base.startswith("FlextExample") and base != "FlextExampleModelsBase"
    )
    (package_dir / "models.py").write_text(
        "from __future__ import annotations\n"
        f"{imports}"
        "class FlextExampleModelsBase:\n"
        "    pass\n\n"
        f"class FlextExampleModels({facade_bases}):\n"
        "    pass\n\n"
        "m = FlextExampleModels\n",
        encoding="utf-8",
    )
    models_dir = package_dir / "_models"
    models_dir.mkdir(parents=True)
    (models_dir / "__init__.py").write_text("", encoding="utf-8")
    (models_dir / "domain.py").write_text(
        f"from __future__ import annotations\nclass {candidate_class}:\n    pass\n",
        encoding="utf-8",
    )
    rope_project = _make_rope(tmp_path)
    return package_dir / "models.py", rope_project


def test_detects_missing_local_composition_base(tmp_path: Path) -> None:
    facade_file, rope_project = _write_models_project(
        tmp_path=tmp_path,
        facade_bases="FlextExampleModelsBase",
        candidate_class="FlextExampleModelsDomain",
    )

    violations = FlextInfraMROCompletenessDetector.detect_file(
        file_path=facade_file,
        rope_project=rope_project,
    )

    assert len(violations) == 1
    assert violations[0].facade_class == "FlextExampleModels"
    assert violations[0].missing_base == "FlextExampleModelsDomain"
    assert violations[0].family == "m"


def test_skips_when_candidate_is_already_in_facade_bases(tmp_path: Path) -> None:
    facade_file, rope_project = _write_models_project(
        tmp_path=tmp_path,
        facade_bases="FlextExampleModelsBase, FlextExampleModelsDomain",
        candidate_class="FlextExampleModelsDomain",
    )

    violations = FlextInfraMROCompletenessDetector.detect_file(
        file_path=facade_file,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_non_facade_files(tmp_path: Path) -> None:
    target = tmp_path / "consumer.py"
    target.write_text("from __future__ import annotations\n", encoding="utf-8")

    # Rope project not needed — detector exits early for non-facade filenames.
    # Provide a minimal one anyway to satisfy the signature.
    rope_project = _make_rope(tmp_path)
    violations = FlextInfraMROCompletenessDetector.detect_file(
        file_path=target,
        rope_project=rope_project,
    )

    assert violations == []


def test_skips_private_candidate_classes(tmp_path: Path) -> None:
    facade_file, rope_project = _write_models_project(
        tmp_path=tmp_path,
        facade_bases="FlextExampleModelsBase",
        candidate_class="_FlextExampleModelsDomain",
    )

    violations = FlextInfraMROCompletenessDetector.detect_file(
        file_path=facade_file,
        rope_project=rope_project,
    )

    assert violations == []


def test_rewriter_adds_missing_base_and_formats(tmp_path: Path) -> None:
    facade_file, rope_project = _write_models_project(
        tmp_path=tmp_path,
        facade_bases="FlextExampleModelsBase",
        candidate_class="FlextExampleModelsDomain",
    )

    violations = FlextInfraMROCompletenessDetector.detect_file(
        file_path=facade_file,
        rope_project=rope_project,
    )
    u.Infra.rewrite_mro_completeness_violations(
        violations=violations,
        parse_failures=[],
    )

    rewritten = facade_file.read_text(encoding="utf-8")
    assert "FlextExampleModelsDomain" in rewritten
    assert "class FlextExampleModels(" in rewritten
