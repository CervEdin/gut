#!/bin/sh

usage=''

# This script is used to "sync" local repositories over a remote.
# Keeping local repositories in sync on different machines can be a bit arduous.
# Usually, one uses branches to accomplish the task. You do work locally, it's
# not polished, you push it to a branch, and then you can pull it on another
# machine. Then on that machine you do some polishing, rewriting history and
# force pushing to the remote to "sync" it.

# This quickly get's tedious. Firstly, even though you're just syncing "draft"
# work, you still need to do some branch management. Force rewriting history
# also easily get's messy, especially if sufficient time passes in-between
# force rewriting and "fixing" the local or remote. It's often non-trivial
# which one is canonical.

# An alternative approach is avoiding branches altogether. Instead, one can use
# sync tags. The idea is simple, instead of pushing "syncing" changes to a
# branch and then dealing with history modification, create a tag of the
# content to sync and push that tag.

# A "sync tag" shall be prefixed "sync/". This will place them in a dedicated
# "sync" directory. The second part of the tag shall be the name of the branch,
# as it is called upstream, as a sub directory. The final part is a timestamp,
# with the date and time in UTC using iso-8601.

# This allows easy identification of sync tags. Easy identification of which
# branch the tag belongs too. Easy sorting of tags by time created and low chance
# of name clashes.

name="sync/$(git rev-parse --abbrev-ref HEAD)/$(date --utc +'%Y-%m-%dT%H.%M.%S')" &&
	git tag "$name" &&
	git push origin "$name"
