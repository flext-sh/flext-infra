# @flext-managed: continuous
# @flext-regenerate: make gen APPLY=Y
# @flext-ssot: flext-infra/config/codegen.yaml + flext-infra/src/flext_infra/templates/project/base/Makefile.j2
# @flext-maintenance: do not edit generated projections; edit the SSOT and regenerate
# flext-infra — generated project interface.
# Managed by flext-infra codegen conform for new and existing repositories.
# === SECTION: header (managed) ===
# Source: template (base/Makefile.j2)
# Free: no
# End SECTION: header

SHELL := /bin/sh
.DEFAULT_GOAL := help

# === SECTION: project identity (managed) ===
# Source: config:dist / config:make_profile / config:workspace_root_rel / config:uv_link_mode
PROJECT_NAME := flext-infra
MAKE_PROFILE := standalone
WORKSPACE_ROOT_REL := .
# === SECTION: workspace members (managed) ===
# Source: config:workspace_members (list), config:workspace_repositories (list)
# Computed: MANAGED_GITLINKS mirrors WORKSPACE_MEMBERS for workspace-root gitlink
# governance; standalone projects discover managed submodules at runtime from
# .gitmodules (flext-managed=true).
WORKSPACE_MEMBERS :=
MANAGED_GITLINKS :=
WORKSPACE_EDITABLES := $(PROJECT_NAME):.
UV_LINK_MODE := copy
# End SECTION: project identity

# === SECTION: user overrides (managed) ===
# Source: template (canonical public knobs documented by base.mk)
# Free: no — values are caller-supplied each invocation, not preserved in the file.
APPLY ?=
ARGS ?=
CHANGED_ONLY ?= 0
CHECK_GATES ?=
CI ?= N
DEPENDENCY ?=
FAIL_FAST ?= 0
FILE ?=
FILES ?=
MATCH ?=
PROJECT ?=
PROJECTS ?=
BASE ?=
BRANCH ?=
PYRIGHT_ARGS ?=
PYTEST_ARGS ?=
PYTEST_DIAG_ARGS ?= -rA --durations=0 --tb=long --showlocals
PYTEST_REPORT_ARGS ?= -ra --durations=25 --durations-min=0.001 --tb=short
PYTEST_PROCESS_TIMEOUT_SECONDS ?= 332
# mro-99ae: the pytest process inherits a hard wall-clock boundary, mirroring
# MYPY_BOUNDED, so a hung run is terminated even if the typed runner stalls.
PYTEST_BOUNDED = timeout --signal=TERM --kill-after=5s "$(PYTEST_PROCESS_TIMEOUT_SECONDS)s"
PYTEST_REPORTS_DIR ?= .reports/tests
RUFF_ARGS ?=
override PYTEST_CASE_TIMEOUT_SECONDS := 30
override PYTEST_RUN_TIMEOUT_SECONDS := 300
override PYTEST_TERMINATION_GRACE_SECONDS := 2
override PYTEST_TIMEOUT_EXIT_CODE := 124
override PYTEST_ENFORCEMENT_PLUGIN := flext_tests_enforcement
override PYTEST_PROGRESS_ARGS := --verbose
override PYTEST_REPORT_ARGS := -ra --durations=25 --durations-min=0.001 --tb=short
override PYTEST_DIAG_ARGS := -rA --durations=0 --tb=long --showlocals
override PYTEST_PARALLEL_WORKERS := 4
override PYTEST_PARALLEL_DISTRIBUTION := worksteal
override PYTEST_PROFILE_SORT := cumulative
override PYTEST_PROFILE_LIMIT := 50
override PROCESS_TIMEOUT_COMMAND := timeout
override export FLEXT_PYTEST_ARGS_RAW := $(value PYTEST_ARGS)
override export FLEXT_PYTEST_FILE_RAW := $(value FILE)
override export FLEXT_PYTEST_FILES_RAW := $(value FILES)
override export FLEXT_PYTEST_MATCH_RAW := $(value MATCH)
override export FLEXT_PYTEST_DIAG_RAW := $(value DIAG)
override export FLEXT_PYTEST_FAIL_FAST_RAW := $(value FAIL_FAST)
override export FLEXT_PYTEST_REPORTS_RAW := $(value PYTEST_REPORTS_DIR)
override export FLEXT_PYTEST_WHAT_RAW := $(value WHAT)
override export FLEXT_PYTEST_VERBOSE_RAW := $(value VERBOSE)
WHAT ?=
# End SECTION: user overrides

# === SECTION: derived paths (managed) ===
# Source: computed (git rev-parse, pwd, abspath)
PROJECT_ROOT := $(shell pwd -P)
override export FLEXT_PYTEST_TARGET_RAW := tests
SELF_MAKEFILE := $(abspath $(firstword $(MAKEFILE_LIST)))
MAKEFILE_ROOT := $(patsubst %/,%,$(dir $(SELF_MAKEFILE)))
WORKSPACE ?= $(PROJECT_ROOT)
# === SECTION: WORKSPACE_ROOT isolation (managed) ===
# Source: computed (rule: derive from current checkout unless caller overrides)
# Rule: WORKSPACE_ROOT is always derived from the current checkout unless the
# caller passed it on the command line or via an override origin. An inherited
# environment WORKSPACE_ROOT (e.g. a leaked .envrc export from a foreign checkout)
# must never redirect verbs to another working tree.
ifeq ($(filter command line override,$(origin WORKSPACE_ROOT)),)
WORKSPACE_ROOT := $(shell root=$$(git rev-parse --show-superproject-working-tree 2>/dev/null); if [ -n "$$root" ]; then printf '%s\n' "$$root"; else git rev-parse --show-toplevel 2>/dev/null || pwd -P; fi)
endif
# End SECTION: WORKSPACE_ROOT isolation

# === SECTION: verb dispatch (managed) ===
# Source: config:make.verbs and its computed registry projections.
PUBLIC_VERBS := help setup deps build check test fmt fix run status docs clean release gen worktree
CHECK_GATES_ALLOWED := lint pyrefly mypy pyright silent-failure security markdown smells
CHECK_GATES_DEFAULT := lint pyrefly mypy pyright silent-failure security markdown smells
CHECK_GATES_FAST := lint pyrefly mypy pyright
DOCS_ACTIONS := generate fix audit build validate
SERIALIZED_VERBS := check test fmt fix clean gen
SERIALIZED_TARGETS := _serialized_check _serialized_test _serialized_fmt _serialized_fix _serialized_clean _serialized_gen
# End SECTION: verb dispatch

# === SECTION: lint/type paths (managed) ===
# Source: template + computed (script_dispatch conditional)
RUFF_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests
MYPY_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests
# End SECTION: lint/type paths

# === SECTION: infra bootstrap (managed) ===
# Source: config:infra_repository.*, config:infra_source_root_rel, template (UV default)
UV ?= uv
UV_REQUESTED := $(UV)
CALLER_PATH := $(PATH)
CALLER_VIRTUAL_ENV := $(patsubst %/,%,$(VIRTUAL_ENV))
FLEXT_INFRA_BOOTSTRAP_REQUIREMENT := flext-infra @ git+https://github.com/flext-sh/flext-infra.git@0.12.0-dev
FLEXT_INFRA_SOURCE_ROOT_REL := 
UV_BOOTSTRAP_FLAGS := --isolated --all-groups --all-extras
# End SECTION: infra bootstrap

# === MYPY RESOURCE LIMIT ===
# mro-0ftd.3.11: every Mypy process inherits validated memory and time caps.
MYPY_MEMORY_LIMIT_MB ?= 6144
MYPY_TIMEOUT_SECONDS ?= 600
MYPY_BOUNDED = timeout --signal=TERM --kill-after=5s "$(MYPY_TIMEOUT_SECONDS)s" prlimit --as=$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )):$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )) --
VALIDATE_MYPY_LIMITS = case "$(MYPY_MEMORY_LIMIT_MB)" in ""|*[!0-9]*) echo "ERROR: MYPY_MEMORY_LIMIT_MB must be a positive integer"; exit 2;; esac; [ "$(MYPY_MEMORY_LIMIT_MB)" -gt 0 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be greater than zero"; exit 2; }; [ "$(MYPY_MEMORY_LIMIT_MB)" -le 6144 ] || { echo "ERROR: MYPY_MEMORY_LIMIT_MB must be less than or equal to 6144"; exit 2; }; case "$(MYPY_TIMEOUT_SECONDS)" in ""|*[!0-9]*) echo "ERROR: MYPY_TIMEOUT_SECONDS must be a positive integer"; exit 2;; esac; [ "$(MYPY_TIMEOUT_SECONDS)" -gt 0 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be greater than zero"; exit 2; }; [ "$(MYPY_TIMEOUT_SECONDS)" -le 600 ] || { echo "ERROR: MYPY_TIMEOUT_SECONDS must be less than or equal to 600"; exit 2; }; command -v timeout >/dev/null 2>&1 || { echo "ERROR: required executable not found: timeout"; exit 2; }; command -v prlimit >/dev/null 2>&1 || { echo "ERROR: required executable not found: prlimit"; exit 2; }
REPORT_MYPY_FAILURE = code=$$?; signal=none; if [ "$$code" -ge 128 ]; then signal=$$(( $$code - 128 )); fi; if [ "$$code" -eq 124 ] || [ "$$signal" != none ]; then reason="resource limit triggered"; else reason="type check failed under enforced limits"; fi; echo "ERROR: Mypy $$reason: memory_limit=$(MYPY_MEMORY_LIMIT_MB) MiB; timeout=$(MYPY_TIMEOUT_SECONDS)s; exit=$$code; signal=$$signal" >&2
export MYPY_MEMORY_LIMIT_MB MYPY_TIMEOUT_SECONDS


_DEFAULT_help := all
_DISPATCH_help := builtin
_HANDLER_MAP_help := all:all usage:usage
_DEFAULT_deps := all
_DISPATCH_deps := builtin
_HANDLER_MAP_deps := all:all check:check lock:lock upgrade:upgrade
_DEFAULT_build := all
_DISPATCH_build := builtin
_HANDLER_MAP_build := all:all artifacts:artifacts
_DEFAULT_check := all
_DISPATCH_check := builtin
_HANDLER_MAP_check := all:all
_DEFAULT_test := all
_DISPATCH_test := builtin
_HANDLER_MAP_test := all:all
_DEFAULT_fmt := all
_DISPATCH_fmt := builtin
_HANDLER_MAP_fmt := all:all check:check apply:apply
_DEFAULT_fix := all
_DISPATCH_fix := builtin
_HANDLER_MAP_fix := all:all
_DEFAULT_run := all
_DISPATCH_run := builtin
_HANDLER_MAP_run := all:all default:default
_DEFAULT_status := all
_DISPATCH_status := builtin
_HANDLER_MAP_status := all:all diagnostics:diagnostics
_DEFAULT_docs := all
_DISPATCH_docs := builtin
_HANDLER_MAP_docs := all:all generate:generate fix:fix audit:audit build:build validate:validate
_DEFAULT_clean := all
_DISPATCH_clean := builtin
_HANDLER_MAP_clean := all:all generated:generated
_DEFAULT_release := all
_DISPATCH_release := builtin
_HANDLER_MAP_release := all:all status:status
_DEFAULT_gen := all
_DISPATCH_gen := builtin
_HANDLER_MAP_gen := all:all check:check apply:apply
_DEFAULT_worktree := all
_DISPATCH_worktree := builtin
_HANDLER_MAP_worktree := all:all list:list add:add update:update remove:remove
_DEFAULT_setup := all
_DISPATCH_setup := builtin
_HANDLER_MAP_setup := all:all

_APPLY_WHAT_fmt := all
_APPLY_WHAT_fix := all
_APPLY_WHAT_clean := all
_APPLY_WHAT_gen := all


# === SECTION: profile routing (managed) ===
# Source: config:workspace manifest (role), computed (WORKSPACE_ROOT)
# Rule: workspace-member delegates runtime to the principal (RUNTIME_ROOT is
# the governing workspace root); workspace-root and standalone own their
# runtime locally. An attached member is never promoted to a local runtime.
ifneq ($(filter $(MAKE_PROFILE),workspace-root workspace-member standalone),$(MAKE_PROFILE))
$(error Invalid MAKE_PROFILE '$(MAKE_PROFILE)')
endif

ifeq ($(MAKE_PROFILE),workspace-member)
RUNTIME_ROOT := $(WORKSPACE_ROOT)
else
RUNTIME_ROOT := $(PROJECT_ROOT)
endif
# End SECTION: profile routing

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
override UV_PROJECT := $(RUNTIME_ROOT)
override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)
override VIRTUAL_ENV := $(RUNTIME_VENV)
override PATH := $(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)
export FLEXT_INFRA_PYTHON UV UV_PROJECT UV_PROJECT_ENVIRONMENT VIRTUAL_ENV PATH

ifneq ($(strip $(FLEXT_INFRA_SOURCE_ROOT_REL)),)
FLEXT_INFRA_SOURCE_ROOT := $(abspath $(PROJECT_ROOT)/$(FLEXT_INFRA_SOURCE_ROOT_REL))
FLEXT_INFRA_BOOTSTRAP := env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(SANITIZED_CALLER_PATH)" $(UV) run --project "$(PROJECT_ROOT)" $(UV_BOOTSTRAP_FLAGS) --with-editable "$(FLEXT_INFRA_SOURCE_ROOT)" python -m flext_infra
else
FLEXT_INFRA_SOURCE_ROOT :=
FLEXT_INFRA_BOOTSTRAP := env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(SANITIZED_CALLER_PATH)" $(UV) run --project "$(PROJECT_ROOT)" $(UV_BOOTSTRAP_FLAGS) --with "$(FLEXT_INFRA_BOOTSTRAP_REQUIREMENT)" python -m flext_infra
endif

ifeq ($(MAKE_PROFILE),workspace-root)
CODEGEN_SCOPE := $(if $(filter Y,$(CI)),self,all)
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
ROOT_PROJECT_SELECTOR := .
CI_INPUT := $(strip $(CI))
ifneq ($(filter-out 0 1 N Y false true,$(CI_INPUT)),)
$(error CI must be one of: 0, 1, N, Y, false, true)
endif
override CI := $(if $(filter 1 Y true,$(CI_INPUT)),Y,N)
export CI
EXPLICIT_PROJECTS := $(strip $(if $(PROJECT),$(PROJECT),$(PROJECTS)))
PYTEST_FILE_PATH := $(word 1,$(subst ::, ,$(strip $(FLEXT_PYTEST_FILE_RAW))))
PYTEST_FILE_MEMBER := $(firstword $(foreach member,$(WORKSPACE_MEMBERS),$(if $(filter $(member)/%,$(PYTEST_FILE_PATH)),$(member))))
PYTEST_FILE_PROJECT := $(if $(strip $(PYTEST_FILE_PATH)),$(if $(strip $(PYTEST_FILE_MEMBER)),$(PYTEST_FILE_MEMBER),$(ROOT_PROJECT_SELECTOR)))
REQUESTED_PROJECTS := $(if $(strip $(EXPLICIT_PROJECTS)),$(EXPLICIT_PROJECTS),$(PYTEST_FILE_PROJECT))
# A workspace root owns no local gate implementation: its verbs fan out to the
# declared members by default. CI=Y and an explicit root selection run self.
DEFAULT_PROJECTS := $(if $(filter Y,$(CI)),.,$(WORKSPACE_MEMBERS) .)
SELECTED_PROJECTS := $(if $(strip $(REQUESTED_PROJECTS)),$(REQUESTED_PROJECTS),$(DEFAULT_PROJECTS))
ROOT_PROJECT_SELECTED := $(filter $(ROOT_PROJECT_SELECTOR),$(SELECTED_PROJECTS))
SELECTED_MEMBER_PROJECTS := $(filter-out $(ROOT_PROJECT_SELECTOR),$(SELECTED_PROJECTS))
WORKSPACE_PROJECT_ARGS := $(foreach project,$(SELECTED_MEMBER_PROJECTS),--projects $(project))
WORKSPACE_CHECK_ARGS := $(if $(strip $(CHECK_GATES)),--make-arg "CHECK_GATES=$(strip $(CHECK_GATES))") $(if $(strip $(FILES)),--make-arg "FILES=$(strip $(FILES))") $(if $(strip $(FILE)),--make-arg "FILE=$(strip $(FILE))") $(if $(filter 1,$(CHANGED_ONLY)),--make-arg "CHANGED_ONLY=1")
WORKSPACE_FIX_ARGS := $(if $(filter Y,$(APPLY)),--make-arg "APPLY=Y")
WORKSPACE_TEST_ARGS := $(if $(strip $(FLEXT_PYTEST_FILE_RAW)),--file "$${FLEXT_PYTEST_FILE_RAW}") $(if $(strip $(FLEXT_PYTEST_MATCH_RAW)),--match "$${FLEXT_PYTEST_MATCH_RAW}") $(if $(strip $(FLEXT_PYTEST_WHAT_RAW)),--what "$${FLEXT_PYTEST_WHAT_RAW}")
DOCS_PROJECT_ARGS := $(foreach project,$(SELECTED_PROJECTS),--projects $(project))
UV_RUN := env -u PYTHONPATH -u MYPYPATH $(UV) run --project "$(RUNTIME_ROOT)" --no-sync
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
SELF_MAKE := $(MAKE) --no-print-directory -f "$(SELF_MAKEFILE)"

define _dispatch
	@what="$(strip $(WHAT))"; \
	if [ -n "$(strip $(APPLY))" ] && [ "$(strip $(APPLY))" != "Y" ]; then \
		printf 'ERROR: APPLY must be Y when set\n' >&2; exit 2; \
	fi; \
	if [ -n "$(strip $(APPLY))" ] && [ -z "$(_APPLY_WHAT_$(1))" ]; then \
		printf 'ERROR: verb %s is read-only and does not accept APPLY\n' "$(1)" >&2; exit 2; \
	fi; \
	if [ -z "$$what" ] && [ -n "$(strip $(APPLY))" ] && [ -n "$(_APPLY_WHAT_$(1))" ]; then \
		what="$(_APPLY_WHAT_$(1))"; \
	fi; \
	if [ -z "$$what" ]; then what="$(_DEFAULT_$(1))"; fi; \
	case "$$what" in \
		*[!a-z0-9_-]*|'') printf 'ERROR: invalid WHAT selector %s\n' "$$what" >&2; exit 2 ;; \
	esac; \
	handler=''; \
	for entry in $(_HANDLER_MAP_$(1)); do \
		selector=$${entry%%:*}; \
		if [ "$$selector" = "$$what" ]; then handler=$${entry#*:}; break; fi; \
	done; \
	if [ -z "$$handler" ]; then printf 'ERROR: unsupported %s WHAT=%s (registry:%s)\n' "$(1)" "$$what" "$(_HANDLER_MAP_$(1))" >&2; exit 2; fi; \
	builtin="_builtin_$(1)_$$handler"; \
	for hook in "pre-$(1)" "pre-$(1)-$$what"; do \
		$(SELF_MAKE) -q "$$hook" >/dev/null 2>&1; rc=$$?; \
		if [ "$$rc" -ne 2 ]; then $(SELF_MAKE) "$$hook" || exit $$?; fi; \
	done; \
	case "$(_DISPATCH_$(1))" in \
		builtin) \
			$(SELF_MAKE) -q "$$builtin" >/dev/null 2>&1; rc=$$?; \
			if [ "$$rc" -eq 2 ]; then printf 'ERROR: configured Make handler is missing: %s\n' "$$builtin" >&2; exit 2; fi; \
			$(SELF_MAKE) "$$builtin" || exit $$? ;; \
		*) printf 'ERROR: unsupported dispatch kind for %s: %s\n' "$(1)" "$(_DISPATCH_$(1))" >&2; exit 2 ;; \
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
	selected="$(strip $(SELECTED_PROJECTS))"; \
	for project in $$selected; do \
		case " $(ALLOWED_PROJECTS) " in \
			*" $$project "*) ;; \
			*) printf 'ERROR: undeclared project %s\n' "$$project" >&2; exit 2 ;; \
		esac; \
		if [ "$$project" = "." ]; then project_root="$(PROJECT_ROOT)"; \
		else project_root="$(PROJECT_ROOT)/$$project"; fi; \
		$(UV) lock --project "$$project_root" $(1); \
	done
endef

.PHONY: $(PUBLIC_VERBS) $(SERIALIZED_TARGETS) \
_builtin_help_all \
_builtin_help_usage \
_builtin_setup_all \
_builtin_deps_all \
_builtin_deps_check \
_builtin_deps_lock \
_builtin_deps_upgrade \
_builtin_build_all \
_builtin_build_artifacts \
_builtin_check_all \
_builtin_test_all \
_builtin_fmt_all \
_builtin_fmt_check \
_builtin_fmt_apply \
_builtin_fix_all \
_builtin_run_all \
_builtin_run_default \
_builtin_status_all \
_builtin_status_diagnostics \
_builtin_docs_all \
_builtin_docs_generate \
_builtin_docs_fix \
_builtin_docs_audit \
_builtin_docs_build \
_builtin_docs_validate \
_builtin_clean_all \
_builtin_clean_generated \
_builtin_release_all \
_builtin_release_status \
_builtin_gen_all \
_builtin_gen_check \
_builtin_gen_apply \
_builtin_worktree_all \
_builtin_worktree_list \
_builtin_worktree_add \
_builtin_worktree_update \
_builtin_worktree_remove \
_builtin_require_environment _builtin_setup_environment _builtin_setup_submodules \
	_builtin_build_local _builtin_check_local _builtin_test_local \
	_builtin_fmt_check_local _builtin_fmt_apply_local _builtin_fix_local

$(filter-out setup $(SERIALIZED_VERBS),$(PUBLIC_VERBS)):
	$(call _dispatch,$@)


check: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "check" $(if $(strip $(WHAT)),--selector-value "$(WHAT)") $(if $(strip $(APPLY)),--apply-token "$(APPLY)")

_serialized_check:
	$(call _dispatch,check)


test: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "test" $(if $(strip $(WHAT)),--selector-value "$(WHAT)") $(if $(strip $(APPLY)),--apply-token "$(APPLY)")

_serialized_test:
	$(call _dispatch,test)


fmt: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "fmt" $(if $(strip $(WHAT)),--selector-value "$(WHAT)") $(if $(strip $(APPLY)),--apply-token "$(APPLY)")

_serialized_fmt:
	$(call _dispatch,fmt)


fix: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "fix" $(if $(strip $(WHAT)),--selector-value "$(WHAT)") $(if $(strip $(APPLY)),--apply-token "$(APPLY)")

_serialized_fix:
	$(call _dispatch,fix)


clean: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "clean" $(if $(strip $(WHAT)),--selector-value "$(WHAT)") $(if $(strip $(APPLY)),--apply-token "$(APPLY)")

_serialized_clean:
	$(call _dispatch,clean)


gen: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) workspace serialize-make --workspace "$(PROJECT_ROOT)" --makefile "$(SELF_MAKEFILE)" --verb "gen" $(if $(strip $(WHAT)),--selector-value "$(WHAT)") $(if $(strip $(APPLY)),--apply-token "$(APPLY)")

_serialized_gen:
	$(call _dispatch,gen)



setup:
	$(call _dispatch,setup)

_builtin_setup_all: _builtin_setup_submodules _builtin_setup_environment

_builtin_help_all:
	@printf '%s\n' 'flext-infra [standalone]' '';


	@printf '  %-10s WHAT=%s\n' 'help' 'all|usage';



	@printf '  %-10s\n' 'setup';



	@printf '  %-10s WHAT=%s\n' 'deps' 'all|check|lock|upgrade';



	@printf '  %-10s WHAT=%s\n' 'build' 'all|artifacts';



	@printf '  %-10s WHAT=%s\n' 'check' 'all';



	@printf '  %-10s WHAT=%s\n' 'test' 'all';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'fmt' 'all|check|apply';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'fix' 'all';



	@printf '  %-10s WHAT=%s\n' 'run' 'all|default';



	@printf '  %-10s WHAT=%s\n' 'status' 'all|diagnostics';



	@printf '  %-10s WHAT=%s\n' 'docs' 'all|generate|fix|audit|build|validate';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'clean' 'all|generated';



	@printf '  %-10s WHAT=%s\n' 'release' 'all|status';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'gen' 'all|check|apply';



	@printf '  %-10s WHAT=%s\n' 'worktree' 'all|list|add|update|remove';


	@printf '  %-10s %s\n' 'WORKSPACE' 'target repository (default: current project)';
	@printf '  %-10s %s\n' 'BASE' 'required for worktree add/update';
	@printf '\n%s\n' 'Custom hooks (custom.mk):';
	@printf '  %s\n' 'Define pre-<verb>, post-<verb>, pre-<verb>-<what>, post-<verb>-<what>';
	@printf '  %s\n' 'in custom.mk to run extra steps at the start or end of any verb,';
	@printf '  %s\n' 'for all or some registry-declared WHATs.';
	@if [ -f custom.mk ]; then \
		hooks=$$(grep -oE '^(pre|post)-[a-z][a-z0-9-]*' custom.mk 2>/dev/null | sort -u); \
		if [ -n "$$hooks" ]; then \
			printf '  %s\n' 'Defined in this project:'; \
			for hook in $$hooks; do printf '    %s\n' "$$hook"; done; \
		fi; \
	fi

# A project owns the sources declared by its manifest. The generated setup
# reconciler validates every initialized checkout before mutation, initializes
# only missing modules, and preserves declared branches that fix forward beyond
# the recorded gitlink.
.PHONY: _builtin_setup_submodules

# === SECTION: submodule setup (managed) ===
# Source: template (submodule_setup_recipe.j2)
# Computed: workspace-root uses WORKSPACE_MEMBERS from config; standalone discovers
#           submodules with flext-managed=true from .gitmodules at runtime.
# Rule: managed gitlinks are initialized at the exact commit recorded by their
#       superproject and the declared remote branch is validation-only. Setup
#       never advances an active checkout. Unmanaged submodules are never touched;
#       local commits and changes on the declared branch are preserved. Nested
#       submodules inside managed trees are initialized and validated recursively.
# Free: no
# End SECTION: submodule setup
_builtin_setup_submodules:
	@set -eu; \
	root="$(PROJECT_ROOT)"; \
	if [ ! -f "$$root/.gitmodules" ]; then exit 0; fi; \
	profile="$(MAKE_PROFILE)"; \
	if [ "$$profile" = "workspace-root" ]; then \
		managed="$(WORKSPACE_MEMBERS)"; \
	else \
		managed=""; \
		keys=$$(git -C "$$root" config -f .gitmodules --name-only --get-regexp '^submodule\..*\.flext-managed$$' || :); \
		for key in $$keys; do \
			value=$$(git -C "$$root" config -f .gitmodules --get "$$key"); \
			if [ "$$value" = "true" ]; then \
				section=$${key%.flext-managed}; \
				path=$$(git -C "$$root" config -f .gitmodules --get --default "" "$$section.path"); \
				if [ -n "$$path" ]; then \
					managed="$$managed $$path"; \
				fi; \
			fi; \
		done; \
	fi; \
	managed=$$(printf '%s' "$$managed" | tr ' ' '\n' | sort -u | tr '\n' ' '); \
	if [ -z "$$managed" ]; then exit 0; fi; \
	validate_submodule() { \
		superproject="$$1"; \
		child_path="$$2"; \
		child_root="$$superproject/$$child_path"; \
		keys=$$(git -C "$$superproject" config -f .gitmodules --name-only --get-regexp '^submodule\..*\.path$$' || :); \
		section=""; \
		for key in $$keys; do \
			declared=$$(git -C "$$superproject" config -f .gitmodules --get "$$key"); \
			if [ "$$declared" = "$$child_path" ]; then \
				if [ -n "$$section" ]; then \
					printf 'ERROR: governed gitlink path is duplicated: %s\n' "$$child_path" >&2; \
					exit 2; \
				fi; \
				section=$${key%.path}; \
			fi; \
		done; \
		if [ -z "$$section" ]; then \
			printf 'ERROR: governed gitlink is absent from .gitmodules: %s\n' "$$child_path" >&2; \
			exit 2; \
		fi; \
		git -C "$$superproject" submodule sync --quiet -- "$$child_path"; \
		status=$$(git -C "$$superproject" submodule status -- "$$child_path" || :); \
		case "$$status" in \
			-*) git -C "$$superproject" submodule update --init -- "$$child_path" ;; \
			U*) printf 'ERROR: governed gitlink is conflicted: %s\n' "$$child_path" >&2; exit 2 ;; \
		esac; \
		branch=$$(git -C "$$superproject" config -f .gitmodules --get --default "" "$$section.branch"); \
		if [ -z "$$branch" ]; then \
			printf 'ERROR: governed gitlink has no declared branch: %s\n' "$$child_path" >&2; \
			exit 2; \
		fi; \
		if [ "$$branch" = "." ]; then \
			branch=$$(git -C "$$superproject" branch --show-current); \
			if [ -z "$$branch" ]; then \
				printf 'ERROR: %s: branch = . requires a named superproject branch\n' "$$child_path" >&2; \
				exit 1; \
			fi; \
		fi; \
		git check-ref-format --branch "$$branch" >/dev/null || { \
			printf 'ERROR: %s: invalid declared branch %s\n' "$$child_path" "$$branch" >&2; \
			exit 1; \
		}; \
		git -C "$$child_root" fetch --quiet origin "$$branch" || { \
			printf 'ERROR: %s: fetch origin %s failed\n' "$$child_path" "$$branch" >&2; \
			exit 1; \
		}; \
		remote_head=$$(git -C "$$child_root" rev-parse FETCH_HEAD); \
		gitlink=$$(git -C "$$superproject" ls-files --stage -- "$$child_path" | awk '$$1 == "160000" {print $$2}'); \
		if [ -z "$$gitlink" ]; then \
			printf 'ERROR: governed gitlink is absent from the index: %s\n' "$$child_path" >&2; \
			exit 2; \
		fi; \
		if ! git -C "$$child_root" merge-base --is-ancestor "$$gitlink" "$$remote_head"; then \
			printf 'ERROR: %s: origin/%s diverges from recorded gitlink %s\n' "$$child_path" "$$branch" "$$gitlink" >&2; \
			exit 1; \
		fi; \
		current=$$(git -C "$$child_root" branch --show-current); \
		head=$$(git -C "$$child_root" rev-parse HEAD); \
		if [ -n "$$current" ] && [ "$$current" != "$$branch" ]; then \
			printf 'ERROR: %s: conflicting branch %s; expected %s\n' "$$child_path" "$$current" "$$branch" >&2; \
			exit 1; \
		fi; \
		if [ -z "$$current" ] && [ "$$head" != "$$gitlink" ]; then \
			printf 'ERROR: %s: detached HEAD diverges from recorded gitlink %s\n' "$$child_path" "$$gitlink" >&2; \
			exit 1; \
		fi; \
		if [ -z "$$current" ]; then \
			if git -C "$$child_root" rev-parse --verify --quiet "refs/heads/$$branch" >/dev/null; then \
				branch_head=$$(git -C "$$child_root" rev-parse "refs/heads/$$branch"); \
				git -C "$$child_root" merge-base --is-ancestor "$$gitlink" "$$branch_head" || { \
					printf 'ERROR: %s: local branch %s diverges from gitlink %s\n' "$$child_path" "$$branch" "$$gitlink" >&2; \
					exit 1; \
				}; \
				if [ "$$branch_head" = "$$gitlink" ]; then \
					git -C "$$child_root" checkout --quiet "$$branch"; \
				fi; \
			else \
				git -C "$$child_root" checkout --quiet -b "$$branch"; \
			fi; \
		fi; \
		if ! git -C "$$child_root" merge-base --is-ancestor "$$gitlink" HEAD; then \
			printf 'ERROR: %s: branch %s diverges from recorded gitlink %s\n' "$$child_path" "$$branch" "$$gitlink" >&2; \
			exit 1; \
		fi; \
		if [ -f "$$child_root/.gitmodules" ]; then \
			nested_keys=$$(git -C "$$child_root" config -f .gitmodules --name-only --get-regexp '^submodule\..*\.path$$' || :); \
			for nested_key in $$nested_keys; do \
				nested_path=$$(git -C "$$child_root" config -f .gitmodules --get "$$nested_key"); \
				validate_submodule "$$child_root" "$$nested_path"; \
				done; \
		fi; \
	}; \
	for child_path in $$managed; do \
		validate_submodule "$$root" "$$child_path"; \
	done

_builtin_require_environment:
	@if [ ! -x "$(RUNTIME_PYTHON)" ]; then \
		printf 'ERROR: missing environment interpreter %s; make setup creates it\n' "$(RUNTIME_PYTHON)" >&2; \
		exit 2; \
	fi

# === SECTION: setup environment (managed) ===
# Source: computed (MAKE_PROFILE routing) + operator contract (mro-e9j0.6 C7)
# Operator contract: setup PROVISIONS tooling only — mise, venv, dependencies.
# It never generates, conforms, or mutates project code; `make gen` (APPLY=Y)
# is the single public conformance/generation surface.
# Profile routing: workspace-member delegates the environment to the
# principal (the uv workspace venv lives at RUNTIME_ROOT); workspace-root and
# standalone build their own environment locally.
ifeq ($(MAKE_PROFILE),workspace-member)
_builtin_setup_environment: _builtin_setup_submodules
	@$(MAKE) -C "$(RUNTIME_ROOT)" _builtin_setup_environment
else ifeq ($(MAKE_PROFILE),workspace-root)
_builtin_setup_environment: $(if $(filter Y,$(CI)),,_builtin_setup_submodules)
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --link-mode "$(UV_LINK_MODE)"
	@$(UV) pip check --python "$(RUNTIME_VENV)"
else
_builtin_setup_environment: _builtin_setup_submodules
	@$(UV) venv --clear "$(RUNTIME_VENV)"
	@$(UV) sync --project "$(PROJECT_ROOT)" $(UV_SYNC_FLAGS) --link-mode "$(UV_LINK_MODE)"
endif
# End SECTION: setup environment

_builtin_deps_all: _builtin_require_environment
	$(call _run_for_selected_projects,--check)

_builtin_deps_lock:
	$(call _require_apply)
	$(call _run_for_selected_projects,)

_builtin_deps_upgrade: _builtin_require_environment
	$(call _require_apply)
	@dependency="$(strip $(DEPENDENCY))"; \
	if [ -n "$$dependency" ]; then \
		case "$$dependency" in \
			[-._]*|*[!A-Za-z0-9._-]*) \
				printf 'ERROR: DEPENDENCY must be one normalized distribution name\n' >&2; \
				exit 2 ;; \
		esac; \
	fi
	$(call _run_for_selected_projects,$(if $(strip $(DEPENDENCY)),--upgrade-package "$(strip $(DEPENDENCY))",--upgrade))
	@set -eu; \
	selected="$(strip $(PROJECTS))"; \
	if [ -z "$$selected" ]; then selected="."; fi; \
	set --; \
	for project in $$selected; do set -- "$$@" --projects "$$project"; done; \
	$(PROJECT_FLEXT_INFRA) deps modernize --workspace "$(PROJECT_ROOT)" \
		--apply --rewrite-constraints --skip-check "$$@"
	$(call _run_for_selected_projects,)

_builtin_build_local:
	@$(UV) build --project "$(PROJECT_ROOT)"

_builtin_check_local: _builtin_require_environment
	@set -eu; \
	if [ -n "$(APPLY)" ] || [ -n "$(FIX)" ] || [ -n "$(CHECK_ONLY)" ]; then \
		printf 'ERROR: check is read-only; APPLY, FIX, and CHECK_ONLY are forbidden\n' >&2; exit 2; \
	fi; \
	gates="$(strip $(CHECK_GATES))"; \
	if [ -z "$$gates" ]; then gates="$$(printf '%s' '$(CHECK_GATES_DEFAULT)' | tr ' ' ',')"; fi; \
	gates="$$(printf '%s' "$$gates" | tr -d '[:space:]')"; \
	for gate in $$(printf '%s' "$$gates" | tr ',' ' '); do \
		case " $(CHECK_GATES_ALLOWED) " in *" $$gate "*) ;; \
			*) printf 'ERROR: unknown CHECK_GATES value: %s (allowed: %s)\n' "$$gate" "$(CHECK_GATES_ALLOWED)" >&2; exit 2 ;; \
		esac; \
	done; \
	files="$(strip $(FILES))"; \
	if [ -n "$(strip $(FILE))" ]; then files="$${files:+$$files }$(strip $(FILE))"; fi; \
	if [ "$(CHANGED_ONLY)" = "1" ]; then \
		files="$$( { git diff --name-only --diff-filter=ACMRTUXB HEAD -- '*.py'; git ls-files --others --exclude-standard -- '*.py'; } | tr '\n' ' ' )"; \
	fi; \
	if [ -n "$$files" ]; then \
		if [ -z "$(strip $(CHECK_GATES))" ]; then gates="$$(printf '%s' '$(CHECK_GATES_FAST)' | tr ' ' ',')"; fi; \
		for gate in $$(printf '%s' "$$gates" | tr ',' ' '); do \
			case " $(CHECK_GATES_FAST) " in *" $$gate "*) ;; \
				*) printf 'ERROR: FILE/FILES/CHANGED_ONLY supports only: %s\n' "$(CHECK_GATES_FAST)" >&2; exit 2 ;; \
			esac; \
		done; \
		printf 'Fast-path check: %s\n' "$$files"; \
		status=0; \
		case ",$$gates," in *,lint,*) $(UV_RUN) ruff check --no-fix $$files $(RUFF_ARGS) || status=$$? ;; esac; \
		case ",$$gates," in *,pyright,*) $(UV_RUN) pyright $$files $(PYRIGHT_ARGS) || status=$$? ;; esac; \
		case ",$$gates," in *,pyrefly,*) $(UV_RUN) pyrefly check $$files || status=$$? ;; esac; \
		case ",$$gates," in *,mypy,*) $(VALIDATE_MYPY_LIMITS); $(MYPY_BOUNDED) $(UV_RUN) mypy $$files || { $(REPORT_MYPY_FAILURE); status=$$code; } ;; esac; \
		exit $$status; \
	fi; \
	$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "$$gates" --projects .

_builtin_test_local: _builtin_require_environment

	@$(PYTEST_BOUNDED) $(UV_RUN) python -m flext_infra._pytest_entry

# One tool, one verb: fmt only formats; fix owns the mutating Ruff lint pass.
_builtin_fmt_check_local: _builtin_require_environment
	@$(UV_RUN) ruff format --check $(RUFF_PATHS)

_builtin_fmt_apply_local: _builtin_require_environment
	$(call _require_apply)
	@$(UV_RUN) ruff format $(RUFF_PATHS)


_builtin_build_all: _builtin_build_local

_builtin_check_all: _builtin_check_local

_builtin_test_all: _builtin_test_local

_builtin_fmt_check: _builtin_fmt_check_local

_builtin_fmt_apply: _builtin_fmt_apply_local

_builtin_fix_all: _builtin_fix_local


_builtin_fix_local: _builtin_require_environment
	$(call _require_apply)
	@$(UV_RUN) ruff check --fix $(RUFF_PATHS)

_builtin_run_all: _builtin_require_environment
	@$(UV_RUN) $(PROJECT_NAME) $(ARGS)

_builtin_status_all: _builtin_require_environment
	@printf 'profile=%s\nattached=%s\nproject=%s\nruntime=%s\n' \
		'$(MAKE_PROFILE)' '$(ATTACHED_MEMBER)' '$(PROJECT_ROOT)' '$(RUNTIME_ROOT)'
	@$(UV) --version
	@$(UV) lock --project "$(PROJECT_ROOT)" --check
	@if [ -x "$(RUNTIME_PYTHON)" ]; then \
		$(UV) pip check --python "$(RUNTIME_VENV)"; \
	fi
	@git -C "$(PROJECT_ROOT)" status --short

_builtin_docs_all:
	@set -eu; \
	for action in $(DOCS_ACTIONS); do \
		case "$$action" in generate|fix) mode=$(if $(filter Y,$(APPLY)),--apply,--check) ;; *) mode= ;; esac; \
		$(PROJECT_FLEXT_INFRA) docs "$$action" --workspace "$(PROJECT_ROOT)" --output-dir "$(PROJECT_ROOT)/.reports/docs" $$mode $(DOCS_PROJECT_ARGS); \
	done


_builtin_docs_generate:
	@$(PROJECT_FLEXT_INFRA) docs generate --workspace "$(PROJECT_ROOT)" --output-dir "$(PROJECT_ROOT)/.reports/docs" $(if $(filter Y,$(APPLY)),--apply,--check) $(DOCS_PROJECT_ARGS)


_builtin_docs_fix:
	@$(PROJECT_FLEXT_INFRA) docs fix --workspace "$(PROJECT_ROOT)" --output-dir "$(PROJECT_ROOT)/.reports/docs" $(if $(filter Y,$(APPLY)),--apply,--check) $(DOCS_PROJECT_ARGS)


_builtin_docs_audit:
	@$(PROJECT_FLEXT_INFRA) docs audit --workspace "$(PROJECT_ROOT)" --output-dir "$(PROJECT_ROOT)/.reports/docs" $(DOCS_PROJECT_ARGS)


_builtin_docs_build:
	@$(PROJECT_FLEXT_INFRA) docs build --workspace "$(PROJECT_ROOT)" --output-dir "$(PROJECT_ROOT)/.reports/docs" $(DOCS_PROJECT_ARGS)


_builtin_docs_validate:
	@$(PROJECT_FLEXT_INFRA) docs validate --workspace "$(PROJECT_ROOT)" --output-dir "$(PROJECT_ROOT)/.reports/docs" $(DOCS_PROJECT_ARGS)



_builtin_clean_all:
	$(call _require_apply)
	@find "$(PROJECT_ROOT)" -type d \
		\( -name __pycache__ -o -name .mypy_cache -o -name .pytest_cache -o -name .ruff_cache \) \
		-prune -exec rm -rf {} +
	@rm -rf "$(PROJECT_ROOT)/build" "$(PROJECT_ROOT)/dist" "$(PROJECT_ROOT)/htmlcov"
	@rm -f "$(PROJECT_ROOT)/.coverage"

_builtin_release_all: _builtin_require_environment
	@$(UV) lock --project "$(PROJECT_ROOT)" --check
	@git -C "$(PROJECT_ROOT)" diff --quiet
	@git -C "$(PROJECT_ROOT)" diff --cached --quiet

_builtin_gen_check: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode check

_builtin_gen_all: _builtin_require_environment
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode apply

_builtin_help_usage: _builtin_help_all

_builtin_deps_check: _builtin_deps_all

_builtin_build_artifacts: _builtin_build_all

_builtin_fmt_all: $(if $(filter Y,$(APPLY)),_builtin_fmt_apply,_builtin_fmt_check)

_builtin_run_default: _builtin_run_all

_builtin_status_diagnostics: _builtin_status_all

_builtin_clean_generated: _builtin_clean_all

_builtin_release_status: _builtin_release_all

_builtin_gen_apply: _builtin_gen_all

_builtin_worktree_list: _builtin_worktree_all

_builtin_worktree_all:
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
