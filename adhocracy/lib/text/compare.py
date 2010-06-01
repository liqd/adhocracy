
from .diff_match_patch import diff_match_patch

def compare_html(left, right):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(left, right)
    #print "STAGE 1", diffs
    dmp.diff_cleanupSemantic(diffs)
    full_diff = []
    for (op, text) in diffs:
        if op == dmp.DIFF_INSERT:
            text = u"<ins>%s</ins>" % text
        elif op == dmp.DIFF_DELETE:
            text = u"<del>%s</del>" % text
        full_diff.append(text)
    #print "STAGE 2", diffs
    #print "STAGE 3", dmp.diff_toDelta(diffs)
    #print "DIFF", u"".join(full_diff)
    return u"".join(full_diff)
    
    