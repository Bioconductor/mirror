# Using Git with Bioconductor SVN repositories #

Bioconductor packages are stored using in the Bioconductor Subversion (SVN)
repository.  However Bioconductor also maintains Read-only mirrors for each
package located on [Github](https://github.com/Bioconductor-mirror).

These instructions detail how to use these mirrors as well as
[git-svn](http://git-scm.com/docs/git-svn) to interact with the Subversion
repositories from git.

*The examples below use HTTPS authentication, however you are free to
substitute using SSH if you prefer, in all cases USER should be replaced by
your Github username, and REPO should be replaced by your package name*

# Install Git-Svn Pre-Requisites #

To install git with svn support, see the following OS specific
instructions.

### Windows ###

Download and install the [Git windows client](https://www.git-scm.com/download/win).

When using windows the below commands should be run using the Git Bash client
which is bundled with git.

### Mac OS X - Homebrew ###

```bash
brew update
brew install git
```

### Linux - Debian Based ###

```bash
sudo apt-get install git-svn
```

# Download the update_remotes.sh script #

`curl -O https://raw.githubusercontent.com/Bioconductor/mirror/master/update_remotes.sh`

## Use Git Locally But Use SVN Publicly ##

If you simply want to use git locally on your machine and do not need to have a
publicly accessible git repository on Github (or elsewhere) you can simply
clone your package from the mirror directly.

    1. git clone https://github.com/Bioconductor-mirror/REPO to clone the repository to your machine.
    2. `bash update_remotes.sh` to setup the git remotes.
    3. Commit to git as you normally would.
    4. Each time you want to push git commits to svn run the following commands.
        1. `git rebase`
        2. `git svn dcommit`

## Use Git Locally And Publicly ##

If you are currently using the Git-Svn Bridge please disable it at
<https://gitsvn.bioconductor.org/>.

If you do not already have a public git repository the simplest thing to do is
navigate to your repository mirror at
`https://github.com/Bioconductor-mirror/REPO` and click the `Fork` button in the
upper right.  This will create a copy of the repository on your personal account.
Then perform the following steps in your terminal.

    1. `git clone https://github.com/USER/REPO` to clone the repository to your machine.
    2. `bash update_remotes.sh` to setup the git remotes.
    3. Commit to git and push to Github as you normally would.
    4. Each time you want to push git commits to svn
       1. `git fetch bioc` to get the lastest mirror state.
       2. `git checkout bioc/master` to switch to the Bioconductor mirror.
       3. `git merge master` to merge your local changes.
       4. `git svn dcommit` to commit your changes

# FAQs #

## How do let users know I am using Github for development and contributions?

Add `URL: https://github.com/USER/REPO` and `BugReports:
https://github.com/USER/REPO/issues` to your `DESCRIPTION` file. You can also
put the You can also mention your bridge on the bioc-devel
[mailing list](http://bioconductor.org/help/mailing-list/).

## I don't know my Subversion username and/or password. What do I do? ##

One of the following steps should work:

* Look in your email. Your SVN credentials were originally sent to you
  by a member of the Bioconductor team (probably Marc Carlson), probably
  with the subject line "congrats" or "congratulations". The email 
  should contain the text "Information about your svn account". 
* Go to your `~/.subversion/auth/svn.simple` directory. There should be
  one or more files whose names are long hexadecimal numbers. Use `grep`
  to find out which file contains your username. If you don't know your 
  username,
  it's usually your first initial, a dot, and your last name (all 
  lowercase). So Jill User would be `j.user`. Example:

        $ grep -l j.user *
        81a52e36a28dfd7750bd975f30c7998b

  This indicates that your password can be found in the file called
  `81a52e36a28dfd7750bd975f30c7998b`. Examine that file and you should see 
  something like:

        password
        V 8
        Z7oRUVH6

  In this case, `Z7oRUVH6` is your password.
* If you still can't find your username or password, contact a 
  member of the Bioconductor team at
  `maintainer at bioconductor dot org`. Mention the package(s) that
  you maintain. We cannot send you your password but we can ask for 
  a new one to be generated, and send it to you. It may take 
  a day or two for the request to be processed.

## How do I commit to the release version of my package? ##

If you are cloning the mirrors directly you can switch to the `release-X.X`
branch of the release you would like to commit to, and then proceed as normal.
If you are hosting on Github as well, rather than checking out `bioc/master`
checkout `bioc/release-X.X`, then perform the rest of the steps as normal.

# Known Issues #

`svn` requires a commit message of at least 10 characters. This is however not
a requirement in `git`. If there is such a short `git` commit message, it might
lead to an error in `git svn dcommit`. If the commits, and in particular the
offending commit, have already been pushed to GitHub, updating the commit
message on GitHub is not advised, as it would change the public history of the
repository.  If you encounter this error you should fix the error message with
`git commit --amend`, then `git push -f` to force push the commit and `git svn
dcommit` to svn.  *Note doing this edits the public history, so if other users
history may be out of sync!*

# Troubleshooting #

## Unable to determine upstream SVN information

The dreadful message indicating that `git` and `svn`got out of sync is `Unable
to determine upstream SVN information from working tree history`. This can
happen, for example if one forgets to `git fetch bioc` but changes were
committed to svn independently. Inspect you git log with `git log --graph
--decorate --pretty=oneline --abbrev-commit --all` to help identify such cases.

Useful references to sort such cases out are 
- http://stackoverflow.com/questions/9805980/unable-to-determine-upstream-svn-information-from-working-tree-history
- http://eikke.com/importing-a-git-tree-into-a-subversion-repository/

# Resources #

* [Github's Git help](https://help.github.com/)
* [Good Resources For Learning Git and Github](https://help.github.com/articles/good-resources-for-learning-git-and-github/)
* [Most common git screwups/questions and solutions](http://41j.com/blog/2015/02/common-git-screwupsquestions-solutions/)
* [Flight rules for git](https://github.com/k88hudson/git-flight-rules)
