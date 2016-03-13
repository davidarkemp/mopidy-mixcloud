from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-Mixcloud',
    version=get_version('mopidy_mixcloud/__init__.py'),
    url='https://github.com/david.a.r.kemp/mopidy-mixcloud',
    license='MIT',
    author='david.a.r.kemp',
    author_email='david.a.r.kemp@gmail.com',
    description='Mixcloud extension for Mopidy',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Pykka >= 1.1',
        'requests >= 2.0.0',
    ],
    entry_points={
        'mopidy.ext': [
            'mixcloud = mopidy_mixcloud:MixcloudExtension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
