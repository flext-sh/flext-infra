# =============================================================================
# FLEXT BASE MAKEFILE - Shared patterns for all FLEXT projects
# =============================================================================
# Usage: Set PROJECT_NAME before including: include ../base.mk
# Silent by default. Use VERBOSE=1 for detailed output.
# =============================================================================

# === CONFIGURATION (override before include) ===
PROJECT_NAME ?= flext-infra
PYTHON_VERSION ?= 3.13
SRC_DIR ?= src
TESTS_DIR ?= tests
DOCSTRING_MIN ?= 80
COMPLEXITY_MAX ?= 10
PYTEST_ARGS ?=
PYTEST_TARGETS ?= tests
DIAG ?= 0
CHECK_GATES ?=
VALIDATE_GATES ?=
SCOPE ?= project
NAMESPACE ?=
GATES ?=
PROPAGATE ?=
DOCS_PHASE ?= all
FIX ?=
PR_ACTION ?= status
PR_BASE ?=
PR_HEAD ?=
PR_TITLE ?=
PR_BODY ?=
PR_DRAFT ?= 0
FILE ?=
FILES ?=
CHANGED_ONLY ?=
MATCH ?=
RUFF_ARGS ?=
PYRIGHT_ARGS ?=
CHECK_ONLY ?=
FAIL_FAST ?=
VERBOSE ?=


PYTEST_REPORT_ARGS := -ra --durations=25 --durations-min=0.001 --tb=short
PYTEST_DIAG_ARGS := -rA --durations=0 --tb=long --showlocals
PYTEST_REPORTS_DIR ?= .reports/tests
TEST_ITEM_TIMEOUT_SECONDS ?= 10
TEST_SESSION_TIMEOUT_SECONDS ?= 60
TEST_SHARD_COUNT ?= 16
TEST_SHARD_PARALLELISM ?= 2

# === WORKSPACE/STANDALONE DETECTION ===
BASE_MK_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
PROJECT_ROOT := $(CURDIR)
CALLER_PATH := $(PATH)
CALLER_VIRTUAL_ENV := $(patsubst %/,%,$(VIRTUAL_ENV))

ifeq ($(FLEXT_STANDALONE),1)
FLEXT_MODE := standalone
else
# Caller may already know the workspace root (e.g., when including flext-infra/base.mk).
ifdef FLEXT_WORKSPACE_ROOT
FLEXT_MODE := workspace
else
# Pure Make detection: if base.mk lives in a parent dir, we are inside a workspace.
# No Python dependency — shell/Make only until venv is ready.
ifneq ($(BASE_MK_DIR),$(PROJECT_ROOT))
FLEXT_MODE := workspace
else
FLEXT_MODE := standalone
endif
endif
endif

ifeq ($(FLEXT_MODE),workspace)
# Prefer the caller-provided workspace root; fall back to the directory holding base.mk.
WORKSPACE_ROOT := $(FLEXT_WORKSPACE_ROOT)
ifndef WORKSPACE_ROOT
WORKSPACE_ROOT := $(BASE_MK_DIR)
endif
WORKSPACE_VENV := $(WORKSPACE_ROOT)/.venv
ACTIVE_VENV := $(WORKSPACE_VENV)
else
WORKSPACE_ROOT := $(PROJECT_ROOT)
ACTIVE_VENV := $(PROJECT_ROOT)/.venv
endif

# The shared workspace environment is reusable, but uv must parse the active
# lane's own project metadata.  Resolving dependencies against WORKSPACE_ROOT
# would silently redirect a worktree command to the primary checkout.
override UV_PROJECT := $(PROJECT_ROOT)
override UV_PROJECT_ENVIRONMENT := $(ACTIVE_VENV)
override VIRTUAL_ENV := $(ACTIVE_VENV)
MISE := $(shell command -v mise 2>/dev/null)
SANITIZED_CALLER_PATH := $(CALLER_PATH)
ifneq ($(strip $(CALLER_VIRTUAL_ENV)),)
SANITIZED_CALLER_PATH := $(subst $(CALLER_VIRTUAL_ENV)/bin:,,$(SANITIZED_CALLER_PATH))
SANITIZED_CALLER_PATH := $(subst :$(CALLER_VIRTUAL_ENV)/bin,,$(SANITIZED_CALLER_PATH))
ifeq ($(SANITIZED_CALLER_PATH),$(CALLER_VIRTUAL_ENV)/bin)
SANITIZED_CALLER_PATH :=
endif
endif
override PATH := $(ACTIVE_VENV)/bin:$(SANITIZED_CALLER_PATH)
export UV_PROJECT UV_PROJECT_ENVIRONMENT VIRTUAL_ENV PATH

export PYTHON_KEYRING_BACKEND := keyring.backends.null.Keyring

VENV_PYTHON := $(ACTIVE_VENV)/bin/python
UV ?= uv
FLEXT_INFRA_PYTHON ?= $(VENV_PYTHON)
export FLEXT_INFRA_PYTHON

DMPY_SOCKET := .dmypy/socket.$(PROJECT_NAME)
PYRIGHT_PIDFILE := .pyright/daemon.pid
PYRIGHT_LOG := .pyright/daemon.log

# Export for subprocesses
export PROJECT_NAME PYTHON_VERSION
export FLEXT_ROOT := $(WORKSPACE_ROOT)

# === MYPY RESOURCE LIMIT ===
# mro-0ftd.3.11: every Mypy process inherits validated memory and time caps.
MYPY_MEMORY_LIMIT_MB ?= 6144
MYPY_TIMEOUT_SECONDS ?= 600
MYPY_BOUNDED = timeout --signal=TERM --kill-after=5s "$(MYPY_TIMEOUT_SECONDS)s" prlimit --as=$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )):$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )) --
VALIDATE_MYPY_LIMITS = case "$(MYPY_MEMORY_LIMIT_MB)" in ""|*[!0-9]*) echo "ERROR: MYPY_MEMORY_LIMIT_MB must be a positive integer"; exit 2;; esac; [ "$(MYPY_MEMORY_LIMIT_MB)" -gt 0 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be greater than zero"; exit 2; }; [ "$(MYPY_MEMORY_LIMIT_MB)" -le 6144 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be less than or equal to 6144"; exit 2; }; case "$(MYPY_TIMEOUT_SECONDS)" in ""|*[!0-9]*) echo "ERROR: MYPY_TIMEOUT_SECONDS must be a positive integer"; exit 2;; esac; [ "$(MYPY_TIMEOUT_SECONDS)" -gt 0 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be greater than zero"; exit 2; }; [ "$(MYPY_TIMEOUT_SECONDS)" -le 600 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be less than or equal to 600"; exit 2; }; command -v timeout >/dev/null 2>&1 || { echo "ERROR: required executable not found: timeout"; exit 2; }; command -v prlimit >/dev/null 2>&1 || { echo "ERROR: required executable not found: prlimit"; exit 2; }
REPORT_MYPY_FAILURE = code=$$?; signal=none; if [ "$$code" -ge 128 ]; then signal=$$(( $$code - 128 )); fi; if [ "$$code" -eq 124 ] || [ "$$signal" != none ]; then reason="resource limit triggered"; else reason="type check failed under enforced limits"; fi; echo "ERROR: Mypy $$reason: memory_limit=$(MYPY_MEMORY_LIMIT_MB) MiB; timeout=$(MYPY_TIMEOUT_SECONDS)s; exit=$$code; signal=$$signal" >&2
export MYPY_MEMORY_LIMIT_MB MYPY_TIMEOUT_SECONDS

# === SILENT MODE ===
Q := @
ifdef VERBOSE
Q :=
endif

# === CACHE ===
LINT_CACHE_DIR := .lint-cache
CACHE_TIMEOUT := 300
BASE_INFRA_VALIDATE = $(PROJECT_INFRA_ROOT) validate

$(LINT_CACHE_DIR):
	$(Q)mkdir -p $(LINT_CACHE_DIR)

# === SIMPLE VERB SURFACE ===
.PHONY: help boot build check scan fmt docs docs-serve test val clean pr _preflight daemon-start-mypy daemon-stop-mypy daemon-status-mypy daemon-start-pyright daemon-stop-pyright daemon-status-pyright daemon-start daemon-stop daemon-status daemon-restart
STANDARD_VERBS := boot build check scan fmt docs test val clean pr
$(STANDARD_VERBS): _preflight

define ENFORCE_WORKSPACE_VENV
if [ "$(FLEXT_MODE)" = "workspace" ]; then \
	if [ -d "$(WORKSPACE_ROOT)/.venv" ]; then \
		if [ -d ".venv" ] && [ "$(CURDIR)" != "$(WORKSPACE_ROOT)" ]; then \
			echo "ERROR: [preflight] Project-local .venv violates the workspace environment contract: $(CURDIR)/.venv"; \
			exit 1; \
		fi; \
	elif [ "$(CURDIR)" = "$(WORKSPACE_ROOT)" ]; then \
		echo "ERROR: [preflight] Workspace venv not found. Run 'make boot' at workspace root."; \
		exit 1; \
	elif [ "$(filter boot,$(MAKECMDGOALS))" != "boot" ] && [ ! -d "$(ACTIVE_VENV)" ]; then \
		echo "ERROR: [preflight] No venv found (workspace or local). Run 'make boot' in $(PROJECT_NAME)."; \
		exit 1; \
	else \
		echo "INFO: [preflight] Using project-local venv for $(PROJECT_NAME) (workspace venv not found)."; \
	fi; \
elif [ "$(FLEXT_MODE)" = "standalone" ]; then \
	echo "INFO: [preflight] Running in standalone mode (workspace features unavailable)."; \
elif [ "$(filter boot setup,$(MAKECMDGOALS))" = "" ] && [ ! -d "$(ACTIVE_VENV)" ]; then \
	echo "ERROR: [preflight] No venv found at $(ACTIVE_VENV). Run 'make boot' in $(PROJECT_NAME)."; \
	exit 1; \
fi
endef

# mro-wkii.17.27 (codex): validation verbs detect drift without mutating files.
define VALIDATE_CANONICAL_BASE_MK
if [ "$(FLEXT_MODE)" = "workspace" ] && [ "$(CURDIR)" != "$(WORKSPACE_ROOT)" ]; then \
	if [ "$(filter boot,$(MAKECMDGOALS))" = "boot" ] && [ ! -x "$(FLEXT_INFRA_PYTHON)" ]; then \
		echo "INFO: [preflight] Deferring canonical base.mk validation until boot creates the workspace environment."; \
	elif ! $(BASE_INFRA_VALIDATE) basemk-validate --workspace "$(WORKSPACE_ROOT)/flext-infra"; then \
		echo "ERROR: [preflight] Canonical base.mk is stale. Run 'make -C $(WORKSPACE_ROOT) build WHAT=sync PROJECT=$(PROJECT_NAME)'."; \
		exit 1; \
	fi; \
elif [ "$(FLEXT_MODE)" = "standalone" ]; then \
	echo "INFO: [preflight] Standalone mode: skipping workspace base.mk validation."; \
fi
endef

_preflight: ## Preflight: validate base.mk and enforce venv contract
	$(Q)$(VALIDATE_CANONICAL_BASE_MK)
	$(Q)$(ENFORCE_WORKSPACE_VENV)

PROJECT_INFRA_HOME := $(WORKSPACE_ROOT)/flext-infra
ifeq ($(wildcard $(PROJECT_INFRA_HOME)/src/flext_infra),)
PROJECT_INFRA_HOME := $(PROJECT_ROOT)
endif
PROJECT_INFRA_SRC := $(PROJECT_INFRA_HOME)/src
PROJECT_INFRA_PYTHONPATH ?= $(PROJECT_INFRA_SRC)
FLEXT_INFRA_PYTHON ?= $(VENV_PYTHON)
export FLEXT_INFRA_PYTHON
PROJECT_INFRA_ROOT := test -x "$(FLEXT_INFRA_PYTHON)" || { echo "ERROR: FLEXT_INFRA_PYTHON must name an executable managed Python" >&2; exit 2; }; env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(PATH)" PYTHONPATH="$(PROJECT_INFRA_PYTHONPATH)" $(FLEXT_INFRA_PYTHON) -m flext_infra
PROJECT_INFRA_CHECK := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) check
PROJECT_INFRA_CODEGEN := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) codegen
PROJECT_INFRA_DEPS := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) deps
PROJECT_INFRA_DOCS := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) docs
PROJECT_INFRA_GITHUB := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) github
PROJECT_INFRA_REFACTOR := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) refactor
PROJECT_INFRA_VALIDATE := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) validate

# Verb hook seam: custom.mk may define pre-<verb>, post-<verb>, pre-<verb>-<what>,
# and post-<verb>-<what> targets to append work at the start or end of any verb,
# for all or some WHATs. Undefined hooks are no-ops (make -q returns 2 when a
# target is absent). $(1)=phase (pre|post), $(2)=verb, $(3)=optional WHAT.
define _run_verb_hooks
	@phase="$(1)"; verb="$(2)"; what="$(3)"; \
	hooks="$$phase-$$verb"; \
	if [ -n "$$what" ]; then \
		if [ "$$phase" = "pre" ]; then hooks="$$phase-$$verb $$phase-$$verb-$$what"; \
		else hooks="$$phase-$$verb-$$what $$phase-$$verb"; fi; \
	fi; \
	for hook in $$hooks; do \
		$(MAKE) --no-print-directory -q "$$hook" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then $(MAKE) --no-print-directory "$$hook" || exit $$?; fi; \
	done
endef

# Custom-WHAT dispatch: run the custom.mk handler _custom_<verb>_<what> when it
# exists. Used by the generic `run` verb and by any verb given a WHAT that has no
# builtin meaning. $(1)=verb, $(2)=what. Fails clearly if the handler is absent.
define _run_custom_what
	@verb="$(1)"; what="$(2)"; \
	if [ -z "$$what" ]; then \
		printf 'ERROR: make %s requires WHAT=<action>\n' "$$verb" >&2; exit 2; \
	fi; \
	target="_custom_$${verb}_$${what}"; \
	$(MAKE) --no-print-directory -q "$$target" >/dev/null 2>&1; rc=$$?; \
	if [ "$$rc" -eq 2 ]; then \
		printf 'ERROR: no custom handler %s for make %s WHAT=%s (define it in custom.mk)\n' "$$target" "$$verb" "$$what" >&2; \
		exit 2; \
	fi; \
	$(MAKE) --no-print-directory "$$target"
endef

# Verb body dispatch: if custom.mk defines _custom_<verb>_<what> for the current
# WHAT, run that custom handler; otherwise run the builtin implementation. This
# lets every verb accept project-specific WHATs while preserving builtin WHATs.
# $(1)=verb, $(2)=builtin impl target.
define _run_verb_body
	@verb="$(1)"; impl="$(2)"; what="$(WHAT)"; \
	if [ -n "$$what" ]; then \
		custom="_custom_$${verb}_$${what}"; \
		$(MAKE) --no-print-directory -q "$$custom" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then exec $(MAKE) --no-print-directory "$$custom"; fi; \
	fi; \
	exec $(MAKE) --no-print-directory "$$impl"
endef

help: ## Show commands
	$(Q)echo "================================================"
	$(Q)echo "  $(PROJECT_NAME)"
	$(Q)echo "================================================"
	$(Q)echo ""
	$(Q)echo "Core verbs:"

	$(Q)printf "  %-14s %s\n" "boot" "Install dependencies and hooks"

	$(Q)printf "  %-14s %s\n" "build" "Build distributable artifacts"

	$(Q)printf "  %-14s %s\n" "check" "Run lint gates (CHECK_GATES= to select)"

	$(Q)printf "  %-14s %s\n" "fix-enforcement" "Auto-fix enforcement violations (APPLY=1, PROJECTS=..., RULES=...)"

	$(Q)printf "  %-14s %s\n" "scan" "Run all security checks"

	$(Q)printf "  %-14s %s\n" "fmt" "Run all formatting"

	$(Q)printf "  %-14s %s\n" "docs" "Build docs (DOCS_PHASE= to select)"

	$(Q)printf "  %-14s %s\n" "test" "Run pytest (PYTEST_ARGS= for options)"

	$(Q)printf "  %-14s %s\n" "val" "Run validate gates (FIX=1 to auto-fix)"

	$(Q)printf "  %-14s %s\n" "clean" "Clean build/test/type artifacts"

	$(Q)echo ""
	$(Q)echo "Daemon management:"

	$(Q)printf "  %-16s %s\n" "daemon-start" "Start all daemons (mypy + pyright)"

	$(Q)printf "  %-16s %s\n" "daemon-stop" "Stop all daemons"

	$(Q)printf "  %-16s %s\n" "daemon-status" "Show status of all daemons"

	$(Q)printf "  %-16s %s\n" "daemon-restart" "Restart all daemons"

	$(Q)echo "  Also: daemon-{start,stop,status}-{mypy,pyright}"
	$(Q)echo ""
	$(Q)echo "Selectors and options:"

	$(Q)echo "  CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,smells"

	$(Q)echo "  MYPY_MEMORY_LIMIT_MB=6144  Mypy address-space cap"

	$(Q)echo "  MYPY_TIMEOUT_SECONDS=600  Mypy wall-time cap"

	$(Q)echo "  VALIDATE_GATES=complexity,docstring"

	$(Q)echo "  FILE=src/foo.py             Single file for check/fmt/test"

	$(Q)echo "  FILES=\"a.py b.py\"          Multiple files for check/fmt/test"

	$(Q)echo "  CHANGED_ONLY=1              Git-changed Python files for check"

	$(Q)echo "  CHECK_ONLY=1                Dry-run format/check (no writes)"

	$(Q)echo "  RUFF_ARGS=\"--select E501\"   Extra args for ruff check"

	$(Q)echo "  PYRIGHT_ARGS=\"--level basic\" Extra args for pyright"

	$(Q)echo "  PYTEST_ARGS=\"-k expr\"       Extra pytest args"

	$(Q)echo "  PYTEST_TARGETS=\"tests/unit\" Pytest collection targets"

	$(Q)echo "  MATCH=test_name             Alias for pytest -k"

	$(Q)echo "  FAIL_FAST=1                 Add -x to pytest"

	$(Q)echo "  DIAG=1                      Emit extended pytest diagnostics"

	$(Q)echo "  DOCS_PHASE=all|generate|fix|audit|build|validate"

	$(Q)echo "  FIX=1                       Auto-fix supported gates"

	$(Q)echo "  APPLY=1                     Apply enforcement fixes (default dry-run)"

	$(Q)echo "  PROJECTS=p1,p2              Scope fix-enforcement to projects"

	$(Q)echo "  RULES=ENFORCE-XXX,...       Scope fix-enforcement to rules"

	$(Q)echo "  VERBOSE=1                   Show executed commands"

	$(Q)echo "  TEST_ITEM_TIMEOUT_SECONDS=$(TEST_ITEM_TIMEOUT_SECONDS)  Per-item pytest deadline"
	$(Q)echo "  TEST_SESSION_TIMEOUT_SECONDS=$(TEST_SESSION_TIMEOUT_SECONDS)  Whole pytest process deadline"
	$(Q)echo "  TEST_SHARD_COUNT=$(TEST_SHARD_COUNT)  Deterministic full-suite partitions"
	$(Q)echo "  TEST_SHARD_PARALLELISM=$(TEST_SHARD_PARALLELISM)  Concurrent full-suite partitions"
	$(Q)echo ""
	$(Q)echo "PR variables:"

	$(Q)echo "  PR_ACTION=status|create"

	$(Q)echo "  PR_BASE=<branch>  PR_HEAD=<branch>"

	$(Q)echo "  PR_TITLE='...'  PR_BODY='...'  PR_DRAFT=0|1"


	$(Q)echo ""
	$(Q)echo "Custom hooks (custom.mk):"
	$(Q)echo "  Define pre-<verb>, post-<verb>, pre-<verb>-<what>, post-<verb>-<what>"
	$(Q)echo "  in custom.mk to run extra steps at the start or end of any verb, for"
	$(Q)echo "  all or some WHATs. Add _custom_<verb>_<what> to define a new WHAT."
	$(Q)if [ -f custom.mk ]; then \
		hooks=$$(grep -oE '^(pre|post)-[a-z][a-z0-9-]*|^_custom_[a-z][a-z0-9_-]*' custom.mk 2>/dev/null | sort -u); \
		if [ -n "$$hooks" ]; then \
			echo "  Defined in this project:"; \
			for hook in $$hooks; do echo "    $$hook"; done; \
		fi; \
	fi

boot: ## Complete setup
	$(call _run_verb_hooks,pre,boot,$(WHAT))
	$(call _run_verb_body,boot,_boot_impl)
	$(call _run_verb_hooks,post,boot,$(WHAT))

_boot_impl:
	$(Q)$(UV) sync --all-extras --all-groups
	$(Q)$(PROJECT_INFRA_DEPS) extra-paths --apply --workspace "$(CURDIR)"
	$(Q)$(UV) lock
	$(Q)$(UV) sync --all-extras --all-groups --reinstall-package "$(PROJECT_NAME)"
	$(Q)if git rev-parse --git-dir >/dev/null 2>&1; then \
		hooks_path=$$(git config --get --default '' core.hooksPath); \
		if [ -n "$$hooks_path" ]; then \
			echo "INFO: skipping pre-commit install (core.hooksPath=$$hooks_path)"; \
		elif [ -f .pre-commit-config.yaml ] || [ -f .pre-commit-config.yml ]; then \
			$(UV) run pre-commit install; \
		else \
			echo "INFO: skipping pre-commit install (no pre-commit config)"; \
		fi; \
	else \
		echo "INFO: skipping pre-commit install (no git repository)"; \
	fi

build: ## Build distributable artifacts
	$(call _run_verb_hooks,pre,build,$(WHAT))
	$(call _run_verb_body,build,_build_impl)
	$(call _run_verb_hooks,post,build,$(WHAT))

_build_impl:
	$(Q)build_start=$$(date +%s) && \
	$(UV) build --project "$(CURDIR)" --no-sources && \
	echo "Build complete: $(PROJECT_NAME) ($$(($$(date +%s) - $$build_start))s)"

check: ## Run lint gates (CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,smells to select)
	$(call _run_verb_hooks,pre,check,$(WHAT))
	$(call _run_verb_body,check,_check_impl)
	$(call _run_verb_hooks,post,check,$(WHAT))

_check_impl:
	$(Q)gates="$(CHECK_GATES)"; \
	if [ -n "$$gates" ]; then \
		for g in $$(echo "$$gates" | tr ',' ' '); do \
			case "$$g" in \
				lint|format|pyrefly|mypy|pyright|security|markdown|smells) ;; \
				*) echo "ERROR: unknown CHECK_GATES value '$$g' (allowed: lint,format,pyrefly,mypy,pyright,security,markdown,smells)"; exit 2;; \
			esac; \
		done; \
	else \
		gates="lint,format,pyrefly,mypy,pyright,security,markdown,smells"; \
	fi; \
	gates=$$(echo "$$gates" | tr ',' ' ' | tr ' ' ','); \
	_files=""; \
	if [ -n "$(FILES)" ]; then _files="$(FILES)"; fi; \
	if [ -n "$(FILE)" ]; then \
		if [ -n "$$_files" ]; then _files="$$_files $(FILE)"; \
		else _files="$(FILE)"; fi; \
	fi; \
	if [ "$(CHANGED_ONLY)" = "1" ]; then \
		_files=$$( \
			{ git diff --name-only --diff-filter=ACMRTUXB HEAD -- '*.py'; \
			  git ls-files --others --exclude-standard -- '*.py'; } \
			| tr '\n' ' ' \
		); \
	fi; \
	if [ -n "$$_files" ]; then \
		if [ -z "$(CHECK_GATES)" ]; then gates="lint,format,pyrefly,mypy,pyright"; fi; \
		unsupported_gates=$$(printf '%s\n' "$$gates" | tr ',' '\n' | awk '/^(security|markdown)$$/ {print}'); \
		if [ -n "$$unsupported_gates" ]; then \
			echo "ERROR: FILE/FILES/CHANGED_ONLY fast-path only supports lint,format,pyrefly,mypy,pyright"; \
			exit 2; \
		fi; \
		echo "Fast-path check: $$_files"; \
		status=0; \
		case ",$$gates," in \
			*,lint,*) env -u PYTHONPATH -u MYPYPATH $(UV) run ruff check $$_files $(RUFF_ARGS) $(if $(filter 1,$(FIX)),$(if $(filter 1,$(CHECK_ONLY)),,--fix),) || status=$$?;; \
		esac; \
		case ",$$gates," in \
			*,format,*) env -u PYTHONPATH -u MYPYPATH $(UV) run ruff format $$_files $(if $(filter 1,$(FIX)),$(if $(filter 1,$(CHECK_ONLY)),--check,--quiet),--check) || status=$$?;; \
		esac; \
		case ",$$gates," in \
			*,pyright,*) env -u PYTHONPATH -u MYPYPATH $(UV) run pyright $$_files $(PYRIGHT_ARGS) || status=$$?;; \
		esac; \
		case ",$$gates," in \
			*,pyrefly,*) env -u PYTHONPATH -u MYPYPATH $(UV) run pyrefly check $$_files || status=$$?;; \
		esac; \
		case ",$$gates," in \
			*,mypy,*) $(VALIDATE_MYPY_LIMITS); $(MYPY_BOUNDED) env -u PYTHONPATH -u MYPYPATH $(UV) run mypy $$_files || { $(REPORT_MYPY_FAILURE); status=$$code; };; \
		esac; \
		exit $$status; \
	fi; \
	project_key="$(PROJECT_NAME)"; \
	if [ "$(CURDIR)" = "$(WORKSPACE_ROOT)" ]; then \
		project_key="."; \
	fi; \
	$(PROJECT_INFRA_CHECK) run --workspace "$(WORKSPACE_ROOT)" --gates "$$gates" --reports-dir "$(CURDIR)/.reports/check" --projects "$$project_key" $(if $(filter 1,$(FIX)),$(if $(filter 1,$(CHECK_ONLY)),,--fix),) $(if $(filter 1,$(CHECK_ONLY)),--check-only,) $(if $(RUFF_ARGS),--ruff-args "$(RUFF_ARGS)",) $(if $(PYRIGHT_ARGS),--pyright-args "$(PYRIGHT_ARGS)",); \
	exit $$?

fix-enforcement: ## Auto-fix enforcement-catalog violations (APPLY=1 to apply, PROJECTS=..., RULES=...)
	$(call _run_verb_hooks,pre,fix-enforcement,$(WHAT))
	$(call _run_verb_body,fix-enforcement,_fix_enforcement_impl)
	$(call _run_verb_hooks,post,fix-enforcement,$(WHAT))

_fix_enforcement_impl:
	$(Q)apply_flag=""; \
	if [ "$(APPLY)" = "1" ]; then apply_flag="--apply"; fi; \
	projects_arg=""; \
	if [ -n "$(PROJECTS)" ]; then projects_arg="--projects $(PROJECTS)"; fi; \
	rules_arg=""; \
	if [ -n "$(RULES)" ]; then rules_arg="--rules $(RULES)"; fi; \
	$(PROJECT_INFRA_CHECK) fix-enforcement --workspace "$(WORKSPACE_ROOT)" $$apply_flag $$projects_arg $$rules_arg; \
	exit $$?

scan: ## Run all security checks
	$(call _run_verb_hooks,pre,scan,$(WHAT))
	$(call _run_verb_body,scan,_scan_impl)
	$(call _run_verb_hooks,post,scan,$(WHAT))

_scan_impl:
	$(Q)project_key="$(PROJECT_NAME)"; \
	if [ "$(CURDIR)" = "$(WORKSPACE_ROOT)" ]; then \
		project_key="."; \
	fi; \
	$(PROJECT_INFRA_CHECK) run \
		--workspace "$(WORKSPACE_ROOT)" \
		--gates "security" \
		--reports-dir "$(CURDIR)/.reports/scan" \
		--projects "$$project_key"; \
	exit $$?

fmt: ## Run code formatting (ruff + rumdl on tracked files)
	$(call _run_verb_hooks,pre,fmt,$(WHAT))
	$(call _run_verb_body,fmt,_fmt_impl)
	$(call _run_verb_hooks,post,fmt,$(WHAT))

_fmt_impl:
	$(Q)_fmt_target="."; \
	_fmt_files=""; \
	if [ -n "$(FILES)" ]; then _fmt_files="$(FILES)"; fi; \
	if [ -n "$(FILE)" ]; then \
		if [ -n "$$_fmt_files" ]; then _fmt_files="$$_fmt_files $(FILE)"; \
		else _fmt_files="$(FILE)"; fi; \
	fi; \
	if [ -n "$$_fmt_files" ]; then _fmt_target="$$_fmt_files"; fi; \
	if [ "$(CHECK_ONLY)" = "1" ]; then \
		$(UV) run ruff format $$_fmt_target --check; \
	else \
		$(UV) run ruff format $$_fmt_target --quiet; \
	fi
	$(Q)if [ "$(CURDIR)" = "$(WORKSPACE_ROOT)" ] && [ -n "$(ALL_PROJECTS)" ]; then \
		md_roots=". $(ALL_PROJECTS)"; \
	else \
		md_roots="."; \
	fi; \
	md_files=$$(for md_root in $$md_roots; do \
		[ -d "$$md_root" ] || continue; \
		if git -C "$$md_root" rev-parse --git-dir >/dev/null 2>&1; then \
			md_prefix=""; \
			if [ "$$md_root" != "." ]; then md_prefix="$$md_root/"; fi; \
			git -C "$$md_root" ls-files -- '*.md' ':!vendor/' | sed "s#^#$$md_prefix#"; \
			git -C "$$md_root" ls-files --others --exclude-standard -- '*.md' ':!vendor/' | sed "s#^#$$md_prefix#"; \
		else \
			find "$$md_root" -type f -name '*.md' ! -path '*/.git/*' ! -path '*/.reports/*' ! -path '*/.venv/*' ! -path '*/vendor/*' ! -path '*/node_modules/*' ! -path '*/dist/*' ! -path '*/build/*'; \
		fi; \
	done); \
	md_files=$$(printf '%s\n' "$$md_files" | awk 'NF' | while IFS= read -r f; do [ -f "$$f" ] && printf '%s\n' "$$f"; done | sort -u); \
	if [ -n "$$md_files" ]; then \
		md_config=""; \
		if [ -f "$(WORKSPACE_ROOT)/.markdownlint.json" ]; then \
			md_config="--config $(WORKSPACE_ROOT)/.markdownlint.json"; \
		elif [ -f ".markdownlint.json" ]; then \
			md_config="--config .markdownlint.json"; \
		fi; \
		echo "$$md_files" | xargs -r "$(dir $(VENV_PYTHON))rumdl" check --fix --no-cache --deny-config-warnings --color never $$md_config; \
	fi
	$(Q)echo "Format complete: $(PROJECT_NAME)"

docs: ## Build docs
	$(call _run_verb_hooks,pre,docs,$(WHAT))
	$(call _run_verb_body,docs,_docs_impl)
	$(call _run_verb_hooks,post,docs,$(WHAT))

_docs_impl:
	$(Q)if python3 -c "import flext_infra.docs" >/dev/null 2>&1; then \
		echo "PROJECT=$(PROJECT_NAME) PHASE=sync RESULT=OK REASON=docs-module-available"; \
	else \
		echo "PROJECT=$(PROJECT_NAME) PHASE=sync RESULT=FAIL REASON=docs-module-missing"; \
		exit 1; \
	fi
	$(Q)if [ "$(DOCS_PHASE)" = "all" ]; then \
		phases="generate fix audit build validate"; \
		all_mode=1; \
	else \
		phases="$(DOCS_PHASE)"; \
		all_mode=0; \
	fi; \
	for phase in $$phases; do \
		case "$$phase" in \
			audit) subcmd="$(PROJECT_INFRA_DOCS) audit"; extra="--strict" ;; \
			fix) subcmd="$(PROJECT_INFRA_DOCS) fix"; extra="$(if $(filter 1,$(FIX)),--apply,)" ;; \
			build) subcmd="$(PROJECT_INFRA_DOCS) build"; extra="" ;; \
			generate) subcmd="$(PROJECT_INFRA_DOCS) generate"; extra="--apply" ;; \
			validate) subcmd="$(PROJECT_INFRA_DOCS) validate"; extra="$(if $(filter 1,$(FIX)),--apply,)" ;; \
				*) echo "ERROR: invalid DOCS_PHASE=$$phase (allowed: all|generate|fix|audit|build|validate)"; exit 2 ;; \
			esac; \
		if [ "$$phase" = "fix" ] && [ "$$all_mode" = "1" ]; then extra="--apply"; fi; \
		cmd="$$subcmd --workspace . --output-dir .reports/docs"; \
		if [ -n "$$extra" ]; then cmd="$$cmd $$extra"; fi; \
		eval $$cmd || exit $$?; \
	done

# kimi-docs mro-3o9s: docs-serve padrão no template — motor único flext-infra docs
docs-serve: ## Serve documentation via the flext-infra docs engine
	$(call _run_verb_hooks,pre,docs-serve,$(WHAT))
	$(call _run_verb_body,docs-serve,_docs_serve_impl)
	$(call _run_verb_hooks,post,docs-serve,$(WHAT))

_docs_serve_impl:
	$(Q)$(PROJECT_INFRA_DOCS) serve --workspace .

test: ## Run pytest only
	$(call _run_verb_hooks,pre,test,$(WHAT))
	$(call _run_verb_body,test,_test_impl)
	$(call _run_verb_hooks,post,test,$(WHAT))

_test_impl:

	$(Q)_files="$(strip $(FILES))"; \
	case "$(TEST_ITEM_TIMEOUT_SECONDS)" in ""|*[!0-9]*) \
		printf 'ERROR: TEST_ITEM_TIMEOUT_SECONDS must be a positive integer\n' >&2; exit 2 ;; \
	esac; \
	case "$(TEST_SESSION_TIMEOUT_SECONDS)" in ""|*[!0-9]*) \
		printf 'ERROR: TEST_SESSION_TIMEOUT_SECONDS must be a positive integer\n' >&2; exit 2 ;; \
	esac; \
	case "$(TEST_SHARD_COUNT)" in ""|*[!0-9]*) \
		printf 'ERROR: TEST_SHARD_COUNT must be a positive integer\n' >&2; exit 2 ;; \
	esac; \
	case "$(TEST_SHARD_PARALLELISM)" in ""|*[!0-9]*) \
		printf 'ERROR: TEST_SHARD_PARALLELISM must be a positive integer\n' >&2; exit 2 ;; \
	esac; \
	if [ "$(TEST_ITEM_TIMEOUT_SECONDS)" -le 0 ] || \
		[ "$(TEST_ITEM_TIMEOUT_SECONDS)" -gt 10 ]; then \
		printf 'ERROR: TEST_ITEM_TIMEOUT_SECONDS must be between 1 and 10\n' >&2; exit 2; \
	fi; \
	if [ "$(TEST_SESSION_TIMEOUT_SECONDS)" -le 0 ] || \
		[ "$(TEST_SESSION_TIMEOUT_SECONDS)" -gt 60 ]; then \
		printf 'ERROR: TEST_SESSION_TIMEOUT_SECONDS must be between 1 and 60\n' >&2; exit 2; \
	fi; \
	if [ "$(TEST_ITEM_TIMEOUT_SECONDS)" -ge "$(TEST_SESSION_TIMEOUT_SECONDS)" ]; then \
		printf 'ERROR: TEST_ITEM_TIMEOUT_SECONDS must be less than TEST_SESSION_TIMEOUT_SECONDS\n' >&2; exit 2; \
	fi; \
	if [ "$(TEST_SHARD_COUNT)" -le 0 ] || \
		[ "$(TEST_SHARD_COUNT)" -gt 16 ]; then \
		printf 'ERROR: TEST_SHARD_COUNT must be between 1 and 16\n' >&2; exit 2; \
	fi; \
	if [ "$(TEST_SHARD_PARALLELISM)" -le 0 ] || \
		[ "$(TEST_SHARD_PARALLELISM)" -gt 2 ]; then \
		printf 'ERROR: TEST_SHARD_PARALLELISM must be between 1 and 2\n' >&2; exit 2; \
	fi; \
	if [ "$(TEST_SHARD_PARALLELISM)" -gt "$(TEST_SHARD_COUNT)" ]; then \
		printf 'ERROR: TEST_SHARD_PARALLELISM must not exceed TEST_SHARD_COUNT\n' >&2; exit 2; \
	fi; \
	command -v timeout >/dev/null 2>&1 || { \
		printf 'ERROR: required executable not found: timeout\n' >&2; exit 2; \
	}; \
	session_started_epoch=$$(date +%s); \
	if [ -n "$(FILE)" ]; then \
		case "$(FILE)" in /*|..|../*|*/../*|*/..) \
			printf 'ERROR: FILE must be a repository-relative path\n' >&2; exit 2 ;; \
		esac; \
		if [ -n "$$_files" ]; then _files="$$_files $(FILE)"; else _files="$(FILE)"; fi; \
	fi; \
	_pytest_run="$(PYTEST_TARGETS)"; \
	if [ -n "$$_files" ]; then _pytest_run="$$_files"; fi; \
	for target in $$_pytest_run; do \
		if [ ! -e "$$target" ]; then \
			printf 'ERROR: test target does not exist: %s\n' "$$target" >&2; exit 2; \
		fi; \
	done; \
	_all_pytest_args="$(PYTEST_ARGS)"; \
	if [ -n "$(MATCH)" ]; then _all_pytest_args="$$_all_pytest_args -k $(MATCH)"; fi; \
	if [ "$(FAIL_FAST)" = "1" ]; then _all_pytest_args="$$_all_pytest_args -x"; fi; \
	if [ "$(VERBOSE)" = "1" ]; then _all_pytest_args="$$_all_pytest_args -vv -s"; fi; \
	run_id=$$(date -u +%Y%m%dT%H%M%SZ)-$$$$; \
	report_dir="$(PYTEST_REPORTS_DIR)/$$run_id"; \
	mkdir -p "$$report_dir"; \
	log_file="$$report_dir/pytest.log"; \
	junit_file="$$report_dir/junit.xml"; \
	coverage_file="$$report_dir/coverage.xml"; \
	summary_file="$$report_dir/summary.txt"; \
	failed_file="$$report_dir/failed-tests.txt"; \
	errors_file="$$report_dir/errors.txt"; \
	warnings_file="$$report_dir/warnings.txt"; \
	slowest_file="$$report_dir/slowest-tests.txt"; \
	skips_file="$$report_dir/skipped-tests.txt"; \
	command_file="$$report_dir/command.txt"; \
	_coverage_args="--cov --cov-report=xml:$$coverage_file"; \
	_coverage_required=1; \
	_coverage_value="$$coverage_file"; \
	_coverage_default_target="$$(cd "$(TESTS_DIR)" 2>/dev/null && pwd -P)"; \
	_pytest_run_target="$$(cd "$$_pytest_run" 2>/dev/null && pwd -P)"; \
	if [ -n "$$_files" ] || [ -n "$(MATCH)" ] || \
		[ "$$_pytest_run_target" != "$$_coverage_default_target" ]; then \
		_coverage_args="--no-cov"; \
		_coverage_required=0; \
		_coverage_value="not-generated"; \
	fi; \
	_diag_inputs=""; \
	if [ "$$_coverage_required" -eq 1 ]; then \
		plan_dir="$$report_dir/shard-plan"; \
		plan_log="$$report_dir/pytest-plan.log"; \
		mkdir -p "$$plan_dir"; \
		printf '%s\n' '$(VENV_PYTHON) -m pytest' \
			"$$_pytest_run --collect-only -p flext_infra.pytest_shard" \
			"--flext-shard-count=$(TEST_SHARD_COUNT) --flext-shard-plan-dir=$$plan_dir" \
			"--timeout=$(TEST_ITEM_TIMEOUT_SECONDS) --timeout-method=signal" \
			"$$_all_pytest_args" > "$$command_file"; \
		timeout --signal=TERM \
			--kill-after=5s \
			"$(TEST_SESSION_TIMEOUT_SECONDS)s" \
			$(VENV_PYTHON) -m pytest $$_pytest_run --collect-only -q --no-cov \
			-p no:metadata -p flext_infra.pytest_shard \
			--flext-shard-count="$(TEST_SHARD_COUNT)" \
			--flext-shard-plan-dir="$$plan_dir" \
			--basetemp="$$report_dir/pytest-plan-tmp" \
			-o cache_dir="$$report_dir/pytest-plan-cache" \
			--timeout="$(TEST_ITEM_TIMEOUT_SECONDS)" \
			--timeout-method=signal $$_all_pytest_args > "$$plan_log" 2>&1; \
		rc=$$?; \
		cat "$$plan_log"; \
		if [ "$$rc" -eq 124 ]; then \
			printf 'ERROR: pytest collection plan exceeded %ss\n' \
				"$(TEST_SESSION_TIMEOUT_SECONDS)" >&2; \
		fi; \
		if [ "$$rc" -ne 0 ] || [ ! -s "$$plan_dir/all-items.txt" ]; then \
			printf 'ERROR: pytest shard plan failed or produced no items\n' >&2; \
			ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
			exit "$${rc:-2}"; \
		fi; \
		shard_index=0; \
		while [ "$$shard_index" -lt "$(TEST_SHARD_COUNT)" ]; do \
			expected="$$plan_dir/shard-$$shard_index.expected.txt"; \
			if [ ! -s "$$expected" ]; then \
				printf 'ERROR: pytest shard plan is missing or empty: %s\n' \
					"$$expected" >&2; exit 2; \
			fi; \
			shard_index=$$((shard_index + 1)); \
		done; \
		: > "$$log_file"; \
		rc=0; \
		batch_start=0; \
		while [ "$$batch_start" -lt "$(TEST_SHARD_COUNT)" ]; do \
			batch_end=$$((batch_start + $(TEST_SHARD_PARALLELISM))); \
			if [ "$$batch_end" -gt "$(TEST_SHARD_COUNT)" ]; then \
				batch_end="$(TEST_SHARD_COUNT)"; \
			fi; \
			shard_index="$$batch_start"; \
			pids=""; \
			while [ "$$shard_index" -lt "$$batch_end" ]; do \
				expected="$$plan_dir/shard-$$shard_index.expected.txt"; \
				actual="$$plan_dir/shard-$$shard_index.actual.txt"; \
				shard_log="$$report_dir/pytest-shard-$$shard_index.log"; \
				shard_junit="$$report_dir/junit-shard-$$shard_index.xml"; \
				shard_status="$$report_dir/shard-$$shard_index.status"; \
				shard_coverage="$$report_dir/.coverage.shard-$$shard_index"; \
				( \
					COVERAGE_FILE="$$shard_coverage" \
					timeout --signal=TERM \
						--kill-after=5s \
						"$(TEST_SESSION_TIMEOUT_SECONDS)s" \
						$(VENV_PYTHON) -m pytest $$_pytest_run \
						$(PYTEST_REPORT_ARGS) \
						$(if $(filter 1,$(DIAG)),$(PYTEST_DIAG_ARGS),) \
						-p no:metadata -p flext_infra.pytest_shard \
						--flext-shard-count="$(TEST_SHARD_COUNT)" \
						--flext-shard-index="$$shard_index" \
						--flext-shard-source-manifest="$$expected" \
						--flext-shard-manifest="$$actual" \
						--basetemp="$$report_dir/pytest-shard-$$shard_index-tmp" \
						-o cache_dir="$$report_dir/pytest-shard-$$shard_index-cache" \
						--junitxml="$$shard_junit" \
						--timeout="$(TEST_ITEM_TIMEOUT_SECONDS)" \
						--timeout-method=signal \
						--cov --cov-report= \
						$(if $(filter 1,$(DIAG)),-vv,-q) \
						$$_all_pytest_args > "$$shard_log" 2>&1; \
					printf '%s\n' "$$?" > "$$shard_status"; \
				) & \
				pids="$$pids $$!"; \
				shard_index=$$((shard_index + 1)); \
			done; \
			for pid in $$pids; do wait "$$pid" || :; done; \
			shard_index="$$batch_start"; \
			while [ "$$shard_index" -lt "$$batch_end" ]; do \
				shard_log="$$report_dir/pytest-shard-$$shard_index.log"; \
				shard_junit="$$report_dir/junit-shard-$$shard_index.xml"; \
				shard_status="$$report_dir/shard-$$shard_index.status"; \
				printf '\n=== pytest shard %s ===\n' "$$shard_index" | tee -a "$$log_file"; \
				cat "$$shard_log" | tee -a "$$log_file"; \
				if [ ! -s "$$shard_status" ]; then \
					printf 'ERROR: pytest shard %s produced no status\n' \
						"$$shard_index" >&2; child_rc=2; \
				else \
					child_rc=$$(cat "$$shard_status"); \
				fi; \
				if [ "$$child_rc" -eq 124 ]; then \
					printf 'ERROR: pytest shard %s exceeded %ss\n' \
						"$$shard_index" "$(TEST_SESSION_TIMEOUT_SECONDS)" >&2; \
				fi; \
				if [ "$$child_rc" -ne 0 ] && [ "$$rc" -eq 0 ]; then rc="$$child_rc"; fi; \
				_diag_inputs="$$_diag_inputs --junit $$shard_junit --log $$shard_log"; \
				shard_index=$$((shard_index + 1)); \
			done; \
			if [ "$$rc" -ne 0 ]; then break; fi; \
			batch_start="$$batch_end"; \
		done; \
		if [ "$$rc" -eq 0 ]; then \
			actual_all="$$plan_dir/all-items.actual.txt"; \
			: > "$$actual_all"; \
			shard_index=0; \
			while [ "$$shard_index" -lt "$(TEST_SHARD_COUNT)" ]; do \
				actual="$$plan_dir/shard-$$shard_index.actual.txt"; \
				if [ ! -s "$$actual" ]; then \
					printf 'ERROR: pytest shard result is missing or empty: %s\n' \
						"$$actual" >&2; rc=2; break; \
				fi; \
				cat "$$actual" >> "$$actual_all"; \
				shard_index=$$((shard_index + 1)); \
			done; \
			if [ "$$rc" -eq 0 ]; then \
				LC_ALL=C sort "$$plan_dir/all-items.txt" > "$$plan_dir/all-items.sorted.txt"; \
				LC_ALL=C sort "$$actual_all" > "$$plan_dir/all-items.actual.sorted.txt"; \
				if [ -s "$$actual_all" ] && \
					[ "$$(wc -l < "$$actual_all")" -ne \
						"$$(LC_ALL=C sort -u "$$actual_all" | wc -l)" ]; then \
					printf 'ERROR: duplicate pytest node ids across shards\n' >&2; rc=2; \
				elif ! cmp -s "$$plan_dir/all-items.sorted.txt" \
					"$$plan_dir/all-items.actual.sorted.txt"; then \
					printf 'ERROR: pytest shard manifests do not cover the collection plan\n' \
						>&2; rc=2; \
				fi; \
			fi; \
		fi; \
		if [ "$$rc" -eq 0 ]; then \
			$(VENV_PYTHON) -m coverage combine \
				--data-file="$$report_dir/.coverage.combined" --keep "$$report_dir"; \
			rc=$$?; \
			if [ "$$rc" -eq 0 ]; then \
				$(VENV_PYTHON) -m coverage xml \
					--data-file="$$report_dir/.coverage.combined" \
					-o "$$coverage_file"; \
				rc=$$?; \
			fi; \
		fi; \
		junit_file="sharded:$$report_dir/junit-shard-*.xml"; \
	else \
		printf '%s\n' '$(VENV_PYTHON) -m pytest' \
			"$$_pytest_run $(PYTEST_REPORT_ARGS) -p no:metadata --junitxml=$$junit_file" \
			"--timeout=$(TEST_ITEM_TIMEOUT_SECONDS) --timeout-method=signal" \
			"$$_coverage_args $$_all_pytest_args" > "$$command_file"; \
		timeout --signal=TERM \
			--kill-after=5s \
			"$(TEST_SESSION_TIMEOUT_SECONDS)s" \
			$(VENV_PYTHON) -m pytest $$_pytest_run \
			$(PYTEST_REPORT_ARGS) \
			$(if $(filter 1,$(DIAG)),$(PYTEST_DIAG_ARGS),) \
			-p no:metadata \
			--junitxml="$$junit_file" \
			--timeout="$(TEST_ITEM_TIMEOUT_SECONDS)" \
			--timeout-method=signal \
			$$_coverage_args \
			$(if $(filter 1,$(DIAG)),-vv,-q) \
			$$_all_pytest_args > "$$log_file" 2>&1; \
		rc=$$?; \
		cat "$$log_file"; \
		if [ "$$rc" -eq 124 ]; then \
			printf 'ERROR: pytest session exceeded %ss\n' \
				"$(TEST_SESSION_TIMEOUT_SECONDS)" >&2; \
		fi; \
		_diag_inputs="--junit $$junit_file --log $$log_file"; \
	fi; \
	if [ "$$_coverage_required" -eq 1 ] && [ ! -s "$$coverage_file" ]; then \
		printf 'ERROR: coverage report was not generated or is empty: %s\n' \
			"$$coverage_file" >&2; \
		if [ "$$rc" -eq 0 ]; then rc=2; fi; \
	fi; \
	if [ "$$_coverage_required" -eq 1 ]; then \
		tests=$$(wc -l < "$$plan_dir/all-items.txt"); \
		duration=$$(( $$(date +%s) - session_started_epoch )); \
		failures=0; errors=0; skipped=0; passed="$$tests"; \
	elif [ -f "$$junit_file" ]; then \
		tests=$$(grep -Eo 'tests="[0-9]+"' "$$junit_file" | head -n 1 | tr -dc '0-9'); \
		failures=$$(grep -Eo 'failures="[0-9]+"' "$$junit_file" | head -n 1 | tr -dc '0-9'); \
		errors=$$(grep -Eo 'errors="[0-9]+"' "$$junit_file" | head -n 1 | tr -dc '0-9'); \
		skipped=$$(grep -Eo 'skipped="[0-9]+"' "$$junit_file" | head -n 1 | tr -dc '0-9'); \
		duration=$$(grep -Eo 'time="[0-9.]+"' "$$junit_file" | head -n 1 | sed -E 's/time="([0-9.]+)"/\1/'); \
		tests=$${tests:-0}; failures=$${failures:-0}; errors=$${errors:-0}; \
		skipped=$${skipped:-0}; duration=$${duration:-0}; \
		passed=$$((tests - failures - errors - skipped)); \
		if [ "$$passed" -lt 0 ]; then passed=0; fi; \
	else \
		tests=0; failures=0; errors=0; skipped=0; passed=0; duration=0; \
	fi; \
	printf 'junit=%s\ncoverage=%s\ntotal=%s\npassed=%s\nfailed=%s\nerrors=%s\nskipped=%s\nduration_seconds=%s\n' \
		"$$junit_file" "$$_coverage_value" "$$tests" "$$passed" "$$failures" \
		"$$errors" "$$skipped" "$$duration" > "$$summary_file"; \
	counts_file="$$report_dir/counts.env"; \
	elapsed_seconds=$$(( $$(date +%s) - session_started_epoch )); \
	if [ "$$_coverage_required" -eq 1 ]; then \
		remaining_seconds="$(TEST_SESSION_TIMEOUT_SECONDS)"; \
	else \
		remaining_seconds=$$(( $(TEST_SESSION_TIMEOUT_SECONDS) - elapsed_seconds )); \
	fi; \
	if [ "$$remaining_seconds" -le 0 ]; then \
		printf 'ERROR: test session exhausted %ss before diagnostic extraction\n' \
			"$(TEST_SESSION_TIMEOUT_SECONDS)" >&2; \
		exit 124; \
	fi; \
	if timeout --signal=TERM \
		--kill-after=5s "$${remaining_seconds}s" \
		env $(PROJECT_INFRA_VALIDATE) pytest-diag \
		$$_diag_inputs \
		--failed "$$failed_file" --errors "$$errors_file" \
		--warnings "$$warnings_file" --slowest "$$slowest_file" \
		--skips "$$skips_file" > "$$counts_file"; then \
		:; \
	else \
		counts_status=$$?; \
		printf 'ERROR: pytest diagnostic extraction failed (exit=%s)\n' \
			"$$counts_status" >&2; \
		cat "$$counts_file" >&2; \
		exit "$$counts_status"; \
	fi; \
	if ! awk ' \
		BEGIN { required["failed_count"]; required["error_count"]; required["warning_count"]; required["skipped_count"] } \
		$$0 !~ /^(failed_count|error_count|warning_count|skipped_count)=[0-9]+$$/ { invalid=1; next } \
		{ split($$0, fields, "="); if (seen[fields[1]]++) invalid=1 } \
		END { if (NR != 4) invalid=1; for (key in required) if (seen[key] != 1) invalid=1; exit invalid } \
	' "$$counts_file"; then \
		echo "ERROR: invalid pytest diagnostic counts contract" >&2; \
		cat "$$counts_file" >&2; \
		exit 2; \
	fi; \
	. "$$counts_file"; \
	if [ "$$_coverage_required" -eq 1 ]; then \
		failures="$${failed_count:-0}"; errors="$${error_count:-0}"; \
		skipped="$${skipped_count:-0}"; \
		passed=$$((tests - failures - errors - skipped)); \
		if [ "$$passed" -lt 0 ]; then passed=0; fi; \
		printf 'junit=%s\ncoverage=%s\ntotal=%s\npassed=%s\nfailed=%s\nerrors=%s\nskipped=%s\nduration_seconds=%s\n' \
			"$$junit_file" "$$_coverage_value" "$$tests" "$$passed" "$$failures" \
			"$$errors" "$$skipped" "$$duration" > "$$summary_file"; \
	fi; \
	if [ "$${failed_count:-0}" -gt 0 ] || [ "$${error_count:-0}" -gt 0 ] || \
		[ "$${warning_count:-0}" -gt 0 ] || [ "$${skipped_count:-0}" -gt 0 ]; then \
		if [ "$$rc" -eq 0 ]; then rc=1; fi; \
	fi; \
	if [ "$(DIAG)" = "1" ]; then \
		run_state=COMPLETED; \
		if [ "$$rc" -eq 130 ]; then run_state=INTERRUPTED; fi; \
		printf 'DIAG %s | failed=%s errors=%s warnings=%s skipped=%s\n' \
			"$$run_state" "$$failed_count" "$$error_count" \
			"$$warning_count" "$$skipped_count" >&2; \
	fi; \
	ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
	printf 'Reports: %s (latest: %s/latest)\n' \
		"$$report_dir" "$(PYTEST_REPORTS_DIR)" >&2; \
	exit "$$rc"

val: ## Run validate gates (VALIDATE_GATES=complexity,docstring to select, FIX=1)
	$(call _run_verb_hooks,pre,val,$(WHAT))
	$(call _run_verb_body,val,_val_impl)
	$(call _run_verb_hooks,post,val,$(WHAT))

_val_impl:
	$(Q)if [ -n "$(FIX)" ] && [ "$(FIX)" != "1" ]; then \
		echo "ERROR: FIX must be empty or 1, got '$(FIX)'"; \
		exit 1; \
	fi
	$(Q)if [ "$(FIX)" = "1" ]; then $(UV) run ruff check --fix . --quiet; fi
	$(Q)gates="$(VALIDATE_GATES)"; \
	if [ -n "$$gates" ]; then \
		for g in $$(echo "$$gates" | tr ',' ' '); do \
			case "$$g" in \
				complexity|docstring) ;; \
				*) echo "ERROR: unknown VALIDATE_GATES value '$$g' (allowed: complexity,docstring)"; exit 2;; \
			esac; \
		done; \
	else \
		gates="complexity,docstring"; \
	fi; \
	if echo "$$gates" | grep -qw complexity; then \
		$(UV) run radon cc $(SRC_DIR) -n E -a --total-average; \
		$(UV) run radon mi $(SRC_DIR) -n C -s --sort; \
	fi; \
	if echo "$$gates" | grep -qw docstring; then \
		$(PROJECT_INFRA_DOCS) audit --workspace . --checks docstrings --docstring-min $(DOCSTRING_MIN) --output-dir .reports/docs; \
	fi

run: ## Run a project-specific action (WHAT=<action> -> _custom_run_<action> in custom.mk)
	$(call _run_verb_hooks,pre,run,$(WHAT))
	$(call _run_custom_what,run,$(WHAT))
	$(call _run_verb_hooks,post,run,$(WHAT))

daemon-start-mypy: ## Start dmypy daemon for this project
	$(Q)mkdir -p .dmypy
	$(Q)$(VALIDATE_MYPY_LIMITS); if $(MYPY_BOUNDED) $(VENV_PYTHON) -m mypy.dmypy --status-file "$(DMPY_SOCKET)" status >/dev/null 2>&1; then \
		echo "dmypy already running for $(PROJECT_NAME) at $(DMPY_SOCKET)"; \
	else \
		$(MYPY_BOUNDED) $(VENV_PYTHON) -m mypy.dmypy --status-file "$(DMPY_SOCKET)" start --timeout "$(MYPY_TIMEOUT_SECONDS)" -- --config-file "$(WORKSPACE_ROOT)/pyproject.toml" || { $(REPORT_MYPY_FAILURE); exit $$code; }; \
	fi

daemon-stop-mypy: ## Stop dmypy daemon for this project
	$(Q)$(VALIDATE_MYPY_LIMITS); if $(MYPY_BOUNDED) $(VENV_PYTHON) -m mypy.dmypy --status-file "$(DMPY_SOCKET)" status; then \
		$(MYPY_BOUNDED) $(VENV_PYTHON) -m mypy.dmypy --status-file "$(DMPY_SOCKET)" stop || { $(REPORT_MYPY_FAILURE); exit $$code; }; \
	else \
		echo "dmypy daemon is not running"; \
	fi
	$(Q)rm -f "$(DMPY_SOCKET)"

daemon-status-mypy: ## Show dmypy daemon status for this project
	$(Q)$(VALIDATE_MYPY_LIMITS); if $(MYPY_BOUNDED) $(VENV_PYTHON) -m mypy.dmypy --status-file "$(DMPY_SOCKET)" status; then \
		: ; \
	else \
		echo "dmypy daemon is not running"; \
	fi

daemon-start-pyright: ## Start pyright daemon in watch mode
	$(Q)mkdir -p .pyright
	$(Q)if [ -f "$(PYRIGHT_PIDFILE)" ]; then \
		pid=$$(cat "$(PYRIGHT_PIDFILE)"); \
		if [ -n "$$pid" ] && kill -0 "$$pid" >/dev/null 2>&1; then \
			echo "Pyright daemon already running (PID $$pid)"; \
			exit 0; \
		fi; \
		rm -f "$(PYRIGHT_PIDFILE)"; \
	fi
	$(Q)nohup pyright --watch --threads > "$(PYRIGHT_LOG)" 2>&1 & \
		pid=$$!; \
		echo "$$pid" > "$(PYRIGHT_PIDFILE)"; \
		echo "Pyright daemon started (PID $$pid), log: $(PYRIGHT_LOG)"

daemon-stop-pyright: ## Stop pyright daemon
	$(Q)if [ ! -f "$(PYRIGHT_PIDFILE)" ]; then \
		echo "Pyright daemon is not running"; \
		exit 0; \
	fi
	$(Q)pid=$$(cat "$(PYRIGHT_PIDFILE)"); \
		if [ -n "$$pid" ] && kill -0 "$$pid"; then \
			kill "$$pid"; \
			echo "Stopped pyright daemon (PID $$pid)"; \
	else \
		echo "Pyright daemon PID file was stale"; \
	fi; \
	rm -f "$(PYRIGHT_PIDFILE)"

daemon-status-pyright: ## Show pyright daemon status
	$(Q)if [ ! -f "$(PYRIGHT_PIDFILE)" ]; then \
		echo "Pyright daemon is not running"; \
	else \
		pid=$$(cat "$(PYRIGHT_PIDFILE)"); \
		if [ -n "$$pid" ] && kill -0 "$$pid"; then \
			echo "Pyright daemon running (PID $$pid), log: $(PYRIGHT_LOG)"; \
		else \
			echo "Pyright daemon not running (stale PID file cleaned)"; \
			rm -f "$(PYRIGHT_PIDFILE)"; \
		fi; \
	fi

daemon-start: daemon-start-mypy daemon-start-pyright ## Start all daemons

daemon-stop: daemon-stop-mypy daemon-stop-pyright ## Stop all daemons

daemon-status: ## Show status of all daemons
	$(Q)echo "== dmypy =="; \
	$(MAKE) daemon-status-mypy; \
	echo "== pyright =="; \
	$(MAKE) daemon-status-pyright

daemon-restart: daemon-stop daemon-start ## Restart all daemons

pr: ## Manage pull requests for this repository
	$(Q)$(PROJECT_INFRA_GITHUB) pr \
		--repo-root "$(CURDIR)" \
		--action "$(PR_ACTION)" \
		$(if $(PR_BASE),--base "$(PR_BASE)",) \
		$(if $(PR_HEAD),--head "$(PR_HEAD)",) \
		$(if $(PR_TITLE),--title "$(PR_TITLE)",) \
		$(if $(PR_BODY),--body "$(PR_BODY)",) \
		$(if $(filter 1,$(PR_DRAFT)),--draft,--no-draft)

clean: ## Clean artifacts
	$(Q)rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage* \
		.mypy_cache/ .pyrefly_cache/ .ruff_cache/ $(LINT_CACHE_DIR)/ \
		.pyright/ .pytype/ .pyrefly-report.json .pyrefly-output.txt
	$(Q)find . -type d -name __pycache__ -exec rm -rf {} +
	$(Q)find . -type f -name "*.pyc" -delete
	$(Q)echo "Clean complete: $(PROJECT_NAME)"
