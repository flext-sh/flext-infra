"""Pure Git direct-source parsing shared by repository and dependency owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from urllib.parse import urlparse

from flext_infra import c, p, r


class FlextInfraUtilitiesGitRequirementSource:
    """Parse declared Git requirement sources without guessing their policy."""

    @staticmethod
    def _canonical_https_url(url: str) -> p.Result[str]:
        """Canonicalize one Git remote URL to its HTTPS form, fail loud.

        Returns:
            The resulting ``p.Result[str]``.

        """
        if url.startswith("https://"):
            candidate = url
        elif url.startswith("http://"):
            candidate = f"https://{url.removeprefix('http://')}"
        elif url.startswith("ssh://"):
            candidate = f"https://{url.removeprefix('ssh://').removeprefix('git@')}"
        elif url.startswith("git@") and ":" in url:
            host, _, path = url.removeprefix("git@").partition(":")
            candidate = f"https://{host}/{path}"
        else:
            return r[str].fail(f"git remote url is not canonicalizable to HTTPS: {url}")
        # A URL without a host (``https:///repo``) or without a repository
        # path (``https://host``) carries no origin identity: reject it as a
        # declared remote rather than letting a generated source point at it.
        parsed = urlparse(candidate)
        if not parsed.netloc or not parsed.path.strip("/"):
            return r[str].fail(
                f"git remote url must name a host and repository path: {url}",
            )
        return r[str].ok(candidate)

    @staticmethod
    def ref_is_commit(ref: str) -> bool:
        """Whether one Git ref names a commit rather than an integration line.

        uv.lock, written only by ``make upg``, owns every resolved commit. In a
        generated pyproject a commit ref is projection residue that generation
        re-renders on the family line; in a hand-authored source it is a pin
        beside the lock and fails loudly.

        Returns:
            The resulting ``bool``.

        """
        return c.Infra.GIT_COMMIT_OID_RE.fullmatch(ref) is not None

    @staticmethod
    def declared_git_source(requirement: str) -> p.Result[tuple[str, str]]:
        """Parse one requirement's declared direct Git source.

        Returns ``(canonical_url, ref)`` for a requirement that declares
        ``name @ git+URL@REF``, or the empty pair when the requirement declares
        no direct source at all. The declared line is the only authority for the
        dependency's canonical URL and branch: canonicalization normalizes the
        transport scheme (``ssh://``, SCP-style, ``http``) to ``https`` and
        never invents an organization, host, or ref. A declared source that is
        not a Git URL, or a Git URL without a ref, fails loudly. Whether a
        commit ref is projection residue or a hand-authored pin is the
        caller's decision (``ref_is_commit``).

        Returns:
            The resulting ``p.Result[tuple[str, str]]``.

        """
        requirement_part, _, _ = requirement.partition(";")
        head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(requirement_part.strip())
        if head_match is None:
            return r[tuple[str, str]].fail(f"invalid requirement head: {requirement}")
        _, at_separator, source = requirement_part.partition("@")
        if not at_separator:
            # Plain workspace requirement: no direct git source is declared.
            # Success payloads are never None (flext-core result law), so the
            # caller reads the empty pair as "no declared source".
            return r[tuple[str, str]].ok(("", ""))
        source = source.strip()
        if not source.startswith(c.Infra.GIT_URL_SCHEME_PREFIX):
            return r[tuple[str, str]].fail(
                f"internal dependency direct source must be a git URL: {requirement}",
            )
        url, ref_separator, ref = source.rpartition("@")
        url = url.removeprefix(c.Infra.GIT_URL_SCHEME_PREFIX).strip()
        ref = ref.strip()
        if not ref_separator or not ref:
            return r[tuple[str, str]].fail(
                f"internal dependency git source must declare a branch or ref: "
                f"{requirement}",
            )
        canonical = FlextInfraUtilitiesGitRequirementSource._canonical_https_url(url)
        if canonical.failure:
            return r[tuple[str, str]].from_failure(canonical)
        return r[tuple[str, str]].ok((canonical.value, ref))


__all__: list[str] = ["FlextInfraUtilitiesGitRequirementSource"]
