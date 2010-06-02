
from .diff_match_patch import diff_match_patch


class html_diff_generator(object):
    
    def __init__(self, left, right):
        self.left = left
        self.right = right 
        self.in_tag = False
        self.out = u""

    def section(self, text, tag = None):
        is_open = False
        if not self.in_tag and tag:
            is_open = True 
            self.out += u"<%s>" % tag
        
        for ch in text:
            if ch == u'<':
                self.in_tag = True
                if tag and is_open:
                    self.out += u"</%s>" % tag
            self.out += ch
            if ch == u'>':
                self.in_tag = False
                if tag and not is_open:
                    self.out += u"<%s>" % tag
        
        if is_open and tag and not self.in_tag:
            self.out += u"</%s>" % tag
        
         


def compare_html(left, right):
    dmp = diff_match_patch()
    diffs = dmp.diff_main(left, right)
    #print "STAGE 1", diffs
    dmp.diff_cleanupSemantic(diffs)
    levenshtein = dmp.diff_levenshtein(diffs) 
    if len(left) > 1 and levenshtein > (max(len(left), len(right)) * 0.5):
        return "<del>%s</del><ins>%s</ins>" % (left, right)
    full_diff = html_diff_generator(left, right)
    for (op, text) in diffs:
        if op == dmp.DIFF_INSERT:
            full_diff.section(text, "ins")
            
        elif op == dmp.DIFF_DELETE:
            full_diff.section(text, "del")
        else:
            full_diff.section(text, None)
    
    return full_diff.out
    
    