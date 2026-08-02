# @flext-managed: continuous
# @flext-regenerate: make codegen WHAT=apply APPLY=Y
# @flext-ssot: flext-infra/config/codegen.yaml + flext-infra/src/flext_infra/templates/project/base/Makefile.j2
# @flext-maintenance: do not edit generated projections; edit the SSOT and regenerate
# flext-infra — generated project interface.
# Managed by flext-infra codegen conform for new and existing repositories.

SHELL := /bin/sh
.DEFAULT_GOAL := help

PROJECT_NAME := flext-infra
MAKE_PROFILE := standalone
WORKSPACE_ROOT_REL := .
WORKSPACE_MEMBERS :=
WORKSPACE_EDITABLES := $(PROJECT_NAME):.
UV_LINK_MODE := copy

APPLY ?= N
ARGS ?=
CHECK_GATES ?=
FAIL_FAST ?= 0
FILE ?=
FILES ?=
FIX ?= 0
MATCH ?=
PROJECT ?=
PROJECTS ?=
BASE ?=
BRANCH ?=
# Public selector documented by base.mk. Forwarded to the test recipe so a
# focused run stays inside the canonical Make surface instead of forcing a
# loose pytest invocation.
PYTEST_ARGS ?=
PYTEST_TARGETS ?=
PYTEST_DIAG_ARGS ?= -rA --durations=0 --tb=long --showlocals
PYTEST_REPORT_ARGS ?= -ra --durations=25 --durations-min=0.001 --tb=short
PYTEST_REPORTS_DIR ?= .reports/tests
TEST_ITEM_TIMEOUT_SECONDS ?= 10
TEST_SESSION_TIMEOUT_SECONDS ?= 60
TEST_SHARD_COUNT ?= 16
TEST_SHARD_PARALLELISM ?= 2
WHAT ?=

PROJECT_ROOT := $(shell pwd -P)
SELF_MAKEFILE := $(abspath $(firstword $(MAKEFILE_LIST)))
MAKEFILE_ROOT := $(patsubst %/,%,$(dir $(SELF_MAKEFILE)))
WORKSPACE ?= $(PROJECT_ROOT)
PUBLIC_VERBS := help setup deps build check test fmt run status docs clean release codegen worktree basemk
CHECK_GATES_ALLOWED := lint format pyrefly mypy pyright security markdown smells
CHECK_GATES_DEFAULT := lint format pyrefly mypy pyright security markdown smells
DOCS_PHASES := generate fix audit build validate
SERIALIZED_VERBS := check test codegen
SERIALIZED_TARGETS := _serialized_check _serialized_test _serialized_codegen
RUFF_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests
FMT_PATHS := $(if $(strip $(FILES) $(FILE)),$(strip $(FILES) $(FILE)),$(RUFF_PATHS))
MYPY_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests
UV ?= uv
UV_REQUESTED := $(UV)
CALLER_PATH := $(PATH)
CALLER_VIRTUAL_ENV := $(patsubst %/,%,$(VIRTUAL_ENV))

# === MYPY RESOURCE LIMIT ===
# mro-0ftd.3.11: every Mypy process inherits validated memory and time caps.
MYPY_MEMORY_LIMIT_MB ?= 6144
MYPY_TIMEOUT_SECONDS ?= 600
MYPY_BOUNDED = timeout --signal=TERM --kill-after=5s "$(MYPY_TIMEOUT_SECONDS)s" prlimit --as=$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )):$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )) --
VALIDATE_MYPY_LIMITS = case "$(MYPY_MEMORY_LIMIT_MB)" in ""|*[!0-9]*) echo "ERROR: MYPY_MEMORY_LIMIT_MB must be a positive integer"; exit 2;; esac; [ "$(MYPY_MEMORY_LIMIT_MB)" -gt 0 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be greater than zero"; exit 2; }; [ "$(MYPY_MEMORY_LIMIT_MB)" -le 6144 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be less than or equal to 6144"; exit 2; }; case "$(MYPY_TIMEOUT_SECONDS)" in ""|*[!0-9]*) echo "ERROR: MYPY_TIMEOUT_SECONDS must be a positive integer"; exit 2;; esac; [ "$(MYPY_TIMEOUT_SECONDS)" -gt 0 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be greater than zero"; exit 2; }; [ "$(MYPY_TIMEOUT_SECONDS)" -le 600 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be less than or equal to 600"; exit 2; }; command -v timeout >/dev/null 2>&1 || { echo "ERROR: required executable not found: timeout"; exit 2; }; command -v prlimit >/dev/null 2>&1 || { echo "ERROR: required executable not found: prlimit"; exit 2; }
REPORT_MYPY_FAILURE = code=$$?; signal=none; if [ "$$code" -ge 128 ]; then signal=$$(( $$code - 128 )); fi; if [ "$$code" -eq 124 ] || [ "$$signal" != none ]; then reason="resource limit triggered"; else reason="type check failed under enforced limits"; fi; echo "ERROR: Mypy $$reason: memory_limit=$(MYPY_MEMORY_LIMIT_MB) MiB; timeout=$(MYPY_TIMEOUT_SECONDS)s; exit=$$code; signal=$$signal" >&2
export MYPY_MEMORY_LIMIT_MB MYPY_TIMEOUT_SECONDS


_DEFAULT_help := usage
_DEFAULT_deps := check
_DEFAULT_build := artifacts
_DEFAULT_check := all
_DEFAULT_test := all
_DEFAULT_fmt := check
_DEFAULT_run := default
_DEFAULT_status := diagnostics
_DEFAULT_docs := check
_DEFAULT_clean := generated
_DEFAULT_release := status
_DEFAULT_codegen := check
_DEFAULT_worktree := list
_DEFAULT_basemk := generate


ifneq ($(filter $(MAKE_PROFILE),workspace-root workspace-member standalone),$(MAKE_PROFILE))
$(error Invalid MAKE_PROFILE '$(MAKE_PROFILE)')
endif

ifeq ($(MAKE_PROFILE),workspace-member)
DECLARED_WORKSPACE_ROOT := $(shell cd "$(PROJECT_ROOT)/$(WORKSPACE_ROOT_REL)" 2>/dev/null && pwd -P)
SUPERPROJECT_ROOT_RAW := $(shell git rev-parse --show-superproject-working-tree 2>/dev/null)
SUPERPROJECT_ROOT := $(shell test -n "$(SUPERPROJECT_ROOT_RAW)" && cd "$(SUPERPROJECT_ROOT_RAW)" 2>/dev/null && pwd -P)
ifeq ($(SUPERPROJECT_ROOT),$(DECLARED_WORKSPACE_ROOT))
ATTACHED_MEMBER := Y
RUNTIME_ROOT := $(DECLARED_WORKSPACE_ROOT)
else
ATTACHED_MEMBER := N
RUNTIME_ROOT := $(PROJECT_ROOT)
endif
else
ATTACHED_MEMBER := N
RUNTIME_ROOT := $(PROJECT_ROOT)
endif

RUNTIME_VENV := $(RUNTIME_ROOT)/.venv
FLEXT_INFRA_RUNTIME_ROOT := $(if $(filter $(MAKEFILE_ROOT),$(PROJECT_ROOT)),$(RUNTIME_ROOT),$(MAKEFILE_ROOT))
ifeq ($(OS),Windows_NT)
RUNTIME_BIN := $(RUNTIME_VENV)/Scripts
RUNTIME_PYTHON := $(RUNTIME_BIN)/python.exe
FLEXT_INFRA_RUNTIME_PYTHON := $(FLEXT_INFRA_RUNTIME_ROOT)/.venv/Scripts/python.exe
NORMALIZED_CALLER_PATH := $(shell cygpath --path "$(CALLER_PATH)" 2>/dev/null)
NORMALIZED_CALLER_VIRTUAL_ENV := $(shell cygpath --unix "$(CALLER_VIRTUAL_ENV)" 2>/dev/null)
CALLER_VIRTUAL_ENV_BIN := $(NORMALIZED_CALLER_VIRTUAL_ENV)/Scripts
else
RUNTIME_BIN := $(RUNTIME_VENV)/bin
RUNTIME_PYTHON := $(RUNTIME_BIN)/python
FLEXT_INFRA_RUNTIME_PYTHON := $(FLEXT_INFRA_RUNTIME_ROOT)/.venv/bin/python
NORMALIZED_CALLER_PATH := $(CALLER_PATH)
NORMALIZED_CALLER_VIRTUAL_ENV := $(CALLER_VIRTUAL_ENV)
CALLER_VIRTUAL_ENV_BIN := $(NORMALIZED_CALLER_VIRTUAL_ENV)/bin
endif
SANITIZED_CALLER_PATH := $(NORMALIZED_CALLER_PATH)
ifneq ($(strip $(NORMALIZED_CALLER_VIRTUAL_ENV)),)
SANITIZED_CALLER_PATH := $(subst $(CALLER_VIRTUAL_ENV_BIN):,,$(SANITIZED_CALLER_PATH))
SANITIZED_CALLER_PATH := $(subst :$(CALLER_VIRTUAL_ENV_BIN),,$(SANITIZED_CALLER_PATH))
ifeq ($(SANITIZED_CALLER_PATH),$(CALLER_VIRTUAL_ENV_BIN))
SANITIZED_CALLER_PATH :=
endif
endif
RESOLVED_UV := $(shell PATH="$(SANITIZED_CALLER_PATH)" command -v "$(UV_REQUESTED)" 2>/dev/null)
ifeq ($(strip $(RESOLVED_UV)),)
$(error Required uv executable not found: $(UV_REQUESTED))
endif
override UV := $(RESOLVED_UV)
override FLEXT_INFRA_PYTHON := $(FLEXT_INFRA_RUNTIME_PYTHON)
# A workspace member shares RUNTIME_VENV with its workspace, while dependency
# resolution remains anchored to this lane's checked-out project metadata.
override UV_PROJECT := $(PROJECT_ROOT)
override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)
override VIRTUAL_ENV := $(RUNTIME_VENV)
override PATH := $(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)
export FLEXT_INFRA_PYTHON UV UV_PROJECT UV_PROJECT_ENVIRONMENT VIRTUAL_ENV PATH

ifeq ($(MAKE_PROFILE),workspace-root)
CODEGEN_SCOPE := all
ALLOWED_PROJECTS := . $(WORKSPACE_MEMBERS)
else
CODEGEN_SCOPE := self
ALLOWED_PROJECTS := .
endif

# Workspace-root gate verbs fan out across declared members through the generic
# `flext-infra workspace orchestrate` primitive (verb allowlist + CLI group come
# from the constants SSOT, never hardcoded here). Members and standalone projects
# run the gate locally. FAIL_FAST forwards the stop-on-first-failure policy.
WORKSPACE_ORCHESTRATE = $(UV_RUN) python -m flext_infra workspace orchestrate
REQUESTED_PROJECTS := $(strip $(if $(PROJECT),$(PROJECT),$(PROJECTS)))
FILE_MEMBER := $(firstword $(foreach member,$(WORKSPACE_MEMBERS),$(if $(filter $(member)/%,$(FILE)),$(member))))
FILE_PROJECT := $(if $(strip $(FILE_MEMBER)),$(FILE_MEMBER),.)
FILE_RELATIVE := $(if $(filter .,$(FILE_PROJECT)),$(FILE),$(patsubst $(FILE_PROJECT)/%,%,$(FILE)))
DEFAULT_PROJECTS := $(WORKSPACE_MEMBERS) .
SELECTED_PROJECTS := $(if $(strip $(FILE)),$(FILE_PROJECT),$(if $(strip $(REQUESTED_PROJECTS)),$(REQUESTED_PROJECTS),$(DEFAULT_PROJECTS)))
WORKSPACE_PROJECT_ARGS := $(foreach project,$(SELECTED_PROJECTS),--projects $(project))
WORKSPACE_CHECK_ARGS := $(if $(strip $(CHECK_GATES)),--make-arg "CHECK_GATES=$(strip $(CHECK_GATES))")
WORKSPACE_TEST_ARGS := $(if $(strip $(FILE)),--make-arg "FILE=$(FILE_RELATIVE)") $(if $(strip $(MATCH)),--make-arg "MATCH=$(MATCH)") $(if $(strip $(PYTEST_ARGS)),--make-arg "PYTEST_ARGS=$(strip $(PYTEST_ARGS))")
DOCS_PROJECT_ARGS := $(foreach project,$(REQUESTED_PROJECTS),--projects $(project))
ORCHESTRATED_VERBS := build check clean docs scan test val

UV_RUN := env -u PYTHONPATH -u MYPYPATH $(UV) run --project "$(PROJECT_ROOT)" --no-sync
PROJECT_INFRA_PYTHONPATH ?= $(MAKEFILE_ROOT)/src
PROJECT_FLEXT_INFRA := test -x "$(FLEXT_INFRA_PYTHON)" || { printf 'ERROR: FLEXT_INFRA_PYTHON must name an executable managed Python\n' >&2; exit 2; }; env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(dir $(FLEXT_INFRA_PYTHON)):$(SANITIZED_CALLER_PATH)" PYTHONPATH="$(PROJECT_INFRA_PYTHONPATH)" $(FLEXT_INFRA_PYTHON) -m flext_infra
# mro-j47u (codex): scaffold dev tools live in the validated optional dev
# profile; a fresh project must create its lock before later check-mode locks.
UV_SYNC_FLAGS := --all-extras --all-groups

ifneq ($(strip $(PROJECT)),)
ifneq ($(strip $(PROJECTS)),)
$(error ERROR: Cannot use PROJECT and PROJECTS together)
endif
endif


-include custom.mk

_BUILTIN_HANDLERS := \
	_builtin_help_usage \
	_builtin_deps_check \
	_builtin_deps_lock \
	_builtin_deps_upgrade \
	_builtin_build_artifacts \
	_builtin_check_all \
	_builtin_test_all \
	_builtin_fmt_check \
	_builtin_fmt_apply \
	_builtin_run_default \
	_builtin_status_diagnostics \
	_builtin_docs_check \
	_builtin_docs_all \
_builtin_docs_generate \
_builtin_docs_fix \
_builtin_docs_audit \
_builtin_docs_build \
_builtin_docs_validate \
_builtin_clean_generated \
	_builtin_release_status \
	_builtin_codegen_check \
	_builtin_codegen_apply \
	_builtin_worktree_list \
	_builtin_worktree_add \
	_builtin_worktree_update \
	_builtin_worktree_remove

SELF_MAKE := $(MAKE) --no-print-directory -f "$(SELF_MAKEFILE)"

define _dispatch
	@what="$(strip $(WHAT))"; \
	if [ -z "$$what" ]; then what="$(_DEFAULT_$(1))"; fi; \
	case "$$what" in \
		*[!a-z0-9_-]*|'') printf 'ERROR: invalid WHAT selector %s\n' "$$what" >&2; exit 2 ;; \
	esac; \
	builtin="_builtin_$(1)_$$what"; \
	custom="_custom_$(1)_$$what"; \
	for hook in "pre-$(1)" "pre-$(1)-$$what"; do \
		$(SELF_MAKE) -q "$$hook" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then $(SELF_MAKE) "$$hook" || exit $$?; fi; \
	done; \
	case " $(_BUILTIN_HANDLERS) " in \
		*" $$builtin "*) $(SELF_MAKE) "$$builtin" || exit $$? ;; \
		*) $(SELF_MAKE) "$$custom" || exit $$? ;; \
	esac; \
	for hook in "post-$(1)-$$what" "post-$(1)"; do \
		$(SELF_MAKE) -q "$$hook" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then $(SELF_MAKE) "$$hook" || exit $$?; fi; \
	done
endef

define _require_apply
	@if [ "$(APPLY)" != "Y" ]; then \
		printf 'ERROR: this action requires APPLY=Y\n' >&2; \
		exit 2; \
	fi
endef

define _run_for_selected_projects
	@set -eu; \
	selected="$(strip $(if $(PROJECT),$(PROJECT),$(PROJECTS)))"; \
	if [ -z "$$selected" ]; then selected="."; fi; \
	for project in $$selected; do \
		case " $(ALLOWED_PROJECTS) " in \
			*" $$project "*) ;; \
			*) printf 'ERROR: undeclared project %s\n' "$$project" >&2; exit 2 ;; \
		esac; \
		$(UV) lock --project "$(PROJECT_ROOT)/$$project" $(1); \
	done
endef

.PHONY: $(PUBLIC_VERBS) $(SERIALIZED_TARGETS) $(_BUILTIN_HANDLERS)

$(filter-out setup $(SERIALIZED_VERBS),$(PUBLIC_VERBS)):
	$(call _dispatch,$@)


check: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "check"

_serialized_check:
	$(call _dispatch,check)


test: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "test"

_serialized_test:
	$(call _dispatch,test)


codegen: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "codegen"

_serialized_codegen:
	$(call _dispatch,codegen)



setup:
	@if [ -n "$(strip $(WHAT))" ]; then printf 'ERROR: setup does not accept WHAT\n' >&2; exit 2; fi
	@$(SELF_MAKE) _builtin_setup_environment

_builtin_help_usage:
	@printf '%s\n' 'flext-infra [standalone]' '';


	@printf '  %-10s WHAT=%s\n' 'help' 'usage';



	@printf '  %-10s\n' 'setup';



	@printf '  %-10s WHAT=%s\n' 'deps' 'check';



	@printf '  %-10s WHAT=%s\n' 'build' 'artifacts';



	@printf '  %-10s WHAT=%s\n' 'check' 'all';



	@printf '  %-10s WHAT=%s\n' 'test' 'all';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'fmt' 'check';



	@printf '  %-10s WHAT=%s\n' 'run' 'default';



	@printf '  %-10s WHAT=%s\n' 'status' 'diagnostics';



	@printf '  %-10s WHAT=%s\n' 'docs' 'check';



	@printf '  %-10s WHAT=%s\n' 'clean' 'generated';



	@printf '  %-10s WHAT=%s\n' 'release' 'status';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'codegen' 'check';



	@printf '  %-10s WHAT=%s\n' 'worktree' 'list';


	@printf '  %-10s WHAT=%s\n' 'basemk' 'generate';

	@printf '  %-10s %s\n' 'WORKSPACE' 'target repository (default: current project)';
	@printf '  %-10s %s\n' 'BASE' 'required for worktree add/update';
	@printf '  %s\n' 'TEST_ITEM_TIMEOUT_SECONDS=$(TEST_ITEM_TIMEOUT_SECONDS)  Per-item pytest deadline';
	@printf '  %s\n' 'TEST_SESSION_TIMEOUT_SECONDS=$(TEST_SESSION_TIMEOUT_SECONDS)  Whole pytest process deadline';
	@printf '  %s\n' 'TEST_SHARD_COUNT=$(TEST_SHARD_COUNT)  Deterministic full-suite partitions';
	@printf '  %s\n' 'TEST_SHARD_PARALLELISM=$(TEST_SHARD_PARALLELISM)  Concurrent full-suite partitions';
	@printf '\n%s\n' 'Custom hooks (custom.mk):';
	@printf '  %s\n' 'Define pre-<verb>, post-<verb>, pre-<verb>-<what>, post-<verb>-<what>';
	@printf '  %s\n' 'in custom.mk to run extra steps at the start or end of any verb,';
	@printf '  %s\n' 'for all or some WHATs. Add _custom_<verb>_<what> to define a new WHAT.';
	@if [ -f custom.mk ]; then \
		hooks=$$(grep -oE '^(pre|post)-[a-z][a-z0-9-]*|^_custom_[a-z][a-z0-9_-]*' custom.mk 2>/dev/null | sort -u); \
		if [ -n "$$hooks" ]; then \
			printf '  %s\n' 'Defined in this project:'; \
			for hook in $$hooks; do printf '    %s\n' "$$hook"; done; \
		fi; \
	fi

# A project owns the sources it declares. Setup makes the tree exactly what the
# manifest declares, using nothing outside the tree: every declared submodule is
# initialised recursively at its recorded gitlink and placed on the branch
# declared in .gitmodules. It is a no-op when the project declares no
# submodules, and it converges on re-run. It never moves a branch that holds
# work the superproject does not record: that is an error, never a warning, so
# setup can never report success over a tree that is not what it declares.
_builtin_setup_submodules:
	@set -eu; \
	if [ ! -f "$(PROJECT_ROOT)/.gitmodules" ]; then exit 0; fi; \
	git -C "$(PROJECT_ROOT)" submodule sync --recursive --quiet; \
	git -C "$(PROJECT_ROOT)" submodule update --init --recursive; \
	git -C "$(PROJECT_ROOT)" submodule foreach --recursive --quiet ' \
		branch=$$(git config -f "$$toplevel/.gitmodules" --get --default "" "submodule.$$name.branch"); \
		if [ -z "$$branch" ]; then exit 0; fi; \
		if ! git rev-parse --verify --quiet "refs/heads/$$branch" >/dev/null; then \
			git checkout --quiet -b "$$branch"; \
		elif [ "$$(git rev-parse "refs/heads/$$branch")" = "$$(git rev-parse HEAD)" ]; then \
			git checkout --quiet "$$branch"; \
		else \
			printf "ERROR: %s: branch %s is at %s but the superproject records %s\n" "$$name" "$$branch" "$$(git rev-parse --short "refs/heads/$$branch")" "$$(git rev-parse --short HEAD)" >&2; \
			printf "Reconcile that branch with the recorded gitlink, then re-run setup\n" >&2; \
			exit 1; \
		fi'

_builtin_require_environment:
	@if [ ! -x "$(RUNTIME_PYTHON)" ]; then \
		printf 'ERROR: missing environment interpreter %s; make setup creates it\n' "$(RUNTIME_PYTHON)" >&2; \
		exit 2; \
	fi

ifeq ($(MAKE_PROFILE),workspace-root)
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --link-mode "$(UV_LINK_MODE)"
	@$(UV) pip check --python "$(RUNTIME_VENV)"
else ifeq ($(MAKE_PROFILE),workspace-member)
ifeq ($(ATTACHED_MEMBER),Y)
_builtin_setup_environment: _builtin_setup_submodules
	@$(SELF_MAKE) -C "$(RUNTIME_ROOT)" _builtin_setup_environment
else
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --link-mode "$(UV_LINK_MODE)"
endif
else
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --link-mode "$(UV_LINK_MODE)"
endif

_builtin_deps_check: _builtin_require_environment
	$(call _run_for_selected_projects,--check)

_builtin_deps_lock:
	$(call _require_apply)
	$(call _run_for_selected_projects,)

_builtin_deps_upgrade: _builtin_require_environment
	$(call _require_apply)
	$(call _run_for_selected_projects,--upgrade)
	@set -eu; \
	selected="$(strip $(PROJECTS))"; \
	if [ -z "$$selected" ]; then selected="."; fi; \
	set --; \
	for project in $$selected; do set -- "$$@" --projects "$$project"; done; \
	$(PROJECT_FLEXT_INFRA) deps modernize --workspace "$(PROJECT_ROOT)" \
		--apply --rewrite-constraints --skip-check "$$@"
	$(call _run_for_selected_projects,)


_builtin_build_artifacts:
	@$(UV) build --project "$(PROJECT_ROOT)"

_builtin_check_all: _builtin_require_environment
	@set -eu; \
	if [ "$(FIX)" = "1" ] && [ "$(APPLY)" != "Y" ]; then \
		printf 'ERROR: FIX=1 requires APPLY=Y\n' >&2; exit 2; \
	fi; \
	gates="$(strip $(CHECK_GATES))"; \
	if [ -z "$$gates" ]; then gates="$$(printf '%s' '$(CHECK_GATES_DEFAULT)' | tr ' ' ',')"; fi; \
	gates="$$(printf '%s' "$$gates" | tr -d '[:space:]')"; \
	for gate in $$(printf '%s' "$$gates" | tr ',' ' '); do \
		case " $(CHECK_GATES_ALLOWED) " in *" $$gate "*) ;; \
			*) printf 'ERROR: unknown CHECK_GATES value: %s (allowed: %s)\n' "$$gate" "$(CHECK_GATES_ALLOWED)" >&2; exit 2 ;; \
		esac; \
	done; \
	$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "$$gates" --projects . $(if $(filter 1,$(FIX)),--fix)

_builtin_test_all: _builtin_require_environment

	@_files="$(strip $(FILES))"; \
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
		if [ -n "$$_files" ]; then \
			printf 'ERROR: FILE and FILES cannot be combined\n' >&2; exit 2; \
		fi; \
		case "$(FILE)" in /*|..|../*|*/../*|*/..) \
			printf 'ERROR: FILE must be a repository-relative path\n' >&2; exit 2 ;; \
		esac; \
		_files="$(FILE)"; \
	fi; \
	_pytest_targets="$(PYTEST_TARGETS)"; \
	_pytest_run="$$_pytest_targets"; \
	if [ -n "$$_files" ]; then _pytest_run="$$_files"; fi; \
	for target in $$_pytest_run; do \
		if [ ! -e "$$target" ]; then \
			printf 'ERROR: test target does not exist: %s\n' "$$target" >&2; exit 2; \
		fi; \
	done; \
	_all_pytest_args="$(PYTEST_ARGS)"; \
	_pytest_arg_value=0; \
	for _pytest_arg in $$_all_pytest_args; do \
		if [ "$$_pytest_arg_value" -eq 1 ]; then _pytest_arg_value=0; continue; fi; \
		case "$$_pytest_arg" in \
			--timeout|--timeout=*|--timeout-method|--timeout-method=*|--junitxml|--junitxml=*|--cov|--cov=*|--no-cov|--collect-only|--basetemp|--basetemp=*|--ignore|--ignore=*|--deselect|--deselect=*|-p|-p*|--override-ini|--override-ini=*|-m|--markers|--lf|--last-failed|--ff|--failed-first|--new-first) \
				printf 'ERROR: PYTEST_ARGS may not override Make test controls: %s\n' "$$_pytest_arg" >&2; exit 2 ;; \
			-k|--keyword|--tb|--maxfail|--capture) _pytest_arg_value=1 ;; \
			--keyword=*|--tb=*|--maxfail=*|--capture=*|-v|-vv|-q|-x|--exitfirst|--disable-warnings|--show-capture=*) : ;; \
			-*) : ;; \
			*) printf 'ERROR: PYTEST_ARGS may not add test targets: %s\n' "$$_pytest_arg" >&2; exit 2 ;; \
		esac; \
	done; \
	if [ "$$_pytest_arg_value" -eq 1 ]; then \
		printf 'ERROR: PYTEST_ARGS option requires a value\n' >&2; exit 2; \
	fi; \
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
	if [ -n "$$_files" ] || [ -n "$(MATCH)" ] || \
		[ -n "$$_pytest_targets" ]; then \
		_coverage_args="--no-cov"; \
		_coverage_required=0; \
		_coverage_value="not-generated"; \
	fi; \
	_diag_inputs=""; \
	_junit_inputs=""; \
	if [ "$$_coverage_required" -eq 1 ]; then \
		plan_dir="$$report_dir/shard-plan"; \
		plan_log="$$report_dir/pytest-plan.log"; \
		mkdir -p "$$plan_dir"; \
		printf '%s\n' '$(UV_RUN) python -m pytest' \
			"$$_pytest_run --collect-only -p flext_infra.pytest_shard" \
			"--flext-shard-count=$(TEST_SHARD_COUNT) --flext-shard-plan-dir=$$plan_dir" \
			"--timeout=$(TEST_ITEM_TIMEOUT_SECONDS) --timeout-method=signal" \
			"$$_all_pytest_args" > "$$command_file"; \
		timeout --signal=TERM \
			--kill-after=5s \
			"$(TEST_SESSION_TIMEOUT_SECONDS)s" \
			$(UV_RUN) python -m pytest $$_pytest_run --collect-only -q --no-cov \
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
			duration=$$(( $$(date +%s) - session_started_epoch )); \
			printf 'status=incomplete\njunit=not-combined\ncoverage=not-generated\ntotal=0\npassed=0\nfailed=0\nerrors=0\nskipped=0\nduration_seconds=%s\n' "$$duration" > "$$summary_file"; \
			ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
			exit "$${rc:-2}"; \
		fi; \
		effective_shard_count=$$(find "$$plan_dir" -maxdepth 1 -type f -name 'shard-*.expected.txt' | wc -l | tr -d ' '); \
		case "$$effective_shard_count" in ""|*[!0-9]*) \
			printf 'ERROR: pytest shard plan has an invalid effective count\n' >&2; exit 2 ;; \
		esac; \
		if [ "$$effective_shard_count" -le 0 ] || \
			[ "$$effective_shard_count" -gt "$(TEST_SHARD_COUNT)" ]; then \
			printf 'ERROR: pytest shard plan has an invalid effective count: %s\n' "$$effective_shard_count" >&2; exit 2; \
		fi; \
		effective_shard_parallelism="$(TEST_SHARD_PARALLELISM)"; \
		if [ "$$effective_shard_parallelism" -gt "$$effective_shard_count" ]; then \
			effective_shard_parallelism="$$effective_shard_count"; \
		fi; \
		shard_index=0; \
		while [ "$$shard_index" -lt "$$effective_shard_count" ]; do \
			expected="$$plan_dir/shard-$$shard_index.expected.txt"; \
			if [ ! -s "$$expected" ]; then \
				printf 'ERROR: pytest shard plan is missing or empty: %s\n' \
					"$$expected" >&2; \
				duration=$$(( $$(date +%s) - session_started_epoch )); \
				printf 'status=incomplete\njunit=not-combined\ncoverage=not-generated\ntotal=0\npassed=0\nfailed=0\nerrors=0\nskipped=0\nduration_seconds=%s\n' "$$duration" > "$$summary_file"; \
				ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; exit 2; \
			fi; \
			shard_index=$$((shard_index + 1)); \
		done; \
		: > "$$log_file"; \
		rc=0; \
		batch_start=0; \
		while [ "$$batch_start" -lt "$$effective_shard_count" ]; do \
			batch_end=$$((batch_start + effective_shard_parallelism)); \
			if [ "$$batch_end" -gt "$$effective_shard_count" ]; then \
				batch_end="$$effective_shard_count"; \
			fi; \
			shard_index="$$batch_start"; \
			pids=""; \
			while [ "$$shard_index" -lt "$$batch_end" ]; do \
				expected="$$plan_dir/shard-$$shard_index.expected.txt"; \
				actual="$$plan_dir/shard-$$shard_index.actual.txt"; \
				shard_log="$$report_dir/pytest-shard-$$shard_index.log"; \
				shard_junit="$$report_dir/junit-shard-$$shard_index.xml"; \
				shard_status="$$report_dir/shard-$$shard_index.status"; \
				shard_coverage="$$report_dir/.coverage.combined.$$shard_index"; \
				( \
					COVERAGE_FILE="$$shard_coverage" \
					timeout --signal=TERM \
						--kill-after=5s \
						"$(TEST_SESSION_TIMEOUT_SECONDS)s" \
						$(UV_RUN) python -m pytest $$_pytest_run \
						$(PYTEST_REPORT_ARGS) \
						$(if $(filter 1,$(DIAG)),$(PYTEST_DIAG_ARGS),) \
						-p no:metadata -p flext_infra.pytest_shard \
						--flext-shard-count="$$effective_shard_count" \
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
				if [ ! -s "$$shard_junit" ]; then \
					printf 'ERROR: pytest shard %s JUnit is missing or empty: %s\n' \
						"$$shard_index" "$$shard_junit" >&2; rc=2; \
				fi; \
				_junit_inputs="$$_junit_inputs --junit $$shard_junit"; \
				shard_index=$$((shard_index + 1)); \
			done; \
			if [ "$$rc" -ne 0 ]; then break; fi; \
			batch_start="$$batch_end"; \
		done; \
		if [ "$$rc" -eq 0 ]; then \
			actual_all="$$plan_dir/all-items.actual.txt"; \
			: > "$$actual_all"; \
			shard_index=0; \
			while [ "$$shard_index" -lt "$$effective_shard_count" ]; do \
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
			$(RUNTIME_PYTHON) -m coverage combine \
				--data-file="$$report_dir/.coverage.combined" --keep "$$report_dir"; \
			rc=$$?; \
			if [ "$$rc" -eq 0 ]; then \
				$(RUNTIME_PYTHON) -m coverage xml \
					--data-file="$$report_dir/.coverage.combined" \
					-o "$$coverage_file"; \
				rc=$$?; \
			fi; \
		fi; \
		if [ "$$rc" -eq 0 ]; then \
			env $(PROJECT_FLEXT_INFRA) validate pytest-diag --combine-junit "$$junit_file" $$_junit_inputs; \
			rc=$$?; \
			if [ "$$rc" -eq 0 ]; then _diag_inputs="--junit $$junit_file --log $$log_file"; fi; \
		fi; \
	else \
		printf '%s\n' '$(UV_RUN) python -m pytest' \
			"$$_pytest_run $(PYTEST_REPORT_ARGS) -p no:metadata --junitxml=$$junit_file" \
			"--timeout=$(TEST_ITEM_TIMEOUT_SECONDS) --timeout-method=signal" \
			"$$_coverage_args $$_all_pytest_args" > "$$command_file"; \
		timeout --signal=TERM \
			--kill-after=5s \
			"$(TEST_SESSION_TIMEOUT_SECONDS)s" \
			$(UV_RUN) python -m pytest $$_pytest_run \
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
	if [ "$$_coverage_required" -eq 1 ] && [ "$$rc" -ne 0 ]; then \
		duration=$$(( $$(date +%s) - session_started_epoch )); \
		printf 'status=incomplete\njunit=not-combined\ncoverage=not-generated\ntotal=0\npassed=0\nfailed=0\nerrors=0\nskipped=0\nduration_seconds=%s\n' \
			"$$duration" > "$$summary_file"; \
		ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
		printf 'Reports: %s (latest: %s/latest)\n' \
			"$$report_dir" "$(PYTEST_REPORTS_DIR)" >&2; \
		exit "$$rc"; \
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
		duration=$$(( $$(date +%s) - session_started_epoch )); \
		printf 'status=incomplete\njunit=not-combined\ncoverage=not-generated\ntotal=0\npassed=0\nfailed=0\nerrors=0\nskipped=0\nduration_seconds=%s\n' "$$duration" > "$$summary_file"; \
		ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
		exit 124; \
	fi; \
	if timeout --signal=TERM \
		--kill-after=5s "$${remaining_seconds}s" \
		env $(PROJECT_FLEXT_INFRA) validate pytest-diag \
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
		duration=$$(( $$(date +%s) - session_started_epoch )); \
		printf 'status=incomplete\njunit=not-combined\ncoverage=not-generated\ntotal=0\npassed=0\nfailed=0\nerrors=0\nskipped=0\nduration_seconds=%s\n' "$$duration" > "$$summary_file"; \
		ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
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
		duration=$$(( $$(date +%s) - session_started_epoch )); \
		printf 'status=incomplete\njunit=not-combined\ncoverage=not-generated\ntotal=0\npassed=0\nfailed=0\nerrors=0\nskipped=0\nduration_seconds=%s\n' "$$duration" > "$$summary_file"; \
		ln -sfn "$$run_id" "$(PYTEST_REPORTS_DIR)/latest"; \
		exit 2; \
	fi; \
	. "$$counts_file"; \
	if [ "$$_coverage_required" -eq 1 ]; then \
		failures="$${failed_count:-0}"; errors="$${error_count:-0}"; \
		skipped="$${skipped_count:-0}"; \
		passed=$$((tests - failures - errors - skipped)); \
		if [ "$$passed" -lt 0 ]; then passed=0; fi; \
	fi; \
	if [ "$${failed_count:-0}" -gt 0 ] || [ "$${error_count:-0}" -gt 0 ] || \
		[ "$${warning_count:-0}" -gt 0 ] || [ "$${skipped_count:-0}" -gt 0 ]; then \
		if [ "$$rc" -eq 0 ]; then rc=1; fi; \
	fi; \
	summary_status=complete; \
	if [ "$$rc" -ne 0 ]; then summary_status=incomplete; fi; \
	printf 'status=%s\njunit=%s\ncoverage=%s\ntotal=%s\npassed=%s\nfailed=%s\nerrors=%s\nskipped=%s\nduration_seconds=%s\n' \
		"$$summary_status" "$$junit_file" "$$_coverage_value" "$$tests" "$$passed" \
		"$$failures" "$$errors" "$$skipped" "$$duration" > "$$summary_file"; \
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


_builtin_fmt_check: _builtin_require_environment
	@$(UV_RUN) ruff check --no-fix $(FMT_PATHS)
	@$(UV_RUN) ruff format --check $(FMT_PATHS)

_builtin_fmt_apply: _builtin_require_environment
	$(call _require_apply)
	@$(UV_RUN) ruff check --fix $(FMT_PATHS)
	@$(UV_RUN) ruff format $(FMT_PATHS)

_builtin_run_default: _builtin_require_environment
	@$(UV_RUN) $(PROJECT_NAME) $(ARGS)

_builtin_status_diagnostics: _builtin_require_environment
	@printf 'profile=%s\nattached=%s\nproject=%s\nruntime=%s\n' \
		'$(MAKE_PROFILE)' '$(ATTACHED_MEMBER)' '$(PROJECT_ROOT)' '$(RUNTIME_ROOT)'
	@$(UV) --version
	@$(UV) lock --project "$(PROJECT_ROOT)" --check
	@if [ -x "$(RUNTIME_PYTHON)" ]; then \
		$(UV) pip check --python "$(RUNTIME_VENV)"; \
	fi
	@git -C "$(PROJECT_ROOT)" status --short

_builtin_docs_check:
	@set -eu; \
	for phase in $(DOCS_PHASES); do \
		case "$$phase" in generate|fix) mode=--check ;; *) mode= ;; esac; \
		$(PROJECT_FLEXT_INFRA) docs "$$phase" --workspace "$(PROJECT_ROOT)" $$mode $(DOCS_PROJECT_ARGS); \
	done

_builtin_docs_all:
	$(call _require_apply)
	@set -eu; \
	for phase in $(DOCS_PHASES); do \
		case "$$phase" in generate|fix) mode=--apply ;; *) mode= ;; esac; \
		$(PROJECT_FLEXT_INFRA) docs "$$phase" --workspace "$(PROJECT_ROOT)" $$mode $(DOCS_PROJECT_ARGS); \
	done

_builtin_docs_generate:
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) docs generate --workspace "$(PROJECT_ROOT)" --apply $(DOCS_PROJECT_ARGS)

_builtin_docs_fix:
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) docs fix --workspace "$(PROJECT_ROOT)" --apply $(DOCS_PROJECT_ARGS)

_builtin_docs_audit:
	@$(PROJECT_FLEXT_INFRA) docs audit --workspace "$(PROJECT_ROOT)" $(DOCS_PROJECT_ARGS)

_builtin_docs_build:
	@$(PROJECT_FLEXT_INFRA) docs build --workspace "$(PROJECT_ROOT)" $(DOCS_PROJECT_ARGS)

_builtin_docs_validate:
	@$(PROJECT_FLEXT_INFRA) docs validate --workspace "$(PROJECT_ROOT)" $(DOCS_PROJECT_ARGS)

_builtin_clean_generated:
	$(call _require_apply)
	@find "$(PROJECT_ROOT)" -type d \
		\( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache -o -name .ruff_cache \) \
		-prune -exec rm -rf {} +
	@rm -rf "$(PROJECT_ROOT)/build" "$(PROJECT_ROOT)/dist" "$(PROJECT_ROOT)/htmlcov"
	@rm -f "$(PROJECT_ROOT)/.coverage"

_builtin_release_status: _builtin_require_environment
	@$(UV) lock --project "$(PROJECT_ROOT)" --check
	@git -C "$(PROJECT_ROOT)" diff --quiet
	@git -C "$(PROJECT_ROOT)" diff --cached --quiet

_builtin_codegen_check: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode check

_builtin_codegen_apply: _builtin_require_environment
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode apply

_builtin_worktree_list:
	@$(PROJECT_FLEXT_INFRA) workspace worktree --workspace "$(WORKSPACE)" --operation list

_builtin_worktree_add:
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) workspace worktree --workspace "$(WORKSPACE)" --operation add --branch "$(BRANCH)" --base "$(BASE)" --apply

_builtin_worktree_update:
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) workspace worktree --workspace "$(WORKSPACE)" --operation update --branch "$(BRANCH)" --base "$(BASE)" --apply

_builtin_worktree_remove:
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) workspace worktree --workspace "$(WORKSPACE)" --operation remove --branch "$(BRANCH)" --apply
