from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='brume',
    version='0.0.1',
    description='AWS Cloudformation deployer',
    url='',
    license='MIT',
    packages=['brume'],
    install_requires=required,
    entrypoints={
        'console_scripts': [
            'brume = brume.cli:cli'
        ]
    }
)
