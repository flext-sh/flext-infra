"""Behavior tests for environment provenance of native declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from tests import c, m, t, tm, u


class TestsFlextInfraWorkspaceEnvironmentProvenanceDeclarations:
    """Prove declaration, alias and descriptor identity against physical sources."""

    @pytest.mark.parametrize(
        "layout", ["package", "namespace", "multiple", "hatch-sources"]
    )
    def test_editable_path_must_expose_declared_package_sources(
        self,
        installed_artifact_consumer: Path,
        layout: str,
    ) -> None:
        """Authenticate native backend paths and reject a case-local docs-only path."""
        root = installed_artifact_consumer
        if layout != "package":
            self._materialize_editable_layout(root, layout)
            ci = config.Infra.codegen.make.ci
            setup = tm.ok(
                u.Tests.run_isolated_make(
                    ["setup"],
                    cwd=root,
                    env={ci.variable: ci.local_value},
                )
            )
            tm.that(
                u.Cli.process_succeeded(setup.outcome),
                eq=True,
                msg=setup.stdout + setup.stderr,
            )
        locations = tm.ok(
            u.Cli.run_raw(
                [
                    str(u.Infra.runtime_python(root)),
                    "-c",
                    (
                        "import json, sysconfig; "
                        "print(json.dumps([sysconfig.get_path('purelib')]))"
                    ),
                ],
                cwd=root,
            )
        )
        tm.that(
            u.Cli.process_succeeded(locations.outcome),
            eq=True,
            msg=locations.stdout + locations.stderr,
        )
        metadata_paths = t.Infra.STR_SEQ_ADAPTER.validate_json(locations.stdout)
        repository = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root)
        ).repository
        installed = u.installed_distributions(
            name=repository.distribution,
            path=metadata_paths,
        )
        tm.that(len(installed), eq=1)
        direct_url = installed[0].read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        tm.ok(direct_url is not None)
        if direct_url is None:
            pytest.fail("native editable installation has no PEP 610 receipt")
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(direct_url, strict=True)
        tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
                repository,
                root,
                installed[0],
                receipt,
            ),
        )
        declaration = tm.ok(
            FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                root,
                repository,
            ),
        )
        tm.that(declaration.path, eq=(root / c.PYPROJECT_FILENAME).resolve())
        tm.that(
            declaration.content,
            eq=(root / c.PYPROJECT_FILENAME).read_bytes(),
        )
        inventory = installed[0].files
        tm.ok(inventory is not None)
        if inventory is None:
            pytest.fail("installed editable has no file inventory")
        pth_files = tuple(
            Path(str(installed[0].locate_file(item)))
            for item in inventory
            if str(item).endswith(".pth")
        )
        tm.that(len(pth_files), eq=1)
        docs = root / "docs"
        tm.ok(u.Cli.ensure_dir(docs))
        tm.ok(u.Cli.atomic_write_text_file(pth_files[0], f"{docs}\n"))
        tm.fail(
            FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
                repository,
                root,
                installed[0],
                receipt,
            ),
            has="pth exposes no declared package",
        )
        tm.fail(
            FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                root,
                repository,
            ),
            has="pth exposes no declared package",
        )

    @staticmethod
    def _materialize_editable_layout(root: Path, layout: str) -> None:
        """Declare real source roots through the existing native Hatch table."""
        roots = (root / "left", root / "right")
        primary = u.Infra.project_package_name(root)
        package_names = (
            (primary, primary)
            if layout == "namespace"
            else (primary, f"{primary}_companion")
        )
        declarations: list[str] = []
        for source_root, name in zip(roots, package_names, strict=True):
            package = source_root / name
            tm.ok(u.Cli.ensure_dir(package))
            if layout in {"multiple", "hatch-sources"}:
                tm.ok(u.Cli.atomic_write_text_file(package / c.Infra.INIT_PY, ""))
            else:
                tm.ok(u.Cli.atomic_write_text_file(package / "portion.py", ""))
            declarations.append(package.relative_to(root).as_posix())
        pyproject = root / c.PYPROJECT_FILENAME
        payload = u.Tests.toml_payload(pyproject.read_text(encoding="utf-8"))
        wheel = tm.not_none(
            u.Cli.toml_mapping_path(
                payload, ("tool", "hatch", "build", "targets", "wheel")
            )
        )
        if layout == "hatch-sources":
            for key in ("packages", "include", "sources"):
                wheel.pop(key, None)
            wheel["include"] = [f"/{declaration}/**" for declaration in declarations]
            wheel["sources"] = dict(zip(declarations, package_names, strict=True))
        else:
            boundary_packages: t.JsonValueList = list(declarations)
            wheel["packages"] = boundary_packages
        tm.ok(u.Cli.toml_write_mapping(pyproject, payload))
