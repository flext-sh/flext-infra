"""Make-related constants for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsMake:
    """Make-related constants for Makefile generation and CLI routing."""

    VERB_CHECK: Final[str] = "check"
    VERB_VALIDATE: Final[str] = "validate"
    VERB_PUBLISH: Final[str] = "publish"
    VERB_RUN: Final[str] = "run"
    VERB_CHECKS: Final[str] = "checks"

    # --- Canonical make contract constants (was: class Make) ---

    CLI_GROUP_BASEMK: Final[str] = "basemk"
    CLI_GROUP_CHECK: Final[str] = "check"
    CLI_GROUP_CODEGEN: Final[str] = "codegen"
    CLI_GROUP_DEPS: Final[str] = "deps"
    CLI_GROUP_DOCS: Final[str] = "docs"
    CLI_GROUP_GITHUB: Final[str] = "github"
    CLI_GROUP_MAINTENANCE: Final[str] = "maintenance"
    CLI_GROUP_REFACTOR: Final[str] = "refactor"
    CLI_GROUP_RELEASE: Final[str] = "release"
    CLI_ROUTE_RELEASE: Final[str] = "release run"
    CLI_GROUP_VALIDATE: Final[str] = "validate"
    CLI_ROUTE_MAINTENANCE: Final[str] = "maintenance run"
    CLI_GROUP_WORKSPACE: Final[str] = "workspace"
    PROJECT_CHECK_GATES_ALLOWED: Final[str] = (
        "lint,format,pyrefly,mypy,pyright,security,markdown,go,type"
    )
    PROJECT_CHECK_GATES_DEFAULT: Final[str] = (
        "lint,format,pyrefly,mypy,pyright,security,markdown,go"
    )
    GO_PROJECT_CHECK_GATES_DEFAULT: Final[str] = "lint,format,security,markdown,go"
    PROJECT_FAST_PATH_CHECK_GATES: Final[str] = "lint,format,pyrefly,mypy,pyright"
    PROJECT_VALIDATE_GATES_ALLOWED: Final[str] = "complexity,docstring"
    DOCS_PHASES_ALLOWED: Final[str] = "all|generate|fix|audit|build|validate"
    RELEASE_PHASES_ALLOWED: Final[str] = "validate,version,build,publish|all"
    PR_ACTIONS_ALLOWED: Final[str] = "status|create|view|checks|merge|close"
    PR_MERGE_METHODS_ALLOWED: Final[str] = "squash|merge|rebase"
    ORCHESTRATED_PROJECT_VERBS: Final[t.StrSequence] = (
        "boot",
        "build",
        "check",
        "clean",
        "docs",
        "scan",
        "test",
        "val",
    )
    PROJECT_VARIABLE_DEFAULTS: Final[t.StrPairSequence] = (
        ("PYTEST_ARGS", ""),
        ("DIAG", "0"),
        ("CHECK_GATES", ""),
        ("VALIDATE_GATES", ""),
        ("SCOPE", "project"),
        ("NAMESPACE", ""),
        ("GATES", ""),
        ("PROPAGATE", ""),
        ("DOCS_PHASE", "all"),
        ("FIX", ""),
        ("PR_ACTION", "status"),
        ("PR_BASE", "main"),
        ("PR_HEAD", ""),
        ("PR_NUMBER", ""),
        ("PR_TITLE", ""),
        ("PR_BODY", ""),
        ("PR_DRAFT", "0"),
        ("PR_MERGE_METHOD", "squash"),
        ("PR_AUTO", "0"),
        ("PR_DELETE_BRANCH", "0"),
        ("PR_CHECKS_STRICT", "0"),
        ("PR_RELEASE_ON_MERGE", "1"),
        ("FILE", ""),
        ("FILES", ""),
        ("CHANGED_ONLY", ""),
        ("MATCH", ""),
        ("RUFF_ARGS", ""),
        ("PYRIGHT_ARGS", ""),
        ("CHECK_ONLY", ""),
        ("FAIL_FAST", ""),
        ("VERBOSE", ""),
    )
    WORKSPACE_VARIABLE_DEFAULTS: Final[t.StrPairSequence] = (
        ("PROJECT", ""),
        ("PROJECTS", ""),
        ("WHAT", ""),
        ("PYTEST_ARGS", ""),
        ("VALIDATE_SCOPE", "project"),
        ("DOCS_PHASE", "all"),
        ("FAIL_FAST", ""),
        ("JOBS", ""),
        ("CHECK_GATES", ""),
        ("VALIDATE_GATES", ""),
        ("SCOPE", "project"),
        ("NAMESPACE", ""),
        ("GATES", ""),
        ("PROPAGATE", ""),
        ("FIX", ""),
        ("FILE", ""),
        ("FILES", ""),
        ("CHANGED_ONLY", ""),
        ("MATCH", ""),
        ("RUFF_ARGS", ""),
        ("PYRIGHT_ARGS", ""),
        ("CHECK_ONLY", ""),
        ("RELEASE_PHASE", "all"),
        ("INTERACTIVE", "1"),
        ("DRY_RUN", ""),
        ("PUSH", ""),
        ("VERSION", ""),
        ("MESSAGE", ""),
        ("TAG", ""),
        ("BUMP", ""),
        ("RELEASE_DEV_SUFFIX", "0"),
        ("RELEASE_NEXT_DEV", "0"),
        ("RELEASE_NEXT_BUMP", "minor"),
        ("CREATE_BRANCHES", "1"),
        ("PR_ACTION", "status"),
        ("PR_BASE", "main"),
        ("PR_HEAD", ""),
        ("PR_NUMBER", ""),
        ("PR_TITLE", ""),
        ("PR_BODY", ""),
        ("PR_DRAFT", "0"),
        ("PR_MERGE_METHOD", "squash"),
        ("PR_AUTO", "0"),
        ("PR_DELETE_BRANCH", "0"),
        ("PR_CHECKS_STRICT", "0"),
        ("PR_RELEASE_ON_MERGE", "1"),
        ("PR_INCLUDE_ROOT", "1"),
        ("PR_CHECKPOINT", "1"),
        ("DEPS_REPORT", "1"),
        ("VERBOSE", ""),
    )
    PROJECT_CORE_VERBS: Final[t.StrPairSequence] = (
        ("boot", "Install dependencies and hooks"),
        ("build", "Build distributable artifacts"),
        ("check", "Run lint gates (CHECK_GATES= to select)"),
        ("scan", "Run all security checks"),
        ("fmt", "Run all formatting"),
        ("docs", "Build docs (DOCS_PHASE= to select)"),
        ("test", "Run pytest (PYTEST_ARGS= for options)"),
        ("val", "Run validate gates (FIX=1 to auto-fix)"),
        ("clean", "Clean build/test/type artifacts"),
    )
    PROJECT_DAEMON_VERBS: Final[t.StrPairSequence] = (
        ("daemon-start", "Start all daemons (mypy + pyright)"),
        ("daemon-stop", "Stop all daemons"),
        ("daemon-status", "Show status of all daemons"),
        ("daemon-restart", "Restart all daemons"),
    )
    PROJECT_OPTION_LINES: Final[t.StrSequence] = (
        "CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,go,type",
        "VALIDATE_GATES=complexity,docstring",
        "FILE=src/foo.py             Single file for check/fmt/test",
        'FILES="a.py b.py"          Multiple files for check/fmt/test',
        "CHANGED_ONLY=1              Git-changed Python files for check",
        "CHECK_ONLY=1                Dry-run format/check (no writes)",
        'RUFF_ARGS="--select E501"   Extra args for ruff check',
        'PYRIGHT_ARGS="--level basic" Extra args for pyright',
        'PYTEST_ARGS="-k expr"       Extra pytest args',
        "MATCH=test_name             Alias for pytest -k",
        "FAIL_FAST=1                 Add -x to pytest",
        "DIAG=1                      Emit extended pytest diagnostics",
        "DOCS_PHASE=all|generate|fix|audit|build|validate",
        "FIX=1                       Auto-fix supported gates",
        "VERBOSE=1                   Show executed commands",
    )
    PROJECT_PR_OPTION_LINES: Final[t.StrSequence] = (
        "PR_ACTION=status|create|view|checks|merge|close",
        "PR_BASE=main  PR_HEAD=<branch>  PR_NUMBER=<id>",
        "PR_TITLE='...'  PR_BODY='...'  PR_DRAFT=0|1",
        "PR_MERGE_METHOD=squash|merge|rebase  PR_AUTO=0|1",
        "PR_DELETE_BRANCH=0|1  PR_CHECKS_STRICT=0|1",
        "PR_RELEASE_ON_MERGE=0|1",
    )
    WORKSPACE_CORE_VERBS: Final[t.StrPairSequence] = (
        ("boot", "Bootstrap .venv + submodules (WHAT=venv|submodules|sync|stat|imp)"),
        ("build", "Build/regen (WHAT=gen|mod|up|constraints|sync|docs|stubs)"),
        ("check", "Quality gates (WHAT=lint|format|pol|pyre|scan|loc-cap|boundary)"),
        ("test", "Run tests (WHAT=unit|integration|diag)"),
        ("val", "Validation gates (WHAT=loc-cap|loc-delta|boundary|manual-cmd)"),
        ("ship", "Release workflow (WHAT=save|tag|push|pr|rel; APPLY=Y)"),
        ("clean", "Clean build/test/type artifacts"),
        ("help", "Show workspace verbs"),
    )
    WORKSPACE_GIT_VERBS: Final[t.StrPairSequence] = ()
    # SSOT: verb -> phase -> make target. Template derives the case arms; nothing
    # else hardcodes phase names. WHAT_PHASES (below) derives its sets from this.
    WHAT_DISPATCH: Final[t.MappingKV[str, t.MappingKV[str, str]]] = MappingProxyType({
        "boot": MappingProxyType({
            "": "_boot_default",
            "venv": "_boot_default",
            "submodules": "_boot_default",
            "sync": "_sync",
            "stat": "_stat",
            "imp": "_imp",
        }),
        "build": MappingProxyType({
            "": "_build_default",
            "gen": "_gen",
            "mod": "_mod",
            "up": "_up",
            "constraints": "_constraints",
            "sync": "_sync",
            "docs": "_docs",
            "stubs": "_stubs",
        }),
        "check": MappingProxyType({
            "": "_check_default",
            "scan": "_scan",
            "fmt": "_fmt",
            "format": "_fmt",
            "types": "_types",
            "pyre": "_pyre",
            "pol": "_pol",
            "cqrs": "_cqrs",
            **{
                gate: f'_check_default CHECK_GATES="{gate}"'
                for gate in (
                    "lint",
                    "pyrefly",
                    "mypy",
                    "pyright",
                    "markdown",
                    "go",
                    "silent-failure",
                    "loc-cap",
                    "boundary",
                )
            },
        }),
        "ship": MappingProxyType({
            "save": "_save",
            "tag": "_tag",
            "push": "_push",
            "pr": "_pr",
            "rel": "_rel",
        }),
    })
    # Phase-set per verb (CLI resolve_what); make verbs derived from WHAT_DISPATCH.
    WHAT_PHASES: Final[t.MappingKV[str, frozenset[str]]] = MappingProxyType({
        **{
            verb: frozenset(phase for phase in targets if phase)
            for verb, targets in WHAT_DISPATCH.items()
        },
        "test": frozenset({"unit", "integration", "diag"}),
        "val": frozenset({
            "loc-cap",
            "loc-delta",
            "boundary",
            "manual-cmd",
            "complexity",
            "docstring",
            "silent-failure",
        }),
    })
    WORKSPACE_SELECTOR_LINES: Final[t.StrSequence] = (
        'PROJECT=<name> / PROJECTS="a b"    Scope to project(s)',
        "WHAT=<phase>               Sub-phase for build/check/test/val/ship/boot",
        "FIX=1                      Auto-fix (check/val)",
        'FILE=src/x.py / FILES="a b"        Scope to file(s)',
        "CHANGED_ONLY=1             Only git-modified files",
        "MATCH=expr                 pytest -k filter (test)",
        "FAIL_FAST=1                Stop on first failure",
        "APPLY=Y                    Allow mutation (ship)",
        "VERBOSE=1                  Show executed commands",
    )
    WORKSPACE_EXAMPLES: Final[t.StrSequence] = (
        "make check PROJECT=flext-core",
        "make check WHAT=lint FIX=1 CHANGED_ONLY=1",
        "make check WHAT=loc-cap",
        "make build WHAT=mod PROJECT=flext-core",
        "make test PROJECT=flext-core MATCH=test_x FAIL_FAST=1",
        "make val WHAT=loc-delta",
        'make ship WHAT=save MESSAGE="chore: ..." APPLY=Y',
        "make boot",
    )
    STANDALONE_BOOTSTRAP_VERBS: Final[t.StrPairSequence] = (
        ("venv", "Create virtual environment"),
        ("setup", "Full standalone setup"),
        ("help", "Show this help"),
    )
    STANDALONE_POST_SETUP_VERBS: Final[str] = (
        "check, test, fmt, build, val, clean, docs, pr"
    )
    PROJECT_SELECTION_CONFLICT_ERROR: Final[str] = (
        "ERROR: Cannot use PROJECT and PROJECTS together"
    )
    PROJECT_SELECTION_CONFLICT_HINT: Final[str] = (
        'Use PROJECT=<name> or PROJECTS="proj-a proj-b"'
    )
    PROJECT_SELECTION_EMPTY_ERROR: Final[str] = "ERROR: no projects selected"
    PROJECT_SELECTION_EMPTY_HINT: Final[str] = (
        'Use PROJECT=<name> or PROJECTS="proj-a proj-b"'
    )
    WORKSPACE_BOOT_HINT: Final[str] = "make boot"
    STANDALONE_BOOT_HINT: Final[str] = "make setup"
    SAVE_USAGE: Final[str] = "make save MESSAGE='chore: your message'"
    FORWARD_MODE_VALUE: Final[str] = "value"
    FORWARD_MODE_ENABLED: Final[str] = "enabled"
    CHECK_FORWARD_ARGS: Final[t.StrPairSequence] = (
        ("CHECK_GATES", FORWARD_MODE_VALUE),
        ("FILE", FORWARD_MODE_VALUE),
        ("FILES", FORWARD_MODE_VALUE),
        ("CHANGED_ONLY", FORWARD_MODE_ENABLED),
        ("FIX", FORWARD_MODE_ENABLED),
        ("RUFF_ARGS", FORWARD_MODE_VALUE),
        ("PYRIGHT_ARGS", FORWARD_MODE_VALUE),
        ("CHECK_ONLY", FORWARD_MODE_ENABLED),
    )
    DOCS_FORWARD_ARGS: Final[t.StrPairSequence] = (
        ("DOCS_PHASE", FORWARD_MODE_VALUE),
        ("FIX", FORWARD_MODE_ENABLED),
    )
    TEST_FORWARD_ARGS: Final[t.StrPairSequence] = (
        ("PYTEST_ARGS", FORWARD_MODE_VALUE),
        ("FILE", FORWARD_MODE_VALUE),
        ("FILES", FORWARD_MODE_VALUE),
        ("MATCH", FORWARD_MODE_VALUE),
        ("VERBOSE", FORWARD_MODE_ENABLED),
    )
    VALIDATE_FORWARD_ARGS: Final[t.StrPairSequence] = (
        ("FIX", FORWARD_MODE_ENABLED),
        ("VALIDATE_GATES", FORWARD_MODE_VALUE),
    )


__all__: list[str] = ["FlextInfraConstantsMake"]
