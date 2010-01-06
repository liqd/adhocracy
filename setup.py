try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='adhocracy',
    version='0.3',
    description='Community decision process manager',
    author='Liquid Democracy e.V.',
    author_email='info@adhocracy.de',
    url='http://www.adhocracy.de',
    install_requires=[
        "Pylons>=0.9.7",
        "SQLAlchemy>=0.5",
        "FormEncode>=1.2.2",
        "repoze.who>=1.0.15",
        "repoze.what>=1.0.8",
        "repoze.who.plugins.sa>=1.0rc2",
        "repoze.what-pylons>=1.0",
        "repoze.what.plugins.sql>=1.0rc1",
        "repoze.who-friendlyform>=1.0b3",
        "repoze.who-testutil>=0.9",
        "python-twitter>=0.6",
        "oauth>=1.0.1",
        "amqplib>=0.6.1",
        "babel>=0.9",
        "beautifulsoup>=3.1",
        "python-openid>=2.2.4",
        "python-memcached>=1.45",
        "Whoosh>=0.3.9",
        "PIL>=1.1.6"
    ],
    # REFACT: could/should these become regular dependencies?
    setup_requires=["PasteScript>=1.6.3", "setuptools>=0.6c6"], # fix OS X 10.5.7
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    package_data={'adhocracy': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors={'adhocracy': [
            ('**.py', 'python', None),
            ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
            ('public/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points="""
    [paste.app_factory]
    main = adhocracy.config.middleware:make_app

    [paste.app_install]
    main = pylons.util:PylonsInstaller
    """,
)
