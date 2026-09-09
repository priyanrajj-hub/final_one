#!/bin/bash
git config --global user.name "Priyanraj"
git config --global user.email "priyanrajj@gmail.com"

git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_NAME" = "AI Bot" ]; then
    export GIT_AUTHOR_NAME="Priyanraj"
    export GIT_AUTHOR_EMAIL="priyanrajj@gmail.com"
fi
if [ "$GIT_COMMITTER_NAME" = "AI Bot" ]; then
    export GIT_COMMITTER_NAME="Priyanraj"
    export GIT_COMMITTER_EMAIL="priyanrajj@gmail.com"
fi
' HEAD

git push -f origin HEAD
