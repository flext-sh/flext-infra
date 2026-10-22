"""Native stub publication keeps explicit contracts and the remaining SDK surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from packaging.version import Version

from flext_infra import c, config, deps, gates, m, t, workspace
from tests import tm, u


class TestsFlextInfraTypingPackages:
    """Exercise real declarations and native Pyright without mocking the SDK."""

    @staticmethod
    def _policy() -> m.Infra.TypingGenerationPolicy:
        """Read the live producer policy rather than copying mutable defaults.

        Returns:
            The validated native typing policy.

        """
        return (
            deps.FlextInfraDependencyDetectionService().load_typing_generation_policy()
        )

    @classmethod
    def test_declarations_preserve_native_members_and_imports(
        cls, tmp_path: Path
    ) -> None:
        """A typed kwargs boundary and status field do not erase other SDK APIs."""
        policy = cls._policy()
        native = tmp_path / "native"
        generated = native / "sample" / c.Infra.INIT_PYI
        generated.parent.mkdir(parents=True)
        generated.write_text(
            "class Runner:\n"
            "    def run(self): ...\n"
            "def run_command(executable_cmd, cmdline_args=..., **kwargs): ...\n"
            "def run_async(**kwargs): ...\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declared = tmp_path / policy.directory / "sample" / c.Infra.INIT_PYI
        declared.parent.mkdir(parents=True)
        declared.write_text(
            "from typing import TextIO\n"
            "class Runner:\n"
            "    status: str\n"
            "def run_command(executable_cmd: str, cmdline_args: list[str] | None = ...,"
            " *, output_fd: TextIO | None = ...) -> tuple[str, str, int | None]: ...\n",
            encoding=c.DEFAULT_ENCODING,
        )
        deps.FlextInfraDependencyDetectionService.normalize_typing_sources(
            tmp_path, "sample", policy, native
        )
        merged = generated.read_text(encoding=c.DEFAULT_ENCODING)
        for retained in (
            "from typing import TextIO",
            "status: str",
            "def run(self)",
            "def run_async(**kwargs)",
            "output_fd: TextIO | None",
            "tuple[str, str, int | None]",
        ):
            tm.that(merged, has=retained)

    @classmethod
    def test_authored_helpers_aliases_comments_and_reexports_survive(
        cls, tmp_path: Path
    ) -> None:
        """Keep authored syntax even where native Pyright has no implementation."""
        policy = cls._policy()
        native = tmp_path / "native"
        generated = native / "sample" / c.Infra.INIT_PYI
        generated.parent.mkdir(parents=True)
        generated.write_text(
            "class Runner(UnknownBase):\n"
            "    def run(self): ...\n"
            "    def native_only(self): ...\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declared = tmp_path / policy.directory / "sample"
        declared.mkdir(parents=True)
        source = (
            "# Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
            "from .helpers import Event as Event\n"
            "# Preserve this declaration comment.\n"
            "type Status = str | None\n"
            "class Runner:\n"
            "    # Preserve this method comment.\n"
            "    def run(self) -> Status: ...\n"
        )
        (declared / c.Infra.INIT_PYI).write_text(source, encoding=c.DEFAULT_ENCODING)
        helper = "# Authored-only helper.\ntype Event = dict[str, str]\n"
        (declared / "helpers.pyi").write_text(helper, encoding=c.DEFAULT_ENCODING)
        producer = deps.FlextInfraDependencyDetectionService
        producer.normalize_typing_sources(tmp_path, "sample", policy, native)
        merged = generated.read_text(encoding=c.DEFAULT_ENCODING)
        for text in (
            "# Copyright",
            "Event as Event",
            "# Preserve this declaration comment.",
            "type Status =",
            "# Preserve this method comment.",
            "def run(self) -> Status",
            "def native_only(self)",
        ):
            tm.that(merged, has=text)
        tm.that("UnknownBase" in merged, eq=False)
        tm.that((generated.parent / "helpers.pyi").read_text(), eq=helper)
        producer.normalize_typing_sources(tmp_path, "sample", policy, native)
        tm.that(generated.read_text(), eq=merged)
        tm.that((declared / c.Infra.INIT_PYI).read_text(), eq=source)

    @classmethod
    def test_empty_declared_class_retains_native_members(cls, tmp_path: Path) -> None:
        """An ellipsis-only declaration changes bases, not the native member set."""
        policy = cls._policy()
        native = tmp_path / "native"
        generated = native / "sample" / c.Infra.INIT_PYI
        generated.parent.mkdir(parents=True)
        generated.write_text(
            "class Runner(UnknownBase):\n    def run(self): ...\n",
            encoding=c.DEFAULT_ENCODING,
        )
        declared = tmp_path / policy.directory / "sample" / c.Infra.INIT_PYI
        declared.parent.mkdir(parents=True)
        declared.write_text("class Runner: ...\n", encoding=c.DEFAULT_ENCODING)
        deps.FlextInfraDependencyDetectionService.normalize_typing_sources(
            tmp_path, "sample", policy, native
        )
        merged = generated.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(merged, has="def run(self)")
        tm.that("UnknownBase" in merged, eq=False)

    @classmethod
    def test_native_publication_is_formatted_and_stable(
        cls,
        source_preview_workspace: t.Pair[Path, Path],
    ) -> None:
        """Real Pyright output is normalized before hashing and guarded publication."""
        root, _ = source_preview_workspace
        policy = cls._policy()
        declarations = root / policy.directory / "packaging"
        declarations.mkdir(parents=True)
        source = declarations / c.Infra.INIT_PYI
        source.write_text("__version__:str\n", encoding=c.DEFAULT_ENCODING)
        contract = declarations / "version.pyi"
        contract.write_text(
            "# Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
            "\nclass InvalidVersion(ValueError): ...\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = source.read_bytes()
        producer = deps.FlextInfraDependencyDetectionService
        package = producer.generate_typing_package(
            root, "packaging", policy, ("packaging",)
        )
        files = {
            path.relative_to(package): path.read_bytes()
            for path in package.rglob("*")
            if path.is_file()
        }
        tm.that(
            files[Path("packaging-stubs") / c.Infra.INIT_PYI].decode(),
            has="__version__: str",
        )
        tm.that((package / "packaging-stubs" / "version.pyi").is_file(), eq=True)
        cls._validate_upstream_notices(root, package)
        producer.generate_typing_package(root, "packaging", policy, ("packaging",))
        tm.that(
            {
                path.relative_to(package): path.read_bytes()
                for path in package.rglob("*")
                if path.is_file()
            },
            eq=files,
        )
        tm.that(source.read_bytes(), eq=before)
        cls._validate_local_provenance(root, policy, package)
        cls._reject_path_provenance(root, policy, package)
        manifest = root / c.PYPROJECT_FILENAME
        manifest.write_text(
            manifest.read_text(encoding=c.DEFAULT_ENCODING)
            + f'\n[dependency-groups]\ndev = ["{package.name}"]\n'
            + f"\n[tool.uv.sources]\n{package.name} = "
            + f'{{path = "{package.relative_to(root).as_posix()}"}}\n',
            encoding=c.DEFAULT_ENCODING,
        )
        cls._validate_authorial_scope(root, policy, package)
        cls._validate_external_contract_scope(root, policy, contract)
        stub = package / "packaging-stubs" / c.Infra.INIT_PYI
        stub.write_bytes(stub.read_bytes() + b"\nchanged: str\n")
        with pytest.raises(RuntimeError, match="producer digest mismatch"):
            producer.authenticated_typing_sources(root, policy)
        with pytest.raises(RuntimeError, match="producer digest mismatch"):
            gates.FlextInfraRuffLintGate(root).check_files(
                (contract,),
                root,
                m.Infra.GateContext(
                    repository_root=root, reports_dir=root / ".reports"
                ),
            )
        document = tm.ok(u.Cli.toml_read_document(manifest))
        tm.that(
            u.Infra.generated_typing_packages(
                document, root=root, policy=policy
            ).failure,
            eq=True,
        )
        stub.write_bytes(files[Path("packaging-stubs") / c.Infra.INIT_PYI])
        cls._validate_local_provenance(root, policy, package)
        cls._reject_corrupt_provenance(
            root, policy, package, files[Path(c.PYPROJECT_FILENAME)]
        )
        cls._retire_unimported_package(root, policy, package)

    @staticmethod
    def _retire_unimported_package(
        root: Path, policy: m.Infra.TypingGenerationPolicy, package: Path
    ) -> None:
        """A declared and installed earlier output never resurrects its root.

        The project imports only typed distributions, so the stale package
        is retired from the declaration and the tree instead of regenerated,
        and a second run is a fixed point.
        """
        producer = deps.FlextInfraDependencyDetectionService
        tm.that(tm.ok(producer.generate_typing_packages(root, (root,), policy)), eq=())
        tm.that(package.exists(), eq=False)
        manifest = (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(package.name in manifest, eq=False)
        tm.that(tm.ok(producer.generate_typing_packages(root, (root,), policy)), eq=())
        tm.that(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
            eq=manifest,
        )

    @staticmethod
    def _validate_external_contract_scope(
        root: Path, policy: m.Infra.TypingGenerationPolicy, contract: Path
    ) -> None:
        """Preserve upstream names while native rules judge locally owned names."""
        producer = deps.FlextInfraDependencyDetectionService
        tm.that(
            producer.typing_contract_rules(root, policy)[contract.resolve()],
            eq=frozenset({"error-suffix-on-exception-name"}),
        )
        own = root / "owned.py"
        undeclared = root / policy.directory / "unowned_contract.pyi"
        for path in (own, undeclared):
            path.write_text(
                "# Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
                "\nimport argparse\n\nclass LocalException(Exception): ...\n",
                encoding=c.DEFAULT_ENCODING,
            )
        gate = gates.FlextInfraRuffLintGate(root)
        context = m.Infra.GateContext(
            repository_root=root,
            reports_dir=root / ".reports",
            ruff_args=(
                "--select",
                "CPY001,N818,TID251",
                "--config",
                'lint.flake8-tidy-imports.banned-api.argparse.msg = "Use local CLI"',
            ),
        )
        execution = gate.check_files((contract, own, undeclared), root, context)
        tm.that(
            {(Path(issue.file), issue.code) for issue in execution.issues},
            eq={
                (path, rule)
                for path in (own, undeclared)
                for rule in ("error-suffix-on-exception-name", "banned-api")
            },
        )
        original = contract.read_bytes()
        contract.write_text(
            "class InvalidVersion(ValueError): ...\n", encoding=c.DEFAULT_ENCODING
        )
        execution = gate.check_files((contract,), root, context)
        tm.that(
            tuple(issue.code for issue in execution.issues),
            eq=("missing-copyright-notice",),
        )
        contract.write_bytes(original + b"\nclass LocalException(Exception): ...\n")
        with pytest.raises(
            ValueError, match="declaration differs from producer snapshot"
        ):
            gate.check_files((contract,), root, context)
        contract.write_bytes(original)

    @staticmethod
    def _validate_upstream_notices(root: Path, package: Path) -> None:
        """Check real installed attribution and each source's literal leading notice."""
        observed = tm.ok(
            workspace.FlextInfraBindingService.consumer_package_environment(
                consumer_root=root,
                python=u.Infra.runtime_python(root),
                packages=(),
            )
        )
        installed = u.installed_distributions(
            name="packaging", path=tuple(str(path) for path in observed.metadata_paths)
        )[0]
        for file in installed.files or ():
            if file.parts[0] != "packaging" or file.suffix != ".py":
                continue
            stub = (
                package / "packaging-stubs" / Path(*file.parts[1:]).with_suffix(".pyi")
            )
            if not stub.is_file():
                continue
            generated = stub.read_text(encoding=c.DEFAULT_ENCODING)
            tm.that(
                generated,
                has=f"# Derived from {installed.metadata['Name']}=={installed.version}",
            )
            for line in (
                Path(str(installed.locate_file(file)))
                .read_text(encoding=c.DEFAULT_ENCODING)
                .splitlines()
            ):
                if line and not line.startswith("#"):
                    break
                tm.that(not line or line.rstrip() in generated, eq=True)
            for field in ("Author", "Author-email", "License", "License-Expression"):
                if value := installed.metadata.get(field):
                    for line in value.splitlines():
                        tm.that(
                            " ".join(generated.replace("#", "").split()),
                            has=" ".join(f"Upstream {field}: {line}".split()),
                        )
            for name in installed.metadata.get_all("License-File") or ():
                content = installed.read_text(
                    str(Path("licenses") / name)
                    if Version(installed.metadata["Metadata-Version"]) >= Version("2.4")
                    else name
                )
                assert content is not None
                tm.that(
                    " ".join(generated.replace("#", "").split()),
                    has=" ".join(content.replace("#", "").split()),
                )

    @staticmethod
    def _validate_authorial_scope(
        root: Path, policy: m.Infra.TypingGenerationPolicy, package: Path
    ) -> None:
        """Real Ruff still judges authored and undeclared files beside SDK snapshots."""
        producer = deps.FlextInfraDependencyDetectionService
        external = producer.authenticated_typing_sources(root, policy)
        tm.that(external, eq=frozenset(package.rglob("*.pyi")))
        authored = root / "first_party.py"
        undeclared = root / policy.directory / "unowned.pyi"
        for path in (authored, undeclared):
            path.write_text("value: int\n", encoding=c.DEFAULT_ENCODING)
        execution = gates.FlextInfraRuffLintGate(root).check_files(
            (authored, undeclared, *sorted(external)),
            root,
            m.Infra.GateContext(
                repository_root=root,
                reports_dir=root / ".reports",
                ruff_args=("--select", "CPY001"),
            ),
        )
        tm.that(
            {Path(issue.file) for issue in execution.issues},
            eq={authored, undeclared},
        )
        manifest = root / c.PYPROJECT_FILENAME
        original = manifest.read_bytes()
        manifest.write_text(
            '[project]\nname = "consumer"\nversion = "0.1.0"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            producer.authenticated_typing_sources(root, policy), eq=frozenset[Path]()
        )
        manifest.write_bytes(original)

    @staticmethod
    def _reject_path_provenance(
        root: Path, policy: m.Infra.TypingGenerationPolicy, package: Path
    ) -> None:
        """Reject mismatched names, missing metadata and physical symlink escapes."""
        for name, target in (
            (package.name + "-forged", package),
            (package.name, root.parent / package.name),
            (package.name, root / policy.directory / "missing"),
        ):
            declaration = u.Cli.toml_document_from_mapping({
                "tool": {"uv": {"sources": {name: {"path": target.as_posix()}}}}
            })
            tm.that(
                u.Infra.generated_typing_packages(
                    declaration, root=root, policy=policy
                ).failure,
                eq=True,
            )
        link = root / policy.directory / "escape"
        link.symlink_to(root.parent, target_is_directory=True)
        declaration = u.Cli.toml_document_from_mapping({
            "tool": {
                "uv": {
                    "sources": {
                        package.name: {"path": (link / package.name).as_posix()}
                    }
                }
            }
        })
        tm.that(
            u.Infra.generated_typing_packages(
                declaration, root=root, policy=policy
            ).failure,
            eq=True,
        )

    @staticmethod
    def _validate_local_provenance(
        root: Path, policy: m.Infra.TypingGenerationPolicy, package: Path
    ) -> None:
        """Prove a real producer output survives complete public conformance."""
        name = package.name
        declaration = u.Cli.toml_document_from_mapping({
            "project": {"name": "consumer", "version": "0.1.0", "dependencies": []},
            "dependency-groups": {"dev": [f"{name} ; python_version >= '3.13'"]},
            "tool": {
                "uv": {
                    "sources": {name: {"path": package.relative_to(root).as_posix()}}
                }
            },
        })
        authenticated = tm.ok(
            u.Infra.generated_typing_packages(declaration, root=root, policy=policy)
        )
        tm.that(len(authenticated), eq=1)
        tm.that(authenticated[0].module, eq="packaging")
        workspace = u.Tests.workspace_spec(
            u.Tests.repository_ref("consumer", role=c.Infra.MakeProfile.STANDALONE)
        )
        tc = config.Infra.codegen.toolchain
        resolution = m.Infra.UvResolutionSpec(
            link_mode=tc.uv_link_mode,
            constraint_dependencies=tc.uv_constraint_dependencies,
            environments=tc.uv_environments,
        )
        options = u.Infra.PyprojectConformOptions(
            repository_root=root, typing_policy=policy
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                u.Cli.toml_dumps(declaration),
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=resolution,
                options=options,
            )
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "dependency-groups", "dev"),
            eq=(f"{name} ; python_version >= '3.13'",),
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=workspace,
                    required_dev_dependencies=(),
                    uv_resolution=resolution,
                    options=options,
                )
            ),
            eq=rendered,
        )

    @staticmethod
    def _reject_corrupt_provenance(
        root: Path,
        policy: m.Infra.TypingGenerationPolicy,
        package: Path,
        original: bytes,
    ) -> None:
        """Reject altered metadata and bytes of the real generated distribution."""
        declaration = u.Cli.toml_document_from_mapping({
            "tool": {
                "uv": {
                    "sources": {
                        package.name: {"path": package.relative_to(root).as_posix()}
                    }
                }
            }
        })
        for needle, replacement in (
            ("flext.typing-stubs", "unowned.entry-point"),
            ("implementation =", "unowned ="),
            ("packaging-stubs", "wrong-stubs"),
        ):
            text = original.decode(c.DEFAULT_ENCODING)
            (package / c.PYPROJECT_FILENAME).write_text(
                text.replace(needle, replacement), encoding=c.DEFAULT_ENCODING
            )
            tm.that(
                u.Infra.generated_typing_packages(
                    declaration, root=root, policy=policy
                ).failure,
                eq=True,
            )
        (package / c.PYPROJECT_FILENAME).write_bytes(original)
        stub = package / "packaging-stubs" / c.Infra.INIT_PYI
        stub.write_text(
            stub.read_text(encoding=c.DEFAULT_ENCODING) + "\nchanged: str\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            u.Infra.generated_typing_packages(
                declaration, root=root, policy=policy
            ).failure,
            eq=True,
        )

    @classmethod
    def test_unowned_local_first_party_and_missing_git_remain_failures(
        cls, tmp_path: Path
    ) -> None:
        """A local binding or a reserved-looking name never authenticates a producer."""
        tc = config.Infra.codegen.toolchain
        resolution = m.Infra.UvResolutionSpec(
            link_mode=tc.uv_link_mode,
            constraint_dependencies=tc.uv_constraint_dependencies,
            environments=tc.uv_environments,
        )
        workspace = u.Tests.workspace_spec(
            u.Tests.repository_ref("consumer", role=c.Infra.MakeProfile.STANDALONE)
        )
        for name, path in (
            ("flext-unowned", "local"),
            (cls._policy().distribution_prefix + "forged", "outside"),
        ):
            document = u.Cli.toml_document_from_mapping({
                "project": {
                    "name": "consumer",
                    "version": "0.1.0",
                    "dependencies": [name],
                },
                "tool": {"uv": {"sources": {name: {"path": path}}}},
            })
            actual = u.Infra.pyproject_conform(
                u.Cli.toml_dumps(document),
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=resolution,
                options=u.Infra.PyprojectConformOptions(
                    repository_root=tmp_path, typing_policy=cls._policy()
                ),
            )
            tm.that(actual.failure, eq=True)
