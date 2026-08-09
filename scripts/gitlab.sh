#!/usr/bin/env bash
set -euo pipefail

VCS_PROVIDER=gitlab VCS_PROG=gitlab.sh \
  exec bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/vcs.sh" "$@"
