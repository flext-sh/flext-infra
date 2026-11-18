"""Installed-distribution and provider discovery for FlextInfraUtilitiesCodemodRules.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sysconfig
from collections.abc import Mapping, MutableMapping, Sequence
from functools import lru_cache
from importlib.machinery import PathFinder
from importlib.metadata import Distribution
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r
from flext_infra._utilities import FlextInfraUtilitiesProjectDiscovery


class FlextInfraUtilitiesCodemodRulesDistributions:
    """Project requirements, installed distributions, and codemod providers."""

    @staticmethod
    def project_requirements(
        root: Path,
    ) -> p.Result[tuple[str, Sequence[str]]]:

        pyproject = root / c.PYPROJECT_FILENAME
        document = u.Cli.toml_read_document(pyproject)
        if document.failure:
            return r[tuple[str, Sequence[str]]].from_failure(document)
        payload = u.Cli.toml_as_mapping(document.value)
        project = payload.get(c.Infra.PROJECT) if payload else None
        if not isinstance(project, Mapping):
            return r[tuple[str, Sequence[str]]].fail(
                f"missing [project] table: {pyproject}",
            )
        raw_name = project.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            return r[tuple[str, Sequence[str]]].fail(
                f"missing project.name: {pyproject}",
            )
        raw_dependencies = project.get(c.Infra.DEPENDENCIES)
        if raw_dependencies is None:
            # ``project.dependencies`` is spec-optional: a project with no
            # declared runtime dependency has an empty runtime closure, not a
            # malformed manifest.
            raw_dependencies = ()
        if not isinstance(raw_dependencies, Sequence) or isinstance(
            raw_dependencies,
            str,
        ):
            return r[tuple[str, Sequence[str]]].fail(
                f"project.dependencies must be a sequence: {pyproject}",
            )
        dependencies: set[str] = set()
        for raw in raw_dependencies:
            if not isinstance(raw, str):
                return r[tuple[str, Sequence[str]]].fail(
                    f"project dependency must be a string: {pyproject}",
                )
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate():
                dependencies.add(canonicalize_name(requirement.name))
        return r[tuple[str, Sequence[str]]].ok((
            canonicalize_name(raw_name),
            tuple(sorted(dependencies)),
        ))

    @staticmethod
    @lru_cache(maxsize=1)
    def codemod_environment_distributions() -> Mapping[str, Distribution]:
        """Index the distributions of the owning physical runtime environment.

        The environment the invocation runs in — the workspace's provisioned
        physical runtime — is the declared distribution authority: its metadata
        directories are indexed explicitly by path, once per process, and the
        interpreter's import search path is never enumerated. Every rule plan
        of the invocation reuses the one index.

        Returns:
            Canonical distribution name to its installed distribution.

        """
        return FlextInfraUtilitiesCodemodRulesDistributions._indexed_distributions(
            FlextInfraUtilitiesCodemodRulesDistributions._environment_metadata_paths(),
        )

    @staticmethod
    def _environment_metadata_paths() -> tuple[str, ...]:
        """Return the physical metadata directories of the owning environment.

        Returns:
            The de-duplicated resolved install directories, in order.

        """
        return tuple(
            dict.fromkeys(
                str(Path(sysconfig.get_path(key)).resolve())
                for key in ("purelib", "platlib")
            )
        )

    @classmethod
    def codemod_target_environment(
        cls,
        root: Path,
    ) -> p.Result[p.Infra.PythonEnvironmentObservation]:
        """Observe the TARGET repository's own provisioned Python environment.

        The rule plan of a repository is elected against that repository's
        runtime (``runtime_environment_dir``), never against the invoking
        interpreter: a consumer's runtime distributions live only in the
        consumer's environment. The target interpreter reports its own
        ``sys.path`` (editable ``.pth`` entries included) and import-package
        owners, once per environment: attached members share the workspace
        environment, so the interpreter is probed once for all of them.

        Returns:
            The target observation, or the first failure: an unprovisioned
            target environment, a failed interpreter probe, or a foreign
            reported prefix.

        """
        return cls._observed_environment(
            FlextInfraUtilitiesProjectDiscovery.runtime_environment_dir(root).resolve()
        )

    @staticmethod
    @lru_cache(maxsize=8)
    def _observed_environment(
        environment: Path,
    ) -> p.Result[p.Infra.PythonEnvironmentObservation]:
        """Probe one provisioned environment's interpreter once per run.

        Returns:
            The observation, or the first failure.

        """
        outcome = r[p.Infra.PythonEnvironmentObservation]
        python = FlextInfraUtilitiesProjectDiscovery.environment_python(environment)
        if not (environment / c.Infra.ENVIRONMENT_METADATA).is_file():
            return outcome.fail(
                f"target repository environment is not provisioned: "
                f"{environment}; run make setup in {environment.parent}",
            )
        probe = u.Cli.run(
            (str(python), "-I", "-c", c.Infra.BINDING_PACKAGE_SCRIPT),
            cwd=environment.parent,
        )
        if probe.failure:
            return outcome.from_failure(probe)
        facts = m.Infra.PythonEnvironmentObservation.model_validate_json(
            probe.value.stdout,
        )
        if facts.prefix.resolve() != environment:
            return outcome.fail(
                f"target interpreter reports a foreign environment: "
                f"expected={environment}, actual={facts.prefix}",
            )
        return outcome.ok(facts)

    @classmethod
    def codemod_target_import_paths(cls, root: Path) -> p.Result[tuple[str, ...]]:
        """Return the target environment's physical import search path.

        Import search paths may repeat the same physical directory. Query each
        directory once; distinct installations with the same name still fail.

        Returns:
            The de-duplicated resolved target ``sys.path`` entries, in order.

        """
        return cls.codemod_target_environment(root).map(
            lambda facts: tuple(
                dict.fromkeys(str(path.resolve()) for path in facts.import_paths)
            ),
        )

    @classmethod
    def codemod_target_distributions(
        cls, root: Path
    ) -> p.Result[Mapping[str, Distribution]]:
        """Index the distributions installed in the target environment.

        Returns:
            Canonical distribution name to its installed distribution.

        """
        return cls.codemod_target_import_paths(root).map(cls._indexed_distributions)

    @staticmethod
    @lru_cache(maxsize=8)
    def _indexed_provider_configs(
        paths: tuple[str, ...],
    ) -> Mapping[str, Path]:
        """Locate every installed distribution's codemod config exactly once.

        Where a distribution's package lives is a fact of the same import path
        that keys the distribution index, so discovery is reused by every rule
        plan of the invocation. The configs' contents are still read per plan.

        Returns:
            A read-only canonical-name index of the discovered provider configs.

        """
        configs: MutableMapping[str, Path] = {}
        for name in FlextInfraUtilitiesCodemodRulesDistributions._indexed_distributions(
            paths
        ):
            provider_config = (
                FlextInfraUtilitiesCodemodRulesDistributions._provider_config(
                    name, paths
                )
            )
            if provider_config is not None:
                configs[name] = provider_config
        return MappingProxyType(configs)

    @staticmethod
    @lru_cache(maxsize=8)
    def _indexed_distributions(
        paths: tuple[str, ...],
    ) -> Mapping[str, Distribution]:
        """Read every distribution's metadata on ``paths`` exactly once.

        Returns:
            A read-only canonical-name index of the installed distributions.

        Raises:
            ValueError: If two installations declare the same distribution.

        """
        indexed: MutableMapping[str, Distribution] = {}
        for installed in u.installed_distributions(path=list(paths)):
            raw_name = installed.metadata.get("Name")
            if not isinstance(raw_name, str) or not raw_name.strip():
                continue
            name = canonicalize_name(raw_name)
            previous = indexed.get(name)
            if previous is not None:
                msg = (
                    f"duplicate installed distribution metadata: {name} "
                    f"({previous.version} at {previous.locate_file('')}; "
                    f"{installed.version} at {installed.locate_file('')})"
                )
                raise ValueError(msg)
            indexed[name] = installed
        return MappingProxyType(indexed)

    @classmethod
    def codemod_runtime_closure(
        cls,
        direct: Sequence[str],
        indexed: Mapping[str, Distribution],
    ) -> frozenset[str]:
        pending = list(direct)
        resolved: set[str] = set()
        while pending:
            name = pending.pop()
            if name in resolved:
                continue
            installed = indexed.get(name)
            if installed is None:
                msg = f"required runtime distribution is not installed: {name}"
                raise ValueError(msg)
            resolved.add(name)
            pending.extend(cls._requirements(installed))
        return frozenset(resolved)

    @staticmethod
    def _requirements(installed: Distribution) -> Sequence[str]:
        requirements: set[str] = set()
        for raw in installed.requires or ():
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate():
                requirements.add(canonicalize_name(requirement.name))
        return tuple(sorted(requirements))

    @classmethod
    def _providers(
        cls,
        discovered: Mapping[str, Path],
        *,
        scope: str,
        selected: frozenset[str],
    ) -> p.Result[Mapping[str, Path]]:

        providers: MutableMapping[str, Path] = {}
        for name in sorted(selected):
            provider_config = discovered.get(name)
            if provider_config is None:
                continue
            declared_scope = cls._config_scope(provider_config)
            if declared_scope.failure:
                return r[Mapping[str, Path]].from_failure(declared_scope)
            if declared_scope.value == scope:
                providers[name] = provider_config
        return r[Mapping[str, Path]].ok(providers)

    @classmethod
    def _provider_order(
        cls,
        providers: Mapping[str, Path],
        indexed: Mapping[str, Distribution],
    ) -> Sequence[str]:

        selected = frozenset(providers)
        edges = {
            name: tuple(
                dependency
                for dependency in cls._requirements(indexed[name])
                if dependency in selected
            )
            for name in selected
        }
        order = u.Cli.dag_order(edges)
        if order.failure:
            raise ValueError(order.error)
        return order.value

    @staticmethod
    def _provider_config(name: str, paths: tuple[str, ...]) -> Path | None:
        """Locate one indexed distribution's codemod config, if it ships one.

        ``name`` is the distribution index's canonical name, so the installed
        metadata is never re-read here.

        Returns:
            The distribution's single codemod config, or ``None`` without one.

        Raises:
            ValueError: If the distribution exports more than one codemod config.

        """
        package_name = name.replace("-", "_")
        if not package_name.isidentifier():
            return None
        spec = PathFinder.find_spec(package_name, list(paths))
        if spec is None:
            return None
        roots = tuple(Path(path) for path in spec.submodule_search_locations or ())
        if not roots and spec.origin is not None:
            roots = (Path(spec.origin).parent,)
        # A distribution's rule root is its config directory: the packaged
        # copy (<pkg>/config) of an installed wheel, or the config directory
        # beside src/ of an editable checkout (<root>/src/<pkg> -> <root>).
        configs = {
            base / c.Infra.CODEMOD_CONFIG_RELPATH
            for root in roots
            for base in (root, root.parents[1])
            if (base / c.Infra.CODEMOD_CONFIG_RELPATH).is_file()
        }
        if len(configs) > 1:
            msg = f"distribution exports multiple codemod configs: {name}"
            raise ValueError(msg)
        return next(iter(configs), None)

    @staticmethod
    def _config_scope(config: Path) -> p.Result[str]:
        """Read one provider config's declared scope.

        The ``config`` parameter is the provider's config PATH: the
        flext-infra config facade import some lanes re-insert here shadows
        it and crashes the provider scope read.

        Returns:
            The resulting ``p.Result[str]``.

        """
        parsed = u.Cli.yaml_parse(config.read_text(encoding=c.DEFAULT_ENCODING))
        if parsed.failure:
            return r[str].from_failure(parsed)
        scope = parsed.value.get(c.Infra.CODEMOD_SCOPE_KEY)
        if not isinstance(scope, str) or scope not in {
            c.Infra.CODEMOD_SCOPE_UNIVERSAL,
            c.Infra.CODEMOD_SCOPE_RUNTIME,
        }:
            return r[str].fail(f"codemod config has invalid scope: {config}")
        return r[str].ok(scope)


__all__: list[str] = ["FlextInfraUtilitiesCodemodRulesDistributions"]
