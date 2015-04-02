#!/bin/bash

set -eo pipefail
IFS=$'\n\t'
set -u

branch_sha1 () {
  local branch=$1
  local from=${2:-master}

  local current_branch=$(git status --porcelain -b | perl -ne 'if (/## (.*?)(?:...)?/) { print $1, "\n"; }')

  git checkout $branch 1>&2

  local branch_root=$(git log --format='%H' | tail -n 1)

  local svn_url=$(git svn info --url)

  local from_revision=$(svn log --stop-on-copy --verbose "$svn_url" | perl -ne 'if (/from [^:]+:([0-9]+)/) { print $1,"\n" }')

  git checkout $from 1>&2
  for commit in $(git svn log --oneline --show-commit); do
    local commit_info=(${commit// | /$'\t'})
    local revision=${commit_info[0]}
    local sha1=$(git log -n 1 --format='%H' ${commit_info[1]})
    if [[ ${revision:1} -lt $from_revision ]]; then
      git checkout $current_branch 1>&2
      echo $branch_root $sha1
      return 0
    fi
  done
  git checkout $current_branc 1>&2
  return 1
}

echo $(branch_sha1 $1)
