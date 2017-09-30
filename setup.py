#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup module.
"""

import io
import os
import re
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

from brume import VERSION

# Package meta-data.
NAME = 'brume'
DESCRIPTION = 'AWS Cloudformation deployer. '
URL = 'https://github.com/flou/brume'
AUTHORS = {
    'ferrand@ekino.com': 'Lou Ferrand',
}

# What packages are required for this module to be executed?
REQUIRED = [
    'boto3>=1.4.5',
    'crayons==0.1.2',
    'click>=6.7',
    'PyYAML==3.12',
    'Jinja2==2.9.6',
    'pytz==2017.2',
    'delegator.py==0.0.13',
]

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

HERE = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.rst' is present in your MANIFEST.in file!
with io.open(os.path.join(HERE, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = '\n' + f.read()


def _download_url():
    return '{repo}/repository/archive.tar.gz?ref={version}'.format(
        repo=URL, version=VERSION
    )


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(HERE, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    name='brume',
    version=re.sub(r'[^\d\.]', '', VERSION),
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url=URL,
    author=', '.join(AUTHORS.values()),
    author_email=', '.join(AUTHORS.keys()),
    license='MIT',
    packages=find_packages(exclude=['tests', 'cover']),
    include_package_data=True,
    download_url=_download_url(),
    zip_safe=False,
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'moto'],
    keywords=['AWS', 'CloudFormation'],
    install_requires=[
        'boto3>=1.4.5',
        'crayons==0.1.2',
        'click>=6.7',
        'PyYAML==3.12',
        'Jinja2==2.9.6',
        'pytz==2017.2',
        'delegator.py==0.0.13',
    ],
    entry_points={
        'console_scripts': ['brume=brume.cli:cli']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
