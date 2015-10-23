Many of these scripts require you to create a Github OAuth token and set it to
to environment variable GITHUB_TOKEN.

After cloning one of the mirrored repositories please run `update_remotes.sh`
to add the proper remote information so that `git svn` commands work properly.

## Release Workflow ##
from `git_repos` directory

```bash
ssh svn@hedgehog
cd /fh/fast/morgan_m/git_repos
mirror_scripts/add_release_branches.sh RELEASE_3_1 */
```

Change the post commit hook to look at the new release (`--devel-version X.X`)
```bash
vi /extra/svndata/gentleman/svnroot/bioconductor/hooks/post-commit
```
