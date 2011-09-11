try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='adhocracy',
    version='1.2dev',
    description='Policy drafting and decision-making web platform',
    author='Liquid Democracy e.V.',
    author_email='info@liqd.net',
    url='http://adhocracy.cc/',
    license='GNU Affero General Public License v3',
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Other Audience",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Environment :: Web Environment",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    long_description="""\
Adhocracy is a policy drafting tool for distributed groups.
It allows members of organizations or the public to compose
or vote documents that represent the policy of the group.

In order to allow cooperation, Adhocracy uses LiquidDemocracy,
a set of ideas that include delegating a user's voting rights
to another to enable both active and passive participation in
the process. We also implement ideas from  Direkter Parlamentarismus,
a theory of mass participation in parliamentary processes.

Installation instructions and further information can be found at
http://trac.adhocracy.cc/wiki/InstallationInstructions

This version requires Python 2.5 or later.
""",
    install_requires=[
        "Pylons==0.9.7",
        "WebOb==1.0.8",  # 1.1 removed an imported required by Pylons 0.9.7
        "SQLAlchemy==0.6.8",
        "sqlalchemy-migrate>=0.6",
        "FormEncode>=1.2.2",
        "repoze.who>=2.0a1",
        "repoze.what==1.0.8",  # 1.0.9 conflicts with repoze.who>=2.0
        "repoze.who.plugins.sa==1.0rc2",
        "repoze.what-pylons==1.0",
        "repoze.what.plugins.sql==1.0rc4",
        "repoze.who-friendlyform==1.0.4",
        "repoze.who-testutil==1.0",
        "python-twitter>=0.6",
        "oauth2",  # undeclared requirement of python-twitter
        "oauth>=1.0.1",
        "amqplib>=0.6.1",
        "babel>=0.9",
        "beautifulsoup>=3.0.7",
        "python-openid>=2.2.4",
        "python-memcached>=1.45",
        "solrpy==0.9.3",
        "sunburnt==0.5",
        "PIL>=1.1.6",
        "markdown2>=1.0.1",
        "lxml>=2.2.6"
    ],
    # REFACT: could/should these become regular dependencies?
    setup_requires=["PasteScript>=1.6.3",
                    "setuptools>=0.6c6"],  # fix OS X 10.5.7
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'adhocracy': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors={'adhocracy': [
            ('**.py', 'python', None),
            ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
            ('static/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = adhocracy.config.middleware:make_app

    [paste.paster_command]
    background = adhocracy.lib.cli:Background
    index = adhocracy.lib.cli:Index

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
