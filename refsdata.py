
import collections
import fnmatch
import os
from gitconst import EMPTYSHA1, REFFILE, REFREPO, GITSERVER
from gitrepo import GitRepo


class RemoteRefsError(Exception):
    pass

class RemoteRefsData:
    def __init__(self, stream, pattern, dirpattern='*'):
        self.heads = collections.defaultdict(lambda: collections.defaultdict(lambda: EMPTYSHA1))
        pattern = os.path.join('refs/heads', pattern)
        for line in stream.readlines():
            (sha1, ref, repo) = line.split()
            if fnmatch.fnmatchcase(ref, pattern) and fnmatch.fnmatchcase(repo, dirpattern):
                self.heads[repo][ref] = sha1

    def put(self, repo, data):
        for line in data:
            (sha1_old, sha1, ref) = line.split()
            self.heads[repo][ref] = sha1

    def dump(self, stream):
        for repo in sorted(self.heads):
                for ref in sorted(self.heads[repo]):
                    if self.heads[repo][ref] != EMPTYSHA1:
                        stream.write('{} {} {}\n'.format(self.heads[repo][ref], ref, repo))

class GitRemoteRefsData(RemoteRefsData):
    def __init__(self, path, pattern, dirpattern='*'):
        refsrepo = GitRepo(git_dir=path)
        if not os.path.isdir(refsrepo.gdir):
            refsrepo.init('git://' + os.path.join(GITSERVER, REFREPO))
        refsrepo.fetch(depth=1)
        showfile = refsrepo.showfile(REFFILE)
        RemoteRefsData.__init__(self, showfile.stdout, pattern, dirpattern)
        if showfile.wait():
            raise RemoteRefsError(REFFILE, path)
