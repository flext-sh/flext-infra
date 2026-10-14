"""Real candidate archives must serve consumers with runtime dependencies alone.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import sys
import zipfile
from email.parser import BytesParser
from pathlib import Path
from time import monotonic

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import config
from tests import c, m, t, tm, u

_RUNTIME_PROBE = """
import importlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import sysconfig

distribution_name, package_name, excluded_json, facade_json, wheel_uri = sys.argv[1:]
excluded = json.loads(excluded_json)
distribution = importlib.metadata.distribution(distribution_name)
package = importlib.import_module(package_name)
for facade in json.loads(facade_json):
    assert getattr(package, facade) is not None, facade
if "main" in json.loads(facade_json):
    assert package.main(["--help"]) == 0
for entry in distribution.entry_points:
    if entry.group == "console_scripts":
        assert callable(entry.load()), entry
        subprocess.run(
            [str(Path(sysconfig.get_path("scripts")) / entry.name), "--help"],
            check=True,
        )
core = importlib.import_module("flext_core")
assert core.r[str].ok("runtime").map(str.upper).value == "RUNTIME"
assert core.r[str].fail("expected-runtime-failure").failure
installed = {
    entry.metadata["Name"].lower().replace("_", "-").replace(".", "-")
    for entry in importlib.metadata.distributions()
}
for excluded_name in excluded:
    excluded_module = excluded_name.replace("-", "_")
    assert excluded_name not in installed, sorted(installed)
    assert importlib.util.find_spec(excluded_module) is None, excluded_module
    assert not any(
        name == excluded_module or name.startswith(excluded_module + ".")
        for name in sys.modules
    ), sorted(sys.modules)
origin = Path(package.__file__).resolve()
expected_origin = distribution.locate_file(package_name + "/__init__.py").resolve()
assert origin == expected_origin, (origin, expected_origin)
assert origin.is_relative_to(Path(sys.prefix).resolve()), (origin, sys.prefix)
direct_url = json.loads(distribution.read_text("direct_url.json"))
assert direct_url["url"] == wheel_uri, direct_url
assert not direct_url.get("dir_info", {}).get("editable", False), direct_url
print(json.dumps({
    "distribution": distribution.metadata["Name"],
    "requires_dist": distribution.requires,
    "origin": str(origin),
    "environment": sys.prefix,
    "excluded_distributions": excluded,
}, sort_keys=True))
"""


class TestsArtifactRuntime:
    """Build the actual producer, then import its archives outside every checkout."""

    @staticmethod
    def _identified_provider_repository(
        subject: str,
        producer: Path,
        tmp_path: Path,
        options: m.Cli.ProcessOptions,
    ) -> tuple[Path, str, t.StrSequence, t.StrSequence]:
        """Resolve the built repository and its governed runtime identity.

        Args:
            subject: The parametrized producer subject under proof.
            producer: The checked-out producer repository.
            tmp_path: Test scratch root owning a cloned provider checkout.
            options: Process options carrying the hermetic Git environment.

        Returns:
            The repository, its distribution, the excluded dev distributions
            and the facades the runtime probe must observe.

        """
        if subject == "infra":
            return (
                producer,
                config.Infra.codegen.infra_repository.distribution,
                (u.Tests.repository_ref("flext-tests").distribution,),
                ("c", "t", "p", "m", "u", "infra", "main"),
            )
        provider = u.Tests.repository_ref("flext-core")
        sources = tuple(
            source
            for source in u.Tests.locked_git_sources(producer)
            if source[0] == provider.url
        )
        tm.that(len(sources), eq=1)
        url, _branch, sha = sources[0]
        repository = tmp_path / "provider"
        tm.ok(
            u.Cli.run_checked(
                [
                    c.Infra.GIT,
                    "clone",
                    "--no-checkout",
                    url,
                    str(repository),
                ],
                cwd=tmp_path,
                options=options,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [c.Infra.GIT, "checkout", "--detach", sha],
                cwd=repository,
                options=options,
            ),
        )
        tm.that(
            tm.ok(
                u.Cli.capture(
                    [c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD],
                    cwd=repository,
                ),
            ).strip(),
            eq=sha,
        )
        tm.that(
            tm.ok(
                u.Cli.capture(
                    [c.Infra.GIT, "config", "--get", "remote.origin.url"],
                    cwd=repository,
                ),
            ).strip(),
            eq=url,
        )
        return (
            repository,
            provider.distribution,
            (
                config.Infra.codegen.infra_repository.distribution,
                u.Tests.repository_ref("flext-tests").distribution,
            ),
            ("c", "t", "p", "m", "u", "r", "FlextResult"),
        )

    @staticmethod
    def _built_wheel_artifact(
        uv: str,
        repository: Path,
        options: m.Cli.ProcessOptions,
        artifacts: Path,
        archive_kind: str,
    ) -> tuple[Path, bytes]:
        """Build the producer archive and isolate one installable wheel.

        Args:
            uv: The managed uv binary path.
            repository: The repository whose distribution is built.
            options: Process options carrying the build environment.
            artifacts: Scratch root owning the direct, source and rebuilt
                output directories.
            archive_kind: The parametrized archive kind under proof.

        Returns:
            The isolated wheel artifact with the untouched build manifest.

        """
        direct = artifacts / "direct"
        source = artifacts / "source"
        rebuilt = artifacts / "rebuilt"
        manifest_before = (repository / c.PYPROJECT_FILENAME).read_bytes()
        destination = direct if archive_kind == "wheel" else source
        tm.ok(
            u.Cli.run_checked(
                [
                    uv,
                    "build",
                    "--project",
                    str(repository),
                    f"--{archive_kind}",
                    "--out-dir",
                    str(destination),
                ],
                cwd=repository.parent,
                options=options,
            ),
        )
        directory = direct
        if archive_kind == "sdist":
            sdists = tuple(source.glob("*.tar.gz"))
            tm.that(len(sdists), eq=1)
            tm.ok(
                u.Cli.run_checked(
                    [
                        uv,
                        "build",
                        str(sdists[0]),
                        "--wheel",
                        "--out-dir",
                        str(rebuilt),
                    ],
                    cwd=repository.parent,
                    options=options,
                ),
            )
            directory = rebuilt
        wheels = tuple(directory.glob("*.whl"))
        tm.that(len(wheels), eq=1)
        return wheels[0], manifest_before

    @staticmethod
    def _verified_wheel_requires_dist(wheel: Path, excluded: t.StrSequence) -> None:
        """Assert the wheel metadata excludes every governed dev closure.

        Args:
            wheel: The built wheel artifact to inspect.
            excluded: Distributions that must never become runtime requirements.

        """
        with zipfile.ZipFile(wheel) as archive:
            metadata_files = tuple(
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            )
            tm.that(len(metadata_files), eq=1)
            metadata = BytesParser().parsebytes(archive.read(metadata_files[0]))
        requires_dist: t.SequenceOf[str] = tuple(
            metadata.get_all("Requires-Dist", ()),
        )
        declared: set[str] = {
            canonicalize_name(parsed.name)
            for requirement in requires_dist
            if (parsed := Requirement(requirement)).marker is None
            or (parsed.marker is not None and parsed.marker.evaluate({"extra": ""}))
        }
        tm.that(
            set(excluded).intersection(declared),
            eq=set[str](),
        )

    @staticmethod
    def _synced_consumer_runtime(
        tmp_path: Path,
        git_environment: t.StrMapping,
        uv: str,
        wheel: Path,
        distribution: str,
    ) -> tuple[Path, Path, m.Cli.ProcessOptions]:
        """Sync one isolated consumer runtime from the built wheel.

        Args:
            tmp_path: Test scratch root owning the consumer project.
            git_environment: The hermetic environment with registry access.
            uv: The managed uv binary path.
            wheel: The built wheel artifact the consumer depends on.
            distribution: The consumed distribution requirement name.

        Returns:
            The consumer project, its synced runtime interpreter and the
            consumer process options.

        """
        consumer = tmp_path / "consumer"
        consumer.mkdir()
        environment = tmp_path / "runtime"
        (consumer / c.PYPROJECT_FILENAME).write_text(
            "[project]\n"
            'name = "artifact-consumer"\n'
            'version = "1.0.0"\n'
            "requires-python = "
            f"{json.dumps(config.Infra.codegen.toolchain.python_required_version)}\n"
            "dependencies = "
            f"{json.dumps([f'{distribution} @ {wheel.as_uri()}'])}\n"
            "[tool.uv]\npackage = false\n",
            encoding="utf-8",
        )
        consumer_environment = {
            **git_environment,
            "UV_PROJECT_ENVIRONMENT": str(environment),
        }
        consumer_options = m.Cli.ProcessOptions(
            env=consumer_environment,
            remove_env_keys=tuple(
                key
                for key in c.Tests.MAKE_ISOLATION_ENV_KEYS
                if key not in consumer_environment
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [uv, "lock", "--python", sys.executable],
                cwd=consumer,
                options=consumer_options,
            ),
        )
        synced = tm.ok(
            u.Cli.run(
                [uv, "sync", "--frozen", "--no-default-groups"],
                cwd=consumer,
                options=consumer_options,
            ),
        )
        python = environment / "bin" / c.Infra.PYTHON
        tm.that(
            python.is_file(),
            eq=True,
            msg=synced.stdout + synced.stderr,
        )
        u.Cli.emit_raw(
            json.dumps(
                {
                    "consumer": str(consumer),
                    "environment": str(environment),
                    "python": str(python),
                    "uv_sync_succeeded": u.Cli.process_succeeded(synced.outcome),
                },
                sort_keys=True,
            )
            + "\n",
        )
        return consumer, python, consumer_options

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("subject", ["infra", "core"])
    @pytest.mark.parametrize("archive_kind", ["wheel", "sdist"])
    def test_artifact_runs_with_runtime_dependencies_only(
        tmp_path: Path,
        hermetic_git_environment: t.StrMapping,
        subject: str,
        archive_kind: str,
    ) -> None:
        """No synthetic profile or development environment can satisfy this proof."""
        started = monotonic()
        producer = Path(__file__).resolve().parents[3]
        uv = str(tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, producer)))
        # Git remains file-only at authenticated mirrors; native registry wheels
        # and isolated build requirements retain their real provisioning contract.
        git_environment = {**hermetic_git_environment, "UV_OFFLINE": "0"}
        options = m.Cli.ProcessOptions(
            env=git_environment,
            remove_env_keys=tuple(
                key
                for key in c.Tests.MAKE_ISOLATION_ENV_KEYS
                if key not in git_environment
            ),
        )
        repository, distribution, excluded, facades = (
            TestsArtifactRuntime._identified_provider_repository(
                subject, producer, tmp_path, options
            )
        )
        package_name = distribution.replace("-", "_")
        wheel, manifest_before = TestsArtifactRuntime._built_wheel_artifact(
            uv,
            repository,
            options,
            tmp_path / "artifacts",
            archive_kind,
        )
        TestsArtifactRuntime._verified_wheel_requires_dist(wheel, excluded)
        consumer, python, consumer_options = (
            TestsArtifactRuntime._synced_consumer_runtime(
                tmp_path,
                git_environment,
                uv,
                wheel,
                distribution,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    str(python),
                    "-I",
                    "-c",
                    _RUNTIME_PROBE,
                    distribution,
                    package_name,
                    json.dumps(excluded),
                    json.dumps(facades),
                    wheel.as_uri(),
                ],
                cwd=consumer,
                options=consumer_options,
            ),
        )
        if subject == "infra":
            tm.ok(
                u.Cli.run_checked(
                    [str(python), "-I", "-m", package_name, "--help"],
                    cwd=consumer,
                    options=consumer_options,
                ),
            )
        tm.that(
            (repository / c.PYPROJECT_FILENAME).read_bytes(),
            eq=manifest_before,
        )
        u.Cli.emit_raw(
            json.dumps(
                {
                    "distribution": distribution,
                    "archive_kind": archive_kind,
                    "elapsed_seconds": monotonic() - started,
                },
                sort_keys=True,
            )
            + "\n",
        )
