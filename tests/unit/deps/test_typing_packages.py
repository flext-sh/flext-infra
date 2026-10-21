"""Native stub publication keeps explicit contracts and the remaining SDK surface.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, deps, m, t
from tests import tm, u


class TestsFlextInfraTypingPackages:
    """Exercise real declarations and native Pyright without mocking the SDK."""

    @staticmethod
    def _policy() -> m.Infra.TypingGenerationPolicy:
        """Read the live producer policy rather than copying mutable defaults.

        Returns:
            The validated native typing policy.

        """
        limits = u.Cli.json_as_mapping(
            deps.FlextInfraDependencyDetectionService().load_dependency_limits()[
                "typing_libraries"
            ]
        )
        return m.Infra.TypingGenerationPolicy.model_validate(limits["generation"])

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
