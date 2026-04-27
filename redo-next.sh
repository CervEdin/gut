#!/bin/sh
# Rebuild 'next' from 'main'.
#
# Usage:
#   git checkout --detach main
#   sh redo-next.sh
#   git checkout -B next
#
# Edit the topic list below to add/remove/reorder topics. This script
# is the source of truth for what's in 'next' — never patch 'next' in
# place, always re-run from a clean base.

set -eu

./Reintegrate <<'EOF'
### topics in next (none yet)
EOF
