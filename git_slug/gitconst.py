from os.path import join

EMPTYSHA1 = '0000000000000000000000000000000000000000'
REMOTE_NAME = 'origin'
REMOTEREFS = join('refs/remotes/', REMOTE_NAME)

GITLOGIN = 'draenog@'
GITSERVER = 'git.pld-linux.org'
_packages_dir = 'packages'
_packages_remote = join(GITSERVER, _packages_dir)
GIT_REPO = 'git://' + _packages_remote
GIT_REPO_PUSH = 'ssh://' + GITLOGIN + _packages_remote
REFREPO = 'Refs'
REFFILE = 'heads'
