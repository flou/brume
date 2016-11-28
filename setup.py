import re
from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

with open('brume/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(
    name='brume',
    version=version,
    description='AWS Cloudformation deployer',
    url='',
    license='MIT',
    packages=['brume'],
    install_requires=required,
    scripts=['brume.py']
)
