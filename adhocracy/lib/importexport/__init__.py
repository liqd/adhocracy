"""
Helper functions for human-readable and interoperable formats for adhocracy's data.
"""

import logging
import email.utils
import time
import zipfile

from . import formats
from . import transforms

from pylons import config



def _get_user(options, dict):
    user = None
    if options['incl_users'] == True and 'author' in dict:
        user = model.User.find(dict['author'], include_deleted=True)
    if not user:
            user = options['default_user']
    return user


def _get_commentData(all_comments, id_user, parent=None):
    res = {}
    for rc in all_comments:
        if rc.reply != parent:
            continue
        c = {
            'text': rc.latest.text,
            'adhocracy_type': 'comment',
        }
        if id_user is not None:
            c['author'] = id_user(rc.creator)
        children = _get_commentData(all_comments, id_user, rc)
        if children:
            c['comments'] = children

        res[str(rc.id)] = c
    return res

def _get_instanceData(form, id_user):
    instances = {}
    raw_instances = model.instance.Instance.all()
    for ri in raw_instances:
        i = {
            'key': ri.key,
            'title': ri.label,
            'text': ri.description,
            'frozen': ri.frozen,
            'hidden': ri.hidden,
            'adhocracy_groupname': ri.groupname,
            'adhocracy_type': 'instance',
            'adhocracy_disable_proposals': ri.disable_proposals,
            'adhocracy_allow_adopt': ri.allow_adopt,
            'adhocracy_allow_delegate': ri.allow_delegate,
            'adhocracy_allow_index': ri.allow_index,
        }
        if ri.locale:
            i['locale'] = ri.locale.__str__()
        if id_user is not None:
            i['author'] = id_user(ri.creator)
        if form.get('proposals_enabled'):
            proposals = {}
            raw_proposals = model.proposal.Proposal.all(instance=ri)
            for rp in raw_proposals:
                p = {
                    'title': rp.title,
                    'text': rp.description.head.text,
                    'instance': rp.instance.key,
                    'adhocracy_type': 'proposal',
                }
                if id_user is not None:
                    p['author'] = id_user(rp.creator)
                if form.get('proposals_comments_enabled'):
                    all_comments = rp.description.comments
                    p['comments'] = _get_commentData(all_comments, id_user)
                proposals[str(rp.id)] = p
            i['discussion '] = proposals
        instances[ri.key] = i
    return instances


def _create_proposal(name, proposal, options):
    if 'adhocracy_type' in proposal:
        if proposal['adhocracy_type'] == 'proposal':
            user = _get_user(options, proposal)

            myProposal = model.Proposal.find_by_title(proposal['title'], include_deleted=True)
            if myProposal:
                if options['replacement_strategy'] == 'update':
                    myProposal.text = proposal['text']

            else:
                myProposal = model.Proposal.create(model.Instance.find(proposal['instance'], include_deleted=True), proposal['title'], user)
                myProposal.milestone = None
                model.meta.Session.flush()
                myDescription = model.Page.create(model.Instance.find(proposal['instance'], include_deleted=True), proposal['title'], proposal['text'], user, function=model.Page.DESCRIPTION)
                myDescription.parents = [myProposal]

                myProposal.description = myDescription

            model.meta.Session.add(myProposal)

            # create comments
            if options['incl_comments'] == True:
                if 'comments' in proposal:
                    for id, comment in proposal['comments'].iteritems():
                        _create_comment(id, comment, options, myProposal.description)


def _create_comment(id, comment, options, topic, reply=None):
    if 'adhocracy_type' in comment:
        if comment['adhocracy_type'] == 'comment':
            user = _get_user(options, comment)
            myComment = model.Comment.create(' ', comment['text'], user, topic, reply=reply, wiki=False)
            model.meta.Session.add(myComment)

            # Add subcomments
            if 'comments' in comment:
                for sub_id, subcomment in comment['comments'].iteritems():
                    _create_comment(sub_id, subcomment, options, topic, reply=myComment)


def _perform_import(f, format, opts):

    data = formats.read_data(f)


    if include_badges:
        if 'badges' in data:
            for badge in data['badges'].values():
                _create_badge(badge, options)

    if include_users == True:
        if 'users' in data:
            for user in data['users'].values():
                _create_user(user)

    if include_instances:
        if 'discussions' in data:
            for name, instance in data['discussions'].iteritems():
                inst = _create_instance(name, instance, options)

                # create proposals
                if options['include_proposals']:
                    if 'discussion ' in instance:
                        for p_name, proposal in instance['discussion '].iteritems():
                            _create_proposal(p_name, proposal, options)


def export_data(opts):
    data = {}
    data['metadata'] = {
        'type': 'normsetting-export',
        'version': 3,
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


    #     if self.form_result.get('instances_enabled'):
    #         data['discussions'] = _get_instanceData(self.form_result, id_user)

    # eFormat = self.form_result.get('format')
    

# TODO move model.meta.Session.commit() calls to the upper layers
# TODO merge with csv user import

