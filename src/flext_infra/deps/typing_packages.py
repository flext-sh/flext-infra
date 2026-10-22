"""Generate installable third-party stubs through native Pyright and UV.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from importlib.machinery import PathFinder
from importlib.util import resolve_name
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import wrap
from typing import TYPE_CHECKING

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, GatherImportsVisitor
from libcst.helpers import get_full_name_for_node
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from flext_infra import c, config, m, r, settings, t, u
from flext_infra.gates import FlextInfraRuffFormatGate
from flext_infra.workspace.flext_binding import FlextInfraBindingService

if TYPE_CHECKING:
    from collections.abc import Mapping

    from flext_infra import p


class FlextInfraDependencyTypingPackages:
    """Own native generation, guarded publication and environment installation."""

    @classmethod
    def generate_typing_packages(
        cls,
        repository_root: Path,
        modules: t.StrSequence,
        policy: m.Infra.TypingGenerationPolicy,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Refresh generated packages and declare their native path dependencies.

        Returns:
            Source directories declared for Make's native resolution and install.

        """
        document = u.Cli.toml_read_document(
            repository_root / c.PYPROJECT_FILENAME
        ).unwrap()
        declared = u.Infra.generated_typing_packages(
            document, root=repository_root, policy=policy, for_generation=True
        ).unwrap()
        environment = FlextInfraBindingService.consumer_package_environment(
            consumer_root=repository_root,
            python=u.Infra.runtime_python(repository_root),
            packages=(),
        ).unwrap()
        installed = u.installed_distributions(
            path=tuple(str(path) for path in environment.metadata_paths)
        )
        roots = {
            name.split(".", maxsplit=1)[0]
            for name in (
                *modules,
                *(item.module for item in declared),
                *(
                    item.value
                    for package in installed
                    for item in package.entry_points
                    if item.group == c.Infra.TYPING_STUB_ENTRY_POINT_GROUP
                ),
            )
        }
        if not roots:
            return r[t.VariadicTuple[Path]].ok(())
        u.Cli.info(f"typings: generating {len(roots)} external package(s)")
        destination = repository_root / policy.directory
        with u.Infra.codegen_transaction_lease(destination / "packages"):
            packages = tuple(
                cls.generate_typing_package(
                    repository_root,
                    module,
                    policy,
                    tuple(
                        package.metadata["Name"]
                        for package in installed
                        if any(
                            path.parts[0] in {module, f"{module}.py"}
                            for path in package.files or ()
                        )
                    ),
                )
                for module in sorted(roots)
            )
            installed = u.Cli.run(
                [
                    settings.Infra.uv_executable or c.Infra.UV,
                    "add",
                    "--project",
                    str(repository_root),
                    "--group",
                    c.Infra.DEV,
                    "--frozen",
                    "--no-workspace",
                    "--",
                    *(str(path.relative_to(repository_root)) for path in packages),
                ],
                cwd=repository_root,
                timeout=c.Infra.TIMEOUT_MEDIUM,
            )
            if installed.failure:
                return r[t.VariadicTuple[Path]].from_failure(installed)
        return r[t.VariadicTuple[Path]].ok(packages)

    @staticmethod
    def authenticated_typing_sources(
        root: Path, policy: m.Infra.TypingGenerationPolicy
    ) -> frozenset[Path]:
        """Classify exact producer snapshots, never a directory or name prefix.

        Returns:
            Third-party stub files whose declared identity and digest authenticate.

        """
        document = u.Cli.toml_read_document(root / c.PYPROJECT_FILENAME).unwrap()
        packages = u.Infra.generated_typing_packages(
            document, root=root, policy=policy
        ).unwrap()
        return frozenset(
            state.path
            for package in packages
            for state in package.inputs
            if state.path.suffix == ".pyi"
        )

    @staticmethod
    def typing_contract_rules(
        root: Path, policy: m.Infra.TypingGenerationPolicy
    ) -> t.MappingKV[Path, frozenset[str]]:
        """Elect implementation-only rules from actual upstream declaration identity.

        Returns:
            Inapplicable implementation rules for authenticated external contracts.

        """
        document = u.Cli.toml_read_document(root / c.PYPROJECT_FILENAME).unwrap()
        packages = u.Infra.generated_typing_packages(
            document, root=root, policy=policy
        ).unwrap()
        if not packages:
            return {}
        environment = FlextInfraBindingService.consumer_package_environment(
            consumer_root=root, python=u.Infra.runtime_python(root), packages=()
        ).unwrap()
        banned = u.Cli.toml_table_path(
            document, ("tool", "ruff", "lint", "flake8-tidy-imports", "banned-api")
        )
        contracts: t.MutableMappingKV[Path, frozenset[str]] = {}
        for package in packages:
            source, is_package = (
                FlextInfraDependencyTypingPackages._typing_implementation_source(
                    package, environment
                )
            )
            for state in package.inputs:
                if state.path.suffix != ".pyi":
                    continue
                relative = state.path.relative_to(
                    package.path / f"{package.module}-stubs"
                )
                authored = root / policy.directory / package.module / relative
                implementation = (
                    source.parent / relative.with_suffix(".py")
                    if is_package
                    else source
                )
                if not authored.is_file() or not implementation.is_file():
                    continue
                rules = FlextInfraDependencyTypingPackages._typing_source_rules(
                    authored,
                    implementation,
                    state,
                    ".".join((package.module, *relative.parent.parts)),
                    tuple(str(name) for name in banned or ()),
                )
                if rules:
                    contracts[authored.resolve()] = rules
        return contracts

    @staticmethod
    def _typing_implementation_source(
        package: m.Infra.GeneratedTypingPackage,
        environment: m.Infra.PythonEnvironmentObservation,
    ) -> tuple[Path, bool]:
        """Resolve the exact declared implementation without executing its code.

        Returns:
            Implementation source path and whether it represents a package.

        Raises:
            ValueError: If the implementation version or source cannot authenticate.

        """
        requirement = Requirement(package.implementation)
        installed = u.installed_distributions(
            name=requirement.name,
            path=tuple(str(path) for path in environment.metadata_paths),
        )
        if len(installed) != 1 or installed[0].version not in requirement.specifier:
            msg = f"typing contract implementation differs: {package.implementation}"
            raise ValueError(msg)
        spec = PathFinder.find_spec(
            package.module, tuple(str(path) for path in environment.import_paths)
        )
        if spec is None or spec.origin is None:
            msg = f"typing contract implementation has no source: {package.module}"
            raise ValueError(msg)
        return Path(spec.origin), spec.submodule_search_locations is not None

    @staticmethod
    def _typing_source_rules(
        authored: Path,
        implementation: Path,
        state: m.Cli.AtomicFileState,
        namespace: str,
        banned: t.StrSequence,
    ) -> frozenset[str]:
        """Prove which local implementation choices are instead upstream identities.

        Returns:
            Only rules whose complete affected declaration set is upstream-owned.

        Raises:
            ValueError: If authored declarations diverge from the producer snapshot.

        """
        native = ast.parse(implementation.read_text(encoding=c.DEFAULT_ENCODING))
        declared = ast.parse(authored.read_text(encoding=c.DEFAULT_ENCODING))
        if state.content is None:
            msg = f"typing contract snapshot is missing: {state.path}"
            raise ValueError(msg)
        snapshot = ast.parse(state.content)
        if not FlextInfraDependencyTypingPackages._typing_declarations_match(
            declared.body, snapshot.body
        ) or not FlextInfraDependencyTypingPackages._typing_imports(
            declared, namespace
        ) <= FlextInfraDependencyTypingPackages._typing_imports(snapshot, namespace):
            msg = (
                "typing contract declaration differs from producer snapshot: "
                f"{authored}"
            )
            raise ValueError(msg)
        upstream = FlextInfraDependencyTypingPackages._typing_imports(native, namespace)
        imports = FlextInfraDependencyTypingPackages._typing_imports(
            declared, namespace
        )
        private = frozenset(
            item
            for item in imports
            if any(part.startswith("_") for part in item.split("."))
        )
        restricted = frozenset(
            item
            for item in imports
            if any(item == name or item.startswith(name + ".") for name in banned)
        )
        rules: set[str] = set()
        if private and private <= upstream:
            rules.add("import-private-name")
        if restricted and restricted <= upstream:
            rules.add("banned-api")
        exceptions = {
            node.name
            for node in ast.walk(declared)
            if isinstance(node, ast.ClassDef)
            and not node.name.endswith("Error")
            and any(
                ast.unparse(base).endswith(("Exception", "Error"))
                for base in node.bases
            )
        }
        if exceptions and exceptions <= {
            node.name for node in ast.walk(native) if isinstance(node, ast.ClassDef)
        }:
            rules.add("error-suffix-on-exception-name")
        return frozenset(rules)

    @staticmethod
    def _typing_declarations_match(
        declared: t.SequenceOf[ast.stmt], snapshot: t.SequenceOf[ast.stmt]
    ) -> bool:
        """Check authored declarations survive publication, allowing native members.

        Returns:
            Whether every declaration and class header is present unchanged.

        """
        for node in declared:
            if isinstance(node, ast.Import | ast.ImportFrom):
                continue
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and (node.value.value is Ellipsis or isinstance(node.value.value, str))
            ):
                continue
            if isinstance(node, ast.ClassDef):
                candidates = (
                    item
                    for item in snapshot
                    if isinstance(item, ast.ClassDef) and item.name == node.name
                )
                if not any(
                    tuple(
                        ast.dump(part)
                        for part in (
                            *node.bases,
                            *node.keywords,
                            *node.decorator_list,
                            *node.type_params,
                        )
                    )
                    == tuple(
                        ast.dump(part)
                        for part in (
                            *item.bases,
                            *item.keywords,
                            *item.decorator_list,
                            *item.type_params,
                        )
                    )
                    and FlextInfraDependencyTypingPackages._typing_declarations_match(
                        node.body, item.body
                    )
                    for item in candidates
                ):
                    return False
            elif not any(ast.dump(node) == ast.dump(item) for item in snapshot):
                return False
        return True

    @staticmethod
    def _typing_imports(tree: ast.Module, namespace: str) -> frozenset[str]:
        """Resolve declared import identities without importing the implementation.

        Returns:
            Absolute module or symbol names, independent of aliases and relativity.

        """
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = (
                    resolve_name("." * node.level + (node.module or ""), namespace)
                    if node.level
                    else node.module or ""
                )
                names.update(f"{module}.{alias.name}" for alias in node.names)
        return frozenset(names)

    @classmethod
    def generate_typing_package(
        cls,
        root: Path,
        module: str,
        policy: m.Infra.TypingGenerationPolicy,
        providers: t.StrSequence,
    ) -> Path:
        """Publish one generated distribution from its real installed source.

        Returns:
            The complete non-editable distribution source directory.

        Raises:
            ValueError: If the module has no unambiguous installed implementation.
            FileNotFoundError: If Pyright produces no stub files.

        """
        if (
            not c.Infra.PYTHON_IMPORT_NAME_RE.fullmatch(module)
            or module.startswith(c.Infra.INTERNAL_PREFIXES)
            or len(providers) != 1
        ):
            msg = f"typing generation requires one external distribution: {module}"
            raise ValueError(msg)
        environment = FlextInfraBindingService.consumer_package_environment(
            consumer_root=root,
            python=u.Infra.runtime_python(root),
            packages=(),
        ).unwrap()
        implementations = u.installed_distributions(
            name=providers[0],
            path=tuple(str(path) for path in environment.metadata_paths),
        )
        if len(implementations) != 1:
            msg = f"typing generation requires one installed distribution: {module}"
            raise ValueError(msg)
        implementation = implementations[0]
        attribution = (
            f"# Derived from {implementation.metadata['Name']}"
            f"=={implementation.version}\n"
        )
        for field in ("Author", "Author-email", "License", "License-Expression"):
            if value := implementation.metadata.get(field):
                attribution += "".join(
                    f"# Upstream {field}: {line}\n" for line in value.splitlines()
                )
        for license_file in implementation.metadata.get_all("License-File") or ():
            license_text = implementation.read_text(
                str(Path("licenses") / license_file)
                if Version(implementation.metadata["Metadata-Version"])
                >= Version("2.4")
                else license_file
            )
            if license_text is None:
                msg = f"upstream license file is missing: {license_file}"
                raise FileNotFoundError(msg)
            attribution += f"# Upstream License-File: {license_file}\n"
            attribution += "".join(f"# {line}\n" for line in license_text.splitlines())
        spec = PathFinder.find_spec(
            module, tuple(str(path) for path in environment.import_paths)
        )
        if spec is None or spec.origin is None:
            msg = f"typing implementation has no source origin: {module}"
            raise ValueError(msg)
        source = Path(spec.origin)
        name = canonicalize_name(policy.distribution_prefix + module, validate=True)
        package_root = root / policy.directory / name
        stub_package = f"{module}-stubs"
        u.Cli.info(f"typings: Pyright generation for {module}")
        with TemporaryDirectory(dir=root, prefix=".typing-package-") as scratch:
            native = Path(scratch) / "native"
            u.Cli.json_write(
                Path(scratch) / "pyrightconfig.json",
                {
                    "stubPath": str(native),
                    "extraPaths": [
                        str(
                            source.parent.parent
                            if spec.submodule_search_locations is not None
                            else source.parent,
                        ),
                    ],
                },
            ).unwrap()
            u.Cli.run(
                [
                    c.Infra.PYRIGHT,
                    "--project",
                    str(Path(scratch) / "pyrightconfig.json"),
                    "--pythonpath",
                    str(u.Infra.runtime_python(root)),
                    "--warnings",
                    "--createstub",
                    module,
                ],
                cwd=root,
                timeout=c.Infra.TIMEOUT_MEDIUM,
            ).unwrap()
            cls.normalize_typing_sources(root, module, policy, native)
            files = {
                Path(stub_package) / path.relative_to(native / module): (
                    cls._typing_source_header(
                        source.parent
                        / path.relative_to(native / module).with_suffix(".py"),
                        attribution,
                        path,
                    )
                    + path.read_bytes()
                )
                for path in sorted((native / module).rglob("*.pyi"))
            }
            if (single := native / f"{module}.pyi").is_file():
                files[Path(stub_package) / c.Infra.INIT_PYI] = (
                    cls._typing_source_header(source, attribution, single)
                    + single.read_bytes()
                )
            if not files:
                msg_0 = f"Pyright generated no stubs for {module}"
                raise FileNotFoundError(msg_0)
            context = m.Infra.TypingPackageRenderContext(
                distribution=name,
                version=u.Infra.generated_typing_version(implementation.version, files),
                module=module,
                runtime_requirement=(
                    f"{implementation.metadata['Name']}=={implementation.version}"
                ),
                python_required=config.Infra.codegen.toolchain.python_required_version,
                build=config.Infra.codegen.scaffold.build,
            )
            files[Path(c.PYPROJECT_FILENAME)] = (
                c.Infra.TYPING_STUB_HEADER
                + u.Cli.template_render(
                    Path(__file__).resolve().parent.parent
                    / "templates"
                    / c.Infra.TEMPLATE_TYPING_PACKAGE,
                    context,
                ).unwrap()
            ).encode(c.DEFAULT_ENCODING)
            cls._publish_typing_package(package_root, stub_package, files)
        return package_root

    @classmethod
    def _publish_typing_package(
        cls, package_root: Path, stub_package: str, files: Mapping[Path, bytes]
    ) -> None:
        """Validate ownership of the whole candidate before publishing any bytes.

        Raises:
            ValueError: If any target or obsolete stub is not producer-owned.

        """
        obsolete = tuple(
            path
            for path in sorted((package_root / stub_package).rglob("*.pyi"))
            if path.relative_to(package_root) not in files
        )
        removals = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in obsolete
        )
        for path in (*obsolete, *(package_root / name for name in files)):
            u.Cli.ensure_dir(path.parent).unwrap()
            content = u.Cli.atomic_read_binary_file_state(path).unwrap().content
            if content is not None and not content.startswith(
                c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING),
            ):
                msg = f"typing generation does not own {path}"
                raise ValueError(msg)
        for relative, content in files.items():
            cls._publish_typing_source(package_root / relative, content)
        for before in removals:
            u.Cli.atomic_delete_binary_file_guarded(before).unwrap()

    @staticmethod
    def _typing_source_header(
        source: Path, attribution: str, declarations: Path
    ) -> bytes:
        """Preserve each implementation's literal leading notices, without invention.

        Returns:
            Producer marker, upstream metadata/license and original source comments.

        """
        authored = cst.parse_module(declarations.read_text(encoding=c.DEFAULT_ENCODING))
        header = c.Infra.TYPING_STUB_HEADER + "".join(
            authored.code_for_node(line) for line in authored.header
        )
        header += (
            "\n".join(
                part
                for line in attribution.splitlines()
                for part in (wrap(line.rstrip(), subsequent_indent="# ") or ["#"])
            )
            + "\n"
        )
        if source.is_file():
            header += f"# Upstream source: {source.name}\n"
            for line in source.read_text(encoding=c.DEFAULT_ENCODING).splitlines():
                if line and not line.startswith("#"):
                    break
                header += line.rstrip() + "\n"
        return header.encode(c.DEFAULT_ENCODING)

    @classmethod
    def normalize_typing_sources(
        cls,
        root: Path,
        module: str,
        policy: m.Infra.TypingGenerationPolicy,
        native: Path,
    ) -> None:
        """Normalize native stubs with the consumer's explicit declarations.

        Raises:
            ValueError: If an overlay is generated rather than authored source.

        """
        staged = tuple(sorted((native / module).rglob("*.pyi")))
        single = native / f"{module}.pyi"
        if single.is_file():
            staged = (*staged, single)
        authored_root = root / policy.directory / module
        staged = tuple(
            sorted(
                set(staged)
                | {
                    single
                    if single.is_file()
                    and path.relative_to(authored_root) == Path(c.Infra.INIT_PYI)
                    else native / module / path.relative_to(authored_root)
                    for path in authored_root.rglob("*.pyi")
                }
            )
        )
        for path in staged:
            relative = (
                Path(c.Infra.INIT_PYI)
                if path == single
                else path.relative_to(native / module)
            )
            declared = root / policy.directory / module / relative
            if not declared.is_file():
                continue
            content = declared.read_text(encoding=c.DEFAULT_ENCODING)
            if content.startswith(c.Infra.TYPING_STUB_HEADER):
                msg = f"typing declarations must be authored: {declared}"
                raise ValueError(msg)
            authored = cst.parse_module(content)
            if not path.is_file():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding=c.DEFAULT_ENCODING)
                continue
            imports = GatherImportsVisitor(
                CodemodContext(
                    full_package_name=".".join((module, *relative.parent.parts)),
                )
            )
            generated = cst.parse_module(path.read_text(encoding=c.DEFAULT_ENCODING))
            generated.visit(imports)
            declared_imports = GatherImportsVisitor(imports.context)
            authored.visit(declared_imports)
            context = CodemodContext()
            for name, item in imports.symbol_mapping.items():
                if name in declared_imports.symbol_mapping:
                    continue
                AddImportsVisitor.add_needed_import(
                    context,
                    item.module_name,
                    item.obj_name,
                    item.alias,
                    item.relative,
                )
            merged = authored.with_changes(
                body=cls._merge_typing_declarations(generated.body, authored.body)
            )
            path.write_text(
                AddImportsVisitor(context).transform_module(merged).code,
                encoding=c.DEFAULT_ENCODING,
            )
        FlextInfraRuffFormatGate.format_files(root, staged).unwrap()

    @classmethod
    def _merge_typing_declarations(
        cls,
        native: t.SequenceOf[t.Infra.CstStatement],
        declared: t.SequenceOf[t.Infra.CstStatement],
    ) -> t.VariadicTuple[t.Infra.CstStatement]:
        """Apply explicit signatures and fields without dropping native SDK members.

        Returns:
            Declarations with their authored import closure and native members retained.

        Raises:
            TypeError: If an overlay changes the kind of an existing declaration.

        """
        body = list(declared)
        positions = {
            name: index
            for index, statement in enumerate(body)
            if (name := cls._typing_declaration_name(statement)) is not None
        }
        for statement in native:
            name = cls._typing_declaration_name(statement)
            if name is None:
                continue
            if name not in positions:
                positions[name] = len(body)
                body.append(statement)
                continue
            previous = body[positions[name]]
            if isinstance(previous, cst.ClassDef):
                if isinstance(statement, cst.SimpleStatementLine):
                    continue
                if (
                    isinstance(statement, cst.ClassDef)
                    and isinstance(statement.body, cst.SimpleStatementSuite)
                    and len(statement.body.body) == 1
                    and isinstance(statement.body.body[0], cst.Expr)
                    and isinstance(statement.body.body[0].value, cst.Ellipsis)
                ):
                    continue
                if (
                    isinstance(statement, cst.ClassDef)
                    and isinstance(previous.body, cst.SimpleStatementSuite)
                    and len(previous.body.body) == 1
                    and isinstance(previous.body.body[0], cst.Expr)
                    and isinstance(previous.body.body[0].value, cst.Ellipsis)
                ):
                    body[positions[name]] = previous.with_changes(body=statement.body)
                    continue
                if (
                    not isinstance(statement, cst.ClassDef)
                    or not isinstance(previous.body, cst.IndentedBlock)
                    or not isinstance(statement.body, cst.IndentedBlock)
                ):
                    msg = f"typing declaration changes native class: {name}"
                    raise TypeError(msg)
                body[positions[name]] = previous.with_changes(
                    body=previous.body.with_changes(
                        body=cls._merge_typing_declarations(
                            statement.body.body, previous.body.body
                        )
                    )
                )
                continue
        return tuple(body)

    @staticmethod
    def _typing_declaration_name(statement: t.Infra.CstStatement) -> str | None:
        """Identify only explicit stub declarations, never infer an SDK type.

        Returns:
            The declaration's local name, or no name for imports and controls.

        """
        if isinstance(statement, cst.FunctionDef | cst.ClassDef):
            return statement.name.value
        if isinstance(statement, cst.SimpleStatementLine) and len(statement.body) == 1:
            item = statement.body[0]
            if isinstance(item, cst.AnnAssign):
                return get_full_name_for_node(item.target)
            if isinstance(item, cst.TypeAlias):
                return item.name.value
            if isinstance(item, cst.Assign) and len(item.targets) == 1:
                return get_full_name_for_node(item.targets[0].target)
        return None

    @staticmethod
    def _publish_typing_source(path: Path, content: bytes) -> None:
        """Publish owned changed bytes under their captured physical preconditions.

        Raises:
            ValueError: If typing generation does not own ``path``.

        """
        path.parent.mkdir(parents=True, exist_ok=True)
        before = u.Cli.atomic_read_binary_file_state(path).unwrap()
        if before.content == content:
            return
        if before.content is not None and not before.content.startswith(
            c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING),
        ):
            msg = f"typing generation does not own {path}"
            raise ValueError(msg)
        u.Cli.atomic_write_binary_file_guarded(
            before,
            content,
            permission_mode=None,
        ).unwrap()


__all__: list[str] = ["FlextInfraDependencyTypingPackages"]
