from lxml.html.diff import htmldiff
from .diff_match_patch import diff_match_patch

import adhocracy.model as model
from render import render, render_line_based, _line_table

def _diff_html(left, right):
    return htmldiff(left, right)


def _diffs_lines(diffs):
    line = []
    for op, text in diffs:
        cur_line = ''
        for chr in text:
            if chr == '\n':
                if len(cur_line):
                    line.append((op, cur_line))
                yield line
                line = []
                cur_line = ''
                continue
            cur_line += chr
        if len(cur_line):
            line.append((op, cur_line))
    if len(line):  
        yield line
        
    

def ___x_diff_line_based(left_lines, right_lines):
    left_text = '\n'.join(left_lines)
    right_text = '\n'.join(right_lines)
    print "LEFT: ", left_text.encode('utf-8')
    print "RITE: ", right_text.encode('utf-8')
    dmp = diff_match_patch()
    diffs = dmp.diff_main(left_text, right_text)
    dmp.diff_cleanupSemantic(diffs)
    _out = "<table class='line_based'>\n"
    for num, line in enumerate(_diffs_lines(diffs)):
        print "LINE", repr(line).encode('utf-8')
        _line = ''
        for op, text in line:
            _line += {0: lambda l: l,
                      1: lambda l: "<ins>%s</ins>" % l,
                     -1: lambda l: "<del>%s</del>" % l}.get(op)(text)
        _out += """\t<tr>
                        <td class='line_number'>%s</td>
                        <td class='line_text'><pre>%s</pre></td>
                     </tr>\n""" % (num+1, _line)
    _out += "</table>\n"
    return _out

def _diff_line_based(left_lines, right_lines):
    from difflib import ndiff
    lines = []
    for diff in ndiff(left_lines, right_lines):
        print "DIFF", diff.encode('utf-8')
        val = diff[2:]
        if diff.startswith('+'):
            lines.append("<ins>" + val + "</ins>")
        elif diff.startswith('-'):
            lines.append("<del>" + val + "</del>")
        elif diff.startswith(' '):
            lines.append(val)
    return _line_table(lines)

def comment_revisions_compare(rev_from, rev_to):
    if rev_to is None:
        return render(rev_from.text)
    return _diff_html(render(rev_to.text),
                      render(rev_from.text))

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
    return _diff_line_based(list(text_to.lines), 
                            list(text_from.lines))