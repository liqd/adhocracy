"""Showmore extension for Markdown.

To hide something with [more...], surround the corresponding text with triple
parentheses, e.g. (((text_to_be_hidden))).

In order to show the text, you have to include the following Javascript in your
code, which depends on the availability of jquery.

    $('.showmore').each(function () {
        var self = $(this);
        self.find('.showmore_morelink').bind('click', function (event) {
            event.preventDefault();
            self.find('.showmore_morelink').css('display', 'none');
            self.find('.showmore_uncollapsed').css('display', 'inline');
        });
        self.find('.showmore_lesslink').bind('click', function (event) {
            event.preventDefault();
            self.find('.showmore_morelink').css('display', 'inline');
            self.find('.showmore_uncollapsed').css('display', 'none');
        });
    });

Additionally, you have to add the following to your css code:
    .showmore {
        display: inline;
    }
    .showmore_uncollapsed {
        /* initial state */
        display: none;
    }
    .showmore_morelink, .showmore_lesslink {
        text-transform: lowercase;
        font-variant: small-caps;
        white-space: nowrap;
    }
"""

import re
import markdown
from pylons.i18n import _


SHOWMORE_RE = re.compile(r'\({3,}(?P<text>.*?)\){3,}',
                         re.MULTILINE | re.DOTALL)

PRE_HTML = u'''
<div class="showmore">
    <a class="showmore_morelink" href="#">[%s]</a>
    <div class="showmore_uncollapsed">
'''

POST_HTML = u'''
        <a class="showmore_lesslink" href="#">[%s]</a>
    </div>
</div>
'''


class ShowmoreExtension(markdown.Extension):
    """ Showmore Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.preprocessors.add('showmore', ShowmorePreprocessor(md),
                             '>normalize_whitespace')


class ShowmorePreprocessor(markdown.preprocessors.Preprocessor):

    def run(self, lines):
        text = "\n".join(lines)
        while 1:
            m = SHOWMORE_RE.search(text)
            if m:

                text = '%s%s%s%s%s' % (
                    text[:m.start()],
                    self.markdown.htmlStash.store(PRE_HTML % _(u'show more'),
                                                  safe=True),
                    m.group('text'),
                    self.markdown.htmlStash.store(POST_HTML % _(u'show less'),
                                                  safe=True),
                    text[m.end():])
            else:
                break
        return text.split("\n")


def makeExtension(configs=None):
    return ShowmoreExtension(configs=configs)
