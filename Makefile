# @flext-managed: continuous
# @flext-regenerate: make gen WHAT=apply APPLY=Y
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
# Source: config:dist / config:uv_link_mode
PROJECT_NAME := flext-infra
UV_LINK_MODE := copy
# End SECTION: project identity

# === SECTION: user overrides (managed) ===
# Source: template (canonical public invocation knobs)
# Free: no — values are caller-supplied each invocation, not preserved in the file.
APPLY ?= N
# The seeded absent value means "not applying", so every guard compares against
# APPLYING and a plain read-only run never trips the write-enable check.
APPLYING := $(if $(filter-out N,$(strip $(APPLY))),$(strip $(APPLY)))
ARGS ?=
CHECK_GATES ?=
DEPENDENCY ?=
FAIL_FAST ?= 0
FILE ?=
MATCH ?=
COV ?=
BASE ?=
BRANCH ?=
PYTEST_ARGS ?=
PYTEST_DIAG_ARGS ?= -rA --durations=0 --tb=long --showlocals
PYTEST_REPORT_ARGS ?= -ra --durations=25 --durations-min=0.001 --tb=short
PYTEST_PROCESS_TIMEOUT_SECONDS ?= 660
# mro-99ae: the pytest process inherits a hard wall-clock boundary, mirroring
# MYPY_BOUNDED, so a hung run is terminated even if the typed runner stalls.
PYTEST_BOUNDED = timeout --signal=TERM --kill-after=5s "$(PYTEST_PROCESS_TIMEOUT_SECONDS)s"
PYTEST_REPORTS_DIR ?= .reports/tests
override PYTEST_CASE_TIMEOUT_SECONDS := 10
override PYTEST_RUN_TIMEOUT_SECONDS := 600
override PYTEST_TERMINATION_GRACE_SECONDS := 2
override PYTEST_TIMEOUT_EXIT_CODE := 124
override PYTEST_ENFORCEMENT_PLUGIN := flext_tests_enforcement
override PYTEST_PROGRESS_ARGS := --verbose
override PYTEST_REPORT_ARGS := -ra --durations=25 --durations-min=0.001 --tb=short
override PYTEST_DIAG_ARGS := -rA --durations=0 --tb=long --showlocals
override PYTEST_PARALLEL_WORKERS := 2
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
override export FLEXT_PYTEST_COV_RAW := $(value COV)
WHAT ?=
# The explicit lazy-init selector is a hermetic, target-local transformation.
# Detect it before any parse-time topology probes so the public invocation and
# its recursive builtin never consult Git, worktrees, remotes, or a parent
# workspace merely to regenerate Python package initializers.
GEN_INIT_ONLY := $(if $(and $(filter init,$(WHAT)),$(filter gen _builtin_gen_init,$(MAKECMDGOALS))),Y,)
# End SECTION: user overrides

# === SECTION: derived paths (managed) ===
# Source: computed (git rev-parse, MAKEFILE_LIST, abspath)
# Rule: PROJECT_ROOT is the checkout that OWNS this Makefile, never the caller's
# CWD. Deriving it from `pwd -P` made a member validate whatever tree the
# caller happened to stand in: `make -f <member>/Makefile` invoked from the
# superproject resolved RUFF_PATHS to the SUPERPROJECT's src/tests, so the
# member linted files it does not even contain. With many shared worktrees that
# silently validates the wrong tree.
SELF_MAKEFILE := $(abspath $(firstword $(MAKEFILE_LIST)))
MAKEFILE_ROOT := $(patsubst %/,%,$(dir $(SELF_MAKEFILE)))
PROJECT_ROOT := $(MAKEFILE_ROOT)
override export FLEXT_PYTEST_TARGET_RAW := tests

# === SECTION: verb dispatch (managed) ===
# Source: config:make.verbs[*].whats, config:make.check_gates_allowed,
#        config:make.check_gates_default
PUBLIC_VERBS := help setup deps build check test fmt fix run status docs clean release gen mod
BUILTIN_VERBS := help setup deps build check test fmt fix run status docs clean release gen mod
_ALLOWED_WHATS_help := usage
_ALLOWED_WHATS_setup := environment
_ALLOWED_WHATS_deps := check lock upgrade
_ALLOWED_WHATS_build := artifacts
_ALLOWED_WHATS_check := all lint pyrefly mypy pyright security markdown smells
_ALLOWED_WHATS_test := all full cache-status cache-checkpoint
_ALLOWED_WHATS_fmt := check all apply
_ALLOWED_WHATS_fix := check all apply
_ALLOWED_WHATS_run := default
_ALLOWED_WHATS_status := diagnostics
_ALLOWED_WHATS_docs := all generate fix audit build validate
_ALLOWED_WHATS_clean := status generated
_ALLOWED_WHATS_release := status
_ALLOWED_WHATS_gen := check all apply init
_ALLOWED_WHATS_mod := check all apply

CHECK_GATES_ALLOWED := lint pyrefly mypy pyright security markdown smells
CHECK_GATES_DEFAULT := lint pyrefly mypy pyright security markdown smells
 DOCS_ACTIONS := generate fix audit build validate
 # End SECTION: verb dispatch

# === SECTION: lint/type paths (managed) ===
# Source: repository roots; scripts is included only when it exists.
RUFF_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests $(wildcard $(PROJECT_ROOT)/scripts)
MYPY_PATHS := $(PROJECT_ROOT)/src $(PROJECT_ROOT)/tests $(wildcard $(PROJECT_ROOT)/scripts)
# End SECTION: lint/type paths

# === SECTION: infra bootstrap (managed) ===
# Source: config:infra_repository.*, template (UV default)
UV ?= uv
UV_REQUESTED := $(UV)
CALLER_PATH := $(PATH)
CALLER_VIRTUAL_ENV := $(patsubst %/,%,$(VIRTUAL_ENV))
# Bootstrap never consults a parent checkout or local path.
ifeq ($(GEN_INIT_ONLY),Y)
FLEXT_INFRA_BOOTSTRAP_REF :=
FLEXT_INFRA_BOOTSTRAP_REQUIREMENT :=
UV_BOOTSTRAP_FLAGS :=
else
FLEXT_INFRA_BOOTSTRAP_REF := 0.12.0-dev
FLEXT_INFRA_BOOTSTRAP_REQUIREMENT := flext-infra @ git+https://github.com/flext-sh/flext-infra.git@$(FLEXT_INFRA_BOOTSTRAP_REF)
UV_BOOTSTRAP_FLAGS := --isolated --all-groups --all-extras
endif
# End SECTION: infra bootstrap

_DEFAULT_help := usage
_DEFAULT_deps := check
_DEFAULT_build := artifacts
_DEFAULT_check := all
_DEFAULT_test := all
_DEFAULT_fmt := check
_DEFAULT_fix := check
_DEFAULT_run := default
_DEFAULT_status := diagnostics
_DEFAULT_docs := validate
_DEFAULT_clean := status
_DEFAULT_release := status
_DEFAULT_gen := check
_DEFAULT_mod := check

_APPLY_WHAT_deps := upgrade
_APPLY_WHAT_fmt := apply
_APPLY_WHAT_fix := apply
_APPLY_WHAT_run := default
_APPLY_WHAT_docs := generate
_APPLY_WHAT_clean := generated
_APPLY_WHAT_gen := apply
_APPLY_WHAT_mod := apply
# === SECTION: runtime ownership (managed) ===
# Runtime ownership is always local to the generated project.
RUNTIME_ROOT := $(PROJECT_ROOT)
# End SECTION: runtime ownership

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
ifeq ($(GEN_INIT_ONLY),Y)
RESOLVED_UV :=
else
RESOLVED_UV := $(shell PATH="$(SANITIZED_CALLER_PATH)" command -v "$(UV_REQUESTED)" 2>/dev/null)
ifeq ($(strip $(RESOLVED_UV)),)
$(error Required uv executable not found: $(UV_REQUESTED))
endif
endif
override UV := $(RESOLVED_UV)
override FLEXT_INFRA_PYTHON := $(FLEXT_INFRA_RUNTIME_PYTHON)
override UV_PROJECT := $(RUNTIME_ROOT)
override UV_PROJECT_ENVIRONMENT := $(RUNTIME_VENV)
override VIRTUAL_ENV := $(RUNTIME_VENV)
override PATH := $(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)
export FLEXT_INFRA_PYTHON UV UV_PROJECT UV_PROJECT_ENVIRONMENT VIRTUAL_ENV PATH

FLEXT_INFRA_BOOTSTRAP := env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(SANITIZED_CALLER_PATH)" $(UV) run --project "$(PROJECT_ROOT)" $(UV_BOOTSTRAP_FLAGS) --with "$(FLEXT_INFRA_BOOTSTRAP_REQUIREMENT)" python -m flext_infra

CODEGEN_SCOPE := self
ALLOWED_PROJECTS := .

# Provisioning is declared once. The project manifests are copied under the
# declared runtime before export so uv cannot discover an ancestor workspace or
# substitute its lock and local sources.
# Creating a missing venv is provisioning; clearing one is destruction and is
# never performed.
SETUP_ENVIRONMENT_RECIPE = set -eu; \
	if [ -L "$(RUNTIME_VENV)" ]; then \
		printf 'ERROR: runtime environment must not be a symlink: %s\n' "$(RUNTIME_VENV)" >&2; \
		exit 2; \
	else \
		test -f "$(PROJECT_ROOT)/pyproject.toml" || { printf 'ERROR: missing project manifest %s\n' "$(PROJECT_ROOT)/pyproject.toml" >&2; exit 2; }; \
		test -f "$(PROJECT_ROOT)/uv.lock" || { printf 'ERROR: missing project lock %s\n' "$(PROJECT_ROOT)/uv.lock" >&2; exit 2; }; \
		if [ ! -x "$(RUNTIME_PYTHON)" ]; then \
			$(UV) venv "$(RUNTIME_VENV)"; \
		fi; \
		mkdir -p "$(SETUP_MANIFEST_ROOT)"; \
		cp "$(PROJECT_ROOT)/pyproject.toml" "$(SETUP_MANIFEST_ROOT)/pyproject.toml"; \
		cp "$(PROJECT_ROOT)/uv.lock" "$(SETUP_MANIFEST_ROOT)/uv.lock"; \
		$(UV) export --quiet --project "$(SETUP_MANIFEST_ROOT)" --locked --all-extras --all-groups --no-emit-project --output-file "$(SETUP_REQUIREMENTS)"; \
		$(UV) pip install --python "$(RUNTIME_VENV)" --link-mode "$(UV_LINK_MODE)" --exact --no-deps --requirements "$(SETUP_REQUIREMENTS)" --editable "$(PROJECT_ROOT)"; \
		$(UV) pip check --python "$(RUNTIME_VENV)"; \
	fi

SELECTED_PROJECTS := .
DOCS_PROJECT_ARGS :=

# Execute gates directly from the declared runtime. Asking uv to rediscover a
# project here can select a parent workspace and create its .venv even when the
# caller explicitly supplied an isolated RUNTIME_VENV. PATH binds every command
# to the provisioned environment; PYTHONPATH keeps this checkout's source first.
UV_RUN := env -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)" PYTHONPATH="$(PROJECT_ROOT)/src"
PROJECT_INFRA_PYTHONPATH ?= $(MAKEFILE_ROOT)/src
PROJECT_FLEXT_INFRA := test -x "$(FLEXT_INFRA_PYTHON)" || { printf 'ERROR: FLEXT_INFRA_PYTHON must name an executable managed Python\n' >&2; exit 2; }; env -u PYTHONPATH -u MYPYPATH -u VIRTUAL_ENV -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT PATH="$(dir $(FLEXT_INFRA_PYTHON)):$(SANITIZED_CALLER_PATH)" PYTHONPATH="$(PROJECT_INFRA_PYTHONPATH)" $(FLEXT_INFRA_PYTHON) -m flext_infra
SETUP_MANIFEST_ROOT := $(RUNTIME_VENV).flext-setup
SETUP_REQUIREMENTS := $(SETUP_MANIFEST_ROOT)/requirements.txt

SELF_MAKE := $(MAKE) --no-print-directory -f "$(SELF_MAKEFILE)"

define _dispatch
	@what="$(strip $(WHAT))"; \
	applying="$(strip $(APPLYING))"; \
	if [ -n "$$applying" ] && [ "$$applying" != "Y" ]; then \
		printf 'ERROR: APPLY must be Y when set\n' >&2; exit 2; \
	fi; \
	if [ -n "$$applying" ] && [ -n "$(_DEFAULT_$(1))" ] && [ -z "$(_APPLY_WHAT_$(1))" ]; then \
		printf 'ERROR: verb %s is read-only and does not accept APPLY\n' "$(1)" >&2; exit 2; \
	fi; \
	if [ -z "$$what" ] && [ -n "$$applying" ] && [ -n "$(_APPLY_WHAT_$(1))" ]; then \
		what="$(_APPLY_WHAT_$(1))"; \
	fi; \
	if [ -z "$$what" ]; then what="$(_DEFAULT_$(1))"; fi; \
	if [ -z "$$what" ]; then what="all"; fi; \
	case "$$what" in \
		*[!a-z0-9-]*|'') printf 'ERROR: WHAT must be canonical kebab-case: %s\n' "$$what" >&2; exit 2 ;; \
	esac; \
	what_norm=$$(printf '%s' "$$what" | tr '-' '_'); \
	py_script="$(PROJECT_ROOT)/scripts/$(1)/$$what_norm.py"; \
	sh_script="$(PROJECT_ROOT)/scripts/$(1)/$$what_norm.sh"; \
	py_exists=0; sh_exists=0; \
	if [ -f "$$py_script" ]; then py_exists=1; fi; \
	if [ -f "$$sh_script" ]; then sh_exists=1; fi; \
	if [ "$$py_exists" -eq 1 ] && [ "$$sh_exists" -eq 1 ]; then \
		printf 'ERROR: handler collision for %s WHAT=%s: both .py and .sh exist\n' "$(1)" "$$what" >&2; exit 2; \
	fi; \
	case " $(_ALLOWED_WHATS_$(1)) " in *" $$what "*) builtin_exists=1 ;; *) builtin_exists=0 ;; esac; \
	if [ "$$builtin_exists" -eq 1 ] && { [ "$$py_exists" -eq 1 ] || [ "$$sh_exists" -eq 1 ]; }; then \
		printf 'ERROR: handler collision for %s WHAT=%s: builtin and script both exist\n' "$(1)" "$$what" >&2; exit 2; \
	fi; \
	builtin="_builtin_$(1)_$$what"; \
	if [ "$$builtin_exists" -eq 1 ]; then \
		$(SELF_MAKE) "$$builtin"; \
	elif [ "$$py_exists" -eq 1 ]; then \
		WHAT="$$what" APPLY="$(APPLY)" FILE="$(FILE)" MATCH="$(MATCH)" PROJECT_ROOT="$(PROJECT_ROOT)" RUNTIME_PYTHON="$(RUNTIME_PYTHON)" $(UV_RUN) python "$$py_script"; \
	elif [ "$$sh_exists" -eq 1 ]; then \
		WHAT="$$what" APPLY="$(APPLY)" FILE="$(FILE)" MATCH="$(MATCH)" PROJECT_ROOT="$(PROJECT_ROOT)" RUNTIME_PYTHON="$(RUNTIME_PYTHON)" sh "$$sh_script"; \
	else \
		printf 'ERROR: unsupported %s WHAT=%s; expected scripts/%s/%s.{py,sh}\n' "$(1)" "$$what" "$(1)" "$$what_norm" >&2; exit 2; \
	fi
endef

define _require_apply
	@if [ "$(APPLY)" != "Y" ]; then \
		printf 'ERROR: this action requires APPLY=Y\n' >&2; \
		exit 2; \
	fi
endef

define _run_for_selected_projects
	@set -eu; \
	selected="."; \
	for project in $$selected; do \
		case " $(ALLOWED_PROJECTS) " in \
			*" $$project "*) ;; \
			*) printf 'ERROR: undeclared project %s\n' "$$project" >&2; exit 2 ;; \
		esac; \
		if [ "$$project" = "." ]; then project_root="$(PROJECT_ROOT)"; \
		else project_root="$(PROJECT_ROOT)/$$project"; fi; \
		manifest_root="$(RUNTIME_VENV).flext-lock/$$project"; \
		test -f "$$project_root/pyproject.toml" || { printf 'ERROR: missing project manifest %s\n' "$$project_root/pyproject.toml" >&2; exit 2; }; \
		if [ ! -f "$$project_root/uv.lock" ] && [ "$(APPLYING)" != "Y" ]; then \
			printf 'ERROR: missing project lock %s\n' "$$project_root/uv.lock" >&2; exit 2; \
		fi; \
		mkdir -p "$$manifest_root"; \
		cp "$$project_root/pyproject.toml" "$$manifest_root/pyproject.toml"; \
		if [ -f "$$project_root/uv.lock" ]; then cp "$$project_root/uv.lock" "$$manifest_root/uv.lock"; fi; \
		$(UV) lock --project "$$manifest_root" $(1); \
		if [ "$(APPLYING)" = "Y" ]; then cp "$$manifest_root/uv.lock" "$$project_root/uv.lock"; fi; \
	done
endef

.PHONY: $(PUBLIC_VERBS) _builtin_help_usage _builtin_setup_environment _builtin_deps_check _builtin_deps_lock _builtin_deps_upgrade _builtin_build_artifacts _builtin_check_all _builtin_test_all _builtin_test_full _builtin_test_cache-status _builtin_test_cache-checkpoint _builtin_fmt_check _builtin_fmt_all _builtin_fmt_apply _builtin_fix_check _builtin_fix_all _builtin_fix_apply _builtin_run_default _builtin_status_diagnostics _builtin_docs_all _builtin_docs_generate _builtin_docs_fix _builtin_docs_audit _builtin_docs_build _builtin_docs_validate _builtin_clean_status _builtin_clean_generated _builtin_release_status _builtin_gen_check _builtin_gen_all _builtin_gen_apply _builtin_gen_init _builtin_mod_check _builtin_mod_all _builtin_mod_apply

$(filter-out setup gen,$(PUBLIC_VERBS)):
	$(call _dispatch,$@)

%:
	$(call _dispatch,$@)

# `gen init` deliberately bypasses generic lifecycle hooks. Hooks are allowed
# to discover workspaces and operational state, which would violate the narrow
# initializer contract before the canonical owner even starts.
gen:
ifeq ($(GEN_INIT_ONLY),Y)
gen: _builtin_gen_init
else
	$(call _dispatch,$@)
endif
setup:
	@$(SELF_MAKE) _builtin_setup_environment

_builtin_help_usage:
	@printf '%s\n' 'flext-infra' '';


	@printf '  %-10s WHAT=%s\n' 'help' "$$(printf '%s' '$(_ALLOWED_WHATS_help)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s\n' 'setup';



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'deps' "$$(printf '%s' '$(_ALLOWED_WHATS_deps)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s\n' 'build' "$$(printf '%s' '$(_ALLOWED_WHATS_build)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s\n' 'check' "$$(printf '%s' '$(_ALLOWED_WHATS_check)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s\n' 'test' "$$(printf '%s' '$(_ALLOWED_WHATS_test)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'fmt' "$$(printf '%s' '$(_ALLOWED_WHATS_fmt)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'fix' "$$(printf '%s' '$(_ALLOWED_WHATS_fix)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'run' "$$(printf '%s' '$(_ALLOWED_WHATS_run)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s\n' 'status' "$$(printf '%s' '$(_ALLOWED_WHATS_status)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'docs' "$$(printf '%s' '$(_ALLOWED_WHATS_docs)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'clean' "$$(printf '%s' '$(_ALLOWED_WHATS_clean)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s\n' 'release' "$$(printf '%s' '$(_ALLOWED_WHATS_release)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'gen' "$$(printf '%s' '$(_ALLOWED_WHATS_gen)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";



	@printf '  %-10s WHAT=%s APPLY=Y\n' 'mod' "$$(printf '%s' '$(_ALLOWED_WHATS_mod)' | awk '{$$1=$$1; gsub(/ /, "|"); print}')";


	@if [ -d "$(PROJECT_ROOT)/scripts" ]; then \
		files=$$(find "$(PROJECT_ROOT)/scripts" -mindepth 2 -maxdepth 2 -type f \( -name '*.py' -o -name '*.sh' \) ! -name '__init__.py' -print | LC_ALL=C sort) || exit $$?; \
		seen=' '; \
		for file in $$files; do \
			rel=$${file#"$(PROJECT_ROOT)/scripts/"}; verb=$${rel%%/*}; internal=$${rel#*/}; internal=$${internal%.*}; key="$$verb/$$internal"; \
			case "$$seen" in *" $$key "*) printf 'ERROR: handler collision for scripts/%s.{py,sh}\n' "$$key" >&2; exit 2 ;; esac; \
			seen="$$seen$$key "; what=$$(printf '%s' "$$internal" | tr '_' '-'); \
			printf '  %-10s WHAT=%s\n' "$$verb" "$$what"; \
		done; \
	fi
	@printf '  %-10s %s\n' 'RUNTIME_VENV' 'isolated environment path override (command line only)';

_builtin_require_environment:
	@if [ ! -x "$(RUNTIME_PYTHON)" ]; then \
		printf 'ERROR: missing environment interpreter %s; make setup creates it\n' "$(RUNTIME_PYTHON)" >&2; \
		exit 2; \
	fi

# === SECTION: setup environment (managed) ===
# Source: project manifest and lock + operator contract (mro-e9j0.6 C7)
# Operator contract: setup PROVISIONS tooling only — mise, venv, dependencies.
# It never generates, conforms, or mutates project code; `make gen` (APPLY=Y)
# is the single public conformance/generation surface.
# The venv is created when missing and repaired in place; a symlink fails before
# dependency mutation because environments are never borrowed across checkouts.
_builtin_setup_environment:
	@$(SETUP_ENVIRONMENT_RECIPE)
# End SECTION: setup environment

_builtin_deps_check: _builtin_require_environment
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
	selected="$(strip $(SELECTED_PROJECTS))"; \
	if [ -z "$$selected" ]; then selected="."; fi; \
	set --; \
	for project in $$selected; do set -- "$$@" --projects "$$project"; done; \
	$(PROJECT_FLEXT_INFRA) deps modernize --workspace "$(PROJECT_ROOT)" \
		--apply $(if $(strip $(DEPENDENCY)),,--rewrite-constraints) --skip-check "$$@"
	$(call _run_for_selected_projects,)

_builtin_build_artifacts:
	@$(UV) build --project "$(PROJECT_ROOT)"

# `check` is read-only by contract: it never mutates the tree. Fixing is owned
# by `make fix APPLY=Y` and formatting by `make fmt APPLY=Y`, both run BEFORE
# check. APPLY here made the same tools run twice with conflicting intents,
# so it is rejected instead of silently honoured; FIX=1 became the `fix` verb.
# Under CI=Y the run is narrowed to make.ci.check_gates --
# the strict complement of make.ci.local_check_gates, derived at the config
# owner so the two contexts can never overlap nor leave a gate unowned.
_builtin_check_all: _builtin_require_environment
	@set -eu; \
	gates="$(strip $(CHECK_GATES))"; \
	if [ -z "$$gates" ]; then gates="$$(printf '%s' '$(CHECK_GATES_DEFAULT)' | tr ' ' ',')"; fi; \
	gates="$$(printf '%s' "$$gates" | tr -d '[:space:]')"; \
	if [ "$(strip $(CI))" = "Y" ]; then \
		filtered=""; \
		for gate in $$(printf '%s' "$$gates" | tr ',' ' '); do \
			owned=0; \
			if [ "$$gate" = "lint" ]; then owned=1; fi; \
			if [ "$$gate" = "pyright" ]; then owned=1; fi; \
			if [ "$$gate" = "security" ]; then owned=1; fi; \
			if [ "$$gate" = "markdown" ]; then owned=1; fi; \
			if [ "$$gate" = "smells" ]; then owned=1; fi; \
			if [ "$$owned" -eq 1 ]; then \
				if [ -n "$$filtered" ]; then filtered="$$filtered,$$gate"; else filtered="$$gate"; fi; \
			fi; \
		done; \
		gates="$$filtered"; \
		printf 'INFO: CI=Y runs check gates: lint pyright security markdown smells\n'; \
	fi; \
	for gate in $$(printf '%s' "$$gates" | tr ',' ' '); do \
		case " $(CHECK_GATES_ALLOWED) " in *" $$gate "*) ;; \
			*) printf 'ERROR: unknown CHECK_GATES value: %s (allowed: %s)\n' "$$gate" "$(CHECK_GATES_ALLOWED)" >&2; exit 2 ;; \
		esac; \
	done; \
	if [ -z "$$gates" ]; then \
		printf 'ERROR: no check gates remain after CI=Y filtering\n' >&2; \
		exit 2; \
	fi; \
	$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "$$gates" --projects .


_builtin_check_lint: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "lint" --projects .

_builtin_check_pyrefly: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "pyrefly" --projects .

_builtin_check_mypy: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "mypy" --projects .

_builtin_check_pyright: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "pyright" --projects .

_builtin_check_security: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "security" --projects .

_builtin_check_markdown: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "markdown" --projects .

_builtin_check_smells: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) check run --workspace "$(PROJECT_ROOT)" --gates "smells" --projects .


_builtin_test_all: _builtin_require_environment

	@$(PYTEST_BOUNDED) $(UV_RUN) python -m flext_infra._pytest_entry


_builtin_test_full: _builtin_require_environment

	@$(PYTEST_BOUNDED) $(UV_RUN) python -m flext_infra._pytest_entry

_builtin_test_cache-status: _builtin_require_environment

	@$(PYTEST_BOUNDED) $(UV_RUN) python -m flext_infra._pytest_entry

_builtin_test_cache-checkpoint: _builtin_require_environment

	@$(PYTEST_BOUNDED) $(UV_RUN) python -m flext_infra._pytest_entry


# One tool, one verb: `fmt` only formats, `check` only lints (--no-fix) and
# `fix` owns the mutating lint pass. Running ruff twice per gate was the
# duplication this split removes.
_builtin_fmt_check: _builtin_require_environment
	@$(UV_RUN) ruff format --check $(RUFF_PATHS)

_builtin_fmt_all: _builtin_require_environment
	$(call _require_apply)
	@$(UV_RUN) ruff format $(RUFF_PATHS)

_builtin_fmt_apply: _builtin_fmt_all

# Read-only fixed-point after `make fix APPLY=Y` (strips APPLY and
# re-runs default_what=check). Dual of `ruff check --fix` — never mutate here.
_builtin_fix_check: _builtin_require_environment
	@$(UV_RUN) ruff check $(RUFF_PATHS)

_builtin_fix_all: _builtin_require_environment
	$(call _require_apply)
	@$(UV_RUN) ruff check --fix $(RUFF_PATHS)

_builtin_fix_apply: _builtin_fix_all

_builtin_run_default: _builtin_require_environment
	@$(UV_RUN) $(PROJECT_NAME) $(ARGS)

_builtin_status_diagnostics: _builtin_require_environment
	@printf 'project=%s\nruntime=%s\n' '$(PROJECT_ROOT)' '$(RUNTIME_ROOT)'
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

# Generation has one owner. Conform preserves the caller's scope and applies
# the complete dependency/tooling projection before it verifies its fixed point.
# Dependency upgrades remain a separate explicit verb because they rewrite lock
# floors; gen must never run a second pyproject writer over conform's result.
_builtin_gen_check: _builtin_require_environment
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode check

_builtin_gen_init:
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) codegen init --workspace "$(PROJECT_ROOT)" --apply
	@$(PROJECT_FLEXT_INFRA) codegen init --workspace "$(PROJECT_ROOT)" --check

_builtin_gen_all: _builtin_require_environment
	$(call _require_apply)
	@$(PROJECT_FLEXT_INFRA) codegen conform --root "$(PROJECT_ROOT)" --scope "$(CODEGEN_SCOPE)" --mode apply

_builtin_gen_apply: _builtin_gen_all
