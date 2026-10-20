"""Exercise the dependency-declaration gate through the public registry.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
import venv
from importlib.metadata import distribution
from json import dumps
from pathlib import Path
from typing import ClassVar

import pytest

from flext_infra import config
from flext_infra.check import FlextInfraGateRegistry
from flext_infra.deps import FlextInfraToolTablesPhase
from tests import c, m, t, tm, u


class TestsFlextInfraDepsGate:
    """Undeclared imports fail at check time, never deep inside generation."""

    _SHIPPED_INFRA: ClassVar[str] = (
        "\n[tool.hatch.build.targets.wheel]\n"
        'only-include = ["src/fixturepkg", "infra"]\n'
        "\n[tool.hatch.build.targets.wheel.sources]\n"
        '"src/fixturepkg" = "fixturepkg"\ninfra = "infra"\n'
    )
    _SHIPPED_DATA: ClassVar[str] = (
        "\n[tool.hatch.build.targets.wheel]\n"
        'only-include = ["src/fixturepkg", "deploy/infra"]\n'
        "\n[tool.hatch.build.targets.wheel.sources]\n"
        '"src/fixturepkg" = "fixturepkg"\n'
        '"deploy/infra" = "fixturepkg/deploy/infra"\n'
    )

    @staticmethod
    def _ship_second_root(
        root: Path,
        declaration: str,
        directory: str,
        imports: str,
    ) -> None:
        """Write a second root and append the wheel declaration shipping it."""
        pyproject = root / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + declaration,
            encoding="utf-8",
        )
        (root / directory).mkdir(parents=True)
        (root / directory / "deploy.py").write_text(imports, encoding="utf-8")

    @staticmethod
    def _project(tmp_path: Path, dependencies: str, imports: str) -> Path:
        root = tmp_path / "repository"
        (root / "src" / "fixturepkg").mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n'
            f"dependencies = [{dependencies}]\n"
            '[tool.deptry]\nknown_first_party = ["fixturepkg"]\n',
            encoding="utf-8",
        )
        (root / "src" / "fixturepkg" / "__init__.py").write_text(
            imports,
            encoding="utf-8",
        )
        return root

    @staticmethod
    def _dependency_inputs(root: Path) -> m.Infra.RuntimeDependencyInputs:
        """Capture a real installed supplier and a target-owned native lock input.

        Returns:
            Runtime dependency inputs binding the elected supplier to the
            target's own lock, metadata state and executed source.

        """
        artifact = distribution("requests")
        files = tm.not_none(artifact.files)
        metadata_path = next(
            Path(str(artifact.locate_file(item)))
            for item in files
            if item.name == "METADATA"
        )
        package = m.Infra.LockedPackage(
            name=tm.not_none(artifact.metadata["Name"]),
            version=artifact.version,
            source=m.Infra.LockedPackageSource(registry="https://pypi.org/simple"),
        )
        lock_path = root / c.Infra.UV_LOCK_FILENAME
        lock_path.write_text(
            u.Cli.toml_dumps(
                u.Cli.toml_document_from_mapping({
                    "version": 1,
                    "package": [package.model_dump(mode="json", exclude_none=True)],
                })
            ),
            encoding="utf-8",
        )
        return m.Infra.RuntimeDependencyInputs(
            target_root=root,
            python=Path(sys.executable).absolute(),
            lock=u.Cli.atomic_read_binary_file_state(lock_path, required=True).unwrap(),
            providers=(
                m.Infra.RuntimeDependencyProvider(
                    modules=tuple(
                        sorted({
                            item.parts[0]
                            for item in files
                            if len(item.parts) > 1 and item.parts[1] == "__init__.py"
                        })
                    ),
                    package=package,
                    requirement=f"{package.name}>={package.version}",
                    inputs=(
                        u.Cli.atomic_read_binary_file_state(
                            metadata_path, required=True
                        ).unwrap(),
                    ),
                ),
            ),
            development_only=(),
            inputs=(
                u.Cli.atomic_read_binary_file_state(
                    root / "src" / "fixturepkg" / "__init__.py",
                    required=True,
                ).unwrap(),
            ),
        )

    @staticmethod
    def test_undeclared_import_blocks_at_check_time(tmp_path: Path) -> None:
        """An import the dependency list never declares is a loud finding."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            '"pyyaml>=6"',
            "import requests\n\n\ndef handler() -> int:\n"
            "    return len(requests.get)\n",
        )
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path / "reports"),
        )

        tm.that(result.result.passed, eq=False)
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(result.issues, truth=True, msg="undeclared import must produce an issue")
        tm.that(
            result.issues[0].code.startswith(f"{c.Infra.DEPS}-"),
            eq=True,
        )

    @staticmethod
    def test_declared_imports_pass_the_gate(tmp_path: Path) -> None:
        """A checkout whose imports the dependency list declares stays green."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            '"pyyaml>=6", "requests>=2"',
            "import requests\nimport yaml\n\n\ndef handler() -> str:\n"
            "    return yaml.safe_dump(requests.models.__name__)\n",
        )
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path / "reports"),
        )

        tm.that(result.result.passed, eq=True)
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.CLEAN)
        tm.that(result.issues, eq=())
        tm.that((root / ".reports").exists(), eq=False)

    @staticmethod
    def test_fix_requires_target_supplier_provenance(tmp_path: Path) -> None:
        """A native finding cannot authorize an ambient dependency repair."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import requests\n")
        pyproject = root / c.PYPROJECT_FILENAME
        before = pyproject.read_bytes()
        gate = tm.not_none(FlextInfraGateRegistry.default().create(c.Infra.DEPS, root))

        result = gate.fix(
            root,
            m.Infra.GateContext(
                repository_root=root,
                reports_dir=tmp_path / "reports",
                apply_fixes=True,
            ),
        )

        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        tm.that(pyproject.read_bytes(), eq=before)
        tm.that(any(issue.code.startswith(f"{c.Infra.DEPS}-") for issue in result.issues), truth=True)
        tm.that(result.raw_output, has="selected interpreter")

    @staticmethod
    def test_native_capture_rejects_an_existing_report(tmp_path: Path) -> None:
        """Checking and detection share one fresh native report contract."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            '"pyyaml>=6", "requests>=2"',
            "import requests\nimport yaml\n",
        )
        report_path = tmp_path / "native-deptry.json"
        scan = u.Infra.capture_deptry_scan(
            root,
            Path(sys.executable).parent,
            config_path=root / c.PYPROJECT_FILENAME,
            json_output_path=report_path,
        ).unwrap()
        before = report_path.read_bytes()

        reused = u.Infra.capture_deptry_scan(
            root,
            Path(sys.executable).parent,
            config_path=root / c.PYPROJECT_FILENAME,
            json_output_path=report_path,
        )

        tm.that(u.Cli.process_succeeded(scan.native.outcome), eq=True)
        tm.that(scan.report.root, eq=())
        tm.that(
            tuple(source.root.path for source in scan.source),
            eq=(root / c.Infra.DEFAULT_SRC_DIR,),
        )
        tm.that(scan.report_sha256, eq=u.Cli.sha256_bytes(before))
        tm.that(reused.failure, eq=True)
        tm.that(reused.error, has="already exists")
        tm.that(report_path.read_bytes(), eq=before)

    @staticmethod
    @pytest.mark.parametrize(
        ("declaration", "directory", "roots", "unused"),
        [
            (
                "",
                "infra",
                (c.Infra.DEFAULT_SRC_DIR,),
                ("pyyaml", "requests"),
            ),
            (
                _SHIPPED_INFRA,
                "infra",
                ("infra", c.Infra.DEFAULT_SRC_DIR),
                ("pyyaml",),
            ),
            (
                _SHIPPED_DATA,
                "deploy/infra",
                ("deploy/infra", c.Infra.DEFAULT_SRC_DIR),
                ("pyyaml",),
            ),
        ],
        ids=["undeclared", "namespace", "relocated-data"],
    )
    def test_native_scan_covers_every_declared_wheel_root(
        tmp_path: Path,
        declaration: str,
        directory: str,
        roots: t.StrTuple,
        unused: t.StrTuple,
    ) -> None:
        """Imports in every shipped root count; unshipped siblings stay outside."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            '"pyyaml>=6", "requests>=2"',
            "import os\n",
        )
        TestsFlextInfraDepsGate._ship_second_root(
            root,
            declaration,
            directory,
            "import requests\n",
        )
        ((root / directory).parent / "unshipped.py").write_text(
            "import yaml\n",
            encoding="utf-8",
        )

        scan = u.Infra.capture_deptry_scan(
            root,
            Path(sys.executable).parent,
            config_path=root / c.PYPROJECT_FILENAME,
            json_output_path=tmp_path / "native.json",
        ).unwrap()

        tm.that(
            tuple(source.root.path for source in scan.source),
            eq=tuple(root / item for item in roots),
        )
        # Each root holds exactly one module; the unshipped sibling is not one.
        tm.that(scan.scanned_files, eq=len(roots))
        tm.that(
            tuple(
                sorted(
                    item.module
                    for item in scan.report.root
                    if item.error.code == c.Infra.DEPTRY_UNUSED_DEPENDENCY_CODE
                )
            ),
            eq=unused,
        )

    @staticmethod
    @pytest.mark.parametrize("excluded", [False, True])
    def test_native_capture_requires_executed_sources(
        tmp_path: Path, *, excluded: bool
    ) -> None:
        """An empty tree and native exclusions cannot produce a clean receipt."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import os\n")
        if excluded:
            pyproject = root / c.PYPROJECT_FILENAME
            pyproject.write_text(
                pyproject.read_text(encoding="utf-8") + 'exclude = ["src/.*"]\n',
                encoding="utf-8",
            )
        else:
            (root / "src" / "fixturepkg" / "__init__.py").unlink()

        scan = u.Infra.capture_deptry_scan(
            root,
            Path(sys.executable).parent,
            config_path=root / c.PYPROJECT_FILENAME,
            json_output_path=tmp_path / "empty-native.json",
        )

        tm.that(scan.failure, eq=True)
        tm.that(scan.error, has="native scan coverage")
        tm.that(scan.error, has="Scanning 0 file")

    @staticmethod
    def test_development_only_supplier_requires_consumer_rewire(tmp_path: Path) -> None:
        """Identity stays present while its contract forbids runtime promotion.

        A development-only supplier cannot become a runtime requirement, so
        the repair refuses the unresolved import before any publication and
        the check keeps reporting it until the consumer is rewired.
        """
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import requests\n")
        inputs = TestsFlextInfraDepsGate._dependency_inputs(root)
        provider = inputs.providers[0]
        inputs = inputs.model_copy(update={"development_only": (provider.requirement,)})
        pyproject = root / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + f"\n[dependency-groups]\ndev = [{dumps(provider.requirement)}]\n",
            encoding="utf-8",
        )
        before = pyproject.read_bytes()
        before_lock = inputs.lock.path.read_bytes()
        gate = tm.not_none(FlextInfraGateRegistry.default().create(c.Infra.DEPS, root))
        context = m.Infra.GateContext(
            repository_root=root,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            runtime_dependency_inputs=inputs,
        )

        with pytest.raises(
            RuntimeError,
            match="runtime import requires one authored, installed, locked supplier",
        ) as rejected:
            gate.fix(root, context)
        checked = gate.check(root, context)

        tm.that(
            str(rejected.value),
            eq=(
                "Cannot unwrap failed result: runtime import requires one authored, "
                "installed, locked supplier: requests"
            ),
        )
        tm.that(checked.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(checked.result.passed, eq=False)
        tm.that(any(issue.code.endswith("DEP004") for issue in checked.issues), eq=True)
        tm.that(pyproject.read_bytes(), eq=before)
        tm.that(inputs.lock.path.read_bytes(), eq=before_lock)
        tm.that(inputs.providers, eq=(provider,))

    @staticmethod
    def test_fix_preserves_authored_requirement_policy_and_lock(tmp_path: Path) -> None:
        """Real deptry promotes exact authored extras and markers, then converges."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import requests\n")
        inputs = TestsFlextInfraDepsGate._dependency_inputs(root)
        supplier = inputs.providers[0]
        authored = (
            f"{supplier.package.name}[socks]>={supplier.package.version};"
            " python_version > '0'"
        )
        pyproject = root / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + f"\n[dependency-groups]\ndev = [{dumps(authored)}]\n",
            encoding="utf-8",
        )
        before_lock = inputs.lock.path.read_bytes()
        gate = tm.not_none(FlextInfraGateRegistry.default().create(c.Infra.DEPS, root))
        context = m.Infra.GateContext(
            repository_root=root,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            runtime_dependency_inputs=inputs,
        )

        repaired = gate.fix(root, context)
        after = pyproject.read_bytes()
        repeated = gate.fix(root, context)

        tm.that(repaired.outcome, eq=c.Infra.ToolOutcome.CLEAN)
        tm.that(repeated.outcome, eq=c.Infra.ToolOutcome.CLEAN)
        tm.that(
            u.Tests.toml_strings_at(after.decode("utf-8"), "project", "dependencies"),
            eq=(authored,),
        )
        tm.that(
            u.Tests.toml_strings_at(after.decode("utf-8"), "dependency-groups", "dev"),
            eq=(authored,),
        )
        tm.that(pyproject.read_bytes(), eq=after)
        tm.that(inputs.lock.path.read_bytes(), eq=before_lock)
        tm.that(repaired.raw_output, has="repair-rescan")

    @staticmethod
    @pytest.mark.parametrize(
        "change",
        ["ambiguous", "source", "shipped-source", "wrong-lock"],
    )
    def test_dependency_plan_refuses_unevidenced_repair(
        tmp_path: Path,
        change: str,
    ) -> None:
        """Missing identity proof and changed inputs cannot publish a requirement."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import requests\n")
        if change == "shipped-source":
            TestsFlextInfraDepsGate._ship_second_root(
                root,
                TestsFlextInfraDepsGate._SHIPPED_INFRA,
                "infra",
                "import os\n",
            )
        inputs = TestsFlextInfraDepsGate._dependency_inputs(root)
        scan = u.Infra.capture_deptry_scan(
            root,
            Path(sys.executable).parent,
            config_path=root / c.PYPROJECT_FILENAME,
            json_output_path=tmp_path / "native.json",
        ).unwrap()
        before = scan.settings.path.read_bytes()
        if change == "ambiguous":
            before_lock = inputs.lock.path.read_bytes()
            inputs = inputs.model_copy(update={"providers": inputs.providers * 2})
            plan = u.Infra.runtime_dependency_plan(scan, inputs).unwrap()
            tm.that(plan.unresolved_modules, has="requests")
            tm.that(plan.dependencies, eq=())
            rejected = u.Infra.publish_runtime_dependency_plan(plan)
            tm.fail(rejected)
            tm.that(
                rejected.error,
                eq=(
                    "runtime import requires one authored, installed, "
                    "locked supplier: requests"
                ),
            )
            tm.that(inputs.lock.path.read_bytes(), eq=before_lock)
        elif change in {"source", "shipped-source"}:
            plan = u.Infra.runtime_dependency_plan(scan, inputs).unwrap()
            changed = "infra" if change == "shipped-source" else "src"
            (root / changed / "new_module.py").write_text(
                "import os\n",
                encoding="utf-8",
            )
            rejected = u.Infra.publish_runtime_dependency_plan(plan)
            tm.that(rejected.failure, eq=True)
            tm.that(rejected.error, has="source changed")
        else:
            supplier = inputs.providers[0]
            invalid = supplier.model_copy(
                update={
                    "package": supplier.package.model_copy(update={"version": "0"}),
                }
            )
            rejected = u.Infra.runtime_dependency_plan(
                scan,
                inputs.model_copy(update={"providers": (invalid,)}),
            )
            tm.that(rejected.failure, eq=True)
            tm.that(rejected.error, has="selected lock")
        tm.that(scan.settings.path.read_bytes(), eq=before)

    @staticmethod
    @pytest.mark.parametrize("attached_peer", [False, True])
    def test_peer_import_remains_a_dependency_after_projection(
        tmp_path: Path,
        *,
        attached_peer: bool,
    ) -> None:
        """Composition never makes an installed peer a local production package."""
        root = TestsFlextInfraDepsGate._project(
            tmp_path,
            "",
            "import requests\n",
        )
        if attached_peer:
            peer = root / "peer" / "src" / "requests"
            peer.mkdir(parents=True)
            (peer / "__init__.py").write_text('"""Peer package."""\n', encoding="utf-8")
            (root / ".gitmodules").write_text(
                '[submodule "peer"]\npath = peer\n'
                "url = https://example.org/peer.git\nflext-managed = false\n",
                encoding="utf-8",
            )
        pyproject = root / c.PYPROJECT_FILENAME
        payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_read_json(pyproject).unwrap(),
        )
        FlextInfraToolTablesPhase(config.Infra.tooling).apply_payload(
            payload,
            path=pyproject,
        )
        u.Cli.atomic_write_text_file(
            pyproject,
            u.Cli.toml_dumps(u.Cli.toml_document_from_mapping(payload)),
        ).unwrap()
        gate = tm.not_none(FlextInfraGateRegistry.default().create(c.Infra.DEPS, root))

        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path / "reports"),
        )

        tm.that(result.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(result.result.passed, eq=False)
        tm.that(any("requests" in issue.message for issue in result.issues), truth=True)

    @staticmethod
    def test_invalid_config_is_native_execution_error(tmp_path: Path) -> None:
        """The real scanner's configuration failure is not an empty findings run."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import os\n")
        (root / c.PYPROJECT_FILENAME).write_text("[project", encoding="utf-8")
        gate = tm.not_none(FlextInfraGateRegistry.default().create(c.Infra.DEPS, root))
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path),
        )
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        tm.that(result.issues, truth=True)

    @staticmethod
    def test_missing_deptry_binary_fails_loud(
        tmp_path: Path,
    ) -> None:
        """A real interpreter without the console script emits native ERROR."""
        root = TestsFlextInfraDepsGate._project(tmp_path, '"pyyaml>=6"', "import os\n")
        environment = tmp_path / "runtime"
        venv.EnvBuilder(system_site_packages=True, symlinks=True).create(environment)
        executed = u.Cli.run_raw(
            (
                str(environment / "bin" / "python"),
                "-c",
                (
                    "from pathlib import Path; "
                    "from flext_infra import c, m; "
                    "from flext_infra.check import FlextInfraGateRegistry; "
                    f"root = Path({str(root)!r}); "
                    "gate = FlextInfraGateRegistry.default()."
                    "create(c.Infra.DEPS, root); "
                    "print(gate.check(root, m.Infra.GateContext("
                    "repository_root=root, reports_dir=root)).model_dump_json("
                    "round_trip=True))"
                ),
            ),
            cwd=root,
            options=m.Cli.ProcessOptions(
                env={
                    "PYTHONPATH": os.pathsep.join(
                        str(Path(path).absolute()) for path in sys.path
                    ),
                },
            ),
        ).unwrap()
        tm.that(u.Cli.process_succeeded(executed.outcome), eq=True)
        result = m.Infra.GateExecution.model_validate_json(executed.stdout)
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        tm.that(result.issues, truth=True)
        tm.that(c.Infra.DEPTRY in result.issues[0].message, truth=True)

    @staticmethod
    def test_missing_config_does_not_consume_stale_report(tmp_path: Path) -> None:
        """A stale clean report cannot attest a command with missing inputs."""
        root = TestsFlextInfraDepsGate._project(tmp_path, "", "import os\n")
        stale = root / ".reports" / "deptry-check.json"
        stale.parent.mkdir()
        stale.write_text("[]", encoding="utf-8")
        (root / c.PYPROJECT_FILENAME).unlink()
        gate = tm.not_none(
            FlextInfraGateRegistry.default().create(c.Infra.DEPS, root),
        )
        result = gate.check(
            root,
            m.Infra.GateContext(repository_root=root, reports_dir=tmp_path),
        )
        tm.that(result.outcome, eq=c.Infra.ToolOutcome.ERROR)
        tm.that(result.result.passed, eq=False)
        tm.that(result.issues, truth=True)
        tm.that(stale.read_text(encoding="utf-8"), eq="[]")

    @staticmethod
    @pytest.mark.parametrize(
        "payload",
        [
            "{}",
            "null",
            "[null]",
            "[{}]",
            "[",
            "[1]",
            '[{"error":{},"module":"x","location":{}}]',
            (
                '[{"error":{"code":"DEP001","message":"missing"},"module":"x",'
                '"location":{"file":"src/x.py","line":"1","column":0}}]'
            ),
        ],
    )
    def test_native_report_rejects_unrecognized_payload(
        tmp_path: Path,
        payload: str,
    ) -> None:
        """The public owned JSON boundary rejects malformed or incomplete records."""
        report = tmp_path / "deptry.json"
        report.write_text(payload, encoding="utf-8")
        with pytest.raises(ValueError, match="validation error"):
            m.Infra.DeptryNativeReport.model_validate_json(
                report.read_bytes(),
                strict=True,
            )

    @staticmethod
    def test_native_report_retains_dependency_null_locations(tmp_path: Path) -> None:
        """The external protocol permits null positions, not missing fields."""
        report = tmp_path / "deptry.json"
        report.write_text(
            '[{"error":{"code":"DEP002","message":"dependency is unused"},'
            '"module":"unused","location":{"file":"pyproject.toml",'
            '"line":null,"column":null}}]',
            encoding="utf-8",
        )
        parsed = m.Infra.DeptryNativeReport.model_validate_json(
            report.read_bytes(),
            strict=True,
        )
        tm.that(parsed.root[0].error.code, eq="DEP002")
        tm.that(parsed.root[0].location.line, eq=None)
