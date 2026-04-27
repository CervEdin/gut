#!/bin/sh
# Rebuild 'seen' from 'next' (or directly from 'main' if 'next' is empty).
#
# Usage:
#   git checkout -B seen next
#   sh redo-seen.sh
#
# Edit the topic list below to add/remove/reorder topics. Topics graduate
# from this list once they merge to 'next' (move them to redo-next.sh).
#
# Convention: merges done here use the 'seen: merge ...' subject prefix
# already established in seen's first-parent history.

set -eu

./Reintegrate <<'EOF'
claude/contributing-expand
EOF
