#!/bin/sh
set -eu

tag_prefix='attest/gates/v1'
mode="${1:?usage: gate-attestation.sh wip|merge|review|verify}"
repository_root=$(git rev-parse --show-toplevel)
cd "$repository_root"
canonical_manifest=.github/attestations/promotion-sources.json

require_clean_commit() {
  git diff --quiet
  git diff --cached --quiet
  test -z "$(git status --porcelain --untracked-files=no)"
}

current_repository() {
  git remote get-url origin | sed -E 's#^(https://github.com/|git@github.com:)##; s#\.git$##'
}

local_rig() {
  root=$(git rev-parse --show-toplevel)
  gc status --json | jq -er --arg root "$root" '
    [.rigs[] | . as $rig
      | select($root == $rig.path or ($root | startswith($rig.path + "/")))]
    | sort_by(.path | length) | last | .name'
}

ensure_draft_pull_request() {
  branch=$(git branch --show-current)
  if pr_json=$(gh pr view "$branch" --json number,baseRefName,isDraft 2>/dev/null); then :; else
    gh label create WIP --color D4C5F9 --description 'Draft persistence; validation and attestation are not selected' --force
    gh pr create --draft --base "$BASE" --head "$branch" --title "[WIP] $MESSAGE ($BEAD)" --body "Bead: $BEAD"
    pr_json=$(gh pr view "$branch" --json number,baseRefName,isDraft)
  fi
  test "$(printf '%s' "$pr_json" | jq -r .baseRefName)" = "$BASE"
  test "$(printf '%s' "$pr_json" | jq -r .isDraft)" = true
  PR=$(printf '%s' "$pr_json" | jq -r .number)
  gh pr edit "$PR" --add-label WIP
}

publish_receipt() {
  sha=$(git rev-parse HEAD)
  tag="$tag_prefix/$sha"
  signer=$(git config --get user.email)
  .venv/bin/python -m flext_infra github attest-gates \
    --workspace . --bead "$BEAD" --pull-request "$PR" \
    --integration-branch "$BASE" --signer "$signer" \
    --gates gen --gates check --gates test
  rig=$(local_rig)
  gc bd update "$BEAD" --rig "$rig" --set-metadata "gc.work_branch=$(git branch --show-current)" \
    --set-metadata "gc.work_commit=$sha" --set-metadata "gc.work_pr=$PR" \
    --set-metadata 'gc.work_pr_state=review' \
    --append-notes "Automatic Review proof: SHA $sha, PR $PR, signed aggregate receipt $tag, local gates exit 0."
}

review_contract_json() {
  repository=$(current_repository)
  owner=${repository%%/*}
  name=${repository#*/}
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){isDraft bodyText reviewDecision reviewThreads(first:100){nodes{isResolved isOutdated}}}}}' \
    -F owner="$owner" -F name="$name" -F number="$PR"
}

require_review_pr_contract() {
  expected_draft=$1
  review=$(review_contract_json)
  printf '%s' "$review" | jq -e --argjson draft "$expected_draft" '
    .data.repository.pullRequest as $pr
    | $pr != null
      and $pr.isDraft == $draft
      and (($pr.bodyText | gsub("\\s"; "")) | length > 0)
      and ($pr.bodyText | contains("Bead:"))
      and ($pr.reviewDecision != "CHANGES_REQUESTED")
      and ($pr.reviewThreads.nodes | all(.isResolved or .isOutdated))' >/dev/null
}

demote_failed_promotion() {
  gh pr ready "$PR" --undo
  gh pr edit "$PR" --add-label WIP
  rig=$(local_rig)
  gc bd update "$BEAD" --rig "$rig" --set-metadata 'gc.work_pr_state=draft_wip' \
    --append-notes "Promotion failed for SHA $(git rev-parse HEAD); PR $PR returned automatically to Draft/WIP for fix-forward."
}

complete_transactional_promotion() {
  gh pr edit "$PR" --remove-label WIP
  gh pr ready "$PR"
  if ! gh pr checks "$PR" --watch --fail-fast; then
    demote_failed_promotion
    return 1
  fi
  if ! require_review_pr_contract false; then
    demote_failed_promotion
    return 1
  fi
}

update_wip_tracker() {
  sha=$(git rev-parse HEAD)
  rig=$(local_rig)
  gc bd update "$BEAD" --rig "$rig" --set-metadata "gc.work_branch=$(git branch --show-current)" \
    --set-metadata "gc.work_commit=$sha" --set-metadata "gc.work_pr=$PR" \
    --set-metadata 'gc.work_pr_state=draft_wip' \
    --append-notes "[WIP] checkpoint: SHA $sha, PR $PR Draft/WIP; validation and attestation NOT SELECTED."
}

update_shared_tracker() {
  rig=$(local_rig)
  shared_child=$(gc bd show "$BEAD" --rig "$rig" --json | jq -er '.[0].metadata["gc.shared_child"]')
  city_path=$(gc status --json | jq -er .city_path)
  bd -C "$city_path" update "$shared_child" --append-notes "$1"
}

source_bead() {
  printf '%s\n' "$1" | sed -nE 's/^.*Bead:[[:space:]]*([[:alnum:]_.-]+).*$/\1/p' | head -n 1
}

aggregate_pull_requests() {
  AGGREGATE_CHANGED=false
  target=$(gh pr view "$TARGET_PR" --json number,baseRefName,headRefName,isDraft)
  PR=$(printf '%s' "$target" | jq -r .number)
  BASE=$(printf '%s' "$target" | jq -r .baseRefName)
  target_branch=$(printf '%s' "$target" | jq -r .headRefName)
  TARGET_IS_DRAFT=$(printf '%s' "$target" | jq -r .isDraft)
  if resume_sha=$(git rev-parse -q --verify MERGE_HEAD); then
    test "$(git branch --show-current)" = "$target_branch"
    test -z "$(git diff --name-only --diff-filter=U)"
  else
    resume_sha=
    require_clean_commit
    git fetch origin "$target_branch" "$BASE"
    git switch -C "$target_branch" "origin/$target_branch"
  fi
  manifest_lines=$(mktemp)
  trap 'rm -f "$manifest_lines"' EXIT
  for source_pr in $SOURCE_PRS; do
    case "$source_pr" in *[!0-9]*|'') printf 'ERROR: invalid source PR: %s\n' "$source_pr" >&2; exit 2 ;; esac
    test "$source_pr" != "$PR"
    source=$(gh pr view "$source_pr" --json number,isDraft,headRefOid,body)
    test "$(printf '%s' "$source" | jq -r .isDraft)" = true
    source_sha=$(printf '%s' "$source" | jq -r .headRefOid)
    source_work=$(source_bead "$(printf '%s' "$source" | jq -r .body)")
    test -n "$source_work"
    git fetch origin "pull/$source_pr/head:refs/remotes/origin/promotion-source-$source_pr"
    test "$(git rev-parse "refs/remotes/origin/promotion-source-$source_pr")" = "$source_sha"
    if test -n "$resume_sha" && test "$resume_sha" = "$source_sha"; then
      git commit --no-edit
      resume_sha=
      AGGREGATE_CHANGED=true
    elif git merge-base --is-ancestor "$source_sha" HEAD; then
      :
    else
      git merge --no-ff "refs/remotes/origin/promotion-source-$source_pr" -m "chore(promotion): aggregate Draft PR #$source_pr"
      AGGREGATE_CHANGED=true
    fi
    jq -cn --argjson pr "$source_pr" --arg head_sha "$source_sha" --arg bead "$source_work" \
      '{pr:$pr,head_sha:$head_sha,bead:$bead}' >>"$manifest_lines"
  done
  test -s "$manifest_lines"
  rendered_manifest=$(mktemp)
  trap 'rm -f "$manifest_lines" "$rendered_manifest"' EXIT
  jq -sS . "$manifest_lines" >"$rendered_manifest"
  if ! test -f "$canonical_manifest" || ! cmp -s "$rendered_manifest" "$canonical_manifest"; then
    install -d "$(dirname "$canonical_manifest")"
    cp "$rendered_manifest" "$canonical_manifest"
    git add -- "$canonical_manifest"
    AGGREGATE_CHANGED=true
  fi
}

close_transferred_drafts() {
  aggregate_sha=$(git rev-parse HEAD)
  rig=$(local_rig)
  jq -c '.[]' "$canonical_manifest" | while IFS= read -r source; do
    source_pr=$(printf '%s' "$source" | jq -r .pr)
    source_sha=$(printf '%s' "$source" | jq -r .head_sha)
    source_work=$(printf '%s' "$source" | jq -r .bead)
    gh pr comment "$source_pr" --body "Transferred automatically to maintained PR #$PR at aggregate SHA $aggregate_sha; source SHA $source_sha; bead $source_work."
    gh pr close "$source_pr" --comment "Draft source closed after automatic transfer to maintained PR #$PR."
    gc bd update "$source_work" --rig "$rig" --append-notes "Draft PR $source_pr transferred to maintained PR $PR at $aggregate_sha and closed automatically."
  done
}

case "$mode" in
  wip)
    : "${BEAD:?BEAD is required}"; : "${BASE:?BASE is required}"; : "${PATHS:?PATHS is required}"
    rig=$(local_rig)
    gc bd show "$BEAD" --rig "$rig" --json >/dev/null
    MESSAGE=${MESSAGE:-checkpoint}
    git add -- $PATHS
    git diff --cached --quiet && { printf 'ERROR: checkpoint has no staged changes\n' >&2; exit 2; }
    git commit -m "[WIP] $MESSAGE ($BEAD)"
    git push origin "HEAD:refs/heads/$(git branch --show-current)"
    ensure_draft_pull_request
    update_wip_tracker
    printf '%s\n' '[WIP] persisted; validation and attestation NOT SELECTED'
    ;;
  merge)
    : "${BEAD:?BEAD is required}"; : "${TARGET_PR:?TARGET_PR is required}"; : "${SOURCE_PRS:?SOURCE_PRS is required}"
    MESSAGE=${MESSAGE:-aggregate Draft pull requests}
    aggregate_pull_requests
    if test "$TARGET_IS_DRAFT" = true; then
      if test "$AGGREGATE_CHANGED" = true; then
        git commit --allow-empty -m "[WIP] $MESSAGE ($BEAD)"
        git push origin "HEAD:refs/heads/$(git branch --show-current)"
      fi
      update_wip_tracker
      update_shared_tracker "Automatic Draft aggregation persisted in PR $PR at $(git rev-parse HEAD); validation and attestation NOT SELECTED."
    else
      git commit --allow-empty -m "chore(review): $MESSAGE ($BEAD)"
      publish_receipt
    fi
    close_transferred_drafts
    ;;
  review)
    : "${BEAD:?BEAD is required}"; : "${BASE:?BASE is required}"
    MESSAGE=${MESSAGE:-promote checkpoint to review}
    require_clean_commit
    test -f "$canonical_manifest"
    git commit --allow-empty -m "chore(review): $MESSAGE ($BEAD)"
    PR=$(gh pr view --json number,isDraft --jq 'select(.isDraft == true) | .number')
    test -n "$PR"
    require_review_pr_contract true
    publish_receipt
    complete_transactional_promotion
    ;;
  verify)
    : "${GATE_COMMIT_SHA:?GATE_COMMIT_SHA is required}"; : "${GATE_RECEIPT_OUTPUT:?GATE_RECEIPT_OUTPUT is required}"
    tag="$tag_prefix/$GATE_COMMIT_SHA"
    git fetch --force origin "refs/tags/$tag:refs/tags/$tag"
    .venv/bin/python -m flext_infra github verify-gates \
      --workspace . --allowed-signers .github/attestations/allowed_signers \
      --expected-gates gen --expected-gates check --expected-gates test \
      --output "$GATE_RECEIPT_OUTPUT"
    ;;
  *) printf 'ERROR: unsupported gate attestation mode: %s\n' "$mode" >&2; exit 2 ;;
esac
