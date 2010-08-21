from lxml.html.diff import htmldiff
from .diff_match_patch import diff_match_patch

import adhocracy.model as model
from render import render, render_line_based

def _diff_html(left, right):
    return htmldiff(left, right)

def _diff_line_based(left_lines, right_lines):
    left_text = ''.join(left_lines)
    right_text = ''.join(right_lines)
    dmp = diff_match_patch()
    diffs = dmp.diff_main(left_text, right_text)
    dmp.diff_cleanupSemantic(diffs)
    for op, text in diffs:
        print "OP", op, "D", text.encode('utf-8')
    return ""
    

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
    return _diff_line_based(list(text_from.lines), 
                            list(text_to.lines))