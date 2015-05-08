# Currently using SVN but want to use Git
    1. git clone Bioconductor-mirror/XXX
    2. Run `update_remotes.sh`
    3. Each time you want to push git commits to svn
        1. `git rebase bioc`
        2. `git svn dcommit`

## Use Bioconductor-mirror directly, merge results from old Repository ##
    1. Turn off the git-svn-bridge
    2. git clone Bioconductor-mirror/XXX
    3. Run `update_remotes.sh`
    4. git remote add old_repo git://YYY
    5. git fetch old_repo
    6. git pull old_repo master
    7. Each time you want to push git commits to svn
        1. `git rebase bioc/master`
        2. `git svn dcommit`

## Use existing Git Repository ##
    1. Turn off the git-svn-bridge
    2. git svn init XXX
    3. git svn fetch
    2. Each time you want to push git commits to svn
        1. `git checkout bioc/master` to switch to the Bioconductor mirror.
        2. `git pull --rebase` to update to the latest mirror state.
        3. `git merge master` to merge your local changes.
        4. `git svn dcommit` to commit your changes
