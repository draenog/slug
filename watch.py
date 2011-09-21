#!/usr/bin/python3

import heapq
import os
import pyinotify
import shutil

from git_slug.gitconst import REFREPO, REFFILE
from git_slug.serverconst import WATCHDIR
from git_slug.refsdata import RemoteRefsData
from git_slug.gitrepo import GitRepo


PIDFILE = os.path.expanduser('~/watch.pid')
REFFILE_NEW = REFFILE + '.new'
REFREPO_WDIR = os.path.expanduser('~/Refs')
REFREPO_GDIR = os.path.join(os.path.expanduser('~/repositories'), REFREPO+'.git')

WATCHDIR=WATCHDIR

wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_CLOSE_WRITE # watched events

def convertstream(stream):
    for line in stream:
        (sha1, ref, repo) = line.split()
        yield (repo, ref, 1, sha1)

def processnewfile(stream):
    repo = stream.readline().strip()
    for line in stream:
        (sha1old, sha1, ref) = line.split()
        if ref.startswith('refs/heads/'):
            yield (repo, ref, 0, sha1)


def process_file(pathname):
    if not os.path.isfile(pathname):
        print('{} is not an ordinary file'.format(pathname))
        return
    with open(os.path.join(REFREPO_WDIR, REFFILE),'r') as headfile, open(os.path.join(REFREPO_WDIR, REFFILE_NEW),'w') as headfile_new, open(pathname, 'r') as newfile:
        committer = newfile.readline().strip()
        oldtuple = None
        for (repo, ref, number, sha1) in heapq.merge(sorted(processnewfile(newfile)), convertstream(headfile)):
            if (repo, ref) == oldtuple:
                continue
            oldtuple = (repo, ref)
            print(sha1, ref, repo, file=headfile_new)
    shutil.copyfile(os.path.join(REFREPO_WDIR, REFFILE_NEW), os.path.join(REFREPO_WDIR, REFFILE))

    headrepo = GitRepo(REFREPO_WDIR, REFREPO_GDIR)
    headrepo.commitfile(REFFILE, 'Changes by {}'.format(committer))
    os.remove(pathname)

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        process_file(event.pathname)

if not os.path.isdir(WATCHDIR):
    print('Creating {}'.format(WATCHDIR))
    os.mkdir(WATCHDIR)
notifier = pyinotify.Notifier(wm, EventHandler())
wdd = wm.add_watch(WATCHDIR, mask, rec=False)

for filename in sorted(os.listdir(WATCHDIR), key=lambda f: os.stat(os.path.join(WATCHDIR, f)).st_mtime):
    process_file(os.path.join(WATCHDIR,filename))

notifier.loop(daemonize=True, pid_file=os.path.expanduser(PIDFILE),
            stdout=os.path.expanduser('~/watch.stdout'))
