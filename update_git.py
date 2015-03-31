#!/usr/bin/env python
###############################################################################
# By Jim Hester
# Created: 2015 Mar 31 10:17:20 AM
# Last Modified: 2015 Mar 31 02:36:07 PM
# Title:update_git.py
# Purpose:Update git mirror from svn revision
###############################################################################

import argparse
import os
import subprocess
import re
from contextlib import contextmanager

@contextmanager
def pushd(newDir):
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)

def parse_revision_info(lines):
  packages = set()
  prev_type = None
  path_re = re.compile('^ +[AMR] /(.*)/{}/([^/]*)'.format(args.prefix))
  for line in lines.split("\n"):
    path_search = path_re.search(line)
    if path_search:
      package_type = path_search.group(1)
      if prev_type != None and package_type != prev_type:
        raise Exception("Inconsistent package types")
      else:
        prev_type = package_type
      package = path_search.group(2)
      packages.add(package)

  return list(packages), prev_type

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
                                    '/'.join([args.svn, 'trunk', args.prefix,
                                                 'bioc_' +
                                                 version +
                                                 '.manifest'])])
  packages = set()
  for line in output.split("\n"):
    line_search = re.search("^Package: (.*)", line)
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

def track_branch(project, svn_branch, git_branch):
  subprocess.check_call(['git', 'config', '--add', 'svn-remote.{}.url'.format(git_branch),
                         '/'.join([args.svn, 'branches', svn_branch, args.prefix, project])])
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

  global args
  args = parser.parse_args()

  if not args.token:
    if os.environ.get('GITHUB_TOKEN'):
      args.token = os.environ.get('GITHUB_TOKEN')
    else:
      raise Exception("Must specify a Github token")

  revision_info = subprocess.check_output(["svn", "log", "--verbose", "--stop-on-copy", "-r",
                                   args.revision, args.svn])

  packages, package_type = parse_revision_info(revision_info)

  if package_type == "trunk":
    for package in packages:
      print "Updating {}".format(package)
      if in_manifest(package):
        with pushd(package):
          prev_branch = current_branch()
          checkout("master")
          update()
          push()
          checkout(prev_branch)
      else:
        print "{} not in manifest".format(package)
  elif package_type: # if it is defined it is a branch of some kind
    for package in packages:
      print "Updating {}".format(package)
      svn_branch = package.strip("branches/")
      git_branch = reformat_branch_name(svn_branch)
      version = git_branch.strip("revision-")
      if in_manifest(package, version = version):
        with pushd(package):
          if git_branch:
            prev_branch = current_branch()

            if not branch_exists(git_branch):
                track_branch(svn_branch, git_branch)

            checkout(git_branch)
            update()
            push(git_branch)
            checkout(prev_branch)
      else:
        print "{} not in version {} manifest".format(package, version)

  else:
    raise Exception("Unknown package type: {}, packages: {}".format(package_type, packages))

if __name__ == "__main__":
  main()
