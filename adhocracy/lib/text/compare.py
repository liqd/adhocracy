
from .diff_match_patch import diff_match_patch

def patch_html(text, tag):
    out = u"<%s>" % tag
    for ch in text:
        if ch == u'<':
            out += u"</%s>" % tag
        out += ch
        if ch == u'>':
            out += u"<%s>" % tag
    return out + u"</%s>" % tag

def compare_html(left, right):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(left, right)
    #print "STAGE 1", diffs
    #dmp.diff_cleanupSemantic(diffs)
    levenshtein = dmp.diff_levenshtein(diffs) 
    if len(left) > 1 and levenshtein > (max(len(left), len(right)) * 0.5):
        return "<del>%s</del><ins>%s</ins>" % (left, right)
    full_diff = []
    for (op, text) in diffs:
        if op == dmp.DIFF_INSERT:
            text = patch_html(text, "ins")
        elif op == dmp.DIFF_DELETE:
            text = patch_html(text, "del")
        full_diff.append(text)
    #print "STAGE 2", diffs
    #print "STAGE 3", dmp.diff_toDelta(diffs)
    #print "DIFF", u"".join(full_diff)
    return u"".join(full_diff)
    
    