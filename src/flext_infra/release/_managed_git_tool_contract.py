"""Validation and isolated Git execution for generic managed tool releases."""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlsplit

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.release._release_artifact_persistence import (
    FlextInfraReleaseArtifactPersistenceMixin,
)


class FlextInfraManagedGitToolContractMixin(FlextInfraReleaseArtifactPersistenceMixin):
    """Validate a generic release manifest and isolate Git execution."""

    @staticmethod
    def _relative_path(path: Path, *, label: str) -> p.Result[Path]:
        if path.is_absolute() or ".." in path.parts:
            return r[Path].fail(f"{label} must be repository-relative: {path}")
        return r[Path].ok(path)

    @staticmethod
    def _source_url_supported(source_url: str) -> bool:
        parsed = urlsplit(source_url)
        identity_invalid = (
            parsed.scheme != c.Infra.MANAGED_GIT_TOOL_ALLOWED_URL_SCHEME
            or parsed.hostname is None
        )
        credentials_present = parsed.username is not None or parsed.password is not None
        decoration_present = bool(parsed.query) or bool(parsed.fragment)
        return not any((identity_invalid, credentials_present, decoration_present))

    @classmethod
    def _validate_managed_git_tool_spec(
        cls, spec: m.Infra.ManagedGitToolRelease
    ) -> p.Result[bool]:
        if not cls._source_url_supported(spec.source_url):
            return r[bool].fail(
                "managed Git source must be credential-free HTTPS without query or fragment"
            )
        for path, label in (
            (spec.source_subdirectory, "source_subdirectory"),
            (spec.artifact.build_path, "artifact.build_path"),
        ):
            relative = cls._relative_path(path, label=label)
            if relative.failure:
                return r[bool].fail(relative.error or f"invalid {label}")
        artifact = spec.artifact
        if artifact.build_path == Path():
            return r[bool].fail("artifact.build_path must name one file")
        if artifact.build_path.name == c.Infra.MANAGED_GIT_TOOL_RECEIPT_FILENAME:
            return r[bool].fail("artifact filename collides with the release receipt")
        if (
            not artifact.install_path.is_absolute()
            or not spec.artifact_store.is_absolute()
        ):
            return r[bool].fail(
                "managed install and artifact store paths must be absolute"
            )
        if not Path(spec.build_command[0]).is_absolute():
            return r[bool].fail("build command executable must be absolute")
        if not any(
            c.Infra.MANAGED_GIT_TOOL_ARTIFACT_PLACEHOLDER in item
            for item in spec.build_command
        ):
            return r[bool].fail(
                "build command must write the "
                f"{c.Infra.MANAGED_GIT_TOOL_ARTIFACT_PLACEHOLDER} placeholder"
            )
        environment_names = tuple(item.name for item in spec.build_environment)
        if len(environment_names) != len(set(environment_names)):
            return r[bool].fail("build environment contains duplicate names")
        reserved = (
            set(environment_names) & c.Infra.MANAGED_GIT_TOOL_RESERVED_BUILD_ENV_KEYS
        )
        if reserved:
            return r[bool].fail(
                f"build environment overrides reserved keys: {', '.join(sorted(reserved))}"
            )
        probe_names = tuple(probe.name for probe in spec.probes)
        if len(probe_names) != len(set(probe_names)):
            return r[bool].fail("runtime probes contain duplicate names")
        for probe in spec.probes:
            executable = probe.command[0]
            if (
                executable != c.Infra.MANAGED_GIT_TOOL_ARTIFACT_PLACEHOLDER
                and not Path(executable).is_absolute()
            ):
                return r[bool].fail(
                    f"probe executable must be absolute or {{artifact}}: {probe.name}"
                )
        return r[bool].ok(True)

    @staticmethod
    def _resolve_git_executable() -> p.Result[Path]:
        resolved = shutil.which(c.Infra.GIT)
        if resolved is None:
            return r[Path].fail("required Git executable is unavailable")
        executable = Path(resolved).resolve()
        if not executable.is_file():
            return r[Path].fail(f"resolved Git executable is not a file: {executable}")
        return r[Path].ok(executable)

    @staticmethod
    def _run_git(
        executable: Path, cwd: Path, arguments: t.StrSequence
    ) -> p.Result[p.Cli.CommandOutput]:
        result = u.Cli.run_raw(
            (str(executable), *arguments),
            cwd=cwd,
            timeout=c.Infra.TIMEOUT_LONG,
            env={
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            },
            remove_env_keys=c.Infra.MANAGED_GIT_TOOL_GIT_ENV_KEYS,
        )
        if result.failure:
            return r[p.Cli.CommandOutput].fail(result.error or "Git execution failed")
        if result.value.exit_code != 0:
            detail = (result.value.stderr or result.value.stdout).strip()
            return r[p.Cli.CommandOutput].fail(
                detail or f"Git exited {result.value.exit_code}"
            )
        return r[p.Cli.CommandOutput].ok(result.value)


__all__: list[str] = ["FlextInfraManagedGitToolContractMixin"]
