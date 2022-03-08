#!/bin/bash
set -euo pipefail

# sort by committerdate, latest first
git for-each-ref --merged HEAD --no-contains HEAD \
	--sort="-committerdate" \
	--format="%(refname:short)" -- refs/heads/
