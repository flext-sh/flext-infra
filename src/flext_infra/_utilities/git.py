"""Public Git utilities facet for ``u.Infra`` (composed into utilities MRO).

Private GitPython parts live under ``_utilities/_git/``. Consumers use
``from flext_infra import u`` only — never import this module or ``_git``.
"""

from __future__ import annotations

from flext_infra._utilities._git.scope import FlextInfraUtilitiesGitScopeMixin
from flext_infra._utilities._git.semantic import (
    FlextInfraUtilitiesGitSemanticMixin,
from flext_infra._utilities._git.semantic_submodule import (
    FlextInfraUtilitiesGitSemanticSubmoduleMixin,
)


class FlextInfraUtilitiesGit(
    FlextInfraUtilitiesGitScopeMixin, FlextInfraUtilitiesGitSemanticMixin
):
    """Canonical Git owner for flext-infra: scope + worktree + checkpoint/patch.

    Why (hq-36xk): the semantic composition lives in
    FlextInfraUtilitiesGitSemanticMixin (scope + semantic chain: identity,
    submodule, index, paths, publish, worktree, refs). The facade inherits BOTH
    the scope mixin and the semantic composite so that every semantic_* method is
    visible as u.Infra.<name>. Before this lane the facade inherited only
    WorktreeMixin, so git_submodule_init / git_staged_gitlink_oid /
    git_submodule_sections / git_submodule_config_value / git_identity were
    unreachable at runtime -- root cause of the 4 missing-attribute errors
    downstream. One-line inheritance restoration; no behavior change for the
    methods, they simply become visible again.
    """


__all__: list[str] = ["FlextInfraUtilitiesGit"]
