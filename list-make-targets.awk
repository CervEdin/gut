#!/bin/awk

# This script is merely trying to generate a list of documented
# (assumed relevant) targets in a Makefile in an easy to read format.
# It is intended to be a guide and not a source of truth.
# The parsing done in this script is probably not exhaustive and may very well
# produce incorrect results, when in doubt, read the actual Makefile.

/^[a-zA-z_0-9%./()\-\$]+:/ {
  if (message) {
    target = $1
    gsub("\\\\", "", target)
    gsub(":+$", "", target)
    printf "  \x1b[32;01m%-35s\x1b[0m\r%s", target, message
    printf "\n"
    message=""
  }
}

/^## / {
  gsub(/^## /, "")
  if (message) {
    message = message"\r"$0
  } else {
    message = $0
  }
}
