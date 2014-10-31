from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import os
import re

rel_file = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')


def get_version():
    data = open(rel_file('xmodels', '__init__.py')).read()
    return re.search(r"__version__ = '([^']+)'", data).group(1)

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='xmodels',
    version=get_version(),
    description='Python xmodels contains all the xmodels you need to create a Python package.',
    long_description=readme + '\n\n' + history,
    author='Bernd Meyer',
    author_email='berndca@gmail.com',
    url='https://github.com/berndca/xmodels',
    packages=['xmodels'],
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='xmodels',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)