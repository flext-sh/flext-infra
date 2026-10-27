"""Generic file pattern matching iteration utility facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
import os
import re
from typing import TYPE_CHECKING

from flext_infra._utilities import FlextInfraUtilitiesProjectManagedArtifacts
from flext_infra._utilities._git import FlextInfraUtilitiesGitScopeMixin

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraUtilitiesIterationMatching(FlextInfraUtilitiesGitScopeMixin):
    """Static helpers for matching files by include/exclude glob patterns."""

    @classmethod
    def iter_matching_files(
        cls,
        root: Path,
        *,
        includes: t.StrSequence,
        excludes: t.StrSequence = (),
    ) -> t.SequenceOf[Path]:
        """Return files in one scope through the canonical git-aware selection path.

        The scope's tracked inventory is read from Git; outside Git every
        file under the scope is a candidate.

        Returns:
            Files in one scope through the canonical git-aware selection path.

        """
        if not root.is_dir():
            return []
        root = root.resolve()
        return cls._select_matching(
            root,
            cls._git_tracked_scope_relative_paths(str(root)),
            includes,
            excludes,
        )

    @classmethod
    def scope_matching_files(
        cls,
        root: Path,
        includes: t.StrSequence,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> t.SequenceOf[Path]:
        """Return included files in one scope from an invocation's shared facts.

        Without injected facts the scope's tracked inventory is read from Git.

        Returns:
            The included files, selected from the tracked inventory.

        """
        if scope_facts is None:
            return cls.iter_matching_files(root, includes=includes)
        if not root.is_dir():
            return []
        root = root.resolve()
        return cls._select_matching(
            root,
            scope_facts.tracked_scope_relative_paths(root),
            includes,
            (),
        )

    @staticmethod
    def scope_excluded_paths(
        root: Path,
        paths: t.SequenceOf[Path],
        patterns: t.StrSequence,
    ) -> t.SequenceOf[Path]:
        """Apply the declared positive glob view through native path matching.

        Git inventory owns tracking and ignore semantics; these derived globs
        describe analysis eligibility, not another interpretation of .gitignore.

        Returns:
            Eligible paths, retaining the original path objects and order.

        """
        return tuple(
            path
            for path in paths
            if not any(
                path.relative_to(root).full_match(pattern) for pattern in patterns
            )
        )

    @classmethod
    def governed_scope_files(
        cls,
        root: Path,
        includes: t.StrSequence,
        scope_facts: p.Infra.GitScopeFacts | None,
    ) -> t.SequenceOf[Path]:
        """Return the included governed files of one scope.

        The native tracked inventory preserves tracked ignored source. Analysis
        exclusions use the same effective repository policy as tool projections.

        Returns:
            The governed files, in the matched order.

        """
        root = root.resolve()
        inputs = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            root
        ).unwrap()
        return cls.scope_excluded_paths(
            root,
            cls.scope_matching_files(root, includes, scope_facts),
            inputs.spec.analyzer_exclude_globs,
        )

    @staticmethod
    def _select_matching(
        root: Path,
        tracked: t.StrSequence | None,
        includes: t.StrSequence,
        excludes: t.StrSequence,
    ) -> t.SequenceOf[Path]:
        """Match each scope-relative candidate once; stat only matched paths.

        Returns:
            The matched files under ``root``, sorted.

        """
        candidates: t.StrSequence = (
            tracked
            if tracked is not None
            else tuple(
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            )
        )
        # fnmatch.fnmatch semantics (normcase plus translate), compiled once.
        included = tuple(
            re.compile(fnmatch.translate(os.path.normcase(pattern))).match
            for pattern in includes
        )
        excluded = tuple(
            re.compile(fnmatch.translate(os.path.normcase(pattern))).match
            for pattern in excludes
        )
        return sorted({
            root / relative
            for relative in candidates
            for name in (os.path.normcase(relative),)
            if (not included or any(match(name) for match in included))
            and not any(match(name) for match in excluded)
            and (root / relative).is_file()
        })


__all__: list[str] = ["FlextInfraUtilitiesIterationMatching"]
