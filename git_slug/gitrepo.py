from .gitconst import *

import os
from subprocess import PIPE
import subprocess

class GitRepoError(Exception):
    pass

class GitRepo:
    def __init__(self, working_tree = None, git_dir = None):
        self.wtree = working_tree
        self.command_prefix = ['git']
        if git_dir is None and working_tree is not None:
            self.gdir = os.path.join(working_tree, '.git')
        else:
            self.gdir = git_dir
        if self.gdir is not None:
            self.command_prefix.append('--git-dir='+self.gdir)
        if self.wtree is not None:
            self.command_prefix.append('--work-tree='+self.wtree)

    def command(self, clist):
        return subprocess.Popen(self.command_prefix + clist, stdout=PIPE, stderr=PIPE, bufsize=-1)

    def commandio(self, clist):
        return self.command(clist).communicate()

    def commandexc(self, clist):
        proc = self.command(clist)
        (out, err) = proc.communicate()
        if proc.returncode:
            raise GitRepoError(err.decode('utf-8'))
        return (out, err)

    def checkout(self, branch):
        clist = ['checkout', '-m', branch]
        return self.commandexc(clist)

    def commitfile(self, path, message):
        clist = ['commit', '-m', message, path]
        self.commandio(clist)

    def configvalue(self, option):
        clist = ['config', '-z', option]
        try:
            return self.commandexc(clist)[0].decode("utf-8")
        except GitRepoError:
            return None

    def fetch(self, fetchlist=[], depth = 0, remotename=REMOTE_NAME):
        clist = ['fetch']
        if depth:
            clist.append('--depth={}'.format(depth))
        clist += [ remotename ] + fetchlist
        return self.commandexc(clist)

    def init(self, remotepull, remotepush = None, remotename=REMOTE_NAME):
        clist = ['git', 'init']
        if self.wtree is not None:
            clist.append(self.wtree)
        else:
            clist.extend(['--bare', self.gdir])
        if subprocess.call(clist):
            raise GitRepoError(self.gdir)
        self.commandio(['remote', 'add', remotename, remotepull])
        if remotepush is not None:
            self.commandio(['remote', 'set-url', '--push', remotename, remotepush])
        self.commandio(['config', '--local', '--add', 'remote.{}.fetch'.format(remotename),
            'refs/notes/commits:refs/notes/commits'])

    def check_remote(self, ref, remote=REMOTE_NAME):
        ref = ref.replace(REFFILE, os.path.join('remotes', remote))
        try:
            with open(os.path.join(self.gdir, ref), 'r') as f:
                localref = f.readline().strip()
        except IOError:
            localref = EMPTYSHA1
        return localref

    def showfile(self, filename, ref='origin/master'):
        clist = ['show', ref + ':' + filename]
        return self.command(clist)
