"""
Helper functions for human-readable and interoperable formats for adhocracy's data.
"""

import logging
import email.utils
import time
import zipfile

from . import formats
from . import transforms

from adhocracy import model
from pylons import config


# def _create_proposal(name, proposal, options):
#     if 'adhocracy_type' in proposal:
#         if proposal['adhocracy_type'] == 'proposal':
#             user = _get_user(options, proposal)

#             myProposal = model.Proposal.find_by_title(proposal['title'], include_deleted=True)
#             if myProposal:
#                 if options['replacement_strategy'] == 'update':
#                     myProposal.text = proposal['text']

#             else:
#                 myProposal = model.Proposal.create(model.Instance.find(proposal['instance'], include_deleted=True), proposal['title'], user)
#                 myProposal.milestone = None
#                 model.meta.Session.flush()
#                 myDescription = model.Page.create(model.Instance.find(proposal['instance'], include_deleted=True), proposal['title'], proposal['text'], user, function=model.Page.DESCRIPTION)
#                 myDescription.parents = [myProposal]

#                 myProposal.description = myDescription

#             model.meta.Session.add(myProposal)

#             # create comments
#             if options['incl_comments']:
#                 if 'comments' in proposal:
#                     for id, comment in proposal['comments'].iteritems():
#                         _create_comment(id, comment, options, myProposal.description)


# def _create_comment(id, comment, options, topic, reply=None):
#     if 'adhocracy_type' in comment:
#         if comment['adhocracy_type'] == 'comment':
#             user = _get_user(options, comment)
#             myComment = model.Comment.create(' ', comment['text'], user, topic, reply=reply, wiki=False)
#             model.meta.Session.add(myComment)

#             # Add subcomments
#             if 'comments' in comment:
#                 for sub_id, subcomment in comment['comments'].iteritems():
#                     _create_comment(sub_id, subcomment, options, topic, reply=myComment)






def export_data(opts):
    data = {}
    data['metadata'] = {
        'type': 'normsetting-export',
        'version': 4,
        'time': email.utils.formatdate(time.time()),
        'adhocracy_options': opts,
    }
    for transform in transforms.gen_active(opts):
        data[transform.public_name] = transform.export_all()
    return data

def export(opts):
    timeStr = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
    title = config.get('adhocracy.site.name', 'adhocracy') + '-' + timeStr
    format = opts.get('format', 'json')
    return formats.render(export_data(opts), format, title)

def import_(f, format, opts):
    data = formats.read_data(f)
    import_data(data, opts)

def import_data(opts, data):
    
    model.meta.Session.commit()

    
# TODO merge with csv user import

