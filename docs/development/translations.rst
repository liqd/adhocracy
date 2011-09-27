Update translations
===================

Adhocracy uses Babel_ to manage translations with gettext message catalogs.
It has some babel commands preconfigured in setup.cfg. 

.. CAUTION:: If you use the 
   `adhocracy.buildout`_ you
   need to use the ``--distribute`` option to ``bootstrap.py``.

Babel command
-------------

``(adhocracy)/src/adhocracy$ adhocpy setup.py extract_messages``
   Extract the messages from the python files and templates into 
   ``adhocracy/i18n/adhocracy.pot``

``(adhocracy)/src/adhocracy$ adhocpy setup.py update_catalog``
   Use the ``adhocray.pot``file to update the ``.po`` files for all
   languages in ``adhocracy/i18n/{LANG}/LC_MESSAGES/adhocracy.po``.
   For new msgids babel will try to find a similar msgid and
   automatically insert a msgstr. This is only a helper and
   those msgstrs (marked with ``, fulzzy`` in the ``.po`` file
   will not be included into the compiled ``.mo`` files.

``(adhocracy)/src/adhocracy$ adhocpy setup.py compile_catalog``
  Compile the ``.po`` files for all languages to ``.mo`` files.

Translation workflow
--------------------


1. extract new messages to the ``.pot`` file with ``extract_messages``.
2. update the ``.po`` files with ``update_catalog``
3. edit the ``.po`` files for your language(s). 

   The prefered way to edit ``.po`` files is to use an application like 
   poedit_. It will highlight untranslated messages and messages that
   where created with fuzzy matching and will automatically
   update or remove markers like ``, fuzzy`` and update the header of the
   ``.po`` file.

4. compile the catalogs with ``compile_catalog``

   This will also show you errors in the ``.po`` files and statistics
   about translation

Now you can commit the translations or send the files or a patch to
the `adhocracy mailing list`_.

.. _Babel: http://babel.edgewall.org/
.. _adhocracy.buildout: https://bitbucket.org/liqd/adhocracy.buildout
.. _poedit: http://www.poedit.net/
.. _adhocracy mailing list: 
  http://lists.liqd.net/cgi-bin/mailman/listinfo/adhocracy-dev
