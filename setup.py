import os

from setuptools import find_packages, setup

from brume import VERSION


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='brume',
    version=VERSION,
    description='AWS Cloudformation deployer',
    long_description=read('README.rst'),
    url='https://github.com/flou/brume',
    author='Lou Ferrand',
    author_email='ferrand@ekino.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'moto'],
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
