import re
import cgi

import markdown2 as markdown
#from webhelpers.text import truncate

from adhocracy.lib.cache import memoize
import adhocracy.model as model

markdowner = markdown.Markdown() 

SUB_USER = re.compile("@([a-zA-Z0-9_\-]{3,255})")

def user_sub(match):
    from adhocracy.lib import helpers as h
    user = model.User.find(match.group(1))
    if user is not None:
        return h.user.link(user)
    return match.group(0)
    

SUB_PAGE = re.compile("\[\[([^(\]\])]{3,255})\]\]", re.M)

def page_sub(match):
    from adhocracy.lib import helpers as h
    page_name = match.group(1)
    variant = model.Text.HEAD
    if '/' in page_name:
        page_name, variant = page_name.split('/', 1)
    page = model.Page.find_fuzzy(page_name, include_deleted=True) 
    if page is not None:
        if page.is_deleted():
            return page_name
        return h.page.link(page, variant=variant, icon=not (page.function == page.DOCUMENT))
    else:
        from adhocracy.forms import FORBIDDEN_NAMES
        return h.page.redlink(page_name)


SUB_TRANSCLUDE = re.compile("@@([^(@@)]{3,255})@@", re.M)

def transclude_sub(transclude_path):
    if transclude_path is None:
        transclude_path = []
    
    def render_transclusion(match):
        from adhocracy.lib import helpers as h
        page_name, variant = match.group(1), model.Text.HEAD
        if '/' in page_name:
            page_name, variant = page_name.split('/', 1)
        page = model.Page.find_fuzzy(page_name) 
        if variant not in page.variants:
            variant = model.Text.HEAD
        if (page is not None) and (page.id not in transclude_path):
            transclude_path.append(page.id)
            text = page.variant_head(variant).text
            return render(text, transclude_path=transclude_path)
        return match.group(0)
    
    return render_transclusion


def render(text, substitutions=True, transclude_path=None):
    if text is None:
        return ""
    text = cgi.escape(text)
    text = markdowner.convert(text)
    if substitutions:
        text = SUB_USER.sub(user_sub, text)
        text = SUB_PAGE.sub(page_sub, text)
        #text = SUB_TRANSCLUDE.sub(transclude_sub(transclude_path), text)
    return text


def _line_table(lines):
    _out = "<table class='line_based'>"
    for num, line in enumerate(lines):
        _out += """\t<tr>
                        <td class='line_number'>%s</td>
                        <td class='line_text'><pre>%s</pre></td>
                     </tr>\n""" % (num+1, line)
    _out += "</table>\n"
    return _out

@memoize('text_render')
def render_line_based(text_obj): 
    if not text_obj.text:
        return ""
    return _line_table([cgi.escape(l) for l in text_obj.lines])


def truncate(text, length):
    if len(text) <= length:
        return text
    
    last_space = len(text)
    in_tag = False
    render_count = 0
    for i, c in enumerate(text):
        if c.isspace():
            last_space = i + 1
        elif c == '<':
            in_tag = True
            continue
        elif c == '>':
            in_tag = False
            continue
        
        if not in_tag:
            render_count += 1
        if render_count >= length:
            break
    x = text[:last_space]
    return x
    
    
def linify(text, length):
    for line in text.strip().split("\n"):
        #print "LINE", line.encode('utf-8')
        while True:
            part = truncate(line, length)
            #print "PART", part.encode('utf-8')
            yield part
            line = line[len(part):]
            if not len(line):
                break

