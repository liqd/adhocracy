try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

from scripts.version import get_git_version


setup(
    name='adhocracy',
    version=get_git_version(),
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
    long_description='\n'.join([open(f).read() for f in [
        "README.rst",
        "INSTALLATION.md",
        "CHANGES.txt",
        "AUTHORS.txt",
    ]]),
    install_requires=[
        "adhocracy-Pylons>=1.0.1",
        "WebOb==1.2.3",
        "SQLAlchemy==0.7.10",
        "sqlalchemy-migrate>=0.6",
        "FormEncode>=1.2.5",
        "repoze.who>=2.0",
        "repoze.what==1.0.8",  # 1.0.9 conflicts with repoze.who>=2.0
        "repoze.who.plugins.sa==1.0rc2",
        "repoze.what.plugins.sql==1.0.1",
        "repoze.who-friendlyform==1.0.8",
        "repoze.who-testutil==1.0",
        "python-twitter>=0.6",
        "oauth2",  # undeclared requirement of python-twitter
        "oauth>=1.0.1",
        "rq",
        "redis",
        "ordereddict",
        "babel>=0.9",
        "beautifulsoup>=3.0.7",
        "python-openid>=2.2.4",
        "python-memcached>=1.45",
        "sunburnt==0.6",
        "PIL>=1.1.6",
        "Markdown>=2.3",
        "lxml>=2.2.6",
        "Mako>=0.7.3",
        "MarkupSafe>=0.15",
        "recaptcha-client>=1.0.6",
        "fanstatic >=0.11.2",
        "js.jquery >= 1.7.1,<=1.7.99",
        "js.jquery_qtip >= 1.0.0,<= 1.0.99",
        "js.socialshareprivacy >= 1.3-1",
        "js.jquery_joyride",
        "PasteScript>=1.6.3",
        "setuptools_git >= 0.3",
        "ipaddress>=1.0.3",
        "pytz",
    ],
    setup_requires=["setuptools>=0.6c6",  # fix OS X 10.5.7
                    "PasteScript",
                    "Babel"],
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    include_package_data=True,
    exclude_package_data={'': ['.gitignore'],
                          'images': ['*.xcf', '*.blend']},
    test_suite='nose.collector',
    extras_require={
        'test': ['zope.testbrowser [wsgi]',
                 'repoze.tm2',
                 'mock >=0.8.0, <=0.8.99',
                 'nose',
                 'nose-cov',
                 'nose-exclude',
                 'cssselect',
                 'decorator',
                 'pep8',]
    },
    package_data={'adhocracy': ['i18n/*/LC_MESSAGES/*.mo'],
                  '': ['RELEASE-VERSION'],
                  },
    message_extractors={'src/adhocracy': [
        ('**.py', 'python', None),
        ('templates/**.html', 'mako', {'input_encoding': 'utf-8'}),
        ('static/**', 'ignore', None)]},
    zip_safe=False,
    paster_plugins=['PasteScript', 'adhocracy_Pylons'],
    entry_points={
        'paste.app_factory': [
            'main = adhocracy.config.middleware:make_app'
        ],
        'paste.paster_command': [
            'worker = adhocracy.lib.cli:Worker',
            'timer = adhocracy.lib.cli:Timer',
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
        ],
        'nose.plugins': [
            'pylons = pylons.test:PylonsPlugin',
        ]

    }
)
