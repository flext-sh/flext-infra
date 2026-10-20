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

from packaging.utils import canonicalize_name
from packaging.version import Version

from flext_infra import c, config, m, r, settings, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDependencyTypingPackages:
    """Own native generation, guarded publication and environment installation."""

    @classmethod
    def generate_typing_packages(
        cls,
        repository_root: Path,
        modules: t.StrSequence,
        policy: p.Infra.TypingGenerationPolicy,
    ) -> p.Result[t.StrSequence]:
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
            return r[t.StrSequence].ok(())
        u.Cli.info(f"typings: generating {len(roots)} external package(s)")
        providers = packages_distributions()
        destination = repository_root / policy.directory
        with u.Infra.codegen_transaction_lease(destination / "packages"):
            packages = tuple(
                cls._generate_typing_package(
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
                    "--no-sync",
                    "--no-workspace",
                    "--",
                    *(str(path) for path in packages),
                ],
                cwd=repository_root,
                timeout=c.Infra.TIMEOUT_MEDIUM,
            )
            if installed.failure:
                return r[t.StrSequence].from_failure(installed)
        return r[t.StrSequence].ok(tuple(str(path) for path in packages))

    @classmethod
    def _generate_typing_package(  # ruff: ignore[too-many-locals]
        cls,
        root: Path,
        module: str,
        policy: p.Infra.TypingGenerationPolicy,
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
        import_root = (
            source.parent.parent
            if spec.submodule_search_locations is not None
            else source.parent
        )
        name = canonicalize_name(policy.distribution_prefix + module)
        package_root = root / policy.directory / name
        stub_package = f"{module}-stubs"
        u.Cli.info(f"typings: Pyright generation for {module}")
        with TemporaryDirectory(dir=root, prefix=".typing-package-") as scratch:
            stage = Path(scratch)
            native = stage / "native"
            native_config = stage / "pyrightconfig.json"
            u.Cli.json_write(
                native_config,
                {"stubPath": str(native), "extraPaths": [str(import_root)]},
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
            build = config.Infra.codegen.scaffold.build
            context = m.Infra.TypingPackageRenderContext(
                distribution=name,
                version=f"{Version(implementation.version).public}+{digest.hexdigest()}",
                module=module,
                entry_point_group=c.Infra.TYPING_STUB_ENTRY_POINT_GROUP,
                stub_package=stub_package,
                runtime_requirement=(
                    f"{implementation.metadata['Name']}=={implementation.version}"
                ),
                python_required=config.Infra.codegen.toolchain.python_required_version,
                build_backend=build.backend,
                build_requires=build.requirements,
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
