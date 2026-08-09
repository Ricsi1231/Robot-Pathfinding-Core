#!/usr/bin/env bash
set -euo pipefail

PROG="${VCS_PROG:-${0##*/}}"
VCS_LIB="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/lib" && pwd)"
DRY_RUN=0
DRY_BODY='{"iid":0,"number":0,"web_url":"","html_url":""}'
AUTH=()

usage() {
  cat <<'EOF'
vcs.sh — issue/MR/PR helper for GitLab and GitHub over their REST APIs.

glab is unusable here (the fine-grained token 401/403s on /user and /projects, which
glab validates against); the write endpoints work, so this wraps them in curl. Wrapping
them in one script lets a session grant a narrow Bash allow rule (bash scripts/vcs.sh:*)
instead of a blanket curl permission.

Usage:
  vcs.sh issue   --title T --desc D [--labels "A,B"] [--assignee ID]
  vcs.sh mr      --source BRANCH --title T --desc D [--target dev] [--closes N]
                 [--assignee ID] [--reviewer ID]
  vcs.sh pr      (alias for mr)
  vcs.sh label   --issue N [--add "Status::CODE REVIEW"] [--remove "Status::IN PROGRESS"]
  vcs.sh comment --issue N --body "text"
  vcs.sh close   --issue N

Global flags (accepted anywhere in the argument list):
  --provider gitlab|github   force the target host
  --remote NAME              detect the provider from this git remote
  --dry-run                  print the requests to stderr and exit without calling the API

Provider detection, first match wins:
  --provider  >  $VCS_PROVIDER  >  --remote  >  origin's host  >  a single unambiguous
  remote. Two different providers with no usable origin is an error, not a guess.

Output contract, one line on stdout:
  <kind> #<number>  <url>
Kinds are: issue, MR (GitLab), PR (GitHub), note on issue, closed issue.

GitLab defaults follow the project workflow: assignee/reviewer = Richard, target = dev,
and GITLAB_PROJECT_ID = 83833586 (this repo, robot-pathfinding-core). The platform repo
is a DIFFERENT project (83835542) — override GITLAB_PROJECT_ID for it.

GitHub caveats:
  - "Closes #N" only auto-closes when the pull request targets the repository default
    branch, which the dev/staging/master/production promotion model does not use. On
    GitHub the line is informational.
  - A review is never requested from the pull request author; GitHub rejects that with
    a 422, so the reviewer call is skipped when it resolves to the author.
  - Labels that do not exist yet are created on demand. Set VCS_GH_CREATE_LABELS=0 to
    disable that.
  - remove_source_branch has no per-pull-request equivalent; it is a repository setting
    ("Automatically delete head branches") and the field is dropped.
  - mr and label make several API calls. The first call is fatal; a failure in the
    follow-up assignee/reviewer/label calls is reported as a warning on stderr and the
    command still succeeds, because re-running it would create a duplicate pull request.

Env overrides:
  GITLAB_API, GITLAB_PROJECT_ID, GITLAB_ASSIGNEE, GITLAB_TARGET_BRANCH
  GITHUB_API, GITHUB_REPO, GITHUB_ASSIGNEE, GITHUB_TARGET_BRANCH, VCS_GH_CREATE_LABELS
  VCS_PROVIDER, VCS_TARGET_BRANCH

Tokens are never printed. GitLab reads ~/.git-credentials. GitHub tries `gh auth token`,
then GH_TOKEN, then GITHUB_TOKEN, then ~/.git-credentials.
EOF
}

die() {
  printf '%s: %s\n' "$PROG" "$*" >&2
  exit 1
}

warn() {
  printf '%s: warning: %s\n' "$PROG" "$*" >&2
}

have() {
  command -v "$1" >/dev/null 2>&1
}

json_str() {
  local LC_ALL=C
  local s="${1-}" out="" c ord i n
  n=${#s}
  for ((i = 0; i < n; i++)); do
    c="${s:i:1}"
    case "$c" in
      '"') out+='\"' ;;
      '\') out+='\\' ;;
      $'\n') out+='\n' ;;
      $'\r') out+='\r' ;;
      $'\t') out+='\t' ;;
      *)
        printf -v ord '%d' "'$c"
        if [ "$ord" -ge 0 ] && [ "$ord" -lt 32 ]; then
          printf -v c '\\u%04x' "$ord"
        fi
        out+="$c"
        ;;
    esac
  done
  printf '"%s"' "$out"
}

json_arr() {
  local out="" first=1 v
  for v in "$@"; do
    [ -n "$v" ] || continue
    if [ "$first" -eq 1 ]; then first=0; else out+=","; fi
    out+="$(json_str "$v")"
  done
  printf '[%s]' "$out"
}

json_obj() {
  local out="" first=1 k v
  while [ $# -gt 0 ]; do
    k="$1"
    v="${2-}"
    shift 2
    [ -n "$v" ] || continue
    if [ "$first" -eq 1 ]; then first=0; else out+=","; fi
    case "$k" in
      *@) out+="$(json_str "${k%@}"):$v" ;;
      *) out+="$(json_str "$k"):$(json_str "$v")" ;;
    esac
  done
  printf '{%s}' "$out"
}

urlencode() {
  local LC_ALL=C
  local s="${1-}" out="" c ord i n
  n=${#s}
  for ((i = 0; i < n; i++)); do
    c="${s:i:1}"
    case "$c" in
      [A-Za-z0-9._~-]) out+="$c" ;;
      *)
        printf -v ord '%d' "'$c"
        if [ "$ord" -lt 0 ]; then ord=$((ord + 256)); fi
        printf -v c '%%%02X' "$ord"
        out+="$c"
        ;;
    esac
  done
  printf '%s' "$out"
}

http() {
  local method="$1" url="$2"
  shift 2
  if [ "$DRY_RUN" -eq 1 ]; then
    local a
    printf '%s: [dry-run] %s %s\n' "$PROG" "$method" "$url" >&2
    for a in "$@"; do
      case "$a" in
        -H | --data-urlencode | --data-binary | -X) continue ;;
      esac
      printf '%s: [dry-run]     %s\n' "$PROG" "$a" >&2
    done
    printf '%s\n%s' "$DRY_BODY" "200"
    return 0
  fi
  curl -sS -w $'\n%{http_code}' -X "$method" "${AUTH[@]}" "$@" "$url"
}

split_resp() {
  local resp="${1-}"
  RESP_CODE="${resp##*$'\n'}"
  RESP_BODY="${resp%$'\n'*}"
}

check_http() {
  local code="$1" body="$2"
  shift 2
  if [ $# -eq 0 ]; then
    set -- 200 201
  fi
  local ok
  for ok in "$@"; do
    if [ "$code" = "$ok" ]; then
      return 0
    fi
  done
  printf '%s: HTTP %s\n' "$PROG" "$code" >&2
  printf '%s\n' "$body" | head -c 400 >&2
  printf '\n' >&2
  return 1
}

emit() {
  printf '%s #%s  %s\n' "$1" "${2:-?}" "${3-}"
}

require_arg() {
  [ -n "${ARG[$1]:-}" ] || die "--$1 is required"
}

csv_to_array() {
  _ITEMS=()
  local raw="${1-}" item
  [ -n "$raw" ] || return 0
  local IFS=,
  for item in $raw; do
    item="${item#"${item%%[![:space:]]*}"}"
    item="${item%"${item##*[![:space:]]}"}"
    [ -n "$item" ] && _ITEMS+=("$item")
  done
  return 0
}

host_to_provider() {
  case "$1" in
    github.com) printf 'github' ;;
    gitlab.com) printf 'gitlab' ;;
    *github*) printf 'github' ;;
    *gitlab*) printf 'gitlab' ;;
    *) printf '' ;;
  esac
}

parse_remote_url() {
  local url="$1" rest
  case "$url" in
    *://*)
      rest="${url#*://}"
      rest="${rest#*@}"
      _HOST="${rest%%/*}"
      _SLUG="${rest#*/}"
      ;;
    *:*)
      rest="${url#*@}"
      _HOST="${rest%%:*}"
      _SLUG="${rest#*:}"
      ;;
    *)
      _HOST=""
      _SLUG=""
      return 0
      ;;
  esac
  _HOST="${_HOST%%:*}"
  _SLUG="${_SLUG#/}"
  _SLUG="${_SLUG%.git}"
}

detect_provider() {
  local explicit="${PROVIDER_FLAG:-${VCS_PROVIDER:-}}"
  if [ -n "$explicit" ]; then
    case "$explicit" in
      gitlab | github) ;;
      *) die "unknown provider '$explicit' (expected gitlab or github)" ;;
    esac
  fi

  local names=() name url p
  if [ -n "${REMOTE_FLAG:-}" ]; then
    names=("$REMOTE_FLAG")
  elif git rev-parse --git-dir >/dev/null 2>&1; then
    mapfile -t names < <(git remote 2>/dev/null || true)
  fi

  local seen="" first_p="" first_host="" first_slug=""
  local match_host="" match_slug=""
  local origin_p="" origin_host="" origin_slug=""
  for name in ${names[@]+"${names[@]}"}; do
    url="$(git remote get-url "$name" 2>/dev/null || true)"
    [ -n "$url" ] || continue
    parse_remote_url "$url"
    p="$(host_to_provider "$_HOST")"
    [ -n "$p" ] || continue
    if [ "$name" = origin ] && [ -z "$origin_p" ]; then
      origin_p="$p"
      origin_host="$_HOST"
      origin_slug="$_SLUG"
    fi
    if [ -z "$first_p" ]; then
      first_p="$p"
      first_host="$_HOST"
      first_slug="$_SLUG"
    fi
    case " $seen " in
      *" $p "*) ;;
      *) seen="$seen $p" ;;
    esac
    if [ -n "$explicit" ] && [ "$p" = "$explicit" ] && [ -z "$match_host" ]; then
      match_host="$_HOST"
      match_slug="$_SLUG"
    fi
  done

  if [ -n "$explicit" ]; then
    PROVIDER="$explicit"
    REMOTE_HOST="$match_host"
    REPO_SLUG="$match_slug"
    return 0
  fi

  if [ -n "$origin_p" ]; then
    PROVIDER="$origin_p"
    REMOTE_HOST="$origin_host"
    REPO_SLUG="$origin_slug"
    return 0
  fi

  set -- $seen
  if [ $# -eq 0 ]; then
    die "cannot determine the provider: no git remote points at a known host; pass --provider gitlab|github or set VCS_PROVIDER"
  fi
  if [ $# -gt 1 ]; then
    die "ambiguous provider (remotes resolve to:$seen); pass --provider gitlab|github or set VCS_PROVIDER"
  fi
  PROVIDER="$first_p"
  REMOTE_HOST="$first_host"
  REPO_SLUG="$first_slug"
}

load_adapter() {
  local file="$VCS_LIB/provider_$PROVIDER.sh"
  if [ ! -f "$file" ]; then
    die "missing provider adapter: $file"
  fi
  . "$file"
  local fn
  for fn in provider_init provider_create_issue provider_create_mr \
    provider_set_labels provider_add_comment provider_close_issue; do
    if ! declare -F "$fn" >/dev/null; then
      die "adapter $file does not define $fn"
    fi
  done
}

assign_arg() {
  case "$1" in
    provider) PROVIDER_FLAG="$2" ;;
    remote) REMOTE_FLAG="$2" ;;
    *) ARG["$1"]="$2" ;;
  esac
}

parse_args() {
  local key val
  while [ $# -gt 0 ]; do
    case "$1" in
      --dry-run)
        DRY_RUN=1
        shift
        ;;
      --*=*)
        key="${1%%=*}"
        key="${key#--}"
        val="${1#*=}"
        [ -n "$key" ] || die "malformed argument '$1'"
        assign_arg "$key" "$val"
        shift
        ;;
      --*)
        key="${1#--}"
        [ -n "$key" ] || die "malformed argument '$1'"
        [ $# -ge 2 ] || die "missing value for --$key"
        val="$2"
        case "$val" in
          --*) die "missing value for --$key (next argument is '$val')" ;;
        esac
        assign_arg "$key" "$val"
        shift 2
        ;;
      *)
        die "unexpected argument '$1'"
        ;;
    esac
  done
}

run_command() {
  case "$1" in
    issue) provider_create_issue ;;
    mr | pr) provider_create_mr ;;
    label) provider_set_labels ;;
    comment) provider_add_comment ;;
    close) provider_close_issue ;;
    *)
      printf '%s: unknown command '\''%s'\''\n' "$PROG" "$1" >&2
      usage >&2
      return 1
      ;;
  esac
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    -h | --help | help | "")
      usage
      return 0
      ;;
  esac
  shift

  declare -gA ARG=()
  parse_args "$@"

  detect_provider
  load_adapter
  provider_init

  local out
  out="$(run_command "$cmd")" || exit 1

  if [ "$DRY_RUN" -eq 1 ]; then
    return 0
  fi

  local kind num url
  IFS=$'\t' read -r kind num url <<<"$out"
  emit "$kind" "$num" "$url"
}

main "$@"
