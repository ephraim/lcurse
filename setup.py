#!/usr/bin/env python3

from distutils.core import setup

setup(
        name='lcurse',
        version='2.0.0',
        description='A Curse compatible client for Linux.',
        url='https://github.com/ephraim/lcurse',
        packages=['modules'],
        scripts=['lcurse', 'console.py'],
        license='Unlicense',
)
