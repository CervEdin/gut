# Quick Reference

## One-time setup

Suggest these if not already configured:

```bash
git config --global merge.conflictStyle zdiff3
```

`zdiff3` inserts the common ancestor between the markers, making it obvious what
each side changed relative to the base.

```bash
git config --global rerere.enabled true
```

With `rerere` enabled, git records how you resolve each unique conflict. If the
same conflict reappears (common during iterative rebases), git auto-applies your
previous resolution.

```bash
git rerere status       # files with recorded resolutions
git rerere diff         # what rerere would apply
git rerere forget file  # discard a bad resolution
```

## Command cheat sheet

| Task                           | Command                                     |
| ------------------------------ | ------------------------------------------- |
| List conflicted files          | `git diff --name-only --diff-filter=U`      |
| Why did this conflict?         | `git log --merge --left-right --oneline`    |
| View base / ours / theirs      | `git show :1:file` / `:2:file` / `:3:file`  |
| What our side changed          | `git diff :1:file :2:file`                  |
| What their side changed        | `git diff :1:file :3:file`                  |
| Show ancestor in markers       | `git checkout --conflict=zdiff3 file`       |
| Take ours per conflict block   | `git resolve --ours file`                   |
| Take theirs per conflict block | `git resolve --theirs file`                 |
| Take ours (whole file)         | `git checkout --ours file && git add file`  |
| Resolve artifact (gen'd/fetch) | Resolve source → regenerate → `git add -u`  |
| Incoming commit message/author | `git show MERGE_HEAD`                       |
| Incoming file as commit        | `git show MERGE_HEAD:file`                  |
| Which commit touched lines     | `git blame MERGE_HEAD -L … -- file`         |
| Check resolution vs auto       | `git diff AUTO_MERGE`                       |
| Check for stray markers        | `git diff --check`                          |
| Build-verify unstaged          | `<project build cmd>` before `git add`      |
| Write resolution summary       | `$WORKDIR/resolution-summary.md`, then note |
| Continue (caller's job)        | `git rebase/cherry-pick --continue`         |
| Abort                          | `git merge/rebase/cherry-pick --abort`      |
| Rerere state                   | `git rerere status`                         |
| Forget bad rerere              | `git rerere forget file`                    |
| Restore conflict markers       | `git checkout --merge <file>`               |
