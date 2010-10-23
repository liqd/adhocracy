try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from adhocracy import __version__

setup(
    name='adhocracy',
    version=__version__,
    description='Community decision-making web platform',
    author='Liquid Democracy e.V.',
    author_email='info@liqd.net',
    url='http://wiki.liqd.net/Adhocracy',
    install_requires=[
        "Pylons==0.9.7",
        "SQLAlchemy>=0.6",
        "sqlalchemy-migrate>=0.6",
        "FormEncode>=1.2.2",
        "repoze.who==2.0a1",
        "repoze.what==1.0.8", # 1.0.9 conflicts with repoze.who>=2.0
        "repoze.who.plugins.sa==1.0rc2",
        "repoze.what-pylons==1.0",
        "repoze.what.plugins.sql==1.0rc4",
        "repoze.who-friendlyform==1.0.4",
        "repoze.who-testutil==1.0",
        "python-twitter>=0.6",
        "oauth>=1.0.1",
        "amqplib>=0.6.1",
        "babel>=0.9",
        "beautifulsoup>=3.0.7",
        "python-openid>=2.2.4",
        "python-memcached>=1.45",
        "solrpy==0.9.3",
        "PIL>=1.1.6",
        "markdown2>=1.0.1",
        "lxml>=2.2.6"
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
