import cgi
from itertools import izip_longest
from string import count

from lxml.html.diff import htmldiff

from adhocracy import model
from adhocracy.lib.cache import memoize
from adhocracy.lib.text.normalize import simple_form
from adhocracy.lib.text.render import (render, render_line_based, _line_table,
                                       linify)

LINEBREAK_TOKEN = 23
SPACE_TOKEN = 42


def _diff_html(left, right):
    return htmldiff(left, right)


def _decompose(text):
    if text is None:
        return []
    _tokens = []
    for line in text.split('\n'):
        line = line.replace('\r', '')
        for token in line.split(' '):
            if len(token):
                _tokens.append(simple_form(token))
            _tokens.append(SPACE_TOKEN)
        _tokens.pop()
        _tokens.append(LINEBREAK_TOKEN)
    return _tokens


def _compose(elems):
    lines = []
    line = ''
    for elem in elems:
        if elem == LINEBREAK_TOKEN:
            lines.append(line)
            line = ''
        elif elem == SPACE_TOKEN:
            line += ' '
        else:
            line += elem
    lines.append(line)
    return '\n'.join([cgi.escape(l) for l in lines])


def _diff_line_based(left_text, right_text, include_deletions=True,
                     include_insertions=True, replace_as_insert=False,
                     replace_as_delete=False, ratio_skip=0.7,
                     line_length=model.Text.LINE_LENGTH):
    from difflib import SequenceMatcher
    left = _decompose(left_text)
    right = _decompose(right_text)
    s = SequenceMatcher(None, left, right)

    html_match = ''
    for op, i1, i2, j1, j2 in s.get_opcodes():
        if op == 'equal':
            html_match += _compose(left[i1:i2])
        elif op == 'delete' and include_deletions:
            html_match += '<del>' + _compose(left[i1:i2]) + '</del>'
        elif op == 'insert' and include_insertions:
            html_match += '<ins>' + _compose(right[j1:j2]) + '</ins>'
        elif op == 'replace':
            if replace_as_delete:
                html_match += '<del>' + _compose(left[i1:i2]) + '</del>'
            if replace_as_insert:
                html_match += '<ins>' + _compose(right[j1:j2]) + '</ins>'
            if not (replace_as_delete or replace_as_insert):
                html_match += '<span>' + _compose(right[j1:j2]) + '</span>'

    carry = []
    lines = []
    for line in linify(html_match, line_length):
        for val in reversed(carry):
            line = val + line
        carry = []
        for tag_begin, tag_end in (('<span>', '</span>'),
                                   ('<ins>', '</ins>'),
                                   ('<del>', '</del>')):
            begin_count = count(line, tag_begin)
            end_count = count(line, tag_end)
            if begin_count > end_count:
                line = line + tag_end
                carry.append(tag_begin)
            elif begin_count < end_count:
                line = tag_begin + line
        lines.append(line)

    return lines


@memoize('rev_diff')
def comment_revisions_compare(rev_from, rev_to):
    if rev_to is None:
        return render(rev_from.text)
    return _diff_html(render(rev_to.text),
                      render(rev_from.text))


@memoize('titles_diff')
def page_titles_compare(text_from, text_to):
    if text_to is None or text_from.id == text_to.id:
        return text_from.title
    return _diff_html(text_to.title,
                      text_from.title)


def page_texts_history_compare(text_from, text_to):
    if text_from.page.function == model.Page.NORM:
        return norm_texts_history_compare(text_from, text_to)
    if text_to is None or text_from.id == text_to.id:
        return render(text_from.text)
    return _diff_html(render(text_to.text),
                      render(text_from.text))


@memoize('norms_diff')
def norm_texts_history_compare(text_from, text_to):
    '''
    Note: Inverts from and to inside. Be prepared;)
    '''
    if text_to is None or text_from.id == text_to.id:
        return render_line_based(text_from)
    lines = _diff_line_based(text_to.text,
                             text_from.text,
                             replace_as_insert=True)
    return _line_table(lines)


@memoize('norms_diff_inline')
def norm_texts_inline_compare(text_from, text_to):
    if text_to is None or text_from.id == text_to.id:
        return render_line_based(text_from)
    lines = _diff_line_based(text_from.text,
                             text_to.text,
                             replace_as_insert=True,
                             replace_as_delete=True)
    return _line_table(lines)


@memoize('normtab_diff')
def norm_texts_table_compare(text_from, text_to):
    insertions = _diff_line_based(text_from.text,
                                  text_to.text,
                                  include_insertions=True,
                                  include_deletions=False,
                                  replace_as_insert=True,
                                  ratio_skip=0.8)

    deletions = _diff_line_based(text_from.text,
                                 text_to.text,
                                 include_insertions=False,
                                 include_deletions=True,
                                 replace_as_delete=True,
                                 ratio_skip=0.8)

    llines = []
    rlines = []
    for left, right in izip_longest(deletions, insertions, fillvalue=''):
        llines.append(left)
        rlines.append(right)
    return _line_table(llines), _line_table(rlines)
