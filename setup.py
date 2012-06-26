#!/usr/bin/python3

from distutils.core import setup

setup(name='git-core-slug',
      version='0.7',
      description='Scripts to interact with PLD git repos',
      author='Kacper Kornet',
      author_email='draenog@pld-linux.org',
      url='https://github.com/draenog/slug',
      classifiers=['Programming Language :: Python :: 3'],
      packages=['git_slug', 'Daemon'],
      data_files=[('adc/bin', ['adc/trash', 'adc/move'])],
      scripts=['slug.py', 'slug_watch']
     )
