import os
import shutil
import logging
import re
from pylons.i18n import _
from pylons import config
from BeautifulSoup import BeautifulSoup
from datetime import datetime

log = logging.getLogger(__name__)


def comment_exists(text, user, reply_id):
    '''
    Tries to determine if a comment already exists. This can be useful if
    more than one worker watches the same Inbox and an email is fetched
    multiple times. The last comments made by the user in a specific time
    are checked on the same topic and the text itself.
    If a user replied the same to the same topic in the last two minutes
    the reply will be ignored.
    '''
    now = datetime.utcnow()

    i = 0
    for x in user.comments:
        time_diff = now - user.comments[i].create_time
        if time_diff.seconds < 120 and time_diff.days == 0:
            cmp_text = user.comments[i].revisions[0].text
            cmp_reply_id = user.comments[i].reply_id
            if reply_id == cmp_reply_id:
                if cmp_text == text:
                    return True
        else:
            return False
        i += 1

    return True


def content_type_reader(content_type):
    img_type = re.search(r"image/([^;]*);?", content_type).group(1)
    try:
        img_name = re.search("name=([^;]*)",
                content_type).group(1).rpartition(".")[0]
    except:
        img_name = u"{0}-image".format(img_type)
    return (img_type, img_name)


def error_mail_to_user(errcode, to_user, orig_comm):
    '''receives error codes if posting fails and send notification to user'''
    if errcode == 411:
        body = _(u"Error: Your reply must be longer than 4 characters.\r\n")
    if errcode == 400:
        body = _(u"Error: The email address you replied to is invalid.\r\n")
    if errcode == 401:
        body = _(u"Error: You lack permissions to post replies via email.\r\n")

    if orig_comm:
        br = u"\r\n\r\n"
        body = body + _(u"original comment:") + br + orig_comm.latest.text
        body = body + br + _(u"by: ") + orig_comm.creator.name + br
    else:
        body = body + _(u"Original Comment cannot be determined.\r\n")
    try:
        mail.to_mail(to_user.user_name,
                     to_user.email,
                     _(u"Email comment failed!"),
                     body,
                     headers={},
                     decorate_body=True,
                     email_from=config.get('error_email_from'),
                     name_from="EC-Error")
    except:
        log.error("could not send error mail to user: user undeterminable")
        return
    log.info("sent error mail to user")


def strip_local_part(recipient):
    '''get userid, commentid, security token from local part'''
    pattern = re.compile(r"""\Asubs\.
                             (?P<userid>[1-9][0-9]*)-
                             (?P<commentid>[1-9][0-9]*)\.
                             (?P<sectoken>[a-fA-F0-9]{40})@""", re.VERBOSE)
    result = pattern.match(recipient)
    return result


def remove_notification(text):
    '''removes notification if user didn't'''
    text = re.sub(ur">*\s*_{33}(\r|\n|\r\n|.)*_{33}", u"", text)
    return text


def move_overwrite(src, dst):
    '''overwrite if a file with same name exists'''
    if os.path.exists(dst):
        os.remove(dst)
    shutil.move(src, dst.rpartition("/")[0])


def get_sentiment(text):
    '''
    User can vote via first line of his email:
    (Vote: )1 or +1 or 0 or -1 or + or -
    The Vote will be extracted and the line will be deleted if present.
    Also all leading newlines after vote-line will be deleted.
    '''
    pattern = re.compile(ur"""\A(?:[vV][oO][tT][eE]:?\s*)?
                         (?P<sentiment>0|1|\+1?|-1?)\s*
                         (?:\n|\r|\r\n)+
                         (?P<text>(.|\n|\r|\r\n)*)
                          """, re.VERBOSE)
    result = pattern.match(text)
    if result:
        text = result.group("text")
        sentiment = result.group("sentiment")
        if "+" in sentiment or sentiment == "1":
            sentiment = 1
        elif "-" in sentiment:
            sentiment = -1
        else:
            sentiment = 0
    else:
        sentiment = None

    return text, sentiment


def html_to_markdown(text):
    '''
    Basic HTML-Parsing for markdown-output:
    Use regex to replace tags for use with markdown.

    tag replacements:
    <br>:
        replaced by "  \n"
    <b>text</b> or <strong>text</strong>:
        replaced by "**text**"
    <i>text</i> or <em>text</em>:
        replaced by "*text*"
    <q>text</q> and <blockquote cite="link">text</blockquote>:
        replaced by "\n> text\n" with spaces for breaks
    <hx>text</hx>:
        replaced by "{x times #} text"
    <li>text</li>:
            replaced by "* text  "
    <a href="link">descr</a>:
        replaced by "[descr](http://link "http://link")" (http added if
                                                          required)
    <img src="link" alt="alttext">:
        replaced by "![alttext](http://link "http://link")" (http added if
                                                             required)
    <li>text</li>:
        replaced by "* text  "
        This is a very basic list parser and returns always an unordered list
        without indentations. Deletes </li> before.
    </ol> and </ul>:
        replaced by "  \n"
    other tags:
        replaced by ""
    '''
    def h_repl(matchobj):
        if matchobj:
            h = u""
            for i in range(int(matchobj.group(1))):
                h = h + u"#"
            return h + u" "
        else:
            return ""

    def a_repl(matchobj):
        if matchobj:
            try:
                href = re.search(u"href=[\"]?([^\">]*)[\"]?",
                        matchobj.group(0)).group(1)
                alt = re.search(u">(.*?)<",
                        matchobj.group(0)).group(1)
                if not "http" in href:
                    href = u"http://" + href
                link = u"[{0}]({1} \"{2}\")".format(alt, href, href)
                return link
            except:
                return ""
        else:
            return ""

    def img_repl(matchobj):
        if matchobj:
            try:
                src = re.search(u"src=[\"]?([^\">]*)[\"]?",
                        matchobj.group(0)).group(1)
                alt = re.search(u"alt=[\"]?([^\">]*)[\"]?",
                        matchobj.group(0)).group(1)
                if not "http" in src:
                    src = u"http://" + src
                link = u"![{0}]({1} \"{2}\")".format(alt, src, src)
                return link
            except:
                return ""
        else:
            return ""

    def li_repl(matchobj):
        if matchobj:
            li = u"* " + matchobj.group(1) + u"  \n"
            return li
        else:
            return ""

    def parse_soup(text):
        soup = BeautifulSoup(text)
        blacklist = ["script", "style"]
        keep_attrs = ["a", "img"]

        for tag in soup.findAll():
            if tag.name.lower() in blacklist:
                tag.extract()
            if not tag.name.lower() in keep_attrs:
                tag.attrs = {}
        return unicode(soup)

    replacements = [(ur"(\n|\r|\r\n)[\s]*|\t[\s]*", u""),
            (ur"\s{2,}", u" "),
            (ur"<br />", u"  \n"),
            (ur"(<b>[\s]*)|(</b>)", u"**"),
            (ur"(<strong>[\s]*)|(</strong>)", u"**"),
            (ur"(<i>[\s]*)|(</i>)", u"*"),
            (ur"(<em>[\s]*)|(</em>)", u"*"),
            (ur"<q>|<blockquote.*?>", u"  > "),
            (ur"</q>|</blockquote>", u"  \n\n"),
            (ur"<h([1-6])[\s]*>", h_repl),
            (ur"</h([1-6])[\s]*>", u"  \n"),
            (u"<a.*?</a>", a_repl),
            (ur"<img.*?>", img_repl),
            (ur"</li>", u""),
            (ur"<li>[\s]*([^<|\\n]*)", li_repl),
            (ur"(</ol>)|(</ul>)", u"  \n"),
            (ur"<.*?>", u"")]

    text = parse_soup(text)

    for i, j in replacements:
        text = re.sub(i, j, text, flags=re.IGNORECASE)

    return text


def delete_debris(text):
    '''
    Deletes all ending and leading lines, also shrinks number of lines
    to two if more than three are concatenated at once.
    '''
    replacements = [ur"(\n|\r|\s)*\Z",
                    ur"\A(\n|\r|\s)*"]

    for item in replacements:
        text = re.sub(item, r"", text)

    text = re.sub(ur"((\n|\r\s*|\r\n\s*){3,})", u"\n\n", text)

    return text


def delete_signatures(text):
    '''
    Deletes PGP or other signatures:
    If text begins with a sequence of 2 "-" or "_" at the beginning
    of a new line the rest of the text will be stripped(RFC3676).
    If text contains a reference to the PGP-signed message, the line
    will be deleted before signatures because of containing "-"s.
    Order is crucial: for further replacements add something to the end
    of the list.
    '''
    pgp_debris = ur"(.*?(\r|\n|\r\n))*?"
    pgp_start = ur"-----BEGIN PGP SIGNED MESSAGE-----"
    pgp_hash = ur"((\r|\n|\r\n)hash:\s?\w*(\n|\r|\r\n|\s)*)?"
    p = re.compile(pgp_debris + pgp_start + pgp_hash, re.IGNORECASE)

    replacements = [p,
                    ur"(\r|\n|\r\n)[-_]{2,}(.|\n|\r|\r\n)*"]

    for item in replacements:
        text = re.sub(item, u"", text)

    return text


def create_filesystem(path_md):
    '''create directories if possible and required'''
    try:
        if not os.path.exists(path_md):
            os.makedirs(path_md)
        elif not os.path.exists(os.path.join(path_md, "new")):
            os.makedirs(os.path.join(path_md, "new"))
        elif not os.path.exists(os.path.join(path_md, "cur")):
            os.makedirs(os.path.join(path_md, "cur"))
        elif not os.path.exists(os.path.join(path_md, "tmp")):
            os.makedirs(os.path.join(path_md, "tmp"))
        elif not os.path.exists("/var/mail"):
            os.makedirs("/var/mail")
        return True
    except IOError:
        log.error("you have no permission to create Maildir or mbox")
        log.info("emailcomments are disabled")
        return False
