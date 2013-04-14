import os

from setuptools import find_packages
from setuptools import setup

project = 'adhocracy_kotti'
version = '0.1'

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
#pyramid rest service helpers
    'cornice',
#pyramd kotti cms to handle static pages
    'Kotti',
]

tests_requires = [
# webtest browser
    "webtest",
# pytest
    "pytest",
    "pytest-cov",
    "pytest-pep8",
# kotti testing
    "kotti[testing]"
]

setup(
    name=project,
    version=version,
    description="Adhocracy Kotti CMS",
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Pylons",
        "Framework :: Pyramid",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: User Interfaces",
    ],
    keywords='kotti',
    author='Liquid Democracy e.V.',
    author_email='info@liqd.net',
    url='https://github.com/liqd/adhocracy',
    license='GNU Affero General Public License v3',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_requires=tests_requires,
    extras_require=dict(
        testing=tests_requires, ),
    entry_points={
    },
)
