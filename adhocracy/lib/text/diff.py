from string import count
from itertools import izip_longest
from lxml.html.diff import htmldiff
from .diff_match_patch import diff_match_patch

import adhocracy.model as model
from render import render, render_line_based, _line_table

def _diff_html(left, right):
    return htmldiff(left, right)

LINEBREAK_TOKEN = 23

def _decompose(lines):
    _tokens = []
    for line in lines:
        line = line.replace('\r', '')
        _tokens.extend(line.split(' '))
        _tokens.append(LINEBREAK_TOKEN)
    return _tokens
    
def _compose(elems):
    lines = []
    line = []
    for elem in elems:
        if elem == LINEBREAK_TOKEN:
            lines.append(' '.join(line))
            line = []
        else:
            line.append(elem)
    lines.append(' '.join(line))
    return '\n'.join(lines)
        

def _diff_line_based(left_lines, right_lines, include_deletions=True, include_insertions=True, 
                     replace_as_insert=False, replace_as_delete=False, ratio_skip=None):
    from difflib import SequenceMatcher
    #dmp = diff_match_patch()
    left = _decompose(left_lines)
    #print repr(left).encode('utf-8')
    right = _decompose(right_lines)
    #print repr(right).encode('utf-8')
    #diffs = dmp.diff_main(left_text, right_text)
    #dmp.diff_cleanupSemantic(diffs)
    s = SequenceMatcher(None, left, right)

    #lev_ratio = dmp.diff_levenshtein(diffs)/float(max(len(left_text), len(right_text), 1))
    if ratio_skip is not None and s.ratio() >= ratio_skip and False: 
        lines = []
        for l, r in izip_longest(left_lines, right_lines, fillvalue=''):
            line = ''
            if include_deletions:
                line += '<del>%s</del>' % l 
            if include_insertions:
                line += '<ins>%s</ins>' % r
            lines.append(line)
        return lines

    html_match = ''
    for op, i1, i2, j1, j2 in s.get_opcodes():
        
        #x = ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
        #           (op, i1, i2, left[i1:i2], j1, j2, right[j1:j2]))
        #print x.encode('utf-8')
        
        if op == 'equal':
            html_match += _compose(left[i1:i2])
        elif op == 'delete' and include_deletions:
            html_match += ' <del>' + _compose(left[i1:i2]) + '</del> '
        elif op == 'insert' and include_insertions:
            html_match += ' <ins>' + _compose(right[j1:j2]) + '</ins> '
        elif op == 'replace':
            if include_insertions and replace_as_insert:
                html_match += ' <ins>' + _compose(right[j1:j2]) + '</ins> '
            if include_deletions and replace_as_delete:
                html_match += ' <del>' + _compose(left[i1:i2]) + '</del> '
    
    carry = []
    lines = []
    for line in html_match.split('\n'):
        for val in carry:
            line = val + line
        carry = []
        for tag_begin, tag_end in ((' <ins>', '</ins> '), (' <del>', '</del> ')):
            begin_count = count(line, tag_begin)
            end_count = count(line, tag_end)
            if begin_count > end_count:
                line = line + tag_end
                carry.append(tag_begin)
            elif begin_count < end_count:
                line = tag_begin + line
        #print "LINE", line.encode('utf-8')
        lines.append(line.replace('\n', ''))
    return lines


def comment_revisions_compare(rev_from, rev_to):
    if rev_to is None:
        return render(rev_from.text)
    return _diff_html(render(rev_to.text),
                      render(rev_from.text))

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

def norm_texts_history_compare(text_from, text_to):
    if text_to is None or text_from.id == text_to.id:
        return render_line_based(text_from)
    lines = _diff_line_based(list(text_to.lines), 
                             list(text_from.lines),
                             replace_as_insert=True)
                             #replace_as_delete=True)
    return _line_table(lines)
                            

def norm_texts_table_compare(text_from, text_to):
    insertions = _diff_line_based(list(text_from.lines), 
                                  list(text_to.lines),
                                  include_deletions=False,
                                  replace_as_insert=True,
                                  ratio_skip=0.8)
    deletions = _diff_line_based(list(text_from.lines), 
                                 list(text_to.lines),
                                 include_insertions=False,
                                 replace_as_delete=True,
                                 ratio_skip=0.8)
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