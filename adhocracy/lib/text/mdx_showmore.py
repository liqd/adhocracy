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

import markdown
from markdown.util import etree
from pylons.i18n import _

SHOWMORE_RE = r'(\(\(\()(.*)(\)\)\))'

MORE_STRING = u'[more...]'
LESS_STRING = u'[less...]'


def spaceSpan():
    span = etree.Element('span')
    span.text = u' '
    return span

class ShowmorePattern(markdown.inlinepatterns.Pattern):
    """ Return a superscript Element (`word^2^`). """
    def handleMatch(self, m):
        supr = m.group(3)
        
        text = supr
        s = etree.Element('span', {'class': 'showmore'})

        scol = etree.Element('span', {'class': 'showmore_collapsed'})
        s.append(scol)
        
        am = etree.Element('a',
                     {'href': '#', 'class': 'showmore_morelink'})
        am.text = markdown.util.AtomicString(_(MORE_STRING))
        scol.append(spaceSpan())
        scol.append(am)
        scol.append(spaceSpan())

        suncol = etree.Element('span',
                     {'class': 'showmore_uncollapsed',
                      'style': 'display: none'})
        s.append(suncol)

        sc = etree.Element('span',
                     {'class': 'showmore_content'})
        sc.text = supr
        suncol.append(sc)

        al = etree.Element('a',
                     {'href': '#', 'class': 'showmore_lesslink'})
        al.text = markdown.util.AtomicString(_(LESS_STRING))
        suncol.append(spaceSpan())
        suncol.append(al)
        suncol.append(spaceSpan())

        return s
        

class ShowmoreExtension(markdown.Extension):
    """ Superscript Extension for Python-Markdown. """

    def extendMarkdown(self, md, md_globals):
        """ Replace superscript with SuperscriptPattern """
        md.inlinePatterns['showmore'] = ShowmorePattern(SHOWMORE_RE, md)

def makeExtension(configs=None):
    return ShowmoreExtension(configs=configs)
