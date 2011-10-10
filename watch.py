#!/usr/bin/python3

import asyncore
import os
import pyinotify
import sys
import time

from git_slug.gitconst import REFREPO, REFFILE, WATCHDIR
from git_slug.refsdata import RemoteRefsData
from git_slug.gitrepo import GitRepo


PIDFILE = os.path.expanduser('~/watch.pid')
REFREPO_WDIR = os.path.expanduser('~/Refs')
REFREPO_GDIR = os.path.join(os.path.expanduser('~/repositories'), REFREPO+'.git')

wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_CLOSE_WRITE # watched events

def process_file(pathname):
    print("Reading:", pathname)
    if not os.path.isfile(pathname):
        print('{} is not an ordinary file'.format(pathname))
        return
    with open(os.path.join(REFREPO_WDIR, REFFILE), 'r+') as headfile:
        refs = RemoteRefsData(headfile, '*')
    with open(pathname, 'r') as newfile:
        gitrepo = newfile.readline().strip()
        data = newfile.readlines()
    refs.put(gitrepo, data)
    with open(os.path.join(REFREPO_WDIR, REFFILE), 'w') as headfile:
        refs.dump(headfile)
        headfile.flush()
        os.fsync(headfile.fileno())
    headrepo = GitRepo(REFREPO_WDIR, REFREPO_GDIR)
    headrepo.commitfile(REFFILE, 'Changes in {}'.format(gitrepo))
    print('Removing file', pathname)
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
