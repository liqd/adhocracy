"""Showmore extension for Markdown.

To hide something with [more...], surround the corresponding text with triple
parentheses, e.g. (((text_to_be_hidden))).

In order to show the text, you have to include the following Javascript in your
code, which depends on the availability of jquery.

    $('.showmore').each(function () {
        var self = $(this);
        self.find('.showmore_morelink').bind('click', function (event) {
                self.find('.showmore_collapsed').css('display', 'none');
                self.find('.showmore_uncollapsed').css('display', 'inline');
            });
        self.find('.showmore_lesslink').bind('click', function (event) {
                self.find('.showmore_collapsed').css('display', 'inline');
                self.find('.showmore_uncollapsed').css('display', 'none');
            });
    });
"""

import re
import markdown
from markdown.util import etree
from pylons.i18n import _


SHOWMORE_RE = re.compile(r'\({3,}(?P<text>.*?)\){3,}',
                             re.MULTILINE|re.DOTALL)

MORE_STRING = u'[more...]'
LESS_STRING = u'[less...]'

PRE_HTML = u'''
<div class="showmore" style="display: inline">
    <span class="showmore_collapsed">
        <span> </span>
        <a class="showmore_morelink" href="#">%s</a>
        <span> </span>
    </span>
    <div class="showmore_uncollapsed" style="display: none">
        <div class="showmore_content" style="display: inline">
'''

POST_HTML = u'''
        </div>
        <span> </span>
        <a class="showmore_lesslink" href="#">%s</a>
        <span> </span>
    </div>
</div>
'''

class ShowmoreExtension(markdown.Extension):
    """ Showmore Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.preprocessors.add('showmore', ShowmorePreprocessor(md), "_begin")


class ShowmorePreprocessor(markdown.preprocessors.Preprocessor):

    def run(self, lines):
        text = "\n".join(lines)
        while 1:
            m = SHOWMORE_RE.search(text)
            if m:

                pretext = self.markdown.htmlStash.store('<pre>vorher</pre>', safe=True)
                posttext = self.markdown.htmlStash.store('<pre>nachher</pre>', safe=True)

                text = '%s%s%s%s%s' % (
                    text[:m.start()],
                    self.markdown.htmlStash.store(PRE_HTML % _(MORE_STRING), safe=True),
                    m.group('text'),
                    self.markdown.htmlStash.store(POST_HTML % _(LESS_STRING), safe=True),
                    text[m.end():])
            else:
                break
        return text.split("\n")


def makeExtension(configs=None):
    return ShowmoreExtension(configs=configs)
