"""Make-related constants for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

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
    PROJECT_VARIABLE_DEFAULTS: Final[t.Infra.StrPairSequence] = (
        ("PYTEST_ARGS", ""),
        ("DIAG", "0"),
        ("CHECK_GATES", ""),
        ("VALIDATE_GATES", ""),
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
    WORKSPACE_VARIABLE_DEFAULTS: Final[t.Infra.StrPairSequence] = (
        ("PROJECT", ""),
        ("PROJECTS", ""),
        ("PYTEST_ARGS", ""),
        ("VALIDATE_SCOPE", "project"),
        ("DOCS_PHASE", "all"),
        ("FAIL_FAST", ""),
        ("JOBS", ""),
        ("CHECK_GATES", ""),
        ("VALIDATE_GATES", ""),
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
    PROJECT_CORE_VERBS: Final[t.Infra.StrPairSequence] = (
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
    PROJECT_DAEMON_VERBS: Final[t.Infra.StrPairSequence] = (
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
    WORKSPACE_CORE_VERBS: Final[t.Infra.StrPairSequence] = (
        (
            "boot",
            "Install all projects into workspace .venv, then run val VALIDATE_SCOPE=workspace",
        ),
        (
            "up",
            "Upgrade deps + modernize + dependency report (.reports/dependencies/)",
        ),
        ("mod", "Modernize pyproject.toml configs only (no lock/install)"),
        ("build", "Build/package all selected projects"),
        ("check", "Run the lint gates in all projects"),
        ("scan", "Run all security checks in all projects"),
        ("fmt", "Run all formatting in all projects"),
        ("docs", "Build docs in all projects"),
        ("test", "Run tests only in all projects"),
        (
            "val",
            "Run validate gates (FIX=1 auto-fix, VALIDATE_SCOPE=workspace for repo-level)",
        ),
        ("rel", "Interactive workspace release orchestration"),
        ("pr", "Manage PRs for selected projects"),
        ("types", "Stub supply-chain + typing report (PROJECT/PROJECTS to scope)"),
        ("pyre", "Run authoritative repo-wide pyrefly report"),
        ("stubs", "Validate typing stub supply-chain (repo-wide)"),
        ("pol", "Enforce no Any/t.JsonValue/type: ignore (repo-wide)"),
        (
            "cqrs",
            "Enforce strict CQRS/FlextModels patterns across ecosystem",
        ),
        ("clean", "Clean all projects"),
    )
    WORKSPACE_GIT_VERBS: Final[t.Infra.StrPairSequence] = (
        (
            "save",
            "Commit all changes in selected projects (MESSAGE=)",
        ),
        ("tag", "Create git tags for selected projects (TAG=, DRY_RUN=1)"),
        ("push", "Push branches and tags for selected projects"),
        (
            "gen",
            "Recreate standardized pyproject.toml, base.mk, Makefile and __init__.py",
        ),
    )
    WORKSPACE_SELECTOR_LINES: Final[t.StrSequence] = (
        "PROJECT=<name>             Single project",
        'PROJECTS="proj-a proj-b"        Multi-project',
        "FAIL_FAST=1               Stop on first project failure",
        "FIX=1                     Auto-fix (validate + check)",
        'PYTEST_ARGS="-k expr -x"        Extra pytest args for test',
        "CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,go,type  Select check gates (default: all)",
        "VALIDATE_GATES=complexity,docstring   Select validate gates (default: all)",
        "FILE=src/foo.py             Single file for check/test/format",
        'FILES="a.py b.py"           Multiple files for check/test/format',
        "CHANGED_ONLY=1             check only git-modified .py files",
        "MATCH=test_name            Filter tests by name (pytest -k)",
        "VERBOSE=1                  Verbose test output (-vv -s)",
        'RUFF_ARGS="--select E501"    Extra ruff args for check',
        'PYRIGHT_ARGS="--level basic"  Extra pyright args for check',
        "CHECK_ONLY=1               Dry-run format/check (no writes)",
        "VALIDATE_SCOPE=project|workspace     Validate scope (default: project)",
        "DOCS_PHASE=all|generate|fix|audit|build|validate",
        "RELEASE_PHASE=validate,version,build,publish|all",
        "INTERACTIVE=1|0            Release prompt mode",
        "DRY_RUN=1                  Print plan, do not tag/push",
        "PUSH=1                     Push release commit/tag",
        "VERSION=<semver> TAG=v<semver> BUMP=patch Release controls",
        "RELEASE_DEV_SUFFIX=0|1     Append -dev during release version phase",
        "RELEASE_NEXT_DEV=0|1       After release, auto-bump to next <RELEASE_NEXT_BUMP>-dev",
        "RELEASE_NEXT_BUMP=major|minor|patch   Next dev bump strategy (default: minor)",
        "CREATE_BRANCHES=1|0        Create release branches in workspace + projects",
        "PR_ACTION=status|create|view|checks|merge|close",
        "PR_BASE=main PR_HEAD=<branch> PR_NUMBER=<id> PR_DRAFT=0|1",
        "PR_TITLE='title' PR_BODY='body' PR_MERGE_METHOD=squash|merge|rebase",
        "PR_AUTO=0|1 PR_DELETE_BRANCH=0|1",
        "PR_CHECKS_STRICT=0|1       checks action strict failure toggle",
        "PR_RELEASE_ON_MERGE=0|1    merge action: dispatch release workflow",
        "PR_INCLUDE_ROOT=0|1        include root repo in workspace PR automation",
        "PR_BRANCH=<name> PR_CHECKPOINT=0|1   normalize branch + checkpoint before action",
        "DEPS_REPORT=0              Skip dependency report after upgrade/typings",
        "MESSAGE='chore: ...'       Commit message for save verb",
    )
    WORKSPACE_EXAMPLES: Final[t.StrSequence] = (
        "make check PROJECT=flext-core",
        "make check PROJECT=flext-core FILE=src/flext_core/foo.py CHECK_GATES=pyright",
        "make check PROJECT=flext-core CHANGED_ONLY=1",
        "make check CHECK_GATES=lint FIX=1 CHANGED_ONLY=1",
        "make test PROJECT=flext-core MATCH=test_container FAIL_FAST=1",
        "make test PROJECT=flext-core FILE=tests/unit/test_foo.py",
        "make fmt FILE=src/flext_core/foo.py CHECK_ONLY=1",
        'make check PROJECT=flext-core CHECK_GATES=lint RUFF_ARGS="--select E501"',
        "make build",
        "make types PROJECT=flext-api",
        "make pyre",
        "make stubs",
        "make check CHECK_GATES=lint,type",
        'make val PROJECTS="flext-core flext-api" FIX=1',
        'make test PROJECT=flext-api PYTEST_ARGS="-k unit" FAIL_FAST=1',
        "make val VALIDATE_SCOPE=workspace",
        "make rel BUMP=minor",
        "make save MESSAGE='chore: upgrade deps'",
        "make tag",
        "make tag TAG=v1.0.0",
        "make push",
        "make gen PROJECT=flext-core",
        "make pr PROJECT=flext-core PR_ACTION=status",
        "make pr PROJECT=flext-core PR_ACTION=create PR_TITLE='release: 0.11.0-dev'",
    )
    STANDALONE_BOOTSTRAP_VERBS: Final[t.Infra.StrPairSequence] = (
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
    CHECK_FORWARD_ARGS: Final[t.Infra.StrPairSequence] = (
        ("CHECK_GATES", FORWARD_MODE_VALUE),
        ("FILE", FORWARD_MODE_VALUE),
        ("FILES", FORWARD_MODE_VALUE),
        ("CHANGED_ONLY", FORWARD_MODE_ENABLED),
        ("FIX", FORWARD_MODE_ENABLED),
        ("RUFF_ARGS", FORWARD_MODE_VALUE),
        ("PYRIGHT_ARGS", FORWARD_MODE_VALUE),
        ("CHECK_ONLY", FORWARD_MODE_ENABLED),
    )
    DOCS_FORWARD_ARGS: Final[t.Infra.StrPairSequence] = (
        ("DOCS_PHASE", FORWARD_MODE_VALUE),
        ("FIX", FORWARD_MODE_ENABLED),
    )
    TEST_FORWARD_ARGS: Final[t.Infra.StrPairSequence] = (
        ("PYTEST_ARGS", FORWARD_MODE_VALUE),
        ("FILE", FORWARD_MODE_VALUE),
        ("FILES", FORWARD_MODE_VALUE),
        ("MATCH", FORWARD_MODE_VALUE),
        ("VERBOSE", FORWARD_MODE_ENABLED),
    )
    VALIDATE_FORWARD_ARGS: Final[t.Infra.StrPairSequence] = (
        ("FIX", FORWARD_MODE_ENABLED),
        ("VALIDATE_GATES", FORWARD_MODE_VALUE),
    )


__all__: list[str] = ["FlextInfraConstantsMake"]
