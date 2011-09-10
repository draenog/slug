#!/usr/bin/python

import glob
import sys
import os
import shutil
import Queue
import threading

import argparse

import signal

from gitconst import *
from gitrepo import GitRepo, GitRepoError
from refsdata import *


class ThreadFetch(threading.Thread):
    def __init__(self, queue, dir, depth=0):
        threading.Thread.__init__(self)
        self.queue = queue
        self.packagesdir = dir
        self.depth = depth

    def run(self):
        while True:
            (package, ref2fetch) = self.queue.get()
            gitrepo = GitRepo(os.path.join(self.packagesdir, package))
            (stdout, stderr) = gitrepo.fetch(ref2fetch, self.depth)
            print '------', package, '------\n' + stderr
            self.queue.task_done()

def get_user():
        email=GitRepo().configvalue('user.email')
        if email:
            email = email.partition('@')[0]
        return email

def initpackage(name, options):
    repo = GitRepo(os.path.join(options.packagesdir, name))
    if options.user:
        remotepush = 'ssh://' + os.path.join(options.user+GIT_REPO_PUSH ,name)
    else:
        remotepush = None
    repo.init(os.path.join(GIT_REPO,name), remotepush)
    return repo

def fetch_packages(options):
    fetch_queue = Queue.Queue()
    for i in range(options.j):
        t = ThreadFetch(fetch_queue, options.packagesdir, options.depth)
        t.setDaemon(True)
        t.start()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        refs = GitRemoteRefsData(options.remoterefs, options.branch, options.dirpattern)
    except GitRepoError as e:
        print >> sys.stderr, 'Cannot create repository {}'.format(e)
        sys.exit()
    except RemoteRefsError as e:
        print >> sys.stderr, 'Problem with file {} in repository {}'.format(*e)
        sys.exit()


    print 'Read remotes data'
    for dir in sorted(refs.heads):
        gitdir = os.path.join(options.packagesdir, dir, '.git')
        if not os.path.isdir(gitdir):
            if options.newpkgs:
                gitrepo = initpackage(dir, options)
            else:
                continue
        else:
            gitrepo = GitRepo(os.path.join(options.packagesdir, dir))
        ref2fetch = []
        for ref in refs.heads[dir]:
            if gitrepo.check_remote(ref) != refs.heads[dir][ref]:
                ref2fetch.append('+{}:{}/{}'.format(ref, REMOTEREFS, ref[len('refs/heads/'):]))
        if ref2fetch:
            fetch_queue.put((dir, ref2fetch))

    fetch_queue.join()

    if options.prune:
        try:
            refs = GitRemoteRefsData(options.remoterefs, '*')
        except RemoteRefsError as e:
            print >> sys.stderr, 'Problem with file {} in repository {}'.format(*e)
            sys.exit()
        for fulldir in glob.iglob(os.path.join(options.packagesdir,options.dirpattern)):
            dir = os.path.basename(fulldir)
            if len(refs.heads[dir]) == 0 and os.path.isdir(os.path.join(fulldir, '.git')):
                print 'Removing', fulldir
                shutil.rmtree(fulldir)


parser = argparse.ArgumentParser(description='PLD tool for interaction with git repos',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-b', '--branch', help='branch to fetch', default = 'master')
parser.add_argument('-P', '--prune', help='prune git repositories that do no exist upstream', action='store_true')
parser.add_argument('-j', help='number of threads to use', default=4, type=int)
parser.add_argument('-d', '--packagesdir', help='local directory with git repositories',
        default=os.path.join(os.getenv('HOME'),'PLD_clone/packages'))
parser.add_argument('--depth', help='depth of fetch', default=0)
parser.add_argument('-n', '--newpkgs', help='download packages that do not exist on local side', action='store_true')
parser.add_argument('-r', '--remoterefs', help='repository with list of all refs',
        default=os.path.join(os.getenv('HOME'),'PLD_clone/Refs.git'))
parser.add_argument('-u', '--user', help='the user name to register for pushes for new repositories', default = get_user())
parser.add_argument('dirpattern', nargs='?', default = '*')
options = parser.parse_args()

fetch_packages(options)
