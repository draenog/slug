#!/usr/bin/python3

from distutils.core import setup
from distutils.command.install_data import install_data
import os

class post_install(install_data):
    def run(self):
        super().run()
        dirfd =os.open(os.path.join(self.install_dir, self.data_files[0][0]), os.O_RDONLY)
        os.symlink('move', 'copy', dir_fd=dirfd)
        os.close(dirfd)


setup(name='git-core-slug',
      version='0.13',
      description='Scripts to interact with PLD git repos',
      author='Kacper Kornet',
      author_email='draenog@pld-linux.org',
      url='https://github.com/draenog/slug',
      classifiers=['Programming Language :: Python :: 3'],
      packages=['git_slug', 'Daemon'],
      data_files=[('adc/bin', ['adc/trash', 'adc/move'])],
      scripts=['slug.py', 'slug_watch'],
      cmdclass={"install_data": post_install}
     )
