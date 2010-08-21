from string import count
from itertools import izip_longest
from lxml.html.diff import htmldiff
from .diff_match_patch import diff_match_patch

import adhocracy.model as model
from render import render, render_line_based, _line_table

def _diff_html(left, right):
    return htmldiff(left, right)


def _diff_line_based(left_lines, right_lines, include_deletions=True, include_insertions=True, ratio_skip=0.8):
    dmp = diff_match_patch()
    left_text = '\n'.join(left_lines)
    right_text = '\n'.join(right_lines)
    diffs = dmp.diff_main(left_text, right_text)
    dmp.diff_cleanupSemantic(diffs)
    
    lev_ratio = dmp.diff_levenshtein(diffs)/float(max(len(left_text), len(right_text), 1))
    if lev_ratio >= ratio_skip:
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
    for op, text in diffs:
        if op == 0:
            html_match += text
        elif op == -1 and include_deletions:
            html_match += '<del>' + text + '</del>'
        #elif op == -1 and not include_deletions:
        #    html_match += text
        elif op == 1 and include_insertions:
            html_match += '<ins>' + text + '</ins>'
        #elif op == 1 and not include_insertions:
        #    html_match += text
    
    lines = []
    carry = None
    for line in html_match.split('\n'):
        if carry:
            line = carry + line 
            carry = None
        for tag_begin, tag_end in (('<ins>', '</ins>'), ('<del>', '</del>')):
            begin_count = count(line, tag_begin)
            end_count = count(line, tag_end)
            if begin_count > end_count:
                line = line + tag_end
                carry = tag_begin
            elif begin_count < end_count:
                line = tag_begin + line
        lines.append(line)            
    return lines

def comment_revisions_compare(rev_from, rev_to):
    if rev_to is None:
        return render(rev_from.text)
    return _diff_html(render(rev_to.text),
                      render(rev_from.text))

def page_title_compare(text_form, text_to):
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
                             list(text_from.lines))
    return _line_table(lines)
                            

def norm_texts_table_compare(text_from, text_to):
    insertions = _diff_line_based(list(text_from.lines), 
                                  list(text_to.lines),
                                  include_deletions=False)
    deletions = _diff_line_based(list(text_from.lines), 
                                 list(text_to.lines),
                                 include_insertions=False)
                            
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