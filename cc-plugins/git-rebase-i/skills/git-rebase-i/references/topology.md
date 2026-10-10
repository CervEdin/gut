# Branch topology: move linear commits onto a side branch

Given a linear history, newest first:

```
* <later commits>
* Z   last commit of the group
* ...
* A   first commit of the group
* M   the commit before the group
```

make A..Z a side branch that is merged back where Z was. The todo helper refuses
to cross `label`, `reset` and `merge` lines, so this todo is written with sed.
Follow the Procedure in SKILL.md with these steps in place of the actions.

Write the sed script into the git dir and prep with A:

```bash
cat >"$(git rev-parse --git-path topology.sed)" <<'SED'
/^(pick|p) <A>/i\
label bp
/^(pick|p) <Z>/a\
update-ref refs/heads/<branch>\
label side\
reset bp\
merge side\
x git commit --amend -m "Merge branch '<branch>'"
$a\
break
SED
git rebase-i-prep <A>
```

In the todo the order is oldest first, so A is matched before Z. `<branch>` is
the branch the side line should get, and the `exec` line gives the merge its
subject (without it the merge is called after the label). The abbreviated shas
in the todo are prefixes of the full ones, so `<A>` and `<Z>` must be the short
form that `git log --oneline` prints.

Run the rebase from M itself, not from `M^` (`--root` when M is the first
commit), with the sed as the sequence editor. `-i.bak` is the in-place form that
GNU and BSD sed both accept:

```bash
GIT_SEQUENCE_EDITOR="sed -i.bak -E -f $(git rev-parse --git-path topology.sed)" \
  git -c notes.rewriteRef='refs/notes/*' rebase -i --autostash --rebase-merges --update-refs <M>
```

At the break, the check's commit count shows one merge more than before and an
identical tree. `git cat-file -p <merge> | grep -c ^parent` prints 2. Then
`git rebase --continue`.
