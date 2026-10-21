"""Generate installable third-party stubs through native Pyright and UV.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from hashlib import sha256
from importlib.metadata import distribution, entry_points, packages_distributions
from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import AddImportsVisitor, GatherImportsVisitor
from libcst.helpers import get_full_name_for_node
from packaging.utils import canonicalize_name
from packaging.version import Version

from flext_infra import c, config, m, r, settings, t, u
from flext_infra.gates import FlextInfraRuffFormatGate

if TYPE_CHECKING:
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
        roots = {
            name.split(".", maxsplit=1)[0]
            for name in (
                *modules,
                *(
                    item.value
                    for item in entry_points(
                        group=c.Infra.TYPING_STUB_ENTRY_POINT_GROUP,
                    )
                ),
            )
        }
        if not roots:
            return r[t.VariadicTuple[Path]].ok(())
        u.Cli.info(f"typings: generating {len(roots)} external package(s)")
        providers = packages_distributions()
        destination = repository_root / policy.directory
        with u.Infra.codegen_transaction_lease(destination / "packages"):
            packages = tuple(
                cls.generate_typing_package(
                    repository_root,
                    module,
                    policy,
                    providers.get(module, ()),
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
                    *(str(path) for path in packages),
                ],
                cwd=repository_root,
                timeout=c.Infra.TIMEOUT_MEDIUM,
            )
            if installed.failure:
                return r[t.VariadicTuple[Path]].from_failure(installed)
        return r[t.VariadicTuple[Path]].ok(packages)

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
        implementation = distribution(providers[0])
        spec = find_spec(module)
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
            native_config = Path(scratch) / "pyrightconfig.json"
            u.Cli.json_write(
                native_config,
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
                    str(native_config),
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
                    c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING)
                    + path.read_bytes()
                )
                for path in sorted((native / module).rglob("*.pyi"))
            }
            if (single := native / f"{module}.pyi").is_file():
                files[Path(stub_package) / c.Infra.INIT_PYI] = (
                    c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING)
                    + single.read_bytes()
                )
            if not files:
                msg_0 = f"Pyright generated no stubs for {module}"
                raise FileNotFoundError(msg_0)
            digest = sha256()
            for relative, content in files.items():
                digest.update(relative.as_posix().encode(c.DEFAULT_ENCODING))
                digest.update(content)
            context = m.Infra.TypingPackageRenderContext(
                distribution=name,
                version=f"{Version(implementation.version).public}+{digest.hexdigest()}",
                module=module,
                runtime_requirement=(
                    f"{implementation.metadata['Name']}=={implementation.version}"
                ),
                python_required=config.Infra.codegen.toolchain.python_required_version,
                build=config.Infra.codegen.scaffold.build,
            )
            template = (
                Path(__file__).resolve().parent.parent
                / "templates"
                / c.Infra.TEMPLATE_TYPING_PACKAGE
            )
            files[Path(c.PYPROJECT_FILENAME)] = (
                c.Infra.TYPING_STUB_HEADER
                + u.Cli.template_render(template, context).unwrap()
            ).encode(c.DEFAULT_ENCODING)
            for relative, content in files.items():
                cls._publish_typing_source(package_root / relative, content)
            for obsolete in sorted((package_root / stub_package).rglob("*.pyi")):
                if obsolete.relative_to(package_root) not in files:
                    before = u.Cli.atomic_read_binary_file_state(
                        obsolete,
                        required=True,
                    ).unwrap()
                    if before.content is None or not before.content.startswith(
                        c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING),
                    ):
                        msg = f"typing generation does not own {obsolete}"
                        raise ValueError(msg)
                    u.Cli.atomic_delete_binary_file_guarded(before).unwrap()
        return package_root

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
            imports = GatherImportsVisitor(
                CodemodContext(
                    full_package_name=".".join((module, *relative.parent.parts)),
                )
            )
            authored.visit(imports)
            context = CodemodContext()
            for item in imports.symbol_mapping.values():
                AddImportsVisitor.add_needed_import(
                    context,
                    item.module_name,
                    item.obj_name,
                    item.alias,
                    item.relative,
                )
            generated = cst.parse_module(path.read_text(encoding=c.DEFAULT_ENCODING))
            merged = generated.with_changes(
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
        body = list(native)
        positions = {
            name: index
            for index, statement in enumerate(body)
            if (name := cls._typing_declaration_name(statement)) is not None
        }
        for statement in declared:
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
                    # A class-object annotation does not replace its native class.
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
                            previous.body.body, statement.body.body
                        )
                    )
                )
                continue
            body[positions[name]] = statement
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
