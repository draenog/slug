import os
import tempfile


def run(data):
    WATCHDIR = os.getenv('WATCHDIR')
    if WATCHDIR is None:
        print('Envrionment variable WATCHDIR not defined', file=sys.stderr)
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
