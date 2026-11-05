"""A family module binds its own letter from the composed upstream, never itself.

A facade composing several upstreams (``u(flext_meltano_u, flext_oracle_wms_u)``)
once left the upstream ambiguous, and the header law then bound the letter from
the own package root inside the very family assembling it — an import-time
cycle. Each family module now binds the first composed upstream exposing what
it reads, and a read no upstream exposes fails loud. A module already bound
from the own root (``from <package> import u``) is rebound the same way under
every law of the letter-binding renderer: the own-letter removal and the
upstream rebinding are selected together, never one without the other.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from tests import c, config, t, tm, u


class TestsFlextInfraCodemodFamilyLetterUpstreamElection:
    """The `u` family of a multi-upstream package binds `u` upstream."""

    @staticmethod
    def _project(
        tmp_path: Path, reads: tuple[str, str], *, origin: str = ".utilities"
    ) -> tuple[Path, Path]:
        """Build a package whose `u` facade composes two upstream letters.

        ``origin`` is the family modules' binding of `u`, relative to the
        package: a module path (``.utilities``) or the package root (``""``).

        Returns:
            The repository root and the package root.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        name = package.name
        family = package / "_utilities"
        family.mkdir()
        modules = {"service": reads[0], "runtime": reads[1]}
        for module, read in modules.items():
            (family / f"{module}.py").write_text(
                "from __future__ import annotations\n\n"
                "from typing import ClassVar\n\n"
                f"from {name}{origin} import u\n\n\n"
                f"class Probe{module.title()}:\n"
                '    """Probe."""\n\n'
                f"    value: ClassVar[object] = u.{read}\n\n\n"
                f'__all__: list[str] = ["Probe{module.title()}"]\n',
                encoding=c.DEFAULT_ENCODING,
            )
        (family / c.Infra.INIT_PY).write_text(
            "from .runtime import ProbeRuntime\n"
            "from .service import ProbeService\n\n"
            '__all__ = ("ProbeRuntime", "ProbeService")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "utilities.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import u as flext_cli_u\n"
            "from flext_core import u as flext_core_u\n\n"
            f"from {name}._utilities import ProbeRuntime, ProbeService\n\n\n"
            "class ProbeUtilities(flext_core_u, flext_cli_u):\n"
            '    """Probe facade composing two upstream letters."""\n\n'
            "    class Probe(ProbeRuntime, ProbeService):\n"
            '        """Probe namespace."""\n\n\n'
            "u = ProbeUtilities\n"
            '__all__: list[str] = ["ProbeUtilities", "u"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (package / c.Infra.INIT_PY).write_text(
            "from .utilities import ProbeUtilities, u\n\n"
            '__all__ = ("ProbeUtilities", "u")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        return repository, package

    @staticmethod
    def _documents(repository: Path) -> Mapping[str, t.JsonMapping]:
        """Render the letter-binding law documents of the project.

        Returns:
            The import-header documents keyed by id.

        """
        with u.Infra.codemod_workspace_snapshot(repository) as snapshot:
            facts = u.Infra.codemod_package_export_facts(snapshot, repository)
            return u.Infra.codemod_import_header_rules(snapshot, repository, facts)

    @staticmethod
    def _apply(repository: Path, sources: Path, law: str | None = None) -> None:
        """Stage the generated documents natively and apply them twice.

        With ``law``, only the documents a ``--laws`` theme selects are
        staged: those claiming it, and those claiming none, which receive the
        renderer's laws.
        """
        documents = {
            identity: document
            for identity, document in (
                TestsFlextInfraCodemodFamilyLetterUpstreamElection._documents(
                    repository
                ).items()
            )
            if law is None
            or "metadata" not in document
            or (
                isinstance(
                    claimed := u.Cli.json_walk_path(
                        document, ("metadata", c.Infra.CODEMOD_RULE_ENFORCE_KEY)
                    ),
                    list,
                )
                and law in claimed
            )
        }
        catalog = repository.parent / f"catalog-{law or 'all'}"
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        (catalog / "utils").mkdir(parents=True, exist_ok=True)
        for identity, document in documents.items():
            tm.ok(u.Cli.yaml_dump(catalog / "rules" / f"{identity}.yml", document))
        for _pass in range(2):
            tm.ok(
                u.Cli.capture([
                    c.Infra.SG,
                    "scan",
                    "-c",
                    str(catalog / "sgconfig.yml"),
                    "--update-all",
                    str(sources),
                ])
            )

    @staticmethod
    def test_each_family_module_binds_the_upstream_exposing_its_reads(
        tmp_path: Path,
    ) -> None:
        """`u.Cli` binds `flext_cli`; `u.fetch_logger` binds the first base."""
        repository, package = (
            TestsFlextInfraCodemodFamilyLetterUpstreamElection._project(
                tmp_path, ("Cli", "fetch_logger")
            )
        )
        TestsFlextInfraCodemodFamilyLetterUpstreamElection._apply(repository, package)
        service = (package / "_utilities" / "service.py").read_text(
            encoding=c.DEFAULT_ENCODING
        )
        runtime = (package / "_utilities" / "runtime.py").read_text(
            encoding=c.DEFAULT_ENCODING
        )
        tm.that(service, has="from flext_cli import u\n")
        tm.that(runtime, has="from flext_core import u\n")
        for rewritten in (service, runtime):
            tm.that(
                rewritten,
                lacks=[f"from {package.name} import", f"from {package.name}.utilities"],
            )

    @staticmethod
    def test_an_own_root_binding_is_rebound_upstream_under_each_law(
        tmp_path: Path,
    ) -> None:
        """`from <package> import u` in the family converges under every law."""
        renderer = next(
            entry
            for entry in config.Infra.codegen.ast_grep.renderers
            if entry.name == "codemod_import_header_rules"
        )
        tm.that(renderer.enforce, ne=())
        for law in renderer.enforce:
            repository, package = (
                TestsFlextInfraCodemodFamilyLetterUpstreamElection._project(
                    tmp_path / law, ("Cli", "fetch_logger"), origin=""
                )
            )
            TestsFlextInfraCodemodFamilyLetterUpstreamElection._apply(
                repository, package, law
            )
            family = package / "_utilities"
            first = {
                module: (family / f"{module}.py").read_text(encoding=c.DEFAULT_ENCODING)
                for module in ("service", "runtime")
            }
            tm.that(first["service"], has="from flext_cli import u\n")
            tm.that(first["runtime"], has="from flext_core import u\n")
            for rewritten in first.values():
                tm.that(rewritten, lacks=f"from {package.name} import")
            TestsFlextInfraCodemodFamilyLetterUpstreamElection._apply(
                repository, package, law
            )
            for module, text in first.items():
                tm.that(
                    (family / f"{module}.py").read_text(encoding=c.DEFAULT_ENCODING),
                    eq=text,
                )

    @staticmethod
    def test_a_read_of_the_own_namespace_fails_loud(tmp_path: Path) -> None:
        """No upstream exposes the own facade's namespace: no binding is elected."""
        repository, _package = (
            TestsFlextInfraCodemodFamilyLetterUpstreamElection._project(
                tmp_path, ("Probe", "fetch_logger")
            )
        )
        with u.Tests.raises(ValueError, match="no composed upstream exposes `u`"):
            TestsFlextInfraCodemodFamilyLetterUpstreamElection._documents(repository)
