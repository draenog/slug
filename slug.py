#!/usr/bin/python3

import copy
import glob
import sys
import os
import shutil
import subprocess
import queue
import threading

import argparse

import signal
import configparser

from git_slug.gitconst import GITLOGIN, GITSERVER, GIT_REPO, GIT_REPO_PUSH, REMOTEREFS
from git_slug.gitrepo import GitRepo, GitRepoError
from git_slug.refsdata import GitArchiveRefsData, RemoteRefsError

class DelAppend(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        item = copy.copy(getattr(namespace, self.dest, None)) if getattr(namespace, self.dest, None) is not None else []
        try:
            self._firstrun
        except AttributeError:
            self._firstrun = True
            del item[:]
        item.append(values)
        setattr(namespace, self.dest, item)

class ThreadFetch(threading.Thread):
    def __init__(self, queue, pkgdir, depth=0):
        threading.Thread.__init__(self)
        self.queue = queue
        self.packagesdir = pkgdir
        self.depth = depth

    def run(self):
        while True:
            (gitrepo, ref2fetch) = self.queue.get()
            try:
                (stdout, stderr) = gitrepo.fetch(ref2fetch, self.depth)
                print('------', gitrepo.gdir[:-len('.git')], '------\n' + stderr.decode('utf-8'))
            except GitRepoError as e:
                print('------', gitrepo.gdir[:-len('.git')], '------\n', e)
            self.queue.task_done()

def readconfig(path):
    config = configparser.ConfigParser(delimiters='=', interpolation=None, strict=False)
    config.read(path)
    optionslist = {}
    for option in ('newpkgs', 'prune'):
        if config.has_option('PLD', option):
            optionslist[option] = config.getboolean('PLD', option)
    for option in ('depth', 'repopattern', 'packagesdir', 'remoterefs'):
        if config.has_option('PLD', option):
            optionslist[option] = config.get('PLD', option)
    if config.has_option('PLD','branch'):
        optionslist['branch'] = config.get('PLD', 'branch').split()
    for option in ('jobs'):
        if config.has_option('PLD', option):
            optionslist[option] = config.getint('PLD', option)

    for pathopt in ('packagesdir', 'remoterefs'):
        if pathopt in optionslist:
            optionslist[pathopt] = os.path.expanduser(optionslist[pathopt])
    return optionslist

def initpackage(name, options):
    repo = GitRepo(os.path.join(options.packagesdir, name))
    remotepush = os.path.join(GIT_REPO_PUSH, name)
    repo.init(os.path.join(GIT_REPO, name), remotepush)
    return repo

def createpackage(name, options):
    if subprocess.Popen(['ssh', GITLOGIN + GITSERVER, 'create', name]).wait():
        sys.exit(1)
    initpackage(name, options)

def create_packages(options):
    for package in options.packages:
        createpackage(package, options)

def fetch_packages(options):
    fetch_queue = queue.Queue()
    for i in range(options.jobs):
        t = ThreadFetch(fetch_queue, options.packagesdir, options.depth)
        t.setDaemon(True)
        t.start()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        refs = GitArchiveRefsData(options.branch, options.repopattern)
    except RemoteRefsError as e:
        print('Problem with file {} in repository {}'.format(*e.args), file=sys.stderr)
        sys.exit(1)


    print('Read remotes data')
    updated_repos = []
    for pkgdir in sorted(refs.heads):
        gitdir = os.path.join(options.packagesdir, pkgdir, '.git')
        if not os.path.isdir(gitdir):
            if options.newpkgs:
                gitrepo = initpackage(pkgdir, options)
            else:
                continue
        elif options.omitexisting:
            continue
        else:
            gitrepo = GitRepo(os.path.join(options.packagesdir, pkgdir))
        ref2fetch = []
        for ref in refs.heads[pkgdir]:
            if gitrepo.check_remote(ref) != refs.heads[pkgdir][ref]:
                ref2fetch.append('+{}:{}/{}'.format(ref, REMOTEREFS, ref[len('refs/heads/'):]))
        if ref2fetch:
            ref2fetch.append('refs/notes/*:refs/notes/*')
            fetch_queue.put((gitrepo, ref2fetch))
            updated_repos.append(gitrepo)

    fetch_queue.join()

    if options.prune:
        try:
            refs = GitArchiveRefsData('*')
        except RemoteRefsError as e:
            print('Problem with file {} in repository {}'.format(*e.args), file=sys.stderr)
            sys.exit(1)
        for pattern in options.repopattern:
            for fulldir in glob.iglob(os.path.join(options.packagesdir, pattern)):
                pkgdir = os.path.basename(fulldir)
                if len(refs.heads[pkgdir]) == 0 and os.path.isdir(os.path.join(fulldir, '.git')):
                    print('Removing', fulldir)
                    shutil.rmtree(fulldir)
    return updated_repos

def clone_packages(options):
    for repo in fetch_packages(options):
        try:
            repo.checkout('master')
        except GitRepoError as e:
            print('Problem with checking branch master in repo {}: {}'.format(repo.gdir, e), file=sys.stderr)

def list_packages(options):
    try:
        refs = GitArchiveRefsData(options.branch, options.repopattern)
    except RemoteRefsError as e:
        print('Problem with file {} in repository {}'.format(*e.args), file=sys.stderr)
        sys.exit(1)
    for package in sorted(refs.heads):
        print(package)

common_options = argparse.ArgumentParser(add_help=False)
common_options.add_argument('-d', '--packagesdir', help='local directory with git repositories',
    default=os.path.expanduser('~/PLD_clone/packages'))

common_fetchoptions = argparse.ArgumentParser(add_help=False, parents=[common_options])
common_fetchoptions.add_argument('-j', '--jobs', help='number of threads to use', default=4, type=int)
common_fetchoptions.add_argument('-r', '--remoterefs', help='repository with list of all refs',
    default=os.path.expanduser('~/PLD_clone/Refs.git'))
common_fetchoptions.add_argument('repopattern', nargs='*', default = ['*'])

parser = argparse.ArgumentParser(description='PLD tool for interaction with git repos',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

subparsers = parser.add_subparsers(help='[-h] [options]')
update = subparsers.add_parser('update', help='fetch repositories', parents=[common_fetchoptions],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
update.add_argument('-b', '--branch', help='branch to fetch', action=DelAppend, default=['master'])
update.add_argument('--depth', help='depth of fetch', default=0)
newpkgsopt = update.add_mutually_exclusive_group()
newpkgsopt.add_argument('-n', '--newpkgs', help='download packages that do not exist on local side',
        action='store_true')
newpkgsopt.add_argument('-nn', '--nonewpkgs', help='do not download new packages', dest='newpkgs', action='store_false')
update.add_argument('-P', '--prune', help='prune git repositories that do no exist upstream',
        action='store_true')
update.set_defaults(func=fetch_packages, omitexisting=False)

init = subparsers.add_parser('init', help='init new repository', parents=[common_options],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
init.add_argument('packages', nargs='+', help='list of packages to create')
init.set_defaults(func=create_packages)

clone = subparsers.add_parser('clone', help='clone repositories', parents=[common_fetchoptions],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
clone.set_defaults(func=clone_packages, branch='[*]', prune=False, depth=0, newpkgs=True, omitexisting=True)

fetch = subparsers.add_parser('fetch', help='fetch repositories', parents=[common_fetchoptions],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
fetch.set_defaults(func=clone_packages, branch='[*]', prune=False, depth=0, newpkgs=False, omitexisting=False)

listpkgs = subparsers.add_parser('list', help='list repositories',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
listpkgs.add_argument('-r', '--remoterefs', help='repository with list of all refs',
    default=os.path.expanduser('~/PLD_clone/Refs.git'))
listpkgs.add_argument('-b', '--branch', help='show packages with given branch', action=DelAppend, default=['*'])
listpkgs.add_argument('repopattern', nargs='*', default = ['*'])
listpkgs.set_defaults(func=list_packages)

parser.set_defaults(**readconfig(os.path.expanduser('~/.gitconfig')))
options = parser.parse_args()
options.func(options)
