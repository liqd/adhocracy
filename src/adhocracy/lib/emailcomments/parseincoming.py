import logging
import hashlib
import re
from adhocracy.model import User, Comment
from adhocracy.lib.emailcomments import setupcomment
from adhocracy.lib.emailcomments import util
from pylons import config


log = logging.getLogger(__name__)


def parse_multipart(message, a, rec_dep):
    '''saves contents of multipart messages to a list'''
    content_list = []
    for part in message.get_payload():
        if not part["Content-Type"]:
            continue
        if part.is_multipart():
            if "multipart/alternative" in part["Content-Type"]:
                content_list = parse_multipart(part, "a", rec_dep)
                rec_dep += 1
            else:
                content_list = parse_multipart(part, "na", rec_dep)
        else:
            if "image" in part["Content-Type"]:
                content_list.append((rec_dep, a, part["Content-Type"],
                        part.get_payload(decode=False)))
            else:
                content_list.append((rec_dep, a, part["Content-Type"],
                        unicode(part.get_payload(decode=True),
                        encoding="utf8", errors="replace")))
    return content_list


def save_image(image, content_type):
    '''
    Helper function for later use of saving attached images in database
    and return markdown-code.
    Markdown safe_mode must be set to False, else an image with
    alt-text will be rendered but looks like plain text.
    '''
    data_uri = image.replace("\n", "")
    img_type, img_name = util.content_type_reader(content_type)
    img_mkd = """  \n![{0}](data:image/{1};base64,{2} \"{0}\")  \n"""
    img_mkd = img_mkd.format(img_name, img_type, data_uri)
    return img_mkd


def get_usable_content(content_list):
    '''
    Extracts all readable contents of list and prefers HTML over plaintext if
    a multipart/alternative content is present.
    Images will be saved via data URL.
    '''
    text = ""
    alt_set = []
    image_list = []
    temp_alt_text = ""
    for rec_dep, alt_version, content_type, payload in content_list:
        if "na" in alt_version:
            text = text + temp_alt_text
            temp_alt_text = ""
            if "text/plain" in content_type:
                text = text + payload
            elif "text/html" in content_type:
                text = text + util.html_to_markdown(payload)
            elif "image" in content_type:
                image_list.append(save_image(payload, content_type))
        else:
            if not rec_dep in alt_set:
                if "text/plain" in content_type:
                    temp_alt_text = payload
                elif "text/html" in content_type:
                    alt_set.append(rec_dep)
                    temp_alt_text = util.html_to_markdown(payload)
    text = text + temp_alt_text
    return text, image_list


def parse_payload(message):
    '''
    Extracts Payload of emails. The payload of a message will be decoded
    if the content-transfer-encoding is base64 or quoted-printable.
    If other encodings (7bit/8bit, bogus base64) are detected no decoding
    happens.
    Multipart messages are supported; the payloads will be concatenated if
    readable (html/plain text).
    If a multipart message is "alternative" HTML will be prefered over plain
    text.
    '''
    if message.is_multipart():
        if "multipart/alternative" in message["Content-Type"]:
            content_list = parse_multipart(message, "a", 0)
        else:
            content_list = parse_multipart(message, "na", 0)
        text, image_list = get_usable_content(content_list)
        text = util.remove_notification(text)
        text = util.delete_signatures(text)
        for item in image_list:
            text = text + item
    else:
        if "text/plain" in message["Content-Type"]:
            text = message.get_payload(decode=True)
        elif "text/html" in message["Content-Type"]:
            text = message.get_payload(decode=True)
            text = util.html_to_markdown(text)
        else:
            text = ""
        text = util.remove_notification(text)
        text = util.delete_signatures(text)
    text = util.delete_debris(text)
    text, sentiment = util.get_sentiment(text)
    return (text, sentiment)


def parse_local_part(recipient):
    '''parse local part of email address to determine if it's a comment'''
    result = util.strip_local_part(recipient)
    if not result:
        return None

    sec_token = result.group("sectoken")

    secrets = config.get("adhocracy.crypto.secret")

    comp_str = result.group("userid") + result.group("commentid")
    comp_str = hashlib.sha1(comp_str + secrets).hexdigest()

    if comp_str != sec_token:
        return None

    user_obj = User.find(result.group("userid"))
    comment_obj = Comment.find(result.group("commentid"))

    if user_obj is None or comment_obj is None:
        return None
    return (user_obj, comment_obj)


def handle_inc_mail(message):
    '''Check if incoming email is a comment - if so call commentcreate.'''
    recipient = re.sub(r"(.|\n|\r|\r\n)*?<|>", u"", message["To"])

    objs = parse_local_part(recipient)

    if not objs:
        log.info("but email is not a comment-reply")
        to_user = User.find_by_email(re.sub(r"(.|\n|\r|\r\n)*?<|>", u"",
                message["From"]))
        util.error_mail_to_user(400, to_user, None)
        return

    user_obj, comment_obj = objs

    out = "user {0} replied to comment {1}"
    log.info(out.format(user_obj.id, comment_obj.id))
    log.info("try to write comment-reply to database")

    text, sentiment = parse_payload(message)

    if len(text) > 3:
        setupcomment.comment(user_obj, comment_obj, text, sentiment)
    else:
        log.error("cannot reply: readable text is shorter than 4 characters!")
        util.error_mail_to_user(411, user_obj, comment_obj)
