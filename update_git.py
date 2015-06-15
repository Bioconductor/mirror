#!/usr/bin/env python
###############################################################################
# By Jim Hester
# Created: 2015 Mar 31 10:17:20 AM
# Last Modified: 2015 Jun 15 05:45:04 PM
# Title:update_git.py
# Purpose:Update git mirror from svn revision
###############################################################################

import argparse
import os
import subprocess
import re
from contextlib import contextmanager
import requests
import json
from operator import itemgetter
import sys

def has_github_remote():
  output = subprocess.check_output(['git', 'remote'])
  return output != ''

def create_github_repo(project):

  print "Creating new Github Repository for {}".format(project)

  url = args.github_api + '/orgs/bioconductor-mirror/repos'
  headers = { 'Authorization': 'token {}'.format(args.token) }
  values = {
    'name': project,
    'homepage': 'http://bioconductor.org/packages/devel/bioc/html/{}.html'.format(project),
    'has_issues': 'false',
    'has_wiki': 'false',
    'has_downloads': 'false'
  }

  r = requests.post(url, headers = headers, data = json.dumps(values))
  print r.json()

  subprocess.check_call(['git', 'remote', 'add',
                         'origin',
                         'git@github.com:bioconductor-mirror/{}.git'.format(project)])

def clone(project):
  subprocess.check_call(['git', 'svn', 'clone',
                         '/'.join([args.svn, args.trunk, args.prefix, project]),
                         project])

@contextmanager
def pushd(newDir):
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)

def parse_revision_info(lines):
  packages = set()
  path_re = re.compile('^ +[AMR] /([^\s]+)/{}/([^/\s]+)'.format(args.prefix))
  for line in lines.split("\n"):
    path_search = path_re.search(line)
    if path_search:
      package_type = path_search.group(1)
      package = path_search.group(2)
      packages.add((package, package_type))

      if not package_type:
        print >> sys.stderr, "line: {}".format(line)

  import pprint; pprint.pprint(packages)
  return sorted(list(packages), key=itemgetter(0, 1))

def current_branch(directory='.'):
  output = subprocess.check_output(["git", "status", "--porcelain", "-b"], cwd=directory)
  for line in output.split("/"):
    search = re.search("## (.*?)(?:...)?", line)
    if search:
      return search.group(1)

  return None

def checkout(branch, directory = '.'):
  subprocess.check_call(["git", "checkout", branch], cwd = directory)

def update(directory = '.'):
  subprocess.check_call(["git", "svn", "rebase"], cwd = directory)

def push(branch = 'master', directory = '.'):
  subprocess.check_call(['git', 'push', '-u', 'origin', branch], cwd = directory)

def parse_manifest(version):
  output = subprocess.check_output(['svn', 'cat',
                                    '/'.join([args.svn, args.trunk, args.prefix,
                                                 'bioc_' +
                                                 version +
                                                 '.manifest'])])
  packages = set()
  for line in output.split("\n"):
    line_search = re.search("^Package:\s*(\S+)", line)
    if line_search:
      packages.add(line_search.group(1))
  return packages

def in_manifest(package, version = None):
  if not 'manifest' in globals():
    global manifests
    manifests = {}

  if not version:
    version = args.devel_version

  if version not in manifests:
    manifests[version] = parse_manifest(version)

  return package in manifests[version]

def reformat_branch_name(name):
  name_search = re.search("RELEASE_(\d+)_(\d+)", name)
  if name_search:
    return "release-{}.{}".format(name_search.group(1), name_search.group(2))
  else:
    return None

def track_branch(package, svn_branch, git_branch):
  subprocess.check_call(['git', 'config', '--add', 'svn-remote.{}.url'.format(git_branch),
                         '/'.join([args.svn, 'branches', svn_branch, args.prefix, package])])
  subprocess.check_call(['git', 'config', '--add', 'svn-remote.{}.fetch'.format(git_branch),
                         ':refs/remotes/git-svn-{}'.format(git_branch)])

  subprocess.check_call(['git', 'svn', 'fetch', git_branch])

  subprocess.check_call(['git', 'branch', git_branch,
                                          'git-svn-{}'.format(git_branch)])

def branch_exists(branch):
  output = subprocess.check_output(['git', 'branch', '--list', branch])

  return output != ''

def main():
  parser = argparse.ArgumentParser(description='Update git mirror from svn revision')
  parser.add_argument('revision', help = 'svn revision to mirror')
  parser.add_argument('--token', help = 'Github API token')
  parser.add_argument('--svn', help = 'svn url',
                      default = 'https://hedgehog.fhcrc.org/bioconductor')
  parser.add_argument('--trunk', help = 'location of the trunk directory',
                      default = 'trunk')
  parser.add_argument('--branch', help = 'location of the branch directories',
                      default = 'branches')
  parser.add_argument('--prefix', help = 'prefix to append before packages',
                      default = 'madman/Rpacks')
  parser.add_argument('--local', help = 'path to the local git mirror',
                      default = '/fh/fast/morgan_m/git_repos')
  parser.add_argument('--remote', help = 'prefix to append before packages',
                      default = 'git@github.com:bioconductor-mirror')
  parser.add_argument('--devel-version', help = 'specify the devel version number',
                      default = '3.1')
  parser.add_argument('--github-api', help = 'specify the url to the Github API',
                      default = 'https://api.github.com')

  global args
  args = parser.parse_args()

  if not args.token:
    if os.environ.get('GITHUB_TOKEN'):
      args.token = os.environ.get('GITHUB_TOKEN')
    else:
      raise Exception("Must specify a Github token")

  revision_info = subprocess.check_output(["svn", "log", "--verbose", "--stop-on-copy", "-r",
                                   args.revision, args.svn])

  for package_info in parse_revision_info(revision_info):
    package, package_type = package_info

    print "Updating {}".format(package)
    if package_type == args.trunk:
      if in_manifest(package):
        if not os.path.exists(package):
          print "Cloning {}".format(package)
          clone(package)

        with pushd(package):
          if not has_github_remote():
            print "creating github remote for {}".format(package)
            create_github_repo(package)

          prev_branch = current_branch()
          checkout("master")
          update()
          push()
          if prev_branch:
            checkout(prev_branch)
      else:
        print "{} not in manifest".format(package)
    else:
      svn_branch = package_type.strip("branches/")
      git_branch = reformat_branch_name(svn_branch)
      if git_branch:
        version = git_branch.strip("release-")
        if in_manifest(package, version = version):
          with pushd(package):
            prev_branch = current_branch()

            if not branch_exists(git_branch):
              track_branch(package, svn_branch, git_branch)

            checkout(git_branch)
            update()
            push(git_branch)
            checkout(prev_branch)
        else:
          print "{} type: {} not in version {} manifest".format(package, package_type, version)

  #else:
    #raise Exception("Unknown package type: {}, packages: {}".format(package_type, packages))

if __name__ == "__main__":
  main()
