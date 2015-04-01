#!/usr/bin/env bash

# This script should be run after cloning, it will update the remote
# information so that git svn commands work properly for both the master and
# release branches.

set -eou pipefail
IFS=$'\n\t'

package=$(git remote -v | perl -ne 'if (m!/([^/]+).git!) { print $1; exit}')
git checkout master
git svn init "https://hedgehog.fhcrc.org/bioconductor/trunk/madman/Rpacks/$package"
git update-ref refs/remotes/git-svn refs/remotes/origin/master
git svn rebase

release_branches=$(git branch -r | perl -ne 'if (m!origin/(release-.*)!) { print $1, "\n" }')
for release_branch in $release_branches; do
  svn_branch=$(echo $release_branch | perl -ne 'if (/release-(\d+)\.(\d+)/) { print "RELEASE_$1_$2"; }')
  svn_url="https://hedgehog.fhcrc.org/bioconductor/branches/$svn_branch/madman/Rpacks/$package"
  git config --add svn-remote.$release_branch.url $svn_url
  git config --add svn-remote.$release_branch.fetch :refs/remotes/git-svn-$release_branch
  git branch --track $release_branch origin/$release_branch
  git update-ref refs/remotes/git-svn-$release_branch refs/heads/$release_branch
done

echo "Commit to git as normal, to push your commits to svn, use git svn dcommit"
