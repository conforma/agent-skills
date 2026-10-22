#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage:\n  bash "%s" --repo-dir DIR --rpm-nvr NVR\n' "$0"
}

fail() {
  printf 'assessment blocked: %s\n' "$1" >&2
  exit 2
}

# Pin executable helpers to an immutable, reviewed upstream revision and content hashes.
HACKS_REVISION='74fe1feb3778ac9be49698008298609a98cced48'
HACKS_URL="https://raw.githubusercontent.com/conforma/hacks/$HACKS_REVISION"
CURRENT_RELEASE_TAGS_SHA256='aee9ba83e07d3741d2618a812f3db10869ddbabfa2e02e73d0c429a90f2dd23a'
RPM_VERSION_CHECKER_SHA256='0f7b8f4e47af6440e4c2616ccc249a775bcb9984252ebcb523ab235d53731318'
HACKS_DIR=''
REPO_DIR=''
RPM_NVR=''
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

while (($#)); do
  case "$1" in
    --repo-dir)
      (($# >= 2)) || { usage >&2; exit 2; }
      REPO_DIR=$2
      shift 2
      ;;
    --rpm-nvr)
      (($# >= 2)) || { usage >&2; exit 2; }
      RPM_NVR=$2
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

[[ -n "$REPO_DIR" && -n "$RPM_NVR" ]] || { usage >&2; exit 2; }
[[ -f "$SCRIPT_DIR/active-release-branches.sh" ]] || fail "missing assessor helper: $SCRIPT_DIR/active-release-branches.sh"
git -C "$REPO_DIR" rev-parse --show-toplevel >/dev/null 2>&1 || fail "not a git checkout: $REPO_DIR"

for tool in git podman skopeo rpm rpmdev-vercmp jq yq curl sha256sum; do
  command -v "$tool" >/dev/null 2>&1 || fail "missing required tool: $tool"
done

origin_url="$(git -C "$REPO_DIR" remote get-url origin 2>/dev/null || true)"
upstream_url="$(git -C "$REPO_DIR" remote get-url upstream 2>/dev/null || true)"
[[ -n "$origin_url" ]] || fail 'origin remote is missing'
[[ -n "$upstream_url" ]] || fail 'upstream remote is missing'
[[ -z "$(git -C "$REPO_DIR" status --porcelain)" ]] || fail 'CLI worktree is not clean'

printf 'Repository: %s\n' "$(git -C "$REPO_DIR" rev-parse --show-toplevel)"
printf 'origin: %s\n' "$origin_url"
printf 'upstream: %s\n' "$upstream_url"
printf 'Target RPM NVR: %s\n' "$RPM_NVR"
printf 'Refreshing upstream remote refs without changing the worktree...\n'
git -C "$REPO_DIR" fetch upstream --prune

HACKS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/vuln-patcher-hacks.XXXXXX")" ||
  fail 'could not create temporary directory for hacks scripts'
trap 'rm -rf -- "$HACKS_DIR"' EXIT

printf '\nDownloading RPM assessor scripts from %s\n' "$HACKS_URL"
for script in current-release-tags.sh rpm-version-checker.sh; do
  script_url="$HACKS_URL/$script"
  curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 \
    "$script_url" -o "$HACKS_DIR/$script" ||
    fail "could not download $script_url"
  [[ -s "$HACKS_DIR/$script" ]] || fail "downloaded empty script: $script_url"
  case "$script" in
    current-release-tags.sh) expected_sha256="$CURRENT_RELEASE_TAGS_SHA256" ;;
    rpm-version-checker.sh) expected_sha256="$RPM_VERSION_CHECKER_SHA256" ;;
    *) fail "unexpected assessor script: $script" ;;
  esac
  actual_sha256="$(sha256sum "$HACKS_DIR/$script")" ||
    fail "could not calculate SHA-256 for $script_url"
  actual_sha256="${actual_sha256%% *}"
  [[ "$actual_sha256" == "$expected_sha256" ]] ||
    fail "SHA-256 mismatch for $script_url"
  chmod 700 "$HACKS_DIR/$script" ||
    fail "could not make downloaded script executable: $script_url"
done

pyxis_branches="$(bash "$SCRIPT_DIR/active-release-branches.sh" --repo-dir "$REPO_DIR")" ||
  fail 'active-release-branches.sh could not determine current Pyxis branches'

printf '\nPyxis-derived release branches:\n%s\n' "$pyxis_branches"

pyxis_tags=()
refs=()
while IFS=$'\t' read -r tag branch; do
  [[ -z "$tag" || "$tag" == Pyxis:* ]] && continue
  [[ "$tag" == main ]] && { refs+=(upstream/main); continue; }
  pyxis_tags+=("$tag")
  refs+=("upstream/$branch")
done <<< "$pyxis_branches"
((${#pyxis_tags[@]} > 0)) || fail 'Pyxis returned no release tags'

checker_tags_output="$(cd "$HACKS_DIR" && ./current-release-tags.sh)" ||
  fail 'current-release-tags.sh could not determine active release tags'
checker_tags=()
while IFS= read -r tag; do
  [[ -z "$tag" ]] && continue
  [[ "$tag" =~ ^[0-9]+\.[0-9]+$ ]] || fail "unexpected checker release tag: $tag"
  checker_tags+=("$tag")
done <<< "$checker_tags_output"

pyxis_sorted=$(printf '%s\n' "${pyxis_tags[@]}" | sort -V | uniq)
checker_sorted=$(printf '%s\n' "${checker_tags[@]}" | sort -V | uniq)
if [[ "$pyxis_sorted" != "$checker_sorted" ]]; then
  fail 'Pyxis release tags and checker release tags differ'
fi

printf '\nCandidate image-to-branch mapping for confirmation:\n'
printf '  quay.io/conforma/cli:latest -> main\n'
for tag in "${pyxis_tags[@]}"; do
  printf '  registry.redhat.io/rhtas/ec-rhel9:%s -> release-v%s\n' "$tag" "$tag"
done

printf '\nRPM checker:\n'
(
  cd "$HACKS_DIR"
  ./rpm-version-checker.sh "$RPM_NVR"
)

missing_ref=0
printf '\nUpstream branch evidence:\n'
for ref in "${refs[@]}"; do
  printf '\n### %s\n' "$ref"
  if ! git -C "$REPO_DIR" rev-parse --verify "$ref" >/dev/null 2>&1; then
    printf 'Missing local ref: %s\n' "$ref"
    missing_ref=1
    continue
  fi
  git -C "$REPO_DIR" show -s --format='%H%n%cI%n%s' "$ref"
  git -C "$REPO_DIR" show "$ref:Dockerfile" 2>/dev/null |
    grep -E '^FROM registry\.access\.redhat\.com/ubi9/ubi-minimal:' || true
  git -C "$REPO_DIR" show "$ref:Dockerfile.dist" 2>/dev/null |
    grep -E '^FROM registry\.access\.redhat\.com/ubi9/ubi-minimal:' || true
done

if ((missing_ref)); then
  fail 'one or more checker-derived upstream branch refs are missing'
fi

printf '\nAssessment complete. No branch, commit, push, or PR was created.\n'
