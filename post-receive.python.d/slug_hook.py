import os
import tempfile

from git_slug.serverconst import WATCHDIR


def run(data):
    global WATCHDIR
    WATCHDIR = os.path.join(os.path.expanduser('~'), WATCHDIR)
    gitrepo = os.environ.get('GL_REPO')
    if gitrepo.startswith('packages/'):
        gitrepo = gitrepo[len('packages/'):]
    else:
        return

    (tfile, name) = tempfile.mkstemp(prefix=gitrepo+'.', dir=WATCHDIR)
    os.write(tfile,(os.getenv('GL_USER')+'\n').encode('utf-8'))
    os.write(tfile,(gitrepo+'\n').encode('utf-8'))
    os.write(tfile,''.join(data).encode('utf-8'))
    os.close(tfile)
