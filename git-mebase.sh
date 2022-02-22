#!/bin/bash

TARGET=$(git parents | head -1)
echo "Rebasing onto: $TARGET"

git arch &&\
  git rebase -i -r --autosquash "$TARGET"
