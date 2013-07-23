Stylesheets
===========


Why no framework
----------------

In the past adhocracy's stylesheets were based on YAML_ and Bootstrap_.
We also considered using Foundation_. However we decided to not use any of them
because all of those frameworks do more than we wanted them to do. For example
they all include button layouts which collide with our own. This let to
UI bugs in the past.

While we do not use a full framework we try to be somewhat compatible in
both code structure and wording.


Code structure
--------------

Instead of using whole frameworks we split our existing code into
a more modular structure. To have some advanced features available we
decided to use the SASS_ preprocessor extended by some libraries and
the command line utility from compass_.
The new folder struture looks like this::

    ...
    - adhocracy
      - static
        - stylesheets
          - adhocracy.css
      - static_src
        - stylesheets
          - adhocracy.scss
          - _overwrite.scss
          - _variables.scss
          - general
            - ...
          - components
            - _type.scss
            - _forms.scss
            - _button.scss
            - ...
          - widgets
            - _content_list.scss
            - ...

`adhocracy.scss` is the main stylesheet. It imports all the others. All the other
filenames should begin with an underscore. This way they will be ignored by the SASS
precompiler and only adhocracy.scss will be converted to css.

`_variables.scss` contains some variables (mostly colors) which can be used in
all stylesheets. `_overwrite.scss` is empty and should only be used in themes.

The stylesheets are structured in three categories (and therefore folders):
`general`, `components` and `widgets`.
Components are self-contained elements like links, buttons or the vote component.
Widgets are larger blocks which may contain components, e.g. header or sidebar.
Everything which does not match one of these categories goes into general, especially
mixin definitions or helper classes.

The generated CSS can be found in `adhocracy/static/stylesheets`.


Running SASS
------------

The SASS precompiler is run automatically by buildout. You can also run it manually
using `bin/compass compile -c etc/compass.rb` from the root directory. You can also
use other compass commands like `watch` which is usefull to make it watch your files
and automatically recompile whenever it detects changes.


Debugging
---------

There is a list of nearly all components on `http://adhocracy.lan:5001/debug/components`
(only available in development mode).

Some compass commands like `stats` might also by helpful.


Extending the stylesheets
-------------------------

When creating new components or widgets you should create a new file in the
corresponding folder and add an entry in `src/adhocracy/templates/debug/components.html`.


Theming
-------

When theming is enabled and `adhocracy_code:compass_theme_dir` is set accordingly
buildout will use the `adhocracy.scss` from your theme.
However when SASS tries to import a file that is not available in your theme
it will fall back to the default theme. So basically you only need to copy `adhocracy.scss`
from the default theme. You can then start customizing using only `_variables.scss` and
`_overwrite.scss`. But if you want more you can also overwrite whole components.

If you do not want to replace a whole component you should think about creating
a file with the suffix `_overwrite` (e.g. `gerneral/_mixins_overwrite.scss`)
instead of throwing everything into `_overwrite.scss`.

Migration from the old `style_custom.css` system
................................................

In the past a common way to theme an adhocracy installation was to create a
`style_custom.css` stylesheets which overwrites many definitions from
the default theme and include it using diazo.

Merging of the new stylesheet system broke the old theming because an `adhocracy.scss`
file is required in every theme.

So to migrate your theme to the new system simply copy `adhocracy.scss` from the default
theme to `${theme-dir}/static_src/adhocracy.scss`. You may also want to move
`style_custom.css` to `${theme-dir}/static_src/_overwrite.scss` and remove the old diazo.


.. _YAML: http://www.yaml.de/
.. _Bootstrap: http://twitter.github.io/bootstrap/
.. _Foundation: http://foundation.zurb.com/
.. _SASS: http://sass-lang.com/
.. _compass: http://compass-style.org/
