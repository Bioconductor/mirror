#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

if [[ -z $GITHUB_TOKEN ]]; then
  echo "Please set GITHUB_TOKEN to your Github API token before running!"
  exit 1
fi

svn_url="https://hedgehog.fhcrc.org/bioconductor/trunk/madman/Rpacks"

function parse_last_revision {
  grep '^r[0-9]' | tail -n 1 | awk '{ print $1 }'
}

if [[ -s .last_revision ]]; then
  revision=$(cat .last_revision)

  head_revision=$(svn log -q -v -l 1 $svn_url | parse_last_revision)

  if [ "$revision" == "$head_revision" ]; then
    echo "No changes since last update"
    exit
  fi

  updated=$(svn log -q -v -$revision:HEAD $svn_url)

  # split records on '/', field 5 is the project directory, print only the
  # first time it is seen
  changed_directories=$(echo "$updated" | \
    awk -F"/" '$0 ~ "[AMR] /trunk/madman/Rpacks" && !a[$5]++ { print $5 }')

else
  changed_directories=$(svn list $svn_url | sed 's!/$!!')
  updated=$(svn log -l 1 -q -v $svn_url)
fi

last_revision=$(echo "$updated" | parse_last_revision)

if [[ ! -z $last_revision ]]; then
  echo $last_revision > .last_revision
fi

echo "$changed_directories"

API="https://api.github.com/"
TOKEN_STRING="Authorization: token $GITHUB_TOKEN"

# https://developer.github.com/v3/repos/#list-organization-repositories
bioc_repos=$(curl -H ${TOKEN_STRING} $API/orgs/bioconductor/repos | \
             grep '"name": ' | \
             sed 's/.*: "\(.*\)",/\1/')

# found via curl -H $TOKEN_STRING $API/orgs/bioconductor/teams
readonly_team_id=1389965

for project in $changed_directories; do
  if [[ -d $project ]]; then
    echo "Updating $project"
    pushd $project
      git svn rebase
      git push origin master
    popd
  else
    if $(echo $bioc_repos | grep -q -w $project); then
      echo "$project already exists on Github without a mirror, skipping!"
    else
      echo "Cloning $project"
      git svn clone ${svn_url}/$project $project
      pushd $project
        echo "Creating new repo for $project"
        # https://developer.github.com/v3/repos/#create
        curl -H $TOKEN_STRING --request POST --data "{\"name\":\"$project\",\"homepage\":\"http://bioconductor.org/packages/devel/bioc/html/${project}.html\",\"has_issues\":\"false\",\"has_wiki\":\"false\",\"has_downloads\":\"false\",\"team_id\":\"${readonly_team_id}\"}" $API/orgs/bioconductor/repos
        echo "Pushing $project to Github"
        git svn rebase
        git remote add origin git@github.com:bioconductor/$project.git
        git push -u origin master
      popd
    fi
  fi
done
