#!/usr/bin/python

from distutils.core import setup

setup(name='pldrepo',
      version='0.001',
      description='Scripts to interact with PLD git repos',
      author='Kacper Kornet',
      author_email='draenog@pld-linux.org',
      url='https://github.com/draenog/slug',
      packages=['pldrepo'],
      scripts=['slug.py']
     )
