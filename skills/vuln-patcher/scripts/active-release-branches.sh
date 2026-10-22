#!/usr/bin/env bash
set -euo pipefail

PYXIS_URL='https://gitlab.cee.redhat.com/releng/pyxis-repo-configs/-/raw/main/products/rhtas/rhtas.yaml'
REPO_DIR=''

usage() {
  printf 'Usage:\n  bash "%s" [--repo-dir DIR] [--pyxis-url URL]\n' "$0"
}

fail() {
  printf 'active-release-branches blocked: %s\n' "$1" >&2
  exit 2
}

while (($#)); do
  case "$1" in
    --repo-dir)
      (($# >= 2)) || { usage >&2; exit 2; }
      REPO_DIR=$2
      shift 2
      ;;
    --pyxis-url)
      (($# >= 2)) || { usage >&2; exit 2; }
      PYXIS_URL=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

command -v curl >/dev/null 2>&1 || fail 'missing required tool: curl'
command -v yq >/dev/null 2>&1 || fail 'missing required tool: yq'

config_file=$(mktemp)
trap 'rm -f "$config_file"' EXIT
curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 \
  "$PYXIS_URL" -o "$config_file" ||
  fail "could not read Pyxis config: $PYXIS_URL"

tags_output="$(yq -r '
  .repositories[]
  | select(.repository.repository == "rhtas/ec-rhel9")
  | .repository.content_stream_tags[]
' "$config_file")" || fail 'yq could not parse the Pyxis config'
tags=()
while IFS= read -r tag; do
  [[ -z "$tag" ]] && continue
  tags+=("$tag")
done <<< "$tags_output"

((${#tags[@]} > 0)) || fail 'Pyxis has no rhtas/ec-rhel9 content streams'

for tag in "${tags[@]}"; do
  [[ "$tag" =~ ^[0-9]+\.[0-9]+$ ]] ||
    fail "unexpected Pyxis content stream tag: $tag"
done

sorted_tags=$(printf '%s\n' "${tags[@]}" | sort -V | uniq)

printf 'Pyxis: %s\n' "$PYXIS_URL"
printf 'main\tmain\n'
while IFS= read -r tag; do
  [[ -z "$tag" ]] && continue
  branch="release-v$tag"
  if [[ -n "$REPO_DIR" ]] &&
     ! git -C "$REPO_DIR" show-ref --verify --quiet "refs/remotes/upstream/$branch"; then
    fail "Pyxis tag $tag maps to missing upstream/$branch"
  fi
  printf '%s\t%s\n' "$tag" "$branch"
done <<< "$sorted_tags"
