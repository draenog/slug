#!/usr/bin/python3

from distutils.core import setup

setup(name='git-core-slug',
      version='0.1',
      description='Scripts to interact with PLD git repos',
      author='Kacper Kornet',
      author_email='draenog@pld-linux.org',
      url='https://github.com/draenog/slug',
      classifiers=['Programming Language :: Python :: 3'],
      packages=['git_slug'],
      scripts=['slug.py']
     )
