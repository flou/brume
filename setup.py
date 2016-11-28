from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='brumecli',
    version='0.0.1',
    description='AWS Cloudformation deployer',
    url='',
    license='MIT',
    packages=['brumecli'],
    install_requires=required,
    scripts=['brume']
)
