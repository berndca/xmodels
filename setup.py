from setuptools import setup
from setuptools.command.test import test as TestCommand
import os
import sys
import io
import re

rel_file = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def get_version():
    data = read(rel_file('xmodels', '__init__.py'))
    return re.search(r"__version__ = '([^']+)'", data).group(1)

readme = read('README.rst')
history = read('HISTORY.rst').replace('.. :changelog:', '')


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

requirements = [
    'six', 'ordereddict'
]

test_requirements = [
    'pytest'
]

setup(
    name='xmodels',
    version=get_version(),
    description='Python models for creation, parsing and validation of XML documents.',
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