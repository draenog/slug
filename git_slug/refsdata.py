
import collections
import fnmatch
import os
import re
import tarfile
from .gitconst import EMPTYSHA1, REFFILE, REFREPO, GITSERVER
from .gitrepo import GitRepo


class RemoteRefsError(Exception):
    pass

class RemoteRefsData:
    def __init__(self, stream, pattern, dirpattern=('*',)):
        self.heads = collections.defaultdict(lambda: collections.defaultdict(lambda: EMPTYSHA1))
        pats = re.compile('|'.join(fnmatch.translate(os.path.join('refs/heads', p)) for p in pattern))
        dirpat = re.compile('|'.join(fnmatch.translate(p) for p in dirpattern))
        for line in stream.readlines():
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            (sha1, ref, repo) = line.split()
            if pats.match(ref) and dirpat.match(repo):
                self.heads[repo][ref] = sha1

    def put(self, repo, data):
        for line in data:
            (sha1_old, sha1, ref) = line.split()
            if(ref.startswith('refs/heads/')):
                self.heads[repo][ref] = sha1

    def dump(self, stream):
        for repo in sorted(self.heads):
            for ref in sorted(self.heads[repo]):
                if self.heads[repo][ref] != EMPTYSHA1:
                    stream.write('{} {} {}\n'.format(self.heads[repo][ref], ref, repo))

class GitRemoteRefsData(RemoteRefsData):
    def __init__(self, path, pattern, dirpattern=('*')):
        refsrepo = GitRepo(git_dir=path)
        if not os.path.isdir(refsrepo.gdir):
            refsrepo.init('git://' + os.path.join(GITSERVER, REFREPO))
        refsrepo.fetch(depth=1)
        showfile = refsrepo.showfile(REFFILE)
        RemoteRefsData.__init__(self, showfile.stdout, pattern, dirpattern)
        if showfile.wait():
            raise RemoteRefsError(REFFILE, path)

class GitArchiveRefsData(RemoteRefsData):
    def __init__(self, path, pattern, dirpattern=('*')):
        fullrefrepo = 'git://{}/{}'.format(GITSERVER, REFREPO)
        archcmd = GitRepo(None, None).command(['archive', '--format=tgz', '--remote={}'.format(fullrefrepo), 'HEAD'])
        try:
            tar = tarfile.open(fileobj=archcmd.stdout, mode='r|*')
        except tarfile.TarError:
            raise RemoteRefsError(REFFILE, fullrefrepo)
        member = tar.next()
        if member.name != REFFILE:
            raise RemoteRefsError(REFFILE, fullrefrepo)
        RemoteRefsData.__init__(self, tar.extractfile(member), pattern, dirpattern)
        if archcmd.wait():
            raise RemoteRefsError(REFFILE, fullrefrepo)
