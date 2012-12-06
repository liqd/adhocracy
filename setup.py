try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='adhocracy',
    version='2.0.0-rc.1',
    description='Policy drafting and decision-making web platform',
    author='Liquid Democracy e.V.',
    author_email='info@liqd.net',
    url='https://github.com/liqd/adhocracy',
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
    long_description=open("README.rst").read() + "\n" +
                     open("CHANGES.txt").read() + "\n" +
                     open("AUTHORS.txt").read() + "\n",
    install_requires=[
        "Pylons==0.9.7",
        "WebOb==1.0.8",  # 1.1 removed an imported required by Pylons 0.9.7
        "SQLAlchemy==0.7.9",
        "sqlalchemy-migrate>=0.6",
        "FormEncode_adhocracy_nmu>=1.2.5", # Really FormEncode>=1.2.5 (for <input type=email>), but that's not released yet (=> https://github.com/formencode/formencode/issues/20)
        "repoze.who>=2.0",
        "repoze.what==1.0.8",  # 1.0.9 conflicts with repoze.who>=2.0
        "repoze.who.plugins.sa==1.0rc2",
        "repoze.what-pylons==1.0",
        "repoze.what.plugins.sql==1.0.1",
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
        "sunburnt==0.6",
        "PIL>=1.1.6",
        "Markdown>=2.2.1",
        "lxml>=2.2.6",
        "Mako>=0.4.2",
        "recaptcha-client>=1.0.6",
        "fanstatic >=0.11.2, <=0.11.99",
        "js.jquery >= 1.7.1,<=1.7.99",
        "js.jquery_qtip >= 1.0.0,<= 1.0.99",
        'js.socialshareprivacy >= 1.3dev',
        'js.jquery_joyride',
    ],
    # REFACT: could/should these become regular dependencies?
    setup_requires=["PasteScript>=1.6.3",

                    "setuptools>=0.6c6"],  # fix OS X 10.5.7
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    extras_require={
        'test': ['zope.testbrowser [wsgi]',
                 'repoze.tm2',
                 'mock >=0.8.0, <=0.8.99',
                 'nose',
                 'nose-cov',
                 'nose-exclude',
                 'decorator']
    },
    package_data={'adhocracy': ['i18n/*/LC_MESSAGES/*.mo']},
    message_extractors={'adhocracy': [
            ('**.py', 'python', None),
            ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
            ('static/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'Pylons'],
    entry_points={
        'paste.app_factory': [
            'main = adhocracy.config.middleware:make_app'
        ],
        'paste.paster_command': [
            'background = adhocracy.lib.cli:Background',
            'index = adhocracy.lib.cli:Index'
        ],
        'paste.app_install': [
            'main = pylons.util:PylonsInstaller'
        ],
        'fanstatic.libraries': [
            'stylesheets = adhocracy.static:stylesheets_library',
            'yaml = adhocracy.static:yaml_library',
            'autocomplete = adhocracy.static:autocomplete_library',
            'placeholder = adhocracy.static:placeholder_library',
            'jquerytools = adhocracy.static:jquerytools_library',
            'knockout = adhocracy.static:knockout_library',
            'misc = adhocracy.static:misc_library',
            'adhocracy = adhocracy.static:adhocracy_library',
            'bootstrap = adhocracy.static:bootstrap_library',
        ]
    }
)
