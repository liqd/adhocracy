from string import count
from itertools import izip_longest
from lxml.html.diff import htmldiff

import adhocracy.model as model
from adhocracy.lib.cache import memoize
from render import render, render_line_based, _line_table

def _diff_html(left, right):
    return htmldiff(left, right)

LINEBREAK_TOKEN = 23
SPACE_TOKEN = 42

def _decompose(lines, line_breaks=True):
    _tokens = []
    for line in lines:
        line = line.replace('\r', '')
        for token in line.split(' '):
            if len(token):
                _tokens.append(token)
            _tokens.append(SPACE_TOKEN)
        _tokens.pop()
        if line_breaks:
            _tokens.append(LINEBREAK_TOKEN)
    return _tokens
    
def _compose(elems):
    lines = []
    line = []
    for elem in elems:
        if elem == LINEBREAK_TOKEN:
            lines.append(''.join(line))
            line = []
        elif elem == SPACE_TOKEN:
            line.append(' ')
        else:
            line.append(elem)
    lines.append(''.join(line))
    return '\n'.join(lines)
        

def _diff_line_based(left_lines, right_lines, include_deletions=True, include_insertions=True, 
                     replace_as_insert=False, replace_as_delete=False, skip_left_newlines=True, 
                     skip_right_newlines=False, ratio_skip=0.7):
    from difflib import SequenceMatcher
    left = _decompose(left_lines, line_breaks=skip_left_newlines)
    right = _decompose(right_lines, line_breaks=skip_right_newlines)
    s = SequenceMatcher(None, left, right)

    if ratio_skip is not None and s.ratio() <= 1-ratio_skip: 
        lines = []
        if include_deletions:
            for l in left_lines:
                lines.append('<del>%s</del>' % l)
        if include_insertions:
            for r in right_lines:
                lines.append('<ins>%s</ins>' % r)
        return lines

    html_match = ''
    for op, i1, i2, j1, j2 in s.get_opcodes():
        if op == 'equal':
            html_match += _compose(left[i1:i2])
        elif op == 'delete' and include_deletions:
            html_match += '<del>' + _compose(left[i1:i2]) + '</del>'
        elif op == 'insert' and include_insertions:
            html_match += '<ins>' + _compose(right[j1:j2]) + '</ins>'
        elif op == 'replace':
            if include_deletions and replace_as_delete:
                html_match += '<del>' + _compose(left[i1:i2]) + '</del>'
            if include_insertions and replace_as_insert:
                html_match += '<ins>' + _compose(right[j1:j2]) + '</ins>'
    
    carry = []
    lines = []
    for line in html_match.split('\n'):
        for val in carry:
            line = val + line
        carry = []
        for tag_begin, tag_end in (('<ins>', '</ins>'), ('<del>', '</del>')):
            if line.startswith(tag_end):
                line = line[len(tag_end):]
            if line.endswith(tag_begin):
                line = line[:len(line)-len(tag_begin)]
            begin_count = count(line, tag_begin)
            end_count = count(line, tag_end)
            if begin_count > end_count:
                line = line + tag_end
                carry.append(tag_begin)
            elif begin_count < end_count:
                line = tag_begin + line
        if line.startswith(' <'):
            line = line[1:]
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

#@memoize('texts_diff')
def page_texts_history_compare(text_from, text_to):
    if text_from.page.function == model.Page.NORM:
        return norm_texts_history_compare(text_from, text_to)
    if text_to is None or text_from.id == text_to.id:
        return render(text_from.text)
    return _diff_html(render(text_to.text),
                      render(text_from.text))

@memoize('norms_diff')
def norm_texts_history_compare(text_from, text_to):
    if text_to is None or text_from.id == text_to.id:
        return render_line_based(text_from)
    lines = _diff_line_based(list(text_to.lines), 
                             list(text_from.lines),
                             replace_as_insert=True)
    return _line_table(lines)
                            
@memoize('normtab_diff')
def norm_texts_table_compare(text_from, text_to):
    insertions = _diff_line_based(list(text_from.lines), 
                                  list(text_to.lines),
                                  include_deletions=False,
                                  replace_as_insert=True,
                                  skip_left_newlines=False,
                                  skip_right_newlines=True,
                                  ratio_skip=0.7)
    deletions = _diff_line_based(list(text_from.lines), 
                                 list(text_to.lines),
                                 include_insertions=False,
                                 replace_as_delete=True,
                                 ratio_skip=0.7)
    insertions.pop()
    deletions.pop()
              
    _out = "<table class='line_based'>\n"
    for num, (left, right) in enumerate(izip_longest(deletions, insertions, fillvalue='')):
        #print "LINE", repr(line).encode('utf-8')
        _out += """\t<tr>
                        <td width='2%%' class='line_number'>%s</td>
                        <td width='49%%' class='line_text'><pre>%s</pre></td>
                        <td width='2%%' class='line_number'>%s</td>
                        <td width='47%%' class='line_text'><pre>%s</pre></td>
                     </tr>\n""" % (num+1, left, num+1, right)
    _out += "</table>\n"
    return _out