Update translations
===================

Translations for contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We manage our translations in a `Transifex project`_. If you want to
change a translation you can go to the project page, choose your
language and click on the resource "Adhocracy". You will get a menu
where you can download the .po file to edit it on your computer with
an application like `poedit`_ ("Download for use"). After you
translated the file you can go to the menu and upload the file. From
the menu you can also use the transifex online editor (Button: "✔
Translate now")

It would be nice to drop us a note before you start to translate, to
adhocracy-dev@lists.liqd.net or info@liqd.net. You can also contact us
to set up a new language on transifex.

Translations for developers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adhocracy uses Babel_ together with Transifex to manage translations.
Both are preconfigured in setup.cfg and .tx/config.


Preperations
------------

NOTE:: This document assumes that you installed the buildout in a virtualenv
"adhocracy". Otherwise, your shell prompt will look slightly different.

Install the `transifex client`_ on your system.  Then add your
username and password for transifex.com to `~/.transifexrc`::

    [https://www.transifex.com]
    hostname = https://www.transifex.com
    username = <your transifex username>
    password = <your transifex password>
    token =

Translation workflow
--------------------

All .po and .pot files should go through transifex before they are
committed. This might be annoying but unifies the formatting and
makes it easier to review commits.

Extract new messages
''''''''''''''''''''
1. Extract new messages with ``extract_messages``. This will update
   ``adhocracy/i18n/adhocracy.pot``::

     (adhocracy)$ bin/adhocpy setup.py extract_messages

2. Push that to transifex::

     (adhocracy)$ tx push --source

3. Pull all files from transifex::

     (adhocracy)$ tx pull

   If it skips languages the files on transifex are older than the
   files on your system. See Troubleshooting.

4. Commit adhocracy.pot::

     (adhocracy)$ git commit adhocracy/i18n/adhocracy.pot \
     > -m 'i18n: extract new messages'

Update the translations
'''''''''''''''''''''''
1. Go to the transifex project and use the the online translation
   editor to translate and continue with 4.

   Or translate it locally. To do that make sure you have pulled the
   most recent translations from transifex::

     (adhocracy)$ tx pull  # pulls all languages or
     (adhocracy)$ tx pull -l <language>

2. Edit the ``.po`` files for your language(s).

   INFO:: The prefered way to edit ``.po`` files is to use an
   application like poedit_. It will highlight untranslated messages
   and messages that were created with fuzzy matching and will
   automatically update or remove markers like ``, fuzzy`` and update
   the header of the ``.po`` file.

3. Push the translation to transifex::

     (adhocracy)$ tx push -l <language>

4. Pull the translation back::

     (adhocracy)$ tx pull -l <language>

5. Compile the catalogs with ``compile_catalog``::

     (adhocracy)$ bin/adhocpy setup.py compile_catalog

   This will also show you errors in the ``.po`` files and statistics
   about the translation.

6. Commit the .po and .mo files of the language(s) you translated, e.g.::

     (adhocracy)$ git commit adhocracy/i18n/de' -m 'i18n: ...'


Troubleshooting
'''''''''''''''

If tx skips the languages you want to pull from the server, the local
file is most likely newer than the file on transifex.com. You can add
`-d` to the command to get debug output, e.g.::

  tx -d pull -l de

Than you have to check which of the files to use. Copy the local file
and pull the language (with `-f`/`--force`) from transifex...::

  (adhocracy)$ cd src/adhocracy/i18n/de/LC_MESSAGES
  (adhocracy) .../de/LC_MESSAGES$ cp adhocracy.po local.po
  (adhocracy) .../de/LC_MESSAGES$ tx pull -f -l de

..and compare them. A good tool to compare is podiff from the `Python
GetText Translation Toolkit`_ (which you can install from source of
from their ubuntu ppa). It contains several other tools to work with
po-files. You might have to give the `-r` (relax) option to podiff.
::

  (adhocracy) .../de/LC_MESSAGES$ podiff local.po adhocracy.po

(There is also another `podiff package`_ on pypi.)

If `tx push --source` fails with `HTTP Error 401: UNAUTHORIZED`, you
need to be added to the transifex project as a maintainer. Contact one of
the existing maintainers for that.

Babel commands
''''''''''''''

``(adhocracy)$ bin/adhocpy setup.py extract_messages``
   Extract the messages from the python files and templates into
   ``adhocracy/i18n/adhocracy.pot``

``(adhocracy)$ bin/adhocpy setup.py compile_catalog``
  Compile the ``.po`` files for all languages to ``.mo`` files.

The babel command `update_catalog` should not be used anymore. Use the
tx client instead.


.. _Babel: http://babel.edgewall.org/
.. _Transifex project: https://www.transifex.com/projects/p/adhocracy/
.. _transifex client: http://pypi.python.org/pypi/transifex-client
.. _poedit: http://www.poedit.net/
.. _Python GetText Translation Toolkit: https://launchpad.net/pyg3t
.. _podiff package: http://pypi.python.org/pypi/podiff
